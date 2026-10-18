"""W4 local, server-authoritative match composition.

Uses frozen W1/W2 and the W3 ordinary reducer without changing their code.
Development preview limits: one power card per attack/counter; seat 0 starts,
clockwise. Canonical D-019 starting-seat/direction and grouped extra skips
need owner-approved match integration before full W4 acceptance.
"""
from __future__ import annotations

import random
import secrets
from dataclasses import dataclass, replace
from typing import Any

from server.app.rules.ordinary import (
    Card, IllegalPlay, OrdinaryState, PlayerState, apply_play, loser, pick_up,
)
from server.app.rules.pile_pass import (
    Accept, Attack3Joker, Counter, EmptyPileSkip, IllegalTransition, Phase,
    PileState, initial_state, reduce,
)
from server.app.rules.turns import resolve_next_actor

SUITS = ("S", "H", "D", "C")
POWERS = (0, 3)


@dataclass(frozen=True)
class Match:
    state: OrdinaryState
    pending: PileState | None = None
    power_removed: tuple[Card, ...] = ()
    power_actors: tuple[int, ...] = ()


def make_match(n_players: int, seed: int | None = None) -> Match:
    if not 2 <= n_players <= 6:
        raise ValueError("match requires 2–6 seats")
    copies = 1 if n_players <= 4 else 2
    deck = [
        Card(rank=rank, suit=suit, id=f"{copy}-{rank}-{suit}")
        for copy in range(copies)
        for rank in range(2, 15)
        for suit in SUITS
    ]
    deck += [
        Card(rank=0, suit="J", id=f"{copy}-J-{j}")
        for copy in range(copies) for j in (1, 2)
    ]
    if seed is None:
        secrets.SystemRandom().shuffle(deck)
    else:
        random.Random(seed).shuffle(deck)

    # Deal face-down, face-up, hand in three complete passes.
    zones: list[dict[str, tuple[Card, ...]]] = [
        {"face_down": (), "face_up": (), "hand": ()}
        for _ in range(n_players)
    ]
    offset = 0
    for zone in ("face_down", "face_up", "hand"):
        for i in range(n_players):
            zones[i][zone] = tuple(deck[offset:offset + 3])
            offset += 3
    players = tuple(PlayerState(**z) for z in zones)
    return Match(OrdinaryState(players=players, deck=tuple(deck[offset:])))


def _player_zone(state: OrdinaryState, player: PlayerState) -> str:
    if player.hand or state.deck:
        return "hand"
    if player.face_up:
        return "face_up"
    return "face_down"


def _seat_order(state: OrdinaryState) -> tuple[str, ...]:
    n = len(state.players)
    return tuple(str((k * state.direction) % n)
                 for k in range(n)
                 if (k * state.direction) % n not in state.finished)


def _valid_target(state: OrdinaryState, actor: int, target: object) -> int:
    if type(target) is not int or not 0 <= target < len(state.players):
        raise IllegalPlay("choose a valid target seat")
    if target == actor or target in state.finished:
        raise IllegalPlay("cannot target yourself or a finished seat")
    return target


def _take_power(state: OrdinaryState, seat: int, index: object) -> tuple[OrdinaryState, Card]:
    pending = state.pending_blind_power
    if pending is not None:
        if pending.actor != seat:
            raise IllegalPlay("wrong actor for blind power")
        return replace(state, pending_blind_power=None), pending.card
    player = state.players[seat]
    zone = _player_zone(state, player)
    if zone == "face_down":
        raise IllegalPlay("blind face-down powers must be revealed first")
    available = getattr(player, zone)
    if type(index) is not int or not 0 <= index < len(available):
        raise IllegalPlay("choose a power card you own")
    card = available[index]
    if card.rank not in POWERS:
        raise IllegalPlay("selected card is not a 3/Joker")
    remaining = available[:index] + available[index + 1:]
    players = list(state.players)
    players[seat] = replace(player, **{zone: remaining})
    return replace(state, players=tuple(players)), card


def _power_code(card: Card) -> str:
    return "J" if card.rank == 0 else "3"


def _resolve_power(match: Match, chosen_next: int) -> Match:
    """Refill participants only after a complete 3/Joker chain, then finish."""
    state = match.state
    players = list(state.players)
    deck = state.deck
    for seat in dict.fromkeys(match.power_actors):
        p = players[seat]
        if deck and len(p.hand) < 3:
            need = min(3 - len(p.hand), len(deck))
            p = replace(p, hand=p.hand + deck[:need])
            deck = deck[need:]
        players[seat] = p
    finished = list(state.finished)
    if not deck:
        for seat, p in enumerate(players):
            if seat not in finished and not (p.hand or p.face_up or p.face_down):
                finished.append(seat)
    remaining = [i for i in range(len(players)) if i not in finished]
    if not remaining:
        raise IllegalPlay("no seats remain")
    if len(remaining) == 1:
        chosen_next = remaining[0]
    else:
        for _ in range(len(players)):
            if chosen_next in remaining:
                break
            chosen_next = (chosen_next + state.direction) % len(players)
        else:
            raise IllegalPlay("no eligible next seat")
    state = replace(
        state, players=tuple(players), deck=deck,
        finished=tuple(finished), current=chosen_next,
    )
    return replace(match, state=state, pending=None, power_actors=())


