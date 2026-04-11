"""Tests for Board serialization and storage persistence (Phase 3)."""

import numpy as np
import pytest

import polyclash.server as server
from polyclash.game.board import BLACK, WHITE, Board
from polyclash.server import app
from polyclash.util.storage import MemoryStorage, create_storage

TEST_TOKEN = "test_token_for_persistence_tests"


class TestBoardSerialization:
    """Test Board.to_dict() / Board.from_dict() roundtrip."""

    def test_empty_board_roundtrip(self):
        board = Board()
        data = board.to_dict()
        restored = Board.from_dict(data)

        assert np.array_equal(board.board, restored.board)
        assert board.current_player == restored.current_player
        assert board.komi == restored.komi
        assert board.consecutive_passes == restored.consecutive_passes
        assert board.zobrist_hash == restored.zobrist_hash
        assert board.counter == restored.counter

    def test_board_with_moves_roundtrip(self):
        board = Board()
        board.disable_notification()
        board.play(0, BLACK)
        board.switch_player()
        board.play(1, WHITE)
        board.switch_player()
        board.play(10, BLACK)
        board.switch_player()

        data = board.to_dict()
        restored = Board.from_dict(data)

        assert np.array_equal(board.board, restored.board)
        assert board.current_player == restored.current_player
        assert board.counter == restored.counter
        assert board.zobrist_hash == restored.zobrist_hash
        assert board.history_hashes == restored.history_hashes
        assert board.latest_player == restored.latest_player
        assert board.black_suicides == restored.black_suicides
        assert board.white_suicides == restored.white_suicides

    def test_restored_board_can_continue_play(self):
        board = Board()
        board.disable_notification()
        board.play(0, BLACK)
        board.switch_player()

        data = board.to_dict()
        restored = Board.from_dict(data)

        # Should be able to continue playing on the restored board
        restored.play(1, WHITE)
        restored.switch_player()
        assert restored.board[1] == WHITE
        assert restored.counter == 2

    def test_restored_board_score_matches(self):
        board = Board()
        board.disable_notification()
        board.play(0, BLACK)
        board.switch_player()
        board.play(1, WHITE)
        board.switch_player()

        data = board.to_dict()
        restored = Board.from_dict(data)

        assert board.score() == restored.score()
        assert board.final_score() == restored.final_score()

    def test_consecutive_passes_preserved(self):
        board = Board()
        board.disable_notification()
        board.consecutive_passes = 1

        data = board.to_dict()
        restored = Board.from_dict(data)
        assert restored.consecutive_passes == 1

    def test_turns_order_preserved(self):
        board = Board()
        board.disable_notification()
        board.play(0, BLACK)
        board.switch_player()
        board.play(1, WHITE)
        board.switch_player()
        board.play(5, BLACK)
        board.switch_player()

        data = board.to_dict()
        restored = Board.from_dict(data)

        assert list(restored.turns.keys()) == list(board.turns.keys())
        for k in board.turns:
            assert restored.turns[k] == board.turns[k]

    def test_to_dict_is_json_serializable(self):
        import json

        board = Board()
        board.disable_notification()
        board.play(0, BLACK)
        board.switch_player()

        data = board.to_dict()
        serialized = json.dumps(data)
        deserialized = json.loads(serialized)
        restored = Board.from_dict(deserialized)
        assert np.array_equal(board.board, restored.board)


class TestStorageBoardPersistence:
    """Test save_board / load_board on MemoryStorage."""

    def test_save_and_load(self):
        storage = MemoryStorage()
        room = storage.create_room()
        game_id = room["game_id"]

        board = Board()
        board.disable_notification()
        board.play(0, BLACK)
        board.switch_player()

        storage.save_board(game_id, board.to_dict())
        loaded = storage.load_board(game_id)
        assert loaded is not None

        restored = Board.from_dict(loaded)
        assert np.array_equal(board.board, restored.board)
        assert board.counter == restored.counter

    def test_load_nonexistent(self):
        storage = MemoryStorage()
        room = storage.create_room()
        game_id = room["game_id"]
        assert storage.load_board(game_id) is None


