# Server Implementation

This document provides details about the implementation of the PolyClash server, including the REST API, Socket.IO integration, authentication, and data storage.

## Overview

The PolyClash server is a Flask web application (`polyclash/server.py`) that serves the web client and provides:

- Static file serving for the web client (`web/` directory)
- REST API endpoints for game management (`/sphgo/*`)
- Socket.IO for real-time communication during gameplay
- Optional team-mode user authentication and lobby
- Board-level move validation and execution (server is authoritative)
- Optional HRM AI engine with heuristic fallback for move generation
- Board state persistence and restoration on startup

## Main Components

### Flask Application

```python
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

app = Flask(__name__, static_folder=WEB_DIR, static_url_path="/web")
app.config["SECRET_KEY"] = secret_key
app.logger.addHandler(InterceptHandler())  # register loguru as handler
socketio = SocketIO(app, cors_allowed_origins="*")
storage = create_storage()
```

**Module-level state:**

- `boards: dict[str, Board]` — in-memory `Board` instances keyed by game ID. The server executes `Board.play()` for move validation, not just storage.
- `_user_store: Optional[Any]` — team-mode user authentication store (set by CLI)
- `MAX_ROOMS: int` — room limit from `POLYCLASH_MAX_ROOMS` env var (0 = unlimited)
- `_hrm_player: Any` — optional HRM AI engine, loaded at startup if available

### API Call Decorator

The `api_call` decorator wraps game API endpoints and handles three authentication modes:

```python
def api_call(func):
    def wrapper(*args, **kwargs):
        data = request.get_json()
        token = data.get("token") or data.get("key")

        skip_auth = os.environ.get("POLYCLASH_NO_AUTH") or os.environ.get(
            "POLYCLASH_SOLO_MODE"
        )
        if skip_auth:
            # Skip token validation; still resolve player context if possible
            if token and storage.contains(token):
                # ... resolve game_id, role from storage
        elif token == server_token:
            pass  # server-level token, skip player auth
        elif token and storage.contains(token):
            # ... resolve game_id, role from storage
        else:
            return jsonify({"message": "invalid token"}), 401

        result, code = func(*args, **kwargs)
        return jsonify(result), code
```

The decorator:
1. Checks `POLYCLASH_NO_AUTH` or `POLYCLASH_SOLO_MODE` environment variables — if set, skips authentication but still resolves player context when possible
2. Checks if the token matches `server_token` — grants server-level access
3. Checks if the token exists in storage — resolves `game_id` and `role` from the token
4. Returns 401 if none of the above match

### Board Persistence

After every state change, `_persist_board(game_id)` saves the board snapshot to storage. On startup, `restore_boards()` rebuilds the in-memory `boards` dict from persisted snapshots.

```python
def _persist_board(game_id: str) -> None:
    board = boards.get(game_id)
    if board is not None:
        storage.save_board(game_id, board.to_dict())

def restore_boards() -> None:
    for game_id in storage.list_rooms():
        board_data = storage.load_board(game_id)
        if board_data is not None:
            boards[game_id] = Board.from_dict(board_data)
```

### REST API

#### Root and Routing

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Serves `index.html`; in solo mode redirects to `/?token=...&side=...`; in team mode redirects to `lobby.html` if no key/token in URL |
| `/sphgo/` | GET | HTML list of active games with viewer keys |
| `/sphgo/list` | GET | JSON list of active room IDs |

#### Game Management

All game endpoints use `POST` with JSON body and the `@api_call` decorator:

| Endpoint | Parameters | Description |
|----------|-----------|-------------|
| `/sphgo/whoami` | `key` | Returns role and game_id for a game key (no auth required) |
| `/sphgo/new` | `key` (server token) | Creates a new game room (enforces room limit), creates a Board, returns game_id + player keys |
| `/sphgo/join` | `token`, `role` | Joins a game as black/white/viewer, returns player token |
| `/sphgo/joined_status` | `token` | Returns joined status for a game |
| `/sphgo/ready_status` | `token` | Returns ready status for a game |
| `/sphgo/ready` | `token` | Marks player as ready; starts game if all players ready |
| `/sphgo/cancel` | `token` | Cancels readiness (placeholder) |
| `/sphgo/close` | `token` | Closes game room, removes board from memory |
| `/sphgo/state` | `token` | Returns full board state: `board[302]`, `score`, `current_player`, `counter`, optionally `game_over` |
| `/sphgo/genmove` | `token` | AI generates a move: tries HRM first, then heuristic fallback, retries on illegal moves |
| `/sphgo/play` | `token`, `steps`, `play` | Validates and executes a player move via `Board.play()`, broadcasts via Socket.IO |
| `/sphgo/resign` | `token` | Player resigns, emits `game_over` event |
| `/sphgo/record` | `token` | Returns game record as JSON |

