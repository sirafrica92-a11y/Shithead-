"""Small, explicit game catalogue. No gameplay or state mutation here.

Contract: adding a game requires one metadata entry here, its own engine and
client renderer. The existing reducers, WebSocket protocol, persistence keys
and room state remain authoritative and unchanged by this catalogue.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class GameSpec:
    key: str
    name: str
    min_players: int
    max_players: int

    def valid_capacity(self, capacity: int) -> bool:
        return type(capacity) is int and self.min_players <= capacity <= self.max_players


GAMES: dict[str, GameSpec] = {
    "shithead": GameSpec("shithead", "Shithead", 2, 6),
    "ludo": GameSpec("ludo", "Ludo", 2, 4),
    "awale": GameSpec("awale", "Awalé", 2, 2),
    "dara": GameSpec("dara", "Dara", 2, 2),
}


def game_spec(game_type: str) -> GameSpec:
    """Reject unknown game types; never silently fall back to Shithead."""
    try:
        return GAMES[game_type]
    except (KeyError, TypeError) as exc:
        raise ValueError("unknown game") from exc


def capacity_after_switch(game_type: str, current: int, occupied: int) -> int:
    """Preserve established Shithead/Ludo lobby transitions exactly."""
    spec = game_spec(game_type)
    if occupied > spec.max_players:
        raise ValueError("too_many_players")
    if game_type == "shithead":
        return max(2, current)
    if game_type == "ludo":
        return max(occupied, min(current, spec.max_players))
    return spec.min_players


def capacity_options(game_type: str) -> tuple[int, ...]:
    spec = game_spec(game_type)
    return tuple(range(spec.min_players, spec.max_players + 1))
