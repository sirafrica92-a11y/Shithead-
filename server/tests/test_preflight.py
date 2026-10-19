"""Preflight checks for browser assets and recoverable server protocol."""
from fastapi.testclient import TestClient
from server.app.main import create_app


def test_browser_client_script_reachable():
    with TestClient(create_app()) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert 'src="/client.js"' in response.text
        script = client.get("/client.js")
        assert script.status_code == 200
        assert "sessionStorage" in script.text
        assert "stateSnapshot" in script.text


def test_stale_version_returns_recoverable_private_snapshot():
    with TestClient(create_app()) as client:
        room = client.post("/api/rooms", json={"capacity":2}).json()["room_id"]
        a = client.post(f"/api/rooms/{room}/join", json={"name":"A"}).json()
        client.post(f"/api/rooms/{room}/join", json={"name":"B"})
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type": "auth", "token": a["token"]})
            state = ws.receive_json()
            ws.send_json({"type": "ready", "ready": True,
                          "expected_version": state["version"] - 1,
                          "request_id": "old-1"})
            err = ws.receive_json()
            assert err["type"] == "error"
            assert err["reasonCode"] == "stale_version"
            assert err["stateSnapshot"]["you"] == a["seat"]
            assert isinstance(err["allowedActions"], list)
            assert err["stateSnapshot"]["version"] >= state["version"]


def test_restoring_same_seat_does_not_add_another_player():
    with TestClient(create_app()) as client:
        room = client.post("/api/rooms", json={"capacity":2}).json()["room_id"]
        seat = client.post(f"/api/rooms/{room}/join", json={"name":"A"}).json()
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type": "auth", "token": seat["token"]})
            assert ws.receive_json()["you"] == seat["seat"]
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type": "auth", "token": seat["token"]})
            assert ws.receive_json()["you"] == seat["seat"]
        assert len(client.get(f"/api/rooms/{room}").json()["players"]) == 1
