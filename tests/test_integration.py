from polyclash.server import server_token


def test_solo_whoami(storage, test_client, socketio_client):
    """Call /sphgo/whoami with a valid key, verify correct role."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200

    # Check black key
    res = test_client.post("/sphgo/whoami", json={"key": result0.json["black_key"]})
    assert res.status_code == 200
    assert res.json["role"] == "black"
    assert res.json["game_id"] == result0.json["game_id"]

    # Check white key
    res = test_client.post("/sphgo/whoami", json={"key": result0.json["white_key"]})
    assert res.status_code == 200
    assert res.json["role"] == "white"

    # Check viewer key
    res = test_client.post("/sphgo/whoami", json={"key": result0.json["viewer_key"]})
    assert res.status_code == 200
    assert res.json["role"] == "viewer"

    # Check invalid key
    res = test_client.post("/sphgo/whoami", json={"key": "bogus_key"})
    assert res.status_code == 401


def test_solo_flow(storage, test_client, socketio_client):
    """Create game → join both → ready both → play black → genmove white → verify state."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200

    # Join black
    result1 = test_client.post(
        "/sphgo/join", json={"token": result0.json["black_key"], "role": "black"}
    )
    assert result1.status_code == 200
    black_token = result1.json["token"]

    # Join white
    result2 = test_client.post(
        "/sphgo/join", json={"token": result0.json["white_key"], "role": "white"}
    )
    assert result2.status_code == 200
    white_token = result2.json["token"]

    # Ready both
    test_client.post("/sphgo/ready", json={"token": black_token})
    test_client.post("/sphgo/ready", json={"token": white_token})

    # Play a move as black (step 0)
    result3 = test_client.post(
        "/sphgo/play",
        json={
            "token": black_token,
            "role": "black",
            "steps": 0,
            "play": [5, 6, 7, 8, 9],
        },
    )
    assert result3.status_code == 200

    # Verify state: counter=1, current_player=-1 (white's turn)
    state1 = test_client.post("/sphgo/state", json={"token": black_token})
    assert state1.status_code == 200
    assert state1.json["counter"] == 1
    assert state1.json["current_player"] == -1

    # genmove for white AI
    result4 = test_client.post("/sphgo/genmove", json={"token": white_token})
    assert result4.status_code == 200

    # After genmove: counter should be 2 (or point is null if AI passes)
    state2 = test_client.post("/sphgo/state", json={"token": black_token})
    assert state2.status_code == 200
    if result4.json["point"] is not None:
        assert state2.json["counter"] == 2
        assert state2.json["current_player"] == 1
    else:
        # AI passed, counter stays at 1
        assert state2.json["counter"] == 1


def test_solo_genmove_pass(storage, test_client, socketio_client):
    """Test that genmove returns point: null gracefully when called on an empty board."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200

    # Join both
    result1 = test_client.post(
        "/sphgo/join", json={"token": result0.json["black_key"], "role": "black"}
    )
    assert result1.status_code == 200
    black_token = result1.json["token"]

    result2 = test_client.post(
        "/sphgo/join", json={"token": result0.json["white_key"], "role": "white"}
    )
    assert result2.status_code == 200
    white_token = result2.json["token"]

    # Ready both
    test_client.post("/sphgo/ready", json={"token": black_token})
    test_client.post("/sphgo/ready", json={"token": white_token})

    # genmove for black on empty board – should succeed (either a move or pass)
    result3 = test_client.post("/sphgo/genmove", json={"token": black_token})
    assert result3.status_code == 200
    # Response should always have "point" and "play" keys
    assert "point" in result3.json
    assert "play" in result3.json


def test_family_flow(storage, test_client, socketio_client):
    """Create game → join black/white → ready → play alternating moves → verify state."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200

    # Join black
    result1 = test_client.post(
        "/sphgo/join", json={"token": result0.json["black_key"], "role": "black"}
    )
    assert result1.status_code == 200
    black_token = result1.json["token"]

    # Join white
    result2 = test_client.post(
        "/sphgo/join", json={"token": result0.json["white_key"], "role": "white"}
    )
    assert result2.status_code == 200
    white_token = result2.json["token"]

    # Ready both
    test_client.post("/sphgo/ready", json={"token": black_token})
    test_client.post("/sphgo/ready", json={"token": white_token})

    # Black plays step 0
    result3 = test_client.post(
        "/sphgo/play",
        json={
            "token": black_token,
            "role": "black",
            "steps": 0,
            "play": [5, 6, 7, 8, 9],
        },
    )
    assert result3.status_code == 200

    # White plays step 1
    result4 = test_client.post(
        "/sphgo/play",
        json={
            "token": white_token,
            "role": "white",
            "steps": 1,
            "play": [0, 1, 2, 3, 4],
        },
    )
    assert result4.status_code == 200

    # Verify state
    state = test_client.post("/sphgo/state", json={"token": black_token})
    assert state.status_code == 200
    assert state.json["counter"] == 2
    assert state.json["current_player"] == 1  # black's turn again


