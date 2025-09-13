from unittest.mock import patch

import numpy as np

from polyclash.game.board import (
    BLACK,
    WHITE,
    Board,
    SimulatedBoard,
    calculate_area,
    calculate_distance,
    calculate_potential,
)


class TestSimulatedBoard:
    """Tests for the SimulatedBoard class."""

    def test_redirect(self):
        """Test redirecting state from another board."""
        original = Board()
        original.board[10] = BLACK
        original.current_player = WHITE
        original.latest_removes.append([20])
        original.black_suicides.add(30)
        original.white_suicides.add(31)
        original.turns[0] = "0-1"

        simulator = SimulatedBoard()
        simulator.redirect(original)

        # Verify the simulator has copied all state
        assert simulator.board[10] == BLACK
        assert simulator.current_player == WHITE
        assert simulator.latest_removes[-1] == [20]
        assert 30 in simulator.black_suicides
        assert 31 in simulator.white_suicides
        assert simulator.turns[0] == "0-1"

        # Verify that modifying the simulator doesn't affect the original
        simulator.board[10] = 0
        assert original.board[10] == BLACK

    def test_genmove_basic(self):
        """Test basic move generation."""
        board = Board()
        simulator = SimulatedBoard()
        simulator.redirect(board)

        move = simulator.genmove(BLACK)

        # Should return a valid move
        assert isinstance(move, int)
        assert 0 <= move < 302

    def test_simulate_score(self):
        """Test score simulation for a move."""
        simulator = SimulatedBoard()
        simulator.board = np.zeros([302])

        # Setup a simple board position to ensure simulation doesn't fail
        simulator.board[10] = BLACK
        simulator.current_player = BLACK
        simulator.latest_removes = [[]]
        simulator.orginal_counter = 0

        # Patch sample method to return a predictable result for testing
        with patch("polyclash.game.board.sample", return_value=[20]):
            try:
                score, gain = simulator.simulate_score(0, 11, BLACK)

                # We should get a score and gain
                assert isinstance(score, float)
                assert isinstance(gain, float)
            except ValueError as e:
                # If the simulation fails due to game logic reasons (like suicide move),
                # make sure it's a known error message
                assert "suicide" in str(e)


class TestHelperFunctions:
    """Tests for the helper functions."""

    def test_calculate_area_unclaimed(self):
        """Test calculating area for an unclaimed territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        assert black == 0
        assert white == 0
        assert unclaimed == area

    def test_calculate_area_black_claimed(self):
        """Test calculating area for a BLACK-claimed territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        for pos in piece:
            boarddata[pos] = BLACK
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        assert black == area
        assert white == 0
        assert unclaimed == 0

    def test_calculate_area_white_claimed(self):
        """Test calculating area for a WHITE-claimed territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        for pos in piece:
            boarddata[pos] = WHITE
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        assert black == 0
        assert white == area
        assert unclaimed == 0

    def test_calculate_area_contested(self):
        """Test calculating area for a contested territory."""
        boarddata = np.zeros([302])
        piece = [0, 1, 2, 3, 4]  # Example piece (face)
        # Mix of BLACK and WHITE
        boarddata[0] = BLACK
        boarddata[1] = BLACK
        boarddata[2] = BLACK
        boarddata[3] = WHITE
        boarddata[4] = WHITE
        area = 10.0  # Example area

        black, white, unclaimed = calculate_area(boarddata, piece, area)

        # Should be split proportionally
        assert black == 6.0  # 3/5 of area
        assert white == 4.0  # 2/5 of area
        assert unclaimed == 0

    def test_calculate_distance(self):
        """Test distance calculation between two points."""
        # This depends on the specific cities data structure
        # Use the first two points for testing
        point1 = 0
        point2 = 1

        distance = calculate_distance(point1, point2)

        # The distance should be positive
        assert distance > 0
        # We can't test the exact value without knowing the cities data,
        # but we can verify it's the expected type
        assert isinstance(distance, float)

    def test_calculate_potential(self):
        """Test potential calculation for a point."""
        board = np.zeros([302])
        board[1] = BLACK
        board[2] = WHITE
        point = 0
        counter = 10

        potential = calculate_potential(board, point, counter)

        # Should return a number based on the distances
        assert isinstance(potential, float)
