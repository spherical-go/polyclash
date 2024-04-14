import pyvista as pv
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow

from polyclash.ui.overly_map import OverlayMap
from polyclash.ui.overly_info import OverlayInfo
from polyclash.ui.view_sphere import ActiveSphereView, get_hidden


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.face_colors = None
        self.spheres = {}
        self.setWindowTitle("Polyclash")

        self.overlay_info = OverlayInfo(self)
        self.overlay_info.setGeometry(20, 20, 210, 240)  # x, y, width, height

        self.overlay_map = OverlayMap(self)
        self.overlay_map.setGeometry(700, 20, 600, 1200)  # x, y, width, height

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

    def update_overlay_position(self):
        overlay_width = 210
        overlay_height = 240
        self.overlay_info.setGeometry(20, 20, overlay_width, overlay_height)
        overlay_width = 550
        overlay_height = 1100
        self.overlay_map.setGeometry(self.width() - overlay_width - 20, 20, overlay_width, overlay_height)

    def resizeEvent(self, event):
        self.update_overlay_position()
        super().resizeEvent(event)
