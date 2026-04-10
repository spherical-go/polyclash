from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from polyclash.data.data import decoder
from polyclash.game.board import BLACK, WHITE, Board


class GameRecord:
    """Records and replays PolyClash games."""

    def __init__(self) -> None:
        self.metadata: dict[str, str] = {
            "format": "PGR",
            "version": "1.0",
            "date": "",
            "black_player": "",
            "white_player": "",
            "result": "",
            "board_size": "302",
        }
        self.moves: list[dict[str, Any]] = []

    @classmethod
    def from_board(
        cls, board: Board, black_name: str = "", white_name: str = ""
    ) -> "GameRecord":
        """Create a record from a completed or in-progress Board."""
        record = cls()
        record.metadata["date"] = datetime.now().isoformat()
        record.metadata["black_player"] = black_name
        record.metadata["white_player"] = white_name

        for i, (counter, encoded) in enumerate(board.turns.items()):
            player = "black" if i % 2 == 0 else "white"
            encoded_tuple: tuple[int, ...] = tuple(int(x) for x in encoded)
            point = decoder[encoded_tuple]
            record.moves.append(
                {
                    "number": i,
                    "player": player,
                    "point": point,
                    "encoded": list(encoded),
                }
            )

        score = board.score()
        record.metadata["result"] = f"B:{score[0]:.4f} W:{score[1]:.4f}"
        return record

    def save(self, path: str | Path) -> None:
        """Save record to a JSON file."""
        data = {
            "metadata": self.metadata,
            "moves": self.moves,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "GameRecord":
        """Load a record from a JSON file."""
        with open(path) as f:
            data = json.load(f)
        record = cls()
        record.metadata = data["metadata"]
        record.moves = data["moves"]
        return record

    def replay(self, up_to: Optional[int] = None) -> Board:
        """Replay the game up to move number `up_to` (inclusive).
        Returns the resulting Board state."""
        board = Board()
        board.disable_notification()
        moves = self.moves if up_to is None else self.moves[: up_to + 1]
        for move in moves:
            player = BLACK if move["player"] == "black" else WHITE
            board.play(move["point"], player)
            board.switch_player()
        board.enable_notification()
        return board

    def to_dict(self) -> dict[str, Any]:
        """Return the record as a serializable dict."""
        return {
            "metadata": self.metadata,
            "moves": self.moves,
        }

    def __len__(self) -> int:
        return len(self.moves)

    def __repr__(self) -> str:
        return (
            f"GameRecord({len(self.moves)} moves, "
            f"{self.metadata.get('date', 'no date')})"
        )
