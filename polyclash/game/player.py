from PyQt5.QtCore import QObject, pyqtSignal

from polyclash.game.timer import Timer

# kind
HUMAN = 0
AI = 1
REMOTE = 2


class Player(QObject):
    stonePlaced = pyqtSignal(int)  # Define a signal to emit when a stone is placed by the player

    def __init__(self, kind, **kwargs):
        super().__init__()
        self.kind = kind
        self.side = kwargs.get("side")
        self.board = kwargs.get("board")
        self.timer = Timer()
        self.stonePlaced.connect(self.play)  # Connect signal to slot

    def play(self, position):
        self.board.play(position, self.side)

    def place_stone(self, position):
        self.stonePlaced.emit(position)  # Emit signal when stone is placed by the player


class HumanPlayer(Player):
    def __init__(self, **kwargs):
        super().__init__(kind=HUMAN, **kwargs)


class AIPlayer(Player):
    def __init__(self, **kwargs):
        super().__init__(kind=AI, **kwargs)

    def auto_place(self):
        try:
            self.board.disable_notification()
            position = self.board.genmove(self.side)
            self.board.enable_notification()
            self.stonePlaced.emit(position)
        except ValueError as e:
            self.auto_place()


class RemotePlayer(Player):
    def __init__(self, **kwargs):
        super().__init__(kind=REMOTE, **kwargs)
        self.key = kwargs.get("key")
        self.network = kwargs.get("network")


class PlayerFactory:
    @staticmethod
    def create_player(kind, **kwargs):
        if kind == HUMAN:
            return HumanPlayer(**kwargs)
        elif kind == AI:
            return AIPlayer(**kwargs)
        elif kind == REMOTE:
            return RemotePlayer(**kwargs)
