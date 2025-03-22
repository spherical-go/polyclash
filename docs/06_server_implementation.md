# Server Implementation

This document provides details about the implementation of the PolyClash server, including the REST API, Socket.IO integration, and data storage.

## Overview

The PolyClash server is a Flask web application that enables network play. It provides:

- REST API endpoints for game management
- Socket.IO for real-time communication during gameplay
- Data storage for game state persistence

## Main Components

### Flask Application

The server is implemented as a Flask application in `polyclash/server.py`:

```python
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.logger.addHandler(InterceptHandler())  # register loguru as handler
socketio = SocketIO(app)
storage = create_storage()
```

The server generates a secret key and server token for security:

```python
secret_key = secrets.token_hex(SECRET_KEY_LENGTH // 2)
server_token = secrets.token_hex(SERVER_TOKEN_LENGTH // 2)
```

### REST API

The server provides several REST API endpoints for game management:

#### Game Creation

```python
@app.route('/sphgo/new', methods=['POST'])
@api_call
def new():
    data = storage.create_room()
    logger.info(f'game created... {data["game_id"]}')
    return data, 200
```

This endpoint creates a new game room and returns keys for players.

#### Joining a Game

```python
@app.route('/sphgo/join', methods=['POST'])
@api_call
def join(game_id=None, role=None, token=None):
    logger.info(f'joining game... {game_id}')
    if role in ['black', 'white']:
        token = player_join_room(game_id, role)
        logger.info(f'{role.capitalize()} player {token} joined game... {game_id}')
        return {'status': storage.joined_status(game_id)}, 200
    else:
        token = viewer_join_room(game_id)
        logger.info(f'Viewer {token} joined game... {game_id}')
        return {'status': storage.joined_status(game_id)}, 200
```

This endpoint allows players to join an existing game.

#### Player Readiness

```python
@app.route('/sphgo/ready', methods=['POST'])
@api_call
def ready(game_id=None, role=None, token=None):
    logger.info(f'game readying... {game_id}')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        player_ready(game_id, role)
        return {'status': storage.ready_status(game_id)}, 200
```

This endpoint marks a player as ready to start the game.

#### Making a Move

```python
@app.route('/sphgo/play', methods=['POST'])
@api_call
def play(game_id=None, role=None, steps=None, play=None, token=None):
    plays = storage.get_plays(game_id)
    logger.info(f'{role} play at {play} with steps {steps} ... {game_id}:{len(plays)}')
    if steps != len(plays):
        return {'message': f'Length of {len(plays)} mismatched with steps {steps} passed in'}, 400

    # black is the first player and then take the even steps, and steps is 0-based
    if steps % 2 == 0 and role != 'black':
        return {'message': 'Invalid player'}, 400

    # white is the second player and then take the odd steps, and steps is 0-based
    if steps % 2 == 1 and role != 'white':
        return {'message': 'Invalid player'}, 400

    code = ','.join([str(elm) for elm in play])
    if code not in valid_plays:
        return {'message': 'Invalid play'}, 400

    storage.add_play(game_id, play)
    socketio.emit('played', {"role": role, "steps": steps, "play": play}, room=game_id)

    return {'message': 'Play processed'}, 200
```

This endpoint allows players to make moves.

#### Closing a Game

```python
@app.route('/sphgo/close', methods=['POST'])
@api_call
def close(game_id=None, role=None, token=None):
    if storage.contains(token):
        logger.info(f'game closing... {game_id}')
        storage.close_room(game_id)
    logger.info('game closed...')
    return {'message': 'Game closed'}, 200
```

This endpoint closes a game and cleans up resources.

### Socket.IO Integration

The server uses Socket.IO for real-time communication during gameplay:

```python
@socketio.on('join')
def on_join(data):
    logger.info(f'event join... {str(data)}')
    try:
        key = data['key']
        if not storage.contains(key):
            logger.error(f'error in event join... {key} was not found in rooms')
            emit('error', {'message': 'Game not found'})
            return
        game_id = storage.get_game_id(key)
        role = storage.get_role(key)

        if role in ['black', 'white']:
            player_join_room(game_id, role)
        if role == 'viewer':
            viewer_join_room(game_id)
    except Exception as e:
        logger.error(f'error in event join... unknown error {str(e)}')
        logger.exception('error in event join...', exc_info=e)
        emit('error', {'message': str(e)})
```

```python
@socketio.on('ready')
def on_ready(data):
    key = data['key']
    if storage.contains(key):
        emit('error', {'message': 'Game not found'})
        return

    game_id = storage.get_game_id(key)
    role = storage.get_role(key)

    if role in ['black', 'white']:
        storage.mark_ready(game_id, role)
        emit('ready', {'role': role}, room=game_id)

        # Check if all required players are ready
        if storage.all_ready(game_id):
            delayed_thread = Thread(target=delayed_start, args=(game_id,))
            delayed_thread.start()
```

### Data Storage

The server supports two storage backends:

#### Abstract Base Class

