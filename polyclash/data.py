import numpy as np
import pickle as pkl
import os.path as osp

from scipy.spatial import cKDTree

data_path = osp.abspath(osp.join(osp.dirname(__file__), "board.npz"))
pkl_path = osp.abspath(osp.join(osp.dirname(__file__), "board.pkl"))
idx_path = osp.abspath(osp.join(osp.dirname(__file__), "index.pkl"))

npz_data = np.load(data_path)
pentagons = npz_data['pentagons']
triangles = npz_data['triangles']

cities = npz_data['cities']
triangle2faces = npz_data['triangle2faces']
pentagon2faces = npz_data['pentagon2faces']

neighbors = pkl.load(open(pkl_path, "rb"))

indexer = pkl.load(open(idx_path, "rb"))

# encoding -> position
decoder = {}
for k, v in indexer.items():
    if len(k) == 1:
        decoder[(k, )] = v
    if len(k) == 2:
        decoder[tuple([k[0], k[1]])] = v
        decoder[tuple([k[1], k[0]])] = v
    if len(k) == 3:
        decoder[tuple([k[0], k[1], k[2]])] = v
        decoder[tuple([k[1], k[2], k[0]])] = v
        decoder[tuple([k[2], k[0], k[1]])] = v
    if len(k) == 5:
        decoder[tuple([k[0], k[1], k[2], k[3], k[4]])] = v
        decoder[tuple([k[1], k[2], k[3], k[4], k[0]])] = v
        decoder[tuple([k[2], k[3], k[4], k[0], k[1]])] = v
        decoder[tuple([k[3], k[4], k[0], k[1], k[2]])] = v
        decoder[tuple([k[4], k[0], k[1], k[2], k[3]])] = v

# position -> encoding
encoder = list([tuple() for i in range(302)])
for k, v in indexer.items():
    encoder[v] = tuple(sorted(k))


# Use a kdTree manage all the cities, when a stone is placed, find the nearest city
class CityManager:
    def __init__(self, cities):
        self.cities = cities
        self.kd_tree = cKDTree(self.cities)

    def find_nearest_city(self, position):
        return self.kd_tree.query(position)[1]


city_manager = CityManager(cities)


axis = np.zeros((8, 3), dtype=np.float_)
axis[0] = np.mean(cities[0:15], axis=0)
axis[1] = np.mean(cities[15:30], axis=0)
axis[2] = np.mean(cities[30:45], axis=0)
axis[3] = np.mean(cities[45:60], axis=0)
axis[4] = - axis[0]
axis[5] = - axis[1]
axis[6] = - axis[2]
axis[7] = - axis[3]
axis = axis / np.linalg.norm(axis, axis=1)[:, np.newaxis]
