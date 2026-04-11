import json
import os
import secrets
import sqlite3
from abc import ABC, abstractmethod

from polyclash.util.logging import logger

try:
    import redis

    _HAS_REDIS = True
except ImportError:
    _HAS_REDIS = False

USER_KEY_LENGTH = 16
USER_TOKEN_LENGTH = 48
GAME_ID_LENGTH = 64


class DataStorage(ABC):
    @abstractmethod
    def create_room(self):
        pass

    @abstractmethod
    def contains(self, key_or_token):
        pass

    @abstractmethod
    def get_game_id(self, key):
        pass

    @abstractmethod
    def get_key(self, game_id, role):
        pass

    @abstractmethod
    def get_plays(self, game_id):
        pass

    @abstractmethod
    def list_rooms(self):
        pass

    @abstractmethod
    def close_room(self, game_id):
        pass

    @abstractmethod
    def exists(self, game_id):
        pass

    @abstractmethod
    def joined_status(self, game_id):
        pass

    @abstractmethod
    def all_joined(self, game_id):
        pass

    @abstractmethod
    def ready_status(self, game_id):
        pass

    @abstractmethod
    def all_ready(self, game_id):
        pass

    @abstractmethod
    def create_player(self, key, role):
        pass

    @abstractmethod
    def create_viewer(self, key):
        pass

    @abstractmethod
    def get_role(self, key_or_token):
        pass

    @abstractmethod
    def join_room(self, game_id, role):
        pass

    @abstractmethod
    def is_ready(self, game_id, role):
        pass

    @abstractmethod
    def mark_ready(self, game_id, role):
        pass

    @abstractmethod
    def start_game(self, game_id):
        pass

    @abstractmethod
    def is_started(self, game_id):
        pass

    @abstractmethod
    def add_play(self, game_id, play):
        pass

    @abstractmethod
    def save_board(self, game_id: str, board_dict: dict) -> None:
        pass

    @abstractmethod
    def load_board(self, game_id: str) -> dict | None:
        pass


