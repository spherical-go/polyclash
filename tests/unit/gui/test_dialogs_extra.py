from unittest.mock import MagicMock, patch

import pytest
from PyQt5.QtWidgets import QApplication, QWidget

from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import LOCAL, SphericalGoController
from polyclash.game.player import HUMAN
from polyclash.gui.dialogs import (
    JoinGameDialog,
    LocalGameDialog,
    NetworkGameDialog,
    restart_network_worker,
)


class FakeAPI:
    def __init__(self, joined_status_value="Both", ready_status_value=True):
        self._joined_status_value = joined_status_value
        self._ready_status_value = ready_status_value
        self.join_called = False
        self.ready_called = False
        self.cancel_called = False

    def joined_status(self, server, key):
        return self._joined_status_value

    def ready_status(self, server, key):
        return self._ready_status_value

    def join(self, server, role, key):
        self.join_called = True
        return "Ready"

    def ready(self, server, role, key):
        self.ready_called = True
        return "Ready"

    def cancel(self, server, role, key):
        self.cancel_called = True
        return "Canceled"


class DummyMessageSignal:
    def __init__(self):
        self._callbacks = []

    def connect(self, fn):
        self._callbacks.append(fn)

    def disconnect(self, fn):
        # remove if present
        self._callbacks = [cb for cb in self._callbacks if cb is not fn]

    def emit(self, event, data):
        for cb in list(self._callbacks):
            cb(event, data)


class DummyNetworkWorker:
    def __init__(self, parent=None, server=None, role=None, key=None):
        self.parent = parent
        self.server = server
        self.role = role
        self.key = key
        self.started = False
        self.stopped = False
        self.messageReceived = DummyMessageSignal()

    def start(self):
        self.started = True

    def stop(self):
        self.stopped = True


class FakeWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.controller = SphericalGoController()
        self.update = MagicMock()
        self.status_bar = MagicMock()
        self.api = FakeAPI()
        self.network_worker = None

    def handle_network_notification(self, *args, **kwargs):
        pass


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app
    # do not quit here to avoid affecting other tests


def test_local_game_dialog_ai_vs_ai_blocked(qapp, monkeypatch):
    window = FakeWindow()
    dlg = LocalGameDialog(parent=window)

    # Set both players to AI
    dlg.black_type.setCurrentText("AI")
    dlg.white_type.setCurrentText("AI")

    with patch("polyclash.gui.dialogs.QMessageBox.critical") as mock_critical:
        dlg.on_start_clicked()
        mock_critical.assert_called_once()
        # Ensure players were not added
        assert BLACK not in window.controller.players
        assert WHITE not in window.controller.players


def test_local_game_dialog_start_success(qapp):
    window = FakeWindow()
    dlg = LocalGameDialog(parent=window)

    dlg.black_type.setCurrentText("Human")
    dlg.white_type.setCurrentText("Human")

    dlg.on_start_clicked()

    assert window.controller.mode == LOCAL
    assert window.controller.players[BLACK].kind == HUMAN
    assert window.controller.players[WHITE].kind == HUMAN
    window.update.assert_called()


def test_network_game_dialog_invalid_server_empty(qapp, monkeypatch):
    window = FakeWindow()
    dlg = NetworkGameDialog(parent=window)

    dlg.server_input.setText("")
    with patch("polyclash.gui.dialogs.QMessageBox.critical") as mock_critical:
        dlg.on_connect_clicked()
        mock_critical.assert_called_once()
        args = mock_critical.call_args[0]
        assert "Server address is required" in args


def test_network_game_dialog_invalid_server_format(qapp):
    window = FakeWindow()
    dlg = NetworkGameDialog(parent=window)

    dlg.server_input.setText("not-a-url")
    dlg.token.setText("t")
    with patch("polyclash.gui.dialogs.QMessageBox.critical") as mock_critical:
        dlg.on_connect_clicked()
        mock_critical.assert_called_once()
        args = mock_critical.call_args[0]
        assert "Invalid server address" in args


def test_network_game_dialog_connect_success(qapp, monkeypatch):
    window = FakeWindow()
    dlg = NetworkGameDialog(parent=window)

    dlg.server_input.setText("http://example.com")
    dlg.token.setText("abc")

    with patch("polyclash.gui.dialogs.connect", return_value=("bk", "wk", "vk")):
        dlg.on_connect_clicked()
        assert dlg.black_key.text() == "bk"
        assert dlg.white_key.text() == "wk"
        assert dlg.viewer_key.text() == "vk"


def test_network_game_dialog_connect_failure(qapp, monkeypatch):
    window = FakeWindow()
    dlg = NetworkGameDialog(parent=window)

    dlg.server_input.setText("http://example.com")
    dlg.token.setText("abc")

    with (
        patch("polyclash.gui.dialogs.connect", side_effect=ValueError("boom")),
        patch("polyclash.gui.dialogs.QMessageBox.critical") as mock_critical,
    ):
        closed = {"v": False}

        def fake_close():
            closed["v"] = True

        dlg.close = fake_close
        dlg.on_connect_clicked()
        mock_critical.assert_called_once()
        assert closed["v"] is True


