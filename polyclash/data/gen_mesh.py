"""
Generate and Visualize a Snub Dodecahedron Mesh

This script calculates the vertices of a snub dodecahedron using specific rotational
transformations and the golden ratio. It then identifies unique vertices, generates
edges, and identifies both triangles and pentagons within the structure. After simplifying
the graph by removing edges that do not contribute to the unique geometric structure of
the snub dodecahedron. The final visualization is done using PyVista through the mesh.

Features:
- Uses the golden ratio and rotational matrices to generate the snub dodecahedron's vertices.
- Employs KDTree for efficient duplicate vertex removal based on a specified tolerance.
- Identifies triangles and pentagons, simplifying the graph to highlight the snub dodecahedron's unique geometry.
- Visualizes the mesh with PyVista, focusing on the geometrical uniqueness of the snub dodecahedron.

References:
- Snub Dodecahedron on Wikipedia: https://en.wikipedia.org/wiki/Snub_dodecahedron

Requirements:
- numpy for calculations and vertex management.
- networkx for graph-based operations including triangle and pentagon identification.
- pyvista for 3D visualization of the mesh.
- scipy, specifically cKDTree, for duplicate vertex removal.

Note: The code aims for educational purposes to illustrate the process of generating and visualizing complex
geometrical structures.

Author：Mingli Yuan with the help of ChatGPT
"""

"""
生成和可视化扭棱十二面体网格

本脚本使用特定的旋转变换和黄金比率计算扭棱十二面体的顶点。然后，它识别唯一的顶点，生成边，并识别结构中的三角形和五边形。
通过移除不贡献于扭棱十二面体独特几何结构的边来简化图形。最终使用 PyVista 进行可视化。

特点：
- 使用黄金比率和旋转矩阵生成扭棱十二面体顶点。
- 基于指定容差使用KDTree高效地移除重复顶点。
- 识别三角形和五边形，简化图形以突出扭棱十二面体的独特几何结构。
- 使用PyVista进行3D可视化，着重展示扭棱十二面体的几何独特性。

参考资料：
- 扭棱十二面体维基百科：https://en.wikipedia.org/wiki/Snub_dodecahedron

需要的库：
- numpy用于计算和顶点管理。
- networkx用于包括三角形和五边形识别在内的基于图的操作。
- pyvista用于网格的3D可视化。
- scipy，特别是cKDTree，用于重复顶点的移除。

注意：该代码旨在用于教育目的，以说明生成和可视化复杂几何结构的过程。

作者：苑明理，由 ChatGPT 提供帮助
"""


# import necessary libraries
# 导入必要的库

import numpy as np
import networkx as nx
import pyvista as pv

from scipy.spatial import cKDTree
from collections import Counter

# Set the precision of the output
# 设置 numpy 的输出精度，以便于查看和调试
np.set_printoptions(precision=8, floatmode='fixed', sign='+')

# Specify a tolerance for considering points as duplicates
# 定义用于判断点重复的容差阈值
tolerance = 1e-6

# Calculate the golden ratio
# 计算黄金比例 φ
phi = (1 + np.sqrt(5)) / 2

# Solve the polynomial equation to get the value of ξ
# 求解多项式方程获取 ξ 的值
coefficients = np.array([1, 2, 0, -phi**2], dtype=np.float64)
roots = np.roots(coefficients)
xi = roots[np.isreal(roots)].real[0]

# Calculate the starting vertex p based on ξ and φ
# 根据 ξ 和 φ 计算起始顶点 p
p = np.array([phi**2 * (1 - xi), -phi**3 + phi * xi + 2 * phi * xi**2, xi], dtype=np.float64)

# Define the two transformations S and T
# 定义旋转变换矩阵S和T
S = np.array([
    [0, 0, 1.0],
    [1.0, 0, 0],
    [0, 1.0, 0],
], dtype=np.float64)
T = np.array([
    [1 / (2 * phi), -phi / 2, 1 / 2],
    [phi / 2, 1 / 2, 1 / (2 * phi)],
    [-1 / 2, 1 / (2 * phi), phi / 2],
], dtype=np.float64)

