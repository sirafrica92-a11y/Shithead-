"""Regression coverage for player-requested multiplayer refinements."""
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from server.app.gameplay import apply_match_action, assert_card_conservation, make_match
from server.app.main import create_app
from server.app.rules.ordinary import loser


def battle():
    m = make_match(2, seed=3)
    st = m.state
    a, b = st.current, 1 - st.current
    players = list(st.players)
    # Reassign ranks while retaining every physical ID.
    for seat in (a, b):
        p = players[seat]
        hand = tuple(replace(c, rank=3 if i < 2 else 0) for i,c in enumerate(p.hand))
        players[seat] = replace(p, hand=hand)
    m = replace(m, state=replace(st, players=tuple(players),
        pile=(st.deck[0],), deck=st.deck[1:]))
    return m, a, b


def test_back_and_forth_counters_refill_each_player_immediately():
    m, a, b = battle()
    m = apply_match_action(m, a, "power", index=0, target=b)
    assert len(m.state.players[a].hand) == 3
    assert m.pending is not None
    assert_card_conservation(m)
    m = apply_match_action(m, b, "counter", index=0, target=a)
    assert len(m.state.players[b].hand) == 3
    assert len(m.state.players[a].hand) == 3
    assert_card_conservation(m)
    m = apply_match_action(m, a, "counter", index=0, target=b)
    assert len(m.state.players[a].hand) == 3
    assert_card_conservation(m)
    m = apply_match_action(m, b, "counter", index=0, target=a)
    assert len(m.state.players[b].hand) == 3
    assert m.pending is not None
    assert_card_conservation(m)
    m = apply_match_action(m, a, "accept")
    assert m.pending is None
    assert_card_conservation(m)


def test_power_refill_with_empty_stock_does_not_invent_cards():
    m, a, b = battle()
    st = m.state
    m = replace(m, state=replace(st, pile=st.pile + st.deck, deck=()))
    m = apply_match_action(m, a, "power", index=0, target=b)
    # With no stock, D-022 absorbs the exposed cards; none are created.
    assert len(m.state.players[a].hand) == 5
    assert not m.state.players[a].face_up
    assert m.pending is not None


def test_rematch_reactions_are_cosmetic_and_preserve_names(tmp_path):
    with TestClient(create_app(db_path=tmp_path / "rooms.db")) as client:
        room = client.post("/api/rooms", json={"capacity": 2, "name": "Africa"}).json()
        other = client.post(f"/api/rooms/{room['room_id']}/join", json={"name": "Bardia"}).json()
        live = client.app.state.room_store.rooms[room["room_id"]]
        with client.websocket_connect(f"/ws/{room['room_id']}") as a:
            a.send_json({"type": "auth", "token": room["token"]})
            first = a.receive_json()
            a.send_json({"type": "reaction", "emoji": "😂",
                         "expected_version": first["version"], "request_id": "reaction-1"})
            error = a.receive_json()
            assert error["reasonCode"] == "wrong_phase"
            assert live.reaction is None
            # Use authoritative end-state fixture to avoid random full-game duration.
            m = make_match(2, seed=2)
            winner = 0
            players = list(m.state.players)
            leftover = players[winner]
            players[winner] = replace(leftover, hand=(), face_up=(), face_down=())
            live.match = replace(m, state=replace(m.state, players=tuple(players),
                                                   deck=(), finished=(winner,)))
            live.version += 1
            before = live.match
            a.send_json({"type": "sync"})
            view = a.receive_json()
            assert view["game"]["loser"] == 1
            a.send_json({"type": "reaction", "emoji": "😂",
                         "expected_version": view["version"], "request_id": "reaction-2"})
            reaction = a.receive_json()
            assert reaction["reaction"]["emoji"] == "😂"
            assert live.match == before
            a.send_json({"type": "rematch", "expected_version": reaction["version"],
                         "request_id": "rematch-a"})
            voted = a.receive_json()
            assert voted["rematch_votes"] == [0]
            with client.websocket_connect(f"/ws/{room['room_id']}") as b:
                b.send_json({"type": "auth", "token": other["token"]})
                bv = b.receive_json()
                a.receive_json()
                b.send_json({"type": "rematch", "expected_version": bv["version"],
                             "request_id": "rematch-b"})
                new_state = b.receive_json()
                assert new_state["game"]["phase"] == "PLAYING"
                assert new_state["rematch_votes"] == []
                assert [x["name"] for x in new_state["players"]] == ["Africa", "Bardia"]
                assert len(new_state["game"]["hand"]) == 3
                assert live.match != before


def test_client_sorted_hand_preserves_authoritative_indices():
    client = (Path(__file__).resolve().parents[1] / "app/static/client.js").read_text()
    assert "sortedHand.map(x => x.index)" in client
    assert "selection.add(serverIndex)" in client
    assert "const loserName = snap?.players?.[g.loser]?.name" in client
    assert 'el("main-menu").onclick' in client
