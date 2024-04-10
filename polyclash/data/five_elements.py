import numpy as np
import pyvista as pv

from itertools import product, permutations

# Load the snub dodecahedron model from a VTK file
# 从 VTK 文件加载扭棱十二面体模型
model_path = 'model3d/snub_dodecahedron.vtk'
mesh = pv.read(model_path)
vertices = np.array(mesh.points)

data_path = 'model3d/snub_dodecahedron.npz'
npz_data = np.load(data_path)
pentagons = np.array([
    [0, 2, 6, 12, 8],
    [35, 23, 13, 16, 39],
    [14, 27, 36, 40, 17],
    [1, 5, 11, 20, 15],
    [47, 57, 50, 45, 46],
    [44, 34, 22, 26, 49],
    [21, 25, 48, 43, 31],
    [56, 59, 55, 54, 53],
    [58, 41, 37, 38, 51],
    [29, 33, 52, 42, 30],
    [32, 9, 7, 18, 28],
    [4, 24, 19, 10, 3],
], dtype=np.int_)

relationship_matrix = np.array([
   [2, -1, 1, 1, -1],
   [-1, 2, -1, 1, 1],
   [1, -1, 2, -1, 1],
   [1, 1, -1, 2, -1],
   [-1, 1, 1, -1, 2],
], dtype=np.int_)  # symmetrical


pentagons = pentagons.flatten()
distsq_matrix = np.zeros((60, 60))
for i in range(60):
    for j in range(i+1, 60):  # Only fill upper triangle
        dist = np.linalg.norm(vertices[pentagons[i]] - vertices[pentagons[j]])
        distsq_matrix[i, j] = dist * dist
        distsq_matrix[j, i] = dist * dist
np.fill_diagonal(distsq_matrix, 1)


def potential_energy(charges):
    interaction_matrix = relationship_matrix[charges[:, None], charges]
    energy_matrix = interaction_matrix / distsq_matrix
    np.fill_diagonal(energy_matrix, 0)
    total_energy = np.sum(energy_matrix)
    return total_energy


min_energy = np.inf
optimal_charges = None

single_face_permutations = [
    np.array((0, 1, 2, 3, 4), dtype=np.int_), np.array((1, 2, 3, 4, 0), dtype=np.int_),
    np.array((2, 3, 4, 0, 1), dtype=np.int_), np.array((3, 4, 0, 1, 2), dtype=np.int_),
    np.array((4, 0, 1, 2, 3), dtype=np.int_)
]

counter = 0
for charges in product(single_face_permutations, repeat=12):
    energy = potential_energy(np.stack(charges).flatten())
    if energy < min_energy:
        min_energy = energy
        optimal_charges = charges
    counter += 1
    if counter % 100 == 0:
        # give the percentage of completion
        percentage = counter / 5**12 * 100
        print(f"Progress: {percentage:.2f}% - Minimum energy: {min_energy} - Counter: {counter} - Energy: {energy}")

print("Optimal charges:", optimal_charges)
print("Minimum potential energy:", min_energy)
