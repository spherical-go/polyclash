import numpy as np
import pyvista as pv
import colorsys

from polyclash.data.data import triangles, pentagons, triangle2faces, pentagon2faces, cities, polysmalls, polylarges
from polyclash.gui.constants import face_continent_colors, face_oceanic_color


faces_list = [[4] + list(small) for small in polysmalls] + [[4] + list(large) for large in polylarges]
mesh = pv.PolyData(cities, np.hstack(faces_list))


def adjust_hue(rgb_color, adjustment_factor):
    hsv_color = colorsys.rgb_to_hsv(*rgb_color[:3])
    new_hue = (hsv_color[0] + adjustment_factor) % 1.0  # adjust hue, make sure the result is in [0, 1]
    adjusted_rgb = colorsys.hsv_to_rgb(new_hue, hsv_color[1], hsv_color[2])
    return adjusted_rgb + (rgb_color[3],)


def init_colors():
    colors = np.ones((mesh.n_cells, 4))

    for i, triangle in enumerate(triangles):
        face = triangle
        groups = [vertex // 15 for vertex in face]
        # If all vertices are from the same group, color the face accordingly
        if len(set(groups)) == 1:
            for j in range(3):
                colors[triangle2faces[i][j]] = face_continent_colors[groups[0]]
        else:
            # Default to sea color for mixed groups
            for j in range(3):
                colors[triangle2faces[i][j]] = face_oceanic_color

    for i, pentagon in enumerate(pentagons):
        face = pentagon
        groups = [vertex // 15 for vertex in face]
        # If all vertices are from the same group, color the face accordingly
        if len(set(groups)) == 1:
            for j in range(5):
                colors[pentagon2faces[i][j]] = face_continent_colors[groups[0]]

    mesh.cell_data['colors'] = colors
    return colors


face_colors = init_colors()
