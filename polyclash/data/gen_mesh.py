import numpy as np
import networkx as nx
import pyvista as pv

from scipy.spatial import cKDTree
from collections import Counter


# Set the precision of the output
np.set_printoptions(precision=8, floatmode='fixed', sign='+')

# Specify a tolerance for considering points as duplicates
tolerance = 1e-5


# Calculate the golden ratio
phi = (1 + np.sqrt(5)) / 2
coefficients = [1, 2, 0, -phi**2]
roots = np.roots(coefficients)
xi = roots[np.isreal(roots)].real[0]
p = np.array([phi**2 * (1 - xi), -phi**3 + phi*xi + 2 * phi * xi**2, xi])

S = np.array([
    [0, 0, 1],
    [1, 0, 0],
    [0, 1, 0],
])
T = np.array([
    [1/(2*phi), -phi/2, 1/2],
    [phi/2, 1/2, 1/(2*phi)],
    [-1/2, 1/(2*phi), phi/2],
])

vertices = [p]

# interpret the transformations
while True:
    print(len(vertices))

    g = [np.dot(t, v) for v in vertices for t in [S, T]]

    # filter out the point is already in the vertices
    new_vertices = []
    for u in g:
        if not np.any([np.all(np.isclose(v, u, rtol=1e-3)) for v in vertices]):
            new_vertices.append(u)

    if len(new_vertices) == 0:
        break
    vertices.extend(new_vertices)


# After generating new vertices
vertices_array = np.array(vertices)
kdtree = cKDTree(vertices_array)

# List to hold indices of vertices to remove (duplicates)
indices_to_remove = []
for i, vertex in enumerate(vertices_array):
    # Query the tree for all points within the tolerance
    if i not in indices_to_remove:
        # This returns indices of all points within 'tolerance' of 'vertex'
        indices = kdtree.query_ball_point(vertex, r=tolerance)
        # Remove the vertex's own index
        indices.remove(i)
        # Add these indices to the removal list
        indices_to_remove.extend(indices)

# Remove duplicates
vertices_array = np.delete(vertices_array, indices_to_remove, axis=0)
vertices_array = np.array(vertices_array)


# find nearest 5 points
for i, v in enumerate(vertices_array):
    dist = np.linalg.norm(vertices_array - v, axis=1)
    idx = np.argsort(dist)
    for j in range(6):
        print(f'{i} - {j}: {dist[idx[j]]} - {idx[j]}')

# Create the edges
edges = []
for i, v in enumerate(vertices_array):
    dist = np.linalg.norm(vertices_array - v, axis=1)
    idx = np.argsort(dist)
    for j in range(1, 6):
        edges.append([i, idx[j]])

print(len(edges))


# Create a graph from the edges of your mesh
G = nx.Graph()
G.add_edges_from(edges)  # Add your mesh's edges here

# Find 3-loops (triangles)
triangles = [list(triangle) for triangle in nx.enumerate_all_cliques(G) if len(triangle) == 3]
print("Triangles (3-loops):", triangles)
print("Number of triangles:", len(triangles))

print("Number of edges before removing:", len(G.edges()))
edge_counts = Counter()
for triangle in triangles:
    triangle_edges = [(triangle[i], triangle[(i + 1) % 3]) for i in range(3)]
    edge_counts.update(triangle_edges)
    triangle_edges = [(triangle[(i + 1) % 3], triangle[i]) for i in range(3)]
    edge_counts.update(triangle_edges)
edges_to_remove = [edge for edge, count in edge_counts.items() if count == 2]
print("Number of edges to remove:", len(edges_to_remove))
G.remove_edges_from(edges_to_remove)
print("Number of edges after removing:", len(G.edges()))

five_loops = []
for cycle in nx.simple_cycles(nx.Graph(G)):
    if len(cycle) == 5:
        five_loops.append(cycle)

print("Pentagons (5-loops):", five_loops)
print("Number of pentagons:", len(five_loops))

# Find independent triangles
independent_triangles = []
for triangle in triangles:
    independent = True
    for i in range(3):
        edge1 = (triangle[i], triangle[(i + 1) % 3])
        edge2 = (triangle[(i + 1) % 3], triangle[i])
        independent = independent and (edge_counts[edge1] == 2 or edge_counts[edge2] == 2)
    if independent:
        independent_triangles.append(triangle)
print("Independent triangles:", independent_triangles)
print("Number of independent triangles:", len(independent_triangles))

# Create the mesh
print("Creating mesh...")
# Correct format for faces in PyVista
faces_list = []
for triangle in triangles:
    faces_list.extend([3] + triangle)  # For triangles
for pentagon in five_loops:
    faces_list.extend([5] + pentagon)  # Directly for pentagons, if supported
faces_array = np.array(faces_list, dtype=np.int_)

# Create a PolyData object
poly_data = pv.PolyData(vertices_array, faces_array)

# Save the model as a VTK file
poly_data.save("model3d/snub_dodecahedron.vtk")
np.savez('model3d/snub_dodecahedron.npz',
         independent_triangles=np.array(independent_triangles, dtype=np.int_),
         triangles=np.array(triangles, dtype=np.int_),
         pentagons=np.array(five_loops, dtype=np.int_),
)

# Plot the mesh
plotter = pv.Plotter()
plotter.add_mesh(poly_data, show_edges=True, color='lightblue')
plotter.show()





