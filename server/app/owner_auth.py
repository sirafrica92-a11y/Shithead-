"""Verify Google's signed ID token for the single SHITHEAD Games owner.

The Google client ID is public. All verification is server-side, and tokens are
used only to establish a short-lived, signed first-party session. Never store
the ID token, Google access tokens, or a token in the analytics database.
"""
from __future__ import annotations

from typing import Any

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2 import id_token
from starlette.concurrency import run_in_threadpool


def _verify(credential: str, client_id: str) -> dict[str, Any]:
    # This verifies signature, issuer, audience and expiration against Google.
    return id_token.verify_oauth2_token(credential, GoogleRequest(), client_id)


async def verify_google_token(credential: str, client_id: str) -> dict[str, Any]:
    # Google's key-fetching verifier uses blocking I/O. Never block the
    # WebSocket event loop while a dashboard owner signs in.
    return await run_in_threadpool(_verify, credential, client_id)
