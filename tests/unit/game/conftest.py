import pytest

from polyclash.game.board import BLACK, WHITE, Board


@pytest.fixture
def board_with_stones():
    """Fixture for a board with some stones placed."""
    board = Board()
    # Place some stones in a typical pattern
    board.play(0, BLACK)
    board.play(1, WHITE)
    board.play(2, BLACK)
    board.play(3, WHITE)
    return board


@pytest.fixture
def board_with_capture():
    """Fixture for a board with a capture situation."""
    board = Board()
    # Set up a capture situation
    # This will depend on the specific board topology
    # For now, we'll create a simple setup where a white stone is surrounded by black stones

    # First, place a white stone
    board.play(0, WHITE)

    # Then surround it with black stones
    # We need to know the neighbors of position 0
    for neighbor in board.neighbors[0]:
        try:
            board.play(neighbor, BLACK)
        except ValueError:
            # Skip if the move is invalid (e.g., suicide)
            pass

    return board
