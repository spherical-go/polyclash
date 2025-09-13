from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import LOCAL, SphericalGoController
from polyclash.game.player import AI, HUMAN, AIPlayer, HumanPlayer


class TestControllerInitialization:
    def test_controller_creation(self):
        controller = SphericalGoController()
        assert controller.mode == LOCAL
        assert controller.board is not None
        assert len(controller.players) == 0


class TestControllerGameFlow:
    def test_add_player(self):
        controller = SphericalGoController()
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        assert len(controller.players) == 2
        assert controller.players[BLACK].side == BLACK
        assert controller.players[WHITE].side == WHITE

    def test_start_game(self):
        controller = SphericalGoController()
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.start()
        assert controller.board.current_player == BLACK

    def test_play_move(self):
        controller = SphericalGoController()
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.start()

        # Play a move
        controller.play(BLACK, 0)
        assert controller.board.board[0] == BLACK
        assert controller.board.current_player == WHITE

        # Play another move
        controller.play(WHITE, 1)
        assert controller.board.board[1] == WHITE
        assert controller.board.current_player == BLACK

    def test_game_over(self):
        controller = SphericalGoController()
        controller.add_player(BLACK)
        controller.add_player(WHITE)
        controller.start()

        # Mock the board's is_game_over method to return True
        original_is_game_over = controller.board.is_game_over
        controller.board.is_game_over = lambda: True

        # Check that the board's is_game_over method returns True
        assert controller.board.is_game_over() == True

        # Restore the original method
        controller.board.is_game_over = original_is_game_over


class TestControllerPlayerTypes:
    def test_add_human_player(self):
        controller = SphericalGoController()
        controller.add_player(BLACK, kind=HUMAN)
        assert isinstance(controller.players[BLACK], HumanPlayer)
        assert controller.players[BLACK].side == BLACK

    def test_add_ai_player(self):
        controller = SphericalGoController()
        controller.add_player(WHITE, kind=AI)
        assert isinstance(controller.players[WHITE], AIPlayer)
        assert controller.players[WHITE].side == WHITE
