"""Shared-password gate for the limited-access web playtest.

No user accounts are introduced here. The password must be set as a Railway
service secret, not committed or sent to the browser except during login.
The cookie is an HMAC derived from the password, not the password itself.
"""
from __future__ import annotations

import hashlib
import hmac
import os
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse


COOKIE_NAME = "shithead_preview"
COOKIE_MESSAGE = b"shithead-staging-cookie-v1"

LOGIN_HTML = """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Shithead — Private Test</title>
<style>
body{font:17px system-ui;margin:12vh auto;padding:0 20px;max-width:440px;background:#121d22;color:#fff}
form{background:#21353a;padding:24px;border-radius:16px}
input,button{box-sizing:border-box;width:100%;padding:14px;margin-top:14px;font:inherit;border-radius:9px}
input{background:#16272c;border:1px solid #8ea7a9;color:#fff}
button{background:#f38a3e;border:0;font-weight:700;cursor:pointer}
p{line-height:1.55;color:#c4d1d1}
</style></head><body>
<h1>Shithead — private test</h1>
<p>This game is still being tested. Enter the access password you received from the host.</p>
<form method="post" action="/test-login">
<label for="password">Test access password</label>
<input type="password" id="password" name="password" autocomplete="current-password" required>
<button type="submit">Enter game</button>
</form></body></html>"""


def cookie_for(secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), COOKIE_MESSAGE, hashlib.sha256).hexdigest()


def cookie_allowed(cookie: str | None, secret: str) -> bool:
    if not secret:
        return True  # Explicitly unprotected localhost development only.
    return bool(cookie) and hmac.compare_digest(cookie, cookie_for(secret))


def install_test_gate(app: FastAPI, *, cloud: bool) -> None:
    secret = os.getenv("SHITHEAD_TEST_PASSWORD", "")
    if cloud and len(secret) < 16:
        raise RuntimeError(
            "Internet deployment requires SHITHEAD_TEST_PASSWORD "
            "(at least 16 characters, set as a private service variable)."
        )
    app.state.test_gate_password = secret

    @app.get("/test-login", include_in_schema=False)
    async def get_login():
        if not secret:
            return RedirectResponse("/", status_code=303)
        return HTMLResponse(LOGIN_HTML, headers={"Cache-Control": "no-store"})

    @app.post("/test-login", include_in_schema=False)
    async def post_login(request: Request):
        if not secret:
            return RedirectResponse("/", status_code=303)
        body = await request.body()
        if len(body) > 2048:
            return JSONResponse({"detail": "Request too large"}, status_code=413)
        try:
            password = parse_qs(body.decode("utf-8"))["password"][0]
        except (UnicodeError, KeyError, IndexError):
            password = ""
        if not hmac.compare_digest(password, secret):
            return HTMLResponse(
                LOGIN_HTML.replace(
                    "<form method=", '<p role="alert">Incorrect password.</p><form method='
                ),
                status_code=401,
                headers={"Cache-Control": "no-store"},
            )
        response = RedirectResponse("/", status_code=303)
        response.set_cookie(
            COOKIE_NAME, cookie_for(secret), httponly=True, secure=cloud,
            max_age=7 * 24 * 3600, samesite="lax", path="/",
        )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.middleware("http")
    async def protect_test_site(request: Request, call_next):
        path = request.url.path
        if (not secret or path in ("/health", "/test-login")
                or cookie_allowed(request.cookies.get(COOKIE_NAME), secret)):
            response = await call_next(request)
        elif request.method == "GET" and path == "/":
            response = RedirectResponse("/test-login", status_code=303)
        else:
            response = JSONResponse({"detail": "Test password required"}, status_code=401)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        return response
