from unittest.mock import Mock, patch

from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import SphericalGoController
from polyclash.game.player import AI, HUMAN
from polyclash.workers.ai_play import AIPlayerWorker


class TestAIIntegration:
    def test_ai_integration_with_controller(self):
        """Test integration of AI with game controller."""
        controller = SphericalGoController()

        # Add a human player (BLACK) and AI player (WHITE)
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=AI)

        # Start the game
        controller.start()

        # Set board's current player to WHITE (AI)
        controller.board.current_player = WHITE

        # Mock the player's auto_place method
        with patch.object(controller.players[WHITE], "auto_place") as mock_auto_place:
            # Let the AI player make a move
            ai_player = controller.get_current_player()
            ai_player.auto_place()

            # Verify the AI's auto_place method was called
            mock_auto_place.assert_called_once()

    def test_ai_worker_interaction_with_controller(self):
        """Test interaction between AI worker and game controller."""
        # Create a controller with players
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=AI)
        controller.start()

        # Get the AI player
        ai_player = controller.players[WHITE]

        # Create an AI worker
        worker = AIPlayerWorker(ai_player)

        # Mock methods to avoid actual thread execution
        worker.start = Mock()
        worker.wake_up = Mock()
        worker.trigger = Mock()

        # Call step to simulate AI worker activation
        worker.step()

        # Verify worker interactions
        assert worker.is_running
        worker.start.assert_called_once()
        worker.wake_up.assert_called_once()
        worker.trigger.emit.assert_called_once()
