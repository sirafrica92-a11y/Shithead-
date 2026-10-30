"""Jamaican Dominoes six-game isolation, rules and recovery contracts."""
from dataclasses import replace
import random

import pytest
from fastapi.testclient import TestClient

from server.app.dominoes import (
    make_domino_match, apply_domino_action, legal_domino_actions, dump_domino,
    restore_domino, public_domino_view, private_domino_view,
    assert_domino_invariants, IllegalDominoMove, ALL_BONES, _end_hand,
)
from server.app.main import create_app


def action(m, seat, rng):
    legal = legal_domino_actions(m, seat)
    if legal["next_hand"]:
        return apply_domino_action(m, seat, "next_hand")
    if legal["pass"]:
        return apply_domino_action(m, seat, "pass")
    plays=legal["plays"]
    assert plays, f"Missing legal play for seat {seat}"
    chosen=rng.choice(plays)
    return apply_domino_action(m,seat,"play",index=chosen["index"],
                               side=rng.choice(chosen["sides"]))


def test_initial_deal_is_complete_and_private():
    m=make_domino_match(seed=8)
    assert len(m.hands)==4
    assert all(len(hand)==7 for hand in m.hands)
    assert set(b for hand in m.hands for b in hand)==set(ALL_BONES)
    assert m.hands[m.actor].count((6,6))==1
    assert legal_domino_actions(m,m.actor)["plays"]==[
        {"index":m.hands[m.actor].index((6,6)),"sides":["left"]}
    ]
    public=public_domino_view(m)
    assert "hand" not in public and "hands" not in public
    assert "hand" not in public_domino_view(m)
    for seat in range(4):
        view=private_domino_view(m,seat)
        assert view["hand"]==[list(t) for t in m.hands[seat]]
        assert "hands" not in view


def test_wrong_turn_illegal_pass_and_invalid_side_rejected():
    m=make_domino_match(seed=3)
    with pytest.raises(IllegalDominoMove):
        apply_domino_action(m,(m.actor+1)%4,"play",index=0,side="left")
    with pytest.raises(IllegalDominoMove):
        apply_domino_action(m,m.actor,"pass")
    tile_index=m.hands[m.actor].index((6,6))
    with pytest.raises(IllegalDominoMove):
        apply_domino_action(m,m.actor,"play",index=tile_index,side="right")
    m=apply_domino_action(m,m.actor,"play",index=tile_index,side="left")
    assert m.chain==((6,6),) and m.left_end==m.right_end==6
    assert_domino_invariants(m)
    assert restore_domino(dump_domino(m))==m


def test_sixty_random_games_preserve_rules_and_seed_conservation():
    # Winning Six Love needs an uninterrupted streak. A legitimate match may
    # stay live past 2,000 actions; this is a bounded invariant soak, not a
    # guaranteed termination test.
    completed=0
    for seed in range(60):
        rng=random.Random(seed)
        m=make_domino_match(seed=seed)
        for turn in range(2000):
            assert_domino_invariants(m)
            assert sum(map(len,m.hands))+len(m.chain)==28
            if m.stage=="FINISHED":
                break
            if m.stage=="PLAYING":
                seat=m.actor
            else:
                seat=m.next_pose_team if m.next_pose_team is not None else 0
            m=action(m,seat,rng)
        assert_domino_invariants(m)
        if m.stage=="FINISHED":
            completed+=1
            assert m.winner_team in (0,1)
            assert max(m.scores)>=6
        else:
            assert m.winner_team is None
            assert max(m.scores)<6
    assert completed >= 10, f"Unexpectedly few six-love finishes: {completed}/60"


def test_room_capacity_and_old_games_survive(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"sixth.db")) as client:
        assert client.post("/api/rooms",json={"name":"A","game_type":"dominoes","capacity":2}).status_code==422
        assert client.post("/api/rooms",json={"name":"A","game_type":"dominoes","capacity":5}).status_code==422
        for kind,n in [("shithead",6),("ludo",4),("awale",2),("dara",2),("yote",2),("dominoes",4)]:
            response=client.post("/api/rooms",json={"name":"A","game_type":kind,"capacity":n})
            assert response.status_code==201,(kind,response.text)
            if kind=="dominoes":
                room=response.json()["room_id"]
                for i in range(3):
                    assert client.post(f"/api/rooms/{room}/join",json={"name":f"P{i}"}).status_code==201
                assert client.post(f"/api/rooms/{room}/join",json={"name":"Extra"}).status_code==409


def test_static_ui_has_jamaican_choice_and_original_logo(tmp_path):
    with TestClient(create_app(db_path=tmp_path/"ui.db")) as client:
        html=client.get("/").text
        assert 'data-game="dominoes"' in html
        assert 'id="screen-dominoes"' in html
        assert 'id="screen-dominoes-rules"' in html
        assert "/brand/shithead-logo.png" in html
        assert client.get("/dominoes.js").status_code==200


def test_six_love_finish_and_broken_streak_reset():
    initial=make_domino_match(seed=11)
    near_win=replace(initial,scores=(5,0))
    finished=_end_hand(near_win,0,0,reason="Team zero hand")
    assert finished.stage=="FINISHED"
    assert finished.winner_team==0 and finished.scores==(6,0)
    interrupted=_end_hand(near_win,1,1,reason="Opposite partnership wins")
    assert interrupted.stage=="HAND_OVER"
    assert interrupted.scores==(0,0)
    assert interrupted.next_pose_team is None
    assert interrupted.winner_team is None
