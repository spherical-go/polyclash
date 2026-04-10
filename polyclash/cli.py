"""Unified CLI for PolyClash — play solo, serve on LAN, or deploy publicly."""

from __future__ import annotations

import argparse
import os
import secrets
import webbrowser
from threading import Timer
from typing import Optional


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="polyclash",
        description="PolyClash: Go on a Spherical Universe",
    )
    sub = parser.add_subparsers(dest="command")

    # --- polyclash play ---
    play_parser = sub.add_parser("play", help="Solo play: start server + open browser")
    play_parser.add_argument("--port", type=int, default=3302)

    # --- polyclash serve ---
    serve_parser = sub.add_parser("serve", help="Start server for LAN/network play")
    serve_parser.add_argument("--host", default="0.0.0.0")
    serve_parser.add_argument("--port", type=int, default=3302)
    serve_parser.add_argument(
        "--no-auth", action="store_true", help="Disable server token requirement"
    )
    serve_parser.add_argument(
        "--token", default=None, help="Set server token (default: auto-generated)"
    )

    # --- polyclash client --- (legacy PyQt client)
    sub.add_parser("client", help="Launch desktop PyQt client")

    args = parser.parse_args()

    if args.command == "play":
        _run_solo(args.port)
    elif args.command == "serve":
        _run_serve(args.host, args.port, args.no_auth, args.token)
    elif args.command == "client":
        from polyclash.client import main as client_main

        client_main()
    else:
        parser.print_help()


def _run_solo(port: int) -> None:
    """Start server in solo mode and open browser."""
    token = secrets.token_hex(16)
    os.environ["POLYCLASH_SERVER_TOKEN"] = token
    os.environ["POLYCLASH_SOLO_MODE"] = "1"

    from polyclash.util.logging import logger

    logger.info(f"Solo mode on port {port}")

    # Open browser after a short delay
    url = f"http://localhost:{port}/?token={token}"
    Timer(1.5, lambda: webbrowser.open(url)).start()

    from polyclash.server import app, socketio

    socketio.run(
        app, host="127.0.0.1", port=port, allow_unsafe_werkzeug=True, debug=False
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
