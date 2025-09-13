from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow

from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import SphericalGoController


@pytest.fixture
def mock_controller():
    """Create a mock SphericalGoController."""
    controller = MagicMock(spec=SphericalGoController)
    controller.board = MagicMock()
    controller.board.register_observer = MagicMock()
    controller.side = BLACK
    controller.players = []
    return controller


# Create a test class instead of patching MainWindow to avoid the QWidget initialization issues
class TestMainWindow:
    def test_handle_network_notification(self, mock_controller):
        """Test network event handling."""
        # Create mocks for all components we need to test
        status_bar = MagicMock()

        # Create test cases
        test_cases = [
            ("error", {"message": "Test error"}, "Error: Test error"),
            (
                "joined",
                {"role": "black", "token": "test-token"},
                "Black player joined...",
            ),
            ("ready", {"role": "white"}, "White player is ready..."),
            ("start", {}, "Game has started."),
            (
                "played",
                {"role": "black", "steps": 0, "play": [0]},
                "Black player played...",
            ),
        ]

        # Import the handle_network_notification function
        from polyclash.gui.main import MainWindow

        # Create a minimal instance with just the attributes we need for this test
        main_window = MagicMock()
        main_window.controller = mock_controller
        main_window.status_bar = status_bar

        # Test each case
        for event, data, expected_message in test_cases:
            # Special setup for 'start' event
            if event == "start":
                mock_controller.start = MagicMock()

            # Special setup for 'played' event
            if event == "played":
                mock_controller.board.counter = 0
                mock_controller.play = MagicMock()

            # Call the method directly
            MainWindow.handle_network_notification(main_window, event, data)

            # Check status bar message
            status_bar.showMessage.assert_called_with(expected_message)

            # Additional checks for specific events
            if event == "start":
                mock_controller.start.assert_called_once()

            if event == "played" and data["steps"] == mock_controller.board.counter:
                if data["role"] == "black" and BLACK != mock_controller.side:
                    mock_controller.play.assert_called()

    def test_delayed_resize(self):
        """Test delayed resize functionality."""
        # Create mock window
        main_window = MagicMock()

        # Import MainWindow to get access to delayed_resize method
        from polyclash.gui.main import MainWindow

        # Test delayed_resize with mocked QTimer
        with patch("polyclash.gui.main.QTimer.singleShot") as mock_timer:
            MainWindow.delayed_resize(main_window, 800, 600)

            # Check if QTimer.singleShot was called
            assert mock_timer.called

            # Extract and call the callback
            args, _ = mock_timer.call_args
            callback = args[1]
            callback()

            # Check if resize was called with correct dimensions
            main_window.resize.assert_called_with(800, 600)
            main_window.update.assert_called_once()

    def test_new_game(self):
        """Test new game dialog."""
        main_window = MagicMock()

        with patch("polyclash.gui.main.NetworkGameDialog") as mock_dialog:
            mock_instance = MagicMock()
            mock_dialog.return_value = mock_instance

            # Import MainWindow to get access to newGame method
            from polyclash.gui.main import MainWindow

            # Call the method
            MainWindow.newGame(main_window)

            # Verify dialog was created and shown
            mock_dialog.assert_called_once_with(main_window)
            mock_instance.exec_.assert_called_once()

    def test_about(self):
        """Test about dialog."""
        main_window = MagicMock()

        with patch("polyclash.gui.main.QMessageBox.about") as mock_about:
            # Import MainWindow to get access to about method
            from polyclash.gui.main import MainWindow

            # Call the method
            MainWindow.about(main_window)

            # Verify dialog was shown
            mock_about.assert_called_once()
            args, _ = mock_about.call_args
            assert args[0] == main_window
            assert args[1] == "About"
            assert "PolyClash" in args[2]