#### Move Execution (`/sphgo/play`)

The server does not merely store moves — it validates and executes them on the `Board` object:

```python
board = boards[game_id]
point = decoder[tuple(play)]
player_color = BLACK if role == "black" else WHITE
try:
    board.play(point, player_color)
    board.consecutive_passes = 0
    board.switch_player()
except ValueError as e:
    return {"message": str(e)}, 400
```

Validation includes: step count matching, correct player turn, valid play encoding, and board-level rule enforcement.

#### AI Move Generation (`/sphgo/genmove`)

```python
# Try HRM AI engine first
point = None
if _hrm_player is not None:
    point = _hrm_player.genmove(board, player_color)

# Fall back to heuristic ranking
if point is None:
    ranked = board.rank_moves(player_color)
    point = ranked[0] if ranked else None

# If chosen move is illegal, try alternatives from ranking
# If no legal move exists, pass
```

#### Auth Endpoints (Team Mode)

These endpoints are active only when `_user_store` is set (team mode):

| Endpoint | Description |
|----------|-------------|
| `/sphgo/auth/register` | Register with username, password, invite code |
| `/sphgo/auth/login` | Log in, receive session token |
| `/sphgo/auth/logout` | Invalidate session token |
| `/sphgo/auth/me` | Return user info (username, is_admin) |
| `/sphgo/auth/invite` | Admin: create invite code |
| `/sphgo/auth/invites` | Admin: list all invite codes |
| `/sphgo/auth/users` | Admin: list all registered users |

#### Lobby Endpoints (Team Mode)

| Endpoint | Description |
|----------|-------------|
| `/sphgo/lobby` | List active rooms with joined/ready status (requires login) |
| `/sphgo/lobby/create` | Create a new game (enforces room limit, requires login) |
| `/sphgo/lobby/join` | Join a game by game_id and role, returns the game key |

### Socket.IO Integration

The server uses Socket.IO for real-time communication:

**Server-side event handlers:**

```python
@socketio.on("join")
def on_join(data):
    key = data["key"]
    # Validate key, resolve game_id and role from storage
    # Join the Socket.IO room
    # Emit "joined" event to the room

@socketio.on("ready")
def on_ready(data):
    key = data["key"]
    # Mark player as ready
    # Emit "ready" event to the room
    # If all players ready, start a delayed_start thread
```

**Emitted events:**

| Event | Data | Trigger |
|-------|------|---------|
| `joined` | `{ role, token, plays }` | Player/viewer joins a game |
| `ready` | `{ role }` | Player marks ready |
| `start` | `{ message }` | All players ready (via `delayed_start` thread) |
| `played` | `{ role, steps, play, score }` | A move is executed |
| `passed` | `{ role }` | AI passes |
| `game_over` | `{ reason, winner, score }` | Game ends (complete or resign) |
| `error` | `{ message }` | Error during Socket.IO operations |

### Data Storage

The server uses a pluggable storage backend via `create_storage()`:

```python
class DataStorage(ABC):
    def create_room(self) -> dict: ...
    def contains(self, key_or_token) -> bool: ...
    def get_game_id(self, key) -> str: ...
    def get_role(self, key) -> str: ...
    def get_key(self, game_id, role) -> str: ...
    def create_player(self, key, role) -> str: ...
    def joined_status(self, game_id) -> dict: ...
    def ready_status(self, game_id) -> dict: ...
    def mark_ready(self, game_id, role): ...
    def all_ready(self, game_id) -> bool: ...
    def add_play(self, game_id, play): ...
    def get_plays(self, game_id) -> list: ...
    def save_board(self, game_id, board_dict): ...
    def load_board(self, game_id) -> dict | None: ...
    def close_room(self, game_id): ...
    def list_rooms(self) -> list: ...
```

