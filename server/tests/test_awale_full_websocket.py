"""Real two-seat Awalé over the existing, versioned WebSocket protocol.

Uses the same nested FastAPI TestClient technique already proven by Ludo's
integration suite. No monkeypatch of the authoritative match, dice or server.
"""
import random

from fastapi.testclient import TestClient
from server.app.main import create_app


def send(ws, version, kind, request_id, **extra):
    ws.send_json({"type": kind, "expected_version": version,
                  "request_id": request_id, **extra})


def test_two_seat_awale_full_match_rematch_and_restart_recovery(tmp_path):
    db = tmp_path / "awale_two_real_seats.db"
    with TestClient(create_app(db_path=db)) as client:
        host = client.post("/api/rooms", json={
            "name": "Host", "capacity": 2, "game_type": "awale"
        }).json()
        code = host["room_id"]
        guest = client.post(f"/api/rooms/{code}/join", json={"name": "Guest"}).json()

        with client.websocket_connect(f"/ws/{code}") as a:
            a.send_json({"type": "auth", "token": host["token"]})
            h = a.receive_json()
            assert h["you"] == 0 and h["phase"] == "LOBBY"
            send(a, h["version"], "ready", "ready-host", ready=True)
            h = a.receive_json()

            with client.websocket_connect(f"/ws/{code}") as b:
                b.send_json({"type": "auth", "token": guest["token"]})
                g = b.receive_json()
                h = a.receive_json()  # connected status broadcast
                assert h["version"] == g["version"]

                send(b, g["version"], "ready", "ready-guest", ready=True)
                g = b.receive_json()
                h = a.receive_json()
                assert h["phase"] == g["phase"] == "PLAYING"
                assert h["version"] == g["version"]
                assert h["game"]["pits"] == [4] * 12
                views = [h, g]
                sockets = [a, b]
                rng = random.Random(42)

                for turn in range(1500):
                    actor = views[0]["game"]["actor"]
                    assert actor == views[1]["game"]["actor"]
                    legal = views[actor]["game"]["your_legal_pits"]
                    assert legal, f"stalled on turn {turn}"
                    other = 1 - actor
                    assert not views[other]["game"]["your_legal_pits"]
                    chosen = rng.choice(legal)
                    before = views[actor]["version"]
                    send(sockets[actor], before, "awale", f"turn-{turn}",
                         kind="sow", pit=chosen)
                    views = [a.receive_json(), b.receive_json()]
                    assert all(x["type"] == "room_state" for x in views)
                    assert views[0]["version"] == views[1]["version"] == before + 1
                    assert views[0]["game"]["turn_number"] == turn + 1
                    for x in views:
                        assert sum(x["game"]["pits"]) + sum(x["game"]["captured"]) == 48
                    if views[0]["phase"] == "FINISHED":
                        break
                else:
                    raise AssertionError("The Awalé match did not finish")

                end = views[0]["game"]
                assert end["winner"] in (0, 1, None)
                assert end["turn_number"] > 10
                assert end["phase"] == "FINISHED"

                # Both players vote: the first vote may not restart alone.
                send(a, views[0]["version"], "rematch", "rematch-host")
                views = [a.receive_json(), b.receive_json()]
                assert views[0]["phase"] == "FINISHED"
                send(b, views[1]["version"], "rematch", "rematch-guest")
                views = [a.receive_json(), b.receive_json()]
                assert views[0]["phase"] == views[1]["phase"] == "PLAYING"
                assert views[0]["game"]["turn_number"] == 0
                assert views[1]["game"]["pits"] == [4] * 12
                restarted_version = views[0]["version"]

                # Duplicate request IDs must not apply a move twice.
                actor = views[0]["game"]["actor"]
                pit = views[actor]["game"]["your_legal_pits"][0]
                send(sockets[actor], restarted_version, "awale", "once-only",
                     kind="sow", pit=pit)
                views = [a.receive_json(), b.receive_json()]
                after_once = views[0]["game"]
                assert after_once["turn_number"] == 1
                send(sockets[actor], restarted_version, "awale", "once-only",
                     kind="sow", pit=pit)
                duplicate = sockets[actor].receive_json()
                assert duplicate["game"] == after_once
                assert duplicate["version"] == views[0]["version"]

        with TestClient(create_app(db_path=db)) as recovered:
            # The persisted room and guest token are still recoverable after
            # server restart; no new seat or re-deal occurs.
            snapshot = recovered.get(f"/api/rooms/{code}").json()
            assert snapshot["phase"] == "PLAYING"
            assert snapshot["game"]["turn_number"] == 1
            with recovered.websocket_connect(f"/ws/{code}") as ws:
                ws.send_json({"type": "auth", "token": guest["token"]})
                restored = ws.receive_json()
                assert restored["you"] == 1
                assert restored["game"]["turn_number"] == 1
                assert len(restored["players"]) == 2


def test_awale_actions_rejected_in_older_games(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "other.db")) as client:
        for game in ("shithead", "ludo"):
            host=client.post("/api/rooms", json={
                "name":"Owner", "capacity":2, "game_type":game
            }).json()
            with client.websocket_connect(f"/ws/{host['room_id']}") as ws:
                ws.send_json({"type":"auth","token":host["token"]})
                snapshot=ws.receive_json()
                send(ws, snapshot["version"], "awale", "not-my-game",
                     kind="sow", pit=0)
                rejected=ws.receive_json()
                assert rejected["type"] == "error"
                assert rejected["reasonCode"] in ("wrong_game", "wrong_phase")
