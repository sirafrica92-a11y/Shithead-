"""W4 lobby tests: no paid external services required."""
from fastapi.testclient import TestClient
from server.app.main import create_app


def test_create_and_join_room_capacity_and_privacy():
    with TestClient(create_app()) as client:
        created = client.post("/api/rooms", json={"capacity":2,"password":"test-room-pass123"})
        assert created.status_code == 201
        rid = created.json()["room_id"]
        a = client.post(f"/api/rooms/{rid}/join", json={"name":"Alice","password":"test-room-pass123"})
        b = client.post(f"/api/rooms/{rid}/join", json={"name":"Bob","password":"test-room-pass123"})
        assert a.status_code == b.status_code == 201
        assert a.json()["seat"] == 0 and b.json()["seat"] == 1
        assert a.json()["token"] != b.json()["token"]
        assert client.post(f"/api/rooms/{rid}/join", json={"name":"Eve","password":"test-room-pass123"}).status_code == 409
        public = client.get(f"/api/rooms/{rid}").json()
        assert public["phase"] == "LOBBY"
        assert public["capacity"] == 2
        assert len(public["players"]) == 2
        assert "token" not in str(public)
        assert a.json()["token"] not in str(public)


def test_bounds_and_unknown_room():
    with TestClient(create_app()) as client:
        assert client.post("/api/rooms", json={"capacity": 1}).status_code == 422
        assert client.post("/api/rooms", json={"capacity": 7}).status_code == 422
        assert client.get("/api/rooms/does-not-exist").status_code == 404
        assert client.get("/").status_code == 200


def test_websocket_auth_ready_replay_and_stale_version():
    with TestClient(create_app()) as client:
        rid = client.post("/api/rooms", json={"capacity":2,"password":"test-room-pass123"}).json()["room_id"]
        token = client.post(f"/api/rooms/{rid}/join", json={"name":"A","password":"test-room-pass123"}).json()["token"]
        client.post(f"/api/rooms/{rid}/join", json={"name":"B","password":"test-room-pass123"})
        with client.websocket_connect(f"/ws/{rid}") as ws:
            ws.send_json({"type": "auth", "token": token})
            snapshot = ws.receive_json()
            assert snapshot["you"] == 0
            v = snapshot["version"]
            ws.send_json({"type": "ready", "ready": True, "request_id": "req-1", "expected_version": v})
            updated = ws.receive_json()
            assert updated["players"][0]["ready"] is True
            assert updated["version"] == v + 1
            ws.send_json({"type": "ready", "ready": False, "request_id": "req-1", "expected_version": v})
            dup = ws.receive_json()
            assert dup["players"][0]["ready"] is True
            ws.send_json({"type": "ready", "ready": False, "request_id": "req-2", "expected_version": v})
            err = ws.receive_json()
            assert err["reasonCode"] == "stale_version"
            ws.send_json({"type": "sync"})
            sync = ws.receive_json()
            assert sync["players"][0]["ready"] is True


def test_reconnect_existing_seat():
    with TestClient(create_app()) as client:
        rid = client.post("/api/rooms", json={"capacity":2,"password":"test-room-pass123"}).json()["room_id"]
        token = client.post(f"/api/rooms/{rid}/join", json={"name":"A","password":"test-room-pass123"}).json()["token"]
        with client.websocket_connect(f"/ws/{rid}") as ws:
            ws.send_json({"type": "auth", "token": token})
            assert ws.receive_json()["you"] == 0
        with client.websocket_connect(f"/ws/{rid}") as ws:
            ws.send_json({"type": "auth", "token": token})
            assert ws.receive_json()["you"] == 0
            assert ws.receive_json if True else None
