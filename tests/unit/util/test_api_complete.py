import pytest
import requests
from unittest.mock import patch, MagicMock

import polyclash.util.api as api
from polyclash.util.api import (
    get_server, set_server, set_game_token, set_player_key, set_player_token, set_viewer_key,
    connect, get_game_status, joined_status, join, ready_status, ready, cancel, play, close
)


class TestAPIGlobals:
    """Test global variables and setter/getter functions."""
    
    def setup_method(self):
        """Reset global variables before each test."""
        api.shared_server = None
        api.game_token = None
        api.player_key = None
        api.viewer_key = None
        api.player_token = None
    
    def test_get_set_server(self):
        """Test setting and getting server."""
        assert get_server() is None
        
        set_server("http://example.com")
        assert get_server() == "http://example.com"
        
        set_server("http://otherserver.com")
        assert get_server() == "http://otherserver.com"
    
    def test_set_game_token(self):
        """Test setting game token."""
        assert api.game_token is None
        
        set_game_token("game123")
        assert api.game_token == "game123"
    
    def test_set_player_key(self):
        """Test setting player key."""
        assert api.player_key is None
        
        set_player_key("player123")
        assert api.player_key == "player123"
    
    def test_set_player_token(self):
        """Test setting player token."""
        assert api.player_token is None
        
        set_player_token("token123")
        assert api.player_token == "token123"
    
    def test_set_viewer_key(self):
        """Test setting viewer key."""
        assert api.viewer_key is None
        
        set_viewer_key("viewer123")
        assert api.viewer_key == "viewer123"


