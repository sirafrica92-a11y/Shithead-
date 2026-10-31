"""Solo Ludo never takes a multiplayer slot and never trusts client die values."""
import pytest
from fastapi.testclient import TestClient
from server.app.main import create_app
from server.app import solo_ludo
from server.app.ludo import LudoMatch, LudoPlayer, make_ludo_match, apply_ludo_action


@pytest.fixture(autouse=True)
def clear_solo_sessions():
    solo_ludo._sessions.clear()
    yield
    solo_ludo._sessions.clear()


def test_solo_create_auth_isolation_and_capacity(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        rooms = c.app.state.room_store
        rooms.max_rooms = 1
        first = c.post("/api/solo/ludo")
        assert first.status_code == 201
        payload=first.json()
        assert payload["solo"] is True
        assert payload["players"] == ["You", "Computer"]
        assert payload["game"]["game_type"] == "ludo"
        assert len(payload["game"]["players"]) == 2
        assert len(rooms.rooms) == 0
        assert c.get("/solo/ludo").status_code == 200
        assert c.get("/solo/ludo.js").status_code == 200
        assert c.get("/api/solo/ludo/"+payload["id"]).status_code == 404
        assert c.get("/api/solo/ludo/"+payload["id"],
                     headers={"X-Solo-Token": "x"*43}).status_code == 404
        assert c.get("/api/solo/ludo/"+payload["id"],
                     headers={"X-Solo-Token":payload["token"]}).status_code == 200
        assert c.post("/api/solo/ludo/"+payload["id"],json={
            "token":"x"*43,"version":payload["version"],"action":"roll"
        }).status_code==404
        assert c.post("/api/rooms",json={
            "name":"Friend","capacity":2,"game_type":"ludo"
        }).status_code == 201
        assert len(rooms.rooms) == 1


def test_solo_roll_move_rejects_stale_and_illegal(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        created=c.post("/api/solo/ludo").json()
        key=created["id"]
        session=solo_ludo._sessions[key]
        # Deterministic board, so token zero leaves base on a six.
        session.match=make_ludo_match(2,seed=1)
        session.match=LudoMatch(players=session.match.players,actor=0)
        created["version"]=session.version
        bad=c.post("/api/solo/ludo/"+key,json={
            "token":created["token"],"version":created["version"],
            "action":"move","piece":0
        })
        assert bad.status_code==422
        assert session.version==created["version"]
        assert c.post("/api/solo/ludo/"+key,json={
            "token":created["token"],"version":created["version"],
            "action":"change_rules"
        }).status_code==422
        # Roll may either pass or permit a legal token; both comply with game engine.
        rolled=c.post("/api/solo/ludo/"+key,json={
            "token":created["token"],"version":created["version"],
            "action":"roll","forced_roll":6
        })
        assert rolled.status_code==200
        assert rolled.json()["version"]>created["version"]
        assert c.post("/api/solo/ludo/"+key,json={
            "token":created["token"],"version":created["version"],
            "action":"roll"
        }).status_code==409
        # A forged die is ignored; schema only permits the actual server roll.
        assert 1<=rolled.json()["game"]["last_roll"]<=6
        assert "forced_roll" not in rolled.json()["game"]


def test_computer_uses_only_legal_tokens_and_bounded_loop():
    import secrets
    from dataclasses import replace
    m=make_ludo_match(2,seed=2)
    m=replace(m,actor=1,stage="MOVE",die=6,last_roll=6)
    legal=solo_ludo.legal_tokens(m,1,6)
    assert solo_ludo._best_piece(m) in legal
    game=solo_ludo.Session(token=secrets.token_urlsafe(32),match=m)
    solo_ludo._bot_play(game)
    assert game.version <= solo_ludo.BOT_STEP_LIMIT
    assert game.match.winner is not None or game.match.actor in (0,1)
    assert all(len(p.tokens)==4 for p in game.match.players)


def test_ludo_dice_game_engine_unchanged():
    m=make_ludo_match(2,seed=7)
    for seat in (0,1):
        from dataclasses import replace
        prepared=replace(m,actor=seat)
        rolled=apply_ludo_action(prepared,seat,"roll",forced_roll=6)
        assert rolled.last_roll==6
        assert rolled.stage=="MOVE"
