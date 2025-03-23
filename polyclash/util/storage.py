import json
import secrets
import redis

from abc import ABC, abstractmethod
from polyclash.util.logging import logger


USER_KEY_LENGTH = 16
USER_TOKEN_LENGTH = 48
GAME_ID_LENGTH = 64


class DataStorage(ABC):

    @abstractmethod
    def create_room(self):
        pass

    @abstractmethod
    def contains(self, key_or_token):
        pass

    @abstractmethod
    def get_game_id(self, key):
        pass

    @abstractmethod
    def get_key(self, game_id, role):
        pass

    @abstractmethod
    def get_plays(self, game_id):
        pass

    @abstractmethod
    def list_rooms(self):
        pass

    @abstractmethod
    def close_room(self, game_id):
        pass

    @abstractmethod
    def exists(self, game_id):
        pass

    @abstractmethod
    def joined_status(self, game_id):
        pass

    @abstractmethod
    def all_joined(self, game_id):
        pass

    @abstractmethod
    def ready_status(self, game_id):
        pass

    @abstractmethod
    def all_ready(self, game_id):
        pass

    @abstractmethod
    def create_player(self, key, role):
        pass

    @abstractmethod
    def create_viewer(self, key):
        pass

    @abstractmethod
    def get_role(self, key_or_token):
        pass

    @abstractmethod
    def join_room(self, game_id, role):
        pass

    @abstractmethod
    def is_ready(self, game_id, role):
        pass

    @abstractmethod
    def mark_ready(self, game_id, role):
        pass

    @abstractmethod
    def start_game(self, game_id):
        pass

    @abstractmethod
    def is_started(self, game_id):
        pass

    @abstractmethod
    def add_play(self, game_id, play):
        pass


class MemoryStorage(DataStorage):
    def __init__(self):
        self.games = {}
        self.rooms = {}

    def create_room(self):
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        self.games[game_id] = {
            'id': game_id,
            'keys': {'black': black_key, 'white': white_key, 'viewer': viewer_key},
            'players': {}, 'viewers': [], 'plays': [],
            'joined': {'black': False, 'white': False},
            'ready': {'black': False, 'white': False},
        }
        self.rooms[black_key] = game_id
        self.rooms[white_key] = game_id
        self.rooms[viewer_key] = game_id

        return dict(game_id=game_id, black_key=black_key, white_key=white_key, viewer_key=viewer_key)

    def contains(self, key_or_token):
        return key_or_token in self.rooms

    def get_game_id(self, key):
        return self.rooms[key]

    def get_key(self, game_id, role):
        return self.games[game_id]['keys'][role]

    def get_plays(self, game_id):
        return self.games[game_id]['plays']

    def list_rooms(self):
        return list([key for key in self.games.keys()])

    def close_room(self, game_id):
        game = self.games[game_id]
        del self.rooms[game['keys']['black']]
        del self.rooms[game['keys']['white']]
        del self.rooms[game['keys']['viewer']]
        del self.rooms[game['players']['black']]
        del self.rooms[game['players']['white']]
        for viewer_id in game['viewers']:
            del self.rooms[viewer_id]
        del self.games[game['id']]

    def exists(self, game_id):
        return game_id in self.games

    def joined_status(self, game_id):
        return self.games[game_id]['joined']

    def all_joined(self, game_id):
        return all(self.games[game_id]['joined'].values())

    def ready_status(self, game_id):
        return self.games[game_id]['ready']

    def all_ready(self, game_id):
        return all(self.games[game_id]['ready'].values())

    def create_player(self, key, role):
        if role not in ['black', 'white']:
            raise ValueError('Invalid role')
        if key not in self.rooms:
            raise ValueError('Invalid key')
        if key != self.games[self.rooms[key]]['keys'][role]:
            raise ValueError('Invalid key for role')

        if self.games[self.rooms[key]]['joined'][role]:
            return self.games[self.rooms[key]]['players'][role]

        game = self.games[self.rooms[key]]
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        self.rooms[token] = game['id']
        game['players'][role] = token
        game['joined'][role] = True

        return token

    def create_viewer(self, key):
        if key not in self.rooms:
            raise ValueError('Invalid key')
        if key != self.games[self.rooms[key]]['keys']['viewer']:
            raise ValueError('Invalid key for role')

        game = self.games[self.rooms[key]]
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        self.rooms[token] = game['id']
        game['viewers'].append(token)

    def get_role(self, key_or_token):
        if key_or_token in self.rooms:
            game_id = self.rooms[key_or_token]
            # Check if it's a key
            if key_or_token == self.games[game_id]['keys']['black']:
                return 'black'
            elif key_or_token == self.games[game_id]['keys']['white']:
                return 'white'
            elif key_or_token == self.games[game_id]['keys']['viewer']:
                return 'viewer'
            
            # Check if it's a token
            if 'players' in self.games[game_id]:
                if 'black' in self.games[game_id]['players'] and key_or_token == self.games[game_id]['players']['black']:
                    return 'black'
                elif 'white' in self.games[game_id]['players'] and key_or_token == self.games[game_id]['players']['white']:
                    return 'white'
                
            # Check if it's a viewer token
            if 'viewers' in self.games[game_id] and key_or_token in self.games[game_id]['viewers']:
                return 'viewer'
                
        raise ValueError('Invalid key or token')

    def join_room(self, game_id, role):
        self.games[game_id]['joined'][role] = True

    def is_ready(self, game_id, role):
        return self.games[game_id]['ready'][role]

    def mark_ready(self, game_id, role):
        self.games[game_id]['ready'][role] = True

    def start_game(self, game_id):
        self.games[game_id]['started'] = True

    def is_started(self, game_id):
        return self.games[game_id]['started']

    def add_play(self, game_id, play):
        return self.games[game_id]['plays'].append(play)


