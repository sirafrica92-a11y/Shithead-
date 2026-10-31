"""Isolated solo Ludo sessions. No multiplayer room, player token, or /data changes."""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import hmac
import secrets
import time

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path

from server.app.ludo import (
    IllegalLudoMove, LudoMatch, apply_ludo_action, legal_tokens,
    make_ludo_match, private_ludo_view, HOME,
)

router = APIRouter()
MAX_SESSIONS = 80
SESSION_TTL = 60 * 60 * 2
BOT_STEP_LIMIT = 80


@dataclass
class Session:
    token: str
    match: LudoMatch
    version: int = 0
    last_active: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


_sessions: dict[str, Session] = {}
_registry_lock = asyncio.Lock()


class SoloAction(BaseModel):
    token: str
    version: int
    action: str
    piece: int | None = None


class ResetAction(BaseModel):
    token: str
    version: int


def _snapshot(session: Session) -> dict:
    state = private_ludo_view(session.match, 0)
    return {
        "version": session.version,
        "game": state,
        "players": ["You", "Computer"],
        "solo": True,
    }


def _best_piece(m: LudoMatch) -> int:
    assert m.stage == "MOVE" and m.die is not None
    choices = legal_tokens(m, 1, m.die)
    # Only legal actions; the computer does not inspect private opponent data.
    ranked = []
    for piece in choices:
        previous = m.players[1].tokens[piece]
        after = apply_ludo_action(m, 1, "move", token=piece)
        destination = after.players[1].tokens[piece]
        capture = sum(x == -1 for x in after.players[0].tokens) - sum(
            x == -1 for x in m.players[0].tokens)
        score = (
            200 if destination == HOME else 0
        ) + 80 * capture + (45 if previous == -1 else 0) + (
            16 if destination >= 51 else 0
        ) + max(0, destination - max(previous, 0)) + destination / 100
        # Stable tie break creates predictable normal-difficulty decisions.
        ranked.append((score, -piece, piece))
    return max(ranked)[2]


def _bot_play(session: Session) -> None:
    # Bounded loop: sixes and captures can award repeated bonus turns.
    for _ in range(BOT_STEP_LIMIT):
        m = session.match
        if m.winner is not None or m.actor != 1:
            return
        if m.stage == "ROLL":
            session.match = apply_ludo_action(m, 1, "roll")
        else:
            session.match = apply_ludo_action(m, 1, "move", token=_best_piece(m))
        session.version += 1


async def _find(key: str, token: str) -> Session:
    if not isinstance(token, str) or len(token) != 43:
        raise HTTPException(404, "Solo session unavailable")
    session = _sessions.get(key)
    if (session is None or not hmac.compare_digest(session.token, token)
            or time.monotonic() - session.last_active > SESSION_TTL):
        raise HTTPException(404, "Solo session unavailable")
    return session


@router.get("/solo/ludo", include_in_schema=False)
async def solo_ludo_page():
    return FileResponse(Path(__file__).parent / "static" / "solo-ludo.html",
                        headers={"Cache-Control": "no-store"})


@router.get("/solo/ludo.js", include_in_schema=False)
async def solo_ludo_script():
    return FileResponse(Path(__file__).parent / "static" / "solo-ludo.js",
                        media_type="application/javascript")


@router.post("/api/solo/ludo", status_code=201)
async def create_solo_ludo():
    async with _registry_lock:
        now = time.monotonic()
        for key, session in list(_sessions.items()):
            if now - session.last_active > SESSION_TTL:
                del _sessions[key]
        if len(_sessions) >= MAX_SESSIONS:
            raise HTTPException(503, "Solo Play is busy; try again shortly")
        key = secrets.token_urlsafe(18)
        session = Session(token=secrets.token_urlsafe(32), match=make_ludo_match(2))
        _sessions[key] = session
    async with session.lock:
        _bot_play(session)
        session.last_active = time.monotonic()
        return {"id": key, "token": session.token, **_snapshot(session)}


@router.get("/api/solo/ludo/{key}")
async def resume_solo_ludo(key: str, x_solo_token: str | None = Header(default=None)):
    session = await _find(key, x_solo_token or "")
    async with session.lock:
        _bot_play(session)
        session.last_active = time.monotonic()
        return _snapshot(session)


@router.post("/api/solo/ludo/{key}/reset")
async def reset_solo_ludo(key: str, payload: ResetAction):
    """Reuse a session for New Game / Play Again without filling the solo limit."""
    session = await _find(key, payload.token)
    async with session.lock:
        if payload.version != session.version:
            raise HTTPException(409, "Board changed; refresh the match")
        session.match = make_ludo_match(2)
        session.version += 1
        _bot_play(session)
        session.last_active = time.monotonic()
        return _snapshot(session)


@router.post("/api/solo/ludo/{key}")
async def solo_ludo_move(key: str, payload: SoloAction):
    session = await _find(key, payload.token)
    async with session.lock:
        if payload.version != session.version:
            raise HTTPException(409, "Board changed; refresh the match")
        if session.match.winner is not None:
            raise HTTPException(409, "Match finished; choose Play Again")
        if session.match.actor != 0:
            raise HTTPException(409, "Computer is taking its turn")
        if payload.action not in ("roll", "move"):
            raise HTTPException(422, "Unknown move")
        try:
            session.match = apply_ludo_action(
                session.match, 0, payload.action, token=payload.piece
            )
        except IllegalLudoMove as exc:
            raise HTTPException(422, str(exc)) from None
        session.version += 1
        _bot_play(session)
        session.last_active = time.monotonic()
        return _snapshot(session)
