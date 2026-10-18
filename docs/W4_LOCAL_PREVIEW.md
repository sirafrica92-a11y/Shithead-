# W4: local multiplayer lobby — development slice

This branch adds a **local-only prototype**, not a deployed game.

- FastAPI API to create a room with 2–6 seats.
- Seat joins use private random bearer tokens returned only to the joining client.
- WebSocket authenticates the seat, broadcasts public lobby state, and accepts
  readiness updates with expected version and bounded request-ID replay checks.
- Read-only public snapshots expose readiness/online status, never tokens.
- A lightweight browser page at `/` supports create, join, ready, and live updates.

## Running locally

From the repository root, with Python 3.12+:

```sh
python -m pip install fastapi uvicorn httpx pytest
python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8000
```

Open http://127.0.0.1:8000 and use multiple browser windows to join the same
room. The server listens only on localhost; this is not publicly hosted.

## Boundaries and cautions

- W1/W2 implementations are untouched. W3 ordinary-play is not yet integrated
  with a complete game controller. **No cards are dealt or played here.**
- Tokens are development-only, held in RAM. No user identity or database.
- Room states and replay-ID caches disappear on process restart.
- Rejoining by a fresh Join POST **creates a new seat**; for an existing seat,
  retain the original token and authenticate again on the WebSocket.
- Does not yet implement game actions, card privacy/snapshots, starting-player
  algorithm, turn clock, persistence, spectator access, or public deployment.
- Before opening internet access: require HTTPS, rate limiting, auth/session
  design, persistence, reconnect/AFK rules, CORS/Origin policy review, and
  operational limits. This prototype is **not safe to expose publicly**.

## Test

```sh
python -m pytest -q server/tests
```

Do not merge with `main`, start hosting or incur paid charges without approval.
