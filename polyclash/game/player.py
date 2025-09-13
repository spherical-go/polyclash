from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from polyclash.game.timer import Timer
from polyclash.workers.ai_play import AIPlayerWorker

if TYPE_CHECKING:
    from polyclash.game.board import Board

# kind
HUMAN: int = 0
AI: int = 1
REMOTE: int = 2


class Player(QObject):
    # Define a signal to emit when a stone is placed by the player
    stonePlaced = pyqtSignal(int)

    def __init__(self, kind: int, **kwargs: Any) -> None:
        super().__init__()
        self.kind: int = kind
        self.side: Optional[int] = kwargs.get("side")
        self.board: Optional["Board"] = kwargs.get("board")
        self.timer: Timer = Timer(3600)
        self.stonePlaced.connect(self.play)  # Connect signal to slot

    def play(self, position: int) -> None:
        # Assume board and side are set by controller when player is attached
        if self.board is None or self.side is None:
            raise ValueError("Player is not attached to a board or side")
        self.board.play(position, self.side)

    def place_stone(self, position: int) -> None:
        # Emit signal when stone is placed by the player
        self.stonePlaced.emit(position)


class HumanPlayer(Player):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(kind=HUMAN, **kwargs)


class AIPlayer(Player):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(kind=AI, **kwargs)
        self.worker: AIPlayerWorker = AIPlayerWorker(self)

    def auto_place(self) -> None:
        # Assume board and side are set by controller when player is attached
        if self.board is None or self.side is None:
            raise ValueError("Player is not attached to a board or side")
        while self.board.current_player == self.side:
            try:
                self.board.disable_notification()
                position = self.board.genmove(self.side)
                self.board.enable_notification()
                self.play(position)
                break  # Exit the loop if move was successful
            except ValueError:
                continue  # Try again if an error occurred

    def stop_worker(self) -> None:
        if self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()


class RemotePlayer(Player):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(kind=REMOTE, **kwargs)
        self.token: Optional[str] = kwargs.get("token")


class PlayerFactory:
    @staticmethod
    def create_player(kind: int, **kwargs: Any) -> Player:
        if kind == HUMAN:
            return HumanPlayer(**kwargs)
        elif kind == AI:
            return AIPlayer(**kwargs)
        elif kind == REMOTE:
            return RemotePlayer(**kwargs)
        else:
            raise ValueError(f"Unknown player kind: {kind}")
