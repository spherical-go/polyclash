import pyvista as pv
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow, QAction, QMessageBox, qApp

from polyclash.ui.overly_map import OverlayMap
from polyclash.ui.overly_info import OverlayInfo
from polyclash.ui.view_sphere import ActiveSphereView, get_hidden


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.face_colors = None
        self.spheres = {}
        self.setWindowTitle("Polyclash")

        self.init_menu()

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

        self.update_overlay_position()
        self.overlay_info.raise_()
        self.overlay_map.raise_()

        get_hidden()

    def init_menu(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('File')
        exitAction = QAction('Exit', self)
        exitAction.triggered.connect(qApp.quit)
        fileMenu.addAction(exitAction)

        gameMenu = menubar.addMenu('Game')
        newGameAction = QAction('New', self)
        newGameAction.triggered.connect(self.newGame)
        gameMenu.addAction(newGameAction)

        endGameAction = QAction('End', self)
        endGameAction.triggered.connect(self.endGame)
        gameMenu.addAction(endGameAction)

        helpMenu = menubar.addMenu('Help')
        aboutAction = QAction('About', self)
        aboutAction.triggered.connect(self.about)
        helpMenu.addAction(aboutAction)

    def newGame(self):
        print("Start New Game...")

    def endGame(self):
        print("End Game...")

    def about(self):
        QMessageBox.about(self, "About", "PolyClash\nv0.1\nA spherical Go")

    def update_overlay_position(self):
        overlay_width = self.width() // 6
        overlay_height = self.width() // 6
        self.overlay_info.setGeometry(self.margin, self.margin, overlay_width, overlay_height)
        overlay_width = self.width() // 4
        overlay_height = self.height() - 4 * self.margin
        self.overlay_map.setGeometry(self.width() - overlay_width - self.margin, self.margin, overlay_width, overlay_height)

    def resizeEvent(self, event):
        self.update_overlay_position()
        super().resizeEvent(event)
