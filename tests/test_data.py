import unittest
import polyclash.data.data as data


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

    def test_indexer(self):
        indexer = data.indexer
        self.assertEqual(452, len(indexer), "The number of index should be 302.")
        self.assertFalse(set([i for i in range(302)]) - set(indexer.values()), "Each index should be in the indexer.")
        for i in range(60):
            self.assertEqual(i, indexer[tuple((i,))], "Each index should be in the indexer.")
        for i in range(15):
            j = (i + 1) % 15
            self.assertTrue((i, j) in indexer, "Each midpoint should be in the indexer.")
            self.assertTrue((15 + i, 15 + j) in indexer, "Each midpoint should be in the indexer.")
            self.assertTrue((30 + i, 30 + j) in indexer, "Each midpoint should be in the indexer.")
            self.assertTrue((45 + i, 45 + j) in indexer, "Each midpoint should be in the indexer.")

    def test_decoder(self):
        decoder = data.decoder
        self.assertEqual(660, len(decoder), "The number of decoder should be 302.")

    def test_encoder(self):
        encoder = data.encoder
        self.assertEqual(302, len(encoder), "The number of encoder should be 302.")
        self.assertEqual(302, len(set(encoder)), "Each code is a different code.")


if __name__ == '__main__':
    unittest.main()
