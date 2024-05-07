import secrets
import time
import logging
from threading import Thread

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room, emit, rooms

from polyclash.data.data import decoder
from polyclash.util.logging import logger

SECRET_KEY_LENGTH = 96
SERVER_TOKEN_LENGTH = 32
USER_KEY_LENGTH = 16
USER_TOKEN_LENGTH = 48
GAME_ID_LENGTH = 64

secret_key = secrets.token_hex(SECRET_KEY_LENGTH // 2)
server_token = secrets.token_hex(SERVER_TOKEN_LENGTH // 2)

app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app)


class InterceptHandler(logging.Handler):
    def emit(self, record):
        logger_opt = logger.opt(depth=6, exception=record.exc_info)
        logger_opt.log(record.levelno, record.getMessage())


# register loguru as handler
app.logger.addHandler(InterceptHandler())


games = {}
rooms = {}
valid_plays = set([','.join([str(elm) for elm in key]) for key in decoder.keys()])


def get_role(key_or_tooken):
    if key_or_tooken in rooms:
        game_id = rooms[key_or_tooken]
        if key_or_tooken == games[game_id]['keys']['black']:
            return 'black'
        elif key_or_tooken == games[game_id]['keys']['white']:
            return 'white'
        elif key_or_tooken == games[game_id]['keys']['viewer']:
            return 'viewer'
    raise ValueError('Invalid key or token')


def get_opponent(role):
    if role == 'black':
        return 'white'
    if role == 'white':
        return 'black'
    return None


def player_join_room(game, role):
    if role in game['players']:
        return game['players'][role]
    token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
    rooms[token] = game['id']
    game['players'][role] = token
    game['joined'][role] = True
    if hasattr(request, 'sid'):
        join_room(game['id'])
    socketio.emit('joined', {'role': role, 'token': token, 'plays': game['plays']}, room=game['id'])

    if all(game['joined'].values()):
        socketio.emit('joined', {'role': 'black', 'token': token, 'plays': game['plays']}, room=game['id'])
        socketio.emit('joined', {'role': 'white', 'token': token, 'plays': game['plays']}, room=game['id'])

    return token


def viewer_join_room(game):
    token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
    rooms[token] = game['id']
    game['viewers'].append(token)
    join_room(game['id'])
    socketio.emit('joined', {'role': 'viewer', 'token': token, 'plays': game['plays']}, room=game['id'])
    return token


def player_ready(game, role):
    if all(game['joined'].values()):
        game['ready'][role] = True
        socketio.emit('ready', {'role': role}, room=game['id'])
        if all(game['ready'].values()):
            game['started'] = True
            socketio.emit('start', {'message': 'Game has started'}, room=game['id'])


def player_canceled(game, role):
    pass


def delayed_start(game_id):
    time.sleep(3)
    games[game_id]['started'] = True
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
                if token not in rooms:
                    return jsonify({'message': 'invalid token'}), 401

                game_id = rooms[token]
                if game_id not in games:
                    return jsonify({'message': 'Game not found'}), 404

                for key, value in data.items():
                    kwargs[key] = value

                game = games[game_id]
                role = get_role(token)
                kwargs['game'] = game
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
    for game_id, game in games.items():
        table_of_games += f"<li>black: {game['keys']['black']}; white: {game['keys']['white']}; viewer: {game['keys']['viewer']}</li>"
    html = f"""
    <h1>Welcome to PolyClash</h1>
    <p>Token: {server_token}</p>
    <h2>List of games</h2>
    <ul>
    {table_of_games}
    </ul>
    """

    return html, 200


@app.route('/sphgo/new', methods=['POST'])
@api_call
def new():
    game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
    black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
    white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
    viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

    logger.info(f'creating game... {game_id}')
    games[game_id] = {
        'id': game_id,
        'keys': {'black': black_key, 'white': white_key, 'viewer': viewer_key},
        'players': {}, 'viewers': [], 'plays': [],
        'joined': {'black': False, 'white': False},
        'ready': {'black': False, 'white': False},
    }
    rooms[black_key] = game_id
    rooms[white_key] = game_id
    rooms[viewer_key] = game_id
    logger.info(f'game created... {game_id}')

    return dict(game_id=game_id, black_key=black_key, white_key=white_key, viewer_key=viewer_key), 200


@app.route('/sphgo/joined_status', methods=['POST'])
@api_call
def joined_status(game=None, role=None, token=None):
    logger.info(f'get joined status of game({game["id"]})...')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        return {'status': game['joined']}, 200


@app.route('/sphgo/join', methods=['POST'])
@api_call
def join(game=None, role=None, token=None):
    logger.info(f'joining game... {game["id"]}')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        player_join_room(game, role)
        logger.info(f'joined game... {game["id"]}')
        return {'status': game['joined']}, 200


@app.route('/sphgo/ready_status', methods=['POST'])
@api_call
def ready_status(game=None, role=None, token=None):
    logger.info(f'get ready status of game({game["id"]})...')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        return {'status': game['ready']}, 200


@app.route('/sphgo/ready', methods=['POST'])
@api_call
def ready(game=None, role=None, token=None):
    logger.info(f'game readying... {game["id"]}')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        player_ready(game, role)
        return {'status': game['ready']}, 200
    logger.info(f'game ready... {game["id"]}')


@app.route('/sphgo/cancel', methods=['POST'])
@api_call
def cancel(game=None, role=None, token=None):
    logger.info(f'game canceling... {game["id"]}')
    if role not in ['black', 'white']:
        return {'message': 'Invalid role'}, 400
    else:
        player_canceled(game, role)
        return {'status': game['ready']}, 200
    logger.info(f'game canceled... {game["id"]}')


@app.route('/sphgo/close', methods=['POST'])
@api_call
def close(game=None, role=None, token=None):
    if game:
        logger.info(f'game closing... {game["id"]}')
        del rooms[game['keys']['black']]
        del rooms[game['keys']['white']]
        del rooms[game['keys']['viewer']]
        del rooms[game['players']['black']]
        del rooms[game['players']['white']]
        for viewer_id in game['viewers']:
            del rooms[viewer_id]
        del games[game['id']]
    logger.info('game closed...')
    return {'message': 'Game closed'}, 200


@app.route('/sphgo/play', methods=['POST'])
@api_call
def play(game=None, role=None, steps=None, play=None, token=None):
    logger.info(f'{role} play at {play} with steps {steps} ... {game["id"]}:{len(game["plays"])}')
    if steps != len(game['plays']):
        return {'message': f'Length of {len(game["plays"])} mismatched with steps {steps} passed in'}, 400

    # black is the first player and then take the even steps, and steps is 0-based
    if steps % 2 == 0 and role != 'black':
        return {'message': 'Invalid player'}, 400

    # white is the second player and then take the odd steps, and steps is 0-based
    if steps % 2 == 1 and role != 'white':
        return {'message': 'Invalid player'}, 400

    code = ','.join([str(elm) for elm in play])
    if code not in valid_plays:
        return {'message': 'Invalid play'}, 400

    game['plays'].append(play)
    socketio.emit('played', {"role": role, "steps": steps, "play": play}, room=game['id'])

    return {'message': 'Play processed'}, 200


@socketio.on('join')
def on_join(data):
    logger.info(f'event join... {str(data)}')
    try:
        key = data['key']
        if key not in rooms:
            logger.error(f'error in event join... game({key}) not found')
            emit('error', {'message': 'Game not found'})
            return
        game_id = rooms[key]
        game = games[game_id]
        role = get_role(key)

        if role in ['black', 'white']:
            player_join_room(game, role)
        if role == 'viewer':
            viewer_join_room(game)
    except Exception as e:
        logger.error(f'error in event join... unknown error {str(e)}')
        logger.exception('error in event join...', exc_info=e)
        emit('error', {'message': str(e)})


@socketio.on('joined')
def on_joined(data):
    pass


@socketio.on('ready')
def on_ready(data):
    key = data['key']
    if key not in rooms:
        emit('error', {'message': 'Game not found'})
        return

    game_id = rooms[key]
    role = None
    if key == games[game_id]['keys']['black']:
        role = 'black'
    elif key == games[game_id]['keys']['white']:
        role = 'white'

    if role in ['black', 'white']:
        games[game_id]['ready'][role] = True
        emit('ready', {'role': role}, room=game_id)

        # Check if all required players are ready
        if all(games[game_id]['ready'].values()):
            delayed_thread = Thread(target=delayed_start, args=(game_id,))
            delayed_thread.start()


@socketio.on('start')
def on_start(data):
    pass


@socketio.on('play')
def on_play(data):
    pass


if __name__ == '__main__':
    logger.info(f"Secret: {secret_key}")
    logger.info(f"Token: {server_token}")
    socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True, debug=True)
