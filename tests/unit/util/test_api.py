import pytest
from unittest.mock import patch, MagicMock
from polyclash.util.api import connect, join, ready, play, close, set_player_token

class TestAPIFunctions:
    @patch('requests.post')
    def test_connect(self, mock_post):
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'black_key': 'test_black_key',
            'white_key': 'test_white_key',
            'viewer_key': 'test_viewer_key'
        }
        mock_post.return_value = mock_response
        
        # Test the connect function
        black_key, white_key, viewer_key = connect('http://test-server.com', 'test_token')
        
        # Verify the function called requests.post with the correct arguments
        mock_post.assert_called_once_with(
            'http://test-server.com/sphgo/new',
            json={'token': 'test_token'}
        )
        
        # Verify the function returned the correct values
        assert black_key == 'test_black_key'
        assert white_key == 'test_white_key'
        assert viewer_key == 'test_viewer_key'
    
    @patch('requests.post')
    def test_join(self, mock_post):
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test the join function
        result = join('http://test-server.com', 'black', 'test_token')
        
        # Verify the function called requests.post with the correct arguments
        mock_post.assert_called_once_with(
            'http://test-server.com/sphgo/join',
            json={'token': 'test_token', 'role': 'black'}
        )
        
        # Verify the function returned the correct value
        assert result == 'Ready'
    
    @patch('requests.post')
    def test_ready(self, mock_post):
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Test the ready function
        result = ready('http://test-server.com', 'black', 'test_token')
        
        # Verify the function called requests.post with the correct arguments
        mock_post.assert_called_once_with(
            'http://test-server.com/sphgo/ready',
            json={'token': 'test_token', 'role': 'black'}
        )
        
        # Verify the function returned the correct value
        assert result == 'Ready'
    
    @patch('requests.post')
    def test_play(self, mock_post):
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Set player token
        set_player_token('test_token')
        
        # Test the play function
        play('http://test-server.com', 1, [0, 1, 2])
        
        # Verify the function called requests.post with the correct arguments
        mock_post.assert_called_once_with(
            'http://test-server.com/sphgo/play',
            json={
                'token': 'test_token',
                'steps': 1,
                'play': [0, 1, 2]
            }
        )
    
    @patch('requests.post')
    def test_close(self, mock_post):
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Set game_token to None
        from polyclash.util.api import game_token, set_game_token
        set_game_token(None)
        
        # Test the close function with game_token set to None
        # It should not make a request
        close('http://test-server.com')
        mock_post.assert_not_called()
        
        # Set game_token to a value
        set_game_token('test_token')
        
        # Test the close function with game_token set
        close('http://test-server.com')
        mock_post.assert_called_once_with(
            'http://test-server.com/sphgo/close',
            json={'token': 'test_token'}
        )
