/**
 * PolyClash Web Client - Network client and game state manager
 *
 * Manages communication with the PolyClash server (/sphgo/* endpoints)
 * and synchronises local board state with the renderer and light rules.
 *
 * Depends on: BoardRenderer (board-renderer.js), LightRules (light-rules.js),
 *             Socket.IO client library (loaded externally).
 */

class GameClient {
    constructor(renderer, rules) {
        this.renderer = renderer;
        this.rules = rules;
        this.socket = null;
        this.serverUrl = null;
        this.token = null;       // player/session token from server
        this.gameToken = null;   // game-level token (for admin ops like close)
        this.playerKey = null;   // key returned from /sphgo/new (black_key, etc.)
        this.side = null;        // 1 = black, -1 = white
        this.boardState = new Array(302).fill(0);
        this.currentPlayer = 1;  // black starts
        this.score = { black: 0, white: 0, unclaimed: 1 };
        this.mode = 'local';     // 'local' | 'network'
        this.counter = 0;
        this.gameId = null;
        this.keys = null;        // { black_key, white_key, viewer_key }
        this.gameOver = false;
        this.aiMode = false;   // true when this client auto-plays via genmove
    }

    // ---------------------------------------------------------------
    // Local game – human (black) vs AI (white) on the server
    // ---------------------------------------------------------------

    async startLocalGame(serverUrl, side) {
        side = side || 'black';
        var aiSide = side === 'black' ? 'white' : 'black';
        this.serverUrl = serverUrl.replace(/\/+$/, '');
        this.mode = 'local';

        try {
            // Create a new game using the server token
            const serverToken = window._serverToken;
            if (!serverToken) {
                this.showStatus('Server token is required to create a game.');
                return;
            }

            const createRes = await this._post('/sphgo/new', { key: serverToken });
            if (!createRes.ok) {
                this.showStatus('Failed to create game: ' + (await createRes.json()).message);
                return;
            }
            const createData = await createRes.json();
            this.gameId = createData.game_id;
            this.keys = {
                black_key: createData.black_key,
                white_key: createData.white_key,
                viewer_key: createData.viewer_key,
            };
            console.log('Game created:', this.gameId);

            // Join as human's side
            const joinRes = await this._post('/sphgo/join', {
                token: this.keys[side + '_key'],
                role: side,
            });
            if (!joinRes.ok) {
                this.showStatus('Failed to join as ' + side + ': ' + (await joinRes.json()).message);
                return;
            }
            const joinData = await joinRes.json();
            this.token = joinData.token;
            this.side = side === 'black' ? 1 : -1;
            console.log('Joined as ' + side + ', token:', this.token);

            // Join AI as the other side
            const joinAIRes = await this._post('/sphgo/join', {
                token: this.keys[aiSide + '_key'],
                role: aiSide,
            });
            if (!joinAIRes.ok) {
                this.showStatus('Failed to join AI as ' + aiSide + '.');
                return;
            }
            const joinAIData = await joinAIRes.json();
            this.gameToken = joinAIData.token; // AI token for genmove

            // Mark both players ready so the game starts
            await this._post('/sphgo/ready', { token: this.token });
            await this._post('/sphgo/ready', { token: this.gameToken });

            // Fetch initial state
            await this.fetchState();
            this.showStatus(i18n.t('status_you_' + side));

            // If human plays white, AI (black) moves first
            if (side === 'white') {
                await this.requestAIMove();
            }
        } catch (err) {
            console.error('startLocalGame error:', err);
            this.showStatus('Error starting local game: ' + err.message);
        }
    }

    // ---------------------------------------------------------------
    // Network game – create / join / connect
    // ---------------------------------------------------------------

    async createNetworkGame(serverUrl) {
        this.serverUrl = serverUrl.replace(/\/+$/, '');
        this.mode = 'network';

        try {
            const serverToken = window._serverToken;
            if (!serverToken) {
                this.showStatus('Server token is required to create a game.');
                return null;
            }

            const res = await this._post('/sphgo/new', { key: serverToken });
            if (!res.ok) {
                this.showStatus('Failed to create network game.');
                return null;
            }
            const data = await res.json();
            this.gameId = data.game_id;
            this.keys = {
                black_key: data.black_key,
                white_key: data.white_key,
                viewer_key: data.viewer_key,
            };

            console.log('Network game created:', this.gameId);
            console.log('Keys:', this.keys);

            this.showStatus(
                'Game created! Share keys — Black: ' +
                    data.black_key +
                    ', White: ' +
                    data.white_key
            );

            return this.keys;
        } catch (err) {
            console.error('createNetworkGame error:', err);
            this.showStatus('Error creating network game: ' + err.message);
            return null;
        }
    }