class TestAPIServerCommunication:
    """Test server communication functions."""
    
    def setup_method(self):
        """Reset global variables before each test."""
        api.shared_server = None
        api.game_token = None
        api.player_key = None
        api.viewer_key = None
        api.player_token = None
    
    @patch('polyclash.util.api.requests.post')
    def test_connect_success(self, mock_post):
        """Test successful connect operation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'black_key': 'black123',
            'white_key': 'white123',
            'viewer_key': 'viewer123'
        }
        mock_post.return_value = mock_response
        
        # Call connect
        black_key, white_key, viewer_key = connect('http://example.com', 'game123')
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/new',
            json={'token': 'game123'}
        )
        
        # Check globals are set
        assert get_server() == 'http://example.com'
        assert api.game_token == 'game123'
        
        # Check return values
        assert black_key == 'black123'
        assert white_key == 'white123'
        assert viewer_key == 'viewer123'
    
    @patch('polyclash.util.api.requests.post')
    def test_connect_error(self, mock_post):
        """Test connect operation with error response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid token'}
        mock_post.return_value = mock_response
        
        # Call connect and check error
        with pytest.raises(ValueError, match='Invalid token'):
            connect('http://example.com', 'game123')
        
        # Check globals are still set
        assert get_server() == 'http://example.com'
        assert api.game_token == 'game123'
    
    @patch('polyclash.util.api.requests.post')
    def test_connect_connection_error(self, mock_post):
        """Test connect operation with connection error."""
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError('Connection error')
        
        # Call connect and check error
        with pytest.raises(ValueError, match='Server not reachable when we start the game'):
            connect('http://example.com', 'game123')
    
    @patch('polyclash.util.api.requests.post')
    def test_get_game_status_both(self, mock_post):
        """Test get_game_status with both players."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {'black': True, 'white': True}
        }
        mock_post.return_value = mock_response
        
        # Call function
        result = get_game_status('joined', 'http://example.com', 'token123')
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/joined_status',
            json={'token': 'token123'}
        )
        
        # Check globals are set
        assert get_server() == 'http://example.com'
        assert api.player_token == 'token123'
        
        # Check result
        assert result == 'Both'
    
    @patch('polyclash.util.api.requests.post')
    def test_get_game_status_black(self, mock_post):
        """Test get_game_status with only black player."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {'black': True, 'white': False}
        }
        mock_post.return_value = mock_response
        
        # Call function
        result = get_game_status('joined', 'http://example.com', 'token123')
        
        # Check result
        assert result == 'Black'
    
    @patch('polyclash.util.api.requests.post')
    def test_get_game_status_white(self, mock_post):
        """Test get_game_status with only white player."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {'black': False, 'white': True}
        }
        mock_post.return_value = mock_response
        
        # Call function
        result = get_game_status('joined', 'http://example.com', 'token123')
        
        # Check result
        assert result == 'White'
    
    @patch('polyclash.util.api.requests.post')
    def test_get_game_status_neither(self, mock_post):
        """Test get_game_status with no players."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'status': {'black': False, 'white': False}
        }
        mock_post.return_value = mock_response
        
        # Call function
        result = get_game_status('joined', 'http://example.com', 'token123')
        
        # Check result
        assert result == 'Neither'
    
    def test_get_game_status_no_token(self):
        """Test get_game_status with no token."""
        result = get_game_status('joined', 'http://example.com', None)
        assert result == 'None'
    
    @patch('polyclash.util.api.requests.post')
    def test_get_game_status_error(self, mock_post):
        """Test get_game_status with error response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid token'}
        mock_post.return_value = mock_response
        
        # Call function and check error
        with pytest.raises(ValueError, match='Invalid token'):
            get_game_status('joined', 'http://example.com', 'token123')
    
    @patch('polyclash.util.api.get_game_status')
    def test_joined_status(self, mock_get_game_status):
        """Test joined_status calls get_game_status correctly."""
        mock_get_game_status.return_value = 'Both'
        
        result = joined_status('http://example.com', 'token123')
        
        mock_get_game_status.assert_called_once_with('joined', 'http://example.com', 'token123')
        assert result == 'Both'
    
    @patch('polyclash.util.api.requests.post')
    def test_join_success(self, mock_post):
        """Test successful join operation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call join
        result = join('http://example.com', 'black', 'token123')
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/join',
            json={'token': 'token123', 'role': 'black'}
        )
        
        # Check globals are set
        assert get_server() == 'http://example.com'
        assert api.player_token == 'token123'
        
        # Check result
        assert result == 'Ready'
    
    def test_join_no_token(self):
        """Test join with no token."""
        result = join('http://example.com', 'black', None)
        assert result is None
    
    @patch('polyclash.util.api.requests.post')
    def test_join_error(self, mock_post):
        """Test join with error response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid token'}
        mock_post.return_value = mock_response
        
        # Call join and check error
        with pytest.raises(ValueError, match='Invalid token'):
            join('http://example.com', 'black', 'token123')
    
    @patch('polyclash.util.api.get_game_status')
    def test_ready_status(self, mock_get_game_status):
        """Test ready_status calls get_game_status correctly."""
        mock_get_game_status.return_value = 'Both'
        
        result = ready_status('http://example.com', 'token123')
        
        mock_get_game_status.assert_called_once_with('ready', 'http://example.com', 'token123')
        assert result == 'Both'
    
    @patch('polyclash.util.api.requests.post')
    def test_ready_success(self, mock_post):
        """Test successful ready operation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call ready
        result = ready('http://example.com', 'black', 'token123')
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/ready',
            json={'token': 'token123', 'role': 'black'}
        )
        
        # Check globals are set
        assert get_server() == 'http://example.com'
        assert api.player_token == 'token123'
        
        # Check result
        assert result == 'Ready'
    
    def test_ready_no_token(self):
        """Test ready with no token."""
        result = ready('http://example.com', 'black', None)
        assert result is None
    
    @patch('polyclash.util.api.requests.post')
    def test_ready_error(self, mock_post):
        """Test ready with error response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid token'}
        mock_post.return_value = mock_response
        
        # Call ready and check error
        with pytest.raises(ValueError, match='Invalid token'):
            ready('http://example.com', 'black', 'token123')
    
    @patch('polyclash.util.api.requests.post')
    def test_cancel_success(self, mock_post):
        """Test successful cancel operation."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call cancel
        result = cancel('http://example.com', 'black', 'token123')
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/cancel',
            json={'token': 'token123', 'role': 'black'}
        )
        
        # Check globals are set
        assert get_server() == 'http://example.com'
        assert api.player_token == 'token123'
        
        # Check result
        assert result == 'Canceled'
    
    def test_cancel_no_token(self):
        """Test cancel with no token."""
        result = cancel('http://example.com', 'black', None)
        assert result is None
    
    @patch('polyclash.util.api.requests.post')
    def test_cancel_error(self, mock_post):
        """Test cancel with error response."""
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid token'}
        mock_post.return_value = mock_response
        
        # Call cancel and check error
        with pytest.raises(ValueError, match='Invalid token'):
            cancel('http://example.com', 'black', 'token123')
    
    @patch('polyclash.util.api.requests.post')
    def test_play_success(self, mock_post):
        """Test successful play operation."""
        # Set player token
        set_player_token('token123')
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call play
        play('http://example.com', 1, [0])
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/play',
            json={'token': 'token123', 'steps': 1, 'play': [0]}
        )
        
        # Check server is set
        assert get_server() == 'http://example.com'
    
    def test_play_no_token(self):
        """Test play with no player token."""
        with pytest.raises(ValueError, match='Player token not set'):
            play('http://example.com', 1, [0])
    
    @patch('polyclash.util.api.requests.post')
    def test_play_error(self, mock_post):
        """Test play with error response."""
        # Set player token
        set_player_token('token123')
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid move'}
        mock_post.return_value = mock_response
        
        # Call play and check error
        with pytest.raises(ValueError, match='Invalid move'):
            play('http://example.com', 1, [0])
    
    @patch('polyclash.util.api.requests.post')
    def test_play_connection_error(self, mock_post):
        """Test play with connection error."""
        # Set player token
        set_player_token('token123')
        
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError('Connection error')
        
        # Call play and check error
        with pytest.raises(ValueError, match='Server not reachable when we play the game'):
            play('http://example.com', 1, [0])
    
    @patch('polyclash.util.api.requests.post')
    def test_close_success(self, mock_post):
        """Test successful close operation."""
        # Set game token
        set_game_token('game123')
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response
        
        # Call close
        close('http://example.com')
        
        # Check request
        mock_post.assert_called_once_with(
            'http://example.com/sphgo/close',
            json={'token': 'game123'}
        )
    
    def test_close_no_token(self):
        """Test close with no game token."""
        # This should not raise an error, just return silently
        close('http://example.com')
    
    @patch('polyclash.util.api.requests.post')
    def test_close_error(self, mock_post):
        """Test close with error response."""
        # Set game token
        set_game_token('game123')
        
        # Mock response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {'message': 'Invalid token'}
        mock_post.return_value = mock_response
        
        # Call close and check error
        with pytest.raises(ValueError, match='Invalid token'):
            close('http://example.com')
    
    @patch('polyclash.util.api.requests.post')
    def test_close_connection_error(self, mock_post):
        """Test close with connection error."""
        # Set game token
        set_game_token('game123')
        
        # Mock connection error
        mock_post.side_effect = requests.exceptions.ConnectionError('Connection error')
        
        # Call close and check error
        with pytest.raises(ValueError, match='Server not reachable when we close the game'):
            close('http://example.com')