class MemoryStorage(DataStorage):
    def __init__(self):
        self.games = {}
        self.rooms = {}

    def create_room(self):
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        self.games[game_id] = {
            "id": game_id,
            "keys": {"black": black_key, "white": white_key, "viewer": viewer_key},
            "players": {},
            "viewers": [],
            "plays": [],
            "joined": {"black": False, "white": False},
            "ready": {"black": False, "white": False},
        }
        self.rooms[black_key] = game_id
        self.rooms[white_key] = game_id
        self.rooms[viewer_key] = game_id

        return dict(
            game_id=game_id,
            black_key=black_key,
            white_key=white_key,
            viewer_key=viewer_key,
        )

    def contains(self, key_or_token):
        return key_or_token in self.rooms

    def get_game_id(self, key):
        return self.rooms[key]

    def get_key(self, game_id, role):
        return self.games[game_id]["keys"][role]

    def get_plays(self, game_id):
        return self.games[game_id]["plays"]

    def list_rooms(self):
        return list([key for key in self.games.keys()])

    def close_room(self, game_id):
        game = self.games[game_id]
        del self.rooms[game["keys"]["black"]]
        del self.rooms[game["keys"]["white"]]
        del self.rooms[game["keys"]["viewer"]]
        del self.rooms[game["players"]["black"]]
        del self.rooms[game["players"]["white"]]
        for viewer_id in game["viewers"]:
            del self.rooms[viewer_id]
        del self.games[game["id"]]

    def exists(self, game_id):
        return game_id in self.games

    def joined_status(self, game_id):
        return self.games[game_id]["joined"]

    def all_joined(self, game_id):
        return all(self.games[game_id]["joined"].values())

    def ready_status(self, game_id):
        return self.games[game_id]["ready"]

    def all_ready(self, game_id):
        return all(self.games[game_id]["ready"].values())

    def create_player(self, key, role):
        if role not in ["black", "white"]:
            raise ValueError("Invalid role")
        if key not in self.rooms:
            raise ValueError("Invalid key")
        if key != self.games[self.rooms[key]]["keys"][role]:
            raise ValueError("Invalid key for role")

        if self.games[self.rooms[key]]["joined"][role]:
            return self.games[self.rooms[key]]["players"][role]

        game = self.games[self.rooms[key]]
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        self.rooms[token] = game["id"]
        game["players"][role] = token
        game["joined"][role] = True

        return token

    def create_viewer(self, key):
        if key not in self.rooms:
            raise ValueError("Invalid key")
        if key != self.games[self.rooms[key]]["keys"]["viewer"]:
            raise ValueError("Invalid key for role")

        game = self.games[self.rooms[key]]
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        self.rooms[token] = game["id"]
        game["viewers"].append(token)
        return token

    def get_role(self, key_or_token):
        if key_or_token in self.rooms:
            game_id = self.rooms[key_or_token]
            # Check if it's a key
            if key_or_token == self.games[game_id]["keys"]["black"]:
                return "black"
            elif key_or_token == self.games[game_id]["keys"]["white"]:
                return "white"
            elif key_or_token == self.games[game_id]["keys"]["viewer"]:
                return "viewer"

            # Check if it's a token
            if "players" in self.games[game_id]:
                if (
                    "black" in self.games[game_id]["players"]
                    and key_or_token == self.games[game_id]["players"]["black"]
                ):
                    return "black"
                elif (
                    "white" in self.games[game_id]["players"]
                    and key_or_token == self.games[game_id]["players"]["white"]
                ):
                    return "white"

            # Check if it's a viewer token
            if (
                "viewers" in self.games[game_id]
                and key_or_token in self.games[game_id]["viewers"]
            ):
                return "viewer"

        raise ValueError("Invalid key or token")

    def join_room(self, game_id, role):
        self.games[game_id]["joined"][role] = True

    def is_ready(self, game_id, role):
        return self.games[game_id]["ready"][role]

    def mark_ready(self, game_id, role):
        self.games[game_id]["ready"][role] = True

    def start_game(self, game_id):
        self.games[game_id]["started"] = True

    def is_started(self, game_id):
        return self.games[game_id]["started"]

    def add_play(self, game_id, play):
        return self.games[game_id]["plays"].append(play)

    def save_board(self, game_id: str, board_dict: dict) -> None:
        self.games[game_id]["board_snapshot"] = board_dict

    def load_board(self, game_id: str) -> dict | None:
        result: dict | None = self.games[game_id].get("board_snapshot")
        return result


