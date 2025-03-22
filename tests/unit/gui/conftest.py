import pytest
from PyQt5.QtWidgets import QApplication
from polyclash.gui.main import MainWindow
from polyclash.game.controller import SphericalGoController

@pytest.fixture(scope="session")
def qapp():
    """Fixture for a QApplication instance."""
    app = QApplication([])
    yield app
    app.quit()

@pytest.fixture
def main_window(qapp):
    """Fixture for a MainWindow instance."""
    controller = SphericalGoController()
    window = MainWindow(controller=controller)
    yield window
    window.close()
