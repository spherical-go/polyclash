import json

from PyQt5.QtCore import QThread, pyqtSignal


class NetworkWorker(QThread):
    messageReceived = pyqtSignal(str, str)

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
            data = dict(data)
            self.messageReceived.emit('joined', json.dumps(data))

        @sio.event
        def played(data):
            print('played... ', data)
            data = dict(data)
            self.messageReceived.emit('played', json.dumps(data))

        @sio.event
        def error(data):
            print('error... ', data)
            data = dict(data)
            self.messageReceived.emit('error', json.dumps(data))

        @sio.event
        def disconnect():
            print('disconnected...')
            if self.is_running:
                sio.connect(self.server)

        self.sio = sio
        self.messageReceived.connect(parent.handle_notification)

    def run(self):
        self.sio.connect(self.server)
        while self.is_running:
            self.sio.wait()

    def stop(self):
        self.is_running = False
        self.sio.disconnect()
        self.wait()

