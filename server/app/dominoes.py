"""Jamaican Partner Dominoes (four seats, two opposing partnerships).

Rule sources: pagat.com/domino/line/caribbean.html (Jamaica / Partner),
jamaicans.com/dominoesjastyle/, and sixlove.app/partner-domino/.

Specific variant: 28 double-six bones, 7 per player, 0+2 vs 1+3, anti-
clockwise turns (in seat order), first pose 6-6, match two line ends or
compulsory pass, blocked hand by lowest individual pip count, Jamaican
six-love reset, winner-team pose on later hands, two-point key-bone finish.
All hidden hands are private to their authenticated seat.
"""
from __future__ import annotations

import random
from dataclasses import asdict, dataclass, replace
from typing import Any

Bone = tuple[int, int]
ALL_BONES: tuple[Bone, ...] = tuple((a, b) for a in range(7) for b in range(a, 7))
SIX_LOVE = 6


class IllegalDominoMove(ValueError):
    pass


@dataclass(frozen=True)
class DominoMatch:
    hands: tuple[tuple[Bone, ...], ...]
    chain: tuple[Bone, ...] = ()  # tiles oriented from left to right
    left_end: int | None = None
    right_end: int | None = None
    actor: int = 0
    stage: str = "PLAYING"  # PLAYING, HAND_OVER, FINISHED
    scores: tuple[int, int] = (0, 0)
    hand_number: int = 1
    require_double_six: bool = True
    next_pose_team: int | None = None
    last_hand_team: int | None = None
    last_hand_player: int | None = None
    last_hand_points: int = 0
    winner_team: int | None = None
    turn_number: int = 0
    event: str = ""


def _shuffled_hands(seed: int | None = None) -> tuple[tuple[Bone, ...], ...]:
    rng = random.Random(seed) if seed is not None else random.SystemRandom()
    tiles = list(ALL_BONES)
    rng.shuffle(tiles)
    return tuple(tuple(tiles[i * 7:(i + 1) * 7]) for i in range(4))


def make_domino_match(seed: int | None = None) -> DominoMatch:
    hands = _shuffled_hands(seed)
    poser = next(i for i, hand in enumerate(hands) if (6, 6) in hand)
    match = DominoMatch(hands=hands, actor=poser,
                        event="Double-six poses the opening hand. Partners: 1 & 3 versus 2 & 4.")
    assert_domino_invariants(match)
    return match


def _playable_sides(match: DominoMatch, bone: Bone) -> tuple[str, ...]:
    if not match.chain:
        return ("left",) if not match.require_double_six or bone == (6, 6) else ()
    return tuple(side for side, end in
                 (("left", match.left_end), ("right", match.right_end))
                 if end in bone)


def legal_domino_actions(match: DominoMatch, seat: int) -> dict[str, Any]:
    empty = {"plays": [], "pass": False, "next_hand": False}
    if type(seat) is not int or seat not in range(4) or match.stage == "FINISHED":
        return empty
    if match.stage == "HAND_OVER":
        empty["next_hand"] = (match.next_pose_team is None or
                               seat % 2 == match.next_pose_team)
        return empty
    if seat != match.actor:
        return empty
    plays = [{"index": i, "sides": list(sides)}
             for i, bone in enumerate(match.hands[seat])
             if (sides := _playable_sides(match, bone))]
    return {"plays": plays, "pass": not plays, "next_hand": False}


def _hard_key_finish(match: DominoMatch, bone: Bone) -> bool:
    if (not match.chain or match.left_end == match.right_end or
            set(bone) != {match.left_end, match.right_end} or bone[0] == bone[1]):
        return False
    left_count = sum(t.count(match.left_end) for t in match.chain)
    right_count = sum(t.count(match.right_end) for t in match.chain)
    return left_count == 7 and right_count == 7


