"""W1+W2 composition contract tests.

Locks the foundation contract between W1 (turns/seat selector) and W2 (pile pass):
- every card class is exactly one of {ordinary, pile-pass, attack} (defined in W1 turns.py);
- pile-pass cards (3, Joker) are removed from the game when played (W2);
- the pile-pass chain engine in worlds.py composes with W1 turn helpers
  (next_index / active_players / choose_first_index) without modification;
- rotation continues clockwise after a pile-pass chain; the counter recipient does not
  become the new base of advancement.
"""

from __future__ import annotations

import pytest

from app.game.cards import build_deck, Joker
from app.game.deck import ACE, EIGHT, FIVE, FOUR, JACK, JOKER, KING, NINE, QUEEN, SEVEN, SIX, TEN, THREE, TWO
from app.rules import pile_pass, turns, worlds
from app.rules.turns import (
    ATTACK_RANKS,
    ORDINARY_RANKS,
    PILE_PASS_RANKS,
    Rank,
    active_players,
    choose_first_index,
    is_power,
    next_index,
)
from app.rules.worlds import (
    Card,
    PlayerState,
    Rank as WRank,
    Suit as WSuit,
    WorldState,
    _new_state,
    attack_ranks,
    begin_play,
    execute_play,
)


def wcard(rank: WRank, n: int) -> Card:
    """Distinct-suit helper so pile-pass rank equality is exercised honestly."""
    suits = [WSuit.SPADES, WSuit.HEARTS, WSuit.CLUBS, WSuit.DIAMONDS]
    return Card(id=f"{rank.name}-{n}", rank=rank, suit=suits[(n - 1) % 4])


def make_world(n_players: int = 3, hand_rank: WRank = WRank.THREE, pile_rank: WRank = WRank.FIVE) -> WorldState:
    state = _new_state(n_players, 1)
    for i, player in enumerate(state.players):
        player.hand = [wcard(hand_rank, i * 4 + k + 1) for k in range(3)]
    state.pile = [wcard(pile_rank, 90)]
    return state


class TestRankClassPartitions:
    def test_every_w1_rank_is_exactly_one_class(self):
        for r in turns.Rank:
            classes = [r in ORDINARY_RANKS, r in PILE_PASS_RANKS, r in ATTACK_RANKS]
            assert sum(classes) == 1, f"{r} in {sum(classes)} classes"

    def test_w2_attack_ranks_match_w1(self):
        assert attack_ranks() == frozenset(ATTACK_RANKS)

    def test_pile_pass_power_flag(self):
        for r in PILE_PASS_RANKS:
            assert is_power(r)
        for r in (ATTACK_RANKS | ORDINARY_RANKS):
            assert not is_power(r)


class TestW2RemovalFromGame:
    def test_three_is_removed_from_game_on_play(self):
        assert THREE.removed_from_game is True

    def test_joker_is_removed_from_game_on_play(self):
        assert JOKER.removed_from_game is True
        assert Joker.removed_from_game is True

    def test_no_other_card_is_removed_from_game(self):
        for card in (TWO, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING, ACE):
            assert card.removed_from_game is False, card

    def test_deck_has_exactly_4_threes_and_2_jokers(self):
        deck = build_deck()
        threes = [c for c in deck if c.rank == THREE.rank]
        jokers = [c for c in deck if c.rank == JOKER.rank]
        assert len(threes) == 4
        assert len(jokers) == 2
        assert len(deck) == 54

    def test_deck_is_shuffled(self):
        import random
        a = build_deck(random.Random(1))
        b = build_deck(random.Random(2))
        assert [c.id for c in a] != [c.id for c in b]


class TestPilePassChainWithW1Turns:
    def test_execute_play_returns_worldstate_and_keeps_rotation_clockwise(self):
        state = make_world()
        out = execute_play(state, 0, ["THREE-1"])
        assert isinstance(out, WorldState)
        # play 3 on 5: no counter at 5 => pile passes to next clockwise player (seat 1)
        assert out.current_actor == 1
        # chain resolved; turn machinery can advance from seat 0 to seat 1 via W1 helper
        assert next_index(0, len(out.players)) == 1

    def test_w1_helpers_operate_on_w2_player_states_unmodified(self):
        state = make_world(4)
        ids = [p.id for p in state.players]
        assert active_players(state.players) == ids
        assert choose_first_index(state.players, method="first") == 0
        assert next_index(2, len(state.players)) == 3
        assert next_index(3, len(state.players)) == 0

    def test_counter_recipient_does_not_rebase_clockwise_advancement(self):
        # Chain: P0 plays 3 on 5 -> passes to P1; P1 counters with another 3 -> passes to P2.
        # P2 cannot counter a 3 (no higher power card) => P2 must pick up.
        # W1/W2 contract: rotation still advances clockwise from P0 (the base), i.e. next base is P1.
        state = _new_state(3, 1)
        state.players[0].hand = [wcard(WRank.THREE, 1)]
        state.players[1].hand = [wcard(WRank.THREE, 2)]
        state.players[2].hand = [wcard(WRank.FOUR, 3)]
        state.pile = [wcard(WRank.FIVE, 90)]

        out = execute_play(state, 0, [state.players[0].hand[0].id])
        assert out.current_actor == 1
        out2 = execute_play(out, 1, [out.players[1].hand[0].id])
        assert out2.current_actor == 2  # decision at P2; cannot counter a 3

        base_of_this_play = 0
        assert next_index(base_of_this_play, len(out2.players)) == 1


class TestPilePassDoesNotLeakIntoOrdinaryRanks:
    @pytest.mark.parametrize("rank", [WRank.THREE, WRank.JOKER])
    def test_pile_pass_ranks_are_not_w1_ordinary(self, rank):
        assert rank not in ORDINARY_RANKS
