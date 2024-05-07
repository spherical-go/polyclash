import json

import pytest

from time import sleep
from flask_socketio import socketio, SocketIO
from polyclash.server import app, server_token


@pytest.fixture
def test_client():
    client = app.test_client()
    return client


@pytest.fixture
def socketio_client(test_client):
    socketio_client = SocketIO(app, client=test_client, async_mode='threading')
    socketio_client.init_app(app)
    return socketio_client.test_client(app)


def test_new_game(test_client, socketio_client):
    result = test_client.post('/sphgo/new', json={'key': server_token})
    assert result.status_code == 200
    assert result.json['game_id']
    assert result.json['black_key']
    assert result.json['white_key']
    assert result.json['viewer_key']


def test_join_game(test_client, socketio_client):
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


def test_game_not_ready(test_client, socketio_client):
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

    result3 = test_client.post('/sphgo/ready', json={'token': result0.json['black_key']})
    assert result3.status_code == 200
    assert not result3.json['status']['black']


def test_game_ready(test_client, socketio_client):
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


def test_play_game(test_client, socketio_client):
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

    result6 = test_client.post('/sphgo/ready_status', json={'token': result0.json['white_key']})
    assert result6.status_code == 200
    assert result6.json['status']['black']
    assert result6.json['status']['white']


if __name__ == '__main__':
    pytest.main()