class RedisStorage(DataStorage):
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.StrictRedis(host=host, port=port, db=db)

    def create_room(self):
        game_id = secrets.token_hex(GAME_ID_LENGTH // 2)
        black_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        white_key = secrets.token_hex(USER_KEY_LENGTH // 2)
        viewer_key = secrets.token_hex(USER_KEY_LENGTH // 2)

        self.redis.rpush('games', game_id)
        self.redis.hset('rooms', black_key, game_id)
        self.redis.hset('rooms', white_key, game_id)
        self.redis.hset('rooms', viewer_key, game_id)

        self.redis.hset(f'games:{game_id}', 'id', game_id)

        self.redis.hset(f'games:{game_id}', 'keys:black', black_key)
        self.redis.hset(f'games:{game_id}', 'keys:white', white_key)
        self.redis.hset(f'games:{game_id}', f'keys:{black_key}', 'black')
        self.redis.hset(f'games:{game_id}', f'keys:{white_key}', 'white')
        self.redis.hset(f'games:{game_id}', 'keys:viewer', viewer_key)

        self.redis.hset(f'games:{game_id}', 'players:black', '')
        self.redis.hset(f'games:{game_id}', 'players:white', '')
        self.redis.hset(f'games:{game_id}', 'joined:black', str(False))
        self.redis.hset(f'games:{game_id}', 'joined:white', str(False))
        self.redis.hset(f'games:{game_id}', 'ready:black', str(False))
        self.redis.hset(f'games:{game_id}', 'ready:white', str(False))
        self.redis.hset(f'games:{game_id}', 'started', str(False))

        self.redis.expire(f'games:{game_id}', 3600 * 24 * 3)

        # self.redis.rpush(f'games:{game_id}:viewers', '')
        # self.redis.rpush(f'games:{game_id}:plays', '')

        self.reaper()

        return dict(game_id=game_id, black_key=black_key, white_key=white_key, viewer_key=viewer_key)

    def contains(self, key_or_token):
        return self.redis.hexists('rooms', key_or_token)

    def get_game_id(self, key):
        return self.redis.hget('rooms', key).decode('utf-8')

    def get_key(self, game_id, role):
        return self.redis.hget(f'games:{game_id}', f'keys:{role}').decode('utf-8')

    def get_plays(self, game_id):
        if self.redis.exists(f'games:{game_id}:plays'):
            return list([
               json.loads(item.decode('utf-8')) for item in self.redis.lrange(f'games:{game_id}:plays', 0, -1)
            ])
        else:
            return []

    def list_rooms(self):
        if not self.redis.exists('games'):
            return []
        return list([
            item.decode('utf-8') for item in self.redis.lrange('games', 0, -1)
        ])

    def close_room(self, game_id):
        if self.redis.exists(f'games:{game_id}'):
            self.redis.hdel('rooms', self.redis.hget(f'games:{game_id}', 'keys:black'))
            self.redis.hdel('rooms', self.redis.hget(f'games:{game_id}', 'keys:white'))
            self.redis.hdel('rooms', self.redis.hget(f'games:{game_id}', 'keys:viewer'))
            self.redis.hdel('rooms', self.redis.hget(f'games:{game_id}', 'players:black'))
            self.redis.hdel('rooms', self.redis.hget(f'games:{game_id}', 'players:white'))
        if self.redis.exists(f'games:{game_id}:viewer'):
            for viewer_id in self.redis.lrange(f'games:{game_id}:viewers', 0, -1):
                self.redis.hdel('rooms', viewer_id.decode('utf-8'))

        self.redis.delete(f'games:{game_id}')
        self.redis.lrem('games', 1, game_id)

        if self.redis.exists(f'games:{game_id}:viewer'):
            self.redis.delete(f'games:{game_id}:viewer')
        if self.redis.exists(f'games:{game_id}:plays'):
            self.redis.delete(f'games:{game_id}:plays')

    def exists(self, game_id):
        return game_id in list([item.decode('utf-8') for item in self.redis.lrange('games', 0, -1)])

    def joined_status(self, game_id):
        return {
            key: bool(self.redis.hget(f'games:{game_id}', f'joined:{key}').decode('utf-8') == 'True') for key in ['black', 'white']
        }

    def all_joined(self, game_id):
        return all(self.joined_status(game_id).values())

    def ready_status(self, game_id):
        return {
            key: bool(self.redis.hget(f'games:{game_id}', f'ready:{key}').decode('utf-8') == 'True') for key in ['black', 'white']
        }

    def all_ready(self, game_id):
        return all(self.ready_status(game_id).values())

    def create_player(self, key, role):
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        game_id = self.get_game_id(key)
        self.redis.hset('rooms', token, game_id)
        self.redis.hset(f'games:{game_id}', f'players:{role}', token)
        self.redis.hset(f'games:{game_id}', f'players:{token}', role)
        self.redis.hset(f'games:{game_id}', f'joined:{role}', str(True))
        return token

    def create_viewer(self, key):
        token = secrets.token_hex(USER_TOKEN_LENGTH // 2)
        game_id = self.get_game_id(key)
        self.redis.hset('rooms', token, game_id)
        self.redis.rpush(f'games:{game_id}:viewer', token)
        self.redis.expire(f'games:{game_id}:viewer', 3600 * 24 * 3)

    def get_role(self, key_or_token):
        game_id = self.get_game_id(key_or_token)
        
        # Check if it's a key
        role = self.redis.hget(f'games:{game_id}', f'keys:{key_or_token}')
        if role:
            return role.decode('utf-8')
            
        # Check if it's a player token
        role = self.redis.hget(f'games:{game_id}', f'players:{key_or_token}')
        if role:
            return role.decode('utf-8')
            
        # If not a key or player token, assume it's a viewer token
        return 'viewer'

    def join_room(self, game_id, role):
        self.redis.hset(f'games:{game_id}', f'joined:{role}', str(True))

    def is_ready(self, game_id, role):
        return bool(self.redis.hget(f'games:{game_id}', f'ready:{role}').decode('utf-8') == 'True')

    def mark_ready(self, game_id, role):
        self.redis.hset(f'games:{game_id}', f'ready:{role}', str(True))

    def start_game(self, game_id):
        self.redis.hset(f'games:{game_id}', 'started', str(True))

    def is_started(self, game_id):
        return bool(self.redis.hget(f'games:{game_id}', 'started').decode('utf-8') == 'True')

    def add_play(self, game_id, play):
        self.redis.rpush(f'games:{game_id}:plays', json.dumps(play))
        self.redis.expire(f'games:{game_id}:plays', 3600 * 24 * 3)

    def reaper(self):
        for game_id in self.list_rooms():
            # if game_id is not represented in the key of games:{game_id}
            # then it means the game is over and we should clean up
            if not self.redis.exists(f'games:{game_id}'):
                self.close_room(game_id)


def test_redis_connection(host='localhost', port=6379, db=0):
    try:
        redis.StrictRedis(host=host, port=port, db=db).ping()
        logger.info("Successfully connected to Redis. Using Redis as data storage.")
        return True
    except redis.ConnectionError:
        logger.info("Failed to connect to Redis. Using memory dict as data storage.")
        return False


def create_storage(flag_redis=None):
    if flag_redis is None:
        flag_redis = test_redis_connection()
    if flag_redis:
        return RedisStorage()
    return MemoryStorage()
