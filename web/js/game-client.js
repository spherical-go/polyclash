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
    }

    // ---------------------------------------------------------------
    // Local game – human (black) vs AI (white) on the server
    // ---------------------------------------------------------------

    async startLocalGame(serverUrl) {
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

            // Join as black
            const joinRes = await this._post('/sphgo/join', {
                token: this.keys.black_key,
                role: 'black',
            });
            if (!joinRes.ok) {
                this.showStatus('Failed to join as black: ' + (await joinRes.json()).message);
                return;
            }
            const joinData = await joinRes.json();
            this.token = joinData.token;
            this.side = 1;
            console.log('Joined as black, token:', this.token);

            // Join AI as white so the game can proceed
            const joinWhiteRes = await this._post('/sphgo/join', {
                token: this.keys.white_key,
                role: 'white',
            });
            if (!joinWhiteRes.ok) {
                this.showStatus('Failed to join AI as white.');
                return;
            }
            const joinWhiteData = await joinWhiteRes.json();
            this.gameToken = joinWhiteData.token; // keep white token for genmove

            // Mark both players ready so the game starts
            await this._post('/sphgo/ready', { token: this.token });
            await this._post('/sphgo/ready', { token: this.gameToken });

            // Fetch initial state
            await this.fetchState();
            this.showStatus(i18n.t('status_local_started'));
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

        this.socket.on('connect', function () {
            console.log('Socket.IO connected');
        });

        var self = this;

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
            self.fetchState();
        });

        this.socket.on('played', function (data) {
            console.log('Socket played:', data);
            // Refresh full state from server to stay in sync
            self.fetchState();
        });

        this.socket.on('error', function (data) {
            console.error('Socket error:', data);
            self.showStatus('Server error: ' + data.message);
        });

        // Tell the server we want to join the room
        if (this.playerKey) {
            this.socket.emit('join', { key: this.playerKey });
        }
    }

    // ---------------------------------------------------------------
    // Game actions
    // ---------------------------------------------------------------

    async playMove(point) {
        // Guard: must have an active game
        if (!this.token || !this.serverUrl) {
            this.showStatus(i18n.t('status_start_game'));
            return;
        }

        // Only allow moves when it is our turn
        if (this.mode === 'network' && this.currentPlayer !== this.side) {
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
            console.log('AI played at point', data.point);
            this.counter++;
            if (data.point !== undefined) {
                this.renderer.markLastMove(data.point);
            }

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
