"""Pure, authoritative Ludo rules. Independent of the Shithead card engine.

A token is -1 (base), 0..50 (the 51 traversed shared-track cells),
or 51..56 (its six private home-lane cells; 56 is home).
A roll of six is required to leave base. Sixes are never penalised, even
three or more consecutively. Captures and sixes grant an extra roll.
Friendly token pairs form blockades that opponents cannot land on or cross.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, replace
import random
import secrets
from typing import Any

COLORS = ("red", "green", "yellow", "blue")
STARTS = (0, 13, 26, 39)
SAFE = frozenset((0, 8, 13, 21, 26, 34, 39, 47))
HOME = 56
TRACK_END = 50
PIECES_PER_PLAYER = 4


class IllegalLudoMove(ValueError):
    """The action is not allowed in this state."""


@dataclass(frozen=True)
class LudoPlayer:
    color: str
    tokens: tuple[int, int, int, int] = (-1, -1, -1, -1)


@dataclass(frozen=True)
class LudoMatch:
    players: tuple[LudoPlayer, ...]
    actor: int
    stage: str = "ROLL"  # ROLL or MOVE (never expose a playable die in ROLL)
    die: int | None = None
    last_roll: int | None = None
    winner: int | None = None
    turn_number: int = 0
    event: str = "Roll to begin."


def make_ludo_match(n_players: int, seed: int | None = None) -> LudoMatch:
    if n_players not in (2, 3, 4):
        raise ValueError("Ludo supports 2 to 4 players")
    colors = ("red", "yellow") if n_players == 2 else COLORS[:n_players]
    seat = random.Random(seed).randrange(n_players) if seed is not None else secrets.randbelow(n_players)
    return LudoMatch(players=tuple(LudoPlayer(color=c) for c in colors), actor=seat)


def track_square(player: LudoPlayer, progress: int) -> int | None:
    """Global 0..51 ring coordinate; private lanes/base have no ring cell."""
    if not isinstance(progress, int) or not 0 <= progress <= TRACK_END:
        return None
    return (STARTS[COLORS.index(player.color)] + progress) % 52


def _enemy_blockades(match: LudoMatch, seat: int) -> set[int]:
    blocked: set[int] = set()
    for i, p in enumerate(match.players):
        if i == seat:
            continue
        occupied: dict[int, int] = {}
        for pos in p.tokens:
            square = track_square(p, pos)
            if square is not None:
                occupied[square] = occupied.get(square, 0) + 1
        blocked.update(square for square, count in occupied.items() if count >= 2)
    return blocked


def legal_tokens(match: LudoMatch, seat: int, die: int) -> tuple[int, ...]:
    if type(die) is not int or not 1 <= die <= 6:
        raise IllegalLudoMove("A die must show 1 to 6")
    if seat != match.actor or match.winner is not None:
        return ()
    blockades = _enemy_blockades(match, seat)
    p = match.players[seat]
    result: list[int] = []
    for token, progress in enumerate(p.tokens):
        if progress == HOME:
            continue
        if progress == -1:
            if die == 6 and track_square(p, 0) not in blockades:
                result.append(token)
            continue
        destination = progress + die
        if destination > HOME:
            continue  # exact roll into home
        # Opponents' paired pieces are walls, including on safe squares.
        # The player's own blockade never blocks their own pieces.
        crossed = (track_square(p, step) for step in
                   range(progress + 1, min(destination, TRACK_END) + 1))
        if any(square in blockades for square in crossed):
            continue
        result.append(token)
    return tuple(result)


def assert_ludo_invariants(match: LudoMatch) -> None:
    if not 2 <= len(match.players) <= 4 or not 0 <= match.actor < len(match.players):
        raise ValueError("Invalid player count or turn")
    if len({p.color for p in match.players}) != len(match.players):
        raise ValueError("Duplicate Ludo colours")
    if any(p.color not in COLORS or len(p.tokens) != PIECES_PER_PLAYER
           or any(type(t) is not int or not -1 <= t <= HOME for t in p.tokens)
           for p in match.players):
        raise ValueError("Invalid Ludo token state")
    if match.stage not in ("ROLL", "MOVE"):
        raise ValueError("Invalid Ludo phase")
    if match.stage == "MOVE" and (match.die is None or
                                 not legal_tokens(match, match.actor, match.die)):
        raise ValueError("A move requires legal token choices")
    if match.stage == "ROLL" and match.die is not None:
        raise ValueError("Roll phase may not hold an unspent die")
    if match.winner is not None and (not 0 <= match.winner < len(match.players)
                                     or not all(x == HOME for x in
                                                match.players[match.winner].tokens)):
        raise ValueError("Winner must have four tokens home")


def apply_ludo_action(match: LudoMatch, seat: int, kind: str,
                      *, token: object = None, forced_roll: int | None = None) -> LudoMatch:
    """Commit a roll or move; forced_roll is ONLY for deterministic unit tests.

    The HTTP/WebSocket adapter MUST NOT forward any client-supplied die value.
    """
    if match.winner is not None:
        raise IllegalLudoMove("The match has ended")
    if type(seat) is not int or seat != match.actor:
        raise IllegalLudoMove("It is not your turn")

    if kind == "roll":
        if match.stage != "ROLL":
            raise IllegalLudoMove("Move a token before rolling again")
        if forced_roll is not None:
            if type(forced_roll) is not int or not 1 <= forced_roll <= 6:
                raise IllegalLudoMove("Invalid die")
            die = forced_roll
        else:
            die = secrets.randbelow(6) + 1
        possible = legal_tokens(match, seat, die)
        if possible:
            out = replace(match, stage="MOVE", die=die, last_roll=die,
                          event=f"Player {seat + 1} rolled {die}. Choose a token.")
        else:
            again = die == 6
            nxt = seat if again else (seat + 1) % len(match.players)
            out = replace(match, actor=nxt, stage="ROLL", die=None,
                          last_roll=die, turn_number=match.turn_number + 1,
                          event=(f"Player {seat + 1} rolled {die}; no legal move."
                                 + (" Roll again." if again else " Turn passed.")))
        assert_ludo_invariants(out)
        return out

    if kind != "move":
        raise IllegalLudoMove("Unknown Ludo action")
    if match.stage != "MOVE" or match.die is None:
        raise IllegalLudoMove("Roll the dice first")
    if type(token) is not int or token not in legal_tokens(match, seat, match.die):
        raise IllegalLudoMove("Select a highlighted legal token")

    players = list(match.players)
    own = players[seat]
    updated_tokens = list(own.tokens)
    previous = updated_tokens[token]
    destination = 0 if previous == -1 else previous + match.die
    updated_tokens[token] = destination
    players[seat] = replace(own, tokens=tuple(updated_tokens))

    captured = False
    square = track_square(players[seat], destination)
    if square is not None and square not in SAFE:
        for i, opponent in enumerate(players):
            if i == seat:
                continue
            enemy_tokens = list(opponent.tokens)
            for j, progress in enumerate(enemy_tokens):
                if track_square(opponent, progress) == square:
                    enemy_tokens[j] = -1
                    captured = True
            if enemy_tokens != list(opponent.tokens):
                players[i] = replace(opponent, tokens=tuple(enemy_tokens))

    won = all(progress == HOME for progress in players[seat].tokens)
    bonus = match.die == 6 or captured
    nxt = seat if bonus or won else (seat + 1) % len(players)
    event = (f"Player {seat + 1} brought all four tokens home!"
             if won else f"Player {seat + 1} moved token {token + 1}."
             + (" Capture! Roll again." if captured else
                " Six! Roll again." if bonus else ""))
    out = replace(match, players=tuple(players), actor=nxt, stage="ROLL",
                  die=None, winner=seat if won else None,
                  turn_number=match.turn_number + 1, event=event)
    assert_ludo_invariants(out)
    return out


def public_ludo_view(match: LudoMatch) -> dict[str, Any]:
    return {
        "game_type": "ludo",
        "phase": "FINISHED" if match.winner is not None else "PLAYING",
        "turn_stage": match.stage,
        "actor": match.actor,
        "die": match.die,
        "last_roll": match.last_roll,
        "winner": match.winner,
        "turn_number": match.turn_number,
        "event": match.event,
        "safe_squares": sorted(SAFE),
        "players": [
            {"seat": i, "color": p.color, "tokens": list(p.tokens),
             "finished": all(x == HOME for x in p.tokens)}
            for i, p in enumerate(match.players)
        ],
    }


def private_ludo_view(match: LudoMatch, seat: int) -> dict[str, Any]:
    out = public_ludo_view(match)
    out["your_legal_tokens"] = (
        list(legal_tokens(match, seat, match.die))
        if match.winner is None and match.stage == "MOVE"
        and seat == match.actor and match.die is not None else []
    )
    return out


def dump_ludo(match: LudoMatch) -> dict[str, Any]:
    return asdict(match)


def restore_ludo(data: dict[str, Any]) -> LudoMatch:
    match = LudoMatch(
        players=tuple(LudoPlayer(color=p["color"], tokens=tuple(p["tokens"]))
                      for p in data["players"]),
        actor=data["actor"], stage=data.get("stage", "ROLL"),
        die=data.get("die"), last_roll=data.get("last_roll"),
        winner=data.get("winner"), turn_number=data.get("turn_number", 0),
        event=data.get("event", ""),
    )
    assert_ludo_invariants(match)
    return match
