"""Dara multiplayer contract without changing live engines."""
from fastapi.testclient import TestClient
from server.app.main import create_app


def send(ws, snapshot, action_type, request_id, **fields):
    ws.send_json({"type":action_type,"expected_version":snapshot["version"],
                  "request_id":request_id,**fields})


def test_dara_two_seat_ready_place_replay_and_restart(tmp_path):
    db=tmp_path/"dara_socket.db"
    with TestClient(create_app(db_path=db)) as client:
        a=client.post("/api/rooms",json={"name":"A","capacity":2,"game_type":"dara"}).json()
        b=client.post(f"/api/rooms/{a['room_id']}/join",json={"name":"B"}).json()
        with client.websocket_connect(f"/ws/{a['room_id']}") as wa:
            wa.send_json({"type":"auth","token":a["token"]})
            va=wa.receive_json()
            send(wa,va,"ready","ready-a",ready=True)
            va=wa.receive_json()
            with client.websocket_connect(f"/ws/{a['room_id']}") as wb:
                wb.send_json({"type":"auth","token":b["token"]})
                vb=wb.receive_json()
                va=wa.receive_json()
                send(wb,vb,"ready","ready-b",ready=True)
                vb=wb.receive_json()
                va=wa.receive_json()
                assert va["phase"]==vb["phase"]=="PLAYING"
                assert va["game"]["game_type"]=="dara"
                assert va["game"]["stage"]=="PLACE"
                send(wa,va,"dara","place-a",kind="place",index=0)
                va=wa.receive_json();vb=wb.receive_json()
                assert va["game"]["cells"][0]==1
                assert va["game"]["actor"]==1
                assert sum(va["game"]["placed"])==1
                send(wa,va,"dara","wrong-turn",kind="place",index=1)
                denied=wa.receive_json()
                assert denied["type"]=="error"
                assert denied["reasonCode"]=="illegal_action"
                send(wb,vb,"dara","place-b",kind="place",index=29)
                va=wa.receive_json();vb=wb.receive_json()
                assert va["game"]["cells"][29]==2
                send(wb,vb,"dara","place-b",kind="place",index=29)
                duplicate=wb.receive_json()
                assert duplicate["game"]["cells"]==vb["game"]["cells"]
                assert duplicate["version"]==vb["version"]
        with TestClient(create_app(db_path=db)) as recovered:
            data=recovered.get(f"/api/rooms/{a['room_id']}").json()
            assert data["game"]["placed"]==[1,1]
            with recovered.websocket_connect(f"/ws/{a['room_id']}") as ws:
                ws.send_json({"type":"auth","token":a["token"]})
                view=ws.receive_json()
                assert view["you"]==0
                assert view["game"]["cells"][0]==1
                assert view["game"]["cells"][29]==2


def test_dara_action_isolation_from_other_game_types(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"isolation.db")) as client:
        for game in ("shithead","ludo","awale"):
            created=client.post("/api/rooms",json={"name":"A","capacity":2,"game_type":game}).json()
            with client.websocket_connect(f"/ws/{created['room_id']}") as ws:
                ws.send_json({"type":"auth","token":created["token"]})
                snapshot=ws.receive_json()
                send(ws,snapshot,"dara","wrong-game",kind="place",index=0)
                denied=ws.receive_json()
                assert denied["type"]=="error"
                assert denied["reasonCode"] in ("wrong_game","wrong_phase")