def _start_power(match: Match, seat: int, index: object, target: object) -> Match:
    state = match.state
    if seat != state.current:
        raise IllegalPlay("not your turn")
    next_state, card = _take_power(state, seat, index)
    order = _seat_order(state)
    passed = initial_state(order, str(seat))
    if state.pile:
        recipient = _valid_target(state, seat, target)
        passed = reduce(
            passed, Attack3Joker(target=str(recipient), cards=(_power_code(card),)),
            actor=str(seat),
        )
        return replace(
            match, state=next_state, pending=passed,
            power_removed=match.power_removed + (card,),
            power_actors=(seat,),
        )

    passed = reduce(passed, EmptyPileSkip(cards=(_power_code(card),)), actor=str(seat))
    selected = int(resolve_next_actor(order, str(seat), None))
    return _resolve_power(
        replace(match, state=next_state,
                power_removed=match.power_removed + (card,), power_actors=(seat,)),
        selected,
    )


def _counter(match: Match, seat: int, index: object, target: object) -> Match:
    assert match.pending is not None
    recipient = _valid_target(match.state, seat, target)
    next_state, card = _take_power(match.state, seat, index)
    next_pass = reduce(
        match.pending,
        Counter(new_target=str(recipient), cards=(_power_code(card),)),
        actor=str(seat),
    )
    return replace(
        match, state=next_state, pending=next_pass,
        power_removed=match.power_removed + (card,),
        power_actors=match.power_actors + (seat,),
    )


def _accept(match: Match, seat: int) -> Match:
    assert match.pending is not None
    result = reduce(match.pending, Accept(), actor=str(seat))
    attack = result.attack
    assert attack is not None
    st = match.state
    players = list(st.players)
    collector = players[seat]
    players[seat] = replace(collector, hand=collector.hand + st.pile)
    state = replace(st, players=tuple(players), pile=(), locked=False)
    order = _seat_order(st)
    chosen = int(resolve_next_actor(
        order, attack.original_actor, str(seat),
        extra_skips=attack.extra_skips,
    ))
    return _resolve_power(replace(match, state=state, pending=None), chosen)


def apply_match_action(match: Match, seat: int, kind: str,
                       *, indices: object = None, index: object = None,
                       target: object = None) -> Match:
    """Authoritatively validate and transition a match. Inputs remain immutable."""
    state = match.state
    if type(seat) is not int or not 0 <= seat < len(state.players):
        raise IllegalPlay("unknown seat")
    if loser(state) is not None:
        raise IllegalPlay("match finished")
    if match.pending is not None:
        if str(seat) != match.pending.actor:
            raise IllegalPlay("not your decision")
        if kind == "counter":
            return _counter(match, seat, index, target)
        if kind == "accept":
            return _accept(match, seat)
        raise IllegalPlay("resolve the pending pile attack first")
    if seat != state.current:
        raise IllegalPlay("not your turn")
    if kind == "power":
        return _start_power(match, seat, index, target)
    if state.pending_blind_power is not None:
        raise IllegalPlay("resolve the revealed 3/Joker power first")
    if kind == "pickup":
        return replace(match, state=pick_up(state))
    if kind == "play":
        if not isinstance(indices, list) or not indices or len(indices) > 4:
            raise IllegalPlay("choose 1–4 same-rank cards")
        return replace(match, state=apply_play(state, _player_zone(state, state.players[seat]), indices))
    if kind == "flip":
        if type(index) is not int:
            raise IllegalPlay("choose a face-down index")
        return replace(match, state=apply_play(state, "face_down", (index,)))
    raise IllegalPlay("unsupported game action")


def _card(c: Card) -> dict[str, Any]:
    return {"rank": c.rank, "suit": c.suit, "id": c.id}


def public_match_view(match: Match) -> dict[str, Any]:
    st = match.state
    over = loser(st)
    return {
        "phase": "FINISHED" if over is not None else
                 "PILE_PASS_DECISION" if match.pending is not None else "PLAYING",
        "actor": int(match.pending.actor) if match.pending is not None else st.current,
        "loser": over,
        "pile": [_card(c) for c in st.pile],
        "deck_count": len(st.deck),
        "burned_count": len(st.burned),
        "power_removed_count": len(match.power_removed),
        "locked": st.locked,
        "players": [
            {
                "seat": i,
                "hand_count": len(p.hand),
                "face_up": [_card(c) for c in p.face_up],
                "face_down_count": len(p.face_down),
                "finished": i in st.finished,
            }
            for i, p in enumerate(st.players)
        ],
        "pending_blind_power": st.pending_blind_power is not None,
        "development_start_rule": "seat 0 clockwise (D-019 not yet integrated)",
    }


def private_match_view(match: Match, seat: int) -> dict[str, Any]:
    out = public_match_view(match)
    st = match.state
    player = st.players[seat]
    out["hand"] = [_card(c) for c in player.hand]
    out["your_zone"] = _player_zone(st, player)
    out["your_face_up"] = [_card(c) for c in player.face_up]
    out["you"] = seat
    out["your_blind_power"] = (
        _card(st.pending_blind_power.card)
        if st.pending_blind_power is not None and st.pending_blind_power.actor == seat
        else None
    )
    return out


def assert_card_conservation(match: Match) -> None:
    """Internal regression guard: each physical ID is represented exactly once."""
    st = match.state
    cards = [*st.deck, *st.pile, *st.burned, *match.power_removed]
    for p in st.players:
        cards.extend(p.hand)
        cards.extend(p.face_up)
        cards.extend(p.face_down)
    if st.pending_blind_power is not None:
        cards.append(st.pending_blind_power.card)
    expected = 54 if len(st.players) <= 4 else 108
    ids = [card.id for card in cards]
    if len(ids) != expected or len(set(ids)) != expected:
        raise AssertionError(f"card conservation violated: {len(ids)} of {expected}")
