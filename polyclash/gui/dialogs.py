import time
import polyclash.gui.icons as icons

from urllib.parse import urlparse

from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QAction, \
    QVBoxLayout
from PyQt5.QtGui import QIcon, QImage, QPixmap

from polyclash.util.api import get_server, set_server, connect
from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import LOCAL, NETWORK
from polyclash.game.player import HUMAN, REMOTE
from polyclash.workers.network import NetworkWorker


def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


class LocalGameDialog(QDialog):
    def __init__(self, parent=None):
        super(LocalGameDialog, self).__init__(parent)
        self.setWindowTitle('Start A Local Game')
        self.setFixedWidth(200)
        layout = QVBoxLayout(self)

        self.black_type = QComboBox(self)
        self.black_type.addItem("Human")
        self.black_type.addItem("AI")
        layout.addWidget(QLabel('Black Type'))
        layout.addWidget(self.black_type)

        self.white_type = QComboBox(self)
        self.white_type.addItem("Human")
        self.white_type.addItem("AI")
        layout.addWidget(QLabel('White Type'))
        layout.addWidget(self.white_type)

        self.start_button = QPushButton('Start', self)
        self.start_button.clicked.connect(self.on_start_clicked)
        layout.addWidget(self.start_button)

        self.setLayout(layout)
        self.window = parent

    def on_start_clicked(self):
        from polyclash.game.player import HUMAN, AI

        black_kind = self.black_type.currentText()
        white_kind = self.white_type.currentText()
        if black_kind == 'AI' and white_kind == 'AI':
            QMessageBox.critical(self, 'Error', 'Black and White players must not be AI at the same time.')
            return

        controller = self.window.controller
        controller.set_mode(LOCAL)
        controller.add_player(BLACK, kind=HUMAN if black_kind == "Human" else AI)
        controller.add_player(WHITE, kind=HUMAN if white_kind == "Human" else AI)
        controller.start_game()
        self.window.update()
        self.close()


class NetworkGameDialog(QDialog):
    def __init__(self, parent=None):
        super(NetworkGameDialog, self).__init__(parent)
        self.setWindowTitle('Create A Network Game Room')
        layout = QVBoxLayout(self)

        # Server input (only enabled for Network mode)
        self.server_input = QLineEdit(self)
        self.server_input.setPlaceholderText("https://sphericalgo.org")
        layout.addWidget(QLabel('Server'))
        layout.addWidget(self.server_input)

        self.token = QLineEdit(self)
        layout.addWidget(QLabel('Token'))
        layout.addWidget(self.token)

        # Connection management
        self.connect_button = QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.on_connect_clicked)
        layout.addWidget(self.connect_button)

        # Manage keys for different roles
        self.manage_keys()

        # Close button
        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(self.on_close_clicked)
        layout.addWidget(self.close_button)

        self.setLayout(layout)
        self.window = parent

    def manage_keys(self):
        copy = QPixmap.fromImage(
            QImage(icons.array_copy.data, icons.array_copy.shape[1], icons.array_copy.shape[0], QImage.Format_RGBA8888))

        # Adds widgets for Black, White, and Viewer keys
        for color in ["Black", "White", "Viewer"]:
            setattr(self, f"{color.lower()}_key", QLineEdit(''))
            getattr(self, f"{color.lower()}_key").setReadOnly(True)
            copyAction = QAction(QIcon(copy), f'copy{color}', self)
            copyAction.triggered.connect(lambda chk, key=color.lower(): self.copy_text(key))
            getattr(self, f"{color.lower()}_key").addAction(copyAction, QLineEdit.TrailingPosition)
            self.layout().addWidget(QLabel(f'{color} Key'))
            self.layout().addWidget(getattr(self, f"{color.lower()}_key"))

    def copy_text(self, key):
        text = getattr(self, f"{key}_key").text()
        QApplication.clipboard().setText(text)

    def on_connect_clicked(self):
        server = self.server_input.text()
        token = self.token.text()
        if not server:
            QMessageBox.critical(self, 'Error', 'Server address is required')
            return
        if not is_valid_url(server):
            QMessageBox.critical(self, 'Error', 'Invalid server address')
            return

        try:
            black_key, white_key, viewer_key = connect(server, token)
            if black_key:
                self.black_key.setText(black_key)
                self.white_key.setText(white_key)
                self.viewer_key.setText(viewer_key)
            else:
                QMessageBox.critical(self, 'Error', 'Failed to connect to the server')
        except ValueError as e:
            QMessageBox.critical(self, 'Error', str(e))
            self.close()

    def on_close_clicked(self):
        self.close()


