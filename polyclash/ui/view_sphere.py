import numpy as np
import pyvista as pv

from PyQt5.QtCore import Qt
from pyvistaqt import QtInteractor
from vtkmodules.vtkCommonCore import vtkCommand

from polyclash.ui.constants import stone_empty_color, stone_black_color, stone_white_color
from polyclash.ui.mesh import mesh, face_colors
from polyclash.board import BLACK, board
from polyclash.data import cities, city_manager


class SphereView(QtInteractor):
    def __init__(self, parent=None, status_bar=None):
        super().__init__(parent)
        self.status_bar = status_bar
        self.picker = self.interactor.GetRenderWindow().GetInteractor().CreateDefaultPicker()
        self.interactor.AddObserver(vtkCommand.LeftButtonPressEvent, self.left_button_press_event)
        self.spheres = {}
        self.init_pyvista()

    def init_pyvista(self):
        self.set_background("darkgray")
        self.add_mesh(mesh, show_edges=True, color="lightblue", pickable=False, scalars=face_colors, rgba=True)
        # self.add_point_labels(cities[:60], range(60), point_color=city_color, point_size=10,
        #                         render_points_as_spheres=True, text_color=font_color, font_size=80, shape_opacity=0.0)

        for idx, city in enumerate(cities):
            self.show_axes = True
            self.add_axes(interactive=True)
            sphere = pv.Sphere(radius=0.02, center=city)
            actor = self.add_mesh(sphere, color=stone_empty_color, pickable=True)
            self.spheres[idx] = actor

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
            except ValueError as e:
                self.status_bar.showMessage(str(e))
        self.interactor.GetRenderWindow().Render()
        return