    async joinWithKey(serverUrl, key, aiMode) {
        this.serverUrl = serverUrl.replace(/\/+$/, '');

        try {
            // Discover role from key
            var whoamiRes = await this._post('/sphgo/whoami', { key: key });
            if (!whoamiRes.ok) {
                this.showStatus(i18n.t('status_invalid_key'));
                return;
            }
            var whoami = await whoamiRes.json();
            var role = whoami.role;
            this.mode = 'network';
            this.playerKey = key;
            this.aiMode = !!aiMode;

            // Join with discovered role
            var res = await this._post('/sphgo/join', { token: key, role: role });
            if (!res.ok) {
                this.showStatus('Failed to join: ' + (await res.json()).message);
                return;
            }
            var data = await res.json();
            this.token = data.token;
            this.side = role === 'black' ? 1 : (role === 'white' ? -1 : 0);

            if (role === 'viewer') {
                this.showStatus(i18n.t('status_watching'));
            } else if (this.aiMode) {
                this.showStatus(i18n.t('status_ai_mode') + ' (' + role + ')');
            } else {
                this.showStatus(i18n.t('status_you_' + role) + ' ' + i18n.t('status_waiting'));
            }

            // Connect socket for real-time updates
            this.connectSocket(serverUrl);

            // Auto-ready for players (not viewers)
            if (role === 'black' || role === 'white') {
                await this._post('/sphgo/ready', { token: this.token });
            }

            await this.fetchState();

            // If AI mode, start auto-playing if it is our turn
            this.autoPlayIfAI();
        } catch (err) {
            console.error('joinWithKey error:', err);
            this.showStatus('Error joining game: ' + err.message);
        }
    }

    async joinGame(serverUrl, key, role) {
        this.serverUrl = serverUrl.replace(/\/+$/, '');
        this.mode = 'network';
        this.playerKey = key;

        try {
            const res = await this._post('/sphgo/join', { token: key, role: role });
            if (!res.ok) {
                this.showStatus('Failed to join game: ' + (await res.json()).message);
                return;
            }
            const data = await res.json();
            this.token = data.token;
            this.side = role === 'black' ? 1 : -1;

            console.log('Joined as', role, '– token:', this.token);
            this.showStatus('Joined as ' + role + '. Waiting for opponent…');

            this.connectSocket(serverUrl);
            await this.fetchState();
        } catch (err) {
            console.error('joinGame error:', err);
            this.showStatus('Error joining game: ' + err.message);
        }
    }

    connectSocket(serverUrl) {
        if (this.socket) {
            this.socket.disconnect();
        }

        var url = serverUrl.replace(/\/+$/, '');
        // eslint-disable-next-line no-undef
        this.socket = io(url);

        var self = this;

        this.socket.on('connect', function () {
            console.log('Socket.IO connected');
            if (self.playerKey) {
                self.socket.emit('join', { key: self.playerKey });
            }
        });

        this.socket.on('joined', function (data) {
            console.log('Socket joined:', data);
            self.showStatus(data.role + ' joined the game.');
        });

        this.socket.on('ready', function (data) {
            console.log('Socket ready:', data);
            self.showStatus(data.role + ' is ready.');
        });

        this.socket.on('start', function (data) {
            console.log('Socket start:', data);
            self.showStatus('Game started!');
            self.fetchState().then(function () {
                self.autoPlayIfAI();
            });
        });

        this.socket.on('played', function (data) {
            console.log('Socket played:', data);
            // Refresh full state from server to stay in sync
            self.fetchState().then(function () {
                self.autoPlayIfAI();
            });
        });

        this.socket.on('passed', function (data) {
            console.log('Socket passed:', data);
            self.fetchState().then(function () {
                self.autoPlayIfAI();
            });
        });

        this.socket.on('game_over', function (data) {
            console.log('Socket game_over:', data);
            self.gameOver = true;
            self.renderer.highlightLegalMoves([]);
            if (data.reason === 'resign') {
                var winnerSide = data.winner === 'black' ? 1 : -1;
                if (self.side === winnerSide) {
                    self.showStatus(i18n.t('status_you_win'));
                } else if (self.side === -winnerSide) {
                    self.showStatus(i18n.t('status_you_lose'));
                } else {
                    self.showStatus(i18n.t('status_game_over'));
                }
            } else {
                self.showStatus(i18n.t('status_game_over'));
            }
        });

        this.socket.on('error', function (data) {
            console.error('Socket error:', data);
            self.showStatus('Server error: ' + data.message);
        });

    }

