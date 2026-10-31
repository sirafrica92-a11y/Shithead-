"""Solo Play Dara: an isolated computer opponent for the existing 5x6 rules.

This router never creates multiplayer rooms and never writes to the /data volume.
The authoritative Dara engine remains the sole referee for all game actions.
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass, field, replace
import hmac
from pathlib import Path
import secrets
import time
from typing import Literal

from fastapi import APIRouter, Header, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictInt

from server.app.dara import (
    DaraMatch, IllegalDaraMove, apply_dara_action, legal_dara_moves,
    make_dara_match, private_dara_view,
)

router = APIRouter()
MAX_SESSIONS = 80
SESSION_TTL = 2 * 60 * 60
BOT_STEP_LIMIT = 64


@dataclass
class SoloDaraSession:
    token: str
    match: DaraMatch
    version: int = 0
    action_trace: list[dict] = field(default_factory=list)
    last_active: float = field(default_factory=time.monotonic)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


_sessions: dict[str, SoloDaraSession] = {}
_registry_lock = asyncio.Lock()


class SoloDaraAction(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=43, max_length=43)
    version: StrictInt = Field(ge=0)
    kind: Literal["place", "move", "capture"]
    index: StrictInt | None = Field(default=None, ge=0, le=29)
    source: StrictInt | None = Field(default=None, ge=0, le=29)
    destination: StrictInt | None = Field(default=None, ge=0, le=29)


class SoloDaraReset(BaseModel):
    model_config = ConfigDict(extra="forbid")
    token: str = Field(min_length=43, max_length=43)
    version: StrictInt = Field(ge=0)


def _snapshot(session: SoloDaraSession) -> dict:
    return {
        "version": session.version,
        "solo": True,
        "computer_actions": list(session.action_trace),
        "players": ["You", "Computer"],
        "game": private_dara_view(session.match, 0),
    }


def _no_store(data: dict, code: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=code, headers={"Cache-Control": "no-store"})


def _pairs(cells: tuple[int, ...], player_piece: int) -> int:
    """Count adjacent orthogonal own pairs without changing the game board."""
    score = 0
    for i, piece in enumerate(cells):
        if piece != player_piece:
            continue
        r, c = divmod(i, 6)
        if c < 5 and cells[i + 1] == piece:
            score += 1
        if r < 4 and cells[i + 6] == piece:
            score += 1
    return score


def _evaluate(match: DaraMatch) -> float:
    """Public-board-only evaluation from the computer's (seat 1) perspective."""
    if match.finished:
        if match.winner == 1:
            return 100000.0
        if match.winner == 0:
            return -100000.0
        return 0.0
    own = match.cells.count(2)
    other = match.cells.count(1)
    lead = 70.0 * (own - other)
    alignments = 5.0 * (_pairs(match.cells, 2) - _pairs(match.cells, 1))
    central = 0.0
    for i, piece in enumerate(match.cells):
        if not piece:
            continue
        r, c = divmod(i, 6)
        # Prefer useful central squares during placement, not a rule change.
        weight = (2 - abs(r - 2)) + (2.5 - abs(c - 2.5))
        central += weight * (1 if piece == 2 else -1)
    return lead + alignments + 0.7 * central


def _legal_options(match: DaraMatch, seat: int) -> list[tuple[str, dict]]:
    legal = legal_dara_moves(match, seat)
    if legal["captures"]:
        return [("capture", {"index":i}) for i in legal["captures"]]
    if legal["places"]:
        return [("place", {"index":i}) for i in legal["places"]]
    return [("move", {"source":src, "destination":dst})
            for src, dst in legal["moves"]]


def _best_bot_action(match: DaraMatch) -> tuple[str, dict]:
    """Choose only engine-approved moves, including compulsory captures.

    A new triple is followed by an actual legal capture in lookahead so the
    computer recognises the value of creating one, without shortcutting the
    pending-capture phase or modifying any established Dara rules.
    """
    if match.finished or match.actor != 1:
        raise ValueError("Not the computer's Dara turn")
    actions = _legal_options(match, 1)
    if not actions:
        raise RuntimeError("Dara engine returned an active computer turn without legal moves")
    scored = []
    for position, (kind, kwargs) in enumerate(actions):
        after = apply_dara_action(match, 1, kind, **kwargs)
        if after.pending_capture and after.actor == 1:
            captures = _legal_options(after, 1)
            score = max(
                _evaluate(apply_dara_action(after, 1, take_kind, **take_kwargs))
                for take_kind, take_kwargs in captures
            )
        else:
            score = _evaluate(after)
        # Stable ordering for ties; do not use paid AI or inspect player secrets.
        scored.append((score, -position, kind, kwargs))
    _, _, kind, kwargs = max(scored)
    return kind, kwargs


