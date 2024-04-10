import numpy as np

from itertools import product


data_path = 'model3d/snub_dodecahedron.npz'
npz_data = np.load(data_path)
vertices = npz_data['vertices']
pentagons = np.array([
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


left_or_right = {
    1: [
        np.array((0, 1, 2, 3, 4), dtype=np.int_), np.array((1, 2, 3, 4, 0), dtype=np.int_),
        np.array((2, 3, 4, 0, 1), dtype=np.int_), np.array((3, 4, 0, 1, 2), dtype=np.int_),
        np.array((4, 0, 1, 2, 3), dtype=np.int_)
    ],
    -1: [
        np.array((4, 3, 2, 1, 0), dtype=np.int_), np.array((3, 2, 1, 0, 4), dtype=np.int_),
        np.array((2, 1, 0, 4, 3), dtype=np.int_), np.array((1, 0, 4, 3, 2), dtype=np.int_),
        np.array((0, 4, 3, 2, 1), dtype=np.int_)
    ]
}


def gen_balanced_cases():
    return [[left_or_right[face] for face in case] for case in product([-1, 1], repeat=12) if np.sum(case) == 0]


all_balanced = gen_balanced_cases()
num_of_balanced = len(all_balanced)
total_combinations = 5**12 * num_of_balanced


def potential_energy(charges):
    interaction_matrix = relationship_matrix[charges[:, None], charges]
    energy_matrix = interaction_matrix / distsq_matrix
    np.fill_diagonal(energy_matrix, 0)
    total_energy = np.sum(energy_matrix)
    return total_energy


min_energy = np.inf
optimal_charges = None

counter = 0
charges = np.zeros((60,), dtype=np.int_)
for balanced in all_balanced:
    for case in product(*balanced):
        counter += 1
        if counter % 10000 == 0:
            percentage = counter / total_combinations * 100
            print(f"Progress: {percentage:.4f}% - Minimum energy: {min_energy}")
            if percentage > 20:
                break

        charges[0:5] = case[0]
        charges[5:10] = case[1]
        charges[10:15] = case[2]
        charges[15:20] = case[3]
        charges[20:25] = case[4]
        charges[25:30] = case[5]
        charges[30:35] = case[6]
        charges[35:40] = case[7]
        charges[40:45] = case[8]
        charges[45:50] = case[9]
        charges[50:55] = case[10]
        charges[55:60] = case[11]

        energy = potential_energy(charges)
        if energy < min_energy:
            min_energy = energy
            optimal_charges = charges

print("Optimal charges:", optimal_charges)
print("Minimum potential energy:", min_energy)
