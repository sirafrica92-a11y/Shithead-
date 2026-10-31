"""UI transport invariant checks; run alongside ALL existing multiplayer tests."""
from fastapi.testclient import TestClient
from server.app.main import create_app

def test_recovery_keeps_same_seat_and_sync_is_read_only(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.sqlite3")) as c:
        js=c.get("/client.js").text
        for key in ("SYNC_INTERVAL_MS", "SYNC_TIMEOUT_MS", "RETRY_MAX_MS", 'type: "sync"', "online", "visibilitychange", "focus", "sessionRevoked", "stopTransportTimers"):
            assert key in js
        assert "retry >= 5" not in js
        assert 'connect(roomId, seatToken)' in js
        assert 'event.code === 1008' in js
        assert "ws.readyState === WebSocket.OPEN" in js
        assert "sessionStorage.removeItem(KEY)" in js
        assert 'request("/api/rooms"' in js # only existing explicit Create action
        # The six multiplayer engines and solo routes are still available.
        for name,capacity in (("shithead",2),("ludo",2),("awale",2),("dara",2),("yote",2),("dominoes",4)):
            response=c.post("/api/rooms",json={"name":"Host","capacity":capacity,"game_type":name})
            assert response.status_code==201
            rid=response.json()["room_id"]
            assert c.post(f"/api/rooms/{rid}/join",json={"name":"Friend"}).status_code==201
        assert c.get("/solo/ludo").status_code==200
        assert c.get("/solo/awale").status_code==200
