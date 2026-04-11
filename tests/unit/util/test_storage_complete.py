from unittest.mock import MagicMock, patch

import pytest
import redis

from polyclash.util.storage import (
    MemoryStorage,
    RedisStorage,
    create_storage,
    test_redis_connection,
)


class TestMemoryStorageComplete:
    @pytest.fixture
    def storage(self):
        """Create a MemoryStorage instance for testing."""
        return MemoryStorage()

    @pytest.fixture
    def room_fixture(self, storage):
        """Create a test room and return its details."""
        room = storage.create_room()
        return {
            "storage": storage,
            "game_id": room["game_id"],
            "black_key": room["black_key"],
            "white_key": room["white_key"],
            "viewer_key": room["viewer_key"],
        }

    def test_create_room(self, storage):
        """Test room creation with all required keys."""
        room = storage.create_room()

        # Check all keys are present
        assert "game_id" in room
        assert "black_key" in room
        assert "white_key" in room
        assert "viewer_key" in room

        # Check all keys are different
        keys = [room["black_key"], room["white_key"], room["viewer_key"]]
        assert len(keys) == len(set(keys))  # All keys are unique

        # Check the game was stored properly
        assert room["game_id"] in storage.games
        assert storage.games[room["game_id"]]["id"] == room["game_id"]

        # Check the room mappings
        assert storage.rooms[room["black_key"]] == room["game_id"]
        assert storage.rooms[room["white_key"]] == room["game_id"]
        assert storage.rooms[room["viewer_key"]] == room["game_id"]

    def test_contains(self, room_fixture):
        """Test checking if storage contains a key."""
        storage = room_fixture["storage"]

        # Valid keys
        assert storage.contains(room_fixture["black_key"])
        assert storage.contains(room_fixture["white_key"])
        assert storage.contains(room_fixture["viewer_key"])

        # Invalid key
        assert not storage.contains("invalid_key")

    def test_get_game_id(self, room_fixture):
        """Test retrieving game ID from a key."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        assert storage.get_game_id(room_fixture["black_key"]) == game_id
        assert storage.get_game_id(room_fixture["white_key"]) == game_id
        assert storage.get_game_id(room_fixture["viewer_key"]) == game_id

        # Non-existent key should raise a KeyError
        with pytest.raises(KeyError):
            storage.get_game_id("invalid_key")

    def test_get_key(self, room_fixture):
        """Test retrieving a role's key for a game."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        assert storage.get_key(game_id, "black") == room_fixture["black_key"]
        assert storage.get_key(game_id, "white") == room_fixture["white_key"]
        assert storage.get_key(game_id, "viewer") == room_fixture["viewer_key"]

        # Invalid role or game_id should raise KeyError
        with pytest.raises(KeyError):
            storage.get_key(game_id, "invalid_role")

        with pytest.raises(KeyError):
            storage.get_key("invalid_game_id", "black")

    def test_get_plays(self, room_fixture):
        """Test retrieving plays for a game."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially empty
        assert storage.get_plays(game_id) == []

        # Add some plays
        play1 = {"role": "black", "position": 0}
        play2 = {"role": "white", "position": 1}
        storage.add_play(game_id, play1)
        storage.add_play(game_id, play2)

        # Check plays are retrieved
        plays = storage.get_plays(game_id)
        assert len(plays) == 2
        assert plays[0] == play1
        assert plays[1] == play2

    def test_list_rooms(self, storage):
        """Test listing all available rooms."""
        # Initially empty
        assert len(storage.list_rooms()) == 0

        # Create some rooms
        room1 = storage.create_room()
        room2 = storage.create_room()
        room3 = storage.create_room()

        # Check all rooms are listed
        rooms = storage.list_rooms()
        assert len(rooms) == 3
        assert room1["game_id"] in rooms
        assert room2["game_id"] in rooms
        assert room3["game_id"] in rooms

    def test_close_room(self, room_fixture):
        """Test closing a room."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Create players
        black_token = storage.create_player(room_fixture["black_key"], "black")
        white_token = storage.create_player(room_fixture["white_key"], "white")

        # Create viewer
        storage.create_viewer(room_fixture["viewer_key"])

        # Close the room
        storage.close_room(game_id)

        # Check room is deleted
        assert game_id not in storage.games

        # Check keys are removed from rooms
        assert room_fixture["black_key"] not in storage.rooms
        assert room_fixture["white_key"] not in storage.rooms
        assert room_fixture["viewer_key"] not in storage.rooms
        assert black_token not in storage.rooms
        assert white_token not in storage.rooms

    def test_exists(self, room_fixture):
        """Test checking if a game exists."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        assert storage.exists(game_id)
        assert not storage.exists("invalid_game_id")

    def test_joined_status(self, room_fixture):
        """Test checking joined status."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially no players joined
        status = storage.joined_status(game_id)
        assert not status["black"]
        assert not status["white"]

        # Join black player
        storage.join_room(game_id, "black")
        status = storage.joined_status(game_id)
        assert status["black"]
        assert not status["white"]

        # Join white player
        storage.join_room(game_id, "white")
        status = storage.joined_status(game_id)
        assert status["black"]
        assert status["white"]

    def test_all_joined(self, room_fixture):
        """Test checking if all players joined."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially no players joined
        assert not storage.all_joined(game_id)

        # Join black player
        storage.join_room(game_id, "black")
        assert not storage.all_joined(game_id)

        # Join white player
        storage.join_room(game_id, "white")
        assert storage.all_joined(game_id)

    def test_ready_status(self, room_fixture):
        """Test checking ready status."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially no players ready
        status = storage.ready_status(game_id)
        assert not status["black"]
        assert not status["white"]

        # Mark black player ready
        storage.mark_ready(game_id, "black")
        status = storage.ready_status(game_id)
        assert status["black"]
        assert not status["white"]

        # Mark white player ready
        storage.mark_ready(game_id, "white")
        status = storage.ready_status(game_id)
        assert status["black"]
        assert status["white"]

    def test_all_ready(self, room_fixture):
        """Test checking if all players are ready."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially no players ready
        assert not storage.all_ready(game_id)

        # Mark black player ready
        storage.mark_ready(game_id, "black")
        assert not storage.all_ready(game_id)

        # Mark white player ready
        storage.mark_ready(game_id, "white")
        assert storage.all_ready(game_id)

    def test_create_player(self, room_fixture):
        """Test player creation."""
        storage = room_fixture["storage"]
        black_key = room_fixture["black_key"]
        white_key = room_fixture["white_key"]
        game_id = room_fixture["game_id"]

        # Create valid players
        black_token = storage.create_player(black_key, "black")
        white_token = storage.create_player(white_key, "white")

        # Check tokens are valid
        assert storage.contains(black_token)
        assert storage.contains(white_token)

        # Check tokens are assigned correctly
        assert storage.get_role(black_token) == "black"
        assert storage.get_role(white_token) == "white"

        # Check players are marked as joined
        assert storage.games[game_id]["joined"]["black"]
        assert storage.games[game_id]["joined"]["white"]

        # Invalid role should raise ValueError
        with pytest.raises(ValueError):
            storage.create_player(black_key, "invalid_role")

        # Invalid key should raise ValueError
        with pytest.raises(ValueError):
            storage.create_player("invalid_key", "black")

        # Wrong key for role should raise ValueError
        with pytest.raises(ValueError):
            storage.create_player(white_key, "black")

    def test_create_viewer(self, room_fixture):
        """Test viewer creation."""
        storage = room_fixture["storage"]
        viewer_key = room_fixture["viewer_key"]
        game_id = room_fixture["game_id"]

        # Create viewer
        storage.create_viewer(viewer_key)

        # Check viewer is added to the game
        assert len(storage.games[game_id]["viewers"]) > 0

        # Invalid key should raise ValueError
        with pytest.raises(ValueError):
            storage.create_viewer("invalid_key")

        # Wrong key for role should raise ValueError
        with pytest.raises(ValueError):
            storage.create_viewer(room_fixture["black_key"])

    def test_get_role(self, room_fixture):
        """Test role retrieval."""
        storage = room_fixture["storage"]

        # Direct keys should return roles
        assert storage.get_role(room_fixture["black_key"]) == "black"
        assert storage.get_role(room_fixture["white_key"]) == "white"
        assert storage.get_role(room_fixture["viewer_key"]) == "viewer"

        # Create players and check tokens
        black_token = storage.create_player(room_fixture["black_key"], "black")
        white_token = storage.create_player(room_fixture["white_key"], "white")

        assert storage.get_role(black_token) == "black"
        assert storage.get_role(white_token) == "white"

        # Create viewer and check token
        storage.create_viewer(room_fixture["viewer_key"])
        viewer_token = storage.games[room_fixture["game_id"]]["viewers"][0]

        assert storage.get_role(viewer_token) == "viewer"

        # Invalid key should raise ValueError
        with pytest.raises(ValueError):
            storage.get_role("invalid_key")

    def test_join_room(self, room_fixture):
        """Test joining a room."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially not joined
        assert not storage.games[game_id]["joined"]["black"]
        assert not storage.games[game_id]["joined"]["white"]

        # Join players
        storage.join_room(game_id, "black")
        assert storage.games[game_id]["joined"]["black"]
        assert not storage.games[game_id]["joined"]["white"]

        storage.join_room(game_id, "white")
        assert storage.games[game_id]["joined"]["black"]
        assert storage.games[game_id]["joined"]["white"]

    def test_is_ready(self, room_fixture):
        """Test ready status check."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially not ready
        assert not storage.is_ready(game_id, "black")
        assert not storage.is_ready(game_id, "white")

        # Mark ready
        storage.mark_ready(game_id, "black")
        assert storage.is_ready(game_id, "black")
        assert not storage.is_ready(game_id, "white")

    def test_mark_ready(self, room_fixture):
        """Test marking a player as ready."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Mark players ready
        storage.mark_ready(game_id, "black")
        storage.mark_ready(game_id, "white")

        # Check ready status
        assert storage.games[game_id]["ready"]["black"]
        assert storage.games[game_id]["ready"]["white"]

    def test_start_game(self, room_fixture):
        """Test starting a game."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Start game
        storage.start_game(game_id)

        # Check started status
        assert storage.games[game_id]["started"]

    def test_is_started(self, room_fixture):
        """Test checking if a game is started."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Initially not started
        with pytest.raises(KeyError):
            storage.is_started(game_id)

        # Start game
        storage.start_game(game_id)

        # Check started
        assert storage.is_started(game_id)

    def test_add_play(self, room_fixture):
        """Test adding a play to a game."""
        storage = room_fixture["storage"]
        game_id = room_fixture["game_id"]

        # Check initial empty plays
        assert storage.games[game_id]["plays"] == []

        # Add play
        play = {"role": "black", "position": 0}
        storage.add_play(game_id, play)

        # Check play added
        assert storage.games[game_id]["plays"] == [play]

        # Add another play
        play2 = {"role": "white", "position": 1}
        storage.add_play(game_id, play2)

        # Check both plays
        assert storage.games[game_id]["plays"] == [play, play2]