    // ---------------------------------------------------------------
    // Game actions
    // ---------------------------------------------------------------

    autoPlayIfAI() {
        if (!this.aiMode || this.gameOver || !this.token) return;
        if (this.currentPlayer !== this.side) return;

        var self = this;
        // Small delay so the UI updates and avoids hammering the server
        setTimeout(function () {
            self._doAIMove();
        }, 500);
    }

    async _doAIMove() {
        if (this.gameOver) return;
        if (this.currentPlayer !== this.side) return;

        this.showStatus(i18n.t('status_ai_thinking'));
        try {
            var res = await this._post('/sphgo/genmove', { token: this.token });
            if (!res.ok) {
                var errData = await res.json();
                this.showStatus('AI move failed: ' + errData.message);
                return;
            }
            var data = await res.json();
            if (data.point === null) {
                console.log('AI passed');
                this.showStatus(i18n.t('status_ai_passed'));
                await this.fetchState();
                return;
            }
            console.log('AI played at point', data.point);
            this.counter++;
            this.renderer.markLastMove(data.point);
            await this.fetchState();
        } catch (err) {
            console.error('_doAIMove error:', err);
            this.showStatus('Error in AI move: ' + err.message);
        }
    }

    async resign() {
        if (!this.token || !this.serverUrl) {
            this.showStatus(i18n.t('status_start_game'));
            return;
        }
        if (this.gameOver) return;

        try {
            var res = await this._post('/sphgo/resign', { token: this.token });
            if (!res.ok) {
                var errData = await res.json();
                this.showStatus('Resign failed: ' + errData.message);
                return;
            }
            this.gameOver = true;
            this.renderer.highlightLegalMoves([]);
            this.showStatus(i18n.t('status_you_lose'));
        } catch (err) {
            console.error('resign error:', err);
            this.showStatus('Error resigning: ' + err.message);
        }
    }

    async playMove(point) {
        // Guard: must have an active game
        if (!this.token || !this.serverUrl) {
            this.showStatus(i18n.t('status_start_game'));
            return;
        }
        if (this.gameOver) return;

        // Only allow moves when it is our turn
        if (this.currentPlayer !== this.side) {
            this.showStatus(i18n.t('status_not_turn'));
            return;
        }

        // Quick client-side legality check
        var legal = this.rules.getLegalMoves(this.currentPlayer);
        if (legal.indexOf(point) === -1) {
            this.showStatus(i18n.t('status_illegal'));
            return;
        }

        try {
            // Encode point for the server
            var encoded = this.renderer.boardData.encoder[point];

            var res = await this._post('/sphgo/play', {
                token: this.token,
                steps: this.counter,
                play: encoded,
            });

            if (!res.ok) {
                var errData = await res.json();
                this.showStatus('Move rejected: ' + errData.message);
                return;
            }

            console.log('Move played at point', point);
            this.counter++;
            this.renderer.markLastMove(point);

            // Refresh state from server
            await this.fetchState();

            // In local mode, trigger AI move automatically
            if (this.mode === 'local') {
                await this.requestAIMove();
            }
        } catch (err) {
            console.error('playMove error:', err);
            this.showStatus('Error playing move: ' + err.message);
        }
    }

    async pass() {
        if (!this.token || !this.serverUrl) {
            this.showStatus(i18n.t('status_start_game'));
            return;
        }

        if (this.mode === 'local') {
            this.counter++;
            this.showStatus(i18n.t('status_passed'));
            await this.fetchState();
            await this.requestAIMove();
        } else {
            this.counter++;
            this.showStatus(i18n.t('status_passed'));
            await this.fetchState();
        }
    }

    async requestAIMove() {
        try {
            var res = await this._post('/sphgo/genmove', { token: this.gameToken });
            if (!res.ok) {
                var errData = await res.json();
                this.showStatus('AI move failed: ' + errData.message);
                return;
            }
            var data = await res.json();
            if (data.point === null) {
                console.log('AI passed');
                this.showStatus(i18n.t('status_ai_passed'));
                await this.fetchState();
                return;
            }
            console.log('AI played at point', data.point);
            this.counter++;
            this.renderer.markLastMove(data.point);

            // Refresh state from server
            await this.fetchState();
        } catch (err) {
            console.error('requestAIMove error:', err);
            this.showStatus('Error requesting AI move: ' + err.message);
        }
    }

