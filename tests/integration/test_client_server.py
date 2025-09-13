import os
import secrets
from unittest.mock import MagicMock, patch

import pytest

import polyclash.server
# Import the server module
from polyclash.server import app
from polyclash.util.api import close, connect, join, play, ready

# Set a fixed token for testing
TEST_TOKEN = "test_token_for_integration_tests"

# Patch the server token directly
polyclash.server.server_token = TEST_TOKEN


class TestClientServerIntegration:
    def test_new_game_endpoint(self, test_client):
        """Test the /sphgo/new endpoint."""
        response = test_client.post("/sphgo/new", json={"token": TEST_TOKEN})
        assert response.status_code == 200
        data = response.get_json()
        assert "game_id" in data
        assert "black_key" in data
        assert "white_key" in data
        assert "viewer_key" in data

    def test_join_endpoint(self, test_client, auth_handshake):
        """Test the /sphgo/join endpoint."""
        # Use the auth_handshake fixture to verify join was successful
        assert auth_handshake["black_token"] is not None
        assert auth_handshake["white_token"] is not None

    def test_ready_endpoint(self, test_client, auth_handshake):
        """Test the /sphgo/ready endpoint."""
        # Use the auth_handshake fixture to get tokens
        black_token = auth_handshake["black_token"]

        # Then mark as ready
        response = test_client.post(
            "/sphgo/ready", json={"token": black_token, "role": "black"}
        )
        assert response.status_code == 200

    def test_play_endpoint(self, test_client, auth_handshake):
        """Test the /sphgo/play endpoint."""
        # Use the auth_handshake fixture to get tokens
        black_token = auth_handshake["black_token"]

        # Mark black as ready
        response = test_client.post(
            "/sphgo/ready", json={"token": black_token, "role": "black"}
        )
        assert response.status_code == 200

        # Mark white as ready
        white_token = auth_handshake["white_token"]
        response = test_client.post(
            "/sphgo/ready", json={"token": white_token, "role": "white"}
        )
        assert response.status_code == 200

        # Play a move as black (first player)
        response = test_client.post(
            "/sphgo/play",
            json={
                "token": black_token,
                "role": "black",
                "steps": 0,
                "play": [0, 1, 2, 3, 4],
            },
        )
        assert response.status_code == 200

    def test_close_endpoint(self, test_client, auth_handshake):
        """Test the /sphgo/close endpoint."""
        # Use the auth_handshake fixture to get tokens
        black_token = auth_handshake["black_token"]

        # Then close it
        response = test_client.post("/sphgo/close", json={"token": black_token})
        assert response.status_code == 200


class TestClientServerErrorHandling:
    def test_invalid_token(self, test_client):
        """Test error handling for invalid tokens."""
        response = test_client.post(
            "/sphgo/join", json={"token": "invalid_token", "role": "black"}
        )
        assert response.status_code == 401

    def test_invalid_role(self, test_client):
        """Test error handling for invalid roles."""
        # First create a game
        response = test_client.post("/sphgo/new", json={"token": TEST_TOKEN})
        data = response.get_json()
        black_key = data["black_key"]

        # Then try to join with an invalid role
        response = test_client.post(
            "/sphgo/join", json={"token": black_key, "role": "invalid_role"}
        )
        assert response.status_code == 400
