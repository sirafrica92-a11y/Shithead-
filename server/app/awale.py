"""Awalé / Oware Abapa: independent, server-authoritative two-player engine.

Indexing follows the sowing path: south pits 0..5 left-to-right,
north pits 6..11 right-to-left. Sowing advances modulo 12, omitting
the source on each lap. Stores only hold captured seeds.

Rules chosen for this new game: Abapa (2/3 capture chains, compulsory
feeding, cancelled grand-slam captures, threefold no-capture repetition).
No existing Shithead or Ludo rules are modified.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import random
import secrets
from typing import Any

PITS = 12
SEEDS = 48
FIRST_TO_WIN = 25


class IllegalAwaleMove(ValueError):
    """Attempt to sow an unavailable pit, an out-of-turn move or ended game."""


@dataclass(frozen=True)
class AwaleMatch:
    pits: tuple[int, ...]
    captured: tuple[int, int]
    actor: int
    winner: int | None = None
    finished: bool = False
    turn_number: int = 0
    last_pit: int | None = None
    last_capture: tuple[int, ...] = ()
    event: str = ""
    # Signatures since most recent capture: repetition only counts when no
    # capture breaks the cycle. This is restored with the SQLite match.
    history: tuple[str, ...] = ()


def _signature(pits: tuple[int, ...], actor: int) -> str:
    return ",".join(str(n) for n in pits) + ":" + str(actor)


def make_awale_match(seed: int | None = None) -> AwaleMatch:
    starter = (random.Random(seed).randrange(2) if seed is not None
               else secrets.randbelow(2))
    pits = (4,) * PITS
    result = AwaleMatch(
        pits=pits, captured=(0, 0), actor=starter,
        event=f"Player {starter + 1} starts. Choose one of your six houses.",
        history=(_signature(pits, starter),),
    )
    assert_awale_invariants(result)
    return result


def _owns(seat: int, pit: int) -> bool:
    return seat * 6 <= pit < seat * 6 + 6


def _sow(pits: tuple[int, ...], origin: int) -> tuple[tuple[int, ...], int]:
    """Return resulting houses and final drop; never refill the origin."""
    next_pits = list(pits)
    seeds = next_pits[origin]
    next_pits[origin] = 0
    i = origin
    for _ in range(seeds):
        i = (i + 1) % PITS
        if i == origin:
            i = (i + 1) % PITS
        next_pits[i] += 1
    return tuple(next_pits), i


def legal_awale_pits(match: AwaleMatch, seat: int) -> tuple[int, ...]:
    if match.finished or type(seat) is not int or match.actor != seat:
        return ()
    choices = tuple(i for i in range(seat * 6, seat * 6 + 6)
                    if match.pits[i] > 0)
    if not choices:
        return ()
    # The opponent must be fed when their side is empty. This is checked
    # after sowing, before any potential capture.
    other = match.pits[(1 - seat) * 6:(2 - seat) * 6]
    if any(other):
        return choices
    return tuple(i for i in choices if
                 any(_sow(match.pits, i)[0][(1 - seat)*6:(2 - seat)*6]))


def _collect_remaining(match: AwaleMatch, event: str) -> AwaleMatch:
    p = match.pits
    counts = (match.captured[0] + sum(p[:6]),
              match.captured[1] + sum(p[6:]))
    winner = (0 if counts[0] > counts[1] else 1 if counts[1] > counts[0] else None)
    result = replace(match, pits=(0,) * 12, captured=counts,
                     winner=winner, finished=True, event=event,
                     history=())
    assert_awale_invariants(result)
    return result


def apply_awale_action(match: AwaleMatch, seat: int, kind: str,
                       *, pit: object = None) -> AwaleMatch:
    if match.finished:
        raise IllegalAwaleMove("The Awalé match has ended")
    if type(seat) is not int or seat != match.actor:
        raise IllegalAwaleMove("It is not your turn")
    if kind != "sow":
        raise IllegalAwaleMove("Unknown Awalé action")
    if type(pit) is not int or pit not in legal_awale_pits(match, seat):
        raise IllegalAwaleMove("Choose a highlighted house on your side")

    pits, last = _sow(match.pits, pit)
    captured_pits: list[int] = []
    # Only opponent houses can be captured, immediately behind final drop,
    # stopping at the first non-2/3 house or at own territory.
    if _owns(1 - seat, last):
        pos = last
        while _owns(1 - seat, pos) and pits[pos] in (2, 3):
            captured_pits.append(pos)
            pos = (pos - 1) % PITS

    # An Abapa grand slam that would empty every opposing house is void.
    if captured_pits and all(pits[i] == 0 or i in captured_pits
                             for i in range((1-seat)*6, (2-seat)*6)):
        captured_pits.clear()

    taken = sum(pits[i] for i in captured_pits)
    after = list(pits)
    for i in captured_pits:
        after[i] = 0
    scores = list(match.captured)
    scores[seat] += taken
    next_actor = 1 - seat
    next_pits = tuple(after)
    history = ((_signature(next_pits, next_actor),) if taken
               else match.history + (_signature(next_pits, next_actor),))
    event = (f"Player {seat + 1} sowed house {pit + 1}."
             + (f" Captured {taken} seeds!" if taken else ""))
    updated = AwaleMatch(
        pits=next_pits, captured=tuple(scores), actor=next_actor,
        turn_number=match.turn_number + 1, last_pit=last,
        last_capture=tuple(captured_pits), event=event,
        history=history,
    )
    if max(scores) >= FIRST_TO_WIN:
        result = replace(updated, finished=True,
                         winner=0 if scores[0] > scores[1] else 1,
                         event=event + " A player captured 25 seeds!")
    elif not legal_awale_pits(updated, next_actor):
        result = _collect_remaining(updated, event + " No legal feeding move; remaining seeds collected.")
    elif history.count(history[-1]) >= 3:
        result = _collect_remaining(updated, event + " Repeated position; remaining seeds collected.")
    else:
        result = updated
    assert_awale_invariants(result)
    return result


def assert_awale_invariants(match: AwaleMatch) -> None:
    if (len(match.pits) != PITS or len(match.captured) != 2
            or type(match.actor) is not int or match.actor not in (0, 1)
            or any(type(x) is not int or x < 0 or x > SEEDS
                   for x in match.pits + match.captured)
            or sum(match.pits) + sum(match.captured) != SEEDS):
        raise ValueError("Invalid Awalé state / seed conservation")
    if (type(match.turn_number) is not int or match.turn_number < 0
            or match.winner not in (0, 1, None)
            or (match.winner is not None and not match.finished)
            or (match.finished and any(match.pits) and
                max(match.captured) < FIRST_TO_WIN)
            or (match.winner is not None and
                match.captured[match.winner] <= match.captured[1-match.winner])
            or (match.last_pit is not None and
                (type(match.last_pit) is not int or not 0 <= match.last_pit < 12))
            or any(type(x) is not int or not 0 <= x < 12 for x in match.last_capture)
            or any(not isinstance(x, str) for x in match.history)):
        raise ValueError("Invalid Awalé score or match phase")


def public_awale_view(match: AwaleMatch) -> dict[str, Any]:
    return {
        "game_type": "awale",
        "phase": "FINISHED" if match.finished else "PLAYING",
        "pits": list(match.pits),
        "captured": list(match.captured),
        "actor": match.actor,
        "winner": match.winner,
        "turn_number": match.turn_number,
        "last_pit": match.last_pit,
        "last_capture": list(match.last_capture),
        "event": match.event,
    }


def private_awale_view(match: AwaleMatch, seat: int) -> dict[str, Any]:
    result = public_awale_view(match)
    result["your_legal_pits"] = list(legal_awale_pits(match, seat))
    return result


def dump_awale(match: AwaleMatch) -> dict[str, Any]:
    return asdict(match)


def restore_awale(data: dict[str, Any]) -> AwaleMatch:
    match = AwaleMatch(
        pits=tuple(data["pits"]),
        captured=tuple(data["captured"]),
        actor=data["actor"],
        winner=data.get("winner"),
        finished=data.get("finished", False),
        turn_number=data.get("turn_number", 0),
        last_pit=data.get("last_pit"),
        last_capture=tuple(data.get("last_capture", [])),
        event=data.get("event", ""),
        history=tuple(data.get("history", [])),
    )
    assert_awale_invariants(match)
    return match
