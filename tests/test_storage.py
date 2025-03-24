import time
import pytest
import polyclash.server as server

from flask_socketio import SocketIO
from polyclash.util.storage import create_storage
from polyclash.server import app, server_token


def test_index_page(storage, test_client):
    result = test_client.get('/sphgo/')
    assert result.status_code == 200
    assert b'PolyClash' in result.data


def test_new_game(storage, test_client, socketio_client):
    result = test_client.post('/sphgo/new', json={'key': server_token})
    assert result.status_code == 200
    assert result.json['game_id']
    assert result.json['black_key']
    assert result.json['white_key']
    assert result.json['viewer_key']


def test_join_game(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/joined_status', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert not result1.json['status']['black']
    assert not result1.json['status']['white']

    result2 = test_client.post('/sphgo/joined_status', json={'token': result0.json['white_key']})
    assert result2.status_code == 200
    assert not result2.json['status']['black']
    assert not result2.json['status']['white']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result3.status_code == 200
    assert result3.json['status']['black']

    result4 = test_client.post('/sphgo/joined_status', json={'token': result0.json['black_key']})
    assert result4.status_code == 200
    assert result4.json['status']['black']
    assert not result4.json['status']['white']


def test_game_not_ready(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result2 = test_client.post('/sphgo/joined_status', json={'token': result0.json['black_key']})
    assert result2.status_code == 200
    assert result2.json['status']['black']
    assert not result2.json['status']['white']

    result3 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result3.status_code == 200
    assert not result3.json['status']['black']
    assert not result3.json['status']['white']


def test_game_ready(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result2 = test_client.post('/sphgo/joined_status', json={'token': result0.json['black_key']})
    assert result2.status_code == 200
    assert result2.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result4 = test_client.post('/sphgo/joined_status', json={'token': result0.json['white_key']})
    assert result4.status_code == 200
    assert result4.json['status']['black']
    assert result4.json['status']['white']

    result3 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result3.status_code == 200
    assert result3.json['status']['black']

    result6 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result6.status_code == 200
    assert result6.json['status']['black']


def test_game_ready2(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result2 = test_client.post('/sphgo/joined_status', json={'token': result0.json['black_key']})
    assert result2.status_code == 200
    assert result2.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result4 = test_client.post('/sphgo/joined_status', json={'token': result0.json['white_key']})
    assert result4.status_code == 200
    assert result4.json['status']['black']
    assert result4.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result6 = test_client.post('/sphgo/ready_status', json={'token': result0.json['black_key']})
    assert result6.status_code == 200
    assert result6.json['status']['black']
    assert not result6.json['status']['white']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result8 = test_client.post('/sphgo/ready_status', json={'token': result0.json['white_key']})
    assert result8.status_code == 200
    assert result8.json['status']['black']
    assert result8.json['status']['white']


def test_game_play(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 0, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 200

    result10 = test_client.post('/sphgo/play', json={'token': result0.json['white_key'], 'role': 'white', 'steps': 1, 'play': [0, 1, 2, 3, 4]})
    assert result10.status_code == 200


def test_game_play_wrong_turn1(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 0, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 200

    result10 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'white', 'steps': 1, 'play': [0, 1, 2, 3, 4]})
    assert result10.status_code == 400


def test_game_play_wrong_turn2(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 0, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 200

    result10 = test_client.post('/sphgo/play', json={'token': result0.json['white_key'], 'role': 'white', 'steps': 1, 'play': [0, 1, 2, 3, 4]})
    assert result10.status_code == 200

    result11 = test_client.post('/sphgo/play', json={'token': result0.json['white_key'], 'role': 'white', 'steps': 2, 'play': [10, 11, 12, 13, 14]})
    assert result11.status_code == 400


def test_game_play_wrong_steps1(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 1, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 400


def test_game_play_wrong_steps2(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 0, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 200

    result10 = test_client.post('/sphgo/play', json={'token': result0.json['white_key'], 'role': 'white', 'steps': 1, 'play': [0, 1, 2, 3, 4]})
    assert result10.status_code == 200

    result11 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 1, 'play': [10, 11, 12, 13, 14]})
    assert result11.status_code == 400


def test_game_play_no_hang(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 0, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 200

    result10 = test_client.post('/sphgo/play', json={'token': result0.json['white_key'], 'role': 'white', 'steps': 1, 'play': [0, 1, 2, 3, 4]})
    assert result10.status_code == 200

    result11 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 1, 'play': [10, 11, 12, 13, 14]})
    assert result11.status_code == 400

    result12 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 2, 'play': [10, 11, 12, 13, 14]})
    assert result12.status_code == 200


def test_game_close(storage, test_client, socketio_client):
    result0 = test_client.post('/sphgo/new', json={'key': server_token})
    assert result0.status_code == 200
    assert result0.json['black_key']
    assert result0.json['white_key']

    result1 = test_client.post('/sphgo/join', json={'token': result0.json['black_key']})
    assert result1.status_code == 200
    assert result1.json['status']['black']

    result3 = test_client.post('/sphgo/join', json={'token': result0.json['white_key']})
    assert result3.status_code == 200
    assert result3.json['status']['white']

    result5 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result5.status_code == 200
    assert result5.json['status']['black']

    result7 = test_client.post('/sphgo/ready', json={'token': result0.json['white_key']})
    assert result7.status_code == 200
    assert result7.json['status']['black']

    result9 = test_client.post('/sphgo/play', json={'token': result0.json['black_key'], 'role': 'black', 'steps': 0, 'play': [5, 6, 7, 8, 9]})
    assert result9.status_code == 200

    result10 = test_client.post('/sphgo/play', json={'token': result0.json['white_key'], 'role': 'white', 'steps': 1, 'play': [0, 1, 2, 3, 4]})
    assert result10.status_code == 200

    result11 = test_client.post('/sphgo/close', json={'token': result0.json['white_key']})
    assert result11.status_code == 200

    result12 = test_client.get('/sphgo/list')
    assert result0.json['game_id'] not in result12.json['rooms']


if __name__ == '__main__':
    pytest.main()
