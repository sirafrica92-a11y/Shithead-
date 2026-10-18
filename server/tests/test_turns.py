"""W1 tests for server/app/rules/turns.py.

One test per single-attack, no-extra-skip row in docs/SCENARIO_MATRIX.md (2-6
seats, every target), the redirect examples, the original-actor-collects case,
owner-supplied multi-skip examples, and the now-resolved O-04/O-05 behaviour
confirmed by D-014 and D-015.
"""

import pytest

from server.app.rules.turns import resolve_next_actor as r

S2 = ["A", "B"]
S3 = ["A", "B", "C"]
S4 = ["A", "B", "C", "D"]
S5 = ["A", "B", "C", "D", "E"]
S6 = ["A", "B", "C", "D", "E", "F"]


@pytest.mark.parametrize("seats,collector,expected", [
    (S2, "B", "A"),
    (S3, "B", "C"), (S3, "C", "B"),
    (S4, "B", "C"), (S4, "C", "B"), (S4, "D", "B"),
    (S5, "B", "C"), (S5, "C", "B"), (S5, "D", "B"), (S5, "E", "B"),
    (S6, "B", "C"), (S6, "C", "B"), (S6, "D", "B"), (S6, "E", "B"), (S6, "F", "B"),
])
def test_seat_order_matrix(seats, collector, expected):
    assert r(seats, "A", collector, 0) == expected


@pytest.mark.parametrize("seats,collector,expected", [
    (S3, "B", "C"),   # A->C->B, B accepts
    (S6, "B", "C"),   # A->E->C->B, B accepts
    (S5, "C", "B"),   # anchor stays A, not last counterer E
])
def test_redirect_anchor_never_last_counterer(seats, collector, expected):
    assert r(seats, "A", collector, 0) == expected


@pytest.mark.parametrize("seats", [S2, S4])
def test_original_actor_collects(seats):
    assert r(seats, "A", "A", 0) == "B"


@pytest.mark.parametrize("seats,expected", [(S2, "A"), (S3, "C"), (S4, "C")])
def test_empty_pile(seats, expected):
    assert r(seats, "A", None, 0) == expected


@pytest.mark.parametrize("seats,collector,skips,expected", [
    (S4, "B", 2, "A"),   # owner example
    (S4, "D", 2, "D"),   # owner example
    (S5, "B", 3, "A"),   # derived
    (S6, "F", 4, "F"),   # derived
])
def test_multi_skip(seats, collector, skips, expected):
    assert r(seats, "A", collector, skips) == expected


@pytest.mark.parametrize("seats,collector,skips,expected", [
    # D-014: extra skips survive the chain, resolve after the collector
    # outcome, and stay anchored to the original actor A.
    (S4, "C", 2, "D"),   # A->B(2 skips), B counters to C, C accepts; C not next, skip B,C -> D
    (S3, "C", 1, "C"),   # A->B(1 skip), B counters to C, C accepts; skip B -> C acts
    (S5, "B", 2, "E"),   # A->B(2 skips), B accepts; B next & collects, skip C,D -> E acts
])
def test_o04_attack_with_extra_skips_then_counter(seats, collector, skips, expected):
    assert r(seats, "A", collector, skips) == expected


@pytest.mark.parametrize("seats,expected", [(S3, "C"), (S4, "C"), (S2, "A")])
def test_o05_elective_empty_pile_skip_with_ordinary_cards(seats, expected):
    # D-015: the empty-pile skip is elective; the seat arithmetic is unchanged.
    assert r(seats, "A", None, 0) == expected


@pytest.mark.parametrize("seats", [["A"], ["A", "B", "C", "D", "E", "F", "G"]])
def test_rejects_bad_seat_count(seats):
    with pytest.raises(ValueError):
        r(seats, seats[0], None, 0)


def test_rejects_duplicate_seats():
    with pytest.raises(ValueError):
        r(["A", "B", "B"], "A", "B", 0)


def test_rejects_unknown_actor_or_collector():
    with pytest.raises(ValueError):
        r(S3, "Z", "B", 0)
    with pytest.raises(ValueError):
        r(S3, "A", "Z", 0)


def test_rejects_negative_skips():
    with pytest.raises(ValueError):
        r(S3, "A", "B", -1)
