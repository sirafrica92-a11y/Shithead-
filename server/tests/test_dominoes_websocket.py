"""Four authenticated partner players across the actual room/WebSocket protocol."""
import random
from fastapi.testclient import TestClient

from server.app.main import create_app


def send(ws, view, action_type, request_id, **extra):
    ws.send_json({"type":action_type,"expected_version":view["version"],
                  "request_id":request_id,**extra})


def test_four_authenticated_seats_private_hands_turns_and_restore(tmp_path):
    db=tmp_path/"dominoes_ws.db"
    with TestClient(create_app(db_path=db)) as app:
        h=app.post("/api/rooms",json={"capacity":4,"game_type":"dominoes","name":"Seat0"}).json()
        code=h["room_id"]
        tokens=[h["token"]]
        for i in range(1,4):
            joined=app.post(f"/api/rooms/{code}/join",json={"name":f"Seat{i}"}).json()
            tokens.append(joined["token"])
        with app.websocket_connect(f"/ws/{code}") as a:
            a.send_json({"type":"auth","token":tokens[0]})
            v0=a.receive_json()
            with app.websocket_connect(f"/ws/{code}") as b:
                b.send_json({"type":"auth","token":tokens[1]})
                v1=b.receive_json();v0=a.receive_json()
                with app.websocket_connect(f"/ws/{code}") as c:
                    c.send_json({"type":"auth","token":tokens[2]})
                    v2=c.receive_json();v0=a.receive_json();v1=b.receive_json()
                    with app.websocket_connect(f"/ws/{code}") as d:
                        d.send_json({"type":"auth","token":tokens[3]})
                        v3=d.receive_json()
                        v0=a.receive_json();v1=b.receive_json();v2=c.receive_json()
                        webs=[a,b,c,d];views=[v0,v1,v2,v3]
                        for i in range(4):
                            send(webs[i],views[i],"ready",f"ready-{i}",ready=True)
                            views=[ws.receive_json() for ws in webs]
                        assert all(x["phase"]=="PLAYING" for x in views)
                        assert len({tuple(b) for x in views for b in x["game"]["hand"]})>=7
                        assert len({tuple(b) for x in views for b in x["game"]["hand"]})==28
                        assert all(x["game"]["hand_counts"]==[7]*4 for x in views)
                        assert all("hands" not in x["game"] for x in views)
                        # Seat zero must not receive seat one's private tiles.
                        for i in range(4):
                            assert views[i]["game"]["hand"]!=views[(i+1)%4]["game"]["hand"]
                            assert views[i]["game"]["legal"]["plays"]==(
                                [] if views[i]["game"]["actor"]!=i else views[i]["game"]["legal"]["plays"])
                        rng=random.Random(10)
                        for turn in range(100):
                            actor=views[0]["game"]["actor"]
                            legal=views[actor]["game"]["legal"]
                            old=views[actor]["version"]
                            if views[0]["game"]["stage"]=="HAND_OVER":
                                # Team that won (if any) poses the next hand.
                                seat=next(i for i,x in enumerate(views) if x["game"]["legal"]["next_hand"])
                                actor=seat
                                send(webs[seat],views[seat],"dominoes",f"deal-{turn}",kind="next_hand")
                            elif legal["pass"]:
                                send(webs[actor],views[actor],"dominoes",f"pass-{turn}",kind="pass")
                            else:
                                play=rng.choice(legal["plays"])
                                send(webs[actor],views[actor],"dominoes",f"play-{turn}",
                                     kind="play",index=play["index"],side=rng.choice(play["sides"]))
                            views=[ws.receive_json() for ws in webs]
                            assert all(x["version"]==old+1 for x in views)
                            assert all(x["game"]["hand_counts"]==views[0]["game"]["hand_counts"] for x in views)
                            assert all("hand" in x["game"] for x in views)
                            if views[0]["phase"]=="FINISHED":break
                        public=app.get(f"/api/rooms/{code}").json()
                        assert "hand" not in public["game"]
                        # Invalid cross-game actions must never alter the match.
                        send(a,views[0],"ludo","wrong-type",kind="roll")
                        error=a.receive_json()
                        assert error["type"]=="error" and error["reasonCode"]=="wrong_game"
    with TestClient(create_app(db_path=db)) as restarted:
        public=restarted.get(f"/api/rooms/{code}").json()
        assert public["game_type"]=="dominoes" and public["game"] is not None
        assert "hand" not in public["game"]
        with restarted.websocket_connect(f"/ws/{code}") as ws:
            ws.send_json({"type":"auth","token":tokens[2]})
            recovered=ws.receive_json()
            assert recovered["you"]==2
            assert "hand" in recovered["game"]
            assert len(recovered["game"]["hand"])==recovered["game"]["hand_counts"][2]
