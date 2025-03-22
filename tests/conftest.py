import pytest
from polyclash.game.board import Board, BLACK, WHITE
from polyclash.game.controller import SphericalGoController
from polyclash.game.player import Player

@pytest.fixture
def empty_board():
    """Fixture for an empty board."""
    return Board()

@pytest.fixture
def controller():
    """Fixture for a controller with an empty board."""
    return SphericalGoController()

@pytest.fixture
def black_player():
    """Fixture for a black player."""
    return Player(BLACK)

@pytest.fixture
def white_player():
    """Fixture for a white player."""
    return Player(WHITE)
