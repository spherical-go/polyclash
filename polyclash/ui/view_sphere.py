import numpy as np
import pyvista as pv

from pyvistaqt import QtInteractor
from vtkmodules.vtkCommonCore import vtkCommand

from polyclash.ui.constants import stone_empty_color, stone_black_color, stone_white_color
from polyclash.ui.mesh import mesh, face_colors
from polyclash.board import BLACK, board
from polyclash.data import cities, city_manager, axis
from PyQt5.QtGui import QImage


hidden = None


def qimage(array):
    if array.ndim == 3:
        h, w, ch = array.shape
        if ch == 3:  # RGB
            format = QImage.Format_RGB888
        else:  # RGBA
            format = QImage.Format_RGBA8888
    else:
        raise ValueError("Unsupported array shape")

    array = np.ascontiguousarray(array)
    qim = QImage(array.data, w, h, array.strides[0], format)
    return qim


class ActiveSphereView(QtInteractor):
    def __init__(self, parent=None, status_bar=None, overlay_info=None, overlay_map=None):
        super().__init__(parent)
        self.picker = None
        self.spheres = {}
        self.initialize_interactor()
        self.status_bar = status_bar
        self.overlay_info = overlay_info
        self.overlay_map = overlay_map
        self.setup_scene()
        self.overlay_map.set_sphere_view(self)

    def initialize_interactor(self):
        self.show_axes = True
        self.add_axes(interactive=True)
        self.set_background("darkgray")

        self.add_mesh(mesh, show_edges=True, color="lightblue", pickable=False, scalars=face_colors, rgba=True)

        for idx, city in enumerate(cities):
            sphere = pv.Sphere(radius=0.03, center=city)
            actor = self.add_mesh(sphere, color=stone_empty_color, pickable=True)
            self.spheres[idx] = actor

        self.camera.position = 6 * axis[0]
        self.camera.focal_point = axis[0]
        self.camera.view_up = axis[1]

    def setup_scene(self):
        self.picker = self.interactor.GetRenderWindow().GetInteractor().CreateDefaultPicker()
        self.interactor.AddObserver(vtkCommand.LeftButtonPressEvent, self.left_button_press_event)

    def handle_notification(self, message, **kwargs):
        if message == "remove_stones":
            self.remove_stone(kwargs["point"])
        self.render()

    def remove_stone(self, point):
        actor = self.spheres[point]
        actor.GetProperty().SetColor(stone_empty_color[0], stone_empty_color[1], stone_empty_color[2])

    def left_button_press_event(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        picked_actor = self.picker.GetActor()
        if picked_actor:
            center = picked_actor.GetCenter()
            position = np.array([center[0], center[1], center[2]])

            nearest_city = city_manager.find_nearest_city(position)
            try:
                board.play(nearest_city, board.current_player)

                if board.current_player == BLACK:
                    picked_actor.GetProperty().SetColor(stone_black_color[0], stone_black_color[1], stone_black_color[2])
                else:
                    picked_actor.GetProperty().SetColor(stone_white_color[0], stone_white_color[1], stone_white_color[2])

                board.switch_player()

                self.update_maps_view()
            except ValueError as e:
                self.status_bar.showMessage(str(e))
        self.interactor.GetRenderWindow().Render()
        return

    def update_maps_view(self):
        img0 = get_hidden().capture_view(0, 6 * axis[0], axis[0], axis[1])
        self.overlay_map.set_image(0, 0, img0)
        img1 = get_hidden().capture_view(1, 6 * axis[1], axis[1], axis[2])
        self.overlay_map.set_image(1, 0, img1)
        img2 = get_hidden().capture_view(2, 6 * axis[2], axis[2], axis[3])
        self.overlay_map.set_image(2, 0, img2)
        img3 = get_hidden().capture_view(3, 6 * axis[3], axis[3], axis[0])
        self.overlay_map.set_image(3, 0, img3)
        img4 = get_hidden().capture_view(4, 6 * axis[4], axis[4], axis[5])
        self.overlay_map.set_image(0, 1, img4)
        img5 = get_hidden().capture_view(5, 6 * axis[5], axis[5], axis[6])
        self.overlay_map.set_image(1, 1, img5)
        img6 = get_hidden().capture_view(6, 6 * axis[6], axis[6], axis[7])
        self.overlay_map.set_image(2, 1, img6)
        img7 = get_hidden().capture_view(7, 6 * axis[7], axis[7], axis[4])
        self.overlay_map.set_image(3, 1, img7)

    def change_view(self, row, col):
        self.camera.position = 6 * axis[row + 4 * col]
        self.camera.focal_point = axis[row + 4 * col] * 0
        self.camera.view_up = axis[(row + 1) % 4 + 4 * col]
        self.update()


class PassiveSphereView(QtInteractor):
    def __init__(self):
        super().__init__(None, off_screen=True)
        self.spheres = {}
        self.initialize_interactor()

    def initialize_interactor(self):
        self.set_background("darkgray")
        self.add_mesh(mesh, show_edges=True, color="lightblue", pickable=False, scalars=face_colors, rgba=True)
        for idx, city in enumerate(cities):
            sphere = pv.Sphere(radius=0.02, center=city)
            actor = self.add_mesh(sphere, color=stone_empty_color, pickable=True)
            self.spheres[idx] = actor
        self.update()

    def handle_notification(self, message, **kwargs):
        if message == "add_stone":
            self.on_stone_added(kwargs["point"], kwargs["color"])
        if message == "remove_stones":
            self.on_stone_removed(kwargs["point"])
        self.render()

    def on_stone_added(self, point, color):
        actor = self.spheres[point]
        if color == BLACK:
            actor.GetProperty().SetColor(stone_black_color[0], stone_black_color[1], stone_black_color[2])
        else:
            actor.GetProperty().SetColor(stone_white_color[0], stone_white_color[1], stone_white_color[2])
        self.update()

    def on_stone_removed(self, point):
        actor = self.spheres[point]
        actor.GetProperty().SetColor(stone_empty_color[0], stone_empty_color[1], stone_empty_color[2])
        self.update()

    def capture_view(self, ix, camera_position, camera_focus, camera_up):
        self.camera.position = camera_position
        self.camera.focal_point = camera_focus
        self.camera.view_up = camera_up
        self.update()
        img = self.screenshot(transparent_background=True, scale=2, return_img=True)
        return qimage(img)


def get_hidden():
    global hidden
    if hidden is None:
        hidden = PassiveSphereView()
        board.register_observer(hidden)
    return hidden
