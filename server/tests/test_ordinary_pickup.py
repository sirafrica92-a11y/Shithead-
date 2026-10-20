"""Forced pickup action regressions for W3."""

import pytest

from server.app.rules.ordinary import (
    Card, IllegalPlay, OrdinaryState, PlayerState, pick_up,
)


def C(rank):
    return Card(rank)


def P(hand=(), face_up=(), face_down=()):
    return PlayerState(tuple(hand), tuple(face_up), tuple(face_down))


def S(players, pile, deck=()):
    return OrdinaryState(tuple(players), pile=tuple(pile), deck=tuple(deck))


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


def test_faceup_pickup_moves_pile_to_hand_and_absorbs_face_up():
    """D-022 (19 Oct 2026): the stock is empty and the hand ends below three, so
    the face-up cards are absorbed into hand as a free action. This supersedes the
    earlier expectation that face-up cards stayed on the table after a pickup."""
    state = S([P(face_up=[C(4)]), P(hand=[C(8)])], [C(12)])
    result = pick_up(state)
    assert result.players[0].hand == (C(12), C(4))
    assert result.players[0].face_up == ()
    assert result.current == 1


def test_face_up_not_absorbed_while_stock_remains():
    """D-022 only fires once the stock is empty."""
    state = S([P(face_up=[C(4)], hand=[C(5)]), P(hand=[C(8)])], [C(12)], deck=[C(6), C(9)])
    result = pick_up(state)
    assert result.players[0].face_up == (C(4),)


def test_face_up_not_absorbed_while_hand_has_three():
    """D-022 requires fewer than three cards in hand."""
    state = S([P(face_up=[C(4)], hand=[C(5), C(6), C(9)]), P(hand=[C(8)])], [C(12)])
    result = pick_up(state)
    assert result.players[0].face_up == (C(4),)
    assert len(result.players[0].hand) == 4


def test_blind_player_cannot_choose_pickup_without_flipping():
    state = S([P(face_down=[C(4)]), P(hand=[C(8)])], [C(12)])
    with pytest.raises(IllegalPlay):
        pick_up(state)
