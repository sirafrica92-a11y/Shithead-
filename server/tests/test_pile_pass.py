"""Acceptance tests for the W2 pile-pass reducer.

Tests are grouped as accept-path, counter-path, empty-pile-skip, and
immutability/replay. The turn-after composition is W1's job and is not
re-tested here."""

import pytest

from server.app.rules.pile_pass import (
    Accept, Attack3Joker, Counter, EmptyPileSkip, IllegalTransition, Phase,
    allowed_actions, initial_state, reduce,
)

S3 = ("A", "B", "C")
S4 = ("A", "B", "C", "D")


def test_attack_enters_decision_and_removes_card():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"), actor="A")
    assert set(allowed_actions(s)) == {Accept, Counter}
    s = reduce(s, Accept(), actor="B")
    assert allowed_actions(s) == ()


def test_extra_skip_cards_count_and_are_removed():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B", cards=("3",)), actor="A")
    assert s.phase is Phase.PILE_PASS_DECISION
    assert s.removed == frozenset({"3"})
    s = reduce(initial_state(S4, "A"),
               Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J", "3")), actor="A")
    assert s.attack.extra_skips == 2
    assert s.removed == frozenset({"3", "J"})


def test_attack_validation():
    s = initial_state(S3, "A")
    with pytest.raises(IllegalTransition):
        reduce(s, Attack3Joker(target="Z"), actor="A")  # not seated
    with pytest.raises(IllegalTransition):
        reduce(s, Attack3Joker(target="A"), actor="A")   # no self attack
    with pytest.raises(IllegalTransition):
        reduce(s, Attack3Joker(target="B", cards=()), actor="A")


def test_accept_resolves_to_collector_and_keeps_skips():
    s = reduce(initial_state(S4, "A"),
               Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J",)), actor="A")
    s = reduce(s, Accept(), actor="B")
    assert s.phase is Phase.RESOLVED
    assert s.attack.extra_skips == 1
    assert s.actor == "B"                       # the collector anchors the turn


def test_counter_redirects_and_preserves_skip_count():
    s = reduce(initial_state(S4, "A"),
               Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J", "3")), actor="A")
    s = reduce(s, Counter(new_target="C", cards=("J",)), actor="B")
    assert s.actor == "C"
    assert s.attack.extra_skips == 2            # skips survive the redirect
    assert s.attack.spent == ("3", "J", "3", "J")
    assert s.attack.chain == ("A", "B")
    s = reduce(s, Accept(), actor="C")
    assert s.phase is Phase.RESOLVED
    assert s.attack.original_actor == "A"


def test_counter_validation():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"), actor="A")
    with pytest.raises(IllegalTransition):
        reduce(s, Counter(new_target="Z"), actor="B")
    with pytest.raises(IllegalTransition):
        reduce(s, Counter(new_target="B"), actor="B")   # cannot redirect to yourself
    with pytest.raises(IllegalTransition):
        reduce(s, Counter(new_target="C", cards=()), actor="B")


def test_empty_pile_skip_removes_card_and_resolves():
    s = reduce(initial_state(S3, "A"), EmptyPileSkip(cards=("J",)), actor="A")
    assert s.phase is Phase.RESOLVED
    assert s.removed == frozenset({"J"})
    assert s.attack is None


def test_only_decision_owner_may_respond():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"), actor="A")
    with pytest.raises(IllegalTransition):
        reduce(s, Accept(), actor="C")        # C is not the decision owner


def test_out_of_phase_actions_rejected():
    s = initial_state(S3, "A")
    with pytest.raises(IllegalTransition):
        reduce(s, Accept(), actor="A")         # no live attack to accept


def test_stale_version_rejected():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"), actor="A")
    with pytest.raises(IllegalTransition):
        reduce(s, Accept(), actor="B", version=0)  # current version is 1


def test_reduce_is_pure_and_deterministic():
    s0 = initial_state(S3, "A")
    a = Attack3Joker(target="B", cards=("3",))
    s1 = reduce(s0, a, actor="A")
    s1_again = reduce(s0, a, actor="A")
    assert s0.version == 0 and s0.phase is Phase.PLAYING   # untouched
    assert s1 == s1_again                                   # deterministic


def test_missing_actor_is_rejected():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"), actor="A")
    with pytest.raises(IllegalTransition):
        reduce(s, Accept(), actor=None)   # actor is mandatory, not optional
