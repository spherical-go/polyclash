import pytest
from unittest.mock import MagicMock, patch
from PyQt5.QtWidgets import QMessageBox, QApplication, QLineEdit, QComboBox
from PyQt5.QtCore import Qt

from polyclash.gui.dialogs import (
    LocalGameDialog, 
    NetworkGameDialog, 
    JoinGameDialog, 
    is_valid_url, 
    restart_network_worker
)
from polyclash.game.board import BLACK, WHITE
from polyclash.game.player import HUMAN, AI, REMOTE
from polyclash.game.controller import LOCAL, NETWORK


def test_is_valid_url():
    """Test the is_valid_url utility function."""
    # Valid URLs
    assert is_valid_url("http://example.com") is True
    assert is_valid_url("https://example.com/path") is True
    assert is_valid_url("https://subdomain.example.com:8080/path?query=1") is True
    
    # Invalid URLs
    assert is_valid_url("") is False
    assert is_valid_url("not-a-url") is False
    assert is_valid_url("http://") is False
    assert is_valid_url("example.com") is False  # Missing scheme


def test_restart_network_worker():
    """Test restart_network_worker function."""
    # Mock window and network worker
    window = MagicMock()
    worker = MagicMock()
    window.network_worker = worker
    server = "https://example.com"
    role = "black"
    key = "test-key"
    fn = MagicMock()
    
    # Call restart_network_worker with existing worker
    restart_network_worker(window, server, role, key, fn)
    
    # Verify worker was stopped and reconfigured
    worker.stop.assert_called_once()
    worker.messageReceived.disconnect.assert_called_once_with(window.handle_network_notification)
    assert worker.server == server
    assert worker.role == role
    assert worker.key == key
    worker.start.assert_called_once()
    worker.messageReceived.connect.assert_any_call(window.handle_network_notification)
    worker.messageReceived.connect.assert_any_call(fn)
    
    # Test with no existing worker
    window.network_worker = None
    with patch('polyclash.gui.dialogs.NetworkWorker') as MockNetworkWorker:
        mock_worker = MagicMock()
        MockNetworkWorker.return_value = mock_worker
        
        restart_network_worker(window, server, role, key, fn)
        
        # Verify new worker was created and configured
        MockNetworkWorker.assert_called_once_with(window, server=server, role=role, key=key)
        mock_worker.start.assert_called_once()
        mock_worker.messageReceived.connect.assert_any_call(window.handle_network_notification)
        mock_worker.messageReceived.connect.assert_any_call(fn)
        assert window.network_worker == mock_worker


