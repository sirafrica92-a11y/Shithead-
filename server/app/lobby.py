"""Development-only multiplayer rooms with optional local SQLite recovery.

Rooms are identified by a short, shareable code and have no password: anyone
holding the code may take a free seat. Privacy still rests on the seat token,
which is issued once per seat, never appears in a public snapshot, and is the
only thing that authenticates a socket or restores a seat after a drop.

Public snapshots never contain seat tokens. A token grants control of exactly
one seat for the lifetime of this process; it is not a user account.
"""

from __future__ import annotations

import asyncio
import json
import re
import secrets
import sqlite3
import threading
import time
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket
from server.app.gameplay import Match, private_match_view, public_match_view
from server.app.persistence import dump_match, restore_match


# Codes are read aloud and typed by hand, so they are short, case-insensitive
# and drawn from a single uppercase alphanumeric alphabet (36**4 = 1_679_616).
ROOM_CODE_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
ROOM_CODE_LENGTH = 4
ROOM_CODE_RE = re.compile(f"^[A-Z0-9]{{{ROOM_CODE_LENGTH}}}$")
MAX_ROOM_CODE_INPUT = 64  # refuse unbounded lookup keys before touching the store


def normalise_room_code(raw: str) -> str:
    """One spelling for a typed code: trimmed and upper-cased."""
    return (raw or "").strip().upper()


def is_room_code(value: str) -> bool:
    return bool(ROOM_CODE_RE.match(value))


class RateLimiter:
    """Fixed-window limiter, keyed by client, to make code guessing impractical.

    Only *failed* lookups are recorded, so ordinary play is never throttled
    while a scan of the code space is stopped after a handful of misses.
    """

    def __init__(self, limit: int, window: float, clock=time.monotonic):
        self.limit = limit
        self.window = window
        self.clock = clock
        self.hits: dict[str, list[float]] = {}

    def allow(self, key: str) -> bool:
        now = self.clock()
        recent = [t for t in self.hits.get(key, ()) if now - t < self.window]
        if len(recent) >= self.limit:
            self.hits[key] = recent
            return False
        recent.append(now)
        self.hits[key] = recent
        if len(self.hits) > 4096:
            self._evict(now)
        return True

    def _evict(self, now: float) -> None:
        for key in [k for k, v in self.hits.items()
                    if all(now - t >= self.window for t in v)]:
            del self.hits[key]


@dataclass
class Seat:
    name: str
    token_digest: str
    ready: bool = False
    socket: WebSocket | None = None
    request_ids: list[str] = field(default_factory=list)


@dataclass
class Room:
    id: str
    capacity: int
    seats: list[Seat] = field(default_factory=list)
    version: int = 0
    match: Match | None = None
    # Seat zero is the creator in the current one-click create-and-seat flow.
    # Older API-created unseated rooms grant this role to their first joiner.
    host_seat: int = 0
    pending_joiners: list[int] = field(default_factory=list)
    room_notice: str = ""
    rematch_votes: set[int] = field(default_factory=set)
    reaction: dict[str, Any] | None = None
    reaction_seq: int = 0
    reaction_at: dict[int, float] = field(default_factory=dict)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def public_view(self) -> dict[str, Any]:
        active_count = len(self.match.state.players) if self.match else 0
        return {
            "type": "room_state",
            "room_id": self.id,
            "capacity": self.capacity,
            "host_seat": self.host_seat,
            "pending_joiners": list(self.pending_joiners),
            "active_player_count": active_count,
            "room_notice": self.room_notice,
            "phase": ("LOBBY" if self.match is None else public_match_view(self.match)["phase"]),
            "version": self.version,
            "game": public_match_view(self.match) if self.match is not None else None,
            "rematch_votes": sorted(self.rematch_votes),
            "reaction": self.reaction,
            "reaction_seq": self.reaction_seq,
            "all_ready": len(self.seats) == self.capacity
            and all(seat.ready for seat in self.seats),
            "players": [
                {
                    "seat": i,
                    "name": seat.name,
                    "ready": seat.ready,
                    "connected": seat.socket is not None,
                    "waiting_next_match": self.match is not None and i >= active_count,
                }
                for i, seat in enumerate(self.seats)
            ],
        }

    def view_for(self, index: int) -> dict[str, Any]:
        """Private owner snapshot; only the authenticated seat sees its hand."""
        out = self.public_view()
        out["you"] = index
        if self.match is not None:
            if index < len(self.match.state.players):
                out["game"] = private_match_view(self.match, index)
                out["game"]["is_spectator"] = False
            else:
                # A player who joined late has no hand in the ongoing match.
                # Never fabricate a private seat or reveal an opponent's cards.
                out["game"] = public_match_view(self.match)
                out["game"]["is_spectator"] = True
        return out


