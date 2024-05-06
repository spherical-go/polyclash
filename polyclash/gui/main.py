from PyQt5.QtCore import QTimer

import polyclash.util.api as api
import polyclash.game.board as board

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, qApp, QMenu

from polyclash.data.data import decoder
from polyclash.game.player import HUMAN, REMOTE
from polyclash.gui.dialogs import NetworkGameDialog, JoinGameDialog, LocalGameDialog
from polyclash.gui.overly_map import OverlayMap
from polyclash.gui.overly_info import OverlayInfo
from polyclash.gui.view_sphere import ActiveSphereView
from polyclash.util.logging import logger


class MainWindow(QMainWindow):
    def __init__(self, parent=None, controller=None):
        super(MainWindow, self).__init__(parent)
        self.controller = controller
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

        self.sphere_view = ActiveSphereView(self.frame, controller, self.status_bar, self.overlay_info, self.overlay_map)
        self.layout.addWidget(self.sphere_view, 0, 0, 1, 2)

        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.controller.board.register_observer(self.sphere_view)
        self.controller.board.register_observer(self.overlay_info)

        self.updateOverlayPosition()
        self.overlay_info.raise_()
        self.overlay_map.raise_()

        self.api = api

    def initMenu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        gameMenu = menubar.addMenu('Game')

        localModeAction = QAction('Local mode', self)
        localModeAction.triggered.connect(self.localMode)
        gameMenu.addAction(localModeAction)

        networkMenu = QMenu('Network mode', self)
        gameMenu.addMenu(networkMenu)

        newGameAction = QAction('New', self)
        newGameAction.triggered.connect(self.newGame)
        networkMenu.addAction(newGameAction)

        joinGameAction = QAction('Join', self)
        joinGameAction.triggered.connect(self.joinGame)
        networkMenu.addAction(joinGameAction)

        endGameAction = QAction('End game', self)
        endGameAction.triggered.connect(self.endGame)
        gameMenu.addAction(endGameAction)

        helpMenu = menubar.addMenu('Help')
        aboutAction = QAction('About', self)
        aboutAction.triggered.connect(self.about)
        helpMenu.addAction(aboutAction)

    def update(self):
        self.sphere_view.update()
        self.sphere_view.update_maps_view()
        self.overlay_info.update()

    def handle_network_notification(self, event, data):
        logger.info(f'Event {event}: {str(data)}')
        if event == 'error':
            self.status_bar.showMessage(f"Error: {data['message']}")
            return

        if event == 'joined':
            self.status_bar.showMessage(f"{data['role'].capitalize()} player joined...")

            role = board.BLACK if data['role'] == 'black' else board.WHITE
            if role == self.controller.side:
                self.controller.add_player(role, kind=HUMAN, token=data['token'])
                api.player_token = data['token']
            else:
                self.controller.add_player(role, kind=REMOTE)
            return

        if event == 'ready':
            self.status_bar.showMessage(f"{data['role'].capitalize()} player is ready...")
            return

        if event == 'start':
            self.status_bar.showMessage("Game has started.")
            self.controller.start()
            return

        if event == 'played':
            self.status_bar.showMessage(f"{data['role'].capitalize()} player played...")
            role = board.BLACK if data['role'] == 'black' else board.WHITE
            if data['steps'] == self.controller.board.counter:
                if role != self.controller.side:
                    self.controller.play(role, decoder[tuple(data['play'])])

    def localMode(self):
        dialog = LocalGameDialog(self)
        dialog.exec_()

    def newGame(self):
        dialog = NetworkGameDialog(self)
        dialog.exec_()

    def joinGame(self):
        dialog = JoinGameDialog(self)
        dialog.exec_()

    def endGame(self):
        print("End Game...")

    def about(self):
        QMessageBox.about(self, "About", "PolyClash\nv0.1\nA spherical Go by using snub dodecahedron\nMingli Yuan")

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
            api.close(api.get_server())
        except Exception as e:
            print(f"Error: {str(e)}")
        if self.network_worker:
            self.network_worker.stop()
        if self.ai_worker:
            self.ai_worker.stop()
        event.accept()

    def delayed_resize(self, width, height):

        def resize_window():
            self.resize(width, height)
            self.update()

        # QTimer to delay the resizing
        QTimer.singleShot(1, resize_window)  # 1000 milliseconds = 1 seconds
