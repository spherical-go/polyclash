import pyvista as pv
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QMainWindow

from polyclash.ui.overly_info import OverlayInfo
from polyclash.ui.view_sphere import SphereView


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.face_colors = None
        self.spheres = {}
        self.setWindowTitle("Polyclash")

        self.overlay_info = OverlayInfo(self)
        self.overlay_info.setGeometry(700, 20, 210, 240)

        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QGridLayout()

        self.sphere_view = SphereView(self.frame)
        self.layout.addWidget(self.sphere_view, 0, 0, 1, 2)

        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.update_overlay_position()
        self.overlay_info.raise_()

    def update_overlay_position(self):
        overlay_width = 210
        overlay_height = 240
        self.overlay_info.setGeometry(self.width() - overlay_width - 20, 20, overlay_width, overlay_height)

    def resizeEvent(self, event):
        self.update_overlay_position()
        super().resizeEvent(event)
