"""Review regressions for room switching, security, and Ludo turn logic."""
from dataclasses import replace

from fastapi.testclient import TestClient

from server.app.ludo import (
    LudoPlayer, make_ludo_match, apply_ludo_action, legal_tokens, IllegalLudoMove,
)
from server.app.main import create_app


def send(ws, snapshot, action, request_id):
    ws.send_json({"expected_version": snapshot["version"], "request_id": request_id, **action})
    return ws.receive_json()


def test_game_change_and_capacity_without_legacy_shithead_regression(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.db")) as client:
        created = client.post("/api/rooms", json={"capacity": 2, "name": "Host"}).json()
        code = created["room_id"]
        friend = client.post(f"/api/rooms/{code}/join", json={"name": "Friend"}).json()
        with client.websocket_connect(f"/ws/{code}") as host:
            host.send_json({"type": "auth", "token": created["token"]})
            first = host.receive_json()
            changed = send(host, first, {"type": "select_game", "game_type": "ludo"}, "change-to-ludo")
            assert changed["game_type"] == "ludo"
            assert changed["capacity"] == 2
            expanded = send(host, changed, {"type": "set_capacity", "capacity": 4}, "four-players")
            assert expanded["capacity"] == 4
            denied = send(host, expanded, {"type": "set_capacity", "capacity": 5}, "exceed-ludo")
            assert denied["reasonCode"] == "invalid_capacity"
            changed = send(host, expanded, {"type": "select_game", "game_type": "shithead"}, "change-to-cards")
            assert changed["game_type"] == "shithead"
            expanded = send(host, changed, {"type": "set_capacity", "capacity": 6}, "six-players")
            assert expanded["capacity"] == 6
            # The host cannot shrink a room below the number already seated.
            denied = send(host, expanded, {"type": "set_capacity", "capacity": 1}, "bad-shrink")
            assert denied["reasonCode"] == "invalid_capacity"
        with client.websocket_connect(f"/ws/{code}") as guest:
            guest.send_json({"type": "auth", "token": friend["token"]})
            first = guest.receive_json()
            denied = send(guest, first, {"type": "select_game", "game_type": "ludo"}, "guest-switch")
            assert denied["reasonCode"] == "host_only"
            denied = send(guest, first, {"type": "set_capacity", "capacity": 2}, "guest-capacity")
            assert denied["reasonCode"] == "host_only"


def test_player_cannot_choose_their_own_die_or_skip_move(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.db")) as client:
        created = client.post("/api/rooms", json={"capacity": 2, "game_type": "ludo", "name": "Host"}).json()
        code=created["room_id"]
        guest=client.post(f"/api/rooms/{code}/join",json={"name":"Guest"}).json()
        room=client.app.state.room_store.rooms[code]
        match=make_ludo_match(2,seed=2)
        room.ludo=replace(match, actor=0,stage="MOVE",die=6)
        room.version+=1
        with client.websocket_connect(f"/ws/{code}") as host:
            host.send_json({"type": "auth", "token": created["token"]})
            view=host.receive_json()
            assert view["game"]["your_legal_tokens"] == [0,1,2,3]
            denied=send(host,view,{"type":"ludo","kind":"roll","forced_roll":6}, "cannot-double-roll")
            assert denied["reasonCode"]=="illegal_action"
            view=host.receive_json() if denied.get("type")=="room_state" else view
            advanced=send(host,view,{"type":"ludo","kind":"move","token":0}, "one-token-moved")
            assert advanced["game"]["players"][0]["tokens"][0]==0
            assert advanced["game"]["turn_stage"]=="ROLL"
            assert advanced["game"]["actor"]==0
            rolled=send(host,advanced,{"type":"ludo","kind":"roll","forced_roll":6}, "cannot-force-die")
            assert rolled["game"]["last_roll"] in (1,2,3,4,5,6)
            assert "forced_roll" not in rolled["game"]


def test_blockade_and_safe_haven_with_four_players():
    match=make_ludo_match(4,seed=1)
    assert len(match.players)==4
    players=list(match.players)
    players[0]=LudoPlayer("red",(1,-1,-1,-1))
    players[1]=LudoPlayer("green",(41,41,-1,-1)) # global square 2
    match=replace(match,players=tuple(players),actor=0,stage="MOVE",die=2)
    assert 0 not in legal_tokens(match,0,2)
    # A player may move any of their own tokens across their own blockade.
    players[1]=LudoPlayer("green",(-1,-1,-1,-1))
    players[0]=LudoPlayer("red",(1,2,2,-1))
    match=replace(match,players=tuple(players))
    assert 0 in legal_tokens(match,0,2)
