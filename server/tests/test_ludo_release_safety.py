"""Release checks for Ludo in the shared room lifecycle."""
from dataclasses import replace
from fastapi.testclient import TestClient
from server.app.main import create_app
from server.app.ludo import make_ludo_match, LudoPlayer


def send(ws, view, action_type, request_id, **fields):
    ws.send_json(dict(type=action_type, request_id=request_id, expected_version=view['version'], **fields))
    return ws.receive_json()


def test_ludo_late_join_restart_finish_and_switch_preserves_seats(tmp_path):
    path = tmp_path/'rooms.db'
    app = create_app(db_path=path)
    with TestClient(app) as client:
        host = client.post('/api/rooms',json=dict(name='Host',capacity=2,game_type='ludo')).json()
        code = host['room_id']
        guest = client.post(f'/api/rooms/{code}/join',json=dict(name='Guest')).json()
        room = app.state.room_store.rooms[code]
        room.ludo = make_ludo_match(2, seed=1)
        late = client.post(f'/api/rooms/{code}/join',json=dict(name='Late')).json()
        assert late['waiting_next_match']
        assert room.view_for(2)['game']['is_spectator']
        with client.websocket_connect(f'/ws/{code}') as ws:
            ws.send_json(dict(type='auth',token=host['token']))
            view = ws.receive_json()
            assert view['pending_joiners'] == [2]
            view = send(ws,view,'host_join_decision','finish-first',decision='finish_current')
            assert len(view['game']['players']) == 2
            assert room.view_for(2)['game']['is_spectator']
        fourth = client.post(f'/api/rooms/{code}/join',json=dict(name='Fourth')).json()
        with client.websocket_connect(f'/ws/{code}') as ws:
            ws.send_json(dict(type='auth',token=host['token']))
            view = ws.receive_json()
            view = send(ws,view,'host_join_decision','restart',decision='restart_now')
            assert len(view['game']['players']) == 4
            assert not room.view_for(2)['game']['is_spectator']
            assert view['pending_joiners'] == []
            denied = send(ws,view,'return_lobby','no-abort')
            assert denied['reasonCode'] == 'wrong_phase'
            players = list(room.ludo.players)
            players[0] = LudoPlayer(players[0].color,(56,56,56,56))
            room.ludo = replace(room.ludo,players=tuple(players),winner=0,actor=0)
            view = send(ws,view,'return_lobby','finished-switch')
            assert view['phase'] == 'LOBBY'
            assert len(view['players']) == 4
            view = send(ws,view,'select_game','cards',game_type='shithead')
            assert view['game_type'] == 'shithead'
            assert not any(p['ready'] for p in view['players'])
    with TestClient(create_app(db_path=path)) as recovered:
        with recovered.websocket_connect(f'/ws/{code}') as ws:
            ws.send_json(dict(type='auth',token=guest['token']))
            view = ws.receive_json()
            assert view['you'] == 1
            assert view['game_type'] == 'shithead' and view['game'] is None
            assert len(view['players']) == 4


def test_ludo_die_is_server_owned_and_duplicate_roll_not_reapplied(monkeypatch):
    app = create_app()
    with TestClient(app) as client:
        host = client.post('/api/rooms',json=dict(name='Host',capacity=2,game_type='ludo')).json()
        code = host['room_id']
        client.post(f'/api/rooms/{code}/join',json=dict(name='Guest'))
        room = app.state.room_store.rooms[code]
        room.ludo = replace(make_ludo_match(2,seed=1),actor=0)
        monkeypatch.setattr('server.app.ludo.secrets.randbelow',lambda n: 0)
        with client.websocket_connect(f'/ws/{code}') as ws:
            ws.send_json(dict(type='auth',token=host['token']))
            view = ws.receive_json()
            rolled = send(ws,view,'ludo','roll-once',kind='roll',forced_roll=6,die=6)
            assert rolled['game']['last_roll'] == 1
            duplicate = send(ws,view,'ludo','roll-once',kind='roll',forced_roll=6)
            assert duplicate['version'] == rolled['version']
            assert duplicate['game'] == rolled['game']
