"""Deterministic unit tests for the ordinary-play reducer (W3).

Contract exercised here (implemented by ``server/app/rules/ordinary.py``):

* ``Card(rank, suit)``               - immutable card, ranks 2..14 (11=J, 12=Q, 13=K, 14=A)
* ``PlayerState(hand, face_up, face_down)`` - the three zones, each a tuple of cards
* ``OrdinaryState(players, deck=(), pile=(), current=0, locked=False, finished=())``
* ``apply_play(state, zone, indices) -> OrdinaryState``
    - ``zone`` is ``"hand"``, ``"face_up"`` or ``"face_down"``
    - ``indices`` are positions inside the current player's zone
    - hand / face_up plays of an illegal card raise ``IllegalPlay``
    - a face_down play is blind: exactly one index, and an illegal reveal is
      resolved by picking up the pile plus the revealed card (no exception)
* ``IllegalPlay``                    - raised for every rejected non-blind play
* ``winner(state) -> int | None``    - first finisher once the game is decided

Rule summary under test: play equal-or-higher than the pile top; 2 resets and
may be played on anything; 7 locks the next player to 7-or-lower for exactly
one play; 10 burns the pile and grants an extra turn; four equal ranks on top
of the pile burn it regardless of who contributed them (2s count); any burn
clears the lock and keeps the turn with the clearing player; the acting player
refills their hand to three from the deck only after the action fully resolves;
zones are played in order hand -> face_up -> face_down (later zones unlock only
once the earlier zones and the deck are empty); a player with all zones empty
and an empty deck has finished.

All tests are pure and deterministic: states are built literally, no shuffling,
no randomness, no I/O.
"""

from app.rules.ordinary import (
    Card,
    IllegalPlay,
    OrdinaryState,
    PlayerState,
    apply_play,
    winner,
)

import pytest


# --------------------------------------------------------------------------
# builders
# --------------------------------------------------------------------------

def C(rank, suit="S"):
    return Card(rank=rank, suit=suit)


def P(hand=(), face_up=(), face_down=()):
    return PlayerState(hand=tuple(hand), face_up=tuple(face_up), face_down=tuple(face_down))


def S(players, deck=(), pile=(), current=0):
    return OrdinaryState(players=tuple(players), deck=tuple(deck), pile=tuple(pile), current=current)


def ranks(cards):
    return tuple(c.rank for c in cards)


# --------------------------------------------------------------------------
# baseline legality
# --------------------------------------------------------------------------

class TestBaselineLegality:
    def test_play_must_meet_or_beat_pile_top(self):
        st = S(
            [P(hand=[C(5), C(9)]), P(hand=[C(8), C(11)])],
            pile=[C(6, "D")],
        )
        nxt = apply_play(st, "hand", (1,))
        assert ranks(nxt.pile) == (6, 9)
        assert ranks(nxt.players[0].hand) == (5,)
        assert nxt.current == 1
        with pytest.raises(IllegalPlay):
            apply_play(st, "hand", (0,))

    def test_equal_rank_is_legal(self):
        st = S(
            [P(hand=[C(9), C(4)]), P(hand=[C(8), C(11)])],
            pile=[C(9, "D")],
        )
        nxt = apply_play(st, "hand", (0,))
        assert ranks(nxt.pile) == (9, 9)

    def test_any_rank_is_legal_on_empty_pile(self):
        st = S([P(hand=[C(4), C(12)]), P(hand=[C(8), C(11)])])
        nxt = apply_play(st, "hand", (0,))
        assert ranks(nxt.pile) == (4,)

    def test_multi_play_must_share_rank(self):
        st = S([P(hand=[C(5), C(9)]), P(hand=[C(8), C(11)])])
        with pytest.raises(IllegalPlay):
            apply_play(st, "hand", (0, 1))

    def test_multi_play_of_matching_ranks_is_legal(self):
        st = S(
            [P(hand=[C(9), C(9, "H"), C(4)]), P(hand=[C(8), C(11)])],
            pile=[C(6, "D")],
        )
        nxt = apply_play(st, "hand", (0, 1))
        assert ranks(nxt.pile) == (6, 9, 9)
        assert ranks(nxt.players[0].hand) == (4,)

    def test_empty_selection_rejected(self):
        st = S([P(hand=[C(5)]), P(hand=[C(8)])])
        with pytest.raises(IllegalPlay):
            apply_play(st, "hand", ())

    def test_out_of_range_index_rejected(self):
        st = S([P(hand=[C(5)]), P(hand=[C(8)])])
        with pytest.raises(IllegalPlay):
            apply_play(st, "hand", (3,))


