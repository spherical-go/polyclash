import numpy as np
import pyvista as pv

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = 'model3d/snub_dodecahedron.vtk'
mesh = pv.read(model_path)
vertices = mesh.points

index = [
    [0, 2, 6, 12, 8],
    [1, 5, 11, 20, 15],
    [3, 10, 19, 24, 4],
    [7, 18, 28, 32, 9],
    [13, 23, 35, 39, 16],
    [14, 27, 36, 40, 17],
    [21, 31, 43, 48, 25],
    [22, 34, 44, 49, 26],
    [29, 30, 42, 52, 33],
    [37, 38, 51, 58, 41],
    [45, 46, 47, 57, 50],
    [53, 54, 55, 59, 56],
]

charges = np.array([
    [0, 1, 2, 3, 4], [1, 2, 3, 4, 0], [1, 2, 3, 4, 0], [1, 2, 3, 4, 0],
    [3, 4, 0, 1, 2], [1, 2, 3, 4, 0], [1, 2, 3, 4, 0], [4, 0, 1, 2, 3],
    [3, 4, 0, 1, 2], [3, 4, 0, 1, 2], [2, 3, 4, 0, 1], [3, 4, 0, 1, 2]
]).flatten()


indexes = np.array(index).flatten()
for i in range(60):
    print(f'{i} - {i in indexes}')

cities = []
for i in np.array(index).flatten():
    cities.append(vertices[i].tolist())
cities_array = np.array(cities, dtype=np.float_)
charges_array = np.array(charges, dtype=np.int_).flatten()

# Set up the PyVista plotter
# 设置 PyVista 绘图器
plotter = pv.Plotter(window_size=(3200, 2400))
plotter.set_background('white')

# Add the snub dodecahedron mesh and the cities to the plot
# 将扭棱十二面体网格和城市添加到绘图中
plotter.add_mesh(mesh, show_edges=True, color='lightblue')
plotter.add_point_labels(cities_array, charges_array, font_size=100, shape_opacity=0.0, render_points_as_spheres=True)

# Enhance the visualization with interactive axes
# 使用交互式坐标轴增强可视化
plotter.show_axes = True
plotter.add_axes(interactive=True)

# Display the visualization
# 显示可视化
plotter.show()


