"""Pure turn-seat resolution for the 3/Joker pile attack (work packet W1).

No game state, no cards, no I/O: given who played, who finally collected,
and how many extra skips were validated, decide who acts next.

Implements docs/RULES.md ("Power cards"/"3 and Joker" and "Goal and players":
2-6 players), docs/SCENARIO_MATRIX.md (seat-order scenarios, redirect and
empty-pile examples) and docs/TURN_ENGINE.md (counterexamples to naive turn
advancement, multi-3/Joker sequencing). The collector loses the immediate
turn only when they were the next scheduled player; an empty-pile 3/Joker
skips the next scheduled player; the anchor is always the original actor.

Deliberately NOT implemented (OPEN, awaiting owner decision): O-04 (attack +
extra skips + counter interaction) and O-05 (empty-pile skip while ordinary
cards exist), both in docs/DECISION_LOG.md.
"""

from collections.abc import Sequence


def resolve_next_actor(
    seats: Sequence[str],
    original_actor: str,
    final_collector: str | None,
    extra_skips: int = 0,
) -> str:
    """Return the seat that acts next after a resolved 3/Joker attack.

    The result is always derived from ``original_actor``'s scheduled order;
    whoever countered last is irrelevant. ``seats`` is the clockwise order of
    currently eligible seats (caller removes finished/ineligible players).
    ``final_collector`` is the seat that accepted the pile (may equal
    ``original_actor``); ``None`` means an empty-pile 3/Joker that skips the
    next scheduled player. ``extra_skips`` bypasses further seats in order.
    """
    if not 2 <= len(seats) <= 6:
        raise ValueError("games have 2 to 6 seats")
    if len(set(seats)) != len(seats):
        raise ValueError("seats must be unique")
    if original_actor not in seats:
        raise ValueError(f"original actor {original_actor!r} is not seated")
    if final_collector is not None and final_collector not in seats:
        raise ValueError(f"final collector {final_collector!r} is not seated")
    if extra_skips < 0:
        raise ValueError("extra_skips cannot be negative")

    n = len(seats)
    nxt = (seats.index(original_actor) + 1) % n

    if final_collector is None:
        # Empty pile: the 3/Joker itself skips the scheduled next player.
        nxt = (nxt + 1) % n
    elif final_collector == seats[nxt]:
        # The collector was due to act next and loses that turn.
        nxt = (nxt + 1) % n

    return seats[(nxt + extra_skips) % n]
