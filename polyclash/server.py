import secrets

from flask import Flask, jsonify, request
from flask_socketio import SocketIO, join_room, emit

from polyclash.data import decoder

secret_key = secrets.token_urlsafe(48)
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key
socketio = SocketIO(app)

token = secrets.token_urlsafe(24)

games = {}
black_keys = {}
white_keys = {}
audience_keys = {}
valid_plays = set([','.join([str(elm) for elm in key]) for key in decoder.keys()])


@app.route('/sphgo/new', methods=['POST'])
def new_game():
    try:
        data = request.get_json()
        token = data.get('token')
        if token != token:
            return jsonify({'status': 'invalid_token'}), 401

        game_id = secrets.token_urlsafe(24)
        black_key = secrets.token_urlsafe(24)
        white_key = secrets.token_urlsafe(24)
        audience_key = secrets.token_urlsafe(24)

        games[game_id] = {
            'keys': {'black': black_key, 'white': white_key, 'audience': audience_key},
            'players': {}, 'audiences': [], 'plays': []
        }

        return jsonify(game_id=game_id, black_key=black_key, white_key=white_key, audience_key=audience_key), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/sphgo/close', methods=['POST'])
def close_game():
    try:
        data = request.get_json()
        if token != data.get('token'):
            return jsonify({'status': 'invalid_token'}), 401

        game_id = data.get('game_id')
        if game_id in games:
            del games[game_id]
            return jsonify({'status': 'closed'}), 200
        else:
            return jsonify({'status': 'game_not_found'}), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/sphgo/play', methods=['POST'])
def play():
    try:
        data = request.get_json()
        game_id = data.get('game_id')
        player_id = data.get('player_id')
        steps = data.get('steps')
        play = data.get('play')

        if game_id not in games:
            return jsonify({'status': 'game_not_found'}), 404

        if player_id not in games[game_id]['players']:
            return jsonify({'status': 'player_not_found'}), 404

        if steps != len(games[game_id]['plays']) + 1:
            return jsonify({'status': 'steps_mismatch'}), 400

        # black is the first player and then take the odd steps
        if steps % 2 == 1 and games[game_id]['players'][player_id] != 'black':
            return jsonify({'status': 'invalid_player'}), 400

        # white is the second player and then take the even steps
        if steps % 2 == 0 and games[game_id]['players'][player_id] != 'white':
            return jsonify({'status': 'invalid_player'}), 400

        if play not in valid_plays:
            return jsonify({'status': 'invalid_play'}), 400

        games[game_id]['plays'].append(play)
        emit('board_change', {'steps': steps, 'play': play}, room=game_id)

        return jsonify({'status': 'played'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@socketio.on('join')
def on_join(data):
    try:
        game_id = data['game_id']
        role = data['role']
        key = data['key']

        if game_id not in games:
            emit('join', {'status': 'game_not_found'})
            return

        if key != games[game_id]['keys'][role]:
            emit('join', {'status': 'invalid_key'})
            return

        if role == 'black':
            if 'black' in games[game_id]['players']:
                emit('join', {'status': 'role_taken'})
                return
            player_id = secrets.token_urlsafe(24)
            games[game_id]['players'][player_id] = 'black'
            join_room(game_id)
            emit('join', {'status': 'joined', 'role': 'black', 'player_id': player_id, 'plays': games['plays']}, room=game_id)
            return

        if role == 'white':
            if 'white' in games[game_id]['players']:
                emit('join', {'status': 'role_taken'})
                return
            player_id = secrets.token_urlsafe(24)
            games[game_id]['players'][player_id] = 'white'
            join_room(game_id)
            emit('join', {'status': 'joined', 'role': 'white', 'player_id': player_id, 'plays': games['plays']}, room=game_id)
            return

        if role == 'audience':
            audience_id = secrets.token_urlsafe(24)
            games[game_id]['audiences'].append(audience_id)
            join_room(game_id)
            emit('join', {'status': 'joined', 'role': 'audience', 'audience_id': audience_id, 'plays': games['plays']}, room=game_id)
            return
    except Exception as e:
        emit('join', {'status': 'error', 'message': str(e)})


if __name__ == '__main__':
    print(f"Secret: {secret_key}")
    print(f"Token: {token}")
    socketio.run(app, host='localhost', port=5000, allow_unsafe_werkzeug=True, debug=True)

