/**
 * PolyClash Lobby – login, registration, game room management
 */

(function () {
    'use strict';

    var SESSION_KEY = 'polyclash_session';
    var serverUrl = window.location.origin;

    // ── Helpers ───────────────────────────────────────

    function post(path, body) {
        return fetch(serverUrl + path, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
    }

    function saveSession(token, username) {
        localStorage.setItem(SESSION_KEY, JSON.stringify({ token: token, username: username }));
    }

    function loadSession() {
        try {
            return JSON.parse(localStorage.getItem(SESSION_KEY));
        } catch (e) {
            return null;
        }
    }

    function clearSession() {
        localStorage.removeItem(SESSION_KEY);
    }

    function $(id) {
        return document.getElementById(id);
    }

    // ── Auth ──────────────────────────────────────────

    function showLogin() {
        $('login-form').classList.remove('hidden');
        $('register-form').classList.add('hidden');
    }

    function showRegister() {
        $('login-form').classList.add('hidden');
        $('register-form').classList.remove('hidden');
    }

    async function doLogin() {
        var username = $('login-username').value.trim();
        var password = $('login-password').value;
        $('login-error').textContent = '';

        if (!username || !password) {
            $('login-error').textContent = 'Please enter username and password.';
            return;
        }

        try {
            var res = await post('/sphgo/auth/login', { username: username, password: password });
            var data = await res.json();
            if (!res.ok) {
                $('login-error').textContent = data.message || 'Login failed.';
                return;
            }
            saveSession(data.token, data.username);
            enterLobby(data.token, data.username);
        } catch (err) {
            $('login-error').textContent = 'Connection error.';
        }
    }

    async function doRegister() {
        var username = $('reg-username').value.trim();
        var password = $('reg-password').value;
        var invite = $('reg-invite').value.trim();
        $('register-error').textContent = '';

        if (!username || !password || !invite) {
            $('register-error').textContent = 'All fields are required.';
            return;
        }

        try {
            var res = await post('/sphgo/auth/register', {
                username: username,
                password: password,
                invite_code: invite,
            });
            var data = await res.json();
            if (!res.ok) {
                $('register-error').textContent = data.message || 'Registration failed.';
                return;
            }
            saveSession(data.token, data.username);
            enterLobby(data.token, data.username);
        } catch (err) {
            $('register-error').textContent = 'Connection error.';
        }
    }

    async function doLogout() {
        var session = loadSession();
        if (session) {
            await post('/sphgo/auth/logout', { token: session.token });
        }
        clearSession();
        $('auth-panel').classList.remove('hidden');
        $('lobby-panel').classList.add('hidden');
        $('admin-panel').classList.add('hidden');
        showLogin();
    }

    // ── Lobby ─────────────────────────────────────────

    var currentSession = null;

    async function enterLobby(token, username) {
        currentSession = { token: token, username: username };
        $('auth-panel').classList.add('hidden');
        $('lobby-panel').classList.remove('hidden');
        $('user-greeting').textContent = 'Welcome, ' + username;

        // Check admin status
        try {
            var res = await post('/sphgo/auth/me', { token: token });
            var data = await res.json();
            if (res.ok && data.is_admin) {
                $('admin-panel').classList.remove('hidden');
                loadInvites();
            }
        } catch (e) {
            // ignore
        }

        refreshRooms();
    }

    async function refreshRooms() {
        if (!currentSession) return;

        try {
            var res = await post('/sphgo/lobby', { token: currentSession.token });
            if (!res.ok) {
                if (res.status === 401) {
                    clearSession();
                    location.reload();
                }
                return;
            }
            var data = await res.json();
            renderRooms(data.rooms, data.max_rooms, data.active_count);
            renderUsers(data.users || []);
        } catch (err) {
            $('lobby-status').textContent = 'Error loading rooms.';
        }
    }

    var STATUS_LABELS = {
        waiting: '⏳ Waiting',
        ready: '✅ Ready',
        playing: '🎮 Playing',
        completed: '🏁 Finished',
    };

    function renderRooms(rooms, maxRooms, activeCount) {
        var limitText = maxRooms > 0 ? activeCount + ' / ' + maxRooms : activeCount + ' active';
        $('rooms-count').textContent = limitText;

        var list = $('rooms-list');
        list.innerHTML = '';

        if (rooms.length === 0) {
            list.innerHTML = '<p style="color:var(--text-muted);text-align:center;padding:20px;">No active games. Create one!</p>';
            return;
        }

        for (var i = 0; i < rooms.length; i++) {
            var room = rooms[i];
            var card = document.createElement('div');
            card.className = 'room-card';
            if (room.status === 'completed') {
                card.classList.add('room-completed');
            }

            var idSpan = document.createElement('span');
            idSpan.className = 'room-id';
            idSpan.textContent = '#' + room.room_number;

            var statusSpan = document.createElement('span');
            statusSpan.className = 'room-status';
            var label = STATUS_LABELS[room.status] || room.status;
            statusSpan.textContent = label;

            var actions = document.createElement('span');
            actions.className = 'room-actions';

            if (room.status !== 'completed') {
                if (!room.joined.black) {
                    var btnBlack = document.createElement('button');
                    btnBlack.textContent = 'Join Black';
                    btnBlack.setAttribute('data-game-id', room.game_id);
                    btnBlack.setAttribute('data-role', 'black');
                    btnBlack.addEventListener('click', joinRoomHandler);
                    actions.appendChild(btnBlack);
                }
                if (!room.joined.white) {
                    var btnWhite = document.createElement('button');
                    btnWhite.textContent = 'Join White';
                    btnWhite.setAttribute('data-game-id', room.game_id);
                    btnWhite.setAttribute('data-role', 'white');
                    btnWhite.addEventListener('click', joinRoomHandler);
                    actions.appendChild(btnWhite);
                }
            }

            var btnWatch = document.createElement('button');
            btnWatch.textContent = room.status === 'completed' ? 'Review' : 'Watch';
            btnWatch.setAttribute('data-game-id', room.game_id);
            btnWatch.setAttribute('data-role', 'viewer');
            btnWatch.addEventListener('click', joinRoomHandler);
            actions.appendChild(btnWatch);

            card.appendChild(idSpan);
            card.appendChild(statusSpan);
            card.appendChild(actions);
            list.appendChild(card);
        }
    }

    function renderUsers(users) {
        var list = $('users-list');
        if (!list) return;
        list.innerHTML = '';
        if (users.length === 0) {
            list.innerHTML = '<p style="color:var(--text-muted);">No registered users.</p>';
            return;
        }
        for (var i = 0; i < users.length; i++) {
            var user = users[i];
            var row = document.createElement('div');
            row.className = 'user-row';
            row.textContent = user.username + (user.is_admin ? ' (admin)' : '');
            list.appendChild(row);
        }
    }

    async function joinRoomHandler(e) {
        var btn = e.target;
        var gameId = btn.getAttribute('data-game-id');
        var role = btn.getAttribute('data-role');

        if (!currentSession) return;

        try {
            // Get the key for this role from the lobby create data
            // We need to use the server token to get the key, then join
            var res = await post('/sphgo/lobby/join', {
                token: currentSession.token,
                game_id: gameId,
                role: role,
            });
            if (!res.ok) {
                var errData = await res.json();
                $('lobby-status').textContent = errData.message || 'Failed to join.';
                return;
            }
            var data = await res.json();
            // Redirect to game with the key
            window.location.href = '/?key=' + data.key;
        } catch (err) {
            $('lobby-status').textContent = 'Error joining game.';
        }
    }

    async function createGame() {
        if (!currentSession) return;

        try {
            var res = await post('/sphgo/lobby/create', { token: currentSession.token });
            var data = await res.json();
            if (!res.ok) {
                $('lobby-status').textContent = data.message || 'Failed to create game.';
                return;
            }
            $('lobby-status').textContent = 'Game created!';
            refreshRooms();
        } catch (err) {
            $('lobby-status').textContent = 'Error creating game.';
        }
    }

    // ── Admin ─────────────────────────────────────────

    async function generateInvite() {
        if (!currentSession) return;

        try {
            var res = await post('/sphgo/auth/invite', { token: currentSession.token });
            var data = await res.json();
            if (res.ok) {
                $('invite-result').textContent = data.invite_code;
                loadInvites();
            }
        } catch (err) {
            // ignore
        }
    }

    async function loadInvites() {
        if (!currentSession) return;

        try {
            var res = await post('/sphgo/auth/invites', { token: currentSession.token });
            var data = await res.json();
            if (!res.ok) return;

            var list = $('invite-list');
            list.innerHTML = '';
            for (var i = 0; i < data.invites.length; i++) {
                var inv = data.invites[i];
                var row = document.createElement('div');
                row.className = 'invite-row' + (inv.used_by ? ' invite-used' : '');
                row.textContent = inv.code + (inv.used_by ? ' (used by ' + inv.used_by + ')' : ' (available)');
                list.appendChild(row);
            }
        } catch (err) {
            // ignore
        }
    }

    // ── Init ──────────────────────────────────────────

    document.addEventListener('DOMContentLoaded', function () {
        // Toggle login/register
        $('show-register').addEventListener('click', showRegister);
        $('show-login').addEventListener('click', showLogin);

        // Auth buttons
        $('btn-login').addEventListener('click', doLogin);
        $('btn-register').addEventListener('click', doRegister);
        $('btn-logout').addEventListener('click', doLogout);

        // Enter on password fields
        $('login-password').addEventListener('keydown', function (e) {
            if (e.key === 'Enter') doLogin();
        });
        $('reg-invite').addEventListener('keydown', function (e) {
            if (e.key === 'Enter') doRegister();
        });

        // Lobby buttons
        $('btn-create-game').addEventListener('click', createGame);
        $('btn-refresh').addEventListener('click', refreshRooms);

        // Admin
        $('btn-gen-invite').addEventListener('click', generateInvite);

        // Auto-restore session
        var session = loadSession();
        if (session && session.token) {
            // Validate session
            post('/sphgo/auth/me', { token: session.token })
                .then(function (res) {
                    if (res.ok) {
                        return res.json().then(function (data) {
                            enterLobby(session.token, data.username);
                        });
                    } else {
                        clearSession();
                        showLogin();
                    }
                })
                .catch(function () {
                    clearSession();
                    showLogin();
                });
        } else {
            showLogin();
        }
    });
})();