def test_copy_text(qapp):
    window = FakeWindow()
    dlg = NetworkGameDialog(parent=window)
    dlg.black_key.setText("hello")
    dlg.copy_text("black")
    assert QApplication.clipboard().text() == "hello"


def test_restart_network_worker_new(qapp, monkeypatch):
    window = FakeWindow()
    window.network_worker = None

    # Monkeypatch the NetworkWorker used inside dialogs to our dummy
    import polyclash.gui.dialogs as dlgmod

    monkeypatch.setattr(dlgmod, "NetworkWorker", DummyNetworkWorker)

    collected = []

    def extra_handler(event, data):
        collected.append((event, data))

    restart_network_worker(
        window, server="http://s", role="black", key="k", fn=extra_handler
    )

    assert isinstance(window.network_worker, DummyNetworkWorker)
    assert window.network_worker.started is True
    # two connections: handle_network_notification and extra_handler
    # simulate an event
    window.network_worker.messageReceived.emit("joined", {"x": 1})
    assert ("joined", {"x": 1}) in collected


def test_restart_network_worker_existing(qapp):
    window = FakeWindow()

    class ExistingWorker(DummyNetworkWorker):
        def __init__(self):
            super().__init__()
            self._disconnect_called = False

            class _Msg(DummyMessageSignal):
                def __init__(self, outer):
                    super().__init__()
                    self.outer = outer

                def disconnect(self, fn):
                    self.outer._disconnect_called = True
                    super().disconnect(fn)

            self.messageReceived = _Msg(self)

    existing = ExistingWorker()
    window.network_worker = existing

    restart_network_worker(
        window, server="http://s2", role="white", key="k2", fn=lambda *_: None
    )

    assert existing.stopped is True
    assert existing.server == "http://s2"
    assert existing.role == "white"
    assert existing.key == "k2"
    assert existing.started is True
    assert existing._disconnect_called is True


def test_join_game_dialog_on_join_clicked_both_ready_enables_ready(qapp, monkeypatch):
    window = FakeWindow()
    window.api = FakeAPI(joined_status_value="Both")

    dlgmod_path = "polyclash.gui.dialogs"
    # Avoid sleeps
    monkeypatch.setattr(f"{dlgmod_path}.time.sleep", lambda *_: None)

    # Stub restart_network_worker to immediately invoke the provided callback with "joined"
    def fake_restart(window_param, server, role, key, fn):
        fn("joined", {"role": role})

    monkeypatch.setattr(f"{dlgmod_path}.restart_network_worker", fake_restart)

    dlg = JoinGameDialog(parent=window)
    dlg.server_input.setText("http://example.com")
    dlg.role_select.setCurrentText("Black")
    dlg.key_input.setText("k")

    # Prepare network_worker with a messageReceived to support later disconnect
    window.network_worker = DummyNetworkWorker(parent=window)

    dlg.on_join_clicked()

    # Ready button should now be enabled when status is "Both"
    assert dlg.ready_button.isEnabled()
    assert window.api.join_called is True
    assert dlg.cancel_button.isEnabled() is True


def test_join_game_dialog_on_ready_clicked_starts_game_and_closes(qapp, monkeypatch):
    window = FakeWindow()
    window.api = FakeAPI(joined_status_value="Both", ready_status_value=True)

    dlgmod_path = "polyclash.gui.dialogs"
    monkeypatch.setattr(f"{dlgmod_path}.time.sleep", lambda *_: None)

    dlg = JoinGameDialog(parent=window)
    dlg.server_input.setText("http://example.com")
    dlg.role_select.setCurrentText("Black")
    dlg.key_input.setText("k")

    # Provide a dummy network worker with messageReceived to trigger "ready"
    window.network_worker = DummyNetworkWorker(parent=window)
    started = {"v": False}

    # Spy on controller.start
    orig_start = window.controller.start

    def spy_start():
        started["v"] = True
        return orig_start()

    window.controller.start = spy_start

    # Call ready which attaches the handler
    dlg.on_ready_clicked()

    # Now emit "ready" to simulate server event
    window.network_worker.messageReceived.emit("ready", {})

    assert started["v"] is True
    assert window.api.ready_called is True
    # Cancel button should be disabled after ready
    assert dlg.cancel_button.isEnabled() is False


def test_join_game_dialog_on_cancel_clicked_calls_api_and_closes(qapp):
    window = FakeWindow()
    window.api = FakeAPI()

    dlg = JoinGameDialog(parent=window)
    dlg.server_input.setText("http://example.com")
    dlg.role_select.setCurrentText("White")
    dlg.key_input.setText("kw")

    closed = {"v": False}

    def fake_close():
        closed["v"] = True

    dlg.close = fake_close

    dlg.on_cancel_clicked()

    assert window.api.cancel_called is True
    assert closed["v"] is True
