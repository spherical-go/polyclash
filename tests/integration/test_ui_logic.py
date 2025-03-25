import pytest
import os
from PyQt5.QtCore import Qt
from polyclash.gui.main import MainWindow
from polyclash.game.controller import SphericalGoController
from polyclash.game.board import BLACK, WHITE

# Check if running in CI environment
is_ci = os.environ.get('CI') == 'true'

class TestUILogicIntegration:
    @pytest.mark.skipif(is_ci, reason="Skip UI tests in CI environment to avoid core dumps")
    def test_stone_placement_updates_ui(self, qapp, main_window):
        """Test that placing a stone updates the UI."""
        controller = main_window.controller
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.gameStarted.emit()
        
        # Mock the view_sphere's update method
        original_update = main_window.view_sphere.update
        update_called = False
        
        def mock_update():
            nonlocal update_called
            update_called = True
            original_update()
        
        main_window.view_sphere.update = mock_update
        
        # Place a stone
        controller.playerPlaced.emit(BLACK, 0)
        
        # Check that the board state is updated
        assert controller.board.board[0] == BLACK
        assert update_called == True

    @pytest.mark.skipif(is_ci, reason="Skip UI tests in CI environment to avoid core dumps")
    def test_game_start_updates_ui(self, qapp, main_window):
        """Test that starting a game updates the UI."""
        controller = main_window.controller
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        
        # Start the game
        controller.gameStarted.emit()
        
        # Check that the UI is updated
        assert main_window.update_status.called
        assert controller.board.current_player == BLACK

    @pytest.mark.skipif(is_ci, reason="Skip UI tests in CI environment to avoid core dumps")
    def test_game_end_updates_ui(self, qapp, main_window):
        """Test that ending a game updates the UI."""
        controller = main_window.controller
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.gameStarted.emit()
        
        # Reset the mock to clear any previous calls
        main_window.update_status.reset_mock()
        
        # End the game
        controller.gameEnded.emit()
        
        # Check that the UI is updated
        assert main_window.update_status.called

    @pytest.mark.skipif(is_ci, reason="Skip UI tests in CI environment to avoid core dumps")
    def test_player_switch_updates_ui(self, qapp, main_window):
        """Test that switching players updates the UI."""
        controller = main_window.controller
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.gameStarted.emit()
        
        # Reset the mock to clear any previous calls
        main_window.update_status.reset_mock()
        
        # Place a stone to switch players
        controller.playerPlaced.emit(BLACK, 0)
        
        # Check that the UI is updated
        assert main_window.update_status.called
        assert controller.board.current_player == WHITE
