"""Development-only in-memory multiplayer lobby. No matchmaking or persistence.

Public snapshots never contain seat tokens. A token grants control of exactly
one seat for the lifetime of this process; it is not a user account.
"""

from __future__ import annotations

import asyncio
import secrets
from dataclasses import dataclass, field
from typing import Any

from fastapi import WebSocket


@dataclass
class Seat:
    name: str
    token: str
    ready: bool = False
    socket: WebSocket | None = None
    request_ids: list[str] = field(default_factory=list)


@dataclass
class Room:
    id: str
    capacity: int
    seats: list[Seat] = field(default_factory=list)
    version: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    def public_view(self) -> dict[str, Any]:
        return {
            "type": "room_state",
            "room_id": self.id,
            "capacity": self.capacity,
            "phase": "LOBBY",
            "version": self.version,
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


class RoomStore:
    def __init__(self, max_rooms: int = 100):
        self.rooms: dict[str, Room] = {}
        self.lock = asyncio.Lock()
        self.max_rooms = max_rooms

    async def create(self, capacity: int) -> Room:
        if not 2 <= capacity <= 6:
            raise ValueError("rooms require 2 to 6 players")
        async with self.lock:
            if len(self.rooms) >= self.max_rooms:
                raise ValueError("development room limit reached")
            room_id = secrets.token_urlsafe(9)
            while room_id in self.rooms:
                room_id = secrets.token_urlsafe(9)
            room = Room(id=room_id, capacity=capacity)
            self.rooms[room_id] = room
            return room

    async def get(self, room_id: str) -> Room | None:
        async with self.lock:
            return self.rooms.get(room_id)


async def broadcast(room: Room, *, exclude: WebSocket | None = None) -> None:
    """Send a fresh public snapshot; never include bearer tokens."""
    async with room.lock:
        view = room.public_view()
        sockets = [s.socket for s in room.seats
                   if s.socket is not None and s.socket is not exclude]
    for socket in sockets:
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
