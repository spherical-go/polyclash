import requests
import json

sever = None
game_token = None
player_token = None


def get_server():
    return sever


def connect(server, token):
    global sever, game_token
    sever = server
    game_token = token
    try:
        resp = requests.post(f'{server}/sphgo/new', json={'token': token})
        if resp.status_code == 200:
            data = resp.json()
            black_key = data.get('black_key')
            white_key = data.get('white_key')
            audience_key = data.get('audience_key')
            return black_key, white_key, audience_key
        else:
            raise ValueError(resp.json().get('message'))
    except requests.exceptions.ConnectionError:
        # when the server is not reachable
        raise ValueError('Server not reachable when we start the game')


def play(steps, play):
    if player_token is None:
        raise ValueError('Player token not set')
    try:
        resp = requests.post(f'{sever}/sphgo/play', json={'token': player_token, 'steps': steps, 'play': [int(city) for city in play]})
        if resp.status_code != 200:
            raise ValueError(resp.json().get('message'))
    except requests.exceptions.ConnectionError:
        raise ValueError('Server not reachable when we play the game')


def close_game():
    if game_token is not None:
        try:
            resp = requests.post(f'{sever}/sphgo/close', json={'token': game_token})
            if resp.status_code != 200:
                raise ValueError(resp.json().get('message'))
        except requests.exceptions.ConnectionError:
            raise ValueError('Server not reachable when we close the game')