# Initialize the list of vertices and apply the transformations iteratively
# 初始化顶点列表，并迭代应用变换
vertices = [p]
while True:
    g = [np.dot(t, v) for v in vertices for t in [S, T]]

    # Filter out the points that are already in the vertices
    # 过滤掉已存在的顶点
    new_vertices = [u for u in g if not np.any([np.all(np.isclose(v, u, atol=tolerance)) for v in vertices])]

    if not new_vertices:
        break
    vertices.extend(new_vertices)

# Remove duplicate vertices using a KDTree
# 使用 KDTree 移除重复的顶点
vertices_array = np.array(vertices, dtype=np.float64)
kdtree = cKDTree(vertices_array)
indices_to_remove = []

for i, vertex in enumerate(vertices_array):
    if i not in indices_to_remove:
        indices = kdtree.query_ball_point(vertex, r=tolerance)
        indices.remove(i)
        indices_to_remove.extend(indices)

vertices_array = np.delete(vertices_array, list(set(indices_to_remove)), axis=0)

# Ensure that the number of vertices is correct
# 确保顶点数量正确
print(f"Number of vertices: {len(vertices_array)}")
assert len(vertices_array) == 60, "The number of vertices should be 60."

# Create edges based on the nearest 5 points
# 根据最近的五个点创建边
edges = []
for i, v in enumerate(vertices_array):
    # Calculate distances from the current vertex to all others
    distances = np.linalg.norm(vertices_array - v, axis=1)
    # Find indices of the five nearest vertices, excluding the current one
    nearest_indices = np.argsort(distances)[1:6]  # Skip the first one (self)
    # Create edges from the current vertex to the five nearest ones
    for index in nearest_indices:
        edges.append([i, index])

print(f"Number of directed edges: {len(edges)}")
assert len(edges) == 300, "The number of vertices should be 300."

# Create a graph to identify triangles
# 创建图，用于识别三角形
G = nx.Graph()
G.add_edges_from(edges)

# Identify triangles
# 识别三角形
triangles = [list(triangle) for triangle in nx.enumerate_all_cliques(G) if len(triangle) == 3]

print(f"Number of triangle faces: {len(triangles)}")
assert len(triangles) == 80, "The number of vertices should be 80."

# Remove edges that appear twice in a triangle
# 移除在三角形中出现两次的边
edge_counts = Counter()
for triangle in triangles:
    edge_counts.update([(triangle[i], triangle[(i + 1) % 3]) for i in range(3)] + [(triangle[(i + 1) % 3], triangle[i])
                                                                                   for i in range(3)])
edges_to_remove = [edge for edge, count in edge_counts.items() if count == 2]
G.remove_edges_from(edges_to_remove)

# Identify pentagons
# 识别五边形
pentagons = [cycle for cycle in nx.simple_cycles(nx.Graph(G)) if len(cycle) == 5]

print(f"Number of pentagon faces: {len(pentagons)}")
assert len(pentagons) == 12, "The number of vertices should be 12."

# Create the mesh
# 准备用于 PyVista 的面数据
faces_list = [[3] + triangle for triangle in triangles] + [[5] + pentagon for pentagon in pentagons]
poly_data = pv.PolyData(vertices_array, np.hstack(faces_list))

# Save the model as a VTK file
# 保存模型为 VTK 文件
poly_data.save("model3d/snub_dodecahedron.vtk")
np.savez('model3d/snub_dodecahedron.npz',
         vertices=vertices_array,
         edges=np.array(G.edges, dtype=np.int_),
         triangles=np.array(triangles, dtype=np.int_),
         pentagons=np.array(pentagons, dtype=np.int_),
         )

print("Data saved!")

print("Visualizing...")

# Visualize the mesh
# 可视化
plotter = pv.Plotter()
plotter.add_mesh(poly_data, show_edges=True, color='lightblue')
plotter.show()

print("Bye!")