Implementations include `MemoryStorage` and `RedisStorage`.

## Server Initialization

The `main()` function in `server.py` calls `restore_boards()` and starts the server:

```python
def main():
    restore_boards()
    port = int(os.environ.get("PORT", 3302))
    logger.info(f"Secret: {secret_key}")
    logger.info(f"Token: {server_token}")
    socketio.run(app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True, debug=False)
```

However, the server is typically started via the CLI (`polyclash/cli.py`), which sets up environment variables and configuration before importing the server module.

## Game Flow

### Game Creation

1. Client sends `POST /sphgo/new` with the server token
2. Server enforces room limit, creates a room in storage
3. Server creates a `Board` instance in the `boards` dict
4. Server persists the board and returns `game_id`, `black_key`, `white_key`, `viewer_key`

### Player Joining

1. Client sends `POST /sphgo/join` with a player key and role
2. Server creates a player token via storage
3. Server joins the Socket.IO room and emits `joined` to the room
4. Server returns the player token and joined status

### Game Start

1. Client sends `POST /sphgo/ready` with the player token
2. Server marks the player as ready and emits `ready` to the room
3. When all players are ready, server starts a `delayed_start` thread
4. The thread calls `storage.start_game()` and emits `start` to the room

### Gameplay

1. Client sends `POST /sphgo/play` with the player token, step count, and encoded move
2. Server validates step count, player turn, and play encoding
3. Server executes `board.play(point, player_color)` for rule validation
4. Server persists the board, stores the play, and emits `played` to the room
5. If the game is over, server emits `game_over`

### Game End

1. Game ends when both players pass consecutively, or a player resigns
2. Server emits `game_over` with winner, final score, and reason
3. Client can close the game via `POST /sphgo/close`, which removes the board and room

## Deployment

### Development / Local Play

The server is started via the unified CLI:

```bash
# Solo mode: human vs AI, opens browser automatically
polyclash solo --side black --port 3302

# Family mode: LAN game, prints URLs for each player
polyclash family --port 3302

# Serve mode: generic server
polyclash serve --port 3302

# Team mode: user accounts, lobby, room limits
polyclash team --port 3302 --rooms 8
```

All modes default to port 3302.

### Production

For production deployment, use `polyclash serve` or `polyclash team` with a reverse proxy:

```nginx
server {
    listen 80;
    server_name polyclash.example.com;

    location / {
        proxy_pass http://127.0.0.1:3302;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /socket.io {
        proxy_redirect off;
        proxy_buffering off;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";

        proxy_pass http://127.0.0.1:3302/socket.io;
    }
}
```

Docker and cloud deployment configs are available in `Dockerfile`, `docker-compose.yml`, `fly.toml`, `railway.json`, and `render.yaml`.

## Security Considerations

The server implements several security measures:

- Secret key for Flask sessions
- Server token for API authentication (auto-generated or set via `--token` / `POLYCLASH_SERVER_TOKEN`)
- Player tokens for game authentication (resolved via storage)
- Skip-auth mode via `POLYCLASH_NO_AUTH` or `POLYCLASH_SOLO_MODE` for local play
- Team mode uses invite codes for registration and session tokens for authentication
- Admin-only endpoints for invite code and user management
- Input validation for all API endpoints (step count, player turn, valid play encoding, board-level rules)
- CORS allowed for all origins on Socket.IO (`cors_allowed_origins="*"`)

## Logging

The server uses the `loguru` library for logging:

```python
from polyclash.util.logging import logger, InterceptHandler

app.logger.addHandler(InterceptHandler())  # register loguru as handler
```

Logs are stored in the user's home directory:
- Windows: `%USERPROFILE%\.polyclash\app.log`
- macOS/Linux: `~/.polyclash/app.log`

## Error Handling

The server includes error handling for various scenarios:

- Invalid/missing tokens return 401 Unauthorized
- Game not found returns 404 Not Found
- Invalid moves (wrong turn, illegal play, board rule violation) return 400 Bad Request
- Room limit reached returns 400 Bad Request
- Team mode endpoints return 400 when team mode is not enabled
- Admin endpoints return 403 when non-admin users attempt access
- Unhandled exceptions return 500 Internal Server Error with the error message
