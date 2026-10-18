"""W2 - pile-pass reducer (the 3/Joker attack). Pure, deterministic, immutable.

``resolve_next_actor`` is composed by the caller AFTER this reducer reaches a
terminal RESOLVED state. This reducer never mutates its input state: it returns
new ``PileState`` values. Its only authority is PLAYING -> PILE_PASS_DECISION ->
RESOLVED and the acceptance/counter mechanics - attack targeting, accept/counter
ownership, skip-card count, and removal of spent 3s/Jokers from the game.

It deliberately holds no deck, hands or pile card list: those belong to the
ordinary-play reducer (W3). ``removed`` is the shared authority the pile-pass
gameplay owns.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class IllegalTransition(Exception):
    """Raised when an action is not legal in the current phase, or is a replay."""


class Phase(Enum):
    PLAYING = "playing"
    PILE_PASS_DECISION = "pile_pass_decision"
    RESOLVED = "resolved"


@dataclass(frozen=True)
class Attack3Joker:
    target: str
    cards: Tuple[str, ...] = ("3",)
    extra_skip_cards: Tuple[str, ...] = ()


@dataclass(frozen=True)
class EmptyPileSkip:
    cards: Tuple[str, ...] = ("3",)


@dataclass(frozen=True)
class Accept:
    pass


@dataclass(frozen=True)
class Counter:
    new_target: str
    cards: Tuple[str, ...] = ("3",)


@dataclass(frozen=True)
class Attack:
    original_actor: str
    target: str
    extra_skips: int
    spent: Tuple[str, ...]
    chain: Tuple[str, ...]


@dataclass(frozen=True)
class PileState:
    seats: Tuple[str, ...]
    actor: str
    phase: Phase
    attack: Optional[Attack]
    removed: frozenset
    version: int


def initial_state(seats, actor):
    return PileState(
        seats=tuple(seats), actor=actor, phase=Phase.PLAYING,
        attack=None, removed=frozenset(), version=0,
    )


def allowed_actions(state: PileState):
    if state.phase is Phase.PLAYING:
        return (Attack3Joker, EmptyPileSkip)
    if state.phase is Phase.PILE_PASS_DECISION:
        return (Accept, Counter)
    return ()


def reduce(
    state: PileState,
    action,
    *,
    actor: str,
    version: Optional[int] = None,
) -> PileState:
    """Apply ``action`` and return the new state; never mutate ``state``.

    Raises IllegalTransition for any out-of-phase action, wrong or missing
    actor, stale version, unknown target, or replay. The input state is left
    untouched, so a rejected action is recoverable (D-006).

    ``actor`` is mandatory (D-006): the server must always name the seat it is
    acting for, and a missing or mismatched actor is rejected. ``version``
    remains optional optimistic-concurrency."""
    if version is not None and version != state.version:
        raise IllegalTransition(
            f"stale version {version}; current is {state.version}"
        )
    if type(action) not in allowed_actions(state):
        raise IllegalTransition(
            f"{type(action).__name__} is not legal in phase {state.phase.value}"
        )
    if actor != state.actor:
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
