"""Forced pickup action regressions for W3."""

import pytest

from server.app.rules.ordinary import (
    Card, IllegalPlay, OrdinaryState, PlayerState, pick_up,
)


def C(rank):
    return Card(rank)


def P(hand=(), face_up=(), face_down=()):
    return PlayerState(tuple(hand), tuple(face_up), tuple(face_down))


def S(players, pile):
    return OrdinaryState(tuple(players), pile=tuple(pile))


def test_forced_pickup_recovers_cards_and_ends_turn():
    original = S([P(hand=[C(4)]), P(hand=[C(8)])], [C(12)])
    result = pick_up(original)
    assert tuple(card.rank for card in result.players[0].hand) == (4, 12)
    assert result.current == 1 and not result.pile
    assert original.pile == (C(12),)


def test_pickup_rejected_if_ordinary_or_power_play_exists():
    for rank in (2, 3, 7, 10, 12):
        state = S([P(hand=[C(rank)]), P(hand=[C(8)])], [C(12)])
        with pytest.raises(IllegalPlay):
            pick_up(state)


def test_faceup_pickup_moves_pile_to_hand_and_keeps_table_cards():
    state = S([P(face_up=[C(4)]), P(hand=[C(8)])], [C(12)])
    result = pick_up(state)
    assert result.players[0].hand == (C(12),)
    assert result.players[0].face_up == (C(4),)
    assert result.current == 1


def test_blind_player_cannot_choose_pickup_without_flipping():
    state = S([P(face_down=[C(4)]), P(hand=[C(8)])], [C(12)])
    with pytest.raises(IllegalPlay):
        pick_up(state)
