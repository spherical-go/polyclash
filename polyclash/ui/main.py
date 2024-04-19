import json
import polyclash.api as api
import polyclash.board as board

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, qApp

from polyclash.ui.dialogs import StartGameDialog, JoinGameDialog
from polyclash.ui.overly_map import OverlayMap
from polyclash.ui.overly_info import OverlayInfo
from polyclash.ui.view_sphere import ActiveSphereView, get_hidden


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.face_colors = None
        self.spheres = {}
        self.setWindowTitle("Polyclash")

        self.network_worker = None
        self.ai_worker = None

        self.initMenu()

        self.margin = 20
        self.overlay_info = OverlayInfo(self)
        self.overlay_info.setGeometry(self.margin, self.margin, self.width() // 6, self.width() // 6)  # x, y, width, height

        self.overlay_map = OverlayMap(self)
        self.overlay_map.setGeometry(self.width() // 4 * 3 - self.margin, self.margin, self.width() // 4, self.height() - 4 * self.margin)  # x, y, width, height

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QGridLayout()

        self.sphere_view = ActiveSphereView(self.frame, self.status_bar, self.overlay_info, self.overlay_map)
        self.layout.addWidget(self.sphere_view, 0, 0, 1, 2)

        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.updateOverlayPosition()
        self.overlay_info.raise_()
        self.overlay_map.raise_()

        get_hidden()

    def initMenu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        gameMenu = menubar.addMenu('Game')
        newGameAction = QAction('New', self)
        newGameAction.triggered.connect(self.newGame)
        gameMenu.addAction(newGameAction)

        joinGameAction = QAction('Join', self)
        joinGameAction.triggered.connect(self.joinGame)
        gameMenu.addAction(joinGameAction)

        endGameAction = QAction('End', self)
        endGameAction.triggered.connect(self.endGame)
        gameMenu.addAction(endGameAction)

        helpMenu = menubar.addMenu('Help')
        aboutAction = QAction('About', self)
        aboutAction.triggered.connect(self.about)
        helpMenu.addAction(aboutAction)

    def handleNotification(self, message):
        data = json.loads(message)
        event = data['event']

        if event == 'error':
            self.status_bar.showMessage(f"Error: {data['message']}")
            return
        if event == 'joined':
            api.player_token = data['player']
            self.status_bar.showMessage(f"{data['role'].capitalize()} player joined...")
            return
        if event == 'played':
            self.status_bar.showMessage(f"{data['role'].capitalize()} player played...")
            current_role = 'black' if board.board.current_player == board.BLACK else 'white'
            if data['role'] != current_role:
                board.play(data['play'], board.board.current_player)
            return

        self.status_bar.showMessage(f"Unknown event...")

    def newGame(self):
        dialog = StartGameDialog(self)
        dialog.exec_()

    def joinGame(self):
        dialog = JoinGameDialog(self)
        dialog.exec_()

    def endGame(self):
        print("End Game...")

    def about(self):
        QMessageBox.about(self, "About", "PolyClash\nv0.1\nA spherical Go")

    def updateOverlayPosition(self):
        overlay_width = self.width() // 6
        overlay_height = self.width() // 6
        self.overlay_info.setGeometry(self.margin, self.margin, overlay_width, overlay_height)
        overlay_width = self.width() // 4
        overlay_height = self.height() - 4 * self.margin
        self.overlay_map.setGeometry(self.width() - overlay_width - self.margin, self.margin, overlay_width, overlay_height)

    def resizeEvent(self, event):
        self.updateOverlayPosition()
        super().resizeEvent(event)

    def closeEvent(self, event):
        try:
            api.close_game()
        except Exception as e:
            print(f"Error: {str(e)}")
        if self.network_worker:
            self.network_worker.stop()
        if self.ai_worker:
            self.ai_worker.stop()
        event.accept()
