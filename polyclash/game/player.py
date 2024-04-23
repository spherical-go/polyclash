from PyQt5.QtCore import QObject, pyqtSignal

from polyclash.game.timer import Timer
from polyclash.workers.ai_play import AIPlayerWorker

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
        self.timer = Timer(3600)
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
        self.worker = AIPlayerWorker(self)

    def auto_place(self):
        while self.board.current_player == self.side:
            try:
                self.board.disable_notification()
                position = self.board.genmove(self.side)
                self.board.enable_notification()
                self.play(position)
                break  # Exit the loop if move was successful
            except ValueError:
                continue  # Try again if an error occurred

    def stop_worker(self):
        if self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()


class RemotePlayer(Player):
    def __init__(self, **kwargs):
        super().__init__(kind=REMOTE, **kwargs)
        self.token = kwargs.get("token")


class PlayerFactory:
    @staticmethod
    def create_player(kind, **kwargs):
        if kind == HUMAN:
            return HumanPlayer(**kwargs)
        elif kind == AI:
            return AIPlayer(**kwargs)
        elif kind == REMOTE:
            return RemotePlayer(**kwargs)
