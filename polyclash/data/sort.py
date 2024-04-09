import numpy as np
import pyvista as pv

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = 'model3d/snub_dodecahedron.vtk'
mesh = pv.read(model_path)
vertices = mesh.points

cities = []
for vertex in vertices:
    cities.append(vertex.tolist())

index = [
    [0, 2, 6, 12, 8],      # _rr
    [35, 23, 13, 16, 39],  # rll
    [14, 27, 36, 40, 17],  # rrr
    [39, 35, 23, 13, 16],  # rll
    [47, 57, 50, 45, 46],  # rrr
    [44, 34, 22, 26, 49],  # rll
    [45, 46, 47, 57, 50],  # Lrr
    [56, 59, 55, 54, 53],  # rll
    [58, 41, 37, 36, 51],  # Lrr
    [29, 33, 52, 42, 30],  # rll
    [32, 9, 7, 18, 28],    # rrl
    [4, 24, 19, 10, 3],    # rr_
]

charges = [
    [0, 1, 2, 3, 4],
    [3, 4, 0, 1, 2],
    [0, 1, 2, 3, 4],
    [1, 2, 3, 4, 0],
    [0, 1, 2, 3, 4],
    [2, 3, 4, 0, 1],
    [0, 1, 2, 3, 4],
    [1, 2, 3, 4, 0],
    [2, 3, 4, 0, 1],
    [0, 1, 2, 3, 4],
    [3, 4, 0, 1, 2],
    [1, 2, 3, 4, 0]
]

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


