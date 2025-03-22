import pytest
import numpy as np
from polyclash.data.data import (
    neighbors, encoder, decoder, cities, polysmalls, polylarges, city_manager,
    pentagons, triangles, triangle2faces, pentagon2faces, indexer, axis,
    CityManager, get_areas, polysmall_area, polylarge_area, total_area
)

class TestDataStructures:
    def test_neighbors_structure(self):
        """Test the structure and content of the neighbors dictionary."""
        # Check that neighbors is a dictionary with the correct structure
        assert isinstance(neighbors, dict)
        assert len(neighbors) == 302  # Should have entries for all vertices, edges, faces
        
        # Check a few specific entries
        assert 0 in neighbors
        assert len(neighbors[0]) == 5  # Vertex 0 should have 5 neighbors
        assert 96 in neighbors[0]  # Vertex 0 should be connected to vertex 96
        
        # Check symmetry of neighbor relationships
        for vertex, neighbor_set in neighbors.items():
            for neighbor in neighbor_set:
                assert vertex in neighbors[neighbor], f"Neighbor relationship not symmetric: {vertex} -> {neighbor}"

    def test_encoder_decoder_consistency(self):
        """Test that encoder and decoder are consistent with each other."""
        # Test encoder structure
        assert len(encoder) == 302
        assert all(isinstance(item, tuple) for item in encoder)
        
        # Test decoder structure
        assert isinstance(decoder, dict)
        
        # Test encoder/decoder consistency for vertices (single-element tuples)
        for i in range(60):  # Vertices are 0-59
            assert len(encoder[i]) == 1
            assert decoder[tuple([encoder[i][0]])] == i
            
        # Test encoder/decoder consistency for edges (two-element tuples)
        for i in range(60, 210):  # Edges are 60-209
            assert len(encoder[i]) == 2
            # Test both orderings of the edge
            edge = encoder[i]
            assert decoder[edge] == i
            assert decoder[tuple(reversed(edge))] == i
            
        # Test encoder/decoder consistency for triangular faces (three-element tuples)
        for i in range(210, 290):  # Triangular faces are 210-289
            assert len(encoder[i]) == 3
            # Test all rotations of the face
            face = encoder[i]
            assert decoder[face] == i
            assert decoder[tuple([face[1], face[2], face[0]])] == i
            assert decoder[tuple([face[2], face[0], face[1]])] == i
            
        # Test encoder/decoder consistency for pentagonal faces (five-element tuples)
        for i in range(290, 302):  # Pentagonal faces are 290-301
            assert len(encoder[i]) == 5
            # Test all rotations of the face
            face = encoder[i]
            assert decoder[face] == i
            assert decoder[tuple([face[1], face[2], face[3], face[4], face[0]])] == i
            assert decoder[tuple([face[2], face[3], face[4], face[0], face[1]])] == i
            assert decoder[tuple([face[3], face[4], face[0], face[1], face[2]])] == i
            assert decoder[tuple([face[4], face[0], face[1], face[2], face[3]])] == i

    def test_indexer_structure(self):
        """Test the structure and content of the indexer dictionary."""
        assert isinstance(indexer, dict)
        assert len(indexer) > 0
        
        # Check that all keys are tuples
        assert all(isinstance(k, tuple) for k in indexer.keys())
        
        # Check that all values are integers
        assert all(isinstance(v, int) for v in indexer.values())
        
        # Check a few specific entries
        assert indexer[(0,)] == 0
        assert indexer[(1,)] == 1
        assert indexer[(0, 1)] == 84 or indexer[(1, 0)] == 84  # Edge between vertices 0 and 1

    def test_cities_structure(self):
        """Test the structure and properties of the cities array."""
        # Check that cities is a numpy array with the correct shape
        assert isinstance(cities, np.ndarray)
        assert cities.shape[1] == 3  # Each city should have 3 coordinates (x, y, z)
        assert cities.shape[0] > 0  # There should be at least one city
        
        # Check that all cities are approximately on the unit sphere
        norms = np.linalg.norm(cities, axis=1)
        assert np.min(norms) >= 0.89, f"Minimum norm {np.min(norms)} is too small"
        assert np.max(norms) <= 1.1, f"Maximum norm {np.max(norms)} is too large"

    def test_poly_structures(self):
        """Test the structure and content of the polysmalls and polylarges arrays."""
        # Check that polysmalls and polylarges are numpy arrays
        assert isinstance(polysmalls, np.ndarray)
        assert isinstance(polylarges, np.ndarray)
        
        # Check dimensions
        assert polysmalls.shape[1] == 4  # Each polysmall should have 4 elements
        assert polylarges.shape[1] == 4  # Each polylarge should have 4 elements
        
        # Check that the first element of each row is the face index
        for i, row in enumerate(polysmalls):
            assert 210 <= row[0] < 290  # Triangular face indices
            
        for i, row in enumerate(polylarges):
            assert 290 <= row[0] < 302  # Pentagonal face indices

    def test_pentagons_triangles(self):
        """Test the structure and content of the pentagons and triangles arrays."""
        # Check that pentagons and triangles are numpy arrays
        assert isinstance(pentagons, np.ndarray)
        assert isinstance(triangles, np.ndarray)
        
        # Check dimensions
        assert pentagons.shape == (12, 5)  # 12 pentagons, each with 5 vertices
        assert triangles.shape == (80, 3)  # 80 triangles, each with 3 vertices
        
        # Check that all indices are valid vertex indices (0-59)
        assert np.all((0 <= pentagons) & (pentagons < 60))
        assert np.all((0 <= triangles) & (triangles < 60))

    def test_triangle2faces_pentagon2faces(self):
        """Test the structure and content of the triangle2faces and pentagon2faces arrays."""
        # Check that triangle2faces and pentagon2faces are numpy arrays
        assert isinstance(triangle2faces, np.ndarray)
        assert isinstance(pentagon2faces, np.ndarray)
        
        # Check dimensions
        assert triangle2faces.shape == (80, 3)  # 80 triangles, each with 3 adjacent faces
        assert pentagon2faces.shape == (12, 5)  # 12 pentagons, each with 5 adjacent faces
        
        # Check that triangle2faces and pentagon2faces have the expected shapes
        assert triangle2faces.shape == (80, 3)  # 80 triangles, each with 3 adjacent faces
        assert pentagon2faces.shape == (12, 5)  # 12 pentagons, each with 5 adjacent faces

    def test_axis(self):
        """Test the structure and properties of the axis array."""
        # Check that axis is a numpy array with the correct shape
        assert isinstance(axis, np.ndarray)
        assert axis.shape == (8, 3)  # 8 axes, each with 3 coordinates
        
        # Check that all axes are unit vectors
        for ax in axis:
            norm = np.linalg.norm(ax)
            assert 0.99 <= norm <= 1.01, f"Axis {ax} is not a unit vector (norm = {norm})"
        
        # Check that opposite axes are indeed opposite
        for i in range(4):
            assert np.allclose(axis[i], -axis[i+4], atol=1e-10)


