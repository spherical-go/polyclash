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
pentagons = npz_data['pentagons']

relationship_matrix = np.array([
    [3, -1, 1, 1, 1],
    [1, 3, -1, 1, 1],
    [1, 1, 3, -1, 1],
    [1, 1, 1, 3, -1],
    [-1, 1, 1, 1, 3],
])


def potential_energy(vertices, charges):
    energy = 0
    for i in range(12):
        p1 = pentagons[i]
        group1 = charges[i]
        for j in range(5):
            k = i * 5 + j
            v1 = vertices[p1[j]]
            charge1 = group1[j]
            for m in range(12):
                p2 = pentagons[m]
                group2 = charges[m]
                for n in range(5):
                    l = m * 5 + n
                    v2 = vertices[p2[n]]
                    charge2 = group2[n]
                    if k != l:
                        dist = np.linalg.norm(v1 - v2)
                        rel = relationship_matrix[charge1, charge2]
                        energy += rel / (dist**2)  # Energy calculation
    return energy


min_energy = np.inf
optimal_charges = None


single_face_permutations = [
    np.array((0, 1, 2, 3, 4), dtype=np.int_), np.array((1, 2, 3, 4, 0), dtype=np.int_),
    np.array((2, 3, 4, 0, 1), dtype=np.int_), np.array((3, 4, 0, 1, 2), dtype=np.int_),
    np.array((4, 0, 1, 2, 3), dtype=np.int_)
]

counter = 0
for charges in product(single_face_permutations, repeat=12):
    energy = potential_energy(vertices, charges)
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

