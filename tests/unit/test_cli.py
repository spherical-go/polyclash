"""Tests for polyclash.cli — covers _get_lan_ip, main, _run_solo, _run_family, _run_serve."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# _get_lan_ip
# ---------------------------------------------------------------------------


class TestGetLanIp:
    def test_returns_ip_on_success(self) -> None:
        mock_sock = MagicMock()
        mock_sock.getsockname.return_value = ("192.168.1.42", 12345)

        with patch("polyclash.cli.socket.socket", return_value=mock_sock):
            from polyclash.cli import _get_lan_ip

            result = _get_lan_ip()

        assert result == "192.168.1.42"
        mock_sock.connect.assert_called_once_with(("8.8.8.8", 80))
        mock_sock.close.assert_called_once()

    def test_returns_localhost_on_exception(self) -> None:
        mock_sock = MagicMock()
        mock_sock.connect.side_effect = OSError("no network")

        with patch("polyclash.cli.socket.socket", return_value=mock_sock):
            from polyclash.cli import _get_lan_ip

            result = _get_lan_ip()

        assert result == "localhost"


# ---------------------------------------------------------------------------
# main() dispatcher
# ---------------------------------------------------------------------------


class TestMain:
    @patch("polyclash.cli._run_solo")
    def test_solo_default_args(self, mock_run_solo: MagicMock) -> None:
        with patch("sys.argv", ["polyclash", "solo"]):
            from polyclash.cli import main

            main()

        mock_run_solo.assert_called_once_with(3302, "black")

    @patch("polyclash.cli._run_solo")
    def test_solo_custom_args(self, mock_run_solo: MagicMock) -> None:
        with patch(
            "sys.argv", ["polyclash", "solo", "--port", "4000", "--side", "white"]
        ):
            from polyclash.cli import main

            main()

        mock_run_solo.assert_called_once_with(4000, "white")

    @patch("polyclash.cli._run_family")
    def test_family_default_args(self, mock_run_family: MagicMock) -> None:
        with patch("sys.argv", ["polyclash", "family"]):
            from polyclash.cli import main

            main()

        mock_run_family.assert_called_once_with(3302)

    @patch("polyclash.cli._run_family")
    def test_family_custom_port(self, mock_run_family: MagicMock) -> None:
        with patch("sys.argv", ["polyclash", "family", "--port", "5000"]):
            from polyclash.cli import main

            main()

        mock_run_family.assert_called_once_with(5000)

    @patch("polyclash.cli._run_serve")
    def test_serve_default_args(self, mock_run_serve: MagicMock) -> None:
        with patch("sys.argv", ["polyclash", "serve"]):
            from polyclash.cli import main

            main()

        mock_run_serve.assert_called_once_with("0.0.0.0", 3302, False, None)

    @patch("polyclash.cli._run_serve")
    def test_serve_custom_args(self, mock_run_serve: MagicMock) -> None:
        with patch(
            "sys.argv",
            [
                "polyclash",
                "serve",
                "--host",
                "127.0.0.1",
                "--port",
                "8080",
                "--no-auth",
                "--token",
                "mytoken",
            ],
        ):
            from polyclash.cli import main

            main()

        mock_run_serve.assert_called_once_with("127.0.0.1", 8080, True, "mytoken")

    def test_no_command_prints_help(self, capsys: pytest.CaptureFixture[str]) -> None:
        with patch("sys.argv", ["polyclash"]):
            from polyclash.cli import main

            main()

        captured = capsys.readouterr()
        assert "usage:" in captured.out.lower() or "polyclash" in captured.out.lower()


# ---------------------------------------------------------------------------
# _run_solo
# ---------------------------------------------------------------------------


class TestRunSolo:
    _ENV_KEYS = ("POLYCLASH_SERVER_TOKEN", "POLYCLASH_SOLO_MODE", "POLYCLASH_SIDE")

    @patch("polyclash.cli.secrets.token_hex", return_value="fixedtoken")
    @patch("polyclash.cli.webbrowser.open")
    @patch("polyclash.cli.Timer")
    def test_run_solo(
        self,
        mock_timer_cls: MagicMock,
        mock_wb_open: MagicMock,
        mock_token_hex: MagicMock,
    ) -> None:
        mock_socketio = MagicMock()
        mock_app = MagicMock()

        with patch.dict("os.environ", {}, clear=False):
            with patch.dict(
                "sys.modules",
                {
                    "polyclash.server": MagicMock(app=mock_app, socketio=mock_socketio),
                    "polyclash.util.logging": MagicMock(),
                },
            ):
                from polyclash.cli import _run_solo

                _run_solo(3302, "black")

        mock_timer_cls.assert_called_once()
        mock_socketio.run.assert_called_once_with(
            mock_app,
            host="127.0.0.1",
            port=3302,
            allow_unsafe_werkzeug=True,
            debug=False,
        )

    @patch("polyclash.cli.secrets.token_hex", return_value="tok123")
    @patch("polyclash.cli.webbrowser.open")
    @patch("polyclash.cli.Timer")
    def test_run_solo_sets_env(
        self,
        mock_timer_cls: MagicMock,
        mock_wb_open: MagicMock,
        mock_token_hex: MagicMock,
    ) -> None:
        mock_socketio = MagicMock()
        mock_app = MagicMock()

        with patch.dict("os.environ", {}, clear=False) as env:
            with patch.dict(
                "sys.modules",
                {
                    "polyclash.server": MagicMock(app=mock_app, socketio=mock_socketio),
                    "polyclash.util.logging": MagicMock(),
                },
            ):
                from polyclash.cli import _run_solo

                _run_solo(4000, "white")

            assert env.get("POLYCLASH_SERVER_TOKEN") == "tok123"
            assert env.get("POLYCLASH_SOLO_MODE") == "1"
            assert env.get("POLYCLASH_SIDE") == "white"


# ---------------------------------------------------------------------------
# _run_family
# ---------------------------------------------------------------------------


class TestRunFamily:
    @patch("polyclash.cli.secrets.token_hex", return_value="famtoken")
    @patch("polyclash.cli.webbrowser.open")
    @patch("polyclash.cli.Timer")
    @patch("polyclash.cli._get_lan_ip", return_value="10.0.0.5")
    def test_run_family(
        self,
        mock_lan_ip: MagicMock,
        mock_timer_cls: MagicMock,
        mock_wb_open: MagicMock,
        mock_token_hex: MagicMock,
    ) -> None:
        mock_socketio = MagicMock()
        mock_app = MagicMock()
        mock_storage = MagicMock()
        mock_storage.create_room.return_value = {
            "game_id": "g1",
            "black_key": "bk",
            "white_key": "wk",
            "viewer_key": "vk",
        }
        mock_boards: dict[str, MagicMock] = {}
        mock_board_cls = MagicMock()

        mock_server_mod = MagicMock(
            app=mock_app,
            socketio=mock_socketio,
            storage=mock_storage,
            boards=mock_boards,
        )

        with patch.dict("os.environ", {}, clear=False):
            with patch.dict(
                "sys.modules",
                {
                    "polyclash.server": mock_server_mod,
                    "polyclash.game.board": MagicMock(Board=mock_board_cls),
                    "polyclash.util.logging": MagicMock(),
                },
            ):
                from polyclash.cli import _run_family

                _run_family(3302)

        mock_storage.create_room.assert_called_once()
        mock_timer_cls.assert_called_once()
        mock_socketio.run.assert_called_once_with(
            mock_app, host="0.0.0.0", port=3302, allow_unsafe_werkzeug=True, debug=False
        )


# ---------------------------------------------------------------------------
# _run_serve
# ---------------------------------------------------------------------------


class TestRunServe:
    def test_run_serve_with_no_auth(self) -> None:
        mock_socketio = MagicMock()
        mock_app = MagicMock()

        mock_server_mod = MagicMock(
            app=mock_app,
            socketio=mock_socketio,
            server_token="unused",
        )

        with patch.dict("os.environ", {}, clear=False) as env:
            with patch.dict(
                "sys.modules",
                {
                    "polyclash.server": mock_server_mod,
                    "polyclash.util.logging": MagicMock(),
                },
            ):
                from polyclash.cli import _run_serve

                _run_serve("0.0.0.0", 8080, no_auth=True, token=None)

            assert env.get("POLYCLASH_NO_AUTH") == "1"

        mock_socketio.run.assert_called_once_with(
            mock_app, host="0.0.0.0", port=8080, allow_unsafe_werkzeug=True, debug=False
        )

    def test_run_serve_with_token(self) -> None:
        mock_socketio = MagicMock()
        mock_app = MagicMock()

        mock_server_mod = MagicMock(
            app=mock_app,
            socketio=mock_socketio,
            server_token="mytoken",
        )

        with patch.dict("os.environ", {}, clear=False) as env:
            with patch.dict(
                "sys.modules",
                {
                    "polyclash.server": mock_server_mod,
                    "polyclash.util.logging": MagicMock(),
                },
            ):
                from polyclash.cli import _run_serve

                _run_serve("127.0.0.1", 3302, no_auth=False, token="mytoken")

            assert env.get("POLYCLASH_SERVER_TOKEN") == "mytoken"

        mock_socketio.run.assert_called_once()

    def test_run_serve_no_auth_false_no_token(self) -> None:
        mock_socketio = MagicMock()
        mock_app = MagicMock()

        mock_server_mod = MagicMock(
            app=mock_app,
            socketio=mock_socketio,
            server_token="auto",
        )

        with patch.dict("os.environ", {}, clear=False) as env:
            # Remove these if present from prior tests
            env.pop("POLYCLASH_NO_AUTH", None)
            env.pop("POLYCLASH_SERVER_TOKEN", None)

            with patch.dict(
                "sys.modules",
                {
                    "polyclash.server": mock_server_mod,
                    "polyclash.util.logging": MagicMock(),
                },
            ):
                from polyclash.cli import _run_serve

                _run_serve("0.0.0.0", 3302, no_auth=False, token=None)

            # no_auth=False should NOT set POLYCLASH_NO_AUTH
            assert env.get("POLYCLASH_NO_AUTH") is None

        mock_socketio.run.assert_called_once()
