import numpy as np
import pickle as pkl
import os.path as osp

from scipy.spatial import cKDTree


data_path = osp.abspath(osp.join(osp.dirname(__file__), "board.npz"))
pkl_path = osp.abspath(osp.join(osp.dirname(__file__), "board.pkl"))

npz_data = np.load(data_path)
pentagons = npz_data['pentagons']
triangles = npz_data['triangles']

cities = npz_data['cities']
triangle2faces = npz_data['triangle2faces']
pentagon2faces = npz_data['pentagon2faces']

neighbors = pkl.load(open(pkl_path, "rb"))


# Use a kdTree manage all the cities, when a stone is placed, find the nearest city
class CityManager:
    def __init__(self, cities):
        self.cities = cities
        self.kd_tree = cKDTree(self.cities)

    def find_nearest_city(self, position):
        return self.kd_tree.query(position)[1]


city_manager = CityManager(cities)

