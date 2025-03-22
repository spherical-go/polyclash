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

    @patch('polyclash.server.storage.all_joined')
    @patch('polyclash.server.storage.get_role')
    def test_ready_endpoint(self, mock_get_role, mock_all_joined, client):
        """Test the /sphgo/ready endpoint."""
        # Mock the all_joined function to always return True
        mock_all_joined.return_value = True
        
        # Mock the get_role function to return 'black'
        mock_get_role.return_value = 'black'
        
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        data = response.get_json()
        black_key = data['black_key']
        
        # Join as black
        response = client.post('/sphgo/join', json={'token': black_key, 'role': 'black'})
        black_token = response.get_json()['token']
        
        # Then mark as ready
        response = client.post('/sphgo/ready', json={'token': black_token, 'role': 'black'})
        assert response.status_code == 200

    @patch('polyclash.server.storage.get_role')
    @patch('polyclash.server.valid_plays')
    def test_play_endpoint(self, mock_valid_plays, mock_get_role, client):
        """Test the /sphgo/play endpoint."""
        # Mock the get_role function to return 'black'
        mock_get_role.return_value = 'black'
        
        # Mock the valid_plays set to include any play
        mock_valid_plays.__contains__.return_value = True
        
        # First create a game
        response = client.post('/sphgo/new', json={'token': TEST_TOKEN})
        data = response.get_json()
        black_key = data['black_key']
        
        # Join as black
        response = client.post('/sphgo/join', json={'token': black_key, 'role': 'black'})
        black_token = response.get_json()['token']
        
        # Play a move
        response = client.post('/sphgo/play', json={'token': black_token, 'steps': 0, 'play': [0, 1, 2, 3, 4]})
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
