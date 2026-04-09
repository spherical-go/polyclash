from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from PyQt5.QtCore import QObject, pyqtSignal

from polyclash.game.timer import Timer
from polyclash.util.logging import logger
from polyclash.workers.ai_play import AIPlayerWorker

if TYPE_CHECKING:
    from polyclash.game.board import Board

# kind
HUMAN: int = 0
AI: int = 1
REMOTE: int = 2
HRM_AI: int = 3


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
    """AI player — uses HRM (Hierarchical Reasoning Model) when available,
    falls back to the built-in heuristic otherwise."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(kind=AI, **kwargs)
        self.worker: AIPlayerWorker = AIPlayerWorker(self)
        self._hrm_player: Any = None

        checkpoint_dir: str = kwargs.get("checkpoint_dir", "./temp")
        checkpoint_file: str = kwargs.get("checkpoint_file", "best.pkl")
        num_mcts_sims: int = kwargs.get("num_mcts_sims", 50)

        try:
            from hrm_polyclash.bridge import HRMPlayer

            self._hrm_player = HRMPlayer(
                checkpoint_dir=checkpoint_dir,
                checkpoint_file=checkpoint_file,
                num_mcts_sims=num_mcts_sims,
            )
            logger.info("AI player: HRM engine loaded")
        except Exception as e:
            logger.info(f"AI player: HRM unavailable ({e}), using heuristic")

    def auto_place(self) -> None:
        if self.board is None or self.side is None:
            raise ValueError("Player is not attached to a board or side")

        # Try HRM first
        if self._hrm_player is not None:
            position = self._hrm_player.genmove(self.board, self.side)
            if position is not None:
                self.board.disable_notification()
                try:
                    self.board.play(position, self.side)
                finally:
                    self.board.enable_notification()
                self.board.notify_observers(
                    "add_stone",
                    point=position,
                    player=self.side,
                    score=self.board.score(),
                )
                return

        # Fallback to heuristic
        while self.board.current_player == self.side:
            try:
                self.board.disable_notification()
                position = self.board.genmove(self.side)
                self.board.enable_notification()
                self.play(position)
                break
            except ValueError:
                continue

    def stop_worker(self) -> None:
        if self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()


class HRMAIPlayer(AIPlayer):
    """Explicit HRM AI player — same as AIPlayer but with kind=HRM_AI."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.kind = HRM_AI


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
        elif kind == HRM_AI:
            return HRMAIPlayer(**kwargs)
        elif kind == REMOTE:
            return RemotePlayer(**kwargs)
        else:
            raise ValueError(f"Unknown player kind: {kind}")
