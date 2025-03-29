import pytest
import numpy as np
from unittest.mock import Mock

from polyclash.game.board import Board, BLACK, WHITE, calculate_area, calculate_distance, calculate_potential, SimulatedBoard
from polyclash.data.data import neighbors, decoder

class TestBoardSwitchPlayer:
    """Tests for the switch_player method."""
    
    def test_switch_player_from_black(self):
        """Test switching player from BLACK to WHITE."""
        board = Board()
        assert board.current_player == BLACK
        
        board.switch_player()
        
        assert board.current_player == WHITE
    
    def test_switch_player_from_white(self):
        """Test switching player from WHITE to BLACK."""
        board = Board()
        board.current_player = WHITE
        
        board.switch_player()
        
        assert board.current_player == BLACK
    
    def test_switch_player_with_observer(self):
        """Test that switching player notifies observers."""
        board = Board()
        # Create a mock observer
        mock_observer = Mock()
        board.register_observer(mock_observer)
        
        board.switch_player()
        
        # Verify the observer was notified
        mock_observer.handle_notification.assert_called_with("switch_player", side=WHITE)


class TestBoardGetEmpties:
    """Tests for the get_empties method."""
    
    def test_get_empties_initial(self):
        """Test getting empty points on an initial board."""
        board = Board()
        empties = board.get_empties(BLACK)
        
        assert len(empties) == 302
        assert set(empties) == set(range(302))
    
    def test_get_empties_with_stones(self):
        """Test getting empty points on a board with stones."""
        board = Board()
        board.board[10] = BLACK
        board.board[11] = WHITE
        
        empties = board.get_empties(BLACK)
        
        assert len(empties) == 300
        assert 10 not in empties
        assert 11 not in empties
    
    def test_get_empties_with_ko(self):
        """Test getting empty points with a ko situation."""
        board = Board()
        # Setup a ko situation
        board.latest_removes.append([42])  # Simulating a ko point
        
        empties = board.get_empties(BLACK)
        
        assert 42 not in empties
    
    def test_get_empties_with_suicides(self):
        """Test getting empty points with suicide points."""
        board = Board()
        # Add some suicide points
        board.black_suicides.add(20)
        board.white_suicides.add(21)
        
        black_empties = board.get_empties(BLACK)
        white_empties = board.get_empties(WHITE)
        
        assert 20 not in black_empties
        assert 21 not in white_empties
        assert 20 in white_empties
        assert 21 in black_empties


class TestBoardScore:
    """Tests for the score method."""
    
    def test_score_empty_board(self):
        """Test scoring an empty board."""
        board = Board()
        black, white, unclaimed = board.score()
        
        # On an empty board, no territories are claimed
        assert black == 0
        assert white == 0
        assert abs(unclaimed - 1.0) < 1e-10  # Allow for floating point precision
    
    def test_score_with_stones(self):
        """Test scoring a board with some stones but no territories."""
        board = Board()
        # Place some stones but don't complete territories
        board.board[10] = BLACK
        board.board[20] = BLACK
        board.board[30] = WHITE
        board.board[40] = WHITE
        
        black, white, unclaimed = board.score()
        
        # Only stones, no territories claimed yet
        assert black > 0
        assert white > 0
        assert unclaimed < 1.0
        assert round(black + white + unclaimed, 6) == 1.0  # Total should be 1.0
    
    def test_score_with_territories(self):
        """Test scoring with claimed territories."""
        board = Board()
        # Identify a face from polysmalls to claim
        from polyclash.data.data import polysmalls
        if len(polysmalls) > 0:  # Make sure there are faces to claim
            face = polysmalls[0]
            for pos in face:
                board.board[pos] = BLACK
            
            black, white, unclaimed = board.score()
            
            # BLACK should have some territory
            assert black > 0
            assert unclaimed < 1.0
            assert round(black + white + unclaimed, 6) == 1.0


class TestBoardGameState:
    """Tests for the game state methods."""
    
    def test_is_game_over_false(self):
        """Test is_game_over when the game is not over."""
        board = Board()
        # With an empty board, game is not over
        assert board.is_game_over() == False
    
    def test_is_game_over_true(self):
        """Test is_game_over when the game is over."""
        board = Board()
        # Make all points suicides for the current player
        player = board.current_player
        if player == BLACK:
            board.black_suicides = set(range(302))
        else:
            board.white_suicides = set(range(302))
        
        assert board.is_game_over() == True
    
    def test_result(self):
        """Test the result method."""
        board = Board()
        # Currently returns an empty dict
        assert board.result() == {}


class TestBoardObserverPattern:
    """Tests for the observer pattern implementation."""
    
    def test_register_observer(self):
        """Test registering an observer."""
        board = Board()
        mock_observer = Mock()
        
        board.register_observer(mock_observer)
        
        assert mock_observer in board._observers
    
    def test_register_duplicate_observer(self):
        """Test registering the same observer twice."""
        board = Board()
        mock_observer = Mock()
        
        board.register_observer(mock_observer)
        board.register_observer(mock_observer)
        
        # The observer should only be added once
        assert board._observers.count(mock_observer) == 1
    
    def test_unregister_observer(self):
        """Test unregistering an observer."""
        board = Board()
        mock_observer = Mock()
        board.register_observer(mock_observer)
        
        board.unregister_observer(mock_observer)
        
        assert mock_observer not in board._observers
    
    def test_enable_disable_notification(self):
        """Test enabling and disabling notifications."""
        board = Board()
        mock_observer = Mock()
        board.register_observer(mock_observer)
        
        # Disable notifications
        board.disable_notification()
        board.notify_observers("test")
        mock_observer.handle_notification.assert_not_called()
        
        # Enable notifications
        board.enable_notification()
        board.notify_observers("test")
        mock_observer.handle_notification.assert_called_once()
