import requests

shared_server = None
game_token = None

player_key = None
viewer_key = None

player_token = None


def get_server():
    return shared_server


def set_server(server):
    global shared_server
    shared_server = server


def set_game_token(token):
    global game_token
    game_token = token


def set_player_key(key):
    global player_key
    player_key = key


def set_player_token(token):
    global player_token
    player_token = token


def set_viewer_key(key):
    global viewer_key
    viewer_key = key


def connect(server, token):
    set_server(server)
    set_game_token(token)
    try:
        resp = requests.post(f'{server}/sphgo/new', json={'token': token})
        if resp.status_code == 200:
            data = resp.json()
            black_key = data.get('black_key')
            white_key = data.get('white_key')
            viewer_key = data.get('viewer_key')
            return black_key, white_key, viewer_key
        else:
            raise ValueError(resp.json().get('message'))
    except requests.exceptions.ConnectionError:
        # when the server is not reachable
        raise ValueError('Server not reachable when we start the game')


def get_game_status(status_type, server, token):
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return 'None'

    resp = requests.post(f'{server}/sphgo/{status_type}_status', json={'token': token})
    if resp.status_code == 200:
        status = resp.json().get('status')
        print(status)
        if status['black'] and status['white']:
            return 'Both'
        elif status['black']:
            return 'Black'
        elif status['white']:
            return 'White'
        else:
            return 'Neither'
    else:
        raise ValueError(resp.json().get('message'))


def joined_status(server, token):
    return get_game_status('joined', server, token)


def join(server, role, token):
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return

    resp = requests.post(f'{server}/sphgo/join', json={'token': token, 'role': role})
    if resp.status_code == 200:
        return 'Ready'
    else:
        raise ValueError(resp.json().get('message'))


def ready_status(server, token):
    return get_game_status('ready', server, token)


def ready(server, role, token):
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return

    resp = requests.post(f'{server}/sphgo/ready', json={'token': token, 'role': role})
    if resp.status_code == 200:
        return 'Ready'
    else:
        raise ValueError(resp.json().get('message'))


def cancel(server, role, token):
    set_server(server)
    if token:
        set_player_token(token)
    else:
        return

    resp = requests.post(f'{server}/sphgo/cancel', json={'token': token, 'role': role})
    if resp.status_code == 200:
        return 'Canceled'
    else:
        raise ValueError(resp.json().get('message'))


def play(server, steps, play):
    set_server(server)
    if player_token is None:
        raise ValueError('Player token not set')
    try:
        resp = requests.post(f'{server}/sphgo/play', json={'token': player_token, 'steps': steps, 'play': [int(city) for city in play]})
        if resp.status_code != 200:
            raise ValueError(resp.json().get('message'))
    except requests.exceptions.ConnectionError:
        raise ValueError('Server not reachable when we play the game')


def close(server):
    if game_token is not None:
        try:
            resp = requests.post(f'{server}/sphgo/close', json={'token': game_token})
            if resp.status_code != 200:
                raise ValueError(resp.json().get('message'))
        except requests.exceptions.ConnectionError:
            raise ValueError('Server not reachable when we close the game')
