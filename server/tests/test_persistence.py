"""Local SQLite restart recovery and private seat authentication checks."""
from dataclasses import replace

from fastapi.testclient import TestClient

from server.app.gameplay import (
    apply_match_action, assert_card_conservation, make_match,
)
from server.app.main import create_app
from server.app.lobby import Room, RoomStore, Seat
from server.app.persistence import dump_match, restore_match, token_digest


def test_exact_match_serialization_with_pending_attack():
    m=make_match(3,seed=5)
    actor=m.state.current
    p=m.state.players[actor]
    cards=list(p.hand)
    cards[0]=replace(cards[0],rank=3)
    players=list(m.state.players)
    players[actor]=replace(p,hand=tuple(cards))
    pile_card=m.state.deck[0]
    m=replace(m,state=replace(m.state,players=tuple(players),
                               deck=m.state.deck[1:],pile=(pile_card,)))
    target=(actor+m.state.direction)%3
    m=apply_match_action(m,actor,"power",index=0,target=target)
    assert_card_conservation(m)
    restored=restore_match(dump_match(m))
    assert restored==m
    assert_card_conservation(restored)


def test_sqlite_restores_room_ready_state_and_seat_token(tmp_path):
    path=tmp_path/"game.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        room=client.post("/api/rooms",json={"capacity":2}).json()["room_id"]
        a=client.post(f"/api/rooms/{room}/join",json={"name":"A"}).json()
        b=client.post(f"/api/rooms/{room}/join",json={"name":"B"}).json()
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type":"auth","token":a["token"]})
            view=ws.receive_json()
            ws.send_json({"type":"ready","ready":True,
                          "expected_version":view["version"],"request_id":"one"})
            assert ws.receive_json()["players"][0]["ready"]
    assert path.exists()
    assert a["token"].encode() not in path.read_bytes()
    with TestClient(create_app(db_path=path)) as client:
        view=client.get(f"/api/rooms/{room}").json()
        assert len(view["players"])==2
        assert view["players"][0]["ready"]
        assert not view["players"][0]["connected"]
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type":"auth","token":a["token"]})
            assert ws.receive_json()["you"]==0
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type":"auth","token":b["token"]})
            assert ws.receive_json()["you"]==1


def test_started_match_restores_with_private_hand(tmp_path):
    path=tmp_path/"match.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        room=client.post("/api/rooms",json={"capacity":2}).json()["room_id"]
        a=client.post(f"/api/rooms/{room}/join",json={"name":"A"}).json()
        b=client.post(f"/api/rooms/{room}/join",json={"name":"B"}).json()
        with client.websocket_connect(f"/ws/{room}") as wa:
            wa.send_json({"type":"auth","token":a["token"]})
            va=wa.receive_json()
            with client.websocket_connect(f"/ws/{room}") as wb:
                wb.send_json({"type":"auth","token":b["token"]})
                vb=wb.receive_json()
                va=wa.receive_json()
                wa.send_json({"type":"ready","ready":True,
                              "expected_version":va["version"],"request_id":"a"})
                va=wa.receive_json()
                vb=wb.receive_json()
                wb.send_json({"type":"ready","ready":True,
                              "expected_version":vb["version"],"request_id":"b"})
                va=wa.receive_json()
                vb=wb.receive_json()
                assert va["phase"]=="PLAYING"
    with TestClient(create_app(db_path=path)) as client:
        view=client.get(f"/api/rooms/{room}").json()
        assert view["phase"]=="PLAYING"
        assert "hand" not in view["game"]
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type":"auth","token":a["token"]})
            aview=ws.receive_json()
            assert aview["game"]["you"]==0
            assert len(aview["game"]["hand"])==3
