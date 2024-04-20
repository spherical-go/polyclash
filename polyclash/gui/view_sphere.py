import numpy as np
import pyvista as pv

from pyvistaqt import QtInteractor
from vtkmodules.vtkCommonCore import vtkCommand
from PyQt5.QtGui import QImage

from polyclash.gui.constants import stone_empty_color, stone_black_color, stone_white_color
from polyclash.gui.mesh import mesh, face_colors
from polyclash.game.board import BLACK
from polyclash.data.data import cities, city_manager, axis

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
        self.cyclic_pad = 1
        self.initialize_interactor()

    def initialize_interactor(self):
        self.set_background("darkgray")
        self.add_mesh(mesh, show_edges=True, color="lightblue", pickable=False, scalars=face_colors, rgba=True)
        for idx, city in enumerate(cities):
            sphere = pv.Sphere(radius=0.03, center=city)
            actor = self.add_mesh(sphere, color=stone_empty_color, pickable=True)
            self.spheres[idx] = actor

    def handle_notification(self, message, **kwargs):
        if message == "reset":
            self.on_reset()
        if message == "add_stone":
            self.on_stone_added(kwargs["point"], kwargs["player"])
        if message == "remove_stone":
            self.on_stone_removed(kwargs["point"])
        self.render()

    def on_reset(self):
        for actor in self.spheres:
            actor.GetProperty().SetColor(stone_empty_color[0], stone_empty_color[1], stone_empty_color[2])
        self.update()

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

    def change_view(self, row, col):
        print(row, col)
        self.camera.position = 6 * axis[row + 4 * col]
        self.camera.focal_point = np.zeros((3,))
        self.camera.view_up = axis[(row + self.cyclic_pad) % 4 + 4 * col]
        print(self.camera.position, self.camera.focal_point, self.camera.view_up)
        self.reset_camera()
        self.render()


class ActiveSphereView(SphereView):
    def __init__(self, parent=None, controller=None, status_bar=None, overlay_info=None, overlay_map=None):
        super().__init__(parent)
        self.controller = controller
        self.picker = None
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

    def update(self, **kwargs):
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
                    self.controller.play(self.controller.board.current_player, target_city)
                except ValueError as e:
                    self.status_bar.showMessage(str(e))
        return

    def update_maps_view(self):
        hidden = get_hidden(self.controller)
        for col in range(self.overlay_map.columns):
            for row in range(self.overlay_map.rows):
                hidden.change_view(row, col)
                image = hidden.capture_view()
                print(hidden.camera.position, hidden.camera.focal_point, hidden.camera.view_up)
                self.overlay_map.set_image(row, col, image)


class PassiveSphereView(SphereView):
    def __init__(self):
        super().__init__(None, off_screen=True)

    def capture_view(self):
        img = self.screenshot(transparent_background=True, return_img=True, window_size=(256, 256))
        return qimage(img)


def get_hidden(controller=None):
    global hidden
    if hidden is None:
        hidden = PassiveSphereView()
        if controller:
            controller.board.register_observer(hidden)
    return hidden
