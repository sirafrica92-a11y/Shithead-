"""Canonical W4 rule gap regressions. No network or external services."""
from dataclasses import replace

import pytest

from server.app.gameplay import (
    Match, UndecidedStartTie, _seat_order,
    apply_match_action, assert_card_conservation,
    make_match, starting_seat_and_direction,
)
from server.app.rules.ordinary import Card, IllegalPlay, PlayerState


def player(*ranks):
    return PlayerState(hand=tuple(Card(rank=r, suit="S") for r in ranks))


def test_d019_starter_and_direction():
    players = (player(9, 10, 11), player(5, 8, 14),
               player(3, 7, 12), player(4, 7, 13))
    assert starting_seat_and_direction(players) == (2, 1)
    players = (player(9, 10, 11), player(5, 8, 14),
               player(3, 7, 12), player(2, 7, 13))
    assert starting_seat_and_direction(players) == (3, -1)


def test_d019_third_card_tie_stays_unresolved():
    players = (player(2, 4, 6), player(2, 4, 6),
               player(7, 8, 9))
    with pytest.raises(UndecidedStartTie):
        starting_seat_and_direction(players)


@pytest.mark.parametrize("n", range(2, 7))
@pytest.mark.parametrize("seed", range(20))
def test_seeded_deals_choose_correct_starter_and_preserve_cards(n, seed):
    match = make_match(n, seed=seed)
    starter, direction = starting_seat_and_direction(match.state.players)
    assert match.state.current == match.start_seat == starter
    assert match.state.direction == direction
    assert_card_conservation(match)
    assert len(_seat_order(match.state)) == n


def test_grouped_empty_pile_skips_three_seats_and_keeps_cards():
    match = make_match(4, seed=5)
    seat = match.state.current
    player_state = match.state.players[seat]
    hand = list(player_state.hand)
    for i in (0, 1, 2):
        hand[i] = replace(hand[i], rank=3)
    players = list(match.state.players)
    players[seat] = replace(player_state, hand=tuple(hand))
    state = replace(match.state, players=tuple(players))
    match = replace(match, state=state)
    out = apply_match_action(match, seat, "power", indices=[0, 1, 2])
    assert_card_conservation(out)
    assert len(out.power_removed) == 3
    # Exactly three other players are skipped.
    assert out.state.current == seat


def test_grouped_nonempty_attack_extra_skip_survives_counter():
    match = make_match(4, seed=5)
    seat = match.state.current
    players = list(match.state.players)
    current_hand = list(players[seat].hand)
    for i in (0, 1):
        current_hand[i] = replace(current_hand[i], rank=3)
    players[seat] = replace(players[seat], hand=tuple(current_hand))
    target = (seat + match.state.direction) % 4
    recipient_hand = list(players[target].hand)
    recipient_hand[0] = replace(recipient_hand[0], rank=3)
    players[target] = replace(players[target], hand=tuple(recipient_hand))
    # Move one physical card from deck to the playing pile to maintain total.
    pile_card = match.state.deck[0]
    match = replace(match, state=replace(
        match.state, players=tuple(players), deck=match.state.deck[1:],
        pile=(pile_card,)))
    started = apply_match_action(match, seat, "power", indices=[0, 1], target=target)
    assert_card_conservation(started)
    assert started.pending.attack.extra_skips == 1
    new_target = (target + match.state.direction) % 4
    countered = apply_match_action(started, target, "counter", index=0, target=new_target)
    assert countered.pending.attack.extra_skips == 1
    finished = apply_match_action(countered, new_target, "accept")
    assert_card_conservation(finished)
    assert finished.pending is None


def test_unresolved_starting_tie_keeps_websocket_lobby_recoverable(monkeypatch):
    from fastapi.testclient import TestClient
    import server.app.main as server_main

    def tied(_):
        raise UndecidedStartTie("three-card tie needs owner decision")

    monkeypatch.setattr(server_main, "make_match", tied)
    with TestClient(server_main.create_app()) as client:
        room = client.post("/api/rooms", json={"capacity": 2}).json()["room_id"]
        a = client.post(f"/api/rooms/{room}/join", json={"name": "A"}).json()
        b = client.post(f"/api/rooms/{room}/join", json={"name": "B"}).json()
        with client.websocket_connect(f"/ws/{room}") as ws_a:
            ws_a.send_json({"type": "auth", "token": a["token"]})
            first = ws_a.receive_json()
            with client.websocket_connect(f"/ws/{room}") as ws_b:
                ws_b.send_json({"type": "auth", "token": b["token"]})
                second = ws_b.receive_json()
                first = ws_a.receive_json()
                ws_a.send_json({"type": "ready", "ready": True,
                                "expected_version": first["version"], "request_id": "first"})
                first = ws_a.receive_json()
                second = ws_b.receive_json()
                ws_b.send_json({"type": "ready", "ready": True,
                                "expected_version": second["version"], "request_id": "second"})
                failure = ws_b.receive_json()
                assert failure["reasonCode"] == "starting_tie_unresolved"
                assert failure["stateSnapshot"]["phase"] == "LOBBY"
                assert failure["stateSnapshot"]["players"][1]["ready"] is False
                ws_b.send_json({"type": "sync"})
                assert ws_b.receive_json()["phase"] == "LOBBY"
