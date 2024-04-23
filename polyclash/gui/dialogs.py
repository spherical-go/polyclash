import os.path as osp

from urllib.parse import urlparse

from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QAction, \
    QVBoxLayout
from PyQt5.QtGui import QIcon

from polyclash.api.api import get_server, connect
from polyclash.game.board import BLACK, WHITE
from polyclash.game.controller import LOCAL

png_copy_path = osp.abspath(osp.join(osp.dirname(__file__), "copy.png"))


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
        self.server_input.setPlaceholderText("http://127.0.0.1:5000")
        layout.addWidget(QLabel('Server'))
        layout.addWidget(self.server_input)

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

    def manage_keys(self):
        # Adds widgets for Black, White, and Viewer keys
        for color in ["Black", "White", "Viewer"]:
            setattr(self, f"{color.lower()}_key", QLineEdit(''))
            getattr(self, f"{color.lower()}_key").setReadOnly(True)
            copyAction = QAction(QIcon(png_copy_path), f'copy{color}', self)
            copyAction.triggered.connect(lambda chk, key=color.lower(): self.copy_text(key))
            getattr(self, f"{color.lower()}_key").addAction(copyAction, QLineEdit.TrailingPosition)
            self.layout().addWidget(QLabel(f'{color} Key'))
            self.layout().addWidget(getattr(self, f"{color.lower()}_key"))

    def copy_text(self, key):
        text = getattr(self, f"{key}_key").text()
        QApplication.clipboard().setText(text)

    def on_connect_clicked(self):
        server = self.server_input.text()
        if not server:
            QMessageBox.critical(self, 'Error', 'Server address is required')
            return
        if not is_valid_url(server):
            QMessageBox.critical(self, 'Error', 'Invalid server address')
            return

        try:
            black_key, white_key, viewer_key = connect(server, None)
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

        self.setLayout(layout)
        self.window = parent

    def on_join_clicked(self):
        server = self.server_input.text()
        role = self.role_select.currentText().lower()
        key = self.key_input.text()

        from polyclash.workers.network import NetworkWorker
        self.window.network_worker = NetworkWorker(self.window, server=server, role=role, key=key)
        self.window.network_worker.start()

        self.close()
