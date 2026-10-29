"""Ludo engine and original Shithead safety contract."""
from dataclasses import replace
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from server.app.ludo import (
    make_ludo_match, apply_ludo_action, legal_tokens,
    track_square, LudoPlayer, IllegalLudoMove, dump_ludo, restore_ludo,
)
from server.app.main import create_app


def match_with(*players, actor=0, stage="MOVE", die=1):
    m = make_ludo_match(len(players), seed=1)
    return replace(m, players=tuple(players), actor=actor, stage=stage, die=die)


def test_sixes_are_unlimited_and_leaving_base_uses_six():
    m = make_ludo_match(2, seed=2)
    seat = m.actor
    for _ in range(4):
        m = apply_ludo_action(m, seat, "roll", forced_roll=6)
        assert m.stage == "MOVE"
        assert legal_tokens(m, seat, 6)
        new = next(i for i,p in enumerate(m.players[seat].tokens) if p == -1)
        m = apply_ludo_action(m, seat, "move", token=new)
        assert m.actor == seat and m.stage == "ROLL"
    assert all(p == 0 for p in m.players[seat].tokens)
    assert m.winner is None


def test_capture_awards_extra_roll_safe_squares_do_not_capture():
    red = LudoPlayer("red", (10,-1,-1,-1))
    green = LudoPlayer("green", (49,-1,-1,-1))  # global square 10
    m = match_with(red, green, die=1)
    assert track_square(green,49) == 10
    # Red arrives at global 11, so adjust target to match.
    green = replace(green, tokens=(50,-1,-1,-1))
    m = match_with(red, green, die=1)
    assert track_square(green, 50) == 11
    nxt = apply_ludo_action(m,0,"move",token=0)
    assert nxt.players[1].tokens[0] == -1
    assert nxt.actor == 0
    safe = match_with(LudoPlayer("red",(7,-1,-1,-1)),
                      LudoPlayer("green",(47,-1,-1,-1)),die=1)
    # Red lands on square 8 (safe), green at same global 8.
    assert track_square(safe.players[1],47) == 8
    out = apply_ludo_action(safe,0,"move",token=0)
    assert out.players[1].tokens[0] == 47
    assert out.actor == 1


def test_blockades_block_crossing_and_exact_home():
    red = LudoPlayer("red",(9,55,-1,-1))
    green = LudoPlayer("green",(49,49,-1,-1))  # square 10 blockade
    m = match_with(red,green,die=3)
    assert 0 not in legal_tokens(m,0,3)
    assert 1 not in legal_tokens(m,0,3)  # 55 + 3 overshoots
    m = replace(m, die=1)
    assert 0 not in legal_tokens(m,0,1)
    assert 1 in legal_tokens(m,0,1)
    finished = apply_ludo_action(m,0,"move",token=1)
    assert finished.players[0].tokens[1] == 56


def test_winner_four_home_and_no_moves_after_win():
    m = match_with(LudoPlayer("red",(56,56,56,55)),
                   LudoPlayer("yellow",(-1,-1,-1,-1)),die=1)
    out = apply_ludo_action(m,0,"move",token=3)
    assert out.winner == 0
    with pytest.raises(IllegalLudoMove):
        apply_ludo_action(out,0,"roll")


def test_recovery_roundtrip():
    m = make_ludo_match(4,seed=1)
    m = apply_ludo_action(m,m.actor,"roll",forced_roll=6)
    restored = restore_ludo(dump_ludo(m))
    assert restored == m


def test_ludo_room_websocket_and_isolated_persistence(tmp_path):
    path=tmp_path/"rooms.db"
    with TestClient(create_app(db_path=path)) as client:
        create=client.post("/api/rooms",json={"capacity":2,"game_type":"ludo","name":"Africa"})
        assert create.status_code==201
        rid=create.json()["room_id"]
        other=client.post(f"/api/rooms/{rid}/join",json={"name":"Grad E"}).json()
        assert client.get(f"/api/rooms/{rid}").json()["game_type"]=="ludo"
        assert client.get("/ludo.js").status_code==200
        with client.websocket_connect(f"/ws/{rid}") as a:
            a.send_json({"type":"auth","token":create.json()["token"]})
            view=a.receive_json()
            a.send_json({"type":"ready","ready":True,"expected_version":view["version"],"request_id":"a-ready"})
            ready=a.receive_json()
            assert ready["players"][0]["ready"]
            with client.websocket_connect(f"/ws/{rid}") as b:
                b.send_json({"type":"auth","token":other["token"]})
                vb=b.receive_json()
                a.receive_json()
                b.send_json({"type":"ready","ready":True,"expected_version":vb["version"],"request_id":"b-ready"})
                match=b.receive_json()
                assert match["game_type"]=="ludo"
                assert match["game"]["phase"]=="PLAYING"
                assert match["game"]["game_type"]=="ludo"
                assert len(match["game"]["players"])==2
                assert client.get(f"/api/rooms/{rid}").json()["game"]["game_type"]=="ludo"
                # Reject cards in a Ludo room, even from an authorised seat.
                b.send_json({"type":"game","kind":"pickup","expected_version":match["version"],"request_id":"wrong-game"})
                err=b.receive_json()
                assert err["reasonCode"]=="wrong_game"
    with TestClient(create_app(db_path=path)) as client:
        public=client.get(f"/api/rooms/{rid}").json()
        assert public["game_type"]=="ludo"
        assert len(public["game"]["players"])==2
        raw=sqlite3.connect(path).execute("SELECT payload FROM rooms WHERE id=?",(rid,)).fetchone()[0]
        assert json.loads(raw)["match"] is None


def test_legacy_shithead_still_default():
    with TestClient(create_app()) as client:
        x=client.post("/api/rooms",json={"capacity":6,"name":"Africa"})
        assert x.status_code==201
        assert x.json()["game_type"]=="shithead"
        snap=client.get(f"/api/rooms/{x.json()['room_id']}").json()
        assert snap["game_type"]=="shithead"
        assert snap["game"] is None
        assert client.post("/api/rooms",json={"capacity":5,"game_type":"ludo"}).status_code==422
