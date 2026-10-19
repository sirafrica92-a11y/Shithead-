"""Public website, protected rooms, and private seat credentials."""
from fastapi.testclient import TestClient
from server.app.main import create_app
from server.app.lobby import RoomStore
import pytest

def test_website_and_js_are_public_without_site_password():
    with TestClient(create_app()) as client:
        assert client.get("/").status_code == 200
        assert client.get("/client.js").status_code == 200
        assert client.get("/health").json() == {"status":"ok"}

def test_password_protects_joins_but_not_the_website():
    with TestClient(create_app()) as client:
        create=client.post("/api/rooms",json={"capacity":2,"password":"correct-password"})
        assert create.status_code == 201
        room=create.json()["room_id"]
        public=client.get(f"/api/rooms/{room}").json()
        assert "password" not in str(public)
        assert client.post(f"/api/rooms/{room}/join",json={"name":"Bardia","password":"wrong-password"}).status_code == 403
        assert len(client.get(f"/api/rooms/{room}").json()["players"]) == 0
        ok=client.post(f"/api/rooms/{room}/join",json={"name":"Bardia","password":"correct-password"})
        assert ok.status_code == 201
        assert "token" in ok.json()
        assert "password" not in str(client.get(f"/api/rooms/{room}").json())

def test_room_password_generated_when_not_supplied():
    with TestClient(create_app()) as client:
        created=client.post("/api/rooms",json={"capacity":2}).json()
        assert len(created["room_password"]) >= 16
        room=created["room_id"]
        assert client.post(f"/api/rooms/{room}/join",json={"name":"Friend","password":"incorrect"}).status_code == 403
        assert client.post(f"/api/rooms/{room}/join",json={"name":"Friend","password":created["room_password"]}).status_code == 201
        assert "room_password" not in str(client.get(f"/api/rooms/{room}").json())

def test_password_is_not_saved_to_sqlite(tmp_path):
    path=tmp_path/"rooms.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        created=client.post("/api/rooms",json={"capacity":2,"password":"the-private-room-password"}).json()
        assert "the-private-room-password".encode() not in path.read_bytes()
    with TestClient(create_app(db_path=path)) as client:
        room=created["room_id"]
        assert client.post(f"/api/rooms/{room}/join",json={"name":"Alice","password":"the-private-room-password"}).status_code == 201

def test_legacy_rooms_fail_closed_when_no_room_password(tmp_path):
    path=tmp_path/"rooms.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        created=client.post("/api/rooms",json={"capacity":2}).json()
        room_id=created["room_id"]
    import sqlite3, json
    db=sqlite3.connect(path)
    record=db.execute("SELECT payload FROM rooms WHERE id=?",(room_id,)).fetchone()
    payload=json.loads(record[0]);payload.pop("password_salt",None);payload.pop("password_hash",None)
    db.execute("UPDATE rooms SET payload=? WHERE id=?",(json.dumps(payload),room_id));db.commit();db.close()
    with TestClient(create_app(db_path=path)) as client:
        assert client.post(f"/api/rooms/{room_id}/join",json={"name":"Alice","password":"whatever"}).status_code==403
