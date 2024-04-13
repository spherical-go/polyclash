import unittest

from polyclash.board import Board, BLACK, WHITE
from polyclash.data import neighbors, decoder


class TestBoard(unittest.TestCase):
    def test_init(self):
        board = Board()
        self.assertEqual(board.board_size, 302, "The board size should be 302.")
        self.assertEqual(board.board.shape, (302,), "The shape of the board should be (302,).")
        self.assertEqual(board.current_player, BLACK, "The current player should be BLACK.")
        self.assertEqual(len(board.neighbors), 302, "The number of neighbors should be 302.")
        for i in range(302):
            self.assertTrue(board.neighbors[i] is not None and len(board.neighbors[i]) > 0,
                            "Each neighbor should not be empty.")

    def test_has_liberty_case_0(self):
        board = Board()
        board.board[0] = BLACK
        self.assertEqual(board.has_liberty(0), True, "The point 0 should have liberty.")

    def test_has_liberty_case_1(self):
        board = Board()
        board.board[0] = WHITE
        for pos in neighbors[0]:
            board.board[pos] = BLACK
        self.assertEqual(board.has_liberty(0), False, "The point 0 should not have liberty.")

    def test_has_liberty_case_3(self):
        board = Board()
        cycle = [0, decoder[(0, 1)], 1, decoder[(1, 2)], 2, decoder[2, 3], 3, decoder[(3, 4)], 4, decoder[(4, 0)]]
        face = decoder[(0, 1, 2, 3, 4)]
        for pos in cycle:
            board.board[pos] = BLACK
        for pos in cycle:
            for n in neighbors[pos]:
                if n not in cycle and n != face:
                    board.board[n] = WHITE

        self.assertEqual(board.has_liberty(0), True, "The point 0 should have liberty.")

    def test_has_liberty_case_4(self):
        board = Board()
        cycle = [0, decoder[(0, 1)], 1, decoder[(1, 2)], 2, decoder[2, 3], 3, decoder[(3, 4)], 4, decoder[(4, 0)]]
        face = decoder[(0, 1, 2, 3, 4)]
        for pos in cycle:
            board.board[pos] = BLACK
        for pos in cycle:
            for n in neighbors[pos]:
                if n not in cycle and n != face:
                    board.board[n] = WHITE
        board.board[face] = BLACK

        self.assertEqual(board.has_liberty(0), False, "The point 0 should have liberty.")