class RedisStorage(DataStorage):
    def __init__(self, host="localhost", port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)

    def create_room(self):
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        self.redis.rpush("games", game_id)
        self.redis.hset("rooms", black_key, game_id)
        self.redis.hset("rooms", white_key, game_id)
        self.redis.hset("rooms", viewer_key, game_id)

        self.redis.hset(f"games:{game_id}", "id", game_id)

        self.redis.hset(f"games:{game_id}", "keys:black", black_key)
        self.redis.hset(f"games:{game_id}", "keys:white", white_key)
        self.redis.hset(f"games:{game_id}", f"keys:{black_key}", "black")
        self.redis.hset(f"games:{game_id}", f"keys:{white_key}", "white")
        self.redis.hset(f"games:{game_id}", "keys:viewer", viewer_key)

        self.redis.hset(f"games:{game_id}", "players:black", "")
        self.redis.hset(f"games:{game_id}", "players:white", "")
        self.redis.hset(f"games:{game_id}", "joined:black", str(False))
        self.redis.hset(f"games:{game_id}", "joined:white", str(False))
        self.redis.hset(f"games:{game_id}", "ready:black", str(False))
        self.redis.hset(f"games:{game_id}", "ready:white", str(False))
        self.redis.hset(f"games:{game_id}", "started", str(False))

        self.redis.expire(f"games:{game_id}", 3600 * 24 * 3)

        # self.redis.rpush(f'games:{game_id}:viewers', '')
        # self.redis.rpush(f'games:{game_id}:plays', '')

        self.reaper()

        return dict(
            game_id=game_id,
            black_key=black_key,
            white_key=white_key,
            viewer_key=viewer_key,
        )

    def contains(self, key_or_token):
        return self.redis.hexists("rooms", key_or_token)

    def get_game_id(self, key):
        return self.redis.hget("rooms", key).decode("utf-8")

    def get_key(self, game_id, role):
        return self.redis.hget(f"games:{game_id}", f"keys:{role}").decode("utf-8")

    def get_plays(self, game_id):
        if self.redis.exists(f"games:{game_id}:plays"):
            return list(
                [
                    json.loads(item.decode("utf-8"))
                    for item in self.redis.lrange(f"games:{game_id}:plays", 0, -1)
                ]
            )
        else:
            return []

    def list_rooms(self):
        if not self.redis.exists("games"):
            return []
        return list(
            [item.decode("utf-8") for item in self.redis.lrange("games", 0, -1)]
        )

    def close_room(self, game_id):
        if self.redis.exists(f"games:{game_id}"):
            self.redis.hdel("rooms", self.redis.hget(f"games:{game_id}", "keys:black"))
            self.redis.hdel("rooms", self.redis.hget(f"games:{game_id}", "keys:white"))
            self.redis.hdel("rooms", self.redis.hget(f"games:{game_id}", "keys:viewer"))
            self.redis.hdel(
                "rooms", self.redis.hget(f"games:{game_id}", "players:black")
            )
            self.redis.hdel(
                "rooms", self.redis.hget(f"games:{game_id}", "players:white")
            )
        if self.redis.exists(f"games:{game_id}:viewer"):
            for viewer_id in self.redis.lrange(f"games:{game_id}:viewers", 0, -1):
                self.redis.hdel("rooms", viewer_id.decode("utf-8"))

        self.redis.delete(f"games:{game_id}")
        self.redis.lrem("games", 1, game_id)

        if self.redis.exists(f"games:{game_id}:viewer"):
            self.redis.delete(f"games:{game_id}:viewer")
        if self.redis.exists(f"games:{game_id}:plays"):
            self.redis.delete(f"games:{game_id}:plays")
        if self.redis.exists(f"games:{game_id}:board"):
            self.redis.delete(f"games:{game_id}:board")

    def exists(self, game_id):
        return game_id in list(
            [item.decode("utf-8") for item in self.redis.lrange("games", 0, -1)]
        )

    def joined_status(self, game_id):
        return {
            key: bool(
                self.redis.hget(f"games:{game_id}", f"joined:{key}").decode("utf-8")
                == "True"
            )
            for key in ["black", "white"]
        }

    def all_joined(self, game_id):
        return all(self.joined_status(game_id).values())

    def ready_status(self, game_id):
        return {
            key: bool(
                self.redis.hget(f"games:{game_id}", f"ready:{key}").decode("utf-8")
                == "True"
            )
            for key in ["black", "white"]
        }

    def all_ready(self, game_id):
        return all(self.ready_status(game_id).values())

    def create_player(self, key, role):
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        game_id = self.get_game_id(key)
        self.redis.hset("rooms", token, game_id)
        self.redis.hset(f"games:{game_id}", f"players:{role}", token)
        self.redis.hset(f"games:{game_id}", f"players:{token}", role)
        self.redis.hset(f"games:{game_id}", f"joined:{role}", str(True))
        return token

    def create_viewer(self, key):
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        game_id = self.get_game_id(key)
        self.redis.hset("rooms", token, game_id)
        self.redis.rpush(f"games:{game_id}:viewer", token)
        self.redis.expire(f"games:{game_id}:viewer", 3600 * 24 * 3)
        return token

    def get_role(self, key_or_token):
        game_id = self.get_game_id(key_or_token)

        # Check if it's a key
        role = self.redis.hget(f"games:{game_id}", f"keys:{key_or_token}")
        if role:
            return role.decode("utf-8")

        # Check if it's a player token
        role = self.redis.hget(f"games:{game_id}", f"players:{key_or_token}")
        if role:
            return role.decode("utf-8")

        # If not a key or player token, assume it's a viewer token
        return "viewer"

    def join_room(self, game_id, role):
        self.redis.hset(f"games:{game_id}", f"joined:{role}", str(True))

    def is_ready(self, game_id, role):
        return bool(
            self.redis.hget(f"games:{game_id}", f"ready:{role}").decode("utf-8")
            == "True"
        )

    def mark_ready(self, game_id, role):
        self.redis.hset(f"games:{game_id}", f"ready:{role}", str(True))

    def start_game(self, game_id):
        self.redis.hset(f"games:{game_id}", "started", str(True))

    def is_started(self, game_id):
        return bool(
            self.redis.hget(f"games:{game_id}", "started").decode("utf-8") == "True"
        )

    def add_play(self, game_id, play):
        self.redis.rpush(f"games:{game_id}:plays", json.dumps(play))
        self.redis.expire(f"games:{game_id}:plays", 3600 * 24 * 3)

    def save_board(self, game_id: str, board_dict: dict) -> None:
        self.redis.set(
            f"games:{game_id}:board", json.dumps(board_dict), ex=3600 * 24 * 3
        )

    def load_board(self, game_id: str) -> dict | None:
        raw = self.redis.get(f"games:{game_id}:board")
        if raw:
            result: dict = json.loads(raw.decode("utf-8"))
            return result
        return None

    def reaper(self):
        for game_id in self.list_rooms():
            # if game_id is not represented in the key of games:{game_id}
            # then it means the game is over and we should clean up
            if not self.redis.exists(f"games:{game_id}"):
                self.close_room(game_id)


