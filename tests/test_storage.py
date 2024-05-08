import pytest

import polyclash.server as server

from flask_socketio import SocketIO
from polyclash.util.storage import create_storage
from polyclash.server import app, server_token


server.storage = create_storage()


@pytest.fixture
def test_client():
    client = app.test_client()
    return client


@pytest.fixture
def socketio_client(test_client):
    socketio_client = SocketIO(app, client=test_client, async_mode='threading')
    socketio_client.init_app(app)
    return socketio_client.test_client(app)


@pytest.fixture
def storage():
    server.storage = create_storage(flag_redis=True)
    return server.storage


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


def test_play_game(storage, test_client, socketio_client):
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


if __name__ == '__main__':
    pytest.main()
