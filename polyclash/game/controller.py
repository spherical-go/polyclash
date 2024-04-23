from PyQt5.QtCore import pyqtSignal, QObject

from polyclash.api import api
from polyclash.data.data import encoder
from polyclash.game.board import BLACK, WHITE, Board
from polyclash.game.player import PlayerFactory, HUMAN, REMOTE, AI


# mode
LOCAL = 0
NETWORK = 1
VIEW = 2


class SphericalGoController(QObject):
    # game related signals
    gameStarted = pyqtSignal()
    playerPlaced = pyqtSignal(int, int)
    gameResigned = pyqtSignal(int)
    gameEnded = pyqtSignal()
    gameClosed = pyqtSignal()

    # board related signals
    # boardResetSignal = pyqtSignal()
    # stoneAddedSignal = pyqtSignal(int, int)
    # stoneRemovedSignal = pyqtSignal(int)

    def __init__(self, mode=LOCAL, board=None):
        super().__init__()
        self.mode = mode
        self.players = {}
        self.winner = None
        self.result = None

        self.board = board if board else Board()
        # self.board.register_observer(self)

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
            raise InvalidPlayerError("Invalid player kind for local game")
        if self.mode == VIEW and kind != REMOTE:
            raise InvalidPlayerError("Invalid player kind for view mode")

        player = PlayerFactory.create_player(kind, board=self.board, side=side, **kwargs)
        self.players[side] = player
        player.stonePlaced.connect(self.player_played)

    def check_ready(self):
        if len(self.players) == 2:
            return True
        return False

    def get_current_player(self):
        return self.players[self.board.current_player]

    def start_game(self):
        if self.check_ready():
            self.board.reset()
            self.players[BLACK].timer.reset()
            self.players[WHITE].timer.reset()

            while not self.board.is_game_over():
                if self.get_current_player().kind == AI:
                    self.get_current_player().auto_place()
                    self.switch_player()
                else:
                    break
        else:
            raise Exception("Players are not ready")

    def is_player_turn(self, side):
        return self.board.current_player == side

    def play(self, side, placement):
        if not self.is_player_turn(side):
            raise InvalidTurnError("Not the player's turn")

        if self.board.is_game_over():
            self.end_game()
        else:
            player = self.players[side]
            player.play(placement)
            if self.mode == NETWORK:
                api.play(self.board.counter, encoder[placement])
            self.switch_player()

            if self.get_current_player().kind == AI:
                self.get_current_player().auto_place()
                self.switch_player()

    def switch_player(self):
        self.board.switch_player()

    def resign(self, player):
        self.winner = -player

    def end_game(self):
        self.result = self.board.result()

    def close_game(self):
        self.board.reset()
        for side, players in self.players.items():
            players.worker.stop()
        self.players = {}

    def player_played(self, position):
        self.playerPlaced.emit(self.board.current_player, position)

    # def handle_notification(self, message, **kwargs):
    #     if message == "reset":
    #         self.boardResetSignal.emit()
    #     if message == "add_stone":
    #         self.stoneAddedSignal.emit(kwargs["point"], kwargs["player"])
    #     if message == "remove_stone":
    #         self.stoneRemovedSignal.emit(kwargs["point"])


class InvalidPlayerError(Exception):
    """Exception raised for errors in the input player type or game mode."""
    def __init__(self, message="Invalid player configuration"):
        self.message = message
        super().__init__(self.message)


class InvalidTurnError(Exception):
    """Exception raised for errors in the player turn."""
    def __init__(self, message="Invalid player's turn"):
        self.message = message
        super().__init__(self.message)