def restart_network_worker(window, server, role, key, fn):
    worker = window.network_worker
    if worker:
        worker.stop()
        worker.messageReceived.disconnect(window.handle_network_notification)
        worker.server = server
        worker.role = role
        worker.key = key
        worker.start()
        worker.messageReceived.connect(window.handle_network_notification)
        worker.messageReceived.connect(fn)
    else:
        window.network_worker = NetworkWorker(window, server=server, role=role, key=key)
        window.network_worker.start()
        window.network_worker.messageReceived.connect(window.handle_network_notification)
        window.network_worker.messageReceived.connect(fn)


class JoinGameDialog(QDialog):
    def __init__(self, parent=None):
        super(JoinGameDialog, self).__init__(parent)
        self.setWindowTitle('Join Game')

        layout = QVBoxLayout(self)

        self.server_input = QLineEdit(self)
        server = get_server()
        if server is not None:
            self.server_input.setText(server)
        else:
            self.server_input.setPlaceholderText("http://127.0.0.1:5000")
        layout.addWidget(QLabel('Server'))
        layout.addWidget(self.server_input)

        layout.addWidget(QLabel('Role'))
        self.role_select = QComboBox(self)
        self.role_select.addItem('Black')
        self.role_select.addItem('White')
        self.role_select.addItem('Viewer')
        layout.addWidget(self.role_select)

        layout.addWidget(QLabel('Key'))
        self.key_input = QLineEdit('')
        layout.addWidget(self.key_input)

        self.join_button = QPushButton('Join', self)
        self.join_button.clicked.connect(self.on_join_clicked)
        layout.addWidget(self.join_button)

        layout.addWidget(QLabel('Room status'))
        self.room_status = QLabel('Neither')  # room status can be 'Neither', 'Black', 'White', 'Both', or 'Canceled'
        layout.addWidget(self.room_status)

        self.ready_button = QPushButton('Ready', self)
        self.ready_button.setEnabled(False)
        self.ready_button.clicked.connect(self.on_ready_clicked)
        layout.addWidget(self.ready_button)

        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.on_cancel_clicked)
        layout.addWidget(self.cancel_button)

        self.setLayout(layout)
        self.window = parent
        self.api = self.window.api

    def on_join_clicked(self):
        server = self.server_input.text()
        if server:
            set_server(server)
        role = self.role_select.currentText().lower()
        key = self.key_input.text()

        def check_joined_status(event, data):
            if event == 'joined':
                joined_role = data.get('role')
                if joined_role == role:
                    self.window.controller.add_player(role, kind=HUMAN)
                else:
                    self.window.controller.add_player(role, kind=REMOTE)

                try:
                    time.sleep(5)
                    status = self.api.joined_status(server, key)
                    self.room_status.setText(status)
                    if status == 'Both':
                        self.ready_button.setEnabled(True)
                        self.window.status_bar.showMessage('Ready')
                        self.window.network_worker.messageReceived.disconnect(check_joined_status)
                    elif status == 'Canceled':
                        self.window.controller.reset()
                        self.window.status_bar.showMessage('Canceled')
                    self.update()
                except Exception as e:
                    self.room_status.setText('None')

        try:
            restart_network_worker(self.window, server, role, key, check_joined_status)
            self.window.controller.set_mode(NETWORK)
            self.window.controller.set_side(BLACK if role == 'black' else WHITE)
            time.sleep(2)
            self.api.join(server, role, key)

            self.cancel_button.setEnabled(True)
        except Exception as e:
            self.window.status_bar.showMessage(str(e))

    def on_ready_clicked(self):
        server = self.server_input.text()
        if server:
            set_server(server)
        role = self.role_select.currentText().lower()
        key = self.key_input.text()
        try:
            self.api.ready(server, role, key)
            self.cancel_button.setEnabled(False)
        except Exception as e:
            self.window.status_bar.showMessage(str(e))

        def check_ready_status(event, data):
            server = self.server_input.text()
            key = self.key_input.text()

            if event == 'ready':
                try:
                    both_ready = self.api.ready_status(server, key)
                    if both_ready:
                        self.window.network_worker.messageReceived.disconnect(check_ready_status)
                        self.window.controller.start()
                        self.window.status_bar.showMessage('Game started')
                        self.close()
                except Exception as e:
                    self.window.status_bar.showMessage(str(e))

        self.window.network_worker.messageReceived.connect(check_ready_status)

    def on_cancel_clicked(self):
        server = self.server_input.text()
        if server:
            set_server(server)
        role = self.role_select.currentText().lower()
        key = self.key_input.text()
        try:
            self.api.cancel(server, role, key)
        except Exception as e:
            self.window.status_bar.showMessage(str(e))
        self.close()
