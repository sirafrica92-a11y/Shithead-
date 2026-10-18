"""Stateful legal-play traces and real card-conserving endgame regression fixtures.

A legal Shithead game is not guaranteed to terminate under an arbitrary bot
strategy: repeated pickups can be cyclic. Do not invent a forced-win rule.
"""
import pytest

from dataclasses import replace

from server.app.gameplay import apply_match_action, assert_card_conservation, make_match
from server.app.rules.ordinary import IllegalPlay, PlayerState, loser


def bot_step(match):
    if match.pending is not None:
        # Deliberately accepting rather than countering prevents endless counter loops.
        return apply_match_action(match, int(match.pending.actor), "accept")
    st = match.state
    actor = st.current
    hand = st.players[actor].hand
    if st.pending_blind_power is not None:
        other = next(i for i in range(len(st.players))
                     if i != actor and i not in st.finished)
        return apply_match_action(match, actor, "power", target=other)
    if not hand and not st.deck and not st.players[actor].face_up:
        return apply_match_action(match, actor, "flip", index=0)
    zone = "hand" if hand or st.deck else "face_up"
    cards = getattr(st.players[actor], zone)
    # Use the full same-rank group. This intentionally selects a different
    # legal policy than the naive single-card bot (which may cycle forever).
    candidates=sorted(
        (rank for rank in {c.rank for c in cards} if rank not in (0,3)),
        key=lambda rank: (-min(4,sum(c.rank==rank for c in cards)),
                          rank != 10, rank),
    )
    for rank in candidates:
        indices=[i for i,c in enumerate(cards) if c.rank==rank][:4]
        try:
            return apply_match_action(match, actor, "play", indices=indices)
        except IllegalPlay:
            pass
    for i,c in enumerate(cards):
        if c.rank in (0,3):
            other=next(i for i in range(len(st.players))
                       if i != actor and i not in st.finished)
            return apply_match_action(match, actor, "power", index=i, target=other)
    return apply_match_action(match, actor, "pickup")


@pytest.mark.parametrize("players",range(2,7))
@pytest.mark.parametrize("seed",range(3))
def test_legal_full_deck_trace_keeps_cards_and_action_owner(players, seed):
    """Trace authentic shuffled games; legal pickup cycles are not engine hangs."""
    match=make_match(players,seed=seed)
    for step in range(500):
        assert_card_conservation(match)
        last=loser(match.state)
        if last is not None:
            assert len(match.state.finished)==players-1
            return
        match=bot_step(match)
    assert_card_conservation(match)


@pytest.mark.parametrize("players",range(2,7))
def test_endgame_from_last_cards_finishes_all_but_one(players):
    """Near-terminal 54/108-card fixture, every physical ID accounted for."""
    match=make_match(players,seed=21)
    st=match.state
    order=[(st.current + i*st.direction)%players for i in range(players)]
    all_cards=[*st.deck]
    for p in st.players:
        all_cards.extend(p.hand)
        all_cards.extend(p.face_up)
        all_cards.extend(p.face_down)
    tens=[c for c in all_cards if c.rank==10]
    other=next(c for c in all_cards if c.rank!=10)
    assert len(tens)>=players-1
    chosen=tens[:players-1]+[other]
    assert len({c.id for c in chosen})==players
    prepared=[PlayerState() for _ in range(players)]
    for seat,card in zip(order,chosen):
        prepared[seat]=PlayerState(hand=(card,))
    used={c.id for c in chosen}
    st=replace(st,players=tuple(prepared),deck=(),pile=(),
               burned=tuple(c for c in all_cards if c.id not in used))
    match=replace(match,state=st)
    assert_card_conservation(match)
    for seat in order[:-1]:
        assert match.state.current==seat
        match=apply_match_action(match,seat,"play",indices=[0])
        assert_card_conservation(match)
    assert loser(match.state)==order[-1]
    assert len(match.state.finished)==players-1