def test_family_viewer(storage, test_client, socketio_client):
    """Viewer joins with viewer_key and can fetch state."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200

    # Join as viewer
    result1 = test_client.post(
        "/sphgo/join", json={"token": result0.json["viewer_key"], "role": "viewer"}
    )
    assert result1.status_code == 200
    viewer_token = result1.json["token"]

    # Viewer can fetch state
    state = test_client.post("/sphgo/state", json={"token": viewer_token})
    assert state.status_code == 200
    assert "board" in state.json
    assert "score" in state.json
    assert len(state.json["board"]) == 302


def test_resign(storage, test_client, socketio_client):
    """Create game → join + ready → play a move → black resigns → verify response."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200

    # Join both
    result1 = test_client.post(
        "/sphgo/join", json={"token": result0.json["black_key"], "role": "black"}
    )
    assert result1.status_code == 200
    black_token = result1.json["token"]

    result2 = test_client.post(
        "/sphgo/join", json={"token": result0.json["white_key"], "role": "white"}
    )
    assert result2.status_code == 200
    white_token = result2.json["token"]

    # Ready both
    test_client.post("/sphgo/ready", json={"token": black_token})
    test_client.post("/sphgo/ready", json={"token": white_token})

    # Play a move
    test_client.post(
        "/sphgo/play",
        json={
            "token": black_token,
            "role": "black",
            "steps": 0,
            "play": [5, 6, 7, 8, 9],
        },
    )

    # Black resigns
    result3 = test_client.post("/sphgo/resign", json={"token": black_token})
    assert result3.status_code == 200
    assert result3.json["winner"] == "white"
    assert "score" in result3.json
    assert len(result3.json["score"]) == 2  # (black_score, white_score)


def test_close_game(storage, test_client, socketio_client):
    """Create game → join + ready → play → close → verify removed from list."""
    result0 = test_client.post("/sphgo/new", json={"key": server_token})
    assert result0.status_code == 200
    game_id = result0.json["game_id"]

    # Join both
    result1 = test_client.post(
        "/sphgo/join", json={"token": result0.json["black_key"], "role": "black"}
    )
    assert result1.status_code == 200
    black_token = result1.json["token"]

    result2 = test_client.post(
        "/sphgo/join", json={"token": result0.json["white_key"], "role": "white"}
    )
    assert result2.status_code == 200
    white_token = result2.json["token"]

    # Ready both
    test_client.post("/sphgo/ready", json={"token": black_token})
    test_client.post("/sphgo/ready", json={"token": white_token})

    # Play a move
    test_client.post(
        "/sphgo/play",
        json={
            "token": black_token,
            "role": "black",
            "steps": 0,
            "play": [5, 6, 7, 8, 9],
        },
    )

    # Close game
    result3 = test_client.post("/sphgo/close", json={"token": black_token})
    assert result3.status_code == 200

    # Verify game is removed from list
    result4 = test_client.get("/sphgo/list")
    assert game_id not in result4.json["rooms"]
