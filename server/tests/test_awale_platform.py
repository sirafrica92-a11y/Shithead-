"""Awalé Abapa rules, no regressions to Shithead/Ludo, live seat protocol."""
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from server.app.awale import (
    IllegalAwaleMove, make_awale_match, apply_awale_action, legal_awale_pits,
    dump_awale, restore_awale, _sow, AwaleMatch,
)
from server.app.main import create_app


def fixture(pits, actor=0, scores=(0, 0), history=()):
    assert len(pits) == 12
    assert sum(pits) + sum(scores) == 48
    return AwaleMatch(tuple(pits), scores, actor, history=history)


def test_initial_four_seeds_each_deterministic_starter():
    m = make_awale_match(seed=1)
    assert m.pits == (4,) * 12
    assert sum(m.pits) == 48
    assert len(legal_awale_pits(m, m.actor)) == 6


def test_sow_skips_origin_when_circling():
    pits = (13,) + (0,) * 10 + (35,)
    new, last = _sow(pits, 0)
    assert new[0] == 0
    assert last == 2
    assert sum(new) == 48


def test_capture_two_three_reverse_opposing_houses():
    # From south house 5 sow exactly two; end at north 7 with two seeds
    m = fixture([0,0,0,0,0,2, 1,1,5,5,5,5], scores=(10,14))
    out = apply_awale_action(m, 0, "sow", pit=5)
    assert out.captured[0] == 14
    assert out.pits[6:8] == (0,0)
    assert sum(out.pits)+sum(out.captured)==48


def test_grand_slam_cancelled():
    m = fixture([0,0,0,0,0,1,1,0,0,0,0,0], scores=(23,23))
    out = apply_awale_action(m, 0, "sow", pit=5)
    assert out.captured == (23,23)
    assert out.pits[6] == 2


def test_cannot_starve_unfed_opponent():
    m = fixture([0,0,0,0,4,4,0,0,0,0,0,0], scores=(20,20))
    assert legal_awale_pits(m, 0) == (4,5)
    with pytest.raises(IllegalAwaleMove):
        apply_awale_action(m, 0, "sow", pit=3)


def test_illegal_moves_leave_state_alone():
    m = make_awale_match(seed=1)
    for seat,pit in ((1-m.actor,m.actor*6), (m.actor, -1),(m.actor, "0"),(m.actor, True)):
        with pytest.raises(IllegalAwaleMove):
            apply_awale_action(m, seat,"sow",pit=pit)
    assert m.pits == (4,)*12


def test_persistence_roundtrip():
    m = apply_awale_action(make_awale_match(seed=1),0,"sow",pit=0) if make_awale_match(seed=1).actor==0 else make_awale_match(seed=1)
    assert restore_awale(dump_awale(m)) == m


def test_awale_api_and_two_seat_websocket(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.db")) as client:
        assert client.post("/api/rooms",json={"capacity":3,"game_type":"awale","name":"A"}).status_code==422
        assert client.get("/awale.js").status_code==200
        created=client.post("/api/rooms",json={"capacity":2,"game_type":"awale","name":"A"}).json()
        code=created["room_id"]
        other=client.post(f"/api/rooms/{code}/join",json={"name":"B"}).json()
        with client.websocket_connect(f"/ws/{code}") as a,client.websocket_connect(f"/ws/{code}") as b:
            a.send_json({"type":"auth","token":created["token"]})
            first=a.receive_json()
            b.send_json({"type":"auth","token":other["token"]})
            second=b.receive_json()
            first=a.receive_json()  # newer broadcast after guest reconnect
            a.send_json({"type":"ready","ready":True,"expected_version":first["version"],"request_id":"ready-a"})
            first=a.receive_json()
            second=b.receive_json()
            b.send_json({"type":"ready","ready":True,"expected_version":second["version"],"request_id":"ready-b"})
            first=a.receive_json()
            second=b.receive_json()
            assert first["game_type"]=="awale"
            assert sum(first["game"]["pits"])==48
            actor=first["game"]["actor"]
            mover=a if actor==0 else b
            view=first if actor==0 else second
            pit=view["game"]["your_legal_pits"][0]
            mover.send_json({"type":"awale","kind":"sow","pit":pit,
                             "expected_version":view["version"],"request_id":"first-sow"})
            after=mover.receive_json()
            assert after["game"]["turn_number"]==1
            assert sum(after["game"]["pits"])+sum(after["game"]["captured"])==48
        with TestClient(create_app(db_path=tmp_path / "rooms.db")) as restored:
            again=restored.get(f"/api/rooms/{code}").json()
            assert again["game"]["turn_number"]==1
            assert again["game_type"]=="awale"


def test_other_games_still_accepted(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "other.db")) as client:
        for game,capacity in (("shithead",6),("ludo",4)):
            r=client.post("/api/rooms",json={"name":"A","capacity":capacity,"game_type":game})
            assert r.status_code==201
            assert r.json()["game_type"]==game
