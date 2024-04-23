import json

from PyQt5.QtCore import QThread, pyqtSignal


class NetworkWorker(QThread):
    messageReceived = pyqtSignal(str, object)

    def __init__(self, parent=None, server=None, role=None, key=None):
        super(NetworkWorker, self).__init__(parent)
        self.is_running = True
        self.server = server
        self.role = role
        self.key = key

        import socketio
        sio = socketio.Client()

        @sio.event
        def connect():
            sio.emit('join', {'key': key})

        @sio.event
        def joined(data):
            print('joined... ', data)
            self.messageReceived.emit('joined', data)

        @sio.event
        def played(data):
            print('played... ', data)
            self.messageReceived.emit('played', data)

        @sio.event
        def error(data):
            print('error... ', data)
            self.messageReceived.emit('error', data)

        @sio.event
        def disconnect():
            print('disconnected...')
            if self.is_running:
                sio.connect(self.server)

        self.sio = sio
        self.messageReceived.connect(parent.handle_network_notification)

    def run(self):
        self.sio.connect(self.server)
        while self.is_running:
            self.sio.wait()

    def stop(self):
        self.is_running = False
        self.sio.disconnect()
        self.wait()

