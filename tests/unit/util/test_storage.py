import pytest
import secrets
from polyclash.util.storage import MemoryStorage, create_storage

class TestMemoryStorage:
    def test_create_room(self):
        storage = MemoryStorage()
        data = storage.create_room()
        assert 'game_id' in data
        assert 'black_key' in data
        assert 'white_key' in data
        assert 'viewer_key' in data

    def test_contains(self):
        storage = MemoryStorage()
        data = storage.create_room()
        black_key = data['black_key']
        
        # Test that the key exists
        assert storage.contains(black_key) == True
        
        # Test with a non-existent key
        non_existent_key = secrets.token_hex(8)
        assert storage.contains(non_existent_key) == False

    def test_get_game_id(self):
        storage = MemoryStorage()
        data = storage.create_room()
        game_id = data['game_id']
        black_key = data['black_key']
        
        # Test getting the game_id by key
        assert storage.get_game_id(black_key) == game_id

    def test_get_key(self):
        storage = MemoryStorage()
        data = storage.create_room()
        game_id = data['game_id']
        black_key = data['black_key']
        
        # Test getting the key by game_id and role
        assert storage.get_key(game_id, 'black') == black_key

    def test_get_role(self):
        storage = MemoryStorage()
        data = storage.create_room()
        black_key = data['black_key']
        
        # Test getting the role by key
        assert storage.get_role(black_key) == 'black'
        
        # Test with an invalid key
        with pytest.raises(ValueError):
            storage.get_role('invalid_key')

    def test_create_player(self):
        storage = MemoryStorage()
        data = storage.create_room()
        black_key = data['black_key']
        
        # Test creating a player
        token = storage.create_player(black_key, 'black')
        assert token is not None
        assert storage.contains(token) == True
        
        # Test with an invalid key
        with pytest.raises(ValueError):
            storage.create_player('invalid_key', 'black')
        
        # Test with an invalid role
        with pytest.raises(ValueError):
            storage.create_player(black_key, 'invalid_role')

class TestStorageFactory:
    def test_create_storage(self):
        # Test creating a MemoryStorage
        storage = create_storage(flag_redis=False)
        assert isinstance(storage, MemoryStorage)
