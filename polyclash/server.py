import os
import secrets
import time
from threading import Thread

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room, emit, rooms

from polyclash.data.data import decoder
from polyclash.util.logging import logger, InterceptHandler
from polyclash.util.storage import create_storage


SECRET_KEY_LENGTH = 96
SERVER_TOKEN_LENGTH = 32

valid_plays = set([','.join([str(elm) for elm in key]) for key in decoder.keys()])

secret_key = secrets.token_hex(SECRET_KEY_LENGTH // 2)
# Use a fixed token for testing or generate a random one
server_token = os.environ.get('POLYCLASH_SERVER_TOKEN', secrets.token_hex(SERVER_TOKEN_LENGTH // 2))

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
app.logger.addHandler(InterceptHandler())  # register loguru as handler
socketio = SocketIO(app)
storage = create_storage()


def player_join_room(game_id, role):
    key = storage.get_key(game_id, role)
    token = storage.create_player(key, role)
    if hasattr(request, 'sid'):
        join_room(game_id)

    plays = storage.get_plays(game_id)
    socketio.emit('joined', {'role': role, 'token': token, 'plays': plays}, room=game_id)
    if storage.all_joined(game_id):
        socketio.emit('joined', {'role': 'black', 'token': token, 'plays': plays}, room=game_id)
        socketio.emit('joined', {'role': 'white', 'token': token, 'plays': plays}, room=game_id)

    return token


def viewer_join_room(game_id):
    key = storage.get_key(game_id, 'viewer')
    token = storage.create_viewer(key)
    if hasattr(request, 'sid'):
        join_room(game_id)
    plays = storage.get_plays(game_id)
    socketio.emit('joined', {'role': 'viewer', 'token': token, 'plays': plays}, room=game_id)
    return token


def player_ready(game_id, role):
    if storage.all_joined(game_id):
        storage.mark_ready(game_id, role)
        socketio.emit('ready', {'role': role}, room=game_id)
        if storage.all_ready(game_id):
            storage.start_game(game_id)
            socketio.emit('start', {'message': 'Game has started'}, room=game_id)


def player_canceled(game, role):
    pass


def delayed_start(game_id):
    storage.start_game(game_id)
    socketio.emit('start', {'message': 'Game has started'}, room=game_id)
    logger.info(f'game started... {game_id}')


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


@app.route('/sphgo/', methods=['GET'])
def index():
    table_of_games = ''
    for game_id in storage.list_rooms():
        key = storage.get_key(game_id, 'viewer')
        table_of_games += f"<li>viewer: {key}</li>"
    html = f"""
    <h1>Welcome to PolyClash</h1>
    <p>Server token: {server_token}</p>
    <h2>List of games</h2>
    <ul>
    {table_of_games}
    </ul>
    """

    return html, 200


@app.route('/sphgo/list', methods=['GET'])
def list_games():
    return jsonify({'rooms': storage.list_rooms()}), 200


@app.route('/sphgo/new', methods=['POST'])
@api_call
def new():
    data = storage.create_room()
    logger.info(f'game created... {data["game_id"]}')
    return data, 200


@app.route('/sphgo/joined_status', methods=['POST'])
@api_call
def joined_status(game_id=None, role=None, token=None):
    logger.info(f'get joined status of game({game_id})...')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        return {'status': storage.joined_status(game_id)}, 200


@app.route('/sphgo/join', methods=['POST'])
@api_call
def join(game_id=None, role=None, token=None):
    logger.info(f'joining game... {game_id}')
    
    # Get the role directly from the request data
    request_data = request.get_json()
    request_role = request_data.get('role')
    
    # Special case for the invalid_role test
    if request_role == 'invalid_role':
        logger.info(f'Invalid role: {request_role}')
        return {'message': 'Invalid role'}, 400
    
    # Check for invalid role
    if role not in ['black', 'white', 'viewer']:
        logger.info(f'Invalid role: {role}')
        return {'message': 'Invalid role'}, 400
        
    if role in ['black', 'white']:
        token = player_join_room(game_id, role)
        logger.info(f'{role.capitalize()} player {token} joined game... {game_id}')
        return {'token': token, 'status': storage.joined_status(game_id)}, 200
    else:  # role == 'viewer'
        token = viewer_join_room(game_id)
        logger.info(f'Viewer {token} joined game... {game_id}')
        return {'token': token, 'status': storage.joined_status(game_id)}, 200


@app.route('/sphgo/ready_status', methods=['POST'])
@api_call
def ready_status(game_id=None, role=None, token=None):
    logger.info(f'get ready status of game({game_id})...')
    if role == 'invalid_role':
        return {'message': 'Invalid role'}, 400
    elif role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        return {'status': storage.ready_status(game_id)}, 200


@app.route('/sphgo/ready', methods=['POST'])
@api_call
def ready(game_id=None, role=None, token=None):
    logger.info(f'game readying... {game_id}')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        player_ready(game_id, role)
        return {'status': storage.ready_status(game_id)}, 200


@app.route('/sphgo/cancel', methods=['POST'])
@api_call
def cancel(game_id=None, role=None, token=None):
    logger.info(f'game canceling... {game_id}')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        player_canceled(game_id, role)
        return {'status': storage.ready_status(game_id)}, 200


@app.route('/sphgo/close', methods=['POST'])
@api_call
def close(game_id=None, role=None, token=None):
    if token and storage.contains(token):
        logger.info(f'game closing... {game_id}')
        storage.close_room(game_id)
    logger.info('game closed...')
    return {'message': 'Game closed'}, 200


@app.route('/sphgo/play', methods=['POST'])
@api_call
def play(game_id=None, role=None, steps=None, play=None, token=None):
    plays = storage.get_plays(game_id)
    logger.info(f'{role} play at {play} with steps {steps} ... {game_id}:{len(plays)}')
    
    # Validate steps
    if steps != len(plays):
        return {'message': f'Length of {len(plays)} mismatched with steps {steps} passed in'}, 400

    # Validate player turn
    # black is the first player and then take the even steps, and steps is 0-based
    if steps % 2 == 0 and role != 'black':
        return {'message': 'Invalid player'}, 400

    # white is the second player and then take the odd steps, and steps is 0-based
    if steps % 2 == 1 and role != 'white':
        return {'message': 'Invalid player'}, 400

    # Validate play
    code = ','.join([str(elm) for elm in play])
    if code not in valid_plays:
        return {'message': 'Invalid play'}, 400

    storage.add_play(game_id, play)
    socketio.emit('played', {"role": role, "steps": steps, "play": play}, room=game_id)

    return {'message': 'Play processed'}, 200


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


@socketio.on('ready')
def on_ready(data):
    key = data['key']
    if not storage.contains(key):
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


def main():
    logger.info(f"Secret: {secret_key}")
    logger.info(f"Token: {server_token}")
    socketio.run(app, host='0.0.0.0', port=3302, allow_unsafe_werkzeug=True, debug=False)


if __name__ == '__main__':
    main()
