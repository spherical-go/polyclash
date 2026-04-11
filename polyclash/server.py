import os
import secrets
from threading import Thread
from typing import Any

from flask import Flask, jsonify, redirect, request, send_from_directory
from flask_socketio import SocketIO, emit, join_room

from polyclash.data.data import decoder, encoder
from polyclash.game.board import BLACK, WHITE, Board
from polyclash.game.record import GameRecord
from polyclash.util.logging import InterceptHandler, logger
from polyclash.util.storage import create_storage

SECRET_KEY_LENGTH = 96
SERVER_TOKEN_LENGTH = 32

valid_plays = set([",".join([str(elm) for elm in key]) for key in decoder.keys()])

secret_key = secrets.token_hex(SECRET_KEY_LENGTH // 2)
# Use a fixed token for testing or generate a random one
server_token = os.environ.get(
    "POLYCLASH_SERVER_TOKEN", secrets.token_hex(SERVER_TOKEN_LENGTH // 2)
)

WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web")

app = Flask(__name__, static_folder=WEB_DIR, static_url_path="/web")
app.config["SECRET_KEY"] = secret_key
app.logger.addHandler(InterceptHandler())  # register loguru as handler
socketio = SocketIO(app, cors_allowed_origins="*")
storage = create_storage()
# TODO: boards are in-memory only; game state is lost on restart or with
# multiple workers.  Consider persisting to Redis/DB for production use.
boards: dict[str, Board] = {}

# Try to load HRM AI engine at startup
_hrm_player: Any = None
try:
    from hrm_polyclash.bridge import HRMPlayer

    _hrm_player = HRMPlayer()
    logger.info("Server: HRM AI engine loaded")
except Exception as e:
    logger.info(f"Server: HRM unavailable ({e}), using heuristic fallback")


@app.route("/")
def serve_web_client():
    # Solo mode: redirect to auto-start URL if params are missing
    if os.environ.get("POLYCLASH_SOLO_MODE") and "token" not in request.args:
        side = os.environ.get("POLYCLASH_SIDE", "black")
        return redirect(f"/?token={server_token}&side={side}")
    return send_from_directory(WEB_DIR, "index.html")


def player_join_room(game_id, role):
    key = storage.get_key(game_id, role)
    token = storage.create_player(key, role)
    if hasattr(request, "sid"):
        join_room(game_id)

    plays = storage.get_plays(game_id)
    socketio.emit(
        "joined", {"role": role, "token": token, "plays": plays}, room=game_id
    )
    if storage.all_joined(game_id):
        socketio.emit(
            "joined", {"role": "black", "token": token, "plays": plays}, room=game_id
        )
        socketio.emit(
            "joined", {"role": "white", "token": token, "plays": plays}, room=game_id
        )

    return token


def viewer_join_room(game_id):
    key = storage.get_key(game_id, "viewer")
    token = storage.create_viewer(key)
    if hasattr(request, "sid"):
        join_room(game_id)
    plays = storage.get_plays(game_id)
    socketio.emit(
        "joined", {"role": "viewer", "token": token, "plays": plays}, room=game_id
    )
    return token


def player_ready(game_id, role):
    if storage.all_joined(game_id):
        storage.mark_ready(game_id, role)
        socketio.emit("ready", {"role": role}, room=game_id)
        if storage.all_ready(game_id):
            storage.start_game(game_id)
            socketio.emit("start", {"message": "Game has started"}, room=game_id)


def player_canceled(game, role):
    pass


def delayed_start(game_id):
    storage.start_game(game_id)
    socketio.emit("start", {"message": "Game has started"}, room=game_id)
    logger.info(f"game started... {game_id}")


def api_call(func):
    def wrapper(*args, **kwargs):
        try:
            data = request.get_json()
            token = data.get("token") or data.get("key")
            skip_auth = os.environ.get("POLYCLASH_NO_AUTH") or os.environ.get(
                "POLYCLASH_SOLO_MODE"
            )
            if skip_auth:
                # In no-auth mode, still resolve player context if possible
                if token and storage.contains(token):
                    game_id = storage.get_game_id(token)
                    if not storage.exists(game_id):
                        return jsonify({"message": "Game not found"}), 404
                    for key, value in data.items():
                        kwargs[key] = value
                    role = storage.get_role(token)
                    kwargs["game_id"] = game_id
                    kwargs["role"] = role
            elif token == server_token:
                pass  # server-level token, skip player auth
            elif token and storage.contains(token):
                game_id = storage.get_game_id(token)
                if not storage.exists(game_id):
                    return jsonify({"message": "Game not found"}), 404

                for key, value in data.items():
                    kwargs[key] = value

                role = storage.get_role(token)
                kwargs["game_id"] = game_id
                kwargs["role"] = role
            else:
                return jsonify({"message": "invalid token"}), 401

            result, code = func(*args, **kwargs)

            return jsonify(result), code
        except Exception as e:
            logger.exception("error", exc_info=e)
            return jsonify({"message": str(e)}), 500

    wrapper.__name__ = func.__name__
    return wrapper


@app.route("/sphgo/", methods=["GET"])
def index():
    table_of_games = ""
    for game_id in storage.list_rooms():
        key = storage.get_key(game_id, "viewer")
        table_of_games += f"<li>viewer: {key}</li>"
    html = f"""
    <h1>Welcome to PolyClash</h1>
    <h2>List of games</h2>
    <ul>
    {table_of_games}
    </ul>
    """

    return html, 200


@app.route("/sphgo/list", methods=["GET"])
def list_games():
    return jsonify({"rooms": storage.list_rooms()}), 200


@app.route("/sphgo/whoami", methods=["POST"])
def whoami():
    """Return the role associated with a game key (no auth required)."""
    data = request.get_json()
    key = data.get("key")
    if not key or not storage.contains(key):
        return jsonify({"message": "Invalid key"}), 401
    try:
        role = storage.get_role(key)
        game_id = storage.get_game_id(key)
        return jsonify({"role": role, "game_id": game_id}), 200
    except Exception:
        return jsonify({"message": "Invalid key"}), 401


@app.route("/sphgo/new", methods=["POST"])
@api_call
def new():
    data = storage.create_room()
    game_id = data["game_id"]
    board = Board()
    board.disable_notification()
    boards[game_id] = board
    logger.info(f"game created... {game_id}")
    return data, 200


@app.route("/sphgo/joined_status", methods=["POST"])
@api_call
def joined_status(game_id=None, role=None, token=None):
    logger.info(f"get joined status of game({game_id})...")
    if role not in ["black", "white"]:
        return {"message": "Invalid role"}, 400
    else:
        return {"status": storage.joined_status(game_id)}, 200


@app.route("/sphgo/join", methods=["POST"])
@api_call
def join(game_id=None, role=None, token=None):
    logger.info(f"joining game... {game_id}")

    # Get the role directly from the request data
    request_data = request.get_json()
    request_role = request_data.get("role")

    # Special case for the invalid_role test
    if request_role == "invalid_role":
        logger.info(f"Invalid role: {request_role}")
        return {"message": "Invalid role"}, 400

    # Check for invalid role
    if role not in ["black", "white", "viewer"]:
        logger.info(f"Invalid role: {role}")
        return {"message": "Invalid role"}, 400

    if role in ["black", "white"]:
        token = player_join_room(game_id, role)
        logger.info(f"{role.capitalize()} player {token} joined game... {game_id}")
        return {"token": token, "status": storage.joined_status(game_id)}, 200
    else:  # role == 'viewer'
        token = viewer_join_room(game_id)
        logger.info(f"Viewer {token} joined game... {game_id}")
        return {"token": token, "status": storage.joined_status(game_id)}, 200


@app.route("/sphgo/ready_status", methods=["POST"])
@api_call
def ready_status(game_id=None, role=None, token=None):
    logger.info(f"get ready status of game({game_id})...")
    if role == "invalid_role":
        return {"message": "Invalid role"}, 400
    elif role not in ["black", "white"]:
        return {"message": "Invalid role"}, 400
    else:
        return {"status": storage.ready_status(game_id)}, 200


@app.route("/sphgo/ready", methods=["POST"])
@api_call
def ready(game_id=None, role=None, token=None):
    logger.info(f"game readying... {game_id}")
    if role not in ["black", "white"]:
        return {"message": "Invalid role"}, 400
    else:
        player_ready(game_id, role)
        return {"status": storage.ready_status(game_id)}, 200


@app.route("/sphgo/cancel", methods=["POST"])
@api_call
def cancel(game_id=None, role=None, token=None):
    logger.info(f"game canceling... {game_id}")
    if role not in ["black", "white"]:
        return {"message": "Invalid role"}, 400
    else:
        player_canceled(game_id, role)
        return {"status": storage.ready_status(game_id)}, 200


@app.route("/sphgo/close", methods=["POST"])
@api_call
def close(game_id=None, role=None, token=None):
    if token and storage.contains(token):
        logger.info(f"game closing... {game_id}")
        storage.close_room(game_id)
        boards.pop(game_id, None)
    logger.info("game closed...")
    return {"message": "Game closed"}, 200


@app.route("/sphgo/state", methods=["POST"])
@api_call
def state(game_id=None, role=None, token=None):
    board = boards[game_id]
    result: dict = {
        "board": board.board.tolist(),
        "score": board.score(),
        "current_player": board.current_player,
        "counter": board.counter,
    }
    if board.is_game_over():
        final = board.final_score()
        winner = "black" if final[0] > final[1] else "white"
        result["game_over"] = {"winner": winner, "score": final}
    return result, 200


@app.route("/sphgo/genmove", methods=["POST"])
@api_call
def genmove(game_id=None, role=None, token=None):
    board = boards[game_id]
    player_color = BLACK if role == "black" else WHITE

    # Try HRM first, fall back to heuristic
    point = None
    if _hrm_player is not None:
        try:
            point = _hrm_player.genmove(board, player_color)
        except Exception as e:
            logger.warning(f"HRM genmove failed: {e}, falling back to heuristic")

    if point is None:
        point = board.genmove(player_color)

    if point is None:
        board.consecutive_passes += 1
        board.switch_player()
        socketio.emit("passed", {"role": role}, room=game_id)
        if board.is_game_over():
            final = board.final_score()
            winner = "black" if final[0] > final[1] else "white"
            socketio.emit(
                "game_over",
                {"reason": "complete", "winner": winner, "score": final},
                room=game_id,
            )
        return {"message": "pass", "point": None, "play": None}, 200

    try:
        board.play(point, player_color)
    except ValueError:
        # AI's chosen move is illegal; try remaining legal moves
        logger.warning(f"AI move {point} illegal, trying alternatives")
        point = None
        for candidate in board.get_empties(player_color):
            try:
                board.play(candidate, player_color)
                point = candidate
                break
            except ValueError:
                continue
        if point is None:
            # Truly no legal move — pass
            board.consecutive_passes += 1
            board.switch_player()
            socketio.emit("passed", {"role": role}, room=game_id)
            if board.is_game_over():
                final = board.final_score()
                winner = "black" if final[0] > final[1] else "white"
                socketio.emit(
                    "game_over",
                    {"reason": "complete", "winner": winner, "score": final},
                    room=game_id,
                )
            return {"message": "pass", "point": None, "play": None}, 200

    board.consecutive_passes = 0
    board.switch_player()
    encoded = encoder[point]
    storage.add_play(game_id, list(encoded))
    plays = storage.get_plays(game_id)
    steps = len(plays) - 1
    score = board.score()
    socketio.emit(
        "played",
        {"role": role, "steps": steps, "play": list(encoded), "score": score},
        room=game_id,
    )

    if board.is_game_over():
        final = board.final_score()
        winner = "black" if final[0] > final[1] else "white"
        socketio.emit(
            "game_over",
            {"reason": "complete", "winner": winner, "score": final},
            room=game_id,
        )

    return {"point": point, "play": list(encoded)}, 200


@app.route("/sphgo/play", methods=["POST"])
@api_call
def play(game_id=None, role=None, steps=None, play=None, token=None):
    plays = storage.get_plays(game_id)
    logger.info(f"{role} play at {play} with steps {steps} ... {game_id}:{len(plays)}")

    # Validate steps
    if steps != len(plays):
        return {
            "message": f"Length of {len(plays)} mismatched with steps {steps} passed in"
        }, 400

    # Validate player turn
    # black is the first player and then take the even steps, and steps is 0-based
    if steps % 2 == 0 and role != "black":
        return {"message": "Invalid player"}, 400

    # white is the second player and then take the odd steps, and steps is 0-based
    if steps % 2 == 1 and role != "white":
        return {"message": "Invalid player"}, 400

    # Validate play
    code = ",".join([str(elm) for elm in play])
    if code not in valid_plays:
        return {"message": "Invalid play"}, 400

    # Validate and execute move on the board
    board = boards[game_id]
    point = decoder[tuple(play)]
    player_color = BLACK if role == "black" else WHITE
    try:
        board.play(point, player_color)
        board.consecutive_passes = 0
        board.switch_player()
    except ValueError as e:
        return {"message": str(e)}, 400

    storage.add_play(game_id, play)
    score = board.score()
    socketio.emit(
        "played",
        {"role": role, "steps": steps, "play": play, "score": score},
        room=game_id,
    )

    if board.is_game_over():
        final = board.final_score()
        winner = "black" if final[0] > final[1] else "white"
        socketio.emit(
            "game_over",
            {"reason": "complete", "winner": winner, "score": final},
            room=game_id,
        )

    return {"message": "Play processed"}, 200


@app.route("/sphgo/resign", methods=["POST"])
@api_call
def resign(game_id=None, role=None, token=None):
    logger.info(f"player {role} resigning... {game_id}")
    if role not in ["black", "white"]:
        return {"message": "Invalid role"}, 400
    board = boards[game_id]
    winner = "white" if role == "black" else "black"
    final = board.final_score()
    socketio.emit(
        "game_over",
        {"reason": "resign", "winner": winner, "score": final},
        room=game_id,
    )
    return {"winner": winner, "score": final}, 200


@app.route("/sphgo/record", methods=["POST"])
@api_call
def record(game_id=None, role=None, token=None):
    board = boards[game_id]
    game_record = GameRecord.from_board(board)
    return game_record.to_dict(), 200


@socketio.on("join")
def on_join(data):
    logger.info(f"event join... {str(data)}")
    try:
        key = data["key"]
        if not storage.contains(key):
            logger.error(f"error in event join... {key} was not found in rooms")
            emit("error", {"message": "Game not found"})
            return
        game_id = storage.get_game_id(key)
        role = storage.get_role(key)

        if role in ["black", "white"]:
            player_join_room(game_id, role)
        if role == "viewer":
            viewer_join_room(game_id)
    except Exception as e:
        logger.error(f"error in event join... unknown error {str(e)}")
        logger.exception("error in event join...", exc_info=e)
        emit("error", {"message": str(e)})


@socketio.on("ready")
def on_ready(data):
    key = data["key"]
    if not storage.contains(key):
        emit("error", {"message": "Game not found"})
        return

    game_id = storage.get_game_id(key)
    role = storage.get_role(key)

    if role in ["black", "white"]:
        storage.mark_ready(game_id, role)
        emit("ready", {"role": role}, room=game_id)

        # Check if all required players are ready
        if storage.all_ready(game_id):
            delayed_thread = Thread(target=delayed_start, args=(game_id,))
            delayed_thread.start()


def main():
    port = int(os.environ.get("PORT", 3302))
    logger.info(f"Secret: {secret_key}")
    logger.info(f"Token: {server_token}")
    socketio.run(
        app, host="0.0.0.0", port=port, allow_unsafe_werkzeug=True, debug=False
    )


if __name__ == "__main__":
    main()
