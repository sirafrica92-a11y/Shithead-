"""W3 ordinary-play rules. Pure state transitions, independent of networking.

This slice handles 2/7/10, groups, four-of-a-kind, refills, face-up/down,
and finished-player rotation. The 3/Joker pass is owned by W2; a blind flip
of one is held as a *pending* power for the future match controller to resolve.
No card is silently discarded and no target is chosen on a player's behalf.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Sequence


class IllegalPlay(ValueError):
    """The proposed action is illegal; the input state has not been changed."""


@dataclass(frozen=True)
class Card:
    rank: int                    # 2..14 (Ace=14), or 0 for Joker
    suit: str = "S"
    id: str | None = None        # set by the authoritative deck for multi-deck games

    def __post_init__(self) -> None:
        if self.rank not in (0, *range(2, 15)):
            raise ValueError("card rank must be 2..14 or 0 for Joker")


@dataclass(frozen=True)
class PlayerState:
    hand: tuple[Card, ...] = ()
    face_up: tuple[Card, ...] = ()
    face_down: tuple[Card, ...] = ()


@dataclass(frozen=True)
class PendingBlindPower:
    actor: int
    card: Card
    """The card is face-up but committed to W2, awaiting resolution.

    In particular, a player who flips a 3/Joker against a nonempty pile must
    still choose an attack target: W3 must not manufacture that choice.
    """


@dataclass(frozen=True)
class OrdinaryState:
    players: tuple[PlayerState, ...]
    deck: tuple[Card, ...] = ()
    pile: tuple[Card, ...] = ()
    current: int = 0
    locked: bool = False
    direction: int = 1
    finished: tuple[int, ...] = ()
    burned: tuple[Card, ...] = ()
    pending_blind_power: PendingBlindPower | None = None

    def __post_init__(self) -> None:
        if not 2 <= len(self.players) <= 6:
            raise ValueError("2 to 6 seats required")
        if not 0 <= self.current < len(self.players):
            raise ValueError("invalid current seat")
        if self.direction not in (-1, 1):
            raise ValueError("direction must be 1 or -1")
        if len(set(self.finished)) != len(self.finished):
            raise ValueError("duplicate finished player")
        if any(i < 0 or i >= len(self.players) for i in self.finished):
            raise ValueError("invalid finished player")


def _zone(state: OrdinaryState, player: PlayerState) -> str:
    if player.hand or state.deck:
        return "hand"
    if player.face_up:
        return "face_up"
    return "face_down"


def _legal_rank(state: OrdinaryState, rank: int) -> bool:
    if rank in (2, 7, 10):
        return True             # overrides comparisons, including a seven-lock
    if rank in (0, 3):
        return False            # handled by W2, not as an ordinary play
    if state.locked:
        return rank <= 7
    if not state.pile or state.pile[-1].rank == 2:
        return True
    return rank >= state.pile[-1].rank


def _next_seat(state: OrdinaryState, current: int, finished: tuple[int, ...]) -> int:
    for offset in range(1, len(state.players) + 1):
        seat = (current + state.direction * offset) % len(state.players)
        if seat not in finished:
            return seat
    raise IllegalPlay("match has no eligible players")


def _absorb_face_up(player: PlayerState) -> PlayerState:
    """D-022: once the stock is empty and the player holds fewer than three cards
    in hand, the three face-up cards are taken into hand automatically. This is a
    free action: it costs no turn and is applied wherever the state settles."""
    if not player.face_up or len(player.hand) >= 3:
        return player
    return replace(player, hand=player.hand + player.face_up, face_up=())


def _settle(state: OrdinaryState, player: PlayerState, *, extra_turn: bool) -> OrdinaryState:
    """After the entire action, refill/finish/advance. State already has its pile."""
    players = list(state.players)
    deck = state.deck
    if player.hand and deck:
        need = max(0, 3 - len(player.hand))
        player = replace(player, hand=player.hand + deck[:need])
        deck = deck[need:]
    # An empty hand with stock remaining is also refilled after playing its last card.
    elif not player.hand and deck:
        player = replace(player, hand=deck[:3])
        deck = deck[3:]
    players[state.current] = player
    # D-022: the stock never refills, so once it is empty every player whose hand
    # has fallen below three absorbs their face-up cards, not just the actor.
    if not deck:
        players = [_absorb_face_up(p) for p in players]
        player = players[state.current]
    finished = state.finished
    if not deck and not (player.hand or player.face_up or player.face_down):
        if state.current not in finished:
            finished = finished + (state.current,)
    next_player = state.current
    remaining = len(players) - len(finished)
    if remaining > 1 and (state.current in finished or not extra_turn):
        next_player = _next_seat(state, state.current, finished)
    if remaining == 1:
        next_player = next(i for i in range(len(players)) if i not in finished)
    return replace(state, players=tuple(players), deck=deck, finished=finished, current=next_player)


def _play_ordinary(state: OrdinaryState, player: PlayerState,
                   zone: str, indices: tuple[int, ...]) -> OrdinaryState:
    available = getattr(player, zone)
    if not indices or len(set(indices)) != len(indices) or any(not isinstance(i, int) or isinstance(i, bool) or i < 0 or i >= len(available) for i in indices):
        raise IllegalPlay("select distinct cards in the current zone")
    cards = tuple(available[i] for i in indices)
    rank = cards[0].rank
    if any(c.rank != rank for c in cards):
        raise IllegalPlay("group plays must have a single rank")
    if not _legal_rank(state, rank):
        raise IllegalPlay("card rank cannot be played on this pile")

    remaining = tuple(c for j, c in enumerate(available) if j not in set(indices))
    player = replace(player, **{zone: remaining})
    pile = state.pile + cards
    burn = rank == 10 or (len(pile) >= 4 and len({c.rank for c in pile[-4:]}) == 1)
    if burn:
        state = replace(state, pile=(), burned=state.burned + pile, locked=False)
    else:
        state = replace(state, pile=pile, locked=(rank == 7))
    return _settle(state, player, extra_turn=burn)


def _flip(state: OrdinaryState, player: PlayerState, indices: tuple[int, ...]) -> OrdinaryState:
    if len(indices) != 1 or not isinstance(indices[0], int) or indices[0] < 0 or indices[0] >= len(player.face_down):
        raise IllegalPlay("flip exactly one face-down card")
    pos = indices[0]
    card = player.face_down[pos]
    player = replace(player, face_down=player.face_down[:pos] + player.face_down[pos + 1:])
    if card.rank in (0, 3):
        # Keep the committed card in state until W2 resolves its target/counter.
        players = list(state.players)
        players[state.current] = player
        return replace(state, players=tuple(players),
                       pending_blind_power=PendingBlindPower(state.current, card))
    if not _legal_rank(state, card.rank):
        picked_up = state.pile + (card,)
        player = replace(player, hand=player.hand + picked_up)
        return _settle(replace(state, pile=(), locked=False), player, extra_turn=False)
    return _play_flipped(state, player, card)


def _play_flipped(state: OrdinaryState, player: PlayerState, card: Card) -> OrdinaryState:
    pile = state.pile + (card,)
    burn = card.rank == 10 or (len(pile) >= 4 and len({c.rank for c in pile[-4:]}) == 1)
    if burn:
        state = replace(state, pile=(), burned=state.burned + pile, locked=False)
    else:
        state = replace(state, pile=pile, locked=card.rank == 7)
    return _settle(state, player, extra_turn=burn)


def apply_play(state: OrdinaryState, zone: str, indices: Sequence[int]) -> OrdinaryState:
    """Return a new authoritative result, never changing the input state."""
    if state.pending_blind_power is not None:
        raise IllegalPlay("a blind 3/Joker must be resolved by the W2 match controller")
    if len(state.finished) >= len(state.players) - 1:
        raise IllegalPlay("match is finished")
    if state.current in state.finished:
        raise IllegalPlay("finished player cannot act")
    player = state.players[state.current]
    if zone != _zone(state, player):
        raise IllegalPlay("must play hand, then face-up, then face-down")
    indices = tuple(indices)
    if zone == "face_down":
        return _flip(state, player, indices)
    return _play_ordinary(state, player, zone, indices)



def pick_up(state: OrdinaryState) -> OrdinaryState:
    """Collect the pile and end the turn when no legal card can be played.

    A player with only blind face-down cards must flip, not choose pickup.
    A 3/Joker counts as an available W2 play and prevents forced pickup.
    """
    if state.pending_blind_power is not None:
        raise IllegalPlay("resolve pending blind power before another action")
    if len(state.finished) >= len(state.players) - 1 or state.current in state.finished:
        raise IllegalPlay("match has ended or current seat is finished")
    if not state.pile:
        raise IllegalPlay("cannot collect an empty pile")
    player = state.players[state.current]
    zone = _zone(state, player)
    if zone == "face_down":
        raise IllegalPlay("face-down cards must be flipped")
    if any(c.rank in (0, 3) or _legal_rank(state, c.rank)
           for c in getattr(player, zone)):
        raise IllegalPlay("a legal play exists; pickup is not forced")
    return _settle(
        replace(state, pile=(), locked=False),
        replace(player, hand=player.hand + state.pile),
        extra_turn=False,
    )


def can_play(state: OrdinaryState, zone: str, indices: Sequence[int]) -> bool:
    """Read-only legality check. An invalid request does not modify state."""
    try:
        apply_play(state, zone, indices)
        return True
    except IllegalPlay:
        return False


def loser(state: OrdinaryState) -> int | None:
    """Last player still holding cards when everybody else has finished."""
    if len(state.finished) != len(state.players) - 1:
        return None
    return next(i for i in range(len(state.players)) if i not in state.finished)


def winner(state: OrdinaryState) -> int | None:
    """First finisher, only once the match has concluded (for 2+ players)."""
    return state.finished[0] if loser(state) is not None else None
