"""Tests targeting specific uncovered lines in server.py and board.py."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

import polyclash.server as server
from polyclash.data.data import decoder, neighbors
from polyclash.game.board import BLACK, WHITE, Board
from polyclash.server import valid_plays
from tests.conftest import TEST_TOKEN


# ---------------------------------------------------------------------------
# Helper: create a game and join both players, returning tokens & game_id
# ---------------------------------------------------------------------------
def _setup_game(client: Any, storage: Any) -> dict[str, str]:
    resp = client.post("/sphgo/new", json={"token": TEST_TOKEN})
    assert resp.status_code == 200
    data = resp.get_json()
    game_id = data["game_id"]

    resp = client.post(
        "/sphgo/join", json={"token": data["black_key"], "role": "black"}
    )
    assert resp.status_code == 200
    black_token = resp.get_json()["token"]

    resp = client.post(
        "/sphgo/join", json={"token": data["white_key"], "role": "white"}
    )
    assert resp.status_code == 200
    white_token = resp.get_json()["token"]

    return {
        "game_id": game_id,
        "black_key": data["black_key"],
        "white_key": data["white_key"],
        "viewer_key": data["viewer_key"],
        "black_token": black_token,
        "white_token": white_token,
    }


# ===================================================================
# Board tests
# ===================================================================


class TestBoardCoverageGaps:
    """Cover missed lines in polyclash/game/board.py."""

    def test_play_out_of_bounds(self) -> None:
        """Line 183: point >= 302 raises ValueError."""
        board = Board()
        # Extend the board array so index 302 doesn't raise IndexError
        board.board = np.append(board.board, [0])
        with pytest.raises(ValueError, match="position not on the board"):
            board.play(302, BLACK)

    def test_play_black_wrong_turn(self) -> None:
        """Line 186: BLACK plays on an odd counter (counter=1)."""
        board = Board()
        # Make one move so counter becomes 1 (odd)
        board.play(0, BLACK)
        board.switch_player()
        # Reset latest_player so the early-return on line 176 doesn't trigger
        board.latest_player = None
        with pytest.raises(ValueError, match="not the player's turn"):
            board.play(1, BLACK)

    def test_play_white_wrong_turn(self) -> None:
        """Line 189: WHITE plays on an even counter (counter=0)."""
        board = Board()
        with pytest.raises(ValueError, match="not the player's turn"):
            board.play(0, WHITE)

    def test_play_turn_check_wrong_player(self) -> None:
        """Line 192: turn_check=True but player != current_player."""
        board = Board()
        # current_player is BLACK, but we pass WHITE with turn_check=True
        # Also need counter to be odd so the counter-parity check passes for WHITE
        board.play(0, BLACK)
        board.switch_player()
        # current_player is now WHITE; try to play BLACK with turn_check
        # But BLACK on odd counter is caught by line 186, so instead:
        # Make counter even again and current_player WHITE
        board.play(1, WHITE)
        board.switch_player()
        # counter=2 (even), current_player=BLACK
        # Play WHITE with turn_check=True: counter is even → line 189 fires.
        # We need counter odd and current_player != player.
        # counter=2, current_player=BLACK. Play WHITE: counter%2==0 → line 189.
        # So let's use a different approach: set current_player directly.
        board.current_player = WHITE  # now current_player=WHITE but counter=2 (even)
        # WHITE on even counter → line 189 fires first.
        # We need to bypass the counter checks. The only way to hit line 192
        # exclusively is when counter parity is correct but current_player differs.
        # counter=2 (even), player=BLACK → counter check passes (BLACK on even OK)
        # but current_player=WHITE ≠ BLACK → line 192.
        with pytest.raises(ValueError, match="not the player's turn"):
            board.play(2, BLACK, turn_check=True)

    def test_white_suicide(self) -> None:
        """Line 217: WHITE suicide adds point to white_suicides."""
        board = Board()
        # Build a cage around a single point using BLACK stones,
        # then try to place WHITE inside.
        cycle = [
            0,
            decoder[(0, 1)],
            1,
            decoder[(1, 2)],
            2,
            decoder[(2, 3)],
            3,
            decoder[(3, 4)],
            4,
            decoder[(4, 0)],
        ]
        face = decoder[(0, 1, 2, 3, 4)]
        # Fill cycle with WHITE stones, surround with BLACK
        for pos in cycle:
            board.board[pos] = WHITE
        for pos in cycle:
            for n in neighbors[pos]:
                if n not in cycle and n != face:
                    board.board[n] = BLACK

        # Now the face point is empty and surrounded by WHITE which is
        # surrounded by BLACK. Playing WHITE at face = suicide.
        # Adjust counter and current_player so WHITE can play.
        board.current_player = WHITE
        # Need odd counter for WHITE
        board.turns[0] = (0,)  # fake turn to make counter=1 (odd)
        with pytest.raises(ValueError, match="suicide is not allowed"):
            board.play(face, WHITE)
        assert face in board.white_suicides

    def test_superko_violation(self) -> None:
        """Lines 222-226: superko violation undoes the move and restores captures."""
        board = Board()
        # We need a situation where a move is legal (not suicide) but
        # reproduces a previous zobrist hash. This requires a ko-like setup.
        # Use the board's internal state to fabricate the condition.
        target = 10
        # Place stone, record hash, remove it, then replay to get same hash
        board.board[target] = BLACK
        board.zobrist_hash ^= board.board_size  # fake hash
        # Directly set up: play at a point that will produce a hash already
        # in history_hashes.
        board.board = np.zeros([302])
        board.zobrist_hash = 0
        board.current_player = BLACK

        # Play a stone, record the resulting hash
        board.play(0, BLACK, turn_check=False)
        first_hash = board.zobrist_hash
        board.switch_player()

        # Play opponent
        board.play(1, WHITE, turn_check=False)
        board.switch_player()

        # Now inject first_hash into history so the next move that produces
        # that hash triggers superko. We need to find a point whose zobrist
        # XOR with current hash equals first_hash.
        # Instead, directly add the *future* hash to history_hashes.
        # If we play point 2 as BLACK, new hash = current ^ ZOBRIST_BLACK[2].
        from polyclash.game.board import ZOBRIST_BLACK

        future_hash = board.zobrist_hash ^ ZOBRIST_BLACK[2]
        board.history_hashes.add(future_hash)

        with pytest.raises(ValueError, match="superko violation"):
            board.play(2, BLACK, turn_check=False)
        # The stone should have been removed (undone)
        assert board.board[2] == 0

    def test_simulated_board_illegal_move(self) -> None:
        """Lines 346-349: SimulatedBoard.simulate_score catches ValueError."""
        from polyclash.game.board import SimulatedBoard

        board = Board()
        board.disable_notification()
        sim = SimulatedBoard()
        sim.redirect(board)

        # Force play to raise ValueError
        with patch.object(sim, "play", side_effect=ValueError("illegal")):
            score, gain = sim.simulate_score(0, 5, BLACK)
        assert score == -float("inf")
        assert gain == 0

    def test_simulated_board_restore_captures(self) -> None:
        """Line 355: SimulatedBoard restores captured stones in simulation."""
        from polyclash.game.board import SimulatedBoard

        board = Board()
        board.disable_notification()
        # Place a WHITE stone that will be captured when BLACK plays nearby
        # Use point 0 and its neighbors
        target = 0
        board.board[target] = WHITE
        for n in neighbors[target]:
            if n != target:
                board.board[n] = BLACK

        sim = SimulatedBoard()
        sim.redirect(board)
        sim.current_player = BLACK

        # Find an empty point to simulate playing
        empties = sim.get_empties(BLACK)
        if empties:
            with patch("polyclash.game.board.sample", return_value=[empties[0]]):
                sim.simulate_score(0, empties[0], BLACK)


# ===================================================================
# Server tests
# ===================================================================


class TestServerCoverageGaps:
    """Cover missed lines in polyclash/server.py."""

    @pytest.fixture(autouse=True)
    def _setup(self, test_client, storage):
        self.client = test_client
        self.storage = storage

    # -- Line 142: invalid token → 401 --
    def test_invalid_token(self) -> None:
        resp = self.client.post("/sphgo/new", json={"token": "totally_bogus_token_xyz"})
        assert resp.status_code == 401
        assert resp.get_json()["message"] == "invalid token"

    # -- Lines 147-149: exception handler → 500 --
    def test_api_call_exception(self) -> None:
        game = _setup_game(self.client, self.storage)
        # Don't add a board → accessing boards[game_id] raises KeyError
        server.boards.pop(game["game_id"], None)
        resp = self.client.post("/sphgo/state", json={"token": game["black_token"]})
        assert resp.status_code == 500

    # -- Lines 51-54: solo mode redirect --
    def test_solo_mode_redirect(self) -> None:
        old_token = server.server_token
        try:
            server.server_token = "fixed_tok"
            with patch.dict("os.environ", {"POLYCLASH_SOLO_MODE": "1"}):
                resp = self.client.get("/")
            assert resp.status_code == 302
            assert "token=fixed_tok" in resp.headers["Location"]
        finally:
            server.server_token = old_token

    # -- Lines 119-127: skip_auth (POLYCLASH_NO_AUTH) --
    def test_skip_auth_mode(self) -> None:
        with patch.dict("os.environ", {"POLYCLASH_NO_AUTH": "1"}):
            game = _setup_game(self.client, self.storage)
            resp = self.client.post(
                "/sphgo/ready_status",
                json={"token": game["black_token"], "role": "black"},
            )
            assert resp.status_code == 200

    # -- Line 133: game not found in authed branch --
    def test_api_call_game_not_found(self) -> None:
        game = _setup_game(self.client, self.storage)
        # Make exists() return False while token is still valid
        with patch.object(self.storage, "exists", return_value=False):
            resp = self.client.post(
                "/sphgo/ready_status", json={"token": game["black_token"]}
            )
        assert resp.status_code == 404
        assert resp.get_json()["message"] == "Game not found"

    # -- Line 100: player_canceled (just pass) --
    def test_player_canceled(self) -> None:
        game = _setup_game(self.client, self.storage)
        resp = self.client.post("/sphgo/cancel", json={"token": game["black_token"]})
        assert resp.status_code == 200

    # -- Lines 230-231: join invalid role --
    def test_join_invalid_role(self) -> None:
        game = _setup_game(self.client, self.storage)
        # Join as viewer first to get a viewer token with role != black/white
        resp = self.client.post(
            "/sphgo/join",
            json={"token": game["viewer_key"], "role": "invalid_role"},
        )
        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Invalid role"

    # -- Lines 248, 250: ready_status invalid role --
    def test_ready_status_invalid_role(self) -> None:
        game = _setup_game(self.client, self.storage)
        # Join as viewer
        resp = self.client.post(
            "/sphgo/join", json={"token": game["viewer_key"], "role": "viewer"}
        )
        assert resp.status_code == 200
        viewer_token = resp.get_json()["token"]
        resp = self.client.post("/sphgo/ready_status", json={"token": viewer_token})
        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Invalid role"

    # -- Line 260: ready invalid role --
    def test_ready_invalid_role(self) -> None:
        game = _setup_game(self.client, self.storage)
        resp = self.client.post(
            "/sphgo/join", json={"token": game["viewer_key"], "role": "viewer"}
        )
        viewer_token = resp.get_json()["token"]
        resp = self.client.post("/sphgo/ready", json={"token": viewer_token})
        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Invalid role"

    # -- Line 271: cancel invalid role --
    def test_cancel_invalid_role(self) -> None:
        game = _setup_game(self.client, self.storage)
        resp = self.client.post(
            "/sphgo/join", json={"token": game["viewer_key"], "role": "viewer"}
        )
        viewer_token = resp.get_json()["token"]
        resp = self.client.post("/sphgo/cancel", json={"token": viewer_token})
        assert resp.status_code == 400

    # -- Lines 315, 318: genmove returns pass (board.genmove → None) --
    def test_genmove_pass(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        original_hrm = server._hrm_player
        server._hrm_player = None
        try:
            with patch.object(board, "rank_moves", return_value=[]):
                resp = self.client.post(
                    "/sphgo/genmove", json={"token": game["black_token"]}
                )
            assert resp.status_code == 200
            assert resp.get_json()["message"] == "pass"
            assert resp.get_json()["point"] is None
        finally:
            server._hrm_player = original_hrm

    # -- genmove AI move illegal, fallback exhausted → pass --
    def test_genmove_illegal_move(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        original_hrm = server._hrm_player
        server._hrm_player = None
        try:
            with patch.object(board, "rank_moves", return_value=[5]):
                with patch.object(board, "play", side_effect=ValueError("illegal")):
                    resp = self.client.post(
                        "/sphgo/genmove", json={"token": game["black_token"]}
                    )
            assert resp.status_code == 200
            assert resp.get_json()["message"] == "pass"
        finally:
            server._hrm_player = original_hrm

    # -- HRM genmove exception fallback --
    def test_genmove_hrm_exception_fallback(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        mock_hrm = MagicMock()
        mock_hrm.genmove.side_effect = RuntimeError("HRM crashed")
        original_hrm = server._hrm_player
        server._hrm_player = mock_hrm
        try:
            with patch.object(board, "rank_moves", return_value=[]):
                resp = self.client.post(
                    "/sphgo/genmove", json={"token": game["black_token"]}
                )
            assert resp.status_code == 200
            assert resp.get_json()["message"] == "pass"
        finally:
            server._hrm_player = original_hrm

    # -- genmove game_over after AI move --
    def test_genmove_game_over(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        original_hrm = server._hrm_player
        server._hrm_player = None
        try:
            with patch.object(board, "rank_moves", return_value=[0]):
                with patch.object(board, "is_game_over", return_value=True):
                    resp = self.client.post(
                        "/sphgo/genmove", json={"token": game["black_token"]}
                    )
            assert resp.status_code == 200
            assert resp.get_json()["point"] == 0
        finally:
            server._hrm_player = original_hrm

    # -- Line 375: play invalid play code --
    def test_play_invalid_code(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        resp = self.client.post(
            "/sphgo/play",
            json={
                "token": game["black_token"],
                "steps": 0,
                "play": [999, 998, 997],
            },
        )
        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Invalid play"

    # -- Lines 384-385: play board.play raises ValueError --
    def test_play_board_error(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        valid_play_str = list(valid_plays)[0]
        valid_play = [int(x) for x in valid_play_str.split(",")]

        with patch.object(board, "play", side_effect=ValueError("bad move")):
            resp = self.client.post(
                "/sphgo/play",
                json={
                    "token": game["black_token"],
                    "steps": 0,
                    "play": valid_play,
                },
            )
        assert resp.status_code == 400
        assert "bad move" in resp.get_json()["message"]

    # -- Lines 396-398: play game_over after successful play --
    def test_play_game_over(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        valid_play_str = list(valid_plays)[0]
        valid_play = [int(x) for x in valid_play_str.split(",")]

        with patch.object(board, "is_game_over", return_value=True):
            resp = self.client.post(
                "/sphgo/play",
                json={
                    "token": game["black_token"],
                    "steps": 0,
                    "play": valid_play,
                },
            )
        assert resp.status_code == 200

    # -- Line 412: resign invalid role --
    def test_resign_invalid_role(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        resp = self.client.post(
            "/sphgo/join", json={"token": game["viewer_key"], "role": "viewer"}
        )
        viewer_token = resp.get_json()["token"]
        resp = self.client.post("/sphgo/resign", json={"token": viewer_token})
        assert resp.status_code == 400
        assert resp.get_json()["message"] == "Invalid role"

    # -- Lines 427-429: record endpoint --
    def test_record_endpoint(self) -> None:
        game = _setup_game(self.client, self.storage)
        board = Board()
        board.disable_notification()
        server.boards[game["game_id"]] = board

        # Make a move so the record has data
        board.play(0, BLACK)
        board.switch_player()

        resp = self.client.post("/sphgo/record", json={"token": game["black_token"]})
        assert resp.status_code == 200
        data = resp.get_json()
        assert "metadata" in data
        assert "moves" in data
        assert len(data["moves"]) == 1

    # -- Lines 188-189: whoami exception handler --
    def test_whoami_exception(self) -> None:
        game = _setup_game(self.client, self.storage)
        with patch.object(
            self.storage, "get_role", side_effect=RuntimeError("db error")
        ):
            resp = self.client.post("/sphgo/whoami", json={"key": game["black_token"]})
        assert resp.status_code == 401
        assert resp.get_json()["message"] == "Invalid key"

    # -- Lines 475-478, 484: main() function --
    def test_main_function(self) -> None:
        with patch.object(server.socketio, "run") as mock_run:
            server.main()
            mock_run.assert_called_once()
            call_kwargs = mock_run.call_args
            assert call_kwargs[1]["port"] == 3302
