import numpy as np
import pyvista as pv

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = 'model3d/snub_dodecahedron.vtk'
mesh = pv.read(model_path)
vertices = mesh.points

indexer = np.array([
    [5, 1, 15, 20, 11],
    [2, 0, 8, 12, 6],
    [3, 4, 24, 19, 10],

    [25, 21, 31, 43, 48],
    [26, 22, 34, 44, 49],
    [59, 56, 53, 54, 55],

    [17, 40, 36, 27, 14],
    [35, 23, 13, 16, 39],
    [47, 46, 45, 50, 57],

    [32, 9, 7, 18, 28],
    [30, 42, 52, 33, 29],
    [58, 41, 37, 38, 51]

]).flatten()

labels = np.array(np.arange(60), dtype=np.int_)

cities = []
for i in indexer:
    cities.append(vertices[i].tolist())
cities_array = np.array(cities, dtype=np.float_)

# Set up the PyVista plotter
# 设置 PyVista 绘图器
plotter = pv.Plotter(window_size=(3200, 2400))
plotter.set_background('white')

# Add the snub dodecahedron mesh and the cities to the plot
# 将扭棱十二面体网格和城市添加到绘图中
plotter.add_mesh(mesh, show_edges=True, color='lightblue')
plotter.add_point_labels(cities_array, labels, font_size=100, shape_opacity=0.0, render_points_as_spheres=True)

# Enhance the visualization with interactive axes
# 使用交互式坐标轴增强可视化
plotter.show_axes = True
plotter.add_axes(interactive=True)

# Display the visualization
# 显示可视化
plotter.show()




