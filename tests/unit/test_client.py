from unittest.mock import MagicMock, patch

import polyclash.client as client


class TestClient:
    """Tests for the client module."""

    def test_main_function(self):
        """Test the main function in the client module."""
        # Mock dependencies
        with (
            patch("polyclash.client.SphericalGoController") as mock_controller,
            patch("polyclash.client.QApplication") as mock_app,
            patch("polyclash.client.MainWindow") as mock_window,
        ):
            # Setup return values
            mock_instance = MagicMock()
            mock_window.return_value = mock_instance

            # Setup QApplication.primaryScreen mocking
            mock_screen = MagicMock()
            mock_screen_geometry = MagicMock()
            mock_screen.primaryScreen.return_value.geometry.return_value = (
                mock_screen_geometry
            )
            mock_screen_geometry.width.return_value = 1000
            mock_screen_geometry.height.return_value = 800
            mock_app.return_value = mock_screen

            # Call the main function
            with patch("sys.argv", ["client.py"]):
                with patch("sys.exit"):  # Prevent actual exit
                    client.main()

            # Assert controller was initialized
            mock_controller.assert_called_once()

            # Assert window was created and shown
            mock_window.assert_called_once()
            mock_instance.show.assert_called_once()

            # Check controller configuration
            controller_instance = mock_controller.return_value
            assert controller_instance.add_player.call_count == 2