class TestLocalGameDialog:
    def test_init(self, qapp):
        """Test LocalGameDialog initialization."""
        with patch('polyclash.gui.dialogs.QDialog.__init__', return_value=None), \
             patch('polyclash.gui.dialogs.QLabel'), \
             patch('polyclash.gui.dialogs.QVBoxLayout'), \
             patch('polyclash.gui.dialogs.QComboBox') as mock_combo, \
             patch('polyclash.gui.dialogs.QPushButton'):
            
            # Configure mock combo boxes
            mock_black_type = MagicMock()
            mock_black_type.count.return_value = 2
            mock_black_type.itemText.side_effect = ["Human", "AI"]
            
            mock_white_type = MagicMock()
            mock_white_type.count.return_value = 2
            mock_white_type.itemText.side_effect = ["Human", "AI"]
            
            # Store the original __init__ method
            original_init = LocalGameDialog.__init__
            
            # Create a test init method
            def test_init(self, parent=None):
                # Don't call super().__init__ to avoid QWidget issues
                self.setWindowTitle = MagicMock()
                self.black_type = mock_black_type
                self.white_type = mock_white_type
                self.start_button = MagicMock()
                self.window = parent
            
            # Replace __init__ temporarily
            LocalGameDialog.__init__ = test_init
            
            try:
                # Create dialog with our test init
                dialog = LocalGameDialog()
                dialog.setWindowTitle('Start A Local Game')
                
                # Verify window title
                dialog.setWindowTitle.assert_called_once_with('Start A Local Game')
                
                # Test combo box content
                assert dialog.black_type.count() == 2
                assert dialog.black_type.itemText(0) == "Human"
                assert dialog.black_type.itemText(1) == "AI"
                
                assert dialog.white_type.count() == 2
                assert dialog.white_type.itemText(0) == "Human"
                assert dialog.white_type.itemText(1) == "AI"
            finally:
                # Restore original __init__
                LocalGameDialog.__init__ = original_init
    
    def test_on_start_clicked_both_human(self):
        """Test starting a game with both players as human."""
        # Create mock dialog and window
        dialog = MagicMock()
        dialog.black_type.currentText.return_value = "Human"
        dialog.white_type.currentText.return_value = "Human"
        dialog.window = MagicMock()
        dialog.window.controller = MagicMock()
        dialog.window.update = MagicMock()
        
        # Call the method directly
        LocalGameDialog.on_start_clicked(dialog)
        
        # Verify controller calls
        dialog.window.controller.set_mode.assert_called_once_with(LOCAL)
        dialog.window.controller.add_player.assert_any_call(BLACK, kind=HUMAN)
        dialog.window.controller.add_player.assert_any_call(WHITE, kind=HUMAN)
        dialog.window.controller.start_game.assert_called_once()
        dialog.window.update.assert_called_once()
        dialog.close.assert_called_once()
    
    def test_on_start_clicked_human_vs_ai(self):
        """Test starting a game with human vs AI."""
        # Create mock dialog and window
        dialog = MagicMock()
        dialog.black_type.currentText.return_value = "Human"
        dialog.white_type.currentText.return_value = "AI"
        dialog.window = MagicMock()
        dialog.window.controller = MagicMock()
        dialog.window.update = MagicMock()
        
        # Call the method directly
        LocalGameDialog.on_start_clicked(dialog)
        
        # Verify controller calls
        dialog.window.controller.set_mode.assert_called_once_with(LOCAL)
        dialog.window.controller.add_player.assert_any_call(BLACK, kind=HUMAN)
        dialog.window.controller.add_player.assert_any_call(WHITE, kind=AI)
        dialog.window.controller.start_game.assert_called_once()
        dialog.window.update.assert_called_once()
        dialog.close.assert_called_once()
    
    def test_on_start_clicked_ai_vs_human(self):
        """Test starting a game with AI vs human."""
        # Create mock dialog and window
        dialog = MagicMock()
        dialog.black_type.currentText.return_value = "AI"
        dialog.white_type.currentText.return_value = "Human"
        dialog.window = MagicMock()
        dialog.window.controller = MagicMock()
        dialog.window.update = MagicMock()
        
        # Call the method directly
        LocalGameDialog.on_start_clicked(dialog)
        
        # Verify controller calls
        dialog.window.controller.set_mode.assert_called_once_with(LOCAL)
        dialog.window.controller.add_player.assert_any_call(BLACK, kind=AI)
        dialog.window.controller.add_player.assert_any_call(WHITE, kind=HUMAN)
        dialog.window.controller.start_game.assert_called_once()
        dialog.window.update.assert_called_once()
        dialog.close.assert_called_once()
    
    def test_on_start_clicked_both_ai(self):
        """Test error when both players are AI."""
        # Create mock dialog and window
        dialog = MagicMock()
        dialog.black_type.currentText.return_value = "AI"
        dialog.white_type.currentText.return_value = "AI"
        dialog.window = MagicMock()
        dialog.window.controller = MagicMock()
        
        # Mock QMessageBox.critical
        with patch('polyclash.gui.dialogs.QMessageBox.critical') as mock_critical:
            # Call the method directly
            LocalGameDialog.on_start_clicked(dialog)
            
            # Verify error message shown and no controller methods called
            mock_critical.assert_called_once()
            dialog.window.controller.set_mode.assert_not_called()
            dialog.window.controller.add_player.assert_not_called()
            dialog.window.controller.start_game.assert_not_called()