class RoomStore:
    def __init__(self, max_rooms: int = 100, db_path: str | Path | None = None):
        self.rooms: dict[str, Room] = {}
        self.lock = asyncio.Lock()
        self.max_rooms = max_rooms
        self.db: sqlite3.Connection | None = None
        self.db_lock = threading.RLock()
        if db_path is not None:
            path = Path(db_path).expanduser()
            path.parent.mkdir(parents=True, exist_ok=True)
            self.db = sqlite3.connect(str(path), check_same_thread=False)
            self.db.execute("CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, payload TEXT NOT NULL)")
            self.db.commit()
            for room_id, payload in self.db.execute("SELECT id, payload FROM rooms"):
                data = json.loads(payload)
                seats = [
                    Seat(
                        name=x["name"], token_digest=x["token_digest"],
                        ready=x["ready"], request_ids=list(x.get("request_ids", []))[-64:],
                    ) for x in data["seats"]
                ]
                # Rooms saved before codes replaced passwords keep their id and
                # seat digests; any stored password material is simply dropped.
                room = Room(
                    id=room_id, capacity=data["capacity"], seats=seats,
                    version=data["version"], match=restore_match(data["match"]),
                    host_seat=data.get("host_seat", 0),
                    pending_joiners=list(data.get("pending_joiners", [])),
                    room_notice=data.get("room_notice", ""),
                    rematch_votes=set(data.get("rematch_votes", [])),
                    reaction_seq=data.get("reaction_seq", 0),
                )
                self.rooms[room.id] = room

    def persist(self, room: Room) -> None:
        """Save an entire authoritative state while caller holds room.lock."""
        if self.db is None:
            return
        payload = {
            "capacity": room.capacity, "version": room.version,
            "host_seat": room.host_seat,
            "pending_joiners": list(room.pending_joiners),
            "room_notice": room.room_notice,
            "seats": [
                {
                    "name": s.name, "token_digest": s.token_digest,
                    "ready": s.ready, "request_ids": list(s.request_ids)[-64:],
                } for s in room.seats
            ],
            "match": dump_match(room.match),
            "rematch_votes": sorted(room.rematch_votes),
            "reaction_seq": room.reaction_seq,
        }
        with self.db_lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO rooms (id, payload) VALUES (?, ?)",
                (room.id, json.dumps(payload, separators=(",", ":"))),
            )

    def _allocate_code(self) -> str:
        """A free code, drawn with secrets and checked against live rooms."""
        for _ in range(100):
            code = "".join(secrets.choice(ROOM_CODE_ALPHABET)
                           for _ in range(ROOM_CODE_LENGTH))
            if code not in self.rooms and is_room_code(code):
                return code
        raise ValueError("could not allocate a free room code")

    async def create(self, capacity: int) -> Room:
        if not 2 <= capacity <= 6:
            raise ValueError("rooms require 2 to 6 players")
        async with self.lock:
            if len(self.rooms) >= self.max_rooms:
                raise ValueError("development room limit reached")
            room = Room(id=self._allocate_code(), capacity=capacity)
            self.rooms[room.id] = room
            self.persist(room)
            return room

    async def get(self, room_id: str) -> Room | None:
        """Look a room up by its code.

        New codes are uppercase, so a typed code is matched case-insensitively.
        Rooms saved under the earlier mixed-case ids stay reachable by their
        exact id, which keeps existing rooms and seat tokens usable.
        """
        raw = (room_id or "").strip()
        if not raw or len(raw) > MAX_ROOM_CODE_INPUT:
            return None
        async with self.lock:
            # Exact first, so a room saved under a mixed-case id can never be
            # shadowed by a newer code that matches it only once upper-cased.
            room = self.rooms.get(raw)
            if room is None:
                room = self.rooms.get(normalise_room_code(raw))
            return room


async def broadcast(room: Room, *, exclude: WebSocket | None = None) -> None:
    """Send a fresh public snapshot; never include bearer tokens."""
    async with room.lock:
        sockets = [(s.socket, room.view_for(i))
                   for i, s in enumerate(room.seats)
                   if s.socket is not None and s.socket is not exclude]
    for socket, view in sockets:
        try:
            await socket.send_json(view)
        except (RuntimeError, OSError):
            # A disconnection may race this broadcast. Its owning handler
            # is responsible for clearing the connection.
            pass


def remember_request(seat: Seat, request_id: str) -> None:
    """Bound duplicate-request memory during a live development session."""
    seat.request_ids.append(request_id)
    if len(seat.request_ids) > 64:
        del seat.request_ids[:-64]
