"""Dara Game 04 regression suite: rules, rooms, socket, and legacy safety."""
from dataclasses import replace
import random
import pytest
from fastapi.testclient import TestClient
from server.app.dara import (
    DaraMatch, make_dara_match, apply_dara_action, legal_dara_moves,
    assert_dara_invariants, dump_dara, restore_dara, IllegalDaraMove,
)
from server.app.main import create_app


def test_initial_board_and_placement():
    m=make_dara_match()
    assert m.phase=="PLACE" and m.actor==0
    assert len(m.cells)==30 and len(legal_dara_moves(m,0)["places"])==30
    m=apply_dara_action(m,0,"place",index=0)
    assert m.cells[0]==1 and m.placed==(1,0) and m.actor==1
    assert legal_dara_moves(m,0)["places"]==[]
    with pytest.raises(IllegalDaraMove):
        apply_dara_action(m,0,"place",index=1)


def test_placement_never_forms_three():
    m=DaraMatch(cells=(1,1,0)+(0,)*27,placed=(2,0),actor=0)
    assert 2 not in legal_dara_moves(m,0)["places"]
    with pytest.raises(IllegalDaraMove):
        apply_dara_action(m,0,"place",index=2)


def test_movement_capture_only_after_new_three():
    c=[0]*30
    for i in [0,2,8,10,12,13,15,17,19,22,24,27]:c[i]=1
    for i in [4,5,6,7,9,11,14,16,18,20,23,25]:c[i]=2
    m=DaraMatch(cells=tuple(c),placed=(12,12),phase="MOVE",actor=0)
    assert [8,1] in legal_dara_moves(m,0)["moves"]
    out=apply_dara_action(m,0,"move",source=8,destination=1)
    assert out.pending_capture and out.actor==0
    victims=legal_dara_moves(out,0)["captures"]
    assert victims
    end=apply_dara_action(out,0,"capture",index=victims[0])
    assert end.cells.count(2)==11 and end.actor==1 and not end.pending_capture
    assert_dara_invariants(end)


def test_illegal_non_adjacent_and_four_in_row():
    c=[0]*30;c[0]=c[1]=c[2]=1;c[4]=1
    m=DaraMatch(cells=tuple(c),placed=(12,12),phase="MOVE",actor=0)
    with pytest.raises(IllegalDaraMove):
        apply_dara_action(m,0,"move",source=4,destination=11)
    with pytest.raises(IllegalDaraMove):
        apply_dara_action(m,0,"move",source=4,destination=3)


def test_serialisation_and_legacy_games_created(tmp_path):
    m=make_dara_match()
    assert restore_dara(dump_dara(m))==m
    with TestClient(create_app(db_path=tmp_path/"rooms.db")) as app:
        assert app.get("/dara.js").status_code==200
        assert app.post("/api/rooms",json={"name":"A","game_type":"dara","capacity":3}).status_code==422
        for game,cap in (("shithead",6),("ludo",4),("awale",2),("dara",2)):
            r=app.post("/api/rooms",json={"name":"Player","game_type":game,"capacity":cap})
            assert r.status_code==201,(game,r.text)
            assert r.json()["game_type"]==game


def test_dara_80_random_complete_engine_games():
    for seed in range(80):
        rng=random.Random(seed)
        m=make_dara_match()
        for turn in range(1500):
            assert_dara_invariants(m)
            if m.finished:break
            legal=legal_dara_moves(m,m.actor)
            if legal["captures"]:
                m=apply_dara_action(m,m.actor,"capture",index=rng.choice(legal["captures"]))
            elif legal["places"]:
                m=apply_dara_action(m,m.actor,"place",index=rng.choice(legal["places"]))
            elif legal["moves"]:
                src,dst=rng.choice(legal["moves"])
                m=apply_dara_action(m,m.actor,"move",source=src,destination=dst)
            else:
                pytest.fail(f"Dara active game has no legal action: seed {seed}, turn {turn}, {m.phase}, {m.placed}")
        else:pytest.fail(f"Dara game never ended for seed {seed}")
        assert m.finished
        assert m.winner in (0,1,None)


def test_dara_website_includes_game_and_existing_logo(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"dara_html.db")) as app:
        html=app.get("/").text
        assert 'data-game="dara"' in html
        assert 'id="dara-board"' in html
        assert '/brand/shithead-logo.png' in html
        assert 'src="/dara.js"' in html
