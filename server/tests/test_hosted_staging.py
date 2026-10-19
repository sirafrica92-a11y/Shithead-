"""Public website, open rooms, private seat credentials.

Rooms are reachable by code alone; nothing here may reintroduce a site
password or a room password, and a seat must stay private to its token.
"""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from server.app.main import create_app
from server.app.persistence import token_digest


def test_website_and_js_are_public_without_site_password():
    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 200
        assert client.get("/client.js").status_code == 200
        assert client.get("/health").json() == {"status": "ok"}


def test_joining_needs_only_a_name_and_the_code():
    with TestClient(create_app()) as client:
        created = client.post("/api/rooms", json={"capacity": 2})
        assert created.status_code == 201
        body = created.json()
        # Creating a room must not hand back any shared secret.
        assert "room_password" not in body and "password" not in str(body)
        room = body["room_id"]
        joined = client.post(f"/api/rooms/{room}/join", json={"name": "Bardia"})
        assert joined.status_code == 201
        assert "token" in joined.json()


def test_no_password_field_is_required_or_accepted_anywhere():
    with TestClient(create_app()) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        # A stray password from an old client is ignored, never a second step.
        assert client.post(f"/api/rooms/{room}/join",
                           json={"name": "Alice", "password": "anything"}).status_code == 201
        public = client.get(f"/api/rooms/{room}").json()
        assert "password" not in str(public)


def test_seat_token_never_appears_in_a_public_snapshot():
    with TestClient(create_app()) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        token = client.post(f"/api/rooms/{room}/join", json={"name": "A"}).json()["token"]
        public = client.get(f"/api/rooms/{room}").json()
        assert token not in str(public)
        assert "token" not in str(public)


def test_a_wrong_seat_token_cannot_take_a_seat():
    with TestClient(create_app()) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        client.post(f"/api/rooms/{room}/join", json={"name": "A"})
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect(f"/ws/{room}") as ws:
                ws.send_json({"type": "auth", "token": "not-the-right-token"})
                ws.receive_json()


def test_rooms_and_seat_tokens_survive_a_restart(tmp_path):
    path = tmp_path / "rooms.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        token = client.post(f"/api/rooms/{room}/join", json={"name": "Alice"}).json()["token"]
    with TestClient(create_app(db_path=path)) as client:
        assert len(client.get(f"/api/rooms/{room}").json()["players"]) == 1
        with client.websocket_connect(f"/ws/{room}") as ws:
            ws.send_json({"type": "auth", "token": token})
            assert ws.receive_json()["you"] == 0


def test_no_password_material_is_written_to_sqlite(tmp_path):
    path = tmp_path / "rooms.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        client.post(f"/api/rooms/{room}/join", json={"name": "Alice"})
    payload = sqlite3.connect(path).execute(
        "SELECT payload FROM rooms WHERE id=?", (room,)).fetchone()[0]
    stored = json.loads(payload)
    assert "password_salt" not in stored and "password_hash" not in stored


def test_rooms_saved_before_the_change_stay_joinable(tmp_path):
    """A room written by the password build keeps its id, seats and tokens.

    Those rooms previously failed closed; with passwords gone the code alone
    is enough, and the stored password material is ignored and dropped.
    """
    path = tmp_path / "rooms.sqlite3"
    legacy_id = "xQ7mK2pLz9A"           # old secrets.token_urlsafe(9) style id
    legacy = {
        "capacity": 2, "version": 3,
        "password_salt": "a1" * 16, "password_hash": "b2" * 32,
        "seats": [{"name": "Alice", "token_digest": token_digest("legacy-seat-token"),
                   "ready": False, "request_ids": []}],
        "match": None,
    }
    db = sqlite3.connect(path)
    db.execute("CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
    db.execute("INSERT INTO rooms (id, payload) VALUES (?, ?)",
               (legacy_id, json.dumps(legacy)))
    db.commit()
    db.close()

    with TestClient(create_app(db_path=path)) as client:
        snapshot = client.get(f"/api/rooms/{legacy_id}")
        assert snapshot.status_code == 200
        assert snapshot.json()["players"][0]["name"] == "Alice"
        # The preserved seat token still authenticates its original seat.
        with client.websocket_connect(f"/ws/{legacy_id}") as ws:
            ws.send_json({"type": "auth", "token": "legacy-seat-token"})
            assert ws.receive_json()["you"] == 0
        # And a second player can now take the free seat with the code alone.
        assert client.post(f"/api/rooms/{legacy_id}/join",
                           json={"name": "Bob"}).status_code == 201
