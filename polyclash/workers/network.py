from __future__ import annotations

import time
from typing import Any, Optional

from PyQt5.QtCore import QThread, pyqtSignal


class NetworkWorker(QThread):
    messageReceived = pyqtSignal(str, object)

    def __init__(
        self,
        parent: Optional[Any] = None,
        server: Optional[str] = None,
        role: Optional[str] = None,
        key: Optional[str] = None,
    ) -> None:
        super(NetworkWorker, self).__init__(parent)
        self.is_running: bool = True
        self.server: Optional[str] = server

        # Import locally to avoid hard dependency at module import time
        import socketio

        sio: Any = socketio.Client()

        @sio.event
        def connect() -> None:
            sio.emit("join", {"key": key})

        @sio.event
        def joined(data: object) -> None:
            print("Player joined... ", data)
            self.messageReceived.emit("joined", data)

        @sio.event
        def ready(data: object) -> None:
            print("Player ready...", data)
            self.messageReceived.emit("ready", data)

        @sio.event
        def start(data: object) -> None:
            print("Game started...", data)
            self.messageReceived.emit("start", data)

        @sio.event
        def played(data: object) -> None:
            print("Player played... ", data)
            self.messageReceived.emit("played", data)

        @sio.event
        def error(data: object) -> None:
            print("error... ", data)
            self.messageReceived.emit("error", data)

        @sio.event
        def disconnect() -> None:
            print("disconnected...")
            if self.is_running and self.server:
                time.sleep(1)  # Avoid reconnect storm
                sio.connect(self.server)

        self.sio: Any = sio
        if parent is not None and hasattr(parent, "handle_network_notification"):
            self.messageReceived.connect(parent.handle_network_notification)

    def run(self) -> None:
        try:
            if self.server:
                self.sio.connect(self.server)
            while self.is_running:
                self.sio.wait()
        except Exception as e:
            print(f"Error: {str(e)}")
            self.messageReceived.emit("error", {"message": str(e)})

    def stop(self) -> None:
        self.is_running = False
        self.sio.disconnect()
        time.sleep(1)
        self.wait()
