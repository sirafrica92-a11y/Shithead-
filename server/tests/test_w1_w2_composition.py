"""W1<->W2 composition tests: thread the pile-pass reducer into the turn
selector the way the match engine will. The caller reads the reducer's
terminal state and composes ``resolve_next_actor``; these tests pin that seam
so a silent break in the contract is caught here, not at W3."""

import pytest

from server.app.rules.pile_pass import (
    Accept, Attack3Joker, Counter, EmptyPileSkip, initial_state, reduce,
)
from server.app.rules.turns import resolve_next_actor


def test_accepted_attack_composes_turn_with_extra_skips():
    seats = ("A", "B", "C", "D")
    s = initial_state(seats, "A")
    s = reduce(s, Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J", "3")), actor="A")
    s = reduce(s, Accept(), actor="B")
    nxt = resolve_next_actor(
        seats,
        original_actor=s.attack.original_actor,
        final_collector=s.actor,
        extra_skips=s.attack.extra_skips,
    )
    assert nxt == "A"


def test_counter_chain_composes_turn_anchored_to_original_actor():
    seats = ("A", "B", "C")
    s = initial_state(seats, "A")
    s = reduce(s, Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J",)), actor="A")
    s = reduce(s, Counter(new_target="C", cards=("J",)), actor="B")
    s = reduce(s, Accept(), actor="C")
    nxt = resolve_next_actor(
        seats,
        original_actor=s.attack.original_actor,
        final_collector=s.actor,
        extra_skips=s.attack.extra_skips,
    )
    assert nxt == "C"


def test_empty_pile_skip_composes_turn_skipping_next_seat():
    seats = ("A", "B", "C")
    s = initial_state(seats, "A")
    s = reduce(s, EmptyPileSkip(cards=("J",)), actor="A")
    assert s.attack is None
    nxt = resolve_next_actor(
        seats,
        original_actor=s.actor,
        final_collector=None,
        extra_skips=0,
    )
    assert nxt == "C"
