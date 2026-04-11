from __future__ import annotations

from pathlib import Path

from polyclash.data.data import encoder
from polyclash.game.board import BLACK, WHITE, Board
from polyclash.game.record import GameRecord


class TestInit:
    def test_init(self) -> None:
        record = GameRecord()
        assert record.metadata["format"] == "PGR"
        assert record.metadata["version"] == "1.0"
        assert record.metadata["date"] == ""
        assert record.metadata["black_player"] == ""
        assert record.metadata["white_player"] == ""
        assert record.metadata["result"] == ""
        assert record.metadata["board_size"] == "302"
        assert record.moves == []


class TestFromBoard:
    def test_from_board(self) -> None:
        board = Board()
        board.disable_notification()

        points = [0, 1, 2]
        for point in points:
            board.play(point, board.current_player)
            board.switch_player()

        record = GameRecord.from_board(board, "Alice", "Bob")

        assert record.metadata["black_player"] == "Alice"
        assert record.metadata["white_player"] == "Bob"
        assert record.metadata["date"] != ""
        assert "B:" in record.metadata["result"]
        assert "W:" in record.metadata["result"]
        assert len(record.moves) == 3

        assert record.moves[0]["player"] == "black"
        assert record.moves[0]["point"] == 0
        assert record.moves[0]["encoded"] == list(encoder[0])

        assert record.moves[1]["player"] == "white"
        assert record.moves[1]["point"] == 1

        assert record.moves[2]["player"] == "black"
        assert record.moves[2]["point"] == 2


class TestSaveLoad:
    def test_save_load(self, tmp_path: Path) -> None:
        record = GameRecord()
        record.metadata["black_player"] = "Alice"
        record.metadata["white_player"] = "Bob"
        record.metadata["date"] = "2026-01-01T00:00:00"
        record.moves = [
            {"number": 0, "player": "black", "point": 0, "encoded": list(encoder[0])},
            {"number": 1, "player": "white", "point": 1, "encoded": list(encoder[1])},
        ]

        filepath = tmp_path / "game.json"
        record.save(filepath)
        assert filepath.exists()

        loaded = GameRecord.load(filepath)
        assert loaded.metadata == record.metadata
        assert loaded.moves == record.moves


class TestReplay:
    def _make_record(self, points: list[int]) -> GameRecord:
        record = GameRecord()
        for i, point in enumerate(points):
            player = "black" if i % 2 == 0 else "white"
            record.moves.append(
                {
                    "number": i,
                    "player": player,
                    "point": point,
                    "encoded": list(encoder[point]),
                }
            )
        return record

    def test_replay(self) -> None:
        points = [0, 1, 2]
        record = self._make_record(points)

        board = record.replay()
        assert board.board[0] == BLACK
        assert board.board[1] == WHITE
        assert board.board[2] == BLACK

    def test_replay_partial(self) -> None:
        points = [0, 1, 2]
        record = self._make_record(points)

        board = record.replay(up_to=1)
        assert board.board[0] == BLACK
        assert board.board[1] == WHITE
        assert board.board[2] == 0


class TestDunderMethods:
    def test_len(self) -> None:
        record = GameRecord()
        assert len(record) == 0

        record.moves.append(
            {"number": 0, "player": "black", "point": 0, "encoded": list(encoder[0])}
        )
        assert len(record) == 1

    def test_repr(self) -> None:
        record = GameRecord()
        record.metadata["date"] = "2026-01-01"
        record.moves = [
            {"number": 0, "player": "black", "point": 0, "encoded": list(encoder[0])},
        ]
        assert repr(record) == "GameRecord(1 moves, 2026-01-01)"

    def test_repr_no_date(self) -> None:
        record = GameRecord()
        record.metadata.pop("date", None)
        assert repr(record) == "GameRecord(0 moves, no date)"