def _end_hand(match: DominoMatch, team: int | None, seat: int | None,
              *, points: int = 1, reason: str) -> DominoMatch:
    if team is None:
        return replace(match, stage="HAND_OVER", next_pose_team=None,
                       last_hand_team=None, last_hand_player=None,
                       last_hand_points=0,
                       event=reason + " Hand tied: double-six poses next.")
    scores = list(match.scores)
    if scores[1 - team]:
        # Authentic six-love format: opposing team breaks a run to reset 0-0.
        scores = [0, 0]
        next_pose_team = None
        extra = " Six-love run broken; scores reset to 0-0. Double-six poses next."
    else:
        scores[team] += points
        next_pose_team = team
        extra = f" Team {team + 1} scores {points} point(s)."
    champion = team if scores[team] >= SIX_LOVE else None
    return replace(match, stage="FINISHED" if champion is not None else "HAND_OVER",
                   scores=tuple(scores), winner_team=champion,
                   next_pose_team=next_pose_team, last_hand_team=team,
                   last_hand_player=seat, last_hand_points=points,
                   event=reason + extra + (" SIX LOVE!" if champion is not None else ""))


def _finish_if_blocked(match: DominoMatch) -> DominoMatch:
    if match.stage != "PLAYING" or not match.chain:
        return match
    if any(_playable_sides(match, bone) for hand in match.hands for bone in hand):
        return match
    totals = [sum(a + b for a, b in hand) for hand in match.hands]
    least = min(totals)
    winners = [seat for seat, total in enumerate(totals) if total == least]
    teams = {seat % 2 for seat in winners}
    if len(teams) == 2:
        return _end_hand(match, None, None,
                         reason="Blocked: opposing players tie for lowest pips.")
    winning_seat = winners[0]
    return _end_hand(match, winning_seat % 2, winning_seat,
                     reason=f"Blocked: Player {winning_seat + 1} has the fewest pips ({least}).")


def apply_domino_action(match: DominoMatch, seat: int, kind: str,
                        *, index: object = None, side: object = None) -> DominoMatch:
    if type(seat) is not int or seat not in range(4):
        raise IllegalDominoMove("Seat does not belong to this four-player table.")
    if match.stage == "FINISHED":
        raise IllegalDominoMove("Six-love match has finished.")
    if match.stage == "HAND_OVER":
        if kind != "next_hand" or (match.next_pose_team is not None and
                                   seat % 2 != match.next_pose_team):
            raise IllegalDominoMove("Only a member of the winning partnership can pose next.")
        fresh = _shuffled_hands()
        must_pose_six = match.next_pose_team is None
        first_actor = (next(i for i, hand in enumerate(fresh) if (6, 6) in hand)
                       if must_pose_six else seat)
        nxt = replace(match, hands=fresh, chain=(), left_end=None, right_end=None,
                      actor=first_actor, stage="PLAYING", hand_number=match.hand_number + 1,
                      require_double_six=must_pose_six, next_pose_team=None,
                      last_hand_team=None, last_hand_player=None, last_hand_points=0,
                      event=("Double-six starts the new hand." if must_pose_six
                             else f"Player {seat + 1} poses for their team."),
                      turn_number=match.turn_number + 1)
        assert_domino_invariants(nxt)
        return nxt
    if seat != match.actor:
        raise IllegalDominoMove("Not your turn.")
    legal = legal_domino_actions(match, seat)
    if kind == "pass":
        if not legal["pass"]:
            raise IllegalDominoMove("Pass only when no tile fits an open end.")
        nxt = replace(match, actor=(seat + 1) % 4,
                      turn_number=match.turn_number + 1,
                      event=f"Player {seat + 1} passes.")
        return _finish_if_blocked(nxt)
    if kind != "play" or type(index) is not int or not 0 <= index < len(match.hands[seat]):
        raise IllegalDominoMove("Choose a valid tile.")
    valid = next((x["sides"] for x in legal["plays"] if x["index"] == index), ())
    if side not in valid:
        raise IllegalDominoMove("Tile cannot be played on that end.")
    bone = match.hands[seat][index]
    key_finish = len(match.hands[seat]) == 1 and _hard_key_finish(match, bone)
    if not match.chain:
        oriented = bone
        chain = (oriented,)
    elif side == "left":
        oriented = bone if bone[1] == match.left_end else (bone[1], bone[0])
        chain = (oriented,) + match.chain
    else:
        oriented = bone if bone[0] == match.right_end else (bone[1], bone[0])
        chain = match.chain + (oriented,)
    hands = list(match.hands)
    hands[seat] = match.hands[seat][:index] + match.hands[seat][index + 1:]
    nxt = replace(match, hands=tuple(hands), chain=chain,
                  left_end=chain[0][0], right_end=chain[-1][1],
                  actor=(seat + 1) % 4, require_double_six=False,
                  turn_number=match.turn_number + 1,
                  event=f"Player {seat + 1} played {bone[0]}-{bone[1]}.")
    if not hands[seat]:
        result = _end_hand(nxt, seat % 2, seat, points=2 if key_finish else 1,
                           reason=f"Domino! Player {seat + 1} emptied their hand." +
                                  (" Key-bone finish!" if key_finish else ""))
    else:
        result = _finish_if_blocked(nxt)
    assert_domino_invariants(result)
    return result


