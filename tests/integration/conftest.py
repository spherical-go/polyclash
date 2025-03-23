import pytest
import tempfile
import os
from polyclash.server import app as flask_app
from polyclash.server import socketio
from PyQt5.QtWidgets import QApplication
from polyclash.gui.main import MainWindow
from polyclash.game.controller import SphericalGoController

@pytest.fixture
def socket_client():
    """Fixture for a Socket.IO test client."""
    from flask_socketio import SocketIOTestClient
    
    flask_app.config['TESTING'] = True
    client = SocketIOTestClient(flask_app, socketio)
    return client

@pytest.fixture(scope="session")
def qapp():
    """Fixture for a QApplication instance."""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(qapp, monkeypatch):
    """Fixture for a mocked MainWindow instance."""
    from unittest.mock import MagicMock
    
    # Create a controller
    controller = SphericalGoController()
    
    # Create a mock MainWindow
    window = MagicMock()
    window.controller = controller
    
    # Mock the view_sphere
    window.view_sphere = MagicMock()
    window.view_sphere.update = MagicMock()
    
    # Mock the update_status method
    window.update_status = MagicMock()
    
    # Connect signals to our mocked methods
    controller.playerPlaced.connect(lambda player, pos: window.view_sphere.update())
    controller.gameStarted.connect(window.update_status)
    controller.gameEnded.connect(window.update_status)
    
    # There's no playerSwitched signal, but playerPlaced also triggers player switching
    controller.playerPlaced.connect(lambda player, pos: window.update_status())
    
    yield window
