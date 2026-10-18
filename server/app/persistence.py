"""Strict JSON storage for local Shithead games; no pickle or secrets.

Dataclass serialisation is schema-specific so private game cards remain only
in the local database, never a public room snapshot.
"""
from __future__ import annotations

from dataclasses import asdict
import hashlib
from typing import Any

from server.app.gameplay import Match
from server.app.rules.ordinary import (
    Card, OrdinaryState, PendingBlindPower, PlayerState,
)
from server.app.rules.pile_pass import Attack, Phase, PileState


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def restore_card(data: dict[str, Any]) -> Card:
    return Card(rank=data["rank"], suit=data["suit"], id=data.get("id"))


def restore_players(data: list[dict[str, Any]]) -> tuple[PlayerState, ...]:
    return tuple(PlayerState(
        hand=tuple(restore_card(c) for c in p["hand"]),
        face_up=tuple(restore_card(c) for c in p["face_up"]),
        face_down=tuple(restore_card(c) for c in p["face_down"]),
    ) for p in data)


def dump_match(match: Match | None) -> dict[str, Any] | None:
    if match is None:
        return None
    d = asdict(match)
    d["pending"] = None
    if match.pending is not None:
        p = asdict(match.pending)
        p["phase"] = match.pending.phase.value
        p["removed"] = sorted(match.pending.removed)
        d["pending"] = p
    return d


def restore_match(data: dict[str, Any] | None) -> Match | None:
    if data is None:
        return None
    x = data["state"]
    blind = x.get("pending_blind_power")
    state = OrdinaryState(
        players=restore_players(x["players"]),
        deck=tuple(restore_card(c) for c in x["deck"]),
        pile=tuple(restore_card(c) for c in x["pile"]),
        burned=tuple(restore_card(c) for c in x["burned"]),
        current=x["current"],
        locked=x["locked"],
        direction=x["direction"],
        finished=tuple(x["finished"]),
        pending_blind_power=PendingBlindPower(
            actor=blind["actor"], card=restore_card(blind["card"])
        ) if blind is not None else None,
    )
    pending = data.get("pending")
    parsed = None
    if pending is not None:
        attack = pending.get("attack")
        parsed = PileState(
            seats=tuple(pending["seats"]),
            actor=pending["actor"],
            phase=Phase(pending["phase"]),
            attack=Attack(
                original_actor=attack["original_actor"],
                target=attack["target"],
                extra_skips=attack["extra_skips"],
                spent=tuple(attack["spent"]),
                chain=tuple(attack["chain"]),
            ) if attack is not None else None,
            removed=frozenset(pending["removed"]),
            version=pending["version"],
        )
    return Match(
        state=state, pending=parsed,
        power_removed=tuple(restore_card(c) for c in data["power_removed"]),
        power_actors=tuple(data["power_actors"]),
        start_seat=data.get("start_seat", state.current),
    )
