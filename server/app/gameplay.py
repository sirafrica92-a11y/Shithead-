"""W4 local, server-authoritative match composition.

Uses frozen W1/W2 and the W3 ordinary reducer without changing their code.
Implements owner-approved D-019 starting seats and direction, grouped
3/Joker attack skips (D-014), and exact physical-card conservation.
A three-card comparison tie remains an explicit owner-decision gate.
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
    start_seat: int = 0


class UndecidedStartTie(IllegalPlay):
    """Owner has not decided the D-019 tie beyond the third comparison."""


def _three_lowest(player: PlayerState) -> tuple[int, int, int]:
    """Compare starting cards: rank 2 low, normal ranks 3–A, unranked Joker last.

    Jokers have no ordinary rank in D-012; this ordering is an implementation
    assumption for the preview and is documented, not a new owner ruling.
    """
    ranks = sorted(99 if card.rank == 0 else card.rank for card in player.hand)
    if len(ranks) != 3:
        raise IllegalPlay("starting hand must contain three cards")
    return tuple(ranks)


def starting_seat_and_direction(players: tuple[PlayerState, ...]) -> tuple[int, int]:
    """D-019: lexicographic lowest three cards; compare starter's neighbours."""
    n = len(players)
    if not 2 <= n <= 6:
        raise ValueError("2–6 players required")
    keys = [_three_lowest(p) for p in players]
    best = min(keys)
    winners = [i for i, value in enumerate(keys) if value == best]
    if len(winners) != 1:
        raise UndecidedStartTie("starting-seat tie after three comparisons")
    starter = winners[0]
    if n == 2:
        return starter, 1
    left = (starter - 1) % n
    right = (starter + 1) % n
    if keys[left] == keys[right]:
        raise UndecidedStartTie("second-seat direction tie after three comparisons")
    return starter, 1 if keys[right] < keys[left] else -1


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
    first, direction = starting_seat_and_direction(players)
    return Match(OrdinaryState(
        players=players, deck=tuple(deck[offset:]),
        current=first, direction=direction,
    ), start_seat=first)


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


def _take_powers(
    state: OrdinaryState, seat: int, index: object,
    indices: object = None,
) -> tuple[OrdinaryState, tuple[Card, ...]]:
    """Consume a validated set of physical 3/Joker cards atomically."""
    blind = state.pending_blind_power
    if blind is not None:
        if blind.actor != seat:
            raise IllegalPlay("wrong actor for blind power")
        if indices is not None and indices != []:
            raise IllegalPlay("a blind power is exactly one committed card")
        return replace(state, pending_blind_power=None), (blind.card,)

    player = state.players[seat]
    zone = _player_zone(state, player)
    if zone == "face_down":
        raise IllegalPlay("blind face-down powers must be revealed first")
    source = getattr(player, zone)
    chosen = indices if indices is not None else [index]
    if (
        not isinstance(chosen, list) or not chosen
        or len(chosen) > len(source)
        or any(type(i) is not int or i < 0 or i >= len(source) for i in chosen)
        or len(set(chosen)) != len(chosen)
    ):
        raise IllegalPlay("select distinct owned 3/Joker cards")
    cards = tuple(source[i] for i in chosen)
    if any(c.rank not in POWERS for c in cards):
        raise IllegalPlay("selected cards must all be 3/Joker")
    selected = set(chosen)
    players = list(state.players)
    players[seat] = replace(
        player, **{zone: tuple(c for i, c in enumerate(source) if i not in selected)}
    )
    return replace(state, players=tuple(players)), cards


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


def _start_power(
    match: Match, seat: int, index: object, target: object,
    indices: object = None,
) -> Match:
    state = match.state
    if seat != state.current:
        raise IllegalPlay("not your turn")
    # Validate target before committing any card.
    recipient = _valid_target(state, seat, target) if state.pile else None
    next_state, cards = _take_powers(state, seat, index, indices)
    order = _seat_order(state)
    passed = initial_state(order, str(seat))
    spent = tuple(_power_code(c) for c in cards)
    updated = replace(
        match, state=next_state,
        power_removed=match.power_removed + cards,
        power_actors=(seat,),
    )
    if state.pile:
        passed = reduce(
            passed, Attack3Joker(
                target=str(recipient), cards=(spent[0],),
                extra_skip_cards=spent[1:],
            ), actor=str(seat),
        )
        return replace(updated, pending=passed)
    passed = reduce(passed, EmptyPileSkip(cards=spent), actor=str(seat))
    # The first empty-pile power skips the next seat. Each additional
    # committed physical power skips one more, all in one atomic action.
    selected = int(resolve_next_actor(
        order, str(seat), None, extra_skips=len(spent)-1,
    ))
    return _resolve_power(updated, selected)


def _counter(match: Match, seat: int, index: object, target: object) -> Match:
    assert match.pending is not None
    recipient = _valid_target(match.state, seat, target)
    next_state, cards = _take_powers(match.state, seat, index)
    if len(cards) != 1:
        raise IllegalPlay("a counter must commit exactly one 3/Joker")
    next_pass = reduce(
        match.pending,
        Counter(new_target=str(recipient), cards=(_power_code(cards[0]),)),
        actor=str(seat),
    )
    return replace(
        match, state=next_state, pending=next_pass,
        power_removed=match.power_removed + cards,
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
        return _start_power(match, seat, index, target, indices=indices)
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
        "starter_seat": match.start_seat,
        "direction": st.direction,
        "starting_rule": "D-019 lowest three, then neighbour direction",
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
