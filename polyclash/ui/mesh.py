import numpy as np
import pyvista as pv
import colorsys

from os import path as osp
from polyclash.data import triangles, pentagons, triangle2faces, pentagon2faces
from polyclash.ui.constants import group_colors, sea_color, city_color

model_path = osp.abspath(osp.join(osp.dirname(__file__), "board.vtk"))
mesh = pv.read(model_path)


def adjust_hue(rgb_color, adjustment_factor):
    hsv_color = colorsys.rgb_to_hsv(*rgb_color[:3])
    new_hue = (hsv_color[0] + adjustment_factor) % 1.0  # adjust hue, make sure the result is in [0, 1]
    adjusted_rgb = colorsys.hsv_to_rgb(new_hue, hsv_color[1], hsv_color[2])
    return adjusted_rgb + (rgb_color[3],)


def init_color():
    face_colors = np.ones((mesh.n_cells, 4))

    for i, triangle in enumerate(triangles):
        face = triangle
        groups = [vertex // 15 for vertex in face]
        # If all vertices are from the same group, color the face accordingly
        if len(set(groups)) == 1:
            for j in range(3):
                face_colors[triangle2faces[i][j]] = group_colors[groups[0]]
        else:
            # Default to sea color for mixed groups
            for j in range(3):
                face_colors[triangle2faces[i][j]] = sea_color

    for i, pentagon in enumerate(pentagons):
        face = pentagon
        groups = [vertex // 15 for vertex in face]
        # If all vertices are from the same group, color the face accordingly
        if len(set(groups)) == 1:
            for j in range(5):
                face_colors[pentagon2faces[i][j]] = group_colors[groups[0]]

    mesh.cell_data['colors'] = face_colors
    return face_colors


face_colors = init_color()