_DEFAULT_STORAGE_DB = os.path.join(
    os.path.dirname(__file__), "..", "..", "polyclash_games.db"
)


class SqliteStorage(DataStorage):
    """SQLite-backed game storage for small-team deployments."""

    def __init__(self, db_path: str | None = None) -> None:
        self.db_path: str = (
            db_path or os.environ.get("POLYCLASH_STORAGE_DB") or _DEFAULT_STORAGE_DB
        )
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS games (
                game_id TEXT PRIMARY KEY,
                black_key TEXT NOT NULL,
                white_key TEXT NOT NULL,
                viewer_key TEXT NOT NULL,
                black_player_token TEXT DEFAULT '',
                white_player_token TEXT DEFAULT '',
                joined_black INTEGER NOT NULL DEFAULT 0,
                joined_white INTEGER NOT NULL DEFAULT 0,
                ready_black INTEGER NOT NULL DEFAULT 0,
                ready_white INTEGER NOT NULL DEFAULT 0,
                started INTEGER NOT NULL DEFAULT 0,
                board_snapshot TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS rooms (
                key_or_token TEXT PRIMARY KEY,
                game_id TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS game_viewers (
                token TEXT PRIMARY KEY,
                game_id TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS game_plays (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                game_id TEXT NOT NULL,
                play_data TEXT NOT NULL
            );
        """)
        conn.commit()
        conn.close()

    def create_room(self) -> dict:
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        conn = self._get_conn()
        conn.execute(
            "INSERT INTO games (game_id, black_key, white_key, viewer_key) "
            "VALUES (?, ?, ?, ?)",
            (game_id, black_key, white_key, viewer_key),
        )
        for key in (black_key, white_key, viewer_key):
            conn.execute(
                "INSERT INTO rooms (key_or_token, game_id) VALUES (?, ?)",
                (key, game_id),
            )
        conn.commit()
        conn.close()

        return dict(
            game_id=game_id,
            black_key=black_key,
            white_key=white_key,
            viewer_key=viewer_key,
        )

    def contains(self, key_or_token: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM rooms WHERE key_or_token = ?", (key_or_token,)
        ).fetchone()
        conn.close()
        return row is not None

    def get_game_id(self, key: str) -> str:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT game_id FROM rooms WHERE key_or_token = ?", (key,)
        ).fetchone()
        conn.close()
        return str(row["game_id"])

    def get_key(self, game_id: str, role: str) -> str:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT black_key, white_key, viewer_key FROM games WHERE game_id = ?",
            (game_id,),
        ).fetchone()
        conn.close()
        return str(row[f"{role}_key"])

    def get_plays(self, game_id: str) -> list:
        conn = self._get_conn()
        rows = conn.execute(
            "SELECT play_data FROM game_plays WHERE game_id = ? ORDER BY id",
            (game_id,),
        ).fetchall()
        conn.close()
        return [json.loads(r["play_data"]) for r in rows]

    def list_rooms(self) -> list[str]:
        conn = self._get_conn()
        rows = conn.execute("SELECT game_id FROM games").fetchall()
        conn.close()
        return [r["game_id"] for r in rows]

    def close_room(self, game_id: str) -> None:
        conn = self._get_conn()
        conn.execute("DELETE FROM rooms WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM game_viewers WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM game_plays WHERE game_id = ?", (game_id,))
        conn.execute("DELETE FROM games WHERE game_id = ?", (game_id,))
        conn.commit()
        conn.close()

    def exists(self, game_id: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        conn.close()
        return row is not None

    def joined_status(self, game_id: str) -> dict:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT joined_black, joined_white FROM games WHERE game_id = ?",
            (game_id,),
        ).fetchone()
        conn.close()
        return {"black": bool(row["joined_black"]), "white": bool(row["joined_white"])}

    def all_joined(self, game_id: str) -> bool:
        return all(self.joined_status(game_id).values())

    def ready_status(self, game_id: str) -> dict:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT ready_black, ready_white FROM games WHERE game_id = ?",
            (game_id,),
        ).fetchone()
        conn.close()
        return {"black": bool(row["ready_black"]), "white": bool(row["ready_white"])}

    def all_ready(self, game_id: str) -> bool:
        return all(self.ready_status(game_id).values())

    def create_player(self, key: str, role: str) -> str:
        if role not in ("black", "white"):
            raise ValueError("Invalid role")
        conn = self._get_conn()
        room = conn.execute(
            "SELECT game_id FROM rooms WHERE key_or_token = ?", (key,)
        ).fetchone()
        if not room:
            conn.close()
            raise ValueError("Invalid key")
        game_id = room["game_id"]

        game = conn.execute(
            "SELECT * FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        if key != game[f"{role}_key"]:
            conn.close()
            raise ValueError("Invalid key for role")

        # Already joined — return existing token
        if game[f"joined_{role}"]:
            conn.close()
            return str(game[f"{role}_player_token"])

        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        conn.execute(
            "INSERT INTO rooms (key_or_token, game_id) VALUES (?, ?)",
            (token, game_id),
        )
        conn.execute(
            f"UPDATE games SET {role}_player_token = ?, joined_{role} = 1 "
            f"WHERE game_id = ?",
            (token, game_id),
        )
        conn.commit()
        conn.close()
        return token

    def create_viewer(self, key: str) -> str:
        conn = self._get_conn()
        room = conn.execute(
            "SELECT game_id FROM rooms WHERE key_or_token = ?", (key,)
        ).fetchone()
        if not room:
            conn.close()
            raise ValueError("Invalid key")
        game_id = room["game_id"]

        game = conn.execute(
            "SELECT viewer_key FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        if key != game["viewer_key"]:
            conn.close()
            raise ValueError("Invalid key for role")

        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        conn.execute(
            "INSERT INTO rooms (key_or_token, game_id) VALUES (?, ?)",
            (token, game_id),
        )
        conn.execute(
            "INSERT INTO game_viewers (token, game_id) VALUES (?, ?)",
            (token, game_id),
        )
        conn.commit()
        conn.close()
        return token

    def get_role(self, key_or_token: str) -> str:
        conn = self._get_conn()
        room = conn.execute(
            "SELECT game_id FROM rooms WHERE key_or_token = ?", (key_or_token,)
        ).fetchone()
        if not room:
            conn.close()
            raise ValueError("Invalid key or token")
        game_id = room["game_id"]

        game = conn.execute(
            "SELECT * FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()

        # Check keys
        if key_or_token == game["black_key"]:
            conn.close()
            return "black"
        if key_or_token == game["white_key"]:
            conn.close()
            return "white"
        if key_or_token == game["viewer_key"]:
            conn.close()
            return "viewer"

        # Check player tokens
        if key_or_token == game["black_player_token"]:
            conn.close()
            return "black"
        if key_or_token == game["white_player_token"]:
            conn.close()
            return "white"

        # Check viewer tokens
        viewer = conn.execute(
            "SELECT 1 FROM game_viewers WHERE token = ? AND game_id = ?",
            (key_or_token, game_id),
        ).fetchone()
        conn.close()
        if viewer:
            return "viewer"

        raise ValueError("Invalid key or token")

    def join_room(self, game_id: str, role: str) -> None:
        conn = self._get_conn()
        conn.execute(
            f"UPDATE games SET joined_{role} = 1 WHERE game_id = ?", (game_id,)
        )
        conn.commit()
        conn.close()

    def is_ready(self, game_id: str, role: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            f"SELECT ready_{role} FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        conn.close()
        return bool(row[f"ready_{role}"])

    def mark_ready(self, game_id: str, role: str) -> None:
        conn = self._get_conn()
        conn.execute(f"UPDATE games SET ready_{role} = 1 WHERE game_id = ?", (game_id,))
        conn.commit()
        conn.close()

    def start_game(self, game_id: str) -> None:
        conn = self._get_conn()
        conn.execute("UPDATE games SET started = 1 WHERE game_id = ?", (game_id,))
        conn.commit()
        conn.close()

    def is_started(self, game_id: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT started FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        conn.close()
        return bool(row["started"])

    def add_play(self, game_id: str, play: list) -> None:
        conn = self._get_conn()
        conn.execute(
            "INSERT INTO game_plays (game_id, play_data) VALUES (?, ?)",
            (game_id, json.dumps(play)),
        )
        conn.commit()
        conn.close()

    def save_board(self, game_id: str, board_dict: dict) -> None:
        conn = self._get_conn()
        conn.execute(
            "UPDATE games SET board_snapshot = ? WHERE game_id = ?",
            (json.dumps(board_dict), game_id),
        )
        conn.commit()
        conn.close()

    def load_board(self, game_id: str) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT board_snapshot FROM games WHERE game_id = ?", (game_id,)
        ).fetchone()
        conn.close()
        if row and row["board_snapshot"]:
            result: dict = json.loads(row["board_snapshot"])
            return result
        return None


def test_redis_connection(
    host: str = "localhost", port: int = 6379, db: int = 0
) -> bool:
    if not _HAS_REDIS:
        logger.info("redis package not installed. Using memory storage.")
        return False
    try:
        redis.StrictRedis(host=host, port=port, db=db).ping()
        logger.info("Successfully connected to Redis. Using Redis as data storage.")
        return True
    except redis.ConnectionError:
        logger.info("Failed to connect to Redis. Using memory dict as data storage.")
        return False


def create_storage(flag_redis=None, memory: bool = False):
    if memory:
        return MemoryStorage()
    if flag_redis is None:
        flag_redis = test_redis_connection()
    if flag_redis:
        return RedisStorage()
    return SqliteStorage()
