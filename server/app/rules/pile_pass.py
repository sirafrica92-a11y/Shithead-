"""Pile / 3-Joker attack state machine for Shithead (work packet W2).

Pure deterministic reducer for ONE resolved pile action, driven by a
server-authoritative actor. It deliberately imports nothing from
``server/app/rules/turns.py`` so W1 stays untouched; the W1
``resolve_next_actor`` is composed by the caller AFTER this reducer reaches a
terminal state, which is where turn anchoring (D-002) and extra skips (D-014)
are applied.

Scope (docs/WORK_PACKETS.md W2): PLAYING -> PILE_PASS_DECISION -> RESOLVED,
one 3/Joker attack, an optional counter chain, an accepted pickup, an
allowed-action whitelist, removed-from-game cards, and authoritative errors.
Ordinary rank play and endgame are W3.

Confirmed rules honoured here:
  D-001  3/Joker share attack and defence; a counter may redirect to any
         other player, including a previous attacker.
  D-002  Turn advancement is NOT decided here (anchored to the original
         actor, applied by the caller via W1).
  D-003  An empty-pile 3/Joker skips the next seat (elective per D-015).
  D-004  Multiple 3/Jokers may attach extra skips to one attack.
  D-014  Extra skips stay attached through counter chains, never resolve
         mid-chain; a counter does not erase them.
  D-015  On an empty pile a player MAY spend a 3/Joker to skip even while
         holding a playable ordinary card; the spent card is removed.
  D-016  No mid-action refills; resolution completes before any draw.

OPEN (rejected here): O-09 timeouts (a pure reducer has no clock) and O-10
non-playing phase ownership (out of this slice's scope).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet, Optional, Tuple


class IllegalTransition(ValueError):
    """Rejected action. Recoverable per D-006: the state is left unchanged."""


class Phase(Enum):
    PLAYING = "PLAYING"                        # idle; actor may open an attack or empty-pile skip
    PILE_PASS_DECISION = "PILE_PASS_DECISION"  # a live attack awaits ACCEPT or COUNTER
    RESOLVED = "RESOLVED"                      # terminal for this slice


@dataclass(frozen=True)
class Attack:
    """A live 3/Joker attack and every card it has spent (removed from game)."""
    original_actor: str
    target: str
    extra_skips: int = 0            # D-014: stay attached, never resolve mid-chain
    spent: Tuple[str, ...] = ()     # 3s / Jokers removed from the game when played
    chain: Tuple[str, ...] = ()     # ordered actors who have handled this attack


@dataclass(frozen=True)
class PileState:
    """Immutable state of one pile action."""
    seats: Tuple[str, ...]          # currently eligible seats, clockwise
    actor: str                      # the single authoritative actor (D-006)
    phase: Phase = Phase.PLAYING
    attack: Optional[Attack] = None
    removed: FrozenSet[str] = frozenset()   # cards removed from the game
    version: int = 0                # optimistic-concurrency token


@dataclass(frozen=True)
class Attack3Joker:
    """Open an attack on ``target``; optionally declare extra skips (D-004).

    ``cards`` is the 3s/Jokers spent for the attack itself (at least one).
    ``extra_skip_cards`` are additional 3s/Jokers spent for skips, one per
    skip. All spent cards are removed from the game."""
    target: str
    cards: Tuple[str, ...] = ("3",)
    extra_skip_cards: Tuple[str, ...] = ()


@dataclass(frozen=True)
class Counter:
    """Redirect the live attack to any other seat (D-001)."""
    new_target: str
    cards: Tuple[str, ...] = ("3",)


@dataclass(frozen=True)
class Accept:
    """The current target takes the pile; the attack resolves."""


@dataclass(frozen=True)
class EmptyPileSkip:
    """Spend a 3/Joker to skip on an empty pile (D-003, D-015). Elective."""
    cards: Tuple[str, ...] = ("3",)


def initial_state(seats, actor: str) -> PileState:
    """Build the idle state. 2-6 unique seats; the actor must be seated."""
    seats = tuple(seats)
    if not 2 <= len(seats) <= 6:
        raise ValueError("games have 2 to 6 seats")
    if len(set(seats)) != len(seats):
        raise ValueError("seats must be unique")
    if actor not in seats:
        raise ValueError(f"actor {actor!r} is not seated")
    return PileState(seats=seats, actor=actor)


def allowed_actions(state: PileState) -> Tuple[type, ...]:
    """The authoritative action whitelist for the current phase."""
    if state.phase is Phase.PLAYING:
        return (Attack3Joker, EmptyPileSkip)
    if state.phase is Phase.PILE_PASS_DECISION:
        return (Accept, Counter)
    return ()


def reduce(
    state: PileState,
    action,
    *,
    actor: Optional[str] = None,
    version: Optional[int] = None,
) -> PileState:
    """Apply ``action`` and return the new state; never mutate ``state``.

    Raises IllegalTransition for any out-of-phase action, wrong actor, stale
    version, unknown target, or replay. The input state is left untouched, so
    a rejected action is recoverable (D-006)."""
    if version is not None and version != state.version:
        raise IllegalTransition(
            f"stale version {version}; current is {state.version}"
        )
    if type(action) not in allowed_actions(state):
        raise IllegalTransition(
            f"{type(action).__name__} is not legal in phase {state.phase.value}"
        )
    if actor is not None and actor != state.actor:
        raise IllegalTransition(f"wrong actor {actor!r}; expected {state.actor!r}")

    if state.phase is Phase.PLAYING:
        return _open(state, action)
    if state.phase is Phase.PILE_PASS_DECISION:
        if isinstance(action, Accept):
            return _accept(state)
        return _counter(state, action)
    raise IllegalTransition(f"no actions in phase {state.phase.value}")


def _open(state: PileState, action) -> PileState:
    if isinstance(action, EmptyPileSkip):
        if not action.cards:
            raise IllegalTransition("an empty-pile skip spends one 3/Joker")
        return PileState(
            seats=state.seats, actor=state.actor, phase=Phase.RESOLVED,
            attack=None, removed=state.removed | frozenset(action.cards),
            version=state.version + 1,
        )
    # Attack3Joker
    if not action.cards:
        raise IllegalTransition("an attack spends at least one 3/Joker")
    if action.target not in state.seats:
        raise IllegalTransition(f"target {action.target!r} is not seated")
    if action.target == state.actor:
        raise IllegalTransition("cannot attack yourself")
    attack = Attack(
        original_actor=state.actor, target=action.target,
        extra_skips=len(action.extra_skip_cards),
        spent=tuple(action.cards) + tuple(action.extra_skip_cards),
        chain=(state.actor,),
    )
    return PileState(
        seats=state.seats, actor=action.target,  # exactly one owner: the target
        phase=Phase.PILE_PASS_DECISION, attack=attack,
        removed=state.removed | frozenset(attack.spent),
        version=state.version + 1,
    )


def _accept(state: PileState) -> PileState:
    attack = state.attack
    assert attack is not None
    return PileState(
        seats=state.seats, actor=state.actor,  # the collector; caller composes W1
        phase=Phase.RESOLVED,
        attack=attack,  # kept so the caller reads extra_skips / original_actor
        removed=state.removed, version=state.version + 1,
    )


def _counter(state: PileState, action: Counter) -> PileState:
    attack = state.attack
    assert attack is not None
    if not action.cards:
        raise IllegalTransition("a counter spends one 3/Joker")
    if action.new_target not in state.seats:
        raise IllegalTransition(f"target {action.new_target!r} is not seated")
    if action.new_target == state.actor:
        raise IllegalTransition("cannot redirect to yourself")
    new_attack = Attack(
        original_actor=attack.original_actor, target=action.new_target,
        extra_skips=attack.extra_skips,         # D-014: a counter does not erase skips
        spent=attack.spent + tuple(action.cards),
        chain=attack.chain + (state.actor,),
    )
    return PileState(
        seats=state.seats, actor=action.new_target,
        phase=Phase.PILE_PASS_DECISION, attack=new_attack,
        removed=state.removed | frozenset(action.cards),
        version=state.version + 1,
    )
