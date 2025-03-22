import pytest
import tempfile
import os
from polyclash.server import app as flask_app

@pytest.fixture
def client():
    """Fixture for a Flask test client."""
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as client:
        yield client

@pytest.fixture
def socket_client():
    """Fixture for a Socket.IO test client."""
    from flask_socketio import SocketIOTestClient
    from polyclash.server import socketio
    
    flask_app.config['TESTING'] = True
    client = SocketIOTestClient(flask_app, socketio)
    return client