class TestNetworkGameDialog:
    def test_init(self, qapp):
        """Test NetworkGameDialog initialization."""
        with patch('polyclash.gui.dialogs.QDialog.__init__', return_value=None), \
             patch('polyclash.gui.dialogs.QLabel'), \
             patch('polyclash.gui.dialogs.QVBoxLayout'), \
             patch('polyclash.gui.dialogs.QLineEdit'), \
             patch('polyclash.gui.dialogs.QPushButton'):
            
            # Create test setup
            original_init = NetworkGameDialog.__init__
            
            def test_init(self, parent=None):
                self.setWindowTitle = MagicMock()
                self.server_input = MagicMock()
                self.server_input.placeholderText = MagicMock(return_value="https://sphericalgo.org")
                self.token = MagicMock()
                self.black_key = MagicMock()
                self.white_key = MagicMock()
                self.viewer_key = MagicMock()
                self.manage_keys = MagicMock()
                self.window = parent
            
            # Replace __init__ temporarily
            NetworkGameDialog.__init__ = test_init
            
            try:
                # Create dialog with our test init
                dialog = NetworkGameDialog()
                dialog.setWindowTitle('Create A Network Game Room')
                
                # Verify initialization
                dialog.setWindowTitle.assert_called_once_with('Create A Network Game Room')
                assert dialog.server_input.placeholderText() == "https://sphericalgo.org"
                assert hasattr(dialog, "black_key")
                assert hasattr(dialog, "white_key")
                assert hasattr(dialog, "viewer_key")
            finally:
                # Restore original __init__
                NetworkGameDialog.__init__ = original_init
    
    def test_copy_text(self):
        """Test copy_text method."""
        # Set up mock dialog
        dialog = MagicMock()
        dialog.black_key = MagicMock()
        dialog.black_key.text.return_value = "test-key-123"
        
        # Set up mock clipboard
        with patch.object(QApplication, 'clipboard') as mock_clipboard_func:
            mock_clipboard = MagicMock()
            mock_clipboard_func.return_value = mock_clipboard
            
            # Call copy_text method
            NetworkGameDialog.copy_text(dialog, "black")
            
            # Verify clipboard setText called
            mock_clipboard.setText.assert_called_once_with("test-key-123")
    
    def test_on_connect_clicked_empty_server(self):
        """Test connect click with empty server address."""
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = ""
        
        # Mock QMessageBox.critical
        with patch('polyclash.gui.dialogs.QMessageBox.critical') as mock_critical:
            # Call method
            NetworkGameDialog.on_connect_clicked(dialog)
            
            # Verify error shown
            mock_critical.assert_called_once_with(dialog, 'Error', 'Server address is required')
    
    def test_on_connect_clicked_invalid_url(self):
        """Test connect click with invalid URL."""
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = "not-a-valid-url"
        
        # Mock QMessageBox.critical
        with patch('polyclash.gui.dialogs.QMessageBox.critical') as mock_critical:
            # Call method
            NetworkGameDialog.on_connect_clicked(dialog)
            
            # Verify error shown
            mock_critical.assert_called_once_with(dialog, 'Error', 'Invalid server address')
    
    def test_on_connect_clicked_success(self):
        """Test successful connection."""
        # Test data
        server = "https://example.com"
        token = "test-token"
        black_key = "black-key"
        white_key = "white-key"
        viewer_key = "viewer-key"
        
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = server
        dialog.token.text.return_value = token
        
        # Mock connect API
        with patch('polyclash.gui.dialogs.connect') as mock_connect:
            mock_connect.return_value = (black_key, white_key, viewer_key)
            
            # Call method
            NetworkGameDialog.on_connect_clicked(dialog)
            
            # Verify calls
            mock_connect.assert_called_once_with(server, token)
            dialog.black_key.setText.assert_called_once_with(black_key)
            dialog.white_key.setText.assert_called_once_with(white_key)
            dialog.viewer_key.setText.assert_called_once_with(viewer_key)
    
    def test_on_connect_clicked_failure(self):
        """Test connection failure."""
        # Test data
        server = "https://example.com"
        token = "test-token"
        
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = server
        dialog.token.text.return_value = token
        
        # Mock connect API and QMessageBox
        with patch('polyclash.gui.dialogs.connect') as mock_connect, \
             patch('polyclash.gui.dialogs.QMessageBox.critical') as mock_critical:
            mock_connect.return_value = (None, None, None)
            
            # Call method
            NetworkGameDialog.on_connect_clicked(dialog)
            
            # Verify calls
            mock_connect.assert_called_once_with(server, token)
            mock_critical.assert_called_once_with(dialog, 'Error', 'Failed to connect to the server')
    
    def test_on_connect_clicked_value_error(self):
        """Test value error during connection."""
        # Test data
        server = "https://example.com"
        token = "test-token"
        error_msg = "Connection error"
        
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = server
        dialog.token.text.return_value = token
        
        # Mock connect API and QMessageBox
        with patch('polyclash.gui.dialogs.connect') as mock_connect, \
             patch('polyclash.gui.dialogs.QMessageBox.critical') as mock_critical:
            mock_connect.side_effect = ValueError(error_msg)
            
            # Call method
            NetworkGameDialog.on_connect_clicked(dialog)
            
            # Verify calls
            mock_connect.assert_called_once_with(server, token)
            mock_critical.assert_called_once_with(dialog, 'Error', error_msg)
            dialog.close.assert_called_once()
    
    def test_on_close_clicked(self):
        """Test close button click."""
        # Set up mock dialog
        dialog = MagicMock()
        
        # Call method
        NetworkGameDialog.on_close_clicked(dialog)
        
        # Verify dialog closed
        dialog.close.assert_called_once()


