"""D-023: a player may conceal a legal Jack and voluntarily collect the pile.

Exercise the exact game->WebSocket->authoritative-match path, not just W3.
No production service, database or other game is changed.
"""
from fastapi.testclient import TestClient

from server.app.gameplay import Match
from server.app.main import create_app
from server.app.rules.ordinary import Card, OrdinaryState, PlayerState


def test_pickup_while_holding_matching_card_moves_pile_and_turn():
    app = create_app()
    with TestClient(app) as client:
        host = client.post("/api/rooms", json={"name": "A", "capacity": 2}).json()
        code = host["room_id"]
        guest = client.post(f"/api/rooms/{code}/join", json={"name": "B"}).json()
        assert guest["seat"] == 1

        # Reduced, deterministic state: A holds a playable Jack against a
        # different Jack on the pile. The player chooses not to reveal theirs.
        room = app.state.room_store.rooms[code]
        room.match = Match(state=OrdinaryState(
            players=(
                PlayerState(hand=(Card(11, "S", "held-jack"),)),
                PlayerState(hand=(Card(8, "C", "opponent-eight"),)),
            ),
            pile=(Card(11, "H", "pile-jack"),),
            current=0,
        ))

        with client.websocket_connect(f"/ws/{code}") as ws:
            ws.send_json({"type": "auth", "token": host["token"]})
            before = ws.receive_json()
            assert before["you"] == 0
            assert before["game"]["actor"] == 0
            assert before["game"]["hand"][0]["rank"] == 11
            assert before["game"]["pile"][0]["rank"] == 11

            ws.send_json({
                "type": "game", "kind": "pickup",
                "expected_version": before["version"],
                "request_id": "voluntary-jack-pickup",
            })
            after = ws.receive_json()
            assert after["type"] == "room_state"
            assert after["version"] == before["version"] + 1
            assert after["game"]["actor"] == 1
            assert after["game"]["pile"] == []
            assert [c["id"] for c in after["game"]["hand"]] == [
                "held-jack", "pile-jack",
            ]
            assert after["game"]["players"][1]["hand_count"] == 1
            assert "hand" not in after["game"]["players"][1]

            ws.send_json({"type": "sync"})
            restored = ws.receive_json()
            assert restored["version"] == after["version"]
            assert restored["game"]["hand"] == after["game"]["hand"]
            assert restored["game"]["pile"] == []
