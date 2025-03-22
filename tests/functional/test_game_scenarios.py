import pytest
from polyclash.game.controller import SphericalGoController
from polyclash.game.board import BLACK, WHITE
from polyclash.game.player import HUMAN, AI

class TestCompleteGameScenarios:
    def test_human_vs_human_game(self):
        """Test a complete game between two human players."""
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=HUMAN)
        controller.gameStarted.emit()
        
        # Play a few moves
        controller.play(BLACK, 0)
        controller.play(WHITE, 1)
        controller.play(BLACK, 2)
        controller.play(WHITE, 3)
        
        # Check game state
        assert controller.board.counter == 4
        assert controller.board.board[0] == BLACK
        assert controller.board.board[1] == WHITE
        assert controller.board.board[2] == BLACK
        assert controller.board.board[3] == WHITE
        assert controller.board.current_player == BLACK

    def test_human_vs_ai_game(self):
        """Test a game between a human and AI player."""
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=AI)
        controller.gameStarted.emit()
        
        # Play a move as human
        controller.play(BLACK, 0)
        
        # AI should have automatically played
        assert controller.board.counter >= 2
        assert controller.board.board[0] == BLACK
        assert controller.board.current_player == BLACK

    def test_game_ending_conditions(self):
        """Test game ending conditions."""
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=HUMAN)
        controller.gameStarted.emit()
        
        # Mock the board's is_game_over method to return True
        original_is_game_over = controller.board.is_game_over
        controller.board.is_game_over = lambda: True
        
        # Check that the game is over
        assert controller.is_game_over() == True
        
        # Restore the original method
        controller.board.is_game_over = original_is_game_over

    def test_scoring(self):
        """Test game scoring."""
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=HUMAN)
        controller.gameStarted.emit()
        
        # Play a few moves to create a specific board state
        controller.play(BLACK, 0)
        controller.play(WHITE, 10)
        controller.play(BLACK, 1)
        controller.play(WHITE, 11)
        
        # Calculate the score
        black_score, white_score, unclaimed = controller.board.score()
        
        # Check that the scores are calculated correctly
        assert black_score >= 0
        assert white_score >= 0
        assert unclaimed >= 0
        assert abs(black_score + white_score + unclaimed - 1.0) < 0.001  # Sum should be close to 1.0

    def test_capture(self):
        """Test stone capture mechanics."""
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        controller.add_player(WHITE, kind=HUMAN)
        controller.gameStarted.emit()
        
        # Create a capture situation
        # This depends on the specific board topology
        # For this test, we'll use a simple example where a white stone is surrounded by black stones
        
        # Place a white stone
        controller.play(BLACK, 0)
        controller.play(WHITE, 1)
        
        # Surround it with black stones
        # We need to know the neighbors of position 1
        neighbors = controller.board.neighbors[1]
        for neighbor in neighbors:
            if neighbor != 0:  # Skip the position where we already placed a black stone
                try:
                    if controller.board.current_player == BLACK:
                        controller.play(BLACK, neighbor)
                    else:
                        controller.play(WHITE, 2)  # Play somewhere else
                        controller.play(BLACK, neighbor)
                except ValueError:
                    # Skip if the move is invalid (e.g., suicide)
                    pass
        
        # Check if the white stone was captured
        assert controller.board.board[1] == 0  # Position should be empty after capture
