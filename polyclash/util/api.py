from __future__ import annotations

from typing import Optional, Tuple

import requests

# Module-scoped shared state for client/server interactions
shared_server: Optional[str] = None
game_token: Optional[str] = None

player_key: Optional[str] = None
viewer_key: Optional[str] = None

player_token: Optional[str] = None


def get_server() -> Optional[str]:
    """Return the currently configured server URL if any."""
    return shared_server


def set_server(server: Optional[str]) -> None:
    """Set the shared server URL (or clear it if None)."""
    global shared_server
    shared_server = server


def set_game_token(token: Optional[str]) -> None:
    """Set the game token used for closing the game on the server."""
    global game_token
    game_token = token


def set_player_key(key: Optional[str]) -> None:
    """Store the player's key (not to be confused with player token)."""
    global player_key
    player_key = key


def set_player_token(token: Optional[str]) -> None:
    """Set the player token used for authenticated API calls."""
    global player_token
    player_token = token


def set_viewer_key(key: Optional[str]) -> None:
    """Store the viewer key for spectating games."""
    global viewer_key
    viewer_key = key


def connect(server: str, token: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """
    Create a new game on the server.

    Returns a tuple of (black_key, white_key, viewer_key) on success.
    Raises ValueError with error message on failure.
    """
    set_server(server)
    set_game_token(token)
    try:
        resp = requests.post(f"{server}/sphgo/new", json={"token": token})
        if resp.status_code == 200:
            data = resp.json()
            black_key = data.get("black_key")
            white_key = data.get("white_key")
            viewer_key_local = data.get("viewer_key")
            return black_key, white_key, viewer_key_local
        else:
            raise ValueError(resp.json().get("message"))
    except requests.exceptions.ConnectionError:
        # when the server is not reachable
        raise ValueError("Server not reachable when we start the game")


def get_game_status(status_type: str, server: str, token: Optional[str]) -> str:
    """
    Fetch joined/ready status from the server and return a normalized string.

    Possible return values:
      - \"Both\"
      - \"Black\"
      - \"White\"
      - \"Neither\"
      - \"None\" (when token is not provided)
    """
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return "None"

    resp = requests.post(f"{server}/sphgo/{status_type}_status", json={"token": token})
    if resp.status_code == 200:
        status = resp.json().get("status")
        # status expected to be a mapping with boolean flags for 'black' and 'white'
        if status["black"] and status["white"]:
            return "Both"
        elif status["black"]:
            return "Black"
        elif status["white"]:
            return "White"
        else:
            return "Neither"
    else:
        raise ValueError(resp.json().get("message"))


def joined_status(server: str, token: Optional[str]) -> str:
    """Helper to retrieve the 'joined' status."""
    return get_game_status("joined", server, token)


def join(server: str, role: str, token: Optional[str]) -> Optional[str]:
    """
    Join a game for a specific role.
    Returns \"Ready\" on success, None if token not provided, raises ValueError on error.
    """
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return None

    resp = requests.post(f"{server}/sphgo/join", json={"token": token, "role": role})
    if resp.status_code == 200:
        return "Ready"
    else:
        raise ValueError(resp.json().get("message"))


def ready_status(server: str, token: Optional[str]) -> str:
    """Helper to retrieve the 'ready' status."""
    return get_game_status("ready", server, token)


def ready(server: str, role: str, token: Optional[str]) -> Optional[str]:
    """
    Mark the player as ready.
    Returns \"Ready\" on success, None if token not provided, raises ValueError on error.
    """
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return None

    resp = requests.post(f"{server}/sphgo/ready", json={"token": token, "role": role})
    if resp.status_code == 200:
        return "Ready"
    else:
        raise ValueError(resp.json().get("message"))


def cancel(server: str, role: str, token: Optional[str]) -> Optional[str]:
    """
    Cancel the game for the current player.
    Returns \"Canceled\" on success, None if token not provided, raises ValueError on error.
    """
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return None

    resp = requests.post(f"{server}/sphgo/cancel", json={"token": token, "role": role})
    if resp.status_code == 200:
        return "Canceled"
    else:
        raise ValueError(resp.json().get("message"))


def play(server: str, steps: int, play: list[int]) -> None:
    """
    Send a play command to the server.

    Raises ValueError when player token is not set or on server/network errors.
    """
    set_server(server)
    if player_token is None:
        raise ValueError("Player token not set")
    try:
        resp = requests.post(
            f"{server}/sphgo/play",
            json={
                "token": player_token,
                "steps": steps,
                "play": [int(city) for city in play],
            },
        )
        if resp.status_code != 200:
            raise ValueError(resp.json().get("message"))
    except requests.exceptions.ConnectionError:
        raise ValueError("Server not reachable when we play the game")


def close(server: str) -> None:
    """
    Close the game on the server using the game token if present.

    Raises ValueError on server/network errors.
    """
    if game_token is not None:
        try:
            resp = requests.post(f"{server}/sphgo/close", json={"token": game_token})
            if resp.status_code != 200:
                raise ValueError(resp.json().get("message"))
        except requests.exceptions.ConnectionError:
            raise ValueError("Server not reachable when we close the game")