class TestCityManager:
    def test_city_manager_initialization(self):
        """Test the initialization of the CityManager class."""
        # Check that city_manager is an instance of CityManager
        assert isinstance(city_manager, CityManager)
        
        # Check that the cities attribute is set correctly
        assert np.array_equal(city_manager.cities, cities)
        
        # Check that the kd_tree attribute is set
        assert hasattr(city_manager, 'kd_tree')

    def test_find_nearest_city(self):
        """Test the find_nearest_city method of the CityManager class."""
        # Test with a position that is exactly a city
        for i, city in enumerate(cities[:10]):  # Test the first 10 cities
            nearest = city_manager.find_nearest_city(city)
            assert nearest == i, f"Expected city {i}, got {nearest}"
        
        # Test with a position that is not exactly a city
        # Create a position slightly offset from a city
        test_position = cities[0] + np.array([0.01, 0.01, 0.01])
        test_position = test_position / np.linalg.norm(test_position)  # Normalize to keep it on the sphere
        nearest = city_manager.find_nearest_city(test_position)
        assert nearest == 0, f"Expected city 0, got {nearest}"


class TestAreaCalculations:
    def test_get_areas(self):
        """Test the get_areas function."""
        # Call the function and check the return values
        triangle_area, pentagon_area, total_area_calc = get_areas()
        
        # Check that the areas are positive
        assert triangle_area > 0
        assert pentagon_area > 0
        assert total_area_calc > 0
        
        # Check that the total area is consistent with the individual areas
        expected_total = 80 * triangle_area * 3 + 12 * pentagon_area * 5
        assert np.isclose(total_area_calc, expected_total, rtol=1e-10)
        
        # Check that the global variables are set correctly
        assert np.isclose(polysmall_area, triangle_area, rtol=1e-10)
        assert np.isclose(polylarge_area, pentagon_area, rtol=1e-10)
        assert np.isclose(total_area, total_area_calc, rtol=1e-10)
