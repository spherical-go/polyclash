import json
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest

redis = pytest.importorskip("redis")

from polyclash.util.storage import (  # noqa: E402
    RedisStorage,
    create_storage,
    test_redis_connection,
)


class TestRedisStorageInit:
    """Tests for RedisStorage.__init__."""

    @patch("polyclash.util.storage.redis.StrictRedis")
    def test_init_default_params(self, mock_strict_redis: MagicMock) -> None:
        mock_client = MagicMock()
        mock_strict_redis.return_value = mock_client

        storage = RedisStorage()

        mock_strict_redis.assert_called_once_with(host="localhost", port=6379, db=0)
        assert storage.redis is mock_client

    @patch("polyclash.util.storage.redis.StrictRedis")
    def test_init_custom_params(self, mock_strict_redis: MagicMock) -> None:
        mock_client = MagicMock()
        mock_strict_redis.return_value = mock_client

        storage = RedisStorage(host="redis.example.com", port=6380, db=2)

        mock_strict_redis.assert_called_once_with(
            host="redis.example.com", port=6380, db=2
        )
        assert storage.redis is mock_client


@pytest.fixture
def mock_redis_client() -> MagicMock:
    """Create a mock Redis client."""
    return MagicMock()


@pytest.fixture
def storage(mock_redis_client: MagicMock) -> RedisStorage:
    """Create a RedisStorage with a mocked Redis client."""
    with patch(
        "polyclash.util.storage.redis.StrictRedis", return_value=mock_redis_client
    ):
        s = RedisStorage()
    return s


class TestRedisStorageCreateRoom:
    """Tests for RedisStorage.create_room."""

    @patch("polyclash.util.storage.secrets.token_hex")
    def test_create_room(
        self,
        mock_hex: MagicMock,
        storage: RedisStorage,
        mock_redis_client: MagicMock,
    ) -> None:
        mock_hex.side_effect = [
            "game_id_val",
            "black_key_val",
            "white_key_val",
            "viewer_key_val",
        ]
        mock_redis_client.exists.return_value = False
        mock_redis_client.lrange.return_value = []

        result = storage.create_room()

        assert result["game_id"] == "game_id_val"
        assert result["black_key"] == "black_key_val"
        assert result["white_key"] == "white_key_val"
        assert result["viewer_key"] == "viewer_key_val"

        mock_redis_client.rpush.assert_any_call("games", "game_id_val")

        mock_redis_client.hset.assert_any_call("rooms", "black_key_val", "game_id_val")
        mock_redis_client.hset.assert_any_call("rooms", "white_key_val", "game_id_val")
        mock_redis_client.hset.assert_any_call("rooms", "viewer_key_val", "game_id_val")

        mock_redis_client.hset.assert_any_call("games:game_id_val", "id", "game_id_val")
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "keys:black", "black_key_val"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "keys:white", "white_key_val"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "keys:black_key_val", "black"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "keys:white_key_val", "white"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "keys:viewer", "viewer_key_val"
        )
        mock_redis_client.hset.assert_any_call("games:game_id_val", "players:black", "")
        mock_redis_client.hset.assert_any_call("games:game_id_val", "players:white", "")
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "joined:black", "False"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "joined:white", "False"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "ready:black", "False"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game_id_val", "ready:white", "False"
        )
        mock_redis_client.hset.assert_any_call("games:game_id_val", "started", "False")

        mock_redis_client.expire.assert_any_call("games:game_id_val", 3600 * 24 * 3)


