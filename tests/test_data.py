import unittest
import polyclash.data as data


class TestData(unittest.TestCase):
    def test_cities(self):
        cities = data.cities
        self.assertEqual(cities.shape, (302, 3), "The shape of cities should be (302, 3).")

    def test_pentagons(self):
        pentagons = data.pentagons
        self.assertEqual(len(pentagons), 12, "The number of pentagons should be 12.")

    def test_triangles(self):
        triangles = data.triangles
        self.assertEqual(len(triangles), 80, "The number of triangles should be 80.")

    def test_neighbors(self):
        neighbors = data.neighbors
        self.assertEqual(len(neighbors), 302, "The number of neighbors should be 302.")
        for i in range(302):
            self.assertTrue(neighbors[i] is not None and len(neighbors[i]) > 0, "Each neighbor should not be empty.")

    def test_triangle2faces(self):
        triangle2faces = data.triangle2faces
        self.assertEqual(len(triangle2faces), 80, "The number of triangle faces should be 80.")

    def test_pentagon2faces(self):
        pentagon2faces = data.pentagon2faces
        self.assertEqual(len(pentagon2faces), 12, "The number of pentagon faces should be 12.")


if __name__ == '__main__':
    unittest.main()
