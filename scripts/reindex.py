import numpy as np
import pyvista as pv

data_path = 'model3d/snub_dodecahedron.npz'
data = np.load(data_path)
vertices = data['vertices']
edges = data['edges']
triangles = data['triangles']
pentagons = data['pentagons']

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

mapper = {indexer[i]: i for i in range(60)}

# re-index the vertices
vertices_new = []
for i in indexer:
    vertices_new.append(vertices[i].tolist())
vertices_array = np.array(vertices_new, dtype=np.float_)

# re-index the edges
edges_new = []
for edge in edges:
    edges_new.append(list(sorted([mapper[edge[0]], mapper[edge[1]]])))
edges_array = np.array(edges_new, dtype=np.int_)

# re-index the triangles
triangles_new = []
for triangle in triangles:
    triangles_new.append(list(sorted([mapper[triangle[0]], mapper[triangle[1]], mapper[triangle[2]]])))

# re-index the pentagons
pentagons_new = [
    [0, 1, 2, 3, 4],
    [5, 6, 7, 8, 9],
    [10, 11, 12, 13, 14],
    [15, 16, 17, 18, 19],
    [20, 21, 22, 23, 24],
    [25, 26, 27, 28, 29],
    [30, 31, 32, 33, 34],
    [35, 36, 37, 38, 39],
    [40, 41, 42, 43, 44],
    [45, 46, 47, 48, 49],
    [50, 51, 52, 53, 54],
    [55, 56, 57, 58, 59],
]

# Create the mesh
# 准备用于 PyVista 的面数据
faces_list = [[3] + triangle for triangle in triangles_new] + [[5] + pentagon for pentagon in pentagons_new]
poly_data = pv.PolyData(vertices_array, np.hstack(faces_list))

# Save the model as a VTK file
# 保存模型为 VTK 文件
poly_data.save("model3d/snub_dodecahedron_new.vtk")
np.savez('model3d/snub_dodecahedron_new.npz',
         vertices=vertices_array,
         edges=np.array(edges_array, dtype=np.int_),
         triangles=np.array(triangles_new, dtype=np.int_),
         pentagons=np.array(pentagons_new, dtype=np.int_),
         )

print("Data saved!")

print("Visualizing...")

# Visualize the mesh
# 可视化
plotter = pv.Plotter()
plotter.add_mesh(poly_data, show_edges=True, color='lightblue')
plotter.show()

print("Bye!")
