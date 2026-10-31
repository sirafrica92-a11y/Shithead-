"""Dara computer safety gates: engine authority, entire games and coexistence."""
import random
import secrets
from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from server.app import solo_dara, solo_awale, solo_ludo
from server.app.dara import (
    make_dara_match, legal_dara_moves, apply_dara_action, assert_dara_invariants,
)
from server.app.main import create_app


@pytest.fixture(autouse=True)
def clear_sessions():
    solo_dara._sessions.clear()
    yield
    solo_dara._sessions.clear()


def test_create_routes_auth_and_all_six_multiplayer_games(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        game=c.post("/api/solo/dara")
        assert game.status_code==201
        data=game.json()
        assert data["solo"] is True
        assert data["game"]["game_type"]=="dara"
        assert data["game"]["stage"]=="PLACE"
        assert len(data["game"]["cells"])==30
        assert not c.app.state.room_store.rooms
        assert c.get("/solo/dara").status_code==200
        assert c.get("/solo/dara.js").status_code==200
        assert c.get("/health").json()=={"status":"ok"}
        assert c.get("/brand/shithead-logo.png").status_code==200
        for path in ("/","/client.js","/ludo.js","/awale.js","/dara.js",
                     "/yote.js","/dominoes.js","/solo/ludo","/solo/ludo.js",
                     "/solo/awale","/solo/awale.js"):
            assert c.get(path).status_code==200,path
        key=data["id"];url="/api/solo/dara/"+key
        assert c.get(url).status_code==404
        assert c.get(url,headers={"X-Solo-Token":"x"*43}).status_code==404
        assert c.get(url,headers={"X-Solo-Token":data["token"]}).status_code==200
        assert c.post(url,json={"token":"x"*43,"version":data["version"],
                                "kind":"place","index":0}).status_code==404
        for name,capacity in (("shithead",2),("ludo",2),("awale",2),("dara",2),
                              ("yote",2),("dominoes",4)):
            r=c.post("/api/rooms",json={"name":"Host","capacity":capacity,"game_type":name})
            assert r.status_code==201,(name,r.text)
            room=r.json()
            assert c.get("/api/rooms/"+room["room_id"]).status_code==200
            assert c.post(f'/api/rooms/{room["room_id"]}/join',json={"name":"Friend"}).status_code==201
        assert len(c.app.state.room_store.rooms)==6
        ludo=c.post("/api/solo/ludo")
        awale=c.post("/api/solo/awale")
        assert ludo.status_code==201 and awale.status_code==201
        assert len(c.app.state.room_store.rooms)==6
        solo_ludo._sessions.pop(ludo.json()["id"],None)
        solo_awale._sessions.pop(awale.json()["id"],None)


def test_strict_actions_and_versions_and_reset(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        data=c.post("/api/solo/dara").json()
        key=data["id"];url="/api/solo/dara/"+key
        v=data["version"]
        for kind,fields in (("capture",{"index":1}),("move",{"source":1,"destination":2}),
                            ("place",{"index":True}),("place",{"index":-1})):
            response=c.post(url,json={"token":data["token"],"version":v,"kind":kind,**fields})
            assert response.status_code==422,(kind,response.text)
        legal=data["game"]["legal"]
        assert legal["places"]
        ok=c.post(url,json={"token":data["token"],"version":v,"kind":"place",
                            "index":legal["places"][0]})
        assert ok.status_code==200,ok.text
        v2=ok.json()["version"]
        assert v2>v
        assert c.post(url,json={"token":data["token"],"version":v,
                                "kind":"place","index":0}).status_code==409
        for _ in range(4):
            r=c.post(url+"/reset",json={"token":data["token"],"version":v2})
            assert r.status_code==200,r.text
            v2=r.json()["version"]
            assert r.json()["game"]["stage"]=="PLACE"
        assert len(solo_dara._sessions)==1
        assert not c.app.state.room_store.rooms


def test_bot_actions_are_legal_and_do_not_mutate_match():
    match=replace(make_dara_match(),actor=1)
    before=match
    kind,kwargs=solo_dara._best_bot_action(match)
    assert match==before
    assert kind=="place" and kwargs["index"] in legal_dara_moves(match,1)["places"]
    s=solo_dara.SoloDaraSession(token=secrets.token_urlsafe(32),match=match)
    solo_dara._computer_reply(s)
    assert s.version==1
    assert s.match.actor==0 or s.match.finished


def test_complete_games_follow_exact_engine_no_rule_modifications():
    rng=random.Random(101)
    terminal=0
    for game in range(12):
        m=make_dara_match()
        for _ in range(1200):
            if m.finished:
                terminal+=1;break
            seat=m.actor
            legal=legal_dara_moves(m,seat)
            if seat==1: kind,kwargs=solo_dara._best_bot_action(m)
            elif legal["captures"]:kind,kwargs="capture",{"index":rng.choice(legal["captures"])}
            elif legal["places"]:kind,kwargs="place",{"index":rng.choice(legal["places"])}
            else:
                source,destination=rng.choice(legal["moves"])
                kind,kwargs="move",{"source":source,"destination":destination}
            m=apply_dara_action(m,seat,kind,**kwargs)
            assert_dara_invariants(m)
        assert m.finished,"Dara match did not complete"
    assert terminal==12


def test_idle_expiry_and_capacity_preserve_room_store(tmp_path,monkeypatch):
    monkeypatch.setattr(solo_dara,"MAX_SESSIONS",1)
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        a=c.post("/api/solo/dara").json()
        assert c.post("/api/solo/dara").status_code==503
        solo_dara._sessions[a["id"]].last_active-=solo_dara.SESSION_TTL+2
        assert c.get("/api/solo/dara/"+a["id"],headers={"X-Solo-Token":a["token"]}).status_code==404
        b=c.post("/api/solo/dara")
        assert b.status_code==201
        assert a["id"] not in solo_dara._sessions
        assert len(solo_dara._sessions)==1
        assert not c.app.state.room_store.rooms

def test_bot_action_trace_matches_actual_engine_state_and_refresh_skips_replay(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        a=c.post("/api/solo/dara").json()
        session=solo_dara._sessions[a["id"]]
        session.match=replace(make_dara_match(),actor=1)
        solo_dara._computer_reply(session)
        steps=session.action_trace
        assert steps and all(step["message"].startswith("Computer ") for step in steps)
        assert steps[-1]["game"]==solo_dara.private_dara_view(session.match,0)
        assert session.match.actor==0 or session.match.finished
        resumed=c.get("/api/solo/dara/"+a["id"],headers={"X-Solo-Token":a["token"]})
        assert resumed.status_code==200
        assert resumed.json()["computer_actions"]==[]
        assert resumed.json()["game"]==steps[-1]["game"]

def test_solo_dara_browser_action_trace_accessibility(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        page=c.get("/solo/dara").text
        code=c.get("/solo/dara.js").text
        assert 'id="cpu-log"' in page and 'id="skip-cpu"' in page
        assert 'aria-live="polite"' in page
        assert "showComputerTurns" in code
        assert "displayFrame=step.game" in code
        assert "computer_actions" in code
