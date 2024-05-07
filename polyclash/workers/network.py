import time

from PyQt5.QtCore import QThread, pyqtSignal


class NetworkWorker(QThread):
    messageReceived = pyqtSignal(str, object)

    def __init__(self, parent=None, server=None, role=None, key=None):
        super(NetworkWorker, self).__init__(parent)
        self.is_running = True
        self.server = server

        import socketio
        sio = socketio.Client()

        @sio.event
        def connect():
            sio.emit('join', {'key': key})

        @sio.event
        def joined(data):
            print('Player joined... ', data)
            self.messageReceived.emit('joined', data)

        @sio.event
        def ready(data):
            print('Player ready...', data)
            self.messageReceived.emit('ready', data)

        @sio.event
        def start(data):
            print('Game started...', data)
            self.messageReceived.emit('start', data)

        @sio.event
        def played(data):
            print('Player played... ', data)
            self.messageReceived.emit('played', data)

        @sio.event
        def error(data):
            print('error... ', data)
            self.messageReceived.emit('error', data)

        @sio.event
        def disconnect():
            print('disconnected...')
            if self.is_running:
                time.sleep(1)  # wait for a while before reconnecting to avoid reconnecting too many
                sio.connect(self.server)

        self.sio = sio
        self.messageReceived.connect(parent.handle_network_notification)

    def run(self):
        try:
            self.sio.connect(self.server)
            while self.is_running:
                self.sio.wait()
        except Exception as e:
            print(f"Error: {str(e)}")
            self.messageReceived.emit('error', {'message': str(e)})

    def stop(self):
        self.is_running = False
        self.sio.disconnect()
        time.sleep(1)
        self.wait()
