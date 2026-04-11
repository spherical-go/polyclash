"""Unified CLI for PolyClash — solo, family, serve."""

from __future__ import annotations

import argparse
import os
import secrets
import socket
import webbrowser
from threading import Timer
from typing import Optional


def _get_lan_ip() -> str:
    """Return the LAN IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip: str = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="polyclash",
        description="PolyClash: Go on a Spherical Universe",
    )
    sub = parser.add_subparsers(dest="command")

    # --- polyclash solo ---
    solo_parser = sub.add_parser("solo", help="Solo play: human vs AI")
    solo_parser.add_argument(
        "--side",
        choices=["black", "white"],
        default="black",
        help="Your color (default: black)",
    )
    solo_parser.add_argument("--port", type=int, default=3302)

    # --- polyclash family ---
    family_parser = sub.add_parser("family", help="Family game on LAN")
    family_parser.add_argument("--port", type=int, default=3302)

    # --- polyclash serve (deployment) ---
    serve_parser = sub.add_parser("serve", help="Start server for deployment")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument(
        "--port", type=int, default=int(os.environ.get("PORT", 3302))
    )
    serve_parser.add_argument(
        "--no-auth", action="store_true", help="Disable server token requirement"
    )
    serve_parser.add_argument(
        "--token", default=None, help="Set server token (default: auto-generated)"
    )

    args = parser.parse_args()

    if args.command == "solo":
        _run_solo(args.port, args.side)
    elif args.command == "family":
        _run_family(args.port)
    elif args.command == "serve":
        _run_serve(args.host, args.port, args.no_auth, args.token)
    else:
        parser.print_help()


def _run_solo(port: int, side: str = "black") -> None:
    """Start server in solo mode and open browser."""
    token = secrets.token_hex(16)
    os.environ["POLYCLASH_SERVER_TOKEN"] = token
    os.environ["POLYCLASH_SOLO_MODE"] = "1"
    os.environ["POLYCLASH_SIDE"] = side

    from polyclash.util.logging import logger

    logger.info(f"Solo mode on port {port}, playing as {side}")

    url = f"http://localhost:{port}/?token={token}&side={side}"
    Timer(1.5, lambda: webbrowser.open(url)).start()

    from polyclash.server import app, socketio

    socketio.run(
        app, host="127.0.0.1", port=port, allow_unsafe_werkzeug=True, debug=False
    )


def _run_family(port: int) -> None:
    """Start server in family mode: create a game and print invite URLs."""
    token = secrets.token_hex(16)
    os.environ["POLYCLASH_SERVER_TOKEN"] = token

    from polyclash.game.board import Board
    from polyclash.server import app, boards, socketio, storage
    from polyclash.util.logging import logger

    # Pre-create a game room
    data = storage.create_room()
    game_id = data["game_id"]
    board = Board()
    board.disable_notification()
    boards[game_id] = board

    lan_ip = _get_lan_ip()
    base = f"http://{lan_ip}:{port}"

    logger.info("PolyClash 星逐 — Family Game")
    logger.info(f"  Black: {base}/?key={data['black_key']}")
    logger.info(f"  White: {base}/?key={data['white_key']}")
    logger.info(f"  Watch: {base}/?key={data['viewer_key']}")

    Timer(1.5, lambda: webbrowser.open(f"{base}/?key={data['black_key']}")).start()

    socketio.run(
        app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True, debug=False
    )


def _run_serve(host: str, port: int, no_auth: bool, token: Optional[str]) -> None:
    """Start server for LAN/network play."""
    if no_auth:
        os.environ["POLYCLASH_NO_AUTH"] = "1"
    if token:
        os.environ["POLYCLASH_SERVER_TOKEN"] = token

    from polyclash.util.logging import logger

    logger.info(f"Serving on {host}:{port}")

    from polyclash.server import app, server_token, socketio

    if not no_auth:
        logger.info(f"Server token: {server_token}")

    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True, debug=False)


if __name__ == "__main__":
    main()
