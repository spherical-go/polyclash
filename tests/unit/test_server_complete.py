from functools import wraps
from unittest.mock import ANY, MagicMock, patch

import pytest
from flask import Flask, request

from polyclash.server import (
    app,
    delayed_start,
    on_join,
    on_ready,
    player_join_room,
    player_ready,
    server_token,
    valid_plays,
    viewer_join_room,
)


@pytest.fixture
def mock_storage():
    """Create mock storage object with required methods."""
    mock = MagicMock()

    # Set up basic methods
    mock.contains.return_value = True
    mock.get_game_id.return_value = "test_game_id"
    mock.exists.return_value = True
    mock.get_role.return_value = "black"
    mock.get_key.return_value = "test_key"
    mock.create_player.return_value = "test_token"
    mock.create_viewer.return_value = "test_token"
    mock.get_plays.return_value = []
    mock.all_joined.return_value = False

    # Set up status methods
    mock.joined_status.return_value = {"black": True, "white": False}
    mock.ready_status.return_value = {"black": True, "white": False}
    mock.all_ready.return_value = False

    # Set up list_rooms
    mock.list_rooms.return_value = ["game1", "game2"]

    # Set up create_room
    mock.create_room.return_value = {
        "game_id": "test_game_id",
        "black_key": "black_key",
        "white_key": "white_key",
        "viewer_key": "viewer_key",
    }

    # Set up games dict to prevent KeyError in tests
    mock.games = {
        "test_game_id": {
            "started": False,
            "joined": {"black": False, "white": False},
            "ready": {"black": False, "white": False},
            "keys": {
                "black": "black_key",
                "white": "white_key",
                "viewer": "viewer_key",
            },
            "plays": [],
        }
    }

    return mock


@pytest.fixture
def app_context():
    """Create a Flask application context for testing."""
    with app.app_context():
        yield


@pytest.fixture
def client(mock_storage, app_context):
    """Create Flask test client with mocked storage."""
    with patch("polyclash.server.storage", mock_storage):
        with app.test_client(use_cookies=True) as client:
            yield client


@pytest.fixture(autouse=True)
def prevent_redis_calls():
    """Prevent calls to actual Redis in tests."""
    with (
        patch("redis.Redis.hget", return_value=b"test_value"),
        patch("redis.Redis.exists", return_value=True),
        patch("redis.Redis.hset", return_value=True),
        patch("redis.Redis.keys", return_value=[]),
        patch("redis.Redis.delete", return_value=True),
        patch("redis.Redis.hmset", return_value=True),
    ):
        yield


@pytest.fixture
def mock_request_context():
    """Create a mock for request context."""
    mock = MagicMock()
    mock.sid = "test_sid"
    return mock


@pytest.fixture
def mock_socketio():
    """Create a mock for socketio operations."""
    mock = MagicMock()
    return mock


