import sys
import numpy as np
import pyvista as pv

from scipy.spatial import cKDTree

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QPainter, QColor, QBrush, QScreen

from pyvistaqt import QtInteractor
from vtkmodules.vtkCommonCore import vtkCommand

from board import Board


# Load the VTK format 3D model
model_path = 'model3d/snub_dodecahedron_new.vtk'
mesh = pv.read(model_path)

# Load additional data from a NPZ file
data_path = 'model3d/snub_dodecahedron_new.npz'
npz_data = np.load(data_path)
pentagons = npz_data['pentagons']
triangles = npz_data['triangles']

# Load the cities data
data_path = 'model3d/cities.npz'
npz_data = np.load(data_path)
cities = npz_data['cities']


# Define colors for different purposes
group_colors = {
    0: (0.85, 0.75, 0.60, 1.0),  # Warm earth tone
    1: (0.65, 0.85, 0.65, 1.0),  # Fresh green
    2: (0.75, 0.70, 0.50, 1.0),  # Sandy brown
    3: (0.65, 0.65, 0.60, 1.0),  # Rocky gray
}
sea_color = (0.3, 0.5, 0.7, 1.0)  # Ocean blue
city_color = (0.5, 0.5, 0.5, 1.0)  # City marker color
font_color = (0.2, 0.2, 0.2, 1.0)  # Text color


# Use a kdTree manage all the cities, when a stone is placed, find the nearest city
class CityManager:
    def __init__(self, cities):
        self.cities = cities
        self.kd_tree = cKDTree(self.cities)

    def find_nearest_city(self, position):
        return self.kd_tree.query(position)[1]


# Create a board and a city manager
board = Board()
city_manager = CityManager(cities)

overlay = None


# Pick event handling
class CustomInteractor(QtInteractor):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.picker = self.interactor.GetRenderWindow().GetInteractor().CreateDefaultPicker()
        self.interactor.AddObserver(vtkCommand.LeftButtonPressEvent, self.left_button_press_event)

    def left_button_press_event(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        picked_actor = self.picker.GetActor()
        if picked_actor:
            center = picked_actor.GetCenter()
            position = np.array([center[0], center[1], center[2]])
            nearest_city = city_manager.find_nearest_city(position)
            if board.current_player == "black":
                picked_actor.GetProperty().SetColor(0, 0, 0)
                if overlay:
                    overlay.change_color(Qt.white)
            else:
                picked_actor.GetProperty().SetColor(1, 1, 1)
                if overlay:
                    overlay.change_color(Qt.black)
            board.play(nearest_city)

        self.interactor.GetRenderWindow().Render()
        return


class Overlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.color = Qt.black  # set default color
        self.setAttribute(Qt.WA_TranslucentBackground)  # set transparent background

    def paintEvent(self, event):
        painter = QPainter(self)

        # set opacity
        painter.setOpacity(0.5)  # 50% transparent

        # 绘制半透明背景
        painter.setBrush(QBrush(QColor(192, 192, 192, 127)))  # 浅灰色，半透明
        painter.drawRect(self.rect())  # 覆盖整个Widget区域

        # 绘制小圆盘，不透明
        painter.setOpacity(1.0)  # 重置为不透明
        painter.setBrush(QBrush(self.color))
        painter.drawEllipse(10, 10, 50, 50)  # 绘制小圆盘

    def change_color(self, color):
        self.color = color
        self.update()  # 更新Widget，触发重绘


# Main window
class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        self.face_colors = None
        self.setWindowTitle("Polyclash")

        self.overlay = Overlay(self)
        self.overlay.setGeometry(700, 20, 210, 240)

        # 设置状态栏
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

        self.frame = QtWidgets.QFrame()
        self.layout = QtWidgets.QGridLayout()

        self.vtk_widget = CustomInteractor(self.frame)
        self.layout.addWidget(self.vtk_widget, 0, 0, 1, 2)

        self.frame.setLayout(self.layout)
        self.setCentralWidget(self.frame)

        self.init_color()
        self.init_pyvista(cities)
        self.update_overlay_position()
        self.overlay.raise_()

    def update_overlay_position(self):
        overlay_width = 210
        overlay_height = 240
        self.overlay.setGeometry(self.width() - overlay_width - 20, 20, overlay_width, overlay_height)

    def resizeEvent(self, event):
        self.update_overlay_position()
        super().resizeEvent(event)

    def init_color(self):

        # Initialize the color array for all faces
        face_colors = np.zeros((mesh.n_cells, 4))

        # Apply colors to each face based on its vertices
        for i in range(mesh.n_cells):
            if i < len(triangles):
                face = triangles[i]
            else:
                face = pentagons[i - len(triangles)]

            groups = [vertex // 15 for vertex in face]
            # If all vertices are from the same group, color the face accordingly
            if len(set(groups)) == 1:
                face_colors[i] = group_colors[groups[0]]
            else:
                # Default to sea color for mixed groups
                face_colors[i] = sea_color

        # Set the color data to the mesh object
        mesh.cell_data['colors'] = face_colors
        self.face_colors = face_colors

    def init_pyvista(self, cities=None):
        self.vtk_widget.set_background("darkgray")
        self.vtk_widget.add_mesh(mesh, color="lightblue", pickable=False, scalars=self.face_colors, rgba=True)
        self.vtk_widget.add_point_labels(cities[:60], range(60), point_color=city_color, point_size=10,
                                 render_points_as_spheres=True, text_color=font_color, font_size=100, shape_opacity=0.0)

        cities = npz_data['cities'][:60]
        for city in cities:
            self.vtk_widget.show_axes = True
            self.vtk_widget.add_axes(interactive=True)
            sphere = pv.Sphere(radius=0.02, center=city)
            self.vtk_widget.add_mesh(sphere, color=city_color, pickable=True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1600, 1200)
    overlay = window.overlay

    screen = app.primaryScreen().geometry()
    x = (screen.width() - window.width()) / 2
    y = (screen.height() - window.height()) / 2
    window.move(int(x), int(y))

    window.show()
    sys.exit(app.exec_())

