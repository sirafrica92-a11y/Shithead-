"""W2 tests for server/app/rules/pile_pass.py (the Shithead pile reducer)."""

import pytest

from server.app.rules.pile_pass import (
    Accept, Attack3Joker, Counter, EmptyPileSkip, IllegalTransition, Phase,
    allowed_actions, initial_state, reduce,
)

S3 = ("A", "B", "C")
S4 = ("A", "B", "C", "D")


def test_initial_state_phase_and_actor():
    s = initial_state(S3, "A")
    assert s.phase is Phase.PLAYING
    assert s.actor == "A"
    assert s.version == 0
    assert s.removed == frozenset()


def test_initial_state_validation():
    with pytest.raises(ValueError):
        initial_state(("A",), "A")
    with pytest.raises(ValueError):
        initial_state(("A", "B", "B"), "A")
    with pytest.raises(ValueError):
        initial_state(S3, "Z")


def test_allowed_actions_whitelist():
    s = initial_state(S3, "A")
    assert set(allowed_actions(s)) == {Attack3Joker, EmptyPileSkip}
    s = reduce(s, Attack3Joker(target="B"))
    assert set(allowed_actions(s)) == {Accept, Counter}
    s = reduce(s, Accept())
    assert allowed_actions(s) == ()


def test_open_attack_moves_ownership_and_spends_card():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B", cards=("3",)))
    assert s.phase is Phase.PILE_PASS_DECISION
    assert s.actor == "B"                    # exactly one owner: the target
    assert "3" in s.removed
    assert s.attack.original_actor == "A"
    assert s.version == 1


def test_attack_extra_skips_attached():
    s = reduce(initial_state(S4, "A"),
               Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J", "3")))
    assert s.attack.extra_skips == 2
    assert s.removed == frozenset({"3", "J"})


def test_attack_rejects_bad_target_and_empty_cards():
    s = initial_state(S3, "A")
    with pytest.raises(IllegalTransition):
        reduce(s, Attack3Joker(target="Z"))
    with pytest.raises(IllegalTransition):
        reduce(s, Attack3Joker(target="A"))   # no self attack
    with pytest.raises(IllegalTransition):
        reduce(s, Attack3Joker(target="B", cards=()))


def test_accept_resolves_and_keeps_skips_pending():
    s = reduce(initial_state(S4, "A"),
               Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J",)))
    s = reduce(s, Accept())
    assert s.phase is Phase.RESOLVED
    assert s.attack.extra_skips == 1
    assert s.attack.original_actor == "A"


def test_counter_chain_preserves_skips_and_anchor():
    s = reduce(initial_state(S4, "A"),
               Attack3Joker(target="B", cards=("3",), extra_skip_cards=("J", "3")))
    s = reduce(s, Counter(new_target="C", cards=("J",)))
    assert s.actor == "C"
    assert s.attack.extra_skips == 2          # D-014: counter does not erase skips
    assert s.attack.original_actor == "A"     # anchor unchanged
    assert s.attack.spent == ("3", "J", "3", "J")
    s = reduce(s, Accept())
    assert s.phase is Phase.RESOLVED
    assert s.attack.original_actor == "A"


def test_counter_rejects_bad_target():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"))
    with pytest.raises(IllegalTransition):
        reduce(s, Counter(new_target="Z"))
    with pytest.raises(IllegalTransition):
        reduce(s, Counter(new_target="B"))   # cannot redirect to yourself
    with pytest.raises(IllegalTransition):
        reduce(s, Counter(new_target="C", cards=()))


def test_empty_pile_skip_removes_card():
    s = reduce(initial_state(S3, "A"), EmptyPileSkip(cards=("J",)))
    assert s.phase is Phase.RESOLVED
    assert "J" in s.removed


def test_rejects_wrong_actor():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"))
    with pytest.raises(IllegalTransition):
        reduce(s, Accept(), actor="C")        # C is not the decision owner


def test_rejects_out_of_phase_action():
    s = initial_state(S3, "A")
    with pytest.raises(IllegalTransition):
        reduce(s, Accept())                    # no live attack to accept


def test_rejects_stale_version():
    s = reduce(initial_state(S3, "A"), Attack3Joker(target="B"))
    with pytest.raises(IllegalTransition):
        reduce(s, Accept(), version=0)         # current version is 1


def test_reducer_is_pure_and_deterministic():
    s0 = initial_state(S3, "A")
    a = Attack3Joker(target="B")
    s1 = reduce(s0, a)
    s1_again = reduce(s0, a)
    assert s0.version == 0 and s0.phase is Phase.PLAYING   # input untouched
    assert s1 == s1_again                                   # deterministic


@pytest.mark.skip(reason="OPEN O-09: timeout/auto-action needs a clock a pure reducer lacks")
def test_pending_afk_timeout():
    pass


@pytest.mark.skip(reason="OPEN O-10: non-playing phase ownership is out of this slice's scope")
def test_pending_lobby_finished_ownership():
    pass
