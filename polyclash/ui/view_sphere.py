import numpy as np
import pyvista as pv
import polyclash.api as api

from pyvistaqt import QtInteractor
from vtkmodules.vtkCommonCore import vtkCommand
from PyQt5.QtGui import QImage

from polyclash.ui.constants import stone_empty_color, stone_black_color, stone_white_color
from polyclash.ui.mesh import mesh, face_colors
from polyclash.board import BLACK, board
from polyclash.data import cities, city_manager, axis, encoder

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


class SphereView(QtInteractor):
    def __init__(self, parent=None, off_screen=False):
        super().__init__(parent, off_screen=off_screen)
        self.spheres = {}
        self.initialize_interactor()

    def initialize_interactor(self):
        self.set_background("darkgray")
        self.add_mesh(mesh, show_edges=True, color="lightblue", pickable=False, scalars=face_colors, rgba=True)
        for idx, city in enumerate(cities):
            sphere = pv.Sphere(radius=0.03, center=city)
            actor = self.add_mesh(sphere, color=stone_empty_color, pickable=True)
            self.spheres[idx] = actor

    def handle_notification(self, message, **kwargs):
        if message == "add_stone":
            self.on_stone_added(kwargs["point"], kwargs["player"])
        if message == "remove_stone":
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


class ActiveSphereView(SphereView):
    def __init__(self, parent=None, status_bar=None, overlay_info=None, overlay_map=None):
        super().__init__(parent)
        self.picker = None
        self.cyclic_pad = 1
        self.status_bar = status_bar
        self.overlay_info = overlay_info
        self.overlay_map = overlay_map
        self.overlay_map.set_sphere_view(self)

        self.show_axes = True
        self.add_axes(interactive=True)
        self.camera.position = 6 * axis[0]
        self.camera.focal_point = np.zeros((3,))
        self.camera.view_up = axis[self.cyclic_pad]

        self.setup_scene()

    def setup_scene(self):
        self.picker = self.interactor.GetRenderWindow().GetInteractor().CreateDefaultPicker()
        self.interactor.AddObserver(vtkCommand.LeftButtonPressEvent, self.left_button_press_event)

    def update(self):
        super().update()
        if self.isActiveWindow():
            self.update_maps_view()
            self.overlay_info.update()

    def left_button_press_event(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        self.picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

        picked_actor = self.picker.GetActor()
        if picked_actor:
            center = picked_actor.GetCenter()
            position = np.array([center[0], center[1], center[2]])
            target_city = city_manager.find_nearest_city(position)
            if target_city is not None:
                try:
                    board.play(target_city, board.current_player)
                    api.play(board.counter, encoder[target_city])
                    board.switch_player()
                    # board.autoplay(board.current_player)
                    # board.switch_player()
                except ValueError as e:
                    self.status_bar.showMessage(str(e))
        return

    def update_maps_view(self):
        for row in range(self.overlay_map.rows):
            for col in range(self.overlay_map.columns):
                img = get_hidden().capture_view(6 * axis[row + self.overlay_map.rows * col], np.zeros((3,)),
                                                axis[(row + self.cyclic_pad) % self.overlay_map.rows + self.overlay_map.rows * col])
                self.overlay_map.set_image(row, col, img)

    def change_view(self, row, col):
        self.camera.position = 6 * axis[row + self.overlay_map.rows * col]
        self.camera.focal_point = np.zeros((3,))
        self.camera.view_up = axis[(row + self.cyclic_pad) % self.overlay_map.rows + self.overlay_map.rows * col]
        self.update()


class PassiveSphereView(SphereView):
    def __init__(self):
        super().__init__(None, off_screen=True)

    def capture_view(self, camera_position, camera_focus, camera_up):
        self.camera.position = camera_position
        self.camera.focal_point = camera_focus * 0
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
