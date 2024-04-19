import os.path as osp

from PyQt5.QtWidgets import QApplication, QDialog, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QAction, QVBoxLayout
from PyQt5.QtGui import QIcon

from polyclash.api import get_server, connect


png_copy_path = osp.abspath(osp.join(osp.dirname(__file__), "copy.png"))


class StartGameDialog(QDialog):
    def __init__(self, parent=None):
        super(StartGameDialog, self).__init__(parent)
        self.setWindowTitle('Start Game')

        layout = QVBoxLayout(self)

        self.server_input = QLineEdit(self)
        server = get_server()
        if server is not None:
            self.server_input.setText(server)
        else:
            self.server_input.setPlaceholderText("http://127.0.0.1:5000")
        layout.addWidget(QLabel('Server'))
        layout.addWidget(self.server_input)

        self.token_input = QLineEdit(self)
        self.token_input.setPlaceholderText('')
        layout.addWidget(QLabel('Token'))
        layout.addWidget(self.token_input)

        self.connect_button = QPushButton('Connect', self)
        self.connect_button.clicked.connect(self.on_connect_clicked)
        layout.addWidget(self.connect_button)

        layout.addWidget(QLabel('Black Key'))
        self.black_key = QLineEdit('')
        self.black_key.setReadOnly(True)
        copyBlackAction = QAction(QIcon(png_copy_path), 'copyBlack', self)
        copyBlackAction.triggered.connect(self.copyBlackText)
        self.black_key.addAction(copyBlackAction, QLineEdit.TrailingPosition)
        layout.addWidget(self.black_key)

        layout.addWidget(QLabel('White Key'))
        self.white_key = QLineEdit('')
        self.white_key.setReadOnly(True)
        copyWhiteAction = QAction(QIcon(png_copy_path), 'copyWhite', self)
        copyWhiteAction.triggered.connect(self.copyWhiteText)
        self.white_key.addAction(copyWhiteAction, QLineEdit.TrailingPosition)
        layout.addWidget(self.white_key)

        layout.addWidget(QLabel('Audience Key'))
        self.audience_key = QLineEdit('')
        self.audience_key.setReadOnly(True)
        copyAudienceAction = QAction(QIcon(png_copy_path), 'copyAudience', self)
        copyAudienceAction.triggered.connect(self.copyAudienceText)
        self.audience_key.addAction(copyAudienceAction, QLineEdit.TrailingPosition)
        layout.addWidget(self.audience_key)

        self.close_button = QPushButton('Close', self)
        self.close_button.clicked.connect(self.on_close_clicked)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def copyBlackText(self):
        text = self.black_key.text()
        QApplication.clipboard().setText(text)

    def copyWhiteText(self):
        text = self.white_key.text()
        QApplication.clipboard().setText(text)

    def copyAudienceText(self):
        text = self.audience_key.text()
        QApplication.clipboard().setText(text)

    def on_connect_clicked(self):
        server = self.server_input.text()
        token = self.token_input.text()
        black_key, white_key, audience_key = connect(server, token)
        if black_key is not None:
            self.black_key.setText(black_key)
            self.white_key.setText(white_key)
            self.audience_key.setText(audience_key)
        else:
            QMessageBox.critical(self, 'Error', 'Failed to connect to the server')

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
        self.role_select.addItem('Audience')
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

        from polyclash.ui.workers.network import NetworkWorker
        self.window.network_worker = NetworkWorker(self.window, server=server, role=role, key=key)
        self.window.network_worker.start()

        self.close()

