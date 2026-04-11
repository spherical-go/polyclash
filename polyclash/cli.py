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
    family_parser.add_argument(
        "--black",
        choices=["human", "ai"],
        default="human",
        help="Who controls black (default: human)",
    )
    family_parser.add_argument(
        "--white",
        choices=["human", "ai"],
        default="human",
        help="Who controls white (default: human)",
    )

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

    # --- polyclash team (self-hosted team server) ---
    team_parser = sub.add_parser(
        "team", help="Self-hosted team server with user accounts"
    )
    team_parser.add_argument("--host", default="0.0.0.0")
    team_parser.add_argument(
        "--port", type=int, default=int(os.environ.get("PORT", 3302))
    )
    team_parser.add_argument(
        "--rooms",
        type=int,
        default=int(os.environ.get("POLYCLASH_MAX_ROOMS", "8")),
        help="Max simultaneous games (default: 8, env: POLYCLASH_MAX_ROOMS)",
    )
    team_parser.add_argument(
        "--admin-user",
        default=os.environ.get("POLYCLASH_ADMIN_USER", "admin"),
        help="Admin username (default: admin, env: POLYCLASH_ADMIN_USER)",
    )
    team_parser.add_argument(
        "--admin-pass",
        default=os.environ.get("POLYCLASH_ADMIN_PASS"),
        help="Admin password (auto-generated if omitted, env: POLYCLASH_ADMIN_PASS)",
    )
    team_parser.add_argument(
        "--invites",
        type=int,
        default=int(os.environ.get("POLYCLASH_INVITES", "5")),
        help="Initial invite codes to generate (default: 5, env: POLYCLASH_INVITES)",
    )
    team_parser.add_argument(
        "--db",
        default=os.environ.get("POLYCLASH_AUTH_DB"),
        help="Path to SQLite user database (env: POLYCLASH_AUTH_DB)",
    )

    args = parser.parse_args()

    if args.command == "solo":
        _run_solo(args.port, args.side)
    elif args.command == "family":
        _run_family(args.port, args.black, args.white)
    elif args.command == "serve":
        _run_serve(args.host, args.port, args.no_auth, args.token)
    elif args.command == "team":
        _run_team(
            args.host,
            args.port,
            args.rooms,
            args.admin_user,
            args.admin_pass,
            args.invites,
            args.db,
        )
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


def _run_family(port: int, black: str = "human", white: str = "human") -> None:
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

    black_ai = "&ai=1" if black == "ai" else ""
    white_ai = "&ai=1" if white == "ai" else ""
    black_url = f"{base}/?key={data['black_key']}{black_ai}"
    white_url = f"{base}/?key={data['white_key']}{white_ai}"
    viewer_url = f"{base}/?key={data['viewer_key']}"

    black_label = "AI" if black == "ai" else "Human"
    white_label = "AI" if white == "ai" else "Human"

    logger.info("PolyClash 星逐 — Family Game")
    logger.info(f"  Black ({black_label}): {black_url}")
    logger.info(f"  White ({white_label}): {white_url}")
    logger.info(f"  Watch: {viewer_url}")

    # Auto-open the first human side, or black if both are AI
    if black == "human":
        auto_url = black_url
    elif white == "human":
        auto_url = white_url
    else:
        auto_url = black_url
    Timer(1.5, lambda: webbrowser.open(auto_url)).start()

    socketio.run(
        app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True, debug=False
    )


def _run_team(
    host: str,
    port: int,
    rooms: int,
    admin_user: str,
    admin_pass: Optional[str],
    invites: int,
    db: Optional[str],
) -> None:
    """Start server in team mode with user accounts and room limits."""
    os.environ["POLYCLASH_TEAM_MODE"] = "1"
    os.environ["POLYCLASH_MAX_ROOMS"] = str(rooms)
    # Team mode uses lobby auth, not server token
    token = secrets.token_hex(16)
    os.environ["POLYCLASH_SERVER_TOKEN"] = token
    if db:
        os.environ["POLYCLASH_AUTH_DB"] = db

    from polyclash.util.auth import UserStore
    from polyclash.util.logging import logger

    user_store = UserStore(db_path=db)

    # Ensure admin account
    if not admin_pass:
        admin_pass = secrets.token_urlsafe(12)
    user_store.ensure_admin(admin_user, admin_pass)

    # Generate initial invite codes
    codes = [user_store.create_invite(created_by=admin_user) for _ in range(invites)]

    import polyclash.server as server_module
    from polyclash.server import app, restore_boards, socketio

    server_module._user_store = user_store
    server_module.MAX_ROOMS = rooms
    restore_boards()

    lan_ip = _get_lan_ip()
    logger.info("PolyClash 星逐 — Team Server")
    logger.info(f"  URL: http://{lan_ip}:{port}/")
    logger.info(f"  Max rooms: {rooms}")
    logger.info(f"  Admin: {admin_user} / {admin_pass}")
    logger.info(f"  Invite codes ({len(codes)}):")
    for code in codes:
        logger.info(f"    {code}")

    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True, debug=False)


def _run_serve(host: str, port: int, no_auth: bool, token: Optional[str]) -> None:
    """Start server for LAN/network play."""
    if no_auth:
        os.environ["POLYCLASH_NO_AUTH"] = "1"
    if token:
        os.environ["POLYCLASH_SERVER_TOKEN"] = token

    from polyclash.util.logging import logger

    logger.info(f"Serving on {host}:{port}")

    from polyclash.server import app, restore_boards, server_token, socketio

    restore_boards()

    if not no_auth:
        logger.info(f"Server token: {server_token}")

    socketio.run(app, host=host, port=port, allow_unsafe_werkzeug=True, debug=False)


if __name__ == "__main__":
    main()
