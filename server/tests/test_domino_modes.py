"""Cut Throat options coexist with the unchanged Jamaican Partner rules."""
from dataclasses import replace
from fastapi.testclient import TestClient
import pytest

from server.app.dominoes import (
    make_domino_match, _end_hand, legal_domino_actions,
    apply_domino_action, dump_domino, restore_domino, IllegalDominoMove
)
from server.app.main import create_app


def test_mode_defaults_and_four_individual_scores():
    partner=make_domino_match(seed=4)
    assert partner.mode=="partner" and partner.scores==(0,0)
    cut=make_domino_match(seed=4,mode="cutthroat")
    assert cut.mode=="cutthroat" and cut.scores==(0,0,0,0)
    assert cut.hands==partner.hands
    assert restore_domino(dump_domino(cut))==cut
    legacy=dump_domino(partner)
    legacy.pop("mode",None)
    legacy.pop("winner_player",None)
    assert restore_domino(legacy).mode=="partner"
    with pytest.raises(ValueError):
        make_domino_match(mode="random")


def test_cutthroat_score_and_game_winner_without_team_reset():
    m=make_domino_match(seed=5,mode="cutthroat")
    m=replace(m,scores=(3,4,1,0))
    after=_end_hand(m,None,0,reason="Player one finishes.")
    assert after.scores==(4,4,1,0)
    assert after.stage=="HAND_OVER" and after.last_hand_player==0
    assert after.winner_team is None
    assert legal_domino_actions(after,0)["next_hand"]
    assert not legal_domino_actions(after,1)["next_hand"]
    with pytest.raises(IllegalDominoMove):
        apply_domino_action(after,1,"next_hand")
    next_hand=apply_domino_action(after,0,"next_hand")
    assert next_hand.mode=="cutthroat" and next_hand.actor==0
    assert len(next_hand.hands[0])==7
    assert next_hand.scores==(4,4,1,0)
    won=_end_hand(replace(m,scores=(5,2,0,0)),None,0,reason="Winner!")
    assert won.stage=="FINISHED" and won.winner_player==0
    assert won.winner_team is None and won.scores==(6,2,0,0)


def test_tied_hand_resets_pose_without_rewarding_player():
    m=make_domino_match(seed=6,mode="cutthroat")
    m=replace(m,scores=(2,1,0,0))
    draw=_end_hand(m,None,None,reason="Equal lowest pip counts.")
    assert draw.last_hand_player is None
    assert draw.scores==(2,1,0,0)
    assert all(legal_domino_actions(draw,s)["next_hand"] for s in range(4))
    dealt=apply_domino_action(draw,3,"next_hand")
    assert dealt.require_double_six is True
    assert (6,6) in dealt.hands[dealt.actor]
    assert dealt.scores==(2,1,0,0)


def test_cutthroat_api_mode_validation_and_persistence(tmp_path):
    db=tmp_path/"cutthroat.db"
    with TestClient(create_app(db_path=db)) as client:
        invalid=client.post("/api/rooms",json={"name":"Host","capacity":4,"game_type":"dominoes","domino_mode":"unknown"})
        assert invalid.status_code==422
        old_invalid=client.post("/api/rooms",json={"name":"Host","capacity":2,"game_type":"shithead","domino_mode":"cutthroat"})
        assert old_invalid.status_code==422
        result=client.post("/api/rooms",json={"name":"Host","capacity":4,"game_type":"dominoes","domino_mode":"cutthroat"})
        assert result.status_code==201
        host=result.json()
        assert host["domino_mode"]=="cutthroat"
        room_id=host["room_id"]
        assert client.get(f"/api/rooms/{room_id}").json()["domino_mode"]=="cutthroat"
        for i in range(3):
            joined=client.post(f"/api/rooms/{room_id}/join",json={"name":f"Guest {i}"})
            assert joined.status_code==201
        with client.websocket_connect(f"/ws/{room_id}") as ws:
            ws.send_json({"type":"auth","token":host["token"]})
            state=ws.receive_json()
            ws.send_json({"type":"ready","request_id":"host-ready","expected_version":state["version"],"ready":True})
            state=ws.receive_json()
            assert state["domino_mode"]=="cutthroat"
    with TestClient(create_app(db_path=db)) as restored:
        state=restored.get(f"/api/rooms/{room_id}").json()
        assert state["domino_mode"]=="cutthroat"
        with restored.websocket_connect(f"/ws/{room_id}") as ws:
            ws.send_json({"type":"auth","token":host["token"]})
            state=ws.receive_json()
            ws.send_json({"type":"set_domino_mode","request_id":"mode-set","expected_version":state["version"],"domino_mode":"partner"})
            updated=ws.receive_json()
            assert updated["domino_mode"]=="partner"
            assert not updated["players"][0]["ready"]


def test_initial_partner_contract_kept():
    initial=make_domino_match(seed=2)
    assert initial.mode=="partner"
    near=replace(initial,scores=(5,0))
    after=_end_hand(near,0,0,reason="Partner finish")
    assert after.stage=="FINISHED" and after.winner_team==0
    assert after.scores==(6,0)
