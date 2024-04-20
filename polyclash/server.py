import secrets

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room, emit

from polyclash.data.data import decoder

secret_key = secrets.token_hex(48)
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app)

token = secrets.token_hex(16)

games = {}
rooms = {}
valid_plays = set([','.join([str(elm) for elm in key]) for key in decoder.keys()])


@app.route('/sphgo/new', methods=['POST'])
def new_game():
    try:
        data = request.get_json()
        token = data.get('token')
        if token != token:
            return jsonify({'message': 'invalid token'}), 401

        game_id = secrets.token_hex(8)
        black_key = secrets.token_hex(8)
        white_key = secrets.token_hex(8)
        audience_key = secrets.token_hex(8)

        games[game_id] = {
            'keys': {'black': black_key, 'white': white_key, 'audience': audience_key},
            'players': {}, 'audiences': [], 'plays': []
        }
        rooms[black_key] = game_id
        rooms[white_key] = game_id
        rooms[audience_key] = game_id

        return jsonify(game_id=game_id, black_key=black_key, white_key=white_key, audience_key=audience_key), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/sphgo/close', methods=['POST'])
def close_game():
    try:
        data = request.get_json()
        if token != data.get('token'):
            return jsonify({'message': 'invalid token'}), 401

        game_id = data.get('game_id')
        if game_id in games:
            del rooms[games[game_id]['keys']['black']]
            del rooms[games[game_id]['keys']['white']]
            del rooms[games[game_id]['keys']['audience']]
            del rooms[games[game_id]['players']['black']]
            del rooms[games[game_id]['players']['white']]
            for audience_id in games[game_id]['audiences']:
                del rooms[audience_id]
            del games[game_id]
            return jsonify({'message': 'Game closed'}), 200
        else:
            return jsonify({'message': 'Game not found'}), 404
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@app.route('/sphgo/play', methods=['POST'])
def play():
    try:
        data = request.get_json()
        token = data['token']
        if token not in rooms:
            emit('error', {'message': 'Game not found'})
            return

        role = None
        game_id = rooms[token]
        if token == games[game_id]['players']['black']:
            role = 'black'
        elif token == games[game_id]['players']['white']:
            role = 'white'

        if role is None:
            return jsonify({'message': 'Invalid role'}), 400

        steps = data.get('steps')
        play = data.get('play')

        if steps != len(games[game_id]['plays']) + 1:
            return jsonify({'message': f'Length of {len(games[game_id]["plays"]) + 1} mismatched with steps {steps} passed in'}), 400

        # black is the first player and then take the odd steps
        if steps % 2 == 1 and role != 'black':
            return jsonify({'message': 'Invalid player'}), 400

        # white is the second player and then take the even steps
        if steps % 2 == 0 and role != 'white':
            return jsonify({'message': 'Invalid player'}), 400

        code = ','.join([str(elm) for elm in play])
        if code not in valid_plays:
            return jsonify({'message': 'Invalid play'}), 400

        games[game_id]['plays'].append(play)
        socketio.emit('played', {"role": role, "steps": steps, "play": play}, room=game_id)

        return jsonify({'message': 'Play processed'}), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500


@socketio.on('join')
def on_join(data):
    try:
        key = data['key']
        if key not in rooms:
            emit('error', {'message': 'Game not found'})
            return

        role = None
        game_id = rooms[key]
        if key == games[game_id]['keys']['black']:
            role = 'black'
        elif key == games[game_id]['keys']['white']:
            role = 'white'

        if role == 'black':
            if 'black' in games[game_id]['players']:
                emit('error', {'message': 'Role had been taken'})
                return
            player_id = secrets.token_urlsafe(24)
            rooms[player_id] = game_id
            games[game_id]['players']['black'] = player_id
            join_room(game_id)
            emit('joined', {'role': 'black', 'player': player_id, 'plays': games[game_id]['plays']}, room=game_id)
            return

        if role == 'white':
            if 'white' in games[game_id]['players']:
                emit('error', {'message': 'Role had been taken'})
                return
            player_id = secrets.token_urlsafe(24)
            rooms[player_id] = game_id
            games[game_id]['players']['white'] = player_id
            join_room(game_id)
            emit('joined', {'role': 'white', 'player': player_id, 'plays': games[game_id]['plays']}, room=game_id)
            return

        if role == 'audience':
            audience_id = secrets.token_urlsafe(24)
            rooms[audience_id] = game_id
            games[game_id]['audiences'].append(audience_id)
            join_room(game_id)
            emit('joined', {'role': 'audience', 'audience_id': audience_id, 'plays': games[game_id]['plays']}, room=game_id)
            return

        emit('error', {'message': 'Invalid role'})
    except Exception as e:
        emit('error', {'message': str(e)})


if __name__ == '__main__':
    print(f"Secret: {secret_key}")
    print(f"Token: {token}")
    socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True, debug=True)

