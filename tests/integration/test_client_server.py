import pytest
import os
import secrets
from unittest.mock import patch, MagicMock

# Import the server module
from polyclash.server import app
import polyclash.server
from polyclash.util.api import connect, join, ready, play, close

# Set a fixed token for testing
TEST_TOKEN = "test_token_for_integration_tests"

# Patch the server token directly
polyclash.server.server_token = TEST_TOKEN

class TestClientServerIntegration:
    def test_new_game_endpoint(self, client):
        """Test the /sphgo/new endpoint."""
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        assert response.status_code == 200
        data = response.get_json()
        assert 'game_id' in data
        assert 'black_key' in data
        assert 'white_key' in data
        assert 'viewer_key' in data

    def test_join_endpoint(self, client):
        """Test the /sphgo/join endpoint."""
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        data = response.get_json()
        black_key = data['black_key']
        
        # Then join as black
        response = client.post('/sphgo/join', json={'token': black_key, 'role': 'black'})
        assert response.status_code == 200
        data = response.get_json()
        assert 'token' in data

    def test_ready_endpoint(self, client):
        """Test the /sphgo/ready endpoint."""
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        data = response.get_json()
        black_key = data['black_key']
        
        # Then join as black
        response = client.post('/sphgo/join', json={'token': black_key, 'role': 'black'})
        black_token = response.get_json()['token']
        
        # Then mark as ready
        response = client.post('/sphgo/ready', json={'token': black_token, 'role': 'black'})
        assert response.status_code == 200

    def test_play_endpoint(self, client):
        """Test the /sphgo/play endpoint."""
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        data = response.get_json()
        black_key = data['black_key']
        white_key = data['white_key']
        
        # Then join as black and white
        response = client.post('/sphgo/join', json={'token': black_key, 'role': 'black'})
        black_token = response.get_json()['token']
        response = client.post('/sphgo/join', json={'token': white_key, 'role': 'white'})
        white_token = response.get_json()['token']
        
        # Then mark both as ready
        client.post('/sphgo/ready', json={'token': black_token, 'role': 'black'})
        client.post('/sphgo/ready', json={'token': white_token, 'role': 'white'})
        
        # Then play a move
        response = client.post('/sphgo/play', json={'token': black_token, 'steps': 0, 'play': [0]})
        assert response.status_code == 200

    def test_close_endpoint(self, client):
        """Test the /sphgo/close endpoint."""
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        
        # Then close it
        response = client.post('/sphgo/close', json={'token': TEST_TOKEN})
        assert response.status_code == 200

class TestClientServerErrorHandling:
    def test_invalid_token(self, client):
        """Test error handling for invalid tokens."""
        response = client.post('/sphgo/join', json={'token': 'invalid_token', 'role': 'black'})
        assert response.status_code == 401
        
    def test_invalid_role(self, client):
        """Test error handling for invalid roles."""
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        data = response.get_json()
        black_key = data['black_key']
        
        # Then try to join with an invalid role
        response = client.post('/sphgo/join', json={'token': black_key, 'role': 'invalid_role'})
        assert response.status_code == 400
