"""Late joins do not change a running match; only its creator chooses restart."""
from dataclasses import replace

from fastapi.testclient import TestClient

from server.app.main import create_app
from server.app.gameplay import make_match
from server.app.persistence import dump_match


def _started_room(client):
    host = client.post("/api/rooms", json={"capacity": 2, "name": "Africa"}).json()
    friend = client.post(f"/api/rooms/{host['room_id']}/join", json={"name": "Bardia"}).json()
    room = client.app.state.room_store.rooms[host["room_id"]]
    room.match = make_match(2, seed=7)
    room.version += 1
    return host, friend, room


def _send(ws, view, type_, **payload):
    ws.send_json({"type": type_, "expected_version": view["version"],
                  "request_id": f"{type_}-{view['version']}", **payload})
    return ws.receive_json()


def test_join_does_not_touch_live_game_and_only_host_can_restart(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "game.db")) as client:
        host, friend, room = _started_room(client)
        before = dump_match(room.match)
        newcomer = client.post(f"/api/rooms/{host['room_id']}/join",
                              json={"name": "Cleo"})
        assert newcomer.status_code == 201
        assert newcomer.json()["waiting_next_match"]
        assert dump_match(room.match) == before
        assert room.capacity == 3
        assert room.pending_joiners == [2]
        with client.websocket_connect(f"/ws/{host['room_id']}") as guest:
            guest.send_json({"type": "auth", "token": newcomer.json()["token"]})
            waiting = guest.receive_json()
            assert waiting["game"]["is_spectator"]
            assert "hand" not in waiting["game"]
            rejected = _send(guest, waiting, "game", kind="play", indices=[0])
            assert rejected["reasonCode"] == "waiting_next_match"
            assert dump_match(room.match) == before
            rejected = _send(guest, waiting, "host_join_decision", decision="restart_now")
            assert rejected["reasonCode"] == "host_only"
            with client.websocket_connect(f"/ws/{host['room_id']}") as owner:
                owner.send_json({"type": "auth", "token": host["token"]})
                current = owner.receive_json()
                decision = _send(owner, current, "host_join_decision", decision="restart_now")
                assert decision["game"]["phase"] == "PLAYING"
                assert decision["active_player_count"] == 3
                assert not decision["pending_joiners"]
                assert room.match != before
                assert len(room.match.state.players) == 3


def test_finish_current_preserves_game_until_rematch(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "game.db")) as client:
        host, friend, room = _started_room(client)
        third = client.post(f"/api/rooms/{host['room_id']}/join",
                            json={"name": "Cleo"}).json()
        before = dump_match(room.match)
        with client.websocket_connect(f"/ws/{host['room_id']}") as owner:
            owner.send_json({"type": "auth", "token": host["token"]})
            current = owner.receive_json()
            after = _send(owner, current, "host_join_decision", decision="finish_current")
            assert after["pending_joiners"] == []
            assert dump_match(room.match) == before
            assert after["active_player_count"] == 2
            # Settle a small terminal fixture; voting must include the newcomer.
            st = room.match.state
            players = list(st.players)
            players[0] = replace(players[0], hand=(), face_up=(), face_down=())
            room.match = replace(room.match, state=replace(st, players=tuple(players),
                            deck=(), finished=(0,)))
            room.version += 1
            owner.send_json({"type": "sync"})
            current = owner.receive_json()
            a = _send(owner, current, "rematch")
            assert a["rematch_votes"] == [0]
            with client.websocket_connect(f"/ws/{host['room_id']}") as guest:
                guest.send_json({"type": "auth", "token": third["token"]})
                current = guest.receive_json()
                # Host and third both vote, but Bardia still holds the last vote.
                _send(guest, current, "rematch")
                assert len(room.rematch_votes) == 2
                with client.websocket_connect(f"/ws/{host['room_id']}") as other:
                    other.send_json({"type": "auth", "token": friend["token"]})
                    current = other.receive_json()
                    done = _send(other, current, "rematch")
                    assert done["game"]["phase"] == "PLAYING"
                    assert done["active_player_count"] == 3
                    assert [p["name"] for p in done["players"]] == [
                        "Africa", "Bardia", "Cleo"
                    ]


def test_room_capacity_six_and_private_restart_state_persists(tmp_path):
    path = tmp_path / "rooms.db"
    with TestClient(create_app(db_path=path)) as client:
        host, _, room = _started_room(client)
        for name in ("Cleo", "Dara", "Ed", "Faye"):
            assert client.post(f"/api/rooms/{host['room_id']}/join",
                               json={"name": name}).status_code == 201
        assert client.post(f"/api/rooms/{host['room_id']}/join",
                           json={"name": "Seventh"}).status_code == 409
        snapshot = client.get(f"/api/rooms/{host['room_id']}").json()
        assert snapshot["pending_joiners"] == [2, 3, 4, 5]
        assert snapshot["host_seat"] == 0
        room_id = room.id
    with TestClient(create_app(db_path=path)) as restored:
        snapshot = restored.get(f"/api/rooms/{room_id}").json()
        assert snapshot["pending_joiners"] == [2, 3, 4, 5]
        assert snapshot["active_player_count"] == 2
        assert snapshot["host_seat"] == 0
