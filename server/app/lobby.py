"""Development-only multiplayer rooms with optional local SQLite recovery.

Public snapshots never contain seat tokens. A token grants control of exactly
one seat for the lifetime of this process; it is not a user account.
"""

from __future__ import annotations

import asyncio
import hashlib
import hmac
import json
import secrets
import sqlite3
import threading
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket
from server.app.gameplay import Match, private_match_view, public_match_view
from server.app.persistence import dump_match, restore_match


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
    password_salt: str = ""
    password_hash: str = ""
    version: int = 0
    match: Match | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def check_password(self, password: str) -> bool:
        """Existing legacy rooms are closed to new joins until recreated."""
        if not self.password_salt or not self.password_hash:
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                                        bytes.fromhex(self.password_salt), 210000)
        return hmac.compare_digest(candidate.hex(), self.password_hash)

    def public_view(self) -> dict[str, Any]:
        return {
            "type": "room_state",
            "room_id": self.id,
            "capacity": self.capacity,
            "phase": ("LOBBY" if self.match is None else public_match_view(self.match)["phase"]),
            "version": self.version,
            "game": public_match_view(self.match) if self.match is not None else None,
            "all_ready": len(self.seats) == self.capacity
            and all(seat.ready for seat in self.seats),
            "players": [
                {
                    "seat": i,
                    "name": seat.name,
                    "ready": seat.ready,
                    "connected": seat.socket is not None,
                }
                for i, seat in enumerate(self.seats)
            ],
        }

    def view_for(self, index: int) -> dict[str, Any]:
        """Private owner snapshot; only the authenticated seat sees its hand."""
        out = self.public_view()
        out["you"] = index
        if self.match is not None:
            out["game"] = private_match_view(self.match, index)
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
                room = Room(
                    id=room_id, capacity=data["capacity"], seats=seats,
                    version=data["version"], match=restore_match(data["match"]),
                    password_salt=data.get("password_salt", ""),
                    password_hash=data.get("password_hash", ""),
                )
                self.rooms[room.id] = room

    def persist(self, room: Room) -> None:
        """Save an entire authoritative state while caller holds room.lock."""
        if self.db is None:
            return
        payload = {
            "capacity": room.capacity, "version": room.version,
            "password_salt": room.password_salt, "password_hash": room.password_hash,
            "seats": [
                {
                    "name": s.name, "token_digest": s.token_digest,
                    "ready": s.ready, "request_ids": list(s.request_ids)[-64:],
                } for s in room.seats
            ],
            "match": dump_match(room.match),
        }
        with self.db_lock, self.db:
            self.db.execute(
                "INSERT OR REPLACE INTO rooms (id, payload) VALUES (?, ?)",
                (room.id, json.dumps(payload, separators=(",", ":"))),
            )

    async def create(self, capacity: int, password: str) -> Room:
        if not 2 <= capacity <= 6:
            raise ValueError("rooms require 2 to 6 players")
        async with self.lock:
            if len(self.rooms) >= self.max_rooms:
                raise ValueError("development room limit reached")
            room_id = secrets.token_urlsafe(9)
            while room_id in self.rooms:
                room_id = secrets.token_urlsafe(9)
            salt = secrets.token_bytes(16)
            digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 210000)
            room = Room(id=room_id, capacity=capacity,
                        password_salt=salt.hex(), password_hash=digest.hex())
            self.rooms[room_id] = room
            self.persist(room)
            return room

    async def get(self, room_id: str) -> Room | None:
        async with self.lock:
            return self.rooms.get(room_id)


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
