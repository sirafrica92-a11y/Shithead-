# Staging: play.shithead.games

The site is an open preview for friends, NOT a public production launch.

Railway service: deploy branch `deploy/railway-shithead-games-staging`.
Railway needs one persistent volume mounted at `/data`.
One Python worker, with Railway's `PORT` env var, FastAPI, and WebSockets.

## Dependencies

`requirements.txt` installs `uvicorn[standard]`, which is what provides the
`websockets` library. Plain `uvicorn` has no WebSocket implementation: it logs
`No supported WebSocket library detected` and answers `/ws/{room_id}` with 404,
so every match silently fails to connect. Do not relax that pin, and keep CI
installing from `requirements.txt` rather than an ad-hoc package list, or the
build can go green while the deployed server cannot hold a socket.

## Joining

There is no site password and no room password. A host creates a room and
shares its four-character code; players enter a name and the code, and join.
Codes are uppercase alphanumeric and matched case-insensitively.

Privacy rests on the per-seat token, not on a shared secret: it is issued once
when a seat is taken, never appears in a public snapshot, and is what restores
a seat after a disconnection. Only the seat's owner sees that seat's hand.

Wrong room codes are rate limited per client address
(`SHITHEAD_FAILED_LOOKUP_LIMIT`, default 10, per
`SHITHEAD_RATE_WINDOW_SECONDS`, default 60). Only failed lookups count, so a
player holding a real code is never throttled by someone else guessing.

## Environment variables

| Variable | Required | Purpose |
|---|---|---|
| `RAILWAY_VOLUME_MOUNT_PATH` | yes, in cloud | SQLite lives on the persistent volume, never the ephemeral disk |
| `SHITHEAD_FAILED_LOOKUP_LIMIT` | no (default 10) | wrong room codes allowed per window, per address |
| `SHITHEAD_RATE_WINDOW_SECONDS` | no (default 60) | the window for the above |

`SHITHEAD_TEST_PASSWORD` is no longer read by the application and can be
removed from the Railway service.

## Verify after deploying

1. The home page loads with no password prompt.
2. Creating a room returns a four-character code.
3. Two browser tabs join that one room by code, Ready up, and play cards.
4. The browser console shows a WebSocket that stays open, not a 404 on `/ws/`.
5. Refresh a tab and reconnect to the existing seat; no second seat appears.
6. Restart the service and confirm rooms and seats survive via the `/data` volume.
7. A wrong code returns 404, and repeated wrong codes start returning 429.

Rooms are open to anyone holding the code. Real accounts, moderation,
multi-instance storage, and AFK policies remain production requirements.
