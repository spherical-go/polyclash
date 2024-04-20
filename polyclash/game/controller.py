from PyQt5.QtCore import pyqtSignal, QObject

from polyclash.api import api
from polyclash.data.data import encoder
from polyclash.game.board import BLACK, WHITE, Board
from polyclash.game.player import PlayerFactory, HUMAN, REMOTE, AI


# mode
LOCAL = 0
NETWORK = 1
AUDIENCE = 2


class SphericalGoController(QObject):
    # game related signals
    gameStarted = pyqtSignal()
    playerPlaced = pyqtSignal(int, int)
    gameResigned = pyqtSignal(int)
    gameEnded = pyqtSignal()
    gameClosed = pyqtSignal()

    # board related signals
    boardResetSignal = pyqtSignal()
    stoneAddedSignal = pyqtSignal(int, int)
    stoneRemovedSignal = pyqtSignal(int)

    def __init__(self, mode=LOCAL, board=None):
        super().__init__()
        self.mode = mode
        self.players = {}
        self.winner = None
        self.result = None

        self.board = board
        if board:
            self.board.add_observer(self)
        else:
            self.board = Board()
            self.board.register_observer(self)

        self.gameStarted.connect(self.start_game)
        self.playerPlaced.connect(self.play)
        self.gameResigned.connect(self.resign)
        self.gameEnded.connect(self.end_game)
        self.gameClosed.connect(self.close_game)

    def set_mode(self, mode):
        self.mode = mode
        self.players = {}
        self.board.reset()

    def add_player(self, side, kind=HUMAN, **kwargs):
        if self.mode == LOCAL and kind == REMOTE:
            raise Exception("Invalid player kind for local game")
        if self.mode == AUDIENCE and kind != REMOTE:
            raise Exception("Invalid player kind for audience mode")

        player = PlayerFactory.create_player(kind, board=self.board, side=side, **kwargs)
        self.players[side] = player

    def check_ready(self):
        if len(self.players) == 2:
            return True
        return False

    def start_game(self):
        if self.check_ready():
            self.board.reset()
            self.players[BLACK].timer.reset()
            self.players[WHITE].timer.reset()
        else:
            raise Exception("Players are not ready")

    def play(self, side, placement):
        if self.board.current_player == side:
            player = self.players[side]
            player.play(placement)
            if self.mode == REMOTE:
                api.play(self.board.counter, encoder[placement])
        else:
            raise Exception("Not the player's turn")

        if self.board.is_game_over():
            self.end_game()
        else:
            self.switch_player()

        if self.players[self.board.current_player].kind == AI:
            self.players[self.board.current_player].auto_place()
            self.switch_player()

    def switch_player(self):
        self.board.switch_player()

    def resign(self, player):
        self.winner = -player

    def end_game(self):
        self.result = self.board.result()

    def close_game(self):
        self.board.reset()

    def handle_notification(self, message, **kwargs):
        if message == "reset":
            self.boardResetSignal.emit()
        if message == "add_stone":
            self.stoneAddedSignal.emit(kwargs["point"], kwargs["player"])
        if message == "remove_stone":
            self.stoneRemovedSignal.emit(kwargs["point"])