class TestRedisStorageMock:
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        redis_mock = MagicMock()
        # Mock ping to indicate successful connection
        redis_mock.ping.return_value = True
        return redis_mock

    @pytest.fixture
    def storage(self, mock_redis):
        """Create a RedisStorage with mocked Redis."""
        with patch("polyclash.util.storage.redis.StrictRedis", return_value=mock_redis):
            storage = RedisStorage()
            storage.redis = mock_redis
            return storage

    def test_create_storage_with_redis(self, mock_redis):
        """Test create_storage function with Redis available."""
        with patch("polyclash.util.storage.test_redis_connection", return_value=True):
            with patch(
                "polyclash.util.storage.RedisStorage", return_value="redis_storage"
            ) as redis_mock:
                result = create_storage()

                # Should return Redis storage
                assert result == "redis_storage"
                redis_mock.assert_called_once()

    def test_create_storage_without_redis(self):
        """Test create_storage function without Redis available."""
        with patch("polyclash.util.storage.test_redis_connection", return_value=False):
            with patch(
                "polyclash.util.storage.MemoryStorage", return_value="memory_storage"
            ) as memory_mock:
                result = create_storage()

                # Should return Memory storage
                assert result == "memory_storage"
                memory_mock.assert_called_once()

    def test_create_storage_explicit_flag(self):
        """Test create_storage function with explicit flag."""
        with patch("polyclash.util.storage.RedisStorage", return_value="redis_storage"):
            with patch(
                "polyclash.util.storage.MemoryStorage", return_value="memory_storage"
            ):
                # Explicitly request Redis
                assert create_storage(True) == "redis_storage"

                # Explicitly request Memory
                assert create_storage(False) == "memory_storage"

    def test_test_redis_connection_success(self, mock_redis):
        """Test Redis connection check when successful."""
        with patch("polyclash.util.storage.redis.StrictRedis", return_value=mock_redis):
            with patch("polyclash.util.storage.logger.info") as mock_logger:
                result = test_redis_connection()

                assert result is True
                mock_logger.assert_called_with(
                    "Successfully connected to Redis. Using Redis as data storage."
                )

    def test_test_redis_connection_failure(self):
        """Test Redis connection check when failed."""
        mock_redis = MagicMock()
        mock_redis.ping.side_effect = redis.ConnectionError("Connection failed")

        with patch("polyclash.util.storage.redis.StrictRedis", return_value=mock_redis):
            with patch("polyclash.util.storage.logger.info") as mock_logger:
                result = test_redis_connection()

                assert result is False
                mock_logger.assert_called_with(
                    "Failed to connect to Redis. Using memory dict as data storage."
                )
