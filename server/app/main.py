"""FastAPI W4 local multiplayer prototype: lobby and live in-memory matches."""

from __future__ import annotations

import asyncio
import base64
import binascii
import hmac
import json
import os
import secrets
import time
from pathlib import Path
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from server.app.lobby import (
    MAX_ROOM_CODE_INPUT, RateLimiter, RoomStore, Seat, broadcast, remember_request,
)
from server.app.persistence import token_digest
from server.app.gameplay import apply_match_action, make_match, UndecidedStartTie
from server.app.ludo import make_ludo_match, apply_ludo_action, IllegalLudoMove
from server.app.awale import make_awale_match, apply_awale_action, IllegalAwaleMove
from server.app.dara import make_dara_match, apply_dara_action, IllegalDaraMove
from server.app.yote import make_yote_match, apply_yote_action, IllegalYoteMove
from server.app.dominoes import make_domino_match, apply_domino_action, IllegalDominoMove
from server.app.game_catalog import game_spec, capacity_after_switch
from server.app.analytics import AnalyticsStore, traffic_source
from server.app.rules.ordinary import IllegalPlay
from server.app.rules.pile_pass import IllegalTransition


REACTIONS = {"😂", "😏", "😭", "👀", "🔥", "💀"}


class CreateRoom(BaseModel):
    capacity: int = Field(default=2, ge=2, le=6)
    game_type: str = "shithead"
    domino_mode: str = "partner"
    # The host names themselves while creating, so one press both opens the
    # room and seats them. Optional, so an older client still works.
    name: str | None = Field(default=None, max_length=32)


class JoinRoom(BaseModel):
    name: str = Field(min_length=1, max_length=32)


def _client_key(scope) -> str:
    """Group lookup attempts by origin address; good enough to stop a scan.

    Behind Railway the socket peer is the edge proxy, so without the forwarded
    address every player would share one bucket and one guesser could lock the
    room out for everyone. The header is spoofable, which costs little here:
    the limiter protects room codes, not an account or a payment.
    """
    forwarded = ""
    headers = getattr(scope, "headers", None)
    if headers is not None:
        forwarded = (headers.get("x-forwarded-for") or "").split(",")[0].strip()
    if forwarded:
        return forwarded[:64]
    client = getattr(scope, "client", None)
    return getattr(client, "host", None) or "unknown"


