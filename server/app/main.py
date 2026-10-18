"""FastAPI W4 local multiplayer prototype: lobby and live in-memory matches."""

from __future__ import annotations

import asyncio
import hmac
import secrets
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from server.app.lobby import RoomStore, Seat, broadcast, remember_request
from server.app.persistence import token_digest
from server.app.gameplay import apply_match_action, make_match
from server.app.rules.ordinary import IllegalPlay
from server.app.rules.pile_pass import IllegalTransition


class CreateRoom(BaseModel):
    capacity: int = Field(default=2, ge=2, le=6)


class JoinRoom(BaseModel):
    name: str = Field(min_length=1, max_length=32)


def create_app(*, db_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(title="Shithead local multiplayer lobby", version="0.1-w4")
    store = RoomStore(db_path=db_path)
    app.state.room_store = store

    async def get_room(room_id: str):
        room = await store.get(room_id)
        if room is None:
            raise HTTPException(status_code=404, detail="room not found")
        return room

    @app.get("/")
    async def home():
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.get("/client.js")
    async def client_script():
        return FileResponse(Path(__file__).parent / "static" / "client.js", media_type="application/javascript")

    @app.post("/api/rooms", status_code=201)
    async def create_room(payload: CreateRoom):
        try:
            room = await store.create(payload.capacity)
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        return {"room_id": room.id, "capacity": room.capacity}

    @app.get("/api/rooms/{room_id}")
    async def room_snapshot(room_id: str):
        room = await get_room(room_id)
        async with room.lock:
            return room.public_view()

    @app.post("/api/rooms/{room_id}/join", status_code=201)
    async def join_room(room_id: str, payload: JoinRoom):
        room = await get_room(room_id)
        name = payload.name.strip()
        if not name or any(ord(c) < 32 for c in name):
            raise HTTPException(status_code=422, detail="enter a valid player name")
        async with room.lock:
            if len(room.seats) == room.capacity:
                raise HTTPException(status_code=409, detail="room is full")
            raw_token = secrets.token_urlsafe(24)
            seat = Seat(name=name, token_digest=token_digest(raw_token))
            room.seats.append(seat)
            room.version += 1
            index = len(room.seats) - 1
            store.persist(room)
        await broadcast(room)
        return {"room_id": room.id, "seat": index, "token": raw_token}

    @app.websocket("/ws/{room_id}")
    async def room_socket(websocket: WebSocket, room_id: str):
        # Same-origin browser access only; seat ownership still requires a token.
        origin = websocket.headers.get("origin")
        if origin and urlsplit(origin).netloc != websocket.headers.get("host"):
            await websocket.close(code=1008)
            return
        room = await store.get(room_id)
        if room is None:
            await websocket.close(code=1008)
            return
        await websocket.accept()
        try:
            auth = await asyncio.wait_for(websocket.receive_json(), timeout=10)
        except (WebSocketDisconnect, ValueError, asyncio.TimeoutError):
            await websocket.close(code=1008)
            return
        if (not isinstance(auth, dict) or auth.get("type") != "auth"
                or not isinstance(auth.get("token"), str)
                or not 1 <= len(auth["token"]) <= 128):
            await websocket.close(code=1008)
            return

        old_socket = None
        index = None
        async with room.lock:
            for i, seat in enumerate(room.seats):
                if hmac.compare_digest(seat.token_digest, token_digest(auth["token"])):
                    index = i
                    old_socket = seat.socket
                    seat.socket = websocket
                    room.version += 1
                    view = room.view_for(i)
                    store.persist(room)
                    break
        if index is None:
            await websocket.close(code=1008)
            return
        if old_socket is not None and old_socket is not websocket:
            try:
                await old_socket.close(code=4000)
            except (RuntimeError, OSError):
                pass
        await websocket.send_json({**view, "you": index})
        await broadcast(room, exclude=websocket)

        try:
            while True:
                try:
                    action = await websocket.receive_json()
                except ValueError:
                    await websocket.send_json({"type": "error", "reasonCode": "invalid_json"})
                    continue
                if not isinstance(action, dict):
                    await websocket.send_json({"type": "error", "reasonCode": "invalid_action"})
                    continue

                if action.get("type") == "sync":
                    async with room.lock:
                        view = room.view_for(index)
                    await websocket.send_json({**view, "you": index})
                    continue

                kind = action.get("type")
                if kind not in ("ready", "game"):
                    await websocket.send_json({"type": "error", "reasonCode": "unknown_action"})
                    continue

                request_id = action.get("request_id")
                expected = action.get("expected_version")
                ready = action.get("ready")
                if (not isinstance(request_id, str) or not 1 <= len(request_id) <= 64
                        or type(expected) is not int
                        or (kind == "ready" and type(ready) is not bool)
                        or (kind == "game" and not isinstance(action.get("kind"), str))):
                    await websocket.send_json({"type": "error", "reasonCode": "invalid_action"})
                    continue

                changed = False
                error = None
                async with room.lock:
                    seat = room.seats[index]
                    if seat.socket is not websocket:
                        error = "seat_reconnected"
                    elif request_id in seat.request_ids:
                        pass
                    elif expected != room.version:
                        error = "stale_version"
                    elif kind == "ready":
                        if room.match is not None:
                            error = "wrong_phase"
                        else:
                            remember_request(seat, request_id)
                            if seat.ready != ready:
                                seat.ready = ready
                                room.version += 1
                                changed = True
                            if (len(room.seats) == room.capacity
                                    and all(s.ready for s in room.seats)):
                                room.match = make_match(room.capacity)
                                room.version += 1
                                changed = True
                    elif room.match is None:
                        error = "wrong_phase"
                    else:
                        try:
                            next_match = apply_match_action(
                                room.match, index, action["kind"],
                                indices=action.get("indices"),
                                index=action.get("index"),
                                target=action.get("target"),
                            )
                        except (IllegalPlay, IllegalTransition, ValueError) as exc:
                            error = "illegal_action"
                        else:
                            room.match = next_match
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                    view = room.view_for(index)
                    if changed or (error is None and request_id in seat.request_ids):
                        store.persist(room)
                if error:
                    await websocket.send_json({
                        "type": "error", "reasonCode": error,
                        "message": "Action rejected; view refreshed. Please choose an available action.",
                        "allowedActions": (["accept", "counter"] if room.match is not None and room.match.pending is not None else ["play", "power", "pickup", "flip"] if room.match is not None else ["ready"]),
                        "stateSnapshot": view,
                    })
                elif changed:
                    await broadcast(room)
                else:
                    await websocket.send_json(view)
        except WebSocketDisconnect:
            pass
        finally:
            async with room.lock:
                seat = room.seats[index]
                if seat.socket is websocket:
                    seat.socket = None
                    room.version += 1
                    store.persist(room)
                    notify = True
                else:
                    notify = False
            if notify:
                await broadcast(room)

    return app


# Persistent only in the CLI server; unit-test create_app() instances stay isolated.
app = create_app(db_path=Path.home() / ".shithead" / "local_rooms.sqlite3")
