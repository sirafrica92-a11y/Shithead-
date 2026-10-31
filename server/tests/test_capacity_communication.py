"""Capacity messaging is truthful, measurable, and never blocks existing rooms."""
from fastapi.testclient import TestClient
from server.app.main import create_app
from server.tests.test_owner_analytics import auth


def test_full_room_allocation_returns_actionable_503_without_fake_queue(monkeypatch, tmp_path):
    monkeypatch.setenv("SHITHEAD_ADMIN_PASSWORD", "a-strong-test-secret")
    path = tmp_path/"rooms.sqlite3"
    with TestClient(create_app(db_path=path)) as client:
        client.app.state.room_store.max_rooms = 1
        first = client.post("/api/rooms", json={"name":"A", "capacity":2, "game_type":"awale"})
        assert first.status_code == 201
        room = first.json()["room_id"]
        denied = client.post("/api/rooms", json={"name":"B", "capacity":2, "game_type":"awale"})
        assert denied.status_code == 503
        assert denied.headers["retry-after"] == "300"
        data = denied.json()["detail"]
        assert data["code"] == "room_capacity_reached"
        assert data["rooms_allocated"] == data["room_limit"] == 1
        assert "temporarily" in data["message"].lower()
        assert "waiting list" not in data["message"].lower()
        assert client.post(f"/api/rooms/{room}/join", json={"name":"Friend"}).status_code == 201
        assert client.get(f"/api/rooms/{room}").status_code == 200
        summary = client.get("/owner/api/analytics",headers=auth()).json()
        assert summary["overview"]["capacity_rejections"] == 1
        assert summary["live"]["rooms_in_memory"] == 1
        assert summary["live"]["room_limit"] == 1
        assert summary["daily"][-1]["capacity_rejections"] == 1
        owner_page = client.get("/owner/analytics", headers=auth()).text
        assert 'id="room-limit"' in owner_page
        assert 'id="allocated-rooms"' in owner_page
        assert summary["overview"]["rooms_created"] == 1
        assert summary["overview"]["players_joined"] == 2
        assert next(g for g in summary["games"] if g["key"] == "awale")["capacity_rejections"] == 1
        assert "capacity_rejections" in client.get("/owner/api/analytics.csv",headers=auth()).text
        assert client.get("/owner/api/analytics").status_code == 401
    with TestClient(create_app(db_path=path)) as again:
        summary = again.get("/owner/api/analytics",headers=auth()).json()
        assert summary["overview"]["capacity_rejections"] == 1
        again.app.state.room_store.max_rooms = 1
        assert again.post("/api/rooms",json={"capacity":2,"game_type":"yote","name":"C"}).status_code == 503
        assert again.get("/owner/api/analytics",headers=auth()).json()["overview"]["capacity_rejections"] == 2


def test_capacity_is_not_claimed_to_be_simultaneous_active_rooms(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"slots.db")) as client:
        store=client.app.state.room_store
        store.max_rooms=1
        assert client.post("/api/rooms",json={"name":"Host","capacity":2}).status_code == 201
        assert not any(s.socket is not None for r in store.rooms.values() for s in r.seats)
        res=client.post("/api/rooms",json={"name":"Another","capacity":2})
        assert res.status_code == 503
        assert res.json()["detail"]["rooms_allocated"] == 1