    async fetchState() {
        try {
            var res = await this._post('/sphgo/state', { token: this.token });
            if (!res.ok) {
                this.showStatus('Failed to fetch state.');
                return;
            }
            var data = await res.json();
            // data: { board: number[302], score: [black, white, unclaimed], current_player: 1|-1, counter: number }
            var score = {
                black: data.score[0],
                white: data.score[1],
                unclaimed: data.score[2],
            };
            this.counter = data.counter;
            this.updateBoardState(data.board, score, data.current_player);

            // Detect game over from state
            if (data.game_over && !this.gameOver) {
                this.gameOver = true;
                this.renderer.highlightLegalMoves([]);
                this.showStatus(i18n.t('status_game_over'));
            }
        } catch (err) {
            console.error('fetchState error:', err);
            this.showStatus('Error fetching state: ' + err.message);
        }
    }

    // ---------------------------------------------------------------
    // State management
    // ---------------------------------------------------------------

    updateBoardState(boardArray, score, currentPlayer) {
        this.boardState = boardArray;
        this.score = score;
        this.currentPlayer = currentPlayer;
        this.rules.setState(boardArray);

        // Update renderer stones and current player hover color
        this.renderer.setCurrentPlayerColor(currentPlayer);
        for (var i = 0; i < 302; i++) {
            this.renderer.setStone(i, boardArray[i]);
        }

        // Highlight legal moves when it is our turn
        if (this.mode === 'local' || this.currentPlayer === this.side) {
            var moves = this.rules.getLegalMoves(this.currentPlayer);
            this.renderer.highlightLegalMoves(moves);
        } else {
            this.renderer.highlightLegalMoves([]);
        }

        this.updateUI();
    }

    updateUI() {
        var blackEl = document.getElementById('score-black');
        var whiteEl = document.getElementById('score-white');
        var unclaimedEl = document.getElementById('score-unclaimed');
        var turnText = document.getElementById('turn-text');
        var turnDot = document.getElementById('turn-dot');

        if (blackEl) blackEl.textContent = i18n.t('score_black') + ': ' + (this.score.black * 100).toFixed(1) + '%';
        if (whiteEl) whiteEl.textContent = i18n.t('score_white') + ': ' + (this.score.white * 100).toFixed(1) + '%';
        if (unclaimedEl) unclaimedEl.textContent = i18n.t('score_unclaimed') + ': ' + (this.score.unclaimed * 100).toFixed(1) + '%';
        if (turnText) turnText.textContent = this.currentPlayer === 1 ? i18n.t('turn_black') : i18n.t('turn_white');
        if (turnDot) {
            turnDot.className = this.currentPlayer === 1 ? 'turn-dot' : 'turn-dot white';
        }

        var moveCounterEl = document.getElementById('move-counter');
        if (moveCounterEl) moveCounterEl.textContent = i18n.t('move_label') + ': ' + this.counter;
    }

    async resetGame() {
        // Close game on server if we have a token
        if (this.token && this.serverUrl) {
            try {
                await this._post('/sphgo/close', { token: this.token });
                console.log('Game closed on server.');
            } catch (err) {
                console.error('resetGame close error:', err);
            }
        }

        // Disconnect socket
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }

        // Reset local state
        this.token = null;
        this.gameToken = null;
        this.playerKey = null;
        this.side = null;
        this.gameId = null;
        this.keys = null;
        this.boardState = new Array(302).fill(0);
        this.currentPlayer = 1;
        this.score = { black: 0, white: 0, unclaimed: 1 };
        this.counter = 0;
        this.mode = 'local';
        this.gameOver = false;
        this.aiMode = false;

        // Clear renderer
        for (var i = 0; i < 302; i++) {
            this.renderer.setStone(i, 0);
        }
        this.renderer.highlightLegalMoves([]);
        this.updateUI();
        this.showStatus(i18n.t('status_reset'));
    }

    async downloadRecord() {
        if (!this.token || !this.serverUrl) {
            this.showStatus(i18n.t('status_start_game'));
            return;
        }

        try {
            var res = await this._post('/sphgo/record', { token: this.token });
            if (!res.ok) {
                this.showStatus('Failed to fetch game record.');
                return;
            }
            var data = await res.json();
            var blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
            var url = URL.createObjectURL(blob);
            var a = document.createElement('a');
            a.href = url;
            a.download = 'polyclash-record-' + (this.gameId || 'game') + '.pgr.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            this.showStatus('Game record downloaded.');
        } catch (err) {
            console.error('downloadRecord error:', err);
            this.showStatus('Error downloading record: ' + err.message);
        }
    }

    // ---------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------

    showStatus(message) {
        console.log('[status]', message);
        var el = document.getElementById('status-bar');
        if (el) {
            el.textContent = message;
        }
    }

    async _post(path, body) {
        return fetch(this.serverUrl + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    }
}

window.GameClient = GameClient;
