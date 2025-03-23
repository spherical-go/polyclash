import pytest
from polyclash.game.board import Board, BLACK, WHITE
from polyclash.game.controller import SphericalGoController
from polyclash.game.player import Player
import polyclash.server as server
from flask_socketio import SocketIO
from polyclash.util.storage import create_storage
from polyclash.server import app

# Set a fixed token for testing
TEST_TOKEN = "test_token_for_integration_tests"
# Patch the server token directly
server.server_token = TEST_TOKEN

@pytest.fixture
def empty_board():
    """Fixture for an empty board."""
    return Board()

@pytest.fixture
def controller():
    """Fixture for a controller with an empty board."""
    return SphericalGoController()

@pytest.fixture
def black_player():
    """Fixture for a black player."""
    return Player(BLACK)

@pytest.fixture
def white_player():
    """Fixture for a white player."""
    return Player(WHITE)

@pytest.fixture
def test_client():
    """Fixture for a Flask test client."""
    client = app.test_client()
    return client

@pytest.fixture
def socketio_client(test_client):
    """Fixture for a Socket.IO test client."""
    socketio_client = SocketIO(app, client=test_client, async_mode='threading')
    socketio_client.init_app(app)
    return socketio_client.test_client(app)

@pytest.fixture
def storage():
    """Fixture for storage with memory backend."""
    server.storage = create_storage(flag_redis=False)
    return server.storage

@pytest.fixture
def auth_handshake(test_client, storage):
    """Fixture for authentication handshake.
    
    This fixture creates a new game and returns the game data including keys and tokens.
    """
    # Create a new game
    response = test_client.post('/sphgo/new', json={'token': TEST_TOKEN})
    assert response.status_code == 200
    game_data = response.get_json()
    
    # Join as black
    response = test_client.post('/sphgo/join', json={'token': game_data['black_key'], 'role': 'black'})
    assert response.status_code == 200
    black_token = response.get_json()['token']
    
    # Join as white
    response = test_client.post('/sphgo/join', json={'token': game_data['white_key'], 'role': 'white'})
    assert response.status_code == 200
    white_token = response.get_json()['token']
    
    # Return all the data needed for tests
    return {
        'game_id': game_data['game_id'],
        'black_key': game_data['black_key'],
        'white_key': game_data['white_key'],
        'viewer_key': game_data['viewer_key'],
        'black_token': black_token,
        'white_token': white_token
    }