# --------------------------------------------------------------------------
# seven-lock
# --------------------------------------------------------------------------

class TestSevenLock:
    def test_seven_locks_next_player_to_seven_or_lower(self):
        st = S(
            [P(hand=[C(7), C(13)]), P(hand=[C(9, "H"), C(3, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))  # P0 plays 7
        assert st.current == 1
        with pytest.raises(IllegalPlay):
            apply_play(st, "hand", (0,))  # 9 under the lock
        st = apply_play(st, "hand", (1,))  # 3 is legal under the lock
        assert ranks(st.pile) == (5, 7, 3)

    def test_lock_expires_after_one_ordinary_play(self):
        st = S(
            [P(hand=[C(7), C(13)]), P(hand=[C(3, "H"), C(9, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))  # 7, lock on
        st = apply_play(st, "hand", (0,))  # 3, lock spent
        st = apply_play(st, "hand", (0,))  # K would be illegal if locked
        assert ranks(st.pile) == (5, 7, 3, 13)

    def test_lock_applies_exactly_once_even_with_multi_play(self):
        st = S(
            [P(hand=[C(7), C(13)]), P(hand=[C(5, "H"), C(5, "D"), C(12, "H")])],
        )
        st = apply_play(st, "hand", (0,))      # 7, lock on
        st = apply_play(st, "hand", (0, 1))    # pair of 5s, legal under lock
        st = apply_play(st, "hand", (0,))      # Q legal again: lock spent
        assert ranks(st.pile) == (7, 5, 5, 12)

    def test_seven_played_under_lock_rearms_it(self):
        st = S(
            [P(hand=[C(7), C(13)]), P(hand=[C(7, "H"), C(4, "H")]), ],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))  # 7, lock on
        st = apply_play(st, "hand", (0,))  # second 7, lock re-armed
        with pytest.raises(IllegalPlay):
            apply_play(st, "hand", (0,))  # 13 under the re-armed lock
        st = apply_play(st, "hand", (1,))  # 4 is legal
        assert ranks(st.pile) == (5, 7, 7, 4)


# --------------------------------------------------------------------------
# 10: burn + extra turn
# --------------------------------------------------------------------------

class TestTenClear:
    def test_ten_burns_the_pile(self):
        st = S(
            [P(hand=[C(10), C(4)]), P(hand=[C(8, "H"), C(11, "H")])],
            pile=[C(9, "D"), C(12, "C")],
        )
        st = apply_play(st, "hand", (0,))
        assert st.pile == ()
        assert ranks(st.players[0].hand) == (4,)

    def test_ten_grants_an_extra_turn(self):
        st = S(
            [P(hand=[C(10), C(4)]), P(hand=[C(8, "H"), C(11, "H")])],
            pile=[C(9, "D")],
        )
        st = apply_play(st, "hand", (0,))
        assert st.current == 0  # still the burning player's turn
        st = apply_play(st, "hand", (0,))  # extra turn is real: P0 moves again
        assert ranks(st.pile) == (4,)
        assert st.current == 1

    def test_ten_is_playable_on_anything(self):
        st = S(
            [P(hand=[C(10), C(4)]), P(hand=[C(8, "H"), C(11, "H")])],
            pile=[C(14, "D")],
        )
        st = apply_play(st, "hand", (0,))
        assert st.pile == ()

    def test_burn_clears_the_seven_lock(self):
        st = S(
            [P(hand=[C(7), C(4)]), P(hand=[C(10, "H"), C(13, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))  # 7, lock on
        st = apply_play(st, "hand", (0,))  # 10 burns, lock gone, extra turn
        assert st.pile == ()
        assert st.current == 1
        st = apply_play(st, "hand", (0,))  # K would be illegal if lock survived
        assert ranks(st.pile) == (13,)


# --------------------------------------------------------------------------
# 2: reset, lock clearing, quad contribution
# --------------------------------------------------------------------------

class TestTwoReset:
    def test_two_is_playable_on_anything(self):
        st = S(
            [P(hand=[C(2), C(4)]), P(hand=[C(8, "H"), C(11, "H")])],
            pile=[C(14, "D")],
        )
        st = apply_play(st, "hand", (0,))
        assert ranks(st.pile) == (14, 2)

    def test_anything_is_playable_after_a_two(self):
        st = S(
            [P(hand=[C(2), C(14)]), P(hand=[C(3, "H"), C(11, "H")])],
            pile=[C(13, "D")],
        )
        st = apply_play(st, "hand", (0,))  # 2 resets the pile value
        st = apply_play(st, "hand", (0,))  # 3 on a King: legal only after reset
        assert ranks(st.pile) == (13, 2, 3)

    def test_two_clears_the_seven_lock(self):
        st = S(
            [P(hand=[C(7), C(4)]), P(hand=[C(2, "H"), C(13, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))  # 7, lock on
        st = apply_play(st, "hand", (0,))  # 2 resets and clears the lock
        st = apply_play(st, "hand", (0,))  # K would be illegal if lock survived
        assert ranks(st.pile) == (5, 7, 2, 13)

    def test_twos_count_toward_four_of_a_kind(self):
        st = S(
            [P(hand=[C(2), C(2, "D"), C(4)]), P(hand=[C(2, "H"), C(2, "C"), C(11, "H")])],
            pile=[C(9, "D")],
        )
        st = apply_play(st, "hand", (0,))       # P0:  2
        assert st.pile != ()
        st = apply_play(st, "hand", (0, 1))     # P1:  2, 2
        assert st.pile != ()                    # three 2s: not yet a quad
        st = apply_play(st, "hand", (1,))       # P0:  fourth 2 burns the pile
        assert st.pile == ()
        assert st.current == 0                  # burn grants the extra turn


# --------------------------------------------------------------------------
# four of a kind
# --------------------------------------------------------------------------

class TestFourOfAKind:
    def test_quad_burns_regardless_of_contributors(self):
        st = S(
            [P(hand=[C(9), C(9, "D"), C(4)]), P(hand=[C(9, "H"), C(9, "C"), C(11, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))      # P0 contributes one 9
        st = apply_play(st, "hand", (0, 1))    # P1 contributes two 9s
        assert st.pile != ()                   # three 9s: no burn yet
        st = apply_play(st, "hand", (1,))      # P0 contributes the fourth 9
        assert st.pile == ()

    def test_quad_burn_grants_extra_turn_to_completer(self):
        st = S(
            [P(hand=[C(9), C(9, "D"), C(4)]), P(hand=[C(9, "H"), C(9, "C"), C(11, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0,))
        st = apply_play(st, "hand", (0, 1))
        st = apply_play(st, "hand", (1,))      # P0 completes the quad
        assert st.current == 0                 # completer keeps the turn
        st = apply_play(st, "hand", (0,))      # and can use it immediately
        assert ranks(st.pile) == (4,)

    def test_quad_from_a_single_multi_play_burns(self):
        st = S(
            [P(hand=[C(12), C(12, "H"), C(12, "D"), C(12, "C")]), P(hand=[C(8, "H")])],
            pile=[C(5, "D")],
        )
        st = apply_play(st, "hand", (0, 1, 2, 3))
        assert st.pile == ()
        assert st.current == 0

    def test_only_the_top_four_cards_are_considered(self):
        st = S(
            [P(hand=[C(9), C(4)]), P(hand=[C(8, "H"), C(11, "H")])],
            pile=[C(9, "H"), C(9, "D"), C(9, "C"), C(13, "D")],
        )
        st = apply_play(st, "hand", (0,))  # 9 on K: top four are 9,9,13,9
        assert st.pile != ()               # no burn: the four 9s are not contiguous on top
        assert ranks(st.pile) == (9, 9, 9, 13, 9)


# --------------------------------------------------------------------------
# refill timing: strictly after the action resolves
# --------------------------------------------------------------------------

class TestRefill:
    def test_hand_is_topped_up_to_three_after_a_play(self):
        st = S(
            [P(hand=[C(4), C(5), C(6)]), P(hand=[C(8, "H"), C(11, "H"), C(12, "H")])],
            deck=[C(14, "C"), C(13, "C"), C(3, "C")],
        )
        st = apply_play(st, "hand", (0,))
        assert ranks(st.players[0].hand) == (5, 6, 14)  # drew exactly one
        assert ranks(st.deck) == (13, 3)

    def test_drawn_cards_preserve_deck_order(self):
        st = S(
            [P(hand=[C(9), C(9, "H"), C(9, "D")]), P(hand=[C(8, "H")])],
            deck=[C(3, "C"), C(4, "C"), C(5, "C")],
        )
        st = apply_play(st, "hand", (0, 1, 2))  # hand empties, then refills
        assert ranks(st.players[0].hand) == (3, 4, 5)
        assert st.deck == ()

    def test_partial_refill_when_deck_runs_out(self):
        st = S(
            [P(hand=[C(4), C(5), C(6)]), P(hand=[C(8, "H")])],
            deck=[C(
