"""Deterministic end-to-end games: actually play from deal until one loser."""
import pytest

from server.app.gameplay import apply_match_action, assert_card_conservation, make_match
from server.app.rules.ordinary import IllegalPlay, loser


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
def test_entire_match_ends_with_exactly_one_loser_and_no_lost_cards(players,seed):
    match=make_match(players,seed=seed)
    for step in range(12000):
        assert_card_conservation(match)
        last=loser(match.state)
        if last is not None:
            assert last not in match.state.finished
            assert len(match.state.finished)==players-1
            assert len(set(match.state.finished))==players-1
            return
        match=bot_step(match)
    pytest.fail(f"match stalled after 12000 turns (seats={players},seed={seed},finished={match.state.finished},pile={len(match.state.pile)},stock={len(match.state.deck)},hands={[len(p.hand) for p in match.state.players]})")