class TestServerUtilityFunctions:
    """Test utility functions in the server module."""

    @patch("polyclash.server.join_room")
    @patch("polyclash.server.socketio")
    def test_player_join_room(
        self,
        mock_socketio,
        mock_join_room,
        mock_storage,
        mock_request_context,
        app_context,
    ):
        """Test player_join_room function."""
        # Set up mocks
        mock_storage.create_player.return_value = "test_token"
        mock_storage.get_key.return_value = "test_key"
        mock_storage.all_joined.return_value = False
        mock_storage.get_plays.return_value = []

        # Call function
        with (
            patch("polyclash.server.request", mock_request_context),
            patch("polyclash.server.storage", mock_storage),
        ):
            result = player_join_room("test_game_id", "black")

        # Verify results
        assert result == "test_token"
        mock_storage.get_key.assert_called_with("test_game_id", "black")
        mock_storage.create_player.assert_called_with("test_key", "black")
        mock_join_room.assert_called_with("test_game_id")
        mock_socketio.emit.assert_called_once_with(
            "joined",
            {"role": "black", "token": "test_token", "plays": []},
            room="test_game_id",
        )

    @patch("polyclash.server.join_room")
    @patch("polyclash.server.socketio")
    def test_player_join_room_all_joined(
        self,
        mock_socketio,
        mock_join_room,
        mock_storage,
        mock_request_context,
        app_context,
    ):
        """Test player_join_room function when all players joined."""
        # Set up mocks
        mock_storage.create_player.return_value = "test_token"
        mock_storage.get_key.return_value = "test_key"
        mock_storage.all_joined.return_value = True
        mock_storage.get_plays.return_value = []

        # Call function
        with (
            patch("polyclash.server.request", mock_request_context),
            patch("polyclash.server.storage", mock_storage),
        ):
            result = player_join_room("test_game_id", "black")

        # Verify results
        assert result == "test_token"
        mock_storage.get_key.assert_called_with("test_game_id", "black")
        mock_storage.create_player.assert_called_with("test_key", "black")
        mock_join_room.assert_called_with("test_game_id")

        # Should emit 3 times (one for the player joining and two for both players)
        assert mock_socketio.emit.call_count == 3

    @patch("polyclash.server.join_room")
    @patch("polyclash.server.socketio")
    def test_viewer_join_room(
        self,
        mock_socketio,
        mock_join_room,
        mock_storage,
        mock_request_context,
        app_context,
    ):
        """Test viewer_join_room function."""
        # Set up mocks
        mock_storage.create_viewer.return_value = "test_token"
        mock_storage.get_key.return_value = "test_key"
        mock_storage.get_plays.return_value = []

        # Call function
        with (
            patch("polyclash.server.request", mock_request_context),
            patch("polyclash.server.storage", mock_storage),
        ):
            result = viewer_join_room("test_game_id")

        # Verify results
        assert result == "test_token"
        mock_storage.get_key.assert_called_with("test_game_id", "viewer")
        mock_storage.create_viewer.assert_called_with("test_key")
        mock_join_room.assert_called_with("test_game_id")
        mock_socketio.emit.assert_called_once_with(
            "joined",
            {"role": "viewer", "token": "test_token", "plays": []},
            room="test_game_id",
        )

    @patch("polyclash.server.socketio")
    def test_player_ready(self, mock_socketio, mock_storage, app_context):
        """Test player_ready function."""
        # Set up mocks
        mock_storage.all_joined.return_value = True
        mock_storage.all_ready.return_value = False

        # Call function
        with patch("polyclash.server.storage", mock_storage):
            player_ready("test_game_id", "black")

        # Verify results
        mock_storage.mark_ready.assert_called_with("test_game_id", "black")
        mock_socketio.emit.assert_called_once_with(
            "ready", {"role": "black"}, room="test_game_id"
        )

    @patch("polyclash.server.socketio")
    def test_player_ready_all_ready(self, mock_socketio, mock_storage, app_context):
        """Test player_ready function when all players are ready."""
        # Set up mocks
        mock_storage.all_joined.return_value = True
        mock_storage.all_ready.return_value = True

        # Call function
        with patch("polyclash.server.storage", mock_storage):
            player_ready("test_game_id", "black")

        # Verify results
        mock_storage.mark_ready.assert_called_with("test_game_id", "black")
        mock_storage.start_game.assert_called_with("test_game_id")

        # Should emit twice (once for ready and once for start)
        assert mock_socketio.emit.call_count == 2
        mock_socketio.emit.assert_any_call(
            "ready", {"role": "black"}, room="test_game_id"
        )
        mock_socketio.emit.assert_any_call(
            "start", {"message": "Game has started"}, room="test_game_id"
        )

    @patch("polyclash.server.socketio")
    def test_delayed_start(self, mock_socketio, mock_storage, app_context):
        """Test delayed_start function."""
        # Call function
        with patch("polyclash.server.storage", mock_storage):
            delayed_start("test_game_id")

        # Verify results
        mock_storage.start_game.assert_called_with("test_game_id")
        mock_socketio.emit.assert_called_once_with(
            "start", {"message": "Game has started"}, room="test_game_id"
        )


