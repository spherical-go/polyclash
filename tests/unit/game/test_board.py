import pytest
from polyclash.game.board import Board, BLACK, WHITE
from polyclash.data.data import neighbors, decoder

class TestBoardInitialization:
    def test_init(self):
        board = Board()
        assert board.board_size == 302, "The board size should be 302."
        assert board.board.shape == (302,), "The shape of the board should be (302,)."
        assert board.current_player == BLACK, "The current player should be BLACK."
        assert len(board.neighbors) == 302, "The number of neighbors should be 302."
        for i in range(302):
            assert board.neighbors[i] is not None and len(board.neighbors[i]) > 0, \
                "Each neighbor should not be empty."

class TestBoardLiberties:
    def test_has_liberty_case_0(self):
        board = Board()
        board.board[0] = BLACK
        assert board.has_liberty(0) == True, "The point 0 should have liberty."

    def test_has_liberty_case_1(self):
        board = Board()
        board.board[0] = WHITE
        for pos in neighbors[0]:
            board.board[pos] = BLACK
        assert board.has_liberty(0) == False, "The point 0 should not have liberty."

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

        assert board.has_liberty(0) == True, "The point 0 should have liberty."

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

        assert board.has_liberty(0) == False, "The point 0 should have liberty."

class TestBoardPlay:
    def test_play_case_0(self):
        board = Board()
        cycle = [0, decoder[(0, 1)], 1, decoder[(1, 2)], 2, decoder[2, 3], 3, decoder[(3, 4)], 4, decoder[(4, 0)]]
        face = decoder[(0, 1, 2, 3, 4)]
        for pos in cycle:
            board.board[pos] = WHITE
        for pos in cycle:
            for n in neighbors[pos]:
                if n not in cycle and n != face:
                    board.board[n] = BLACK

        board.play(face, BLACK)

        assert BLACK == board.board[face], f"The point {face} should be black."
        for pos in cycle:
            assert board.board[pos] == 0, f"The point {pos} should be empty."

    def test_play_case_1(self):
        board = Board()
        cycle = [0, decoder[(0, 1)], 1, decoder[(1, 2)], 2, decoder[2, 3], 3, decoder[(3, 4)], 4, decoder[(4, 0)]]
        face = decoder[(0, 1, 2, 3, 4)]
        for pos in cycle:
            board.board[pos] = BLACK
        for pos in cycle:
            for n in neighbors[pos]:
                if n not in cycle and n != face:
                    board.board[n] = WHITE

        with pytest.raises(ValueError, match="suicide is not allowed"):
            board.play(face, BLACK)

    def test_play_case_2(self):
        board = Board()
        cycle = [0, decoder[(0, 1)], 1, decoder[(1, 2)], 2, decoder[2, 3], 3, decoder[(3, 4)], 4, decoder[(4, 0)]]
        face = decoder[(0, 1, 2, 3, 4)]
        for pos in cycle:
            board.board[pos] = BLACK
        for pos in cycle:
            for n in neighbors[pos]:
                if n not in cycle and n != face:
                    board.board[n] = WHITE

        with pytest.raises(ValueError, match="position already occupied"):
            board.play(0, BLACK)

    def test_play_case_3(self):
        board = Board()
        assert board.current_player == BLACK, f"Current_player should be {1}."
        for ix, step in enumerate([(5, 6, 7, 8, 9), (25, 26, 27, 28, 29),  (25, 29), (35, 36, 37, 38, 39),  (25, 26),
            (45, 46, 47, 48, 49), (26, 27), (30, 31, 32, 33, 34), (27, 28), (21,)
            ]):
            pos = decoder[step]
            board.play(pos, board.current_player)
            board.switch_player()

        pos = decoder[(25, 26, 27, 28, 29)]
        assert board.board[pos] == WHITE, f"The point {pos} should be white."
        board.play(decoder[(28, 29)], BLACK)
        assert board.board[pos] == 0, f"The point {pos} should be empty."
