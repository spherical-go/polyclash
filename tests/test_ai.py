import unittest

from polyclash.game.board import Board, BLACK, WHITE
from polyclash.data.data import neighbors, decoder


class TestBoard(unittest.TestCase):
    def test_autoplay(self):
        board = Board()
        for i in range(2):
            move = board.genmove(BLACK)
            self.assertTrue(move < 302,f"Move[{2 * i}]={move} should not be empty.")
            board.play(move, BLACK)
            board.switch_player()
            move = board.genmove(WHITE)
            self.assertTrue(move < 302,f"Move[{2 * i + 1}]={move}  should not be empty.")
            board.play(move, WHITE)
            board.switch_player()


if __name__ == '__main__':
    unittest.main()
