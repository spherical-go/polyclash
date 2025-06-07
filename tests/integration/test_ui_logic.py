import pytest
import os
from PyQt5.QtCore import Qt
from polyclash.gui.main import MainWindow
from polyclash.game.controller import SphericalGoController
from polyclash.game.board import BLACK, WHITE
from polyclash.gui.dialogs import LocalGameDialog
from polyclash.game.player import HUMAN, AI
from polyclash.game.controller import LOCAL

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

    @pytest.mark.skipif(is_ci, reason="Skip UI tests in CI environment to avoid core dumps")
    def test_start_local_game_no_crash(self, qapp, qtbot):
        """Test starting a local game via the dialog doesn't crash and sets up correctly."""
        controller = SphericalGoController()
        main_window = MainWindow(controller=controller)
        qtbot.addWidget(main_window)

        dialog = LocalGameDialog(parent=main_window)
        qtbot.addWidget(dialog)
        dialog.show()

        qtbot.waitUntil(dialog.isVisible, timeout=1000)
        qtbot.waitUntil(dialog.isActiveWindow, timeout=1000)

        qtbot.mouseClick(dialog.start_button, Qt.LeftButton)

        qtbot.waitUntil(lambda: not dialog.isVisible(), timeout=1000)

        assert controller.mode == LOCAL
        assert controller.players[BLACK].kind == HUMAN
        assert controller.players[WHITE].kind == HUMAN
        assert controller.board.counter == 0
        assert controller.board.current_player == BLACK

        main_window.close()