class TestRedisStorageContains:
    """Tests for RedisStorage.contains."""

    def test_contains_true(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hexists.return_value = True
        assert storage.contains("some_key") is True
        mock_redis_client.hexists.assert_called_once_with("rooms", "some_key")

    def test_contains_false(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hexists.return_value = False
        assert storage.contains("missing_key") is False
        mock_redis_client.hexists.assert_called_once_with("rooms", "missing_key")


class TestRedisStorageGetGameId:
    """Tests for RedisStorage.get_game_id."""

    def test_get_game_id(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.return_value = b"game123"
        result = storage.get_game_id("some_key")
        assert result == "game123"
        mock_redis_client.hget.assert_called_once_with("rooms", "some_key")


class TestRedisStorageGetKey:
    """Tests for RedisStorage.get_key."""

    def test_get_key(self, storage: RedisStorage, mock_redis_client: MagicMock) -> None:
        mock_redis_client.hget.return_value = b"black_key_abc"
        result = storage.get_key("game123", "black")
        assert result == "black_key_abc"
        mock_redis_client.hget.assert_called_once_with("games:game123", "keys:black")


class TestRedisStorageGetPlays:
    """Tests for RedisStorage.get_plays."""

    def test_get_plays_with_data(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        play1 = {"role": "black", "position": 0}
        play2 = {"role": "white", "position": 1}
        mock_redis_client.exists.return_value = True
        mock_redis_client.lrange.return_value = [
            json.dumps(play1).encode("utf-8"),
            json.dumps(play2).encode("utf-8"),
        ]

        result = storage.get_plays("game123")
        assert result == [play1, play2]
        mock_redis_client.exists.assert_called_once_with("games:game123:plays")
        mock_redis_client.lrange.assert_called_once_with("games:game123:plays", 0, -1)

    def test_get_plays_empty(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.exists.return_value = False

        result = storage.get_plays("game123")
        assert result == []
        mock_redis_client.exists.assert_called_once_with("games:game123:plays")


class TestRedisStorageListRooms:
    """Tests for RedisStorage.list_rooms."""

    def test_list_rooms_with_data(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.exists.return_value = True
        mock_redis_client.lrange.return_value = [b"game1", b"game2", b"game3"]

        result = storage.list_rooms()
        assert result == ["game1", "game2", "game3"]
        mock_redis_client.exists.assert_called_once_with("games")
        mock_redis_client.lrange.assert_called_once_with("games", 0, -1)

    def test_list_rooms_empty(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.exists.return_value = False

        result = storage.list_rooms()
        assert result == []
        mock_redis_client.exists.assert_called_once_with("games")


class TestRedisStorageCloseRoom:
    """Tests for RedisStorage.close_room."""

    def test_close_room_full(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        game_id = "game123"

        # First exists call for games:{game_id} → True
        # Second exists call for games:{game_id}:viewer → True
        # Third exists call for games:{game_id}:viewer (second check) → True
        # Fourth exists call for games:{game_id}:plays → True
        # Fifth exists call for games:{game_id}:board → True
        mock_redis_client.exists.side_effect = [True, True, True, True, True]

        mock_redis_client.hget.side_effect = [
            b"black_key",  # keys:black
            b"white_key",  # keys:white
            b"viewer_key",  # keys:viewer
            b"black_token",  # players:black
            b"white_token",  # players:white
        ]
        mock_redis_client.lrange.return_value = [b"viewer_token1", b"viewer_token2"]

        storage.close_room(game_id)

        mock_redis_client.hdel.assert_any_call("rooms", b"black_key")
        mock_redis_client.hdel.assert_any_call("rooms", b"white_key")
        mock_redis_client.hdel.assert_any_call("rooms", b"viewer_key")
        mock_redis_client.hdel.assert_any_call("rooms", b"black_token")
        mock_redis_client.hdel.assert_any_call("rooms", b"white_token")
        mock_redis_client.hdel.assert_any_call("rooms", "viewer_token1")
        mock_redis_client.hdel.assert_any_call("rooms", "viewer_token2")

        mock_redis_client.delete.assert_any_call(f"games:{game_id}")
        mock_redis_client.lrem.assert_called_once_with("games", 1, game_id)
        mock_redis_client.delete.assert_any_call(f"games:{game_id}:viewer")
        mock_redis_client.delete.assert_any_call(f"games:{game_id}:plays")
        mock_redis_client.delete.assert_any_call(f"games:{game_id}:board")

    def test_close_room_no_game_hash(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        game_id = "game_gone"
        # close_room has 5 exists calls:
        # 1. games:{game_id} → False (skip key/player hdel)
        # 2. games:{game_id}:viewer → False (skip viewer cleanup)
        # 3. games:{game_id}:viewer → False (skip delete viewer)
        # 4. games:{game_id}:plays → False (skip delete plays)
        # 5. games:{game_id}:board → False (skip delete board)
        mock_redis_client.exists.side_effect = [False, False, False, False, False]

        storage.close_room(game_id)

        mock_redis_client.delete.assert_any_call(f"games:{game_id}")
        mock_redis_client.lrem.assert_called_once_with("games", 1, game_id)
        # hdel should not be called for keys/players since game hash doesn't exist
        mock_redis_client.hget.assert_not_called()


class TestRedisStorageExists:
    """Tests for RedisStorage.exists."""

    def test_exists_true(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.lrange.return_value = [b"game1", b"game2"]
        assert storage.exists("game1") is True

    def test_exists_false(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.lrange.return_value = [b"game1", b"game2"]
        assert storage.exists("game3") is False


class TestRedisStorageJoinedStatus:
    """Tests for RedisStorage.joined_status and all_joined."""

    def test_joined_status_none_joined(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"False", b"False"]
        result = storage.joined_status("game123")
        assert result == {"black": False, "white": False}

    def test_joined_status_one_joined(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"False"]
        result = storage.joined_status("game123")
        assert result == {"black": True, "white": False}

    def test_joined_status_both_joined(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"True"]
        result = storage.joined_status("game123")
        assert result == {"black": True, "white": True}

    def test_all_joined_false(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"False"]
        assert storage.all_joined("game123") is False

    def test_all_joined_true(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"True"]
        assert storage.all_joined("game123") is True


class TestRedisStorageReadyStatus:
    """Tests for RedisStorage.ready_status and all_ready."""

    def test_ready_status_none_ready(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"False", b"False"]
        result = storage.ready_status("game123")
        assert result == {"black": False, "white": False}

    def test_ready_status_one_ready(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"False"]
        result = storage.ready_status("game123")
        assert result == {"black": True, "white": False}

    def test_ready_status_both_ready(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"True"]
        result = storage.ready_status("game123")
        assert result == {"black": True, "white": True}

    def test_all_ready_false(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"False", b"False"]
        assert storage.all_ready("game123") is False

    def test_all_ready_true(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [b"True", b"True"]
        assert storage.all_ready("game123") is True


class TestRedisStorageCreatePlayer:
    """Tests for RedisStorage.create_player."""

    @patch("polyclash.util.storage.secrets.token_hex")
    def test_create_player(
        self,
        mock_hex: MagicMock,
        storage: RedisStorage,
        mock_redis_client: MagicMock,
    ) -> None:
        mock_hex.return_value = "player_token_abc"
        mock_redis_client.hget.return_value = b"game123"

        result = storage.create_player("black_key", "black")

        assert result == "player_token_abc"
        mock_redis_client.hset.assert_any_call("rooms", "player_token_abc", "game123")
        mock_redis_client.hset.assert_any_call(
            "games:game123", "players:black", "player_token_abc"
        )
        mock_redis_client.hset.assert_any_call(
            "games:game123", "players:player_token_abc", "black"
        )
        mock_redis_client.hset.assert_any_call("games:game123", "joined:black", "True")


class TestRedisStorageCreateViewer:
    """Tests for RedisStorage.create_viewer."""

    @patch("polyclash.util.storage.secrets.token_hex")
    def test_create_viewer(
        self,
        mock_hex: MagicMock,
        storage: RedisStorage,
        mock_redis_client: MagicMock,
    ) -> None:
        mock_hex.return_value = "viewer_token_abc"
        mock_redis_client.hget.return_value = b"game123"

        result = storage.create_viewer("viewer_key")

        assert result == "viewer_token_abc"
        mock_redis_client.hset.assert_any_call("rooms", "viewer_token_abc", "game123")
        mock_redis_client.rpush.assert_called_once_with(
            "games:game123:viewer", "viewer_token_abc"
        )
        mock_redis_client.expire.assert_called_once_with(
            "games:game123:viewer", 3600 * 24 * 3
        )


class TestRedisStorageGetRole:
    """Tests for RedisStorage.get_role."""

    def test_get_role_by_key(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [
            b"game123",  # get_game_id
            b"black",  # keys:{key_or_token} lookup
        ]
        result = storage.get_role("black_key")
        assert result == "black"

    def test_get_role_by_player_token(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [
            b"game123",  # get_game_id
            None,  # keys:{key_or_token} → not a key
            b"white",  # players:{key_or_token} → player token
        ]
        result = storage.get_role("player_token")
        assert result == "white"

    def test_get_role_viewer_fallback(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.side_effect = [
            b"game123",  # get_game_id
            None,  # keys:{key_or_token} → not a key
            None,  # players:{key_or_token} → not a player
        ]
        result = storage.get_role("viewer_token")
        assert result == "viewer"


class TestRedisStorageJoinRoom:
    """Tests for RedisStorage.join_room."""

    def test_join_room(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        storage.join_room("game123", "black")
        mock_redis_client.hset.assert_called_once_with(
            "games:game123", "joined:black", "True"
        )


class TestRedisStorageIsReady:
    """Tests for RedisStorage.is_ready."""

    def test_is_ready_false(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.return_value = b"False"
        assert storage.is_ready("game123", "black") is False
        mock_redis_client.hget.assert_called_once_with("games:game123", "ready:black")

    def test_is_ready_true(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.return_value = b"True"
        assert storage.is_ready("game123", "white") is True


class TestRedisStorageMarkReady:
    """Tests for RedisStorage.mark_ready."""

    def test_mark_ready(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        storage.mark_ready("game123", "black")
        mock_redis_client.hset.assert_called_once_with(
            "games:game123", "ready:black", "True"
        )


class TestRedisStorageStartGame:
    """Tests for RedisStorage.start_game."""

    def test_start_game(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        storage.start_game("game123")
        mock_redis_client.hset.assert_called_once_with(
            "games:game123", "started", "True"
        )


class TestRedisStorageIsStarted:
    """Tests for RedisStorage.is_started."""

    def test_is_started_false(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.return_value = b"False"
        assert storage.is_started("game123") is False

    def test_is_started_true(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.hget.return_value = b"True"
        assert storage.is_started("game123") is True


class TestRedisStorageAddPlay:
    """Tests for RedisStorage.add_play."""

    def test_add_play(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        play: Dict[str, Any] = {"role": "black", "position": 42}
        storage.add_play("game123", play)

        mock_redis_client.rpush.assert_called_once_with(
            "games:game123:plays", json.dumps(play)
        )
        mock_redis_client.expire.assert_called_once_with(
            "games:game123:plays", 3600 * 24 * 3
        )


class TestRedisStorageReaper:
    """Tests for RedisStorage.reaper."""

    def test_reaper_cleans_expired(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        # list_rooms returns two games; only the second has an expired hash
        mock_redis_client.exists.side_effect = [
            True,  # "games" key exists (list_rooms check)
            True,  # games:game1 exists → still active
            False,  # games:game2 does not exist → should be reaped
            # close_room("game2") has 5 exists calls:
            False,  # games:game2 (already gone)
            False,  # games:game2:viewer (viewer list check)
            False,  # games:game2:viewer (delete check)
            False,  # games:game2:plays
            False,  # games:game2:board
        ]
        mock_redis_client.lrange.return_value = [b"game1", b"game2"]

        storage.reaper()

        # close_room should delete for game2
        mock_redis_client.delete.assert_any_call("games:game2")
        mock_redis_client.lrem.assert_called_once_with("games", 1, "game2")

    def test_reaper_no_expired(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.exists.side_effect = [
            True,  # "games" key exists
            True,  # games:game1 exists
            True,  # games:game2 exists
        ]
        mock_redis_client.lrange.return_value = [b"game1", b"game2"]

        storage.reaper()

        mock_redis_client.delete.assert_not_called()
        mock_redis_client.lrem.assert_not_called()

    def test_reaper_empty_list(
        self, storage: RedisStorage, mock_redis_client: MagicMock
    ) -> None:
        mock_redis_client.exists.return_value = False
        mock_redis_client.lrange.return_value = []

        storage.reaper()

        mock_redis_client.delete.assert_not_called()


class TestTestRedisConnection:
    """Tests for the test_redis_connection function."""

    @patch("polyclash.util.storage.redis.StrictRedis")
    def test_connection_success(self, mock_strict_redis: MagicMock) -> None:
        mock_client = MagicMock()
        mock_strict_redis.return_value = mock_client

        result = test_redis_connection()
        assert result is True
        mock_client.ping.assert_called_once()

    @patch("polyclash.util.storage.redis.StrictRedis")
    def test_connection_failure(self, mock_strict_redis: MagicMock) -> None:
        mock_client = MagicMock()
        mock_client.ping.side_effect = redis.ConnectionError("refused")
        mock_strict_redis.return_value = mock_client

        result = test_redis_connection()
        assert result is False

    @patch("polyclash.util.storage._HAS_REDIS", False)
    def test_no_redis_package(self) -> None:
        result = test_redis_connection()
        assert result is False


class TestCreateStorage:
    """Tests for the create_storage function."""

    @patch("polyclash.util.storage.test_redis_connection", return_value=True)
    @patch("polyclash.util.storage.redis.StrictRedis")
    def test_create_storage_redis(
        self, mock_strict_redis: MagicMock, mock_test_conn: MagicMock
    ) -> None:
        result = create_storage()
        assert isinstance(result, RedisStorage)

    @patch("polyclash.util.storage.test_redis_connection", return_value=False)
    def test_create_storage_sqlite(self, mock_test_conn: MagicMock) -> None:
        from polyclash.util.storage import SqliteStorage

        result = create_storage()
        assert isinstance(result, SqliteStorage)

    @patch("polyclash.util.storage.redis.StrictRedis")
    def test_create_storage_explicit_redis(self, mock_strict_redis: MagicMock) -> None:
        result = create_storage(flag_redis=True)
        assert isinstance(result, RedisStorage)

    def test_create_storage_explicit_sqlite(self) -> None:
        from polyclash.util.storage import SqliteStorage

        result = create_storage(flag_redis=False)
        assert isinstance(result, SqliteStorage)

    def test_create_storage_explicit_memory(self) -> None:
        from polyclash.util.storage import MemoryStorage

        result = create_storage(memory=True)
        assert isinstance(result, MemoryStorage)