```python
class DataStorage(ABC):
    @abstractmethod
    def create_room(self):
        pass

    @abstractmethod
    def contains(self, key_or_token):
        pass

    # ... other abstract methods
```

#### Memory Storage

```python
class MemoryStorage(DataStorage):
    def __init__(self):
        self.games = {}
        self.rooms = {}

    def create_room(self):
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        self.games[game_id] = {
            'id': game_id,
            'keys': {'black': black_key, 'white': white_key, 'viewer': viewer_key},
            'players': {}, 'viewers': [], 'plays': [],
            'joined': {'black': False, 'white': False},
            'ready': {'black': False, 'white': False},
        }
        self.rooms[black_key] = game_id
        self.rooms[white_key] = game_id
        self.rooms[viewer_key] = game_id

        return dict(game_id=game_id, black_key=black_key, white_key=white_key, viewer_key=viewer_key)

    # ... other methods
```

#### Redis Storage

```python
class RedisStorage(DataStorage):
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)

    def create_room(self):
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        self.redis.rpush('games', game_id)
        self.redis.hset('rooms', black_key, game_id)
        self.redis.hset('rooms', white_key, game_id)
        self.redis.hset('rooms', viewer_key, game_id)

        # ... set up game data in Redis

        return dict(game_id=game_id, black_key=black_key, white_key=white_key, viewer_key=viewer_key)

    # ... other methods
```

### API Call Decorator

The server uses a decorator to handle API calls:

```python
def api_call(func):
    def wrapper(*args, **kwargs):
        try:
            data = request.get_json()
            token = data.get('token') or data.get('key')
            if len(token) == SERVER_TOKEN_LENGTH:
                if token != server_token:
                    return jsonify({'message': 'invalid token'}), 401
            else:
                if not storage.contains(token):
                    return jsonify({'message': 'invalid token'}), 401

                game_id = storage.get_game_id(token)
                if not storage.exists(game_id):
                    return jsonify({'message': 'Game not found'}), 404

                for key, value in data.items():
                    kwargs[key] = value

                role = storage.get_role(token)
                kwargs['game_id'] = game_id
                kwargs['role'] = role

            result, code = func(*args, **kwargs)

            return jsonify(result), code
        except Exception as e:
            logger.exception('error', exc_info=e)
            return jsonify({'message': str(e)}), 500

    wrapper.__name__ = func.__name__
    return wrapper
```

This decorator:
- Extracts the token from the request
- Validates the token
- Retrieves the game ID and role
- Calls the API function
- Handles exceptions

## Server Initialization

The server is initialized in the `main()` function:

```python
def main():
    logger.info(f"Secret: {secret_key}")
    logger.info(f"Token: {server_token}")
    socketio.run(app, host='0.0.0.0', port=3302, allow_unsafe_werkzeug=True, debug=False)
```

## Game Flow

### Game Creation

1. Client sends a POST request to `/sphgo/new`
2. Server creates a new game room
3. Server generates keys for black, white, and viewer roles
4. Server returns the keys to the client

### Player Joining

1. Client sends a POST request to `/sphgo/join` with the game ID, role, and token
2. Server validates the token
3. Server adds the player to the game room
4. Server returns the joined status to the client
5. Server emits a `joined` event to all clients in the room

### Game Start

1. Client sends a POST request to `/sphgo/ready` with the token
2. Server marks the player as ready
3. Server emits a `ready` event to all clients in the room
4. When all players are ready, server starts the game
5. Server emits a `start` event to all clients in the room

### Gameplay

1. Client sends a POST request to `/sphgo/play` with the token, steps, and play
2. Server validates the move
3. Server adds the move to the game state
4. Server emits a `played` event to all clients in the room

### Game End

1. Client sends a POST request to `/sphgo/close` with the token
2. Server closes the game room
3. Server cleans up resources

## Deployment

### Development

For development, the server can be run directly:

```bash
polyclash-server
```

### Production

For production, the server can be run with uWSGI:

```bash
uwsgi --http :7763 --gevent 100 --http-websockets --master --wsgi polyclash.server:app --logto ~/.polyclash/uwsgi.log
```

With Nginx as a reverse proxy:

```nginx
server {
    listen 80;
    server_name polyclash.example.com;

    location /sphgo {
        proxy_pass http://127.0.0.1:7763;
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
            
        proxy_pass http://127.0.0.1:7763/socket.io;
    }
}
```

## Security Considerations

The server implements several security measures:

- Secret key for Flask sessions
- Server token for API authentication
- Player tokens for game authentication
- Input validation for all API endpoints
- Exception handling for all operations

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

- Invalid tokens return 401 Unauthorized
- Game not found returns 404 Not Found
- Invalid moves return 400 Bad Request
- Exceptions return 500 Internal Server Error with the error message

## Extensibility

The server is designed to be extensible:

- New API endpoints can be added by creating new route functions
- New Socket.IO events can be added by creating new event handlers
- Different storage backends can be implemented by extending the DataStorage class