def assert_domino_invariants(match: DominoMatch) -> None:
    if (len(match.hands) != 4 or match.stage not in ("PLAYING", "HAND_OVER", "FINISHED")
            or type(match.actor) is not int or match.actor not in range(4)
            or len(match.scores) != 2 or any(type(x) is not int or x < 0 for x in match.scores)
            or match.next_pose_team not in (None, 0, 1)
            or match.winner_team not in (None, 0, 1)):
        raise ValueError("Invalid partner dominoes metadata.")
    raw = [tuple(sorted(b)) for hand in match.hands for b in hand]
    raw += [tuple(sorted(b)) for b in match.chain]
    if (len(raw) != 28 or set(raw) != set(ALL_BONES) or
            any(len(b) != 2 or any(type(v) is not int or not 0 <= v <= 6 for v in b)
                for b in raw)):
        raise ValueError("Domino set missing, duplicated or invalid.")
    if match.chain:
        if (match.left_end != match.chain[0][0] or
                match.right_end != match.chain[-1][1] or
                any(a[1] != b[0] for a, b in zip(match.chain, match.chain[1:]))):
            raise ValueError("Domino layout ends do not match.")
    elif match.left_end is not None or match.right_end is not None:
        raise ValueError("Empty domino layout cannot have open ends.")
    if match.stage == "FINISHED" and match.winner_team is None:
        raise ValueError("Completed six-love match has no winning team.")


def public_domino_view(match: DominoMatch) -> dict[str, Any]:
    return {
        "game_type": "dominoes", "phase": "FINISHED" if match.stage == "FINISHED" else "PLAYING",
        "stage": match.stage, "actor": match.actor, "chain": [list(b) for b in match.chain],
        "ends": [match.left_end, match.right_end],
        "hand_counts": [len(hand) for hand in match.hands],
        "scores": list(match.scores), "winner_team": match.winner_team,
        "last_hand_team": match.last_hand_team, "last_hand_player": match.last_hand_player,
        "last_hand_points": match.last_hand_points, "next_pose_team": match.next_pose_team,
        "hand_number": match.hand_number, "turn_number": match.turn_number,
        "event": match.event,
    }


def private_domino_view(match: DominoMatch, seat: int) -> dict[str, Any]:
    out = public_domino_view(match)
    out["hand"] = [list(b) for b in match.hands[seat]]
    out["legal"] = legal_domino_actions(match, seat)
    return out


def dump_domino(match: DominoMatch) -> dict[str, Any]:
    return asdict(match)


def restore_domino(data: dict[str, Any]) -> DominoMatch:
    restored = DominoMatch(
        hands=tuple(tuple(tuple(b) for b in hand) for hand in data["hands"]),
        chain=tuple(tuple(b) for b in data.get("chain", [])),
        left_end=data.get("left_end"), right_end=data.get("right_end"),
        actor=data["actor"], stage=data.get("stage", "PLAYING"),
        scores=tuple(data.get("scores", [0, 0])), hand_number=data.get("hand_number", 1),
        require_double_six=data.get("require_double_six", True),
        next_pose_team=data.get("next_pose_team"),
        last_hand_team=data.get("last_hand_team"),
        last_hand_player=data.get("last_hand_player"),
        last_hand_points=data.get("last_hand_points", 0),
        winner_team=data.get("winner_team"), turn_number=data.get("turn_number", 0),
        event=data.get("event", ""),
    )
    assert_domino_invariants(restored)
    return restored