class TestServerBoardRestore:
    """Test that boards are persisted and restored through server endpoints."""

    @pytest.fixture(autouse=True)
    def setup_server(self):
        old_storage = server.storage
        old_boards = server.boards
        old_token = server.server_token

        server.storage = create_storage(memory=True)
        server.boards = {}
        server.server_token = TEST_TOKEN

        self.client = app.test_client()

        yield

        server.storage = old_storage
        server.boards = old_boards
        server.server_token = old_token

    def _create_and_play(self):
        """Helper: create game, join, play one move, return game data."""
        from polyclash.data.data import encoder

        res = self.client.post("/sphgo/new", json={"token": TEST_TOKEN})
        game_data = res.get_json()
        game_id = game_data["game_id"]

        # Join both players
        res = self.client.post(
            "/sphgo/join",
            json={"token": game_data["black_key"], "role": "black"},
        )
        black_token = res.get_json()["token"]

        res = self.client.post(
            "/sphgo/join",
            json={"token": game_data["white_key"], "role": "white"},
        )
        white_token = res.get_json()["token"]

        # Play a move as black
        point = 0
        encoded = list(encoder[point])
        res = self.client.post(
            "/sphgo/play",
            json={
                "token": black_token,
                "steps": 0,
                "play": encoded,
            },
        )
        assert res.status_code == 200

        return {
            "game_id": game_id,
            "black_token": black_token,
            "white_token": white_token,
        }

    def test_board_persisted_after_play(self):
        data = self._create_and_play()
        game_id = data["game_id"]

        # Board snapshot should exist in storage
        snapshot = server.storage.load_board(game_id)
        assert snapshot is not None
        assert snapshot["board"][0] == BLACK

    def test_board_persisted_after_new(self):
        res = self.client.post("/sphgo/new", json={"token": TEST_TOKEN})
        game_id = res.get_json()["game_id"]

        snapshot = server.storage.load_board(game_id)
        assert snapshot is not None
        # Empty board
        assert all(v == 0 for v in snapshot["board"])

    def test_restore_boards_from_storage(self):
        data = self._create_and_play()
        game_id = data["game_id"]

        # Simulate server restart: clear in-memory boards
        server.boards.clear()
        assert game_id not in server.boards

        # Restore from storage
        server.restore_boards()
        assert game_id in server.boards

        # Verify restored board has the move
        board = server.boards[game_id]
        assert board.board[0] == BLACK
        assert board.counter == 1

    def test_restored_board_can_accept_moves(self):
        from polyclash.data.data import encoder

        data = self._create_and_play()
        game_id = data["game_id"]

        # Simulate restart
        server.boards.clear()
        server.restore_boards()

        # Play move as white on restored board
        point = 1
        encoded = list(encoder[point])
        res = self.client.post(
            "/sphgo/play",
            json={
                "token": data["white_token"],
                "steps": 1,
                "play": encoded,
            },
        )
        assert res.status_code == 200

        # Verify state
        res = self.client.post("/sphgo/state", json={"token": data["black_token"]})
        state = res.get_json()
        assert state["board"][0] == BLACK
        assert state["board"][1] == WHITE
        assert state["counter"] == 2

    def test_genmove_persists_board(self):
        res = self.client.post("/sphgo/new", json={"token": TEST_TOKEN})
        game_data = res.get_json()
        game_id = game_data["game_id"]

        # Join both sides
        res = self.client.post(
            "/sphgo/join",
            json={"token": game_data["black_key"], "role": "black"},
        )
        black_token = res.get_json()["token"]
        self.client.post(
            "/sphgo/join",
            json={"token": game_data["white_key"], "role": "white"},
        )

        # genmove for black
        res = self.client.post("/sphgo/genmove", json={"token": black_token})
        assert res.status_code == 200

        # Should have snapshot
        snapshot = server.storage.load_board(game_id)
        assert snapshot is not None
        assert snapshot["current_player"] == WHITE  # switched after move