def _computer_reply(session: SoloDaraSession) -> None:
    session.action_trace = []
    # Placement is turn-based. A capture can give the bot one extra action.
    # The bound also prevents any unexpected engine state from hanging a request.
    for _ in range(BOT_STEP_LIMIT):
        before = session.match
        if before.finished or before.actor != 1:
            return
        kind, kwargs = _best_bot_action(before)
        session.match = apply_dara_action(before, 1, kind, **kwargs)
        session.version += 1
        if kind == "place":
            message = f"Computer placed a stone on square {kwargs['index'] + 1}."
        elif kind == "move":
            message = (f"Computer moved a stone from square {kwargs['source'] + 1} "
                       f"to {kwargs['destination'] + 1}.")
        else:
            message = f"Computer captured your stone on square {kwargs['index'] + 1}."
        if session.match.pending_capture and kind == "move":
            message += " Formed three; a capture follows."
        session.action_trace.append({
            "message": message,
            "game": private_dara_view(session.match, 0),
        })
    if not session.match.finished and session.match.actor == 1:
        raise RuntimeError("Dara computer exceeded its safe consecutive-action limit")


async def _require_session(key: str, token: str) -> SoloDaraSession:
    if not isinstance(token, str) or len(token) != 43:
        raise HTTPException(404, "Solo Play session unavailable")
    session = _sessions.get(key)
    if (session is None or not hmac.compare_digest(session.token, token)
            or time.monotonic() - session.last_active >= SESSION_TTL):
        raise HTTPException(404, "Solo Play session unavailable")
    return session


@router.get("/solo/dara", include_in_schema=False)
async def dara_solo_page():
    return FileResponse(Path(__file__).parent / "static" / "solo-dara.html",
                        headers={"Cache-Control": "no-store"})


@router.get("/solo/dara.js", include_in_schema=False)
async def dara_solo_script():
    return FileResponse(Path(__file__).parent / "static" / "solo-dara.js",
                        media_type="application/javascript",
                        headers={"Cache-Control": "no-store"})


@router.post("/api/solo/dara", status_code=201)
async def create_dara_solo():
    async with _registry_lock:
        now = time.monotonic()
        for key, session in list(_sessions.items()):
            if now - session.last_active >= SESSION_TTL:
                del _sessions[key]
        if len(_sessions) >= MAX_SESSIONS:
            raise HTTPException(503, "Solo Play is busy; try again shortly")
        key = secrets.token_urlsafe(18)
        session = SoloDaraSession(
            token=secrets.token_urlsafe(32),
            match=make_dara_match(),
        )
        _sessions[key] = session
    _computer_reply(session)
    return _no_store({"id": key, "token": session.token, **_snapshot(session)}, 201)


@router.get("/api/solo/dara/{key}")
async def resume_dara_solo(key: str, x_solo_token: str | None = Header(default=None)):
    session = await _require_session(key, x_solo_token or "")
    async with session.lock:
        _computer_reply(session)
        session.last_active = time.monotonic()
        state = _snapshot(session)
        state["computer_actions"] = []  # Resume must not replay past turns.
        return _no_store(state)


@router.post("/api/solo/dara/{key}/reset")
async def reset_dara_solo(key: str, payload: SoloDaraReset):
    session = await _require_session(key, payload.token)
    async with session.lock:
        if payload.version != session.version:
            raise HTTPException(409, "Board changed; refresh the match")
        session.match = make_dara_match()
        session.version += 1
        _computer_reply(session)
        session.last_active = time.monotonic()
        return _no_store(_snapshot(session))


@router.post("/api/solo/dara/{key}")
async def play_dara_solo(key: str, payload: SoloDaraAction):
    session = await _require_session(key, payload.token)
    async with session.lock:
        if payload.version != session.version:
            raise HTTPException(409, "Board changed; refresh the match")
        if session.match.finished:
            raise HTTPException(409, "Match finished; choose Play Again")
        if session.match.actor != 0:
            raise HTTPException(409, "Computer is taking its turn")
        try:
            session.match = apply_dara_action(
                session.match, 0, payload.kind, index=payload.index,
                source=payload.source, destination=payload.destination,
            )
        except IllegalDaraMove as exc:
            raise HTTPException(422, str(exc)) from None
        session.version += 1
        _computer_reply(session)
        session.last_active = time.monotonic()
        return _no_store(_snapshot(session))
