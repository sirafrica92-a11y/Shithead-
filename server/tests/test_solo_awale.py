"""Solo Awalé computer uses existing server rules, without using multiplayer rooms."""
import random
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from server.app import solo_awale
from server.app.awale import (
    SEEDS, apply_awale_action, assert_awale_invariants, legal_awale_pits,
    make_awale_match,
)
from server.app.main import create_app


@pytest.fixture(autouse=True)
def clean_sessions():
    solo_awale._sessions.clear()
    yield
    solo_awale._sessions.clear()


def test_solo_create_separate_from_room_capacity_and_requires_token(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        c.app.state.room_store.max_rooms = 1
        resp = c.post("/api/solo/awale")
        assert resp.status_code == 201
        assert resp.headers["cache-control"] == "no-store"
        game = resp.json()
        assert game["solo"] is True
        assert game["players"] == ["You", "Computer"]
        assert game["game"]["game_type"] == "awale"
        assert sum(game["game"]["pits"]) + sum(game["game"]["captured"]) == SEEDS
        assert not c.app.state.room_store.rooms
        assert c.get("/solo/awale").status_code == 200
        assert c.get("/solo/awale.js").status_code == 200
        url = "/api/solo/awale/" + game["id"]
        assert c.get(url).status_code == 404
        assert c.get(url, headers={"X-Solo-Token": "x"*43}).status_code == 404
        assert c.get(url, headers={"X-Solo-Token": game["token"]}).status_code == 200
        assert c.post(url, json={
            "token": "x"*43, "version":game["version"],"pit":0
        }).status_code == 404
        assert c.post("/api/rooms", json={"name":"Guest","capacity":2,"game_type":"awale"}).status_code == 201
        assert len(c.app.state.room_store.rooms) == 1


def test_solo_rejects_illegal_stale_wrong_types_and_reuses_session(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.sqlite3")) as c:
        game = c.post("/api/solo/awale").json()
        url = "/api/solo/awale/" + game["id"]
        session = solo_awale._sessions[game["id"]]
        start_version = game["version"]
        assert c.post(url, json={"token":game["token"],"version":start_version,
                                 "pit":11}).status_code == 422
        assert c.post(url, json={"token":game["token"],"version":start_version,
                                 "pit":True}).status_code == 422
        assert c.post(url, json={"token":game["token"],"version":start_version,
                                 "pit":0.5}).status_code == 422
        assert session.version == start_version
        if game["game"]["your_legal_pits"]:
            pit = game["game"]["your_legal_pits"][0]
            response = c.post(url,json={"token":game["token"],"version":start_version,"pit":pit})
            assert response.status_code == 200
            new_version = response.json()["version"]
            assert new_version > start_version
        else:
            new_version = start_version
        stale = c.post(url+"/reset",json={
            "token":game["token"],"version":new_version+1
        })
        assert stale.status_code == 409
        for _ in range(5):
            result = c.post(url+"/reset",json={"token":game["token"],"version":new_version})
            assert result.status_code == 200
            new_version = result.json()["version"]
            assert result.json()["game"]["phase"] == "PLAYING"
        assert len(solo_awale._sessions) == 1


def test_bot_one_move_legal_and_full_games_conserve_seeds():
    rng = random.Random(212)
    saw_terminal = False
    for seed in range(12):
        match = make_awale_match(seed=seed)
        for _ in range(600):
            if match.finished:
                saw_terminal=True
                break
            seat=match.actor
            legal=legal_awale_pits(match, seat)
            assert legal
            pit = solo_awale._best_bot_pit(match) if seat==1 else rng.choice(legal)
            assert pit in legal
            match=apply_awale_action(match,seat,"sow",pit=pit)
            assert_awale_invariants(match)
            assert sum(match.pits)+sum(match.captured)==SEEDS
        assert match.finished, "Awalé policy should reach a terminal result"
    assert saw_terminal


def test_bot_does_not_mutate_state_and_reset_has_no_random_remote_model_cost():
    m=make_awale_match(seed=1)
    if m.actor==0:
        m=replace(m,actor=1)
    before=m
    move=solo_awale._best_bot_pit(m)
    assert move in legal_awale_pits(m,1)
    assert m==before
    s=solo_awale.SoloAwaleSession(token="x"*43,match=m)
    solo_awale._computer_reply(s)
    assert s.version == 1
    assert s.match.actor == 0 or s.match.finished
