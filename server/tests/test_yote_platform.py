"""Yoté fifth-game rules and integration contracts."""
from dataclasses import replace
import random
import pytest
from fastapi.testclient import TestClient
from server.app.yote import (YoteMatch, make_yote_match, legal_yote_moves,
 apply_yote_action, assert_yote_invariants, restore_yote, dump_yote, IllegalYoteMove)
from server.app.main import create_app

def test_opening_placements_and_no_diagonal():
    m=make_yote_match()
    assert len(m.cells)==30 and m.reserves==(12,12)
    assert len(legal_yote_moves(m,0)["places"])==30
    m=apply_yote_action(m,0,"place",index=0)
    assert m.actor==1 and m.cells[0]==1 and m.reserves==(11,12)
    m=apply_yote_action(m,1,"place",index=29)
    assert [0,1] in legal_yote_moves(m,0)["steps"]
    assert [0,7] not in legal_yote_moves(m,0)["steps"]
    with pytest.raises(IllegalYoteMove):
        apply_yote_action(m,0,"move",source=0,destination=7)

def test_jump_and_bonus_capture():
    c=[0]*30;c[0]=1;c[1]=2;c[6]=2
    m=YoteMatch(cells=tuple(c),reserves=(11,10))
    assert [0,2,1] in legal_yote_moves(m,0)["jumps"]
    out=apply_yote_action(m,0,"jump",source=0,destination=2)
    assert out.pending_bonus and out.actor==0
    assert out.cells[1]==0 and out.cells[2]==1
    assert legal_yote_moves(out,0)["bonuses"]==[6]
    done=apply_yote_action(out,0,"bonus",index=6)
    assert not done.pending_bonus and done.cells[6]==0
    assert done.actor==1 and done.reserves==(11,10)

def test_illegal_actions_and_roundtrip():
    m=make_yote_match()
    for bad in (-1,31,"0",True):
        with pytest.raises(IllegalYoteMove):
            apply_yote_action(m,0,"place",index=bad)
    with pytest.raises(IllegalYoteMove):
        apply_yote_action(m,1,"place",index=0)
    assert restore_yote(dump_yote(m))==m

def test_many_complete_matches_conserve_piece_counts():
    for seed in range(65):
        rng=random.Random(seed)
        m=make_yote_match()
        for turn in range(1800):
            assert_yote_invariants(m)
            if m.finished:break
            legal=legal_yote_moves(m,m.actor)
            if legal["bonuses"]:
                m=apply_yote_action(m,m.actor,"bonus",index=rng.choice(legal["bonuses"]))
            elif legal["jumps"]:
                s,t,_=rng.choice(legal["jumps"])
                m=apply_yote_action(m,m.actor,"jump",source=s,destination=t)
            elif legal["places"] and (not legal["steps"] or rng.randrange(3)>0):
                m=apply_yote_action(m,m.actor,"place",index=rng.choice(legal["places"]))
            elif legal["steps"]:
                s,t=rng.choice(legal["steps"])
                m=apply_yote_action(m,m.actor,"move",source=s,destination=t)
            else:
                pytest.fail(f"active Yoté has no moves seed={seed}, turn={turn}")
        else:pytest.fail(f"Yoté does not finish seed={seed}")
        assert m.finished

def test_room_and_ui_creation_and_older_games(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"rooms.db")) as client:
        html=client.get("/").text
        assert 'data-game="yote"' in html and 'id="yote-board"' in html
        assert "/brand/shithead-logo.png" in html
        assert client.get("/yote.js").status_code==200
        assert client.post("/api/rooms",json={"name":"A","game_type":"yote","capacity":3}).status_code==422
        for game,cap in (("shithead",6),("ludo",4),("awale",2),("dara",2),("yote",2)):
            created=client.post("/api/rooms",json={"name":"A","game_type":game,"capacity":cap})
            assert created.status_code==201,created.text

def test_jump_removing_final_enemy_ends_instead_of_deadlock():
    c=[0]*30;c[0]=1;c[1]=2
    m=YoteMatch(cells=tuple(c),reserves=(0,0))
    out=apply_yote_action(m,0,"jump",source=0,destination=2)
    assert out.finished and out.winner==0
    assert not out.pending_bonus