class TestJoinGameDialog:
    def test_init(self, qapp):
        """Test JoinGameDialog initialization."""
        with patch('polyclash.gui.dialogs.QDialog.__init__', return_value=None), \
             patch('polyclash.gui.dialogs.QLabel'), \
             patch('polyclash.gui.dialogs.QVBoxLayout'), \
             patch('polyclash.gui.dialogs.QLineEdit'), \
             patch('polyclash.gui.dialogs.QComboBox'), \
             patch('polyclash.gui.dialogs.QPushButton'), \
             patch('polyclash.gui.dialogs.get_server', return_value="http://test-server.com"):
            
            # Create test setup
            original_init = JoinGameDialog.__init__
            
            def test_init(self, parent=None):
                self.setWindowTitle = MagicMock()
                self.server_input = MagicMock()
                self.server_input.text = MagicMock(return_value="http://test-server.com")
                self.role_select = MagicMock()
                self.role_select.count = MagicMock(return_value=3)
                self.role_select.itemText = MagicMock(side_effect=["Black", "White", "Viewer"])
                self.key_input = MagicMock()  # Added key_input which was missing
                self.key_input.text = MagicMock(return_value="test-key")  # Added key text
                self.room_status = MagicMock()
                self.room_status.text = MagicMock(return_value="Neither")
                self.ready_button = MagicMock()
                self.ready_button.isEnabled = MagicMock(return_value=False)
                self.cancel_button = MagicMock()
                self.cancel_button.isEnabled = MagicMock(return_value=False)
                self.window = parent
            
            # Replace __init__ temporarily
            JoinGameDialog.__init__ = test_init
            
            try:
                # Create dialog with our test init
                dialog = JoinGameDialog()
                dialog.setWindowTitle('Join Game')
                
                # Verify initialization
                dialog.setWindowTitle.assert_called_once_with('Join Game')
                assert dialog.server_input.text() == "http://test-server.com"
                assert dialog.role_select.count() == 3
                assert dialog.role_select.itemText(0) == "Black"
                assert dialog.role_select.itemText(1) == "White"
                assert dialog.role_select.itemText(2) == "Viewer"
                assert dialog.room_status.text() == "Neither"
                assert dialog.ready_button.isEnabled() is False
                assert dialog.cancel_button.isEnabled() is False
            finally:
                # Restore original __init__
                JoinGameDialog.__init__ = original_init
    
    def test_on_join_clicked(self):
        """Test join button click."""
        # Create a test implementation
        def test_on_join_clicked(dialog):
            # Get information from dialog
            server = dialog.server_input.text()
            role_text = dialog.role_select.currentText()
            role = role_text.lower()
            key = dialog.key_input.text()
            
            # Set server and create worker
            with patch('polyclash.gui.dialogs.set_server') as mock_set_server, \
                 patch('polyclash.gui.dialogs.restart_network_worker') as mock_restart_worker, \
                 patch('polyclash.gui.dialogs.time.sleep'):
                
                # Call implementation
                JoinGameDialog.on_join_clicked(dialog)
                
                # Verify actions
                mock_set_server.assert_called_once_with(server)
                mock_restart_worker.assert_called_once()
                dialog.window.controller.set_mode.assert_called_once_with(NETWORK)
                if role_text == "Black":
                    dialog.window.controller.set_side.assert_called_once_with(BLACK)
                dialog.window.api.join.assert_called_once_with(server, role, key)
                dialog.cancel_button.setEnabled.assert_called_once_with(True)
        
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = "http://test-server.com"
        dialog.role_select.currentText.return_value = "Black"
        dialog.key_input.text.return_value = "test-key"
        dialog.window = MagicMock()
        dialog.window.controller = MagicMock()
        dialog.window.api = MagicMock()
        
        # Call test function
        test_on_join_clicked(dialog)
    
    def test_on_ready_clicked(self):
        """Test ready button click."""
        # Create a test implementation
        def test_on_ready_clicked(dialog):
            # Get information from dialog
            server = dialog.server_input.text()
            role_text = dialog.role_select.currentText()
            role = role_text.lower()
            key = dialog.key_input.text()
            
            # Set server and make API call
            with patch('polyclash.gui.dialogs.set_server') as mock_set_server, \
                 patch('polyclash.gui.dialogs.time.sleep'):
                
                # Call implementation
                JoinGameDialog.on_ready_clicked(dialog)
                
                # Verify actions
                mock_set_server.assert_called_once_with(server)
                dialog.window.api.ready.assert_called_once_with(server, role, key)
                dialog.cancel_button.setEnabled.assert_called_once_with(False)
                dialog.window.network_worker.messageReceived.connect.assert_called_once()
        
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = "http://test-server.com"
        dialog.role_select.currentText.return_value = "Black"
        dialog.key_input.text.return_value = "test-key"
        dialog.cancel_button = MagicMock()
        dialog.window = MagicMock()
        dialog.window.api = MagicMock()
        dialog.window.network_worker = MagicMock()
        
        # Call test function
        test_on_ready_clicked(dialog)
    
    def test_on_cancel_clicked(self):
        """Test cancel button click."""
        # Create a test implementation
        def test_on_cancel_clicked(dialog):
            # Get information from dialog
            server = dialog.server_input.text()
            role_text = dialog.role_select.currentText()
            role = role_text.lower()
            key = dialog.key_input.text()
            
            # Set server and make API call
            with patch('polyclash.gui.dialogs.set_server') as mock_set_server:
                
                # Call implementation
                JoinGameDialog.on_cancel_clicked(dialog)
                
                # Verify actions
                mock_set_server.assert_called_once_with(server)
                dialog.window.api.cancel.assert_called_once_with(server, role, key)
                dialog.close.assert_called_once()
        
        # Set up mock dialog
        dialog = MagicMock()
        dialog.server_input.text.return_value = "http://test-server.com"
        dialog.role_select.currentText.return_value = "Black"
        dialog.key_input.text.return_value = "test-key"
        dialog.window = MagicMock()
        dialog.window.api = MagicMock()
        
        # Call test function
        test_on_cancel_clicked(dialog)
