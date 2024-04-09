import numpy as np
import pyvista as pv

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = 'model3d/snub_dodecahedron.vtk'
mesh = pv.read(model_path)
vertices = mesh.points

# Load additional data from an NPZ file
# 从 NPZ 文件加载额外数据
data_path = 'model3d/snub_dodecahedron.npz'
npz_data = np.load(data_path)
edges = npz_data['edges']
pentagons = npz_data['pentagons']
triangles = npz_data['triangles']

# Calculate the geometric centers ("cities") of vertices, edges, triangles, and pentagons
# 计算顶点、边、三角形和五边形的几何中心（“城市”）
cities = []

# Vertex cities
for vertex in vertices:
    cities.append(vertex.tolist())

# Edge cities
for edge in edges:
    cities.append(np.mean(vertices[list(edge)], axis=0).tolist())

# Triangle cities
for triangle in triangles:
    cities.append(np.mean(vertices[triangle], axis=0).tolist())

# Pentagon cities
for pentagon in pentagons:
    cities.append(np.mean(vertices[pentagon], axis=0).tolist())

cities_array = np.array(cities, dtype=np.float_)
np.savez('model3d/cities.npz', cities=cities_array)

# Set up the PyVista plotter
# 设置 PyVista 绘图器
plotter = pv.Plotter(window_size=(3200, 2400))
plotter.set_background('white')

# Add the snub dodecahedron mesh and the cities to the plot
# 将扭棱十二面体网格和城市添加到绘图中
plotter.add_mesh(mesh, show_edges=True, color='lightblue')
plotter.add_point_labels(cities_array[:60], range(60), font_size=100, shape_opacity=0.0, render_points_as_spheres=True)
plotter.add_points(cities_array[60:], point_size=10, render_points_as_spheres=True)

# Enhance the visualization with interactive axes
# 使用交互式坐标轴增强可视化
plotter.show_axes = True
plotter.add_axes(interactive=True)

# Display the visualization
# 显示可视化
plotter.show()
