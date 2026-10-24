"""Voluntary and forced pile-pickup regressions for W3."""

import pytest
from dataclasses import replace

from server.app.rules.ordinary import (
    Card, IllegalPlay, OrdinaryState, PendingBlindPower, PlayerState, pick_up,
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


@pytest.mark.parametrize("rank", [0, 2, 3, 7, 10, 12])
def test_voluntary_pickup_allowed_despite_legal_ordinary_or_power_play(rank):
    """D-023: even a legal 3/Joker or same-rank ordinary card may be withheld."""
    state = S([P(hand=[C(rank)]), P(hand=[C(8)])], [C(12)])
    result = pick_up(state)
    assert result.players[0].hand == (C(rank), C(12))
    assert result.pile == ()
    assert result.current == 1
    assert state.players[0].hand == (C(rank),) and state.pile == (C(12),)


def test_voluntary_pickup_clears_seven_lock_and_ends_turn():
    state = S([P(hand=[C(2), C(3), C(7)]), P(hand=[C(8)])], [C(7)])
    state = replace(state, locked=True)
    result = pick_up(state)
    assert result.players[0].hand == (C(2), C(3), C(7), C(7))
    assert result.locked is False and result.current == 1


def test_voluntary_pickup_allowed_from_face_up_stage():
    state = S([P(face_up=[C(12), C(8), C(6)]), P(hand=[C(5)])], [C(12)])
    result = pick_up(state)
    assert result.players[0].hand == (C(12), C(12), C(8), C(6))
    assert result.players[0].face_up == ()
    assert result.current == 1


def test_pickup_rejected_on_empty_pile():
    state = S([P(hand=[C(3)]), P(hand=[C(8)])], [])
    with pytest.raises(IllegalPlay, match="empty pile"):
        pick_up(state)


def test_pickup_rejected_during_committed_blind_power():
    state = S([P(hand=[C(12)]), P(hand=[C(8)])], [C(12)])
    state = replace(state, pending_blind_power=PendingBlindPower(0, C(3)))
    with pytest.raises(IllegalPlay, match="pending blind power"):
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

@pytest.mark.parametrize("players_count", range(2, 7))
@pytest.mark.parametrize("direction", [-1, 1])
def test_voluntary_pickup_keeps_existing_two_to_six_player_rotation(players_count, direction):
    """Picking up never skips a seat or changes the approved turn direction."""
    players = [P(hand=[C(11)]) for _ in range(players_count)]
    state = replace(S(players, [C(11)]), direction=direction)
    after = pick_up(state)
    assert after.current == (direction % players_count)
    assert len(after.players[0].hand) == 2
    assert after.pile == ()