def create_app(
    *,
    db_path: str | Path | None = None,
    failed_lookup_limit: int | None = None,
    rate_window: float | None = None,
    analytics_path: str | Path | None = None,
) -> FastAPI:
    app = FastAPI(title="Shithead multiplayer preview", version="0.2-w4")
    cloud = bool(os.getenv("RAILWAY_ENVIRONMENT_ID"))
    store = RoomStore(db_path=db_path)
    app.state.room_store = store
    # Separate SQLite file; zero changes to the live rooms schema.
    analytics_location = (
        analytics_path if analytics_path is not None
        else Path(db_path).expanduser().with_name("analytics.sqlite3")
        if db_path is not None else None
    )
    analytics = AnalyticsStore(analytics_location)
    app.state.analytics_store = analytics
    admin_password = os.getenv("SHITHEAD_ADMIN_PASSWORD", "")

    # Rooms are open to anyone holding the code, so a wrong code is the only
    # thing worth throttling. Successful play never touches this limiter.
    limit = failed_lookup_limit if failed_lookup_limit is not None else int(
        os.getenv("SHITHEAD_FAILED_LOOKUP_LIMIT", "10"))
    window = rate_window if rate_window is not None else float(
        os.getenv("SHITHEAD_RATE_WINDOW_SECONDS", "60"))
    bad_codes = RateLimiter(limit=limit, window=window)
    app.state.bad_code_limiter = bad_codes

    async def resolve_room(room_id: str, key: str):
        """Shared code validation for every entry point: HTTP and WebSocket.

        Returns the room, or raises 429 once a client has burned through its
        allowance of wrong codes, otherwise 404.
        """
        room = None
        if room_id and len(room_id) <= MAX_ROOM_CODE_INPUT:
            room = await store.get(room_id)
        if room is None:
            if not bad_codes.allow(key):
                raise HTTPException(
                    status_code=429,
                    detail="too many invalid room codes; wait a minute and try again",
                )
            raise HTTPException(status_code=404, detail="room not found")
        return room

    def check_owner(request: Request) -> None:
        # No owner portal at all until a strong password is configured.
        if not admin_password:
            raise HTTPException(status_code=404, detail="not found")
        provided = request.headers.get("authorization", "")
        valid = False
        if provided.startswith("Basic "):
            try:
                raw = base64.b64decode(provided[6:], validate=True).decode("utf-8")
                user, sep, password = raw.partition(":")
                valid = bool(sep) and hmac.compare_digest(user, "owner") and hmac.compare_digest(password, admin_password)
            except (ValueError, UnicodeDecodeError, binascii.Error):
                pass
        if not valid:
            raise HTTPException(
                status_code=401, detail="Owner authentication required",
                headers={"WWW-Authenticate": 'Basic realm="SHITHEAD Games Owner"',
                         "Cache-Control": "no-store"},
            )

    ADMIN_HEADERS = {"Cache-Control": "no-store, private",
                     "X-Content-Type-Options": "nosniff",
                     "Referrer-Policy": "no-referrer",
                     "X-Frame-Options": "DENY"}

    @app.get("/owner/analytics", include_in_schema=False)
    async def owner_dashboard(request: Request):
        check_owner(request)
        return FileResponse(
            Path(__file__).parent / "static" / "owner.html",
            media_type="text/html",
            headers={**ADMIN_HEADERS, "Content-Security-Policy":
                     "default-src 'none'; script-src 'self'; style-src 'unsafe-inline'; connect-src 'self'; img-src 'none'; base-uri 'none'; frame-ancestors 'none'"},
        )

    @app.get("/owner/analytics.js", include_in_schema=False)
    async def owner_script(request: Request):
        check_owner(request)
        return FileResponse(
            Path(__file__).parent / "static" / "owner.js",
            media_type="application/javascript", headers=ADMIN_HEADERS,
        )

    @app.get("/owner/api/analytics", include_in_schema=False)
    async def owner_metrics(request: Request, days: int = 30):
        check_owner(request)
        try:
            report = analytics.report(days)
        except ValueError:
            raise HTTPException(status_code=422, detail="Choose 7, 30, 90, 365, or all") from None
        except RuntimeError:
            raise HTTPException(status_code=503, detail="Analytics database unavailable") from None
        rooms = list(store.rooms.values())
        report["live"] = {
            "active_rooms": sum(1 for room in rooms if any(s.socket is not None for s in room.seats)),
            "connected_seats": sum(s.socket is not None for room in rooms for s in room.seats),
            "rooms_in_memory": len(rooms),
        }
        return Response(
            content=json.dumps(report), media_type="application/json",
            headers=ADMIN_HEADERS,
        )

    @app.get("/owner/api/analytics.csv", include_in_schema=False)
    async def owner_export(request: Request, days: int = 30):
        check_owner(request)
        try:
            csv_data = analytics.export_csv(days)
        except ValueError:
            raise HTTPException(status_code=422, detail="Invalid period") from None
        except RuntimeError:
            raise HTTPException(status_code=503, detail="Analytics database unavailable") from None
        return Response(
            content=csv_data, media_type="text/csv; charset=utf-8",
            headers={**ADMIN_HEADERS, "Content-Disposition": 'attachment; filename="shithead-analytics.csv"'},
        )

    @app.get("/health", include_in_schema=False)
    async def health():
        return {"status": "ok"}

    @app.get("/")
    async def home(request: Request):
        analytics.record(
            "page_views",
            source=traffic_source(
                utm_source=request.query_params.get("utm_source"),
                referrer=request.headers.get("referer"),
            ),
        )
        return FileResponse(Path(__file__).parent / "static" / "index.html")

    @app.get("/client.js")
    async def client_script():
        return FileResponse(Path(__file__).parent / "static" / "client.js", media_type="application/javascript")

    @app.get("/dominoes.js")
    async def dominoes_script():
        return FileResponse(Path(__file__).parent / "static" / "dominoes.js", media_type="application/javascript")

    @app.get("/yote.js")
    async def yote_script():
        return FileResponse(Path(__file__).parent / "static" / "yote.js", media_type="application/javascript")

    @app.get("/dara.js")
    async def dara_script():
        return FileResponse(Path(__file__).parent / "static" / "dara.js", media_type="application/javascript")

    @app.get("/awale.js")
    async def awale_script():
        return FileResponse(Path(__file__).parent / "static" / "awale.js", media_type="application/javascript")

    @app.get("/ludo.js")
    async def ludo_script():
        return FileResponse(Path(__file__).parent / "static" / "ludo.js", media_type="application/javascript")

    # Owner-approved brand artwork. The unaltered original is kept in
    # design/references/; these are display copies only.
    BRAND = {
        "shithead-logo.png", "shithead-logo-180.png", "favicon.png",
    }

    @app.get("/brand/{name}", include_in_schema=False)
    async def brand_asset(name: str):
        if name not in BRAND:
            raise HTTPException(status_code=404, detail="unknown asset")
        return FileResponse(
            Path(__file__).parent / "static" / "brand" / name,
            media_type="image/png",
            headers={"Cache-Control": "public, max-age=86400"},
        )

    @app.get("/favicon.ico", include_in_schema=False)
    async def favicon():
        return FileResponse(
            Path(__file__).parent / "static" / "brand" / "favicon.png",
            media_type="image/png",
        )

    def clean_name(raw: str) -> str:
        name = raw.strip()
        if not name or any(ord(c) < 32 for c in name):
            raise HTTPException(status_code=422, detail="enter a valid player name")
        return name

    async def seat_player(room, name: str) -> dict:
        """Take the next free seat and issue that seat's private token."""
        async with room.lock:
            max_seats = game_spec(room.game_type).max_players
            if len(room.seats) >= (max_seats if (room.ludo is not None or room.match is not None or room.awale is not None or room.dara is not None or room.yote is not None or room.dominoes is not None) else room.capacity):
                raise HTTPException(status_code=409, detail="room is full")
            raw_token = secrets.token_urlsafe(24)
            index = len(room.seats)
            room.seats.append(Seat(name=name, token_digest=token_digest(raw_token)))
            if room.match is not None or room.ludo is not None or room.awale is not None or room.dara is not None or room.yote is not None or room.dominoes is not None:
                room.pending_joiners.append(index)
                room.capacity = max(room.capacity, len(room.seats))
            room.version += 1
            store.persist(room)
            analytics.record("players_joined", game=room.game_type,
                             mode=room.domino_mode if room.game_type == "dominoes" else "")
        await broadcast(room)
        return {"room_id": room.id, "seat": index, "token": raw_token,
                "waiting_next_match": room.match is not None or room.ludo is not None or room.awale is not None or room.dara is not None or room.yote is not None or room.dominoes is not None}

    @app.post("/api/rooms", status_code=201)
    async def create_room(payload: CreateRoom):
        name = clean_name(payload.name) if payload.name is not None else None
        if payload.game_type not in ("shithead", "ludo", "awale", "dara", "yote", "dominoes"):
            raise HTTPException(status_code=422, detail="unknown game")
        if payload.game_type in ("awale","dara","yote") and payload.capacity != 2:
            raise HTTPException(status_code=422, detail="Awalé requires two players")
        if payload.domino_mode not in ("partner", "cutthroat") or (payload.game_type != "dominoes" and payload.domino_mode != "partner"):
            raise HTTPException(status_code=422, detail="invalid dominoes mode")
        if payload.game_type == "dominoes" and payload.capacity != 4:
            raise HTTPException(status_code=422, detail="Jamaican partner dominoes requires four players")
        if payload.game_type == "ludo" and payload.capacity > 4:
            raise HTTPException(status_code=422, detail="Ludo supports up to four players")
        try:
            room = await store.create(payload.capacity)
            room.game_type = payload.game_type
            room.domino_mode = payload.domino_mode
            store.persist(room)
            analytics.record("rooms_created", game=room.game_type,
                             mode=room.domino_mode if room.game_type == "dominoes" else "")
        except ValueError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from None
        body = {"room_id": room.id, "capacity": room.capacity, "game_type": room.game_type,
                "domino_mode": room.domino_mode}
        if name is not None:
            body.update(await seat_player(room, name))
        return body

    @app.get("/api/rooms/{room_id}")
    async def room_snapshot(room_id: str, request: Request):
        room = await resolve_room(room_id, _client_key(request))
        async with room.lock:
            return room.public_view()

    @app.post("/api/rooms/{room_id}/join", status_code=201)
    async def join_room(room_id: str, payload: JoinRoom, request: Request):
        room = await resolve_room(room_id, _client_key(request))
        return await seat_player(room, clean_name(payload.name))

    @app.websocket("/ws/{room_id}")
    async def room_socket(websocket: WebSocket, room_id: str):
        # Same-origin browser access only; seat ownership still requires a token.
        origin = websocket.headers.get("origin")
        if ((cloud and not origin) or
                (origin and urlsplit(origin).netloc != websocket.headers.get("host"))):
            await websocket.close(code=1008)
            return
        try:
            room = await resolve_room(room_id, _client_key(websocket))
        except HTTPException:
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
                if kind not in ("ready", "game", "ludo", "awale", "dara", "yote", "dominoes", "rematch", "reaction", "host_join_decision", "select_game", "set_capacity", "set_domino_mode", "return_lobby"):
                    await websocket.send_json({"type": "error", "reasonCode": "unknown_action"})
                    continue

                request_id = action.get("request_id")
                expected = action.get("expected_version")
                ready = action.get("ready")
                if (not isinstance(request_id, str) or not 1 <= len(request_id) <= 64
                        or type(expected) is not int
                        or (kind == "ready" and type(ready) is not bool)
                        or (kind in ("game", "ludo", "awale", "dara", "yote", "dominoes") and not isinstance(action.get("kind"), str))
                        or (kind == "select_game" and action.get("game_type") not in ("ludo", "shithead", "awale", "dara", "yote", "dominoes"))
                        or (kind == "set_domino_mode" and action.get("domino_mode") not in ("partner", "cutthroat"))
                        or (kind == "host_join_decision" and action.get("decision") not in
                            ("restart_now", "finish_current"))
                        or (kind == "reaction" and (not isinstance(action.get("emoji"), str)
                            or action["emoji"] not in REACTIONS))):
                    await websocket.send_json({"type": "error", "reasonCode": "invalid_action"})
                    continue

                changed = False
                started_a_match = False
                error = None
                reason = None
                async with room.lock:
                    old_phase = room.public_view()["phase"]
                    seat = room.seats[index]
                    if seat.socket is not websocket:
                        error = "seat_reconnected"
                    elif request_id in seat.request_ids:
                        pass
                    elif expected != room.version:
                        error = "stale_version"
                    elif kind == "reaction":
                        # Cosmetic only: does not mutate Match, card locations,
                        # pending decisions, or any turn state.
                        now = time.monotonic()
                        if room.match is None and room.ludo is None and room.awale is None and room.dara is None and room.yote is None and room.dominoes is None:
                            error = "wrong_phase"
                        elif now - room.reaction_at.get(index, -9999) < 2.0:
                            error = "reaction_cooldown"
                        else:
                            room.reaction_at[index] = now
                            room.reaction_seq += 1
                            room.reaction = {
                                "seat": index, "emoji": action["emoji"],
                                "seq": room.reaction_seq,
                            }
                            remember_request(seat, request_id)
                            # Reactions are cosmetic. Never invalidate a card
                            # selection or an in-flight move's expected_version.
                            changed = True
                    elif kind == "return_lobby":
                        if index != room.host_seat:
                            error = "host_only"
                        elif room.public_view()["phase"] != "FINISHED":
                            error = "wrong_phase"
                        else:
                            room.match = None
                            room.ludo = None
                            room.awale = None
                            room.dara = None
                            room.yote = None
                            room.dominoes = None
                            room.pending_joiners.clear()
                            room.rematch_votes.clear()
                            for player in room.seats:
                                player.ready = False
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                    elif kind == "select_game":
                        if index != room.host_seat:
                            error = "host_only"
                        elif room.match is not None or room.ludo is not None or room.awale is not None or room.dara is not None or room.yote is not None or room.dominoes is not None:
                            error = "wrong_phase"
                        elif action["game_type"] in ("awale", "dara", "yote") and len(room.seats) > 2:
                            error = "too_many_players"
                        elif action["game_type"] == "dominoes" and len(room.seats) > 4:
                            error = "too_many_players"
                        elif action["game_type"] == "ludo" and len(room.seats) > 4:
                            error = "too_many_players"
                        else:
                            room.game_type = action["game_type"]
                            room.capacity = capacity_after_switch(room.game_type, room.capacity, len(room.seats))
                            for player in room.seats:
                                player.ready = False
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                    elif kind == "set_domino_mode":
                        if index != room.host_seat:
                            error = "host_only"
                        elif room.game_type != "dominoes" or room.dominoes is not None:
                            error = "wrong_phase"
                        elif room.domino_mode != action["domino_mode"]:
                            room.domino_mode = action["domino_mode"]
                            for player in room.seats:
                                player.ready = False
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                        else:
                            remember_request(seat, request_id)
                    elif kind == "set_capacity":
                        new_capacity = action.get("capacity")
                        if index != room.host_seat:
                            error = "host_only"
                        elif room.match is not None or room.ludo is not None or room.awale is not None or room.dara is not None or room.yote is not None or room.dominoes is not None:
                            error = "wrong_phase"
                        elif (type(new_capacity) is not int
                              or not len(room.seats) <= new_capacity <= game_spec(room.game_type).max_players
                              or new_capacity < game_spec(room.game_type).min_players):
                            error = "invalid_capacity"
                        else:
                            room.capacity = new_capacity
                            for player in room.seats:
                                player.ready = False
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                    elif kind == "host_join_decision":
                        if index != room.host_seat:
                            error = "host_only"
                        elif not room.pending_joiners or (room.match is None and room.ludo is None and room.awale is None and room.dara is None and room.yote is None and room.dominoes is None):
                            error = "no_pending_joiners"
                        elif action["decision"] == "finish_current":
                            room.pending_joiners.clear()
                            room.room_notice = "New players will join the next round."
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                        else:
                            try:
                                fresh = make_domino_match(mode=room.domino_mode) if room.game_type == "dominoes" else make_yote_match() if room.game_type == "yote" else make_dara_match() if room.game_type == "dara" else make_awale_match() if room.game_type == "awale" else make_ludo_match(len(room.seats)) if room.game_type == "ludo" else make_match(len(room.seats))
                            except UndecidedStartTie:
                                error = "starting_tie_unresolved"
                            else:
                                if room.game_type == "dominoes":
                                    room.dominoes = fresh
                                elif room.game_type == "yote":
                                    room.yote = fresh
                                elif room.game_type == "dara":
                                    room.dara = fresh
                                elif room.game_type == "awale":
                                    room.awale = fresh
                                elif room.game_type == "ludo":
                                    room.ludo = fresh
                                else:
                                    room.match = fresh
                                room.pending_joiners.clear()
                                room.rematch_votes.clear()
                                room.room_notice = "The host restarted the match for everyone."
                                started_a_match = True
                                room.reaction = None
                                room.reaction_at.clear()
                                room.version += 1
                                remember_request(seat, request_id)
                                changed = True
                    elif kind == "rematch":
                        if (room.match is None and room.ludo is None and room.awale is None and room.dara is None and room.yote is None and room.dominoes is None) or room.public_view()["phase"] != "FINISHED":
                            error = "wrong_phase"
                        else:
                            remember_request(seat, request_id)
                            if index not in room.rematch_votes:
                                room.rematch_votes.add(index)
                                room.version += 1
                                changed = True
                            if len(room.rematch_votes) == len(room.seats) and len(room.seats) >= 2:
                                try:
                                    fresh = make_domino_match(mode=room.domino_mode) if room.game_type == "dominoes" else make_yote_match() if room.game_type == "yote" else make_dara_match() if room.game_type == "dara" else make_awale_match() if room.game_type == "awale" else make_ludo_match(len(room.seats)) if room.game_type == "ludo" else make_match(len(room.seats))
                                except UndecidedStartTie:
                                    # Leave the match finished and permit a new
                                    # unanimous retry without a deadlocked vote.
                                    room.rematch_votes.clear()
                                    room.version += 1
                                    changed = True
                                    error = "starting_tie_unresolved"
                                else:
                                    if room.game_type == "dominoes":
                                        room.dominoes = fresh
                                    elif room.game_type == "yote":
                                        room.yote = fresh
                                    elif room.game_type == "dara":
                                        room.dara = fresh
                                    elif room.game_type == "awale":
                                        room.awale = fresh
                                    elif room.game_type == "ludo":
                                        room.ludo = fresh
                                    else:
                                        room.match = fresh
                                    room.pending_joiners.clear()
                                    room.room_notice = ""
                                    started_a_match = True
                                    room.rematch_votes.clear()
                                    room.reaction = None
                                    room.reaction_at.clear()
                                    room.version += 1
                                    changed = True
                    elif kind == "ready":
                        if room.match is not None or room.ludo is not None or room.awale is not None or room.dara is not None or room.yote is not None or room.dominoes is not None:
                            error = "wrong_phase"
                        else:
                            remember_request(seat, request_id)
                            if seat.ready != ready:
                                seat.ready = ready
                                room.version += 1
                                changed = True
                            if (len(room.seats) == room.capacity
                                    and all(s.ready for s in room.seats)):
                                try:
                                    candidate = make_domino_match(mode=room.domino_mode) if room.game_type == "dominoes" else make_yote_match() if room.game_type == "yote" else make_dara_match() if room.game_type == "dara" else make_awale_match() if room.game_type == "awale" else make_ludo_match(room.capacity) if room.game_type == "ludo" else make_match(room.capacity)
                                except UndecidedStartTie:
                                    # No owner-approved fallback for an exact
                                    # D-019 three-card tie: keep lobby recoverable.
                                    seat.ready = False
                                    room.version += 1
                                    error = "starting_tie_unresolved"
                                else:
                                    if room.game_type == "dominoes":
                                        room.dominoes = candidate
                                    elif room.game_type == "yote":
                                        room.yote = candidate
                                    elif room.game_type == "dara":
                                        room.dara = candidate
                                    elif room.game_type == "awale":
                                        room.awale = candidate
                                    elif room.game_type == "ludo":
                                        room.ludo = candidate
                                    else:
                                        room.match = candidate
                                    room.rematch_votes.clear()
                                    started_a_match = True
                                    room.version += 1
                                    changed = True
                    elif room.game_type == "dominoes":
                        if kind != "dominoes":
                            error = "wrong_game"
                        elif room.dominoes is None:
                            error = "wrong_phase"
                        elif index >= 4:
                            error = "waiting_next_match"
                        else:
                            try:
                                next_match = apply_domino_action(room.dominoes, index, action["kind"], index=action.get("index"), side=action.get("side"))
                            except IllegalDominoMove as exc:
                                error = "illegal_action"
                                reason = str(exc)
                            else:
                                room.dominoes = next_match
                                room.version += 1
                                remember_request(seat, request_id)
                                changed = True
                    elif room.game_type == "yote":
                        if kind != "yote":
                            error = "wrong_game"
                        elif room.yote is None:
                            error = "wrong_phase"
                        elif index >= 2:
                            error = "waiting_next_match"
                        else:
                            try:
                                next_match = apply_yote_action(room.yote,index,action["kind"],index=action.get("index"),source=action.get("source"),destination=action.get("destination"))
                            except IllegalYoteMove as exc:
                                error="illegal_action"
                                reason=str(exc)
                            else:
                                room.yote=next_match
                                room.version+=1
                                remember_request(seat,request_id)
                                changed=True
                    elif room.game_type == "dara":
                        if kind != "dara":
                            error = "wrong_game"
                        elif room.dara is None and room.yote is None:
                            error = "wrong_phase"
                        elif index >= 2:
                            error = "waiting_next_match"
                        else:
                            try:
                                next_match = apply_dara_action(room.dara, index, action["kind"], index=action.get("index"), source=action.get("source"), destination=action.get("destination"))
                            except IllegalDaraMove as exc:
                                error = "illegal_action"
                                reason = str(exc)
                            else:
                                room.dara = next_match
                                room.version += 1
                                remember_request(seat, request_id)
                                changed = True
                    elif room.game_type == "awale":
                        if kind != "awale":
                            error = "wrong_game"
                        elif room.awale is None:
                            error = "wrong_phase"
                        elif index >= 2:
                            error = "waiting_next_match"
                        else:
                            try:
                                next_match = apply_awale_action(room.awale, index, action["kind"], pit=action.get("pit"))
                            except IllegalAwaleMove as exc:
                                error = "illegal_action"
                                reason = str(exc)
                            else:
                                room.awale = next_match
                                room.version += 1
                                remember_request(seat, request_id)
                                changed = True
                    elif room.game_type == "ludo":
                        if kind != "ludo":
                            error = "wrong_game"
                        elif room.ludo is None:
                            error = "wrong_phase"
                        elif index >= len(room.ludo.players):
                            error = "waiting_next_match"
                        else:
                            try:
                                next_match = apply_ludo_action(
                                    room.ludo, index, action["kind"], token=action.get("token"))
                            except IllegalLudoMove as exc:
                                error = "illegal_action"
                                reason = str(exc)
                            else:
                                room.ludo = next_match
                                room.version += 1
                                remember_request(seat, request_id)
                                changed = True
                    elif kind != "game":
                        error = "wrong_game"
                    elif room.match is None:
                        error = "wrong_phase"
                    elif index >= len(room.match.state.players):
                        error = "waiting_next_match"
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
                            # The rule text says what the player must do instead
                            # ("choose a valid target seat"). Collapsing it into
                            # a generic string is what made a refused 3/Joker
                            # look like a frozen game.
                            reason = str(exc)
                        else:
                            room.match = next_match
                            room.version += 1
                            remember_request(seat, request_id)
                            changed = True
                    if changed:
                        game_mode = room.domino_mode if room.game_type == "dominoes" else ""
                        if started_a_match:
                            analytics.record("matches_started", game=room.game_type, mode=game_mode)
                        if (kind in ("game", "ludo", "awale", "dara", "yote", "dominoes")
                            and old_phase != "FINISHED"
                            and room.public_view()["phase"] == "FINISHED"):
                            analytics.record("matches_completed", game=room.game_type, mode=game_mode)
                    view = room.view_for(index)
                    if changed or (error is None and request_id in seat.request_ids):
                        store.persist(room)
                if error:
                    await websocket.send_json({
                        "type": "error", "reasonCode": error,
                        "message": (f"{reason[0].upper()}{reason[1:]}." if reason else
                                    "Action rejected; view refreshed. Please choose an available action."),
                        "allowedActions": (["accept", "counter"] if room.match is not None and room.match.pending is not None else ["play", "power", "pickup", "flip"] if room.match is not None else ["ready"]),
                        "stateSnapshot": view,
                    })
                    if changed:
                        await broadcast(room, exclude=websocket)
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


def default_db_path() -> Path:
    """Use Railway's persistent volume, never the ephemeral deployment disk."""
    volume = os.getenv("RAILWAY_VOLUME_MOUNT_PATH")
    if os.getenv("RAILWAY_ENVIRONMENT_ID"):
        if not volume:
            raise RuntimeError(
                "Attach a persistent Railway volume at /data before deploying."
            )
        return Path(volume) / "rooms.sqlite3"
    custom = os.getenv("SHITHEAD_DB_PATH")
    return Path(custom) if custom else Path.home() / ".shithead" / "local_rooms.sqlite3"


# The local launcher and Railway each use one process / one SQLite writer.
# Individual unit-test create_app() instances use their own isolated storage.
app = create_app(db_path=default_db_path())
