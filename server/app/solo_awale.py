"""Independent Solo Play Awalé sessions, reusing the approved Abapa rules engine.

Solo games have no multiplayer room code, WebSocket seat, or SQLite writes.
Sessions are deliberately ephemeral; a Railway restart ends them.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
import hmac
from pathlib import Path
import secrets
import time

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, StrictInt

from server.app.awale import (
    AwaleMatch, IllegalAwaleMove, apply_awale_action, legal_awale_pits,
    make_awale_match, private_awale_view,
)

router = APIRouter()
MAX_SESSIONS = 80
SESSION_TTL = 2 * 60 * 60


@dataclass
class SoloAwaleSession:
    token: str
    match: AwaleMatch
    version: int = 0
    action_trace: list[dict] = field(default_factory=list)
    last_active: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


_sessions: dict[str, SoloAwaleSession] = {}
_registry_lock = asyncio.Lock()


class SoloAwaleMove(BaseModel):
    token: str = Field(min_length=43, max_length=43)
    version: StrictInt = Field(ge=0)
    pit: StrictInt = Field(ge=0, le=11)


class SoloAwaleReset(BaseModel):
    token: str = Field(min_length=43, max_length=43)
    version: StrictInt = Field(ge=0)


def _snapshot(session: SoloAwaleSession) -> dict:
    return {
        "version": session.version,
        "game": private_awale_view(session.match, 0),
        "players": ["You", "Computer"],
        "solo": True,
        "computer_actions": list(session.action_trace),
    }


def _position_value(match: AwaleMatch) -> float:
    """Evaluation from the computer's side; never alters authoritative state."""
    if match.finished:
        if match.winner == 1:
            return 10000.0
        if match.winner == 0:
            return -10000.0
        return 0.0
    lead = match.captured[1] - match.captured[0]
    # Remaining seeds and feeding opportunities are public in Awalé.
    seed_balance = sum(match.pits[6:]) - sum(match.pits[:6])
    return 35.0 * lead + 0.35 * seed_balance


def _best_bot_pit(match: AwaleMatch) -> int:
    """Normal difficulty: legal capture/feeding-aware move with one-ply defence."""
    choices = legal_awale_pits(match, 1)
    if not choices:
        raise RuntimeError("The computer cannot play an unfinished Awalé position")
    candidates: list[tuple[float, int, int]] = []
    for pit in choices:
        after = apply_awale_action(match, 1, "sow", pit=pit)
        current = _position_value(after)
        if after.finished:
            outcome = current
        else:
            # Opponent is free to choose their strongest reply; do not assume
            # a cooperative human or inspect information outside the board.
            replies = legal_awale_pits(after, 0)
            worst_reply = min(
                _position_value(apply_awale_action(after, 0, "sow", pit=reply))
                for reply in replies
            ) if replies else current
            outcome = 0.3 * current + 0.7 * worst_reply
        capture_gain = after.captured[1] - match.captured[1]
        candidates.append((outcome, capture_gain, -pit))
    return -max(candidates)[2]


def _computer_reply(session: SoloAwaleSession) -> None:
    session.action_trace = []
    match = session.match
    if not match.finished and match.actor == 1:
        move = _best_bot_pit(match)
        session.match = apply_awale_action(match, 1, "sow", pit=move)
        session.version += 1
        captured = session.match.captured[1] - match.captured[1]
        session.action_trace.append({
            "message": f"Computer chose house {move + 1}, sowed {match.pits[move]} seeds"
                       + (f" and captured {captured} seeds." if captured else "."),
            "game": private_awale_view(session.match, 0),
        })


async def _require_session(key: str, token: str) -> SoloAwaleSession:
    if not isinstance(token, str) or len(token) != 43:
        raise HTTPException(404, "Solo Play session unavailable")
    session = _sessions.get(key)
    if (session is None or not hmac.compare_digest(session.token, token)
            or time.monotonic() - session.last_active >= SESSION_TTL):
        raise HTTPException(404, "Solo Play session unavailable")
    return session


def _no_store(body: dict, status_code: int = 200) -> JSONResponse:
    return JSONResponse(content=body, status_code=status_code,
                        headers={"Cache-Control": "no-store"})


@router.get("/solo/awale", include_in_schema=False)
async def solo_awale_page():
    return FileResponse(Path(__file__).parent / "static" / "solo-awale.html",
                        headers={"Cache-Control": "no-store"})


@router.get("/solo/awale.js", include_in_schema=False)
async def solo_awale_script():
    return FileResponse(Path(__file__).parent / "static" / "solo-awale.js",
                        media_type="application/javascript")


@router.post("/api/solo/awale", status_code=201)
async def create_solo_awale():
    async with _registry_lock:
        now = time.monotonic()
        for key, session in list(_sessions.items()):
            if now - session.last_active >= SESSION_TTL:
                del _sessions[key]
        if len(_sessions) >= MAX_SESSIONS:
            raise HTTPException(503, "Solo Play is busy; try again shortly")
        key = secrets.token_urlsafe(18)
        session = SoloAwaleSession(
            token=secrets.token_urlsafe(32), match=make_awale_match()
        )
        _sessions[key] = session
    async with session.lock:
        _computer_reply(session)
        session.last_active = time.monotonic()
        return _no_store({
            "id": key,
            "token": session.token,
            **_snapshot(session),
        }, status_code=201)


@router.get("/api/solo/awale/{key}")
async def resume_solo_awale(
    key: str, x_solo_token: str | None = Header(default=None)
):
    session = await _require_session(key, x_solo_token or "")
    async with session.lock:
        _computer_reply(session)
        session.last_active = time.monotonic()
        state = _snapshot(session)
        state["computer_actions"] = []
        return _no_store(state)


@router.post("/api/solo/awale/{key}/reset")
async def reset_solo_awale(key: str, payload: SoloAwaleReset):
    session = await _require_session(key, payload.token)
    async with session.lock:
        if payload.version != session.version:
            raise HTTPException(409, "Board changed; refresh the match")
        session.match = make_awale_match()
        session.version += 1
        _computer_reply(session)
        session.last_active = time.monotonic()
        return _no_store(_snapshot(session))


@router.post("/api/solo/awale/{key}")
async def play_solo_awale(key: str, payload: SoloAwaleMove):
    session = await _require_session(key, payload.token)
    async with session.lock:
        if payload.version != session.version:
            raise HTTPException(409, "Board changed; refresh the match")
        if session.match.finished:
            raise HTTPException(409, "Match finished; choose Play Again")
        if session.match.actor != 0:
            raise HTTPException(409, "Computer is taking its turn")
        try:
            session.match = apply_awale_action(
                session.match, 0, "sow", pit=payload.pit
            )
        except IllegalAwaleMove as exc:
            raise HTTPException(422, str(exc)) from None
        session.version += 1
        _computer_reply(session)
        session.last_active = time.monotonic()
        return _no_store(_snapshot(session))