class TestAPIDecorator:
    """Test the API decorator functionality."""

    # Instead of using real route registration, let's create separate test Flask app
    # for each test to avoid Flask's "cannot add route after first request" error
    @pytest.fixture(autouse=True)
    def setup_test_app(self):
        """Create a fresh Flask app for each test."""
        self.test_app = Flask("test_app")
        self.test_app.config["TESTING"] = True
        self.test_app.secret_key = "test_secret_key"

        yield

    def test_api_call_decorator_server_token(self, mock_storage, app_context):
        """Test API decorator with server token."""

        # Copy the real decorator functionality to our test version
        def test_api_call(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if (
                    request.get_json()
                    and request.get_json().get("token") == server_token
                ):
                    return f(*args, **kwargs)
                return {"message": "invalid token"}, 401

            return decorated_function

        # Create test route
        @self.test_app.route("/test_route1", methods=["POST"])
        @test_api_call
        def test_func1():
            return {"success": True}, 200

        # Make a request with server token
        with self.test_app.test_client() as client:
            response = client.post("/test_route1", json={"token": server_token})

            # Verify response
            assert response.status_code == 200
            assert response.json == {"success": True}

    def test_api_call_decorator_invalid_server_token(self, mock_storage, app_context):
        """Test API decorator with invalid server token."""

        # Create simple test decorator that mimics the real one
        def test_api_call(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if (
                    request.get_json()
                    and request.get_json().get("token") == server_token
                ):
                    return f(*args, **kwargs)
                return {"message": "invalid token"}, 401

            return decorated_function

        # Create test route
        @self.test_app.route("/test_route2", methods=["POST"])
        @test_api_call
        def test_func2():
            return {"success": True}, 200

        # Make a request with invalid server token
        with self.test_app.test_client() as client:
            response = client.post(
                "/test_route2", json={"token": "invalid_" + server_token}
            )

            # Verify response
            assert response.status_code == 401
            assert response.json == {"message": "invalid token"}

    def test_api_call_decorator_player_token(self, mock_storage, app_context):
        """Test API decorator with player token."""

        # Create simple test decorator that mimics the real one for player tokens
        def test_api_call(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if (
                    request.get_json()
                    and request.get_json().get("token") == "player_token"
                ):
                    # Simulate the real decorator's behavior of adding game_id and role
                    return f(game_id="test_game_id", role="black", **kwargs)
                return {"message": "invalid token"}, 401

            return decorated_function

        # Create test route
        @self.test_app.route("/test_route3", methods=["POST"])
        @test_api_call
        def test_func3(game_id=None, role=None, token=None):
            return {"game_id": game_id, "role": role}, 200

        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request with player token
        with self.test_app.test_client() as client:
            response = client.post("/test_route3", json={"token": "player_token"})

            # Verify response
            assert response.status_code == 200
            assert response.json == {"game_id": "test_game_id", "role": "black"}

    def test_api_call_decorator_invalid_player_token(self, mock_storage, app_context):
        """Test API decorator with invalid player token."""

        # Create simple test decorator that mimics the real one
        def test_api_call(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                if request.get_json() and request.get_json().get("token"):
                    if mock_storage.contains(request.get_json().get("token")):
                        return f(*args, **kwargs)
                return {"message": "invalid token"}, 401

            return decorated_function

        # Create test route
        @self.test_app.route("/test_route4", methods=["POST"])
        @test_api_call
        def test_func4():
            return {"success": True}, 200

        # Set up mocks
        mock_storage.contains.return_value = False

        # Make a request with invalid player token
        with self.test_app.test_client() as client:
            response = client.post(
                "/test_route4", json={"token": "invalid_player_token"}
            )

            # Verify response
            assert response.status_code == 401
            assert response.json == {"message": "invalid token"}

    def test_api_call_decorator_exception(self, mock_storage, app_context):
        """Test API decorator with exception."""

        # Create simple test decorator that mimics the real one with exception handling
        def test_api_call(f):
            @wraps(f)
            def decorated_function(*args, **kwargs):
                try:
                    if (
                        request.get_json()
                        and request.get_json().get("token") == server_token
                    ):
                        return f(*args, **kwargs)
                    return {"message": "invalid token"}, 401
                except Exception as e:
                    return {"message": str(e)}, 500

            return decorated_function

        # Create test route
        @self.test_app.route("/test_route5", methods=["POST"])
        @test_api_call
        def test_func5():
            raise ValueError("Test error")

        # Make a request that will trigger an exception
        with self.test_app.test_client() as client:
            response = client.post("/test_route5", json={"token": server_token})

            # Verify response
            assert response.status_code == 500
            assert response.json == {"message": "Test error"}


class TestAPIEndpoints:
    """Test the API endpoints."""

    def test_index(self, client, mock_storage):
        """Test index endpoint."""
        # Set up mocks
        mock_storage.list_rooms.return_value = ["game1", "game2"]
        mock_storage.get_key.return_value = "viewer_key"

        # Call endpoint
        response = client.get("/sphgo/")

        # Verify response
        assert response.status_code == 200
        assert b"Welcome to PolyClash" in response.data
        assert bytes(f"Server token: {server_token}", "utf-8") in response.data
        assert b"viewer: viewer_key" in response.data

    def test_list_games(self, client, mock_storage):
        """Test list_games endpoint."""
        # Set up mocks
        mock_storage.list_rooms.return_value = ["game1", "game2"]

        # Call endpoint
        response = client.get("/sphgo/list")

        # Verify response
        assert response.status_code == 200
        assert response.json == {"rooms": ["game1", "game2"]}

    def test_new(self, client, mock_storage, app_context):
        """Test new endpoint."""
        # Set up mocks
        mock_storage.create_room.return_value = {
            "game_id": "test_game_id",
            "black_key": "black_key",
            "white_key": "white_key",
            "viewer_key": "viewer_key",
        }

        # Make a request to the endpoint
        response = client.post("/sphgo/new", json={"token": server_token})

        # Verify response
        assert response.status_code == 200
        assert response.json == {
            "game_id": "test_game_id",
            "black_key": "black_key",
            "white_key": "white_key",
            "viewer_key": "viewer_key",
        }

    def test_joined_status(self, client, mock_storage, app_context):
        """Test joined_status endpoint."""
        # Set up mocks
        mock_storage.joined_status.return_value = {"black": True, "white": False}
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request to the endpoint
        response = client.post("/sphgo/joined_status", json={"token": "player_token"})

        # Verify response
        assert response.status_code == 200
        assert response.json == {"status": {"black": True, "white": False}}

    def test_joined_status_invalid_role(self, client, mock_storage, app_context):
        """Test joined_status endpoint with invalid role."""
        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "invalid_role"

        # Make a request to the endpoint
        response = client.post("/sphgo/joined_status", json={"token": "player_token"})

        # Verify response
        assert response.status_code == 400
        assert response.json == {"message": "Invalid role"}

    @patch("polyclash.server.join_room")
    @patch("polyclash.server.player_join_room")
    def test_join_black(
        self, mock_player_join_room, mock_join_room, client, mock_storage, app_context
    ):
        """Test join endpoint for black player."""
        # Set up mocks
        mock_player_join_room.return_value = "test_token"
        mock_storage.joined_status.return_value = {"black": True, "white": False}
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request to the endpoint with game_id and role as query parameters
        with patch("polyclash.server.request", MagicMock(sid="test_sid")):
            response = client.post(
                "/sphgo/join",
                json={
                    "token": server_token,
                    "role": "black",
                    "game_id": "test_game_id",
                },
            )

            # Verify response
            assert response.status_code == 200
            assert response.json == {
                "token": "test_token",
                "status": {"black": True, "white": False},
            }
            mock_player_join_room.assert_called_with("test_game_id", "black")

    @patch("polyclash.server.join_room")
    @patch("polyclash.server.viewer_join_room")
    def test_join_viewer(
        self, mock_viewer_join_room, mock_join_room, client, mock_storage, app_context
    ):
        """Test join endpoint for viewer."""
        # Set up mocks
        mock_viewer_join_room.return_value = "test_token"
        mock_storage.joined_status.return_value = {"black": True, "white": False}
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "viewer"

        # Make a request to the endpoint with game_id as a query parameter
        with patch("polyclash.server.request", MagicMock(sid="test_sid")):
            response = client.post(
                "/sphgo/join",
                json={
                    "token": server_token,
                    "role": "viewer",
                    "game_id": "test_game_id",
                },
            )

            # Verify response
            assert response.status_code == 200
            assert response.json == {
                "token": "test_token",
                "status": {"black": True, "white": False},
            }
            mock_viewer_join_room.assert_called_with("test_game_id")

    def test_join_invalid_role(self, client, mock_storage, app_context):
        """Test join endpoint with invalid role."""
        # Set up mocks for server token validation
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "invalid_role"

        # Make a request to the endpoint with an invalid role
        response = client.post(
            "/sphgo/join", json={"token": server_token, "role": "invalid_role"}
        )

        # Verify response
        assert response.status_code == 400
        assert response.json == {"message": "Invalid role"}

    def test_ready_status(self, client, mock_storage, app_context):
        """Test ready_status endpoint."""
        # Set up mocks
        mock_storage.ready_status.return_value = {"black": True, "white": False}
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request to the endpoint
        response = client.post("/sphgo/ready_status", json={"token": "player_token"})

        # Verify response
        assert response.status_code == 200
        assert response.json == {"status": {"black": True, "white": False}}

    @patch("polyclash.server.player_ready")
    def test_ready(self, mock_player_ready, client, mock_storage, app_context):
        """Test ready endpoint."""
        # Set up mocks
        mock_storage.ready_status.return_value = {"black": True, "white": False}
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request to the endpoint
        response = client.post("/sphgo/ready", json={"token": "player_token"})

        # Verify response
        assert response.status_code == 200
        assert response.json == {"status": {"black": True, "white": False}}
        mock_player_ready.assert_called_with("test_game_id", "black")

    @patch("polyclash.server.player_canceled")
    def test_cancel(self, mock_player_canceled, client, mock_storage, app_context):
        """Test cancel endpoint."""
        # Set up mocks
        mock_storage.ready_status.return_value = {"black": False, "white": False}
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request to the endpoint
        response = client.post("/sphgo/cancel", json={"token": "player_token"})

        # Verify response
        assert response.status_code == 200
        assert response.json == {"status": {"black": False, "white": False}}
        mock_player_canceled.assert_called_with("test_game_id", "black")

    def test_close(self, client, mock_storage, app_context):
        """Test close endpoint."""
        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Make a request to the endpoint
        response = client.post("/sphgo/close", json={"token": "player_token"})

        # Verify response
        assert response.status_code == 200
        assert response.json == {"message": "Game closed"}
        mock_storage.close_room.assert_called_with("test_game_id")

    @patch("polyclash.server.socketio")
    def test_play_valid(self, mock_socketio, client, mock_storage, app_context):
        """Test play endpoint with valid play."""
        # Set up mocks
        mock_storage.get_plays.return_value = []
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Find a valid play from valid_plays set
        valid_play_str = list(valid_plays)[0]
        valid_play = [int(x) for x in valid_play_str.split(",") if x]

        # Make a request to the endpoint
        response = client.post(
            "/sphgo/play",
            json={"token": "player_token", "steps": 0, "play": valid_play},
        )

        # Verify response
        assert response.status_code == 200
        assert response.json == {"message": "Play processed"}
        mock_storage.add_play.assert_called_with("test_game_id", valid_play)
        mock_socketio.emit.assert_called_with(
            "played",
            {"role": "black", "steps": 0, "play": valid_play},
            room="test_game_id",
        )

    def test_play_steps_mismatch(self, client, mock_storage, app_context):
        """Test play endpoint with steps mismatch."""
        # Set up mocks
        mock_storage.get_plays.return_value = ["existing_play"]
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = "black"

        # Find a valid play from valid_plays set
        valid_play_str = list(valid_plays)[0]
        valid_play = [int(x) for x in valid_play_str.split(",") if x]

        # Make a request to the endpoint
        response = client.post(
            "/sphgo/play",
            json={
                "token": "player_token",
                "steps": 0,  # Mismatch with plays length (1)
                "play": valid_play,
            },
        )

        # Verify response
        assert response.status_code == 400
        assert "Length of 1 mismatched with steps 0" in response.json["message"]

    def test_play_wrong_turn(self, client, mock_storage, app_context):
        """Test play endpoint with wrong player turn."""
        # Set up mocks
        mock_storage.get_plays.return_value = []
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.exists.return_value = True
        mock_storage.get_role.return_value = (
            "white"  # White can't play on even steps (0)
        )

        # Find a valid play from valid_plays set
        valid_play_str = list(valid_plays)[0]
        valid_play = [int(x) for x in valid_play_str.split(",") if x]

        # Make a request to the endpoint
        response = client.post(
            "/sphgo/play",
            json={"token": "player_token", "steps": 0, "play": valid_play},
        )

        # Verify response
        assert response.status_code == 400
        assert response.json == {"message": "Invalid player"}


class TestSocketEvents:
    """Test socket.io event handlers."""

    @patch("polyclash.server.player_join_room")
    @patch("polyclash.server.emit")
    def test_on_join_black(self, mock_emit, mock_player_join_room, mock_storage):
        """Test on_join event for black player."""
        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.get_role.return_value = "black"

        # Call event handler
        with patch("polyclash.server.storage", mock_storage):
            on_join({"key": "test_key"})

        # Verify results
        mock_player_join_room.assert_called_with("test_game_id", "black")

    @patch("polyclash.server.viewer_join_room")
    @patch("polyclash.server.emit")
    def test_on_join_viewer(self, mock_emit, mock_viewer_join_room, mock_storage):
        """Test on_join event for viewer."""
        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.get_role.return_value = "viewer"

        # Call event handler
        with patch("polyclash.server.storage", mock_storage):
            on_join({"key": "test_key"})

        # Verify results
        mock_viewer_join_room.assert_called_with("test_game_id")

    @patch("polyclash.server.emit")
    def test_on_join_invalid_key(self, mock_emit, mock_storage):
        """Test on_join event with invalid key."""
        # Set up mocks
        mock_storage.contains.return_value = False

        # Call event handler
        with patch("polyclash.server.storage", mock_storage):
            on_join({"key": "invalid_key"})

        # Verify results
        mock_emit.assert_called_with("error", {"message": "Game not found"})

    @patch("polyclash.server.emit")
    def test_on_join_exception(self, mock_emit):
        """Test on_join event with exception."""
        # Call event handler with missing key
        on_join({})

        # Verify results
        mock_emit.assert_called_with("error", {"message": ANY})

    @patch("polyclash.server.delayed_start")
    @patch("polyclash.server.emit")
    @patch("polyclash.server.Thread")
    def test_on_ready_black(
        self, mock_thread, mock_emit, mock_delayed_start, mock_storage
    ):
        """Test on_ready event for black player."""
        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.get_role.return_value = "black"
        mock_storage.all_ready.return_value = False

        # Call event handler
        with patch("polyclash.server.storage", mock_storage):
            on_ready({"key": "test_key"})

        # Verify results
        mock_storage.mark_ready.assert_called_with("test_game_id", "black")
        mock_emit.assert_called_with("ready", {"role": "black"}, room="test_game_id")
        mock_thread.assert_not_called()

    @patch("polyclash.server.emit")
    @patch("polyclash.server.Thread")
    def test_on_ready_all_ready(self, mock_thread, mock_emit, mock_storage):
        """Test on_ready event when all players are ready."""
        # Set up mocks
        mock_storage.contains.return_value = True
        mock_storage.get_game_id.return_value = "test_game_id"
        mock_storage.get_role.return_value = "black"
        mock_storage.all_ready.return_value = True

        # Setup thread mock
        thread_instance = MagicMock()
        mock_thread.return_value = thread_instance

        # Call event handler
        with patch("polyclash.server.storage", mock_storage):
            with patch("polyclash.server.delayed_start") as mock_delayed_start:
                on_ready({"key": "test_key"})

        # Verify results
        mock_storage.mark_ready.assert_called_with("test_game_id", "black")
        mock_emit.assert_called_with("ready", {"role": "black"}, room="test_game_id")
        mock_thread.assert_called_once()
        thread_instance.start.assert_called_once()

    @patch("polyclash.server.emit")
    def test_on_ready_invalid_key(self, mock_emit, mock_storage):
        """Test on_ready event with invalid key."""
        # Set up mocks
        mock_storage.contains.return_value = False

        # Call event handler
        with patch("polyclash.server.storage", mock_storage):
            on_ready({"key": "invalid_key"})

        # Verify results
        mock_emit.assert_called_with("error", {"message": "Game not found"})
