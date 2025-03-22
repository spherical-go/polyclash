import pytest
from polyclash.game.player import Player, HumanPlayer, AIPlayer, RemotePlayer, HUMAN, AI, REMOTE
from polyclash.game.board import Board, BLACK, WHITE

class TestPlayerCreation:
    def test_player_creation(self):
        board = Board()
        player = Player(HUMAN, side=BLACK, board=board)
        assert player.kind == HUMAN
        assert player.side == BLACK
        assert player.board == board

    def test_human_player_creation(self):
        board = Board()
        player = HumanPlayer(side=BLACK, board=board)
        assert player.kind == HUMAN
        assert player.side == BLACK
        assert player.board == board

    def test_ai_player_creation(self):
        board = Board()
        player = AIPlayer(side=WHITE, board=board)
        assert player.kind == AI
        assert player.side == WHITE
        assert player.board == board
        assert hasattr(player, 'worker')

    def test_remote_player_creation(self):
        board = Board()
        player = RemotePlayer(side=BLACK, board=board, token="test_token")
        assert player.kind == REMOTE
        assert player.side == BLACK
        assert player.board == board
        assert player.token == "test_token"

class TestPlayerInteraction:
    def test_player_play(self, mocker):
        board = mocker.Mock()
        player = Player(HUMAN, side=BLACK, board=board)
        player.play(0)
        board.play.assert_called_once_with(0, BLACK)

    def test_player_place_stone(self, mocker):
        board = Board()
        player = Player(HUMAN, side=BLACK, board=board)
        
        # Mock the stonePlaced signal
        mocker.patch.object(player, 'stonePlaced')
        
        player.place_stone(0)
        player.stonePlaced.emit.assert_called_once_with(0)

class TestAIPlayerFunctionality:
    def test_ai_auto_place(self, mocker):
        board = mocker.Mock()
        board.current_player = BLACK
        board.genmove.return_value = 0
        
        player = AIPlayer(side=BLACK, board=board)
        
        # Mock the worker
        mocker.patch.object(player, 'worker')
        
        player.auto_place()
        board.disable_notification.assert_called_once()
        board.genmove.assert_called_once_with(BLACK)
        board.enable_notification.assert_called_once()
        board.play.assert_called_once_with(0, BLACK)
