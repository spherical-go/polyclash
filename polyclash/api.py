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

    resp = requests.post(f'{server}/sphgo/new', json={'token': token})
    if resp.status_code == 200:
        data = resp.json()
        black_key = data.get('black_key')
        white_key = data.get('white_key')
        audience_key = data.get('audience_key')
        return black_key, white_key, audience_key
    else:
        raise ValueError(resp.json().get('message'))


def play(steps, play):
    if player_token is None:
        raise ValueError('Player token not set')

    resp = requests.post(f'{sever}/sphgo/play', json={'token': player_token, 'steps': steps, 'play': [int(city) for city in play]})
    if resp.status_code != 200:
        raise ValueError(resp.json().get('message'))


def close_game():
    if game_token is not None:
        resp = requests.post(f'{sever}/sphgo/close', json={'token': game_token})
        if resp.status_code != 200:
            raise ValueError(resp.json().get('message'))
