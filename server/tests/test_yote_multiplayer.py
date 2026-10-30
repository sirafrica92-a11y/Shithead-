"""Yote multiplayer turn contract, replay protection, game isolation, SQLite recovery."""
from fastapi.testclient import TestClient
from server.app.main import create_app

def act(ws,view,action,id,**kwargs):
    ws.send_json({"type":action,"request_id":id,"expected_version":view["version"],**kwargs})

def test_yote_two_authenticated_players_place_then_reconnect(tmp_path):
    db=tmp_path/"yote_rooms.db"
    with TestClient(create_app(db_path=db)) as client:
        a=client.post("/api/rooms",json={"name":"Host","capacity":2,"game_type":"yote"}).json()
        b=client.post(f"/api/rooms/{a['room_id']}/join",json={"name":"Guest"}).json()
        with client.websocket_connect(f"/ws/{a['room_id']}") as wa:
            wa.send_json({"type":"auth","token":a["token"]});va=wa.receive_json()
            act(wa,va,"ready","ready-a",ready=True);va=wa.receive_json()
            with client.websocket_connect(f"/ws/{a['room_id']}") as wb:
                wb.send_json({"type":"auth","token":b["token"]});vb=wb.receive_json();va=wa.receive_json()
                act(wb,vb,"ready","ready-b",ready=True);vb=wb.receive_json();va=wa.receive_json()
                assert va["phase"]==vb["phase"]=="PLAYING"
                assert va["game"]["game_type"]=="yote"
                act(wa,va,"yote","place-0",kind="place",index=0)
                va=wa.receive_json();vb=wb.receive_json()
                assert va["game"]["cells"][0]==1 and va["game"]["reserves"]==[11,12]
                assert va["game"]["actor"]==1
                act(wa,va,"yote","badturn",kind="place",index=2)
                refused=wa.receive_json()
                assert refused["type"]=="error" and refused["reasonCode"]=="illegal_action"
                act(wb,vb,"yote","place-29",kind="place",index=29)
                va=wa.receive_json();vb=wb.receive_json()
                assert vb["game"]["cells"][29]==2
                act(wb,vb,"yote","place-29",kind="place",index=29)
                replay=wb.receive_json()
                assert replay["game"]["cells"]==vb["game"]["cells"]
                assert replay["version"]==vb["version"]
    with TestClient(create_app(db_path=db)) as restored:
        view=restored.get(f"/api/rooms/{a['room_id']}").json()
        assert view["game"]["reserves"]==[11,11]
        with restored.websocket_connect(f"/ws/{a['room_id']}") as ws:
            ws.send_json({"type":"auth","token":b["token"]});v=ws.receive_json()
            assert v["you"]==1 and v["game"]["cells"][0]==1

def test_yote_not_dispatched_to_previous_four_games(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"legacy.db")) as client:
        for kind in ("shithead","ludo","awale","dara"):
            a=client.post("/api/rooms",json={"name":"A","capacity":2,"game_type":kind}).json()
            with client.websocket_connect(f"/ws/{a['room_id']}") as ws:
                ws.send_json({"type":"auth","token":a["token"]});v=ws.receive_json()
                act(ws,v,"yote","wrong-game",kind="place",index=0)
                denied=ws.receive_json()
                assert denied["type"]=="error"
                assert denied["reasonCode"] in ("wrong_game","wrong_phase")
