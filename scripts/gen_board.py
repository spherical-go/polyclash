import numpy as np
import pyvista as pv
import pickle as pkl

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = 'model3d/snub_dodecahedron_new.vtk'
mesh = pv.read(model_path)
vertices = mesh.points

# Load additional data from a NPZ file
# 从 NPZ 文件加载额外数据
data_path = 'model3d/snub_dodecahedron_new.npz'
npz_data = np.load(data_path)
edges = npz_data['edges']
pentagons = npz_data['pentagons']
triangles = npz_data['triangles']

# Load cities data from a NPZ file
# 从 NPZ 文件加载城市数据
cities_path = 'model3d/cities.npz'
cities_data = np.load(cities_path)
cities = cities_data['cities']


# build index to cities
# 建立城市索引
index = {}
for i in range(60):  # 60 vertices of the snub dodecahedron
    index[(i,)] = i
for i in range(150):  # 150 edges of the snub dodecahedron
    index[tuple(edges[i])] = i + 60
    index[tuple(reversed(edges[i]))] = i + 60
for i in range(80):  # 80 triangles of the snub dodecahedron
    index[tuple(triangles[i])] = i + 210
for i in range(12):  # 12 pentagons of the snub dodecahedron
    index[tuple(pentagons[i])] = i + 290


# Define the neighbors table
# 定义邻居表
neighbors = {}
for v1, v2 in edges:
    edg = index[tuple([v1, v2])]
    if v1 not in neighbors:
        neighbors[v1] = set()
    neighbors[v1].add(edg)
    if v2 not in neighbors:
        neighbors[v2] = set()
    neighbors[v2].add(edg)
    if edg not in neighbors:
        neighbors[edg] = set()
    neighbors[edg].add(v1)
    neighbors[edg].add(v2)


# Define the small polygons
# 定义小四边形
polysmalls = []
triangle2faces = []
for i, triangle in enumerate(triangles):
    center = index[tuple(triangle)]
    vertex0 = index[tuple([triangle[0]])]
    vertex1 = index[tuple([triangle[1]])]
    vertex2 = index[tuple([triangle[2]])]
    edge0 = index[tuple([vertex0, vertex1])]
    edge1 = index[tuple([vertex1, vertex2])]
    edge2 = index[tuple([vertex2, vertex0])]
    polysmalls.append([center, edge0, vertex1, edge1])
    polysmalls.append([center, edge1, vertex2, edge2])
    polysmalls.append([center, edge2, vertex0, edge0])
    triangle2faces.append([3 * i, 3 * i + 1, 3 * i + 2])
    neighbors[center] = {edge0, edge1, edge2}
    if edge0 not in neighbors:
        neighbors[edge0] = set()
    neighbors[edge0].add(center)
    if edge1 not in neighbors:
        neighbors[edge1] = set()
    neighbors[edge1].add(center)
    if edge2 not in neighbors:
        neighbors[edge2] = set()
    neighbors[edge2].add(center)


# Define the large polygons
# 定义大四边形
polylarges = []
pentagon2faces = []
for i, pentagon in enumerate(pentagons):
    center = index[tuple(pentagon)]
    vertex0 = index[tuple([pentagon[0]])]
    vertex1 = index[tuple([pentagon[1]])]
    vertex2 = index[tuple([pentagon[2]])]
    vertex3 = index[tuple([pentagon[3]])]
    vertex4 = index[tuple([pentagon[4]])]
    edge0 = index[tuple([vertex0, vertex1])]
    edge1 = index[tuple([vertex1, vertex2])]
    edge2 = index[tuple([vertex2, vertex3])]
    edge3 = index[tuple([vertex3, vertex4])]
    edge4 = index[tuple([vertex4, vertex0])]
    polylarges.append([center, edge0, vertex1, edge1])
    polylarges.append([center, edge1, vertex2, edge2])
    polylarges.append([center, edge2, vertex3, edge3])
    polylarges.append([center, edge3, vertex4, edge4])
    polylarges.append([center, edge4, vertex0, edge0])
    start = 3 * len(triangle2faces)
    pentagon2faces.append([
        start + 5 * i, start + 5 * i + 1,
        start + 5 * i + 2, start + 5 * i + 3,
        start + 5 * i + 4
    ])
    neighbors[center] = {edge0, edge1, edge2, edge3, edge4}
    if edge0 not in neighbors:
        neighbors[edge0] = set()
    neighbors[edge0].add(center)
    if edge1 not in neighbors:
        neighbors[edge1] = set()
    neighbors[edge1].add(center)
    if edge2 not in neighbors:
        neighbors[edge2] = set()
    neighbors[edge2].add(center)
    if edge3 not in neighbors:
        neighbors[edge3] = set()
    neighbors[edge3].add(center)
    if edge4 not in neighbors:
        neighbors[edge4] = set()
    neighbors[edge4].add(center)


assert len(vertices) == 60
assert len(edges) == 150
assert len(triangles) == 80
assert len(pentagons) == 12
assert len(cities) == 302
assert len(polysmalls) == 240
assert len(polylarges) == 60
assert len(triangle2faces) == 80
assert len(pentagon2faces) == 12
assert len(neighbors) == 302

for i in range(302):
    assert neighbors[i] is not None and len(neighbors[i]) > 0

# Create the mesh
# 创建网格
faces_list = [[4] + small for small in polysmalls] + [[4] + large for large in polylarges]
poly_data = pv.PolyData(cities, np.hstack(faces_list))

# Save the model as a VTK file
# 保存模型为 VTK 文件
poly_data.save("model3d/board.vtk")
np.savez('model3d/board.npz',
         vertices=vertices,
         edges=edges,
         triangles=triangles,
         pentagons=pentagons,
         cities=cities,
         polysmalls=np.array(polysmalls, dtype=np.int_),
         polylarges=np.array(polylarges, dtype=np.int_),
         triangle2faces=np.array(triangle2faces, dtype=np.int_),
         pentagon2faces=np.array(pentagon2faces, dtype=np.int_),
         )
pkl.dump(neighbors, open('model3d/board.pkl', 'wb'))
pkl.dump(index, open('model3d/index.pkl', 'wb'))


print("Data saved!")

print("Visualizing...")

# Visualize the mesh
# 可视化
plotter = pv.Plotter()
plotter.add_mesh(poly_data, show_edges=True, color='lightblue')
plotter.show()

print("Bye!")
