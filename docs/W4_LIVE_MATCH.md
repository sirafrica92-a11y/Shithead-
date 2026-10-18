# W4 second slice — in-memory card match preview

This follows the **local lobby** slice. Server-authoritative gameplay runs
only in RAM, localhost. Joining 2–6 seats and marking every seat ready starts
a match. All seats see shared pile/face-up cards; only their authenticated
socket receives their own hand and any blind-revealed 3/Joker.

## Implemented

- 54 cards (2–4 seats) or 108 cards (5–6 seats), unique physical card IDs,
  three cards dealt to each face-down, face-up and hand zone.
- W3 ordinary play, pickup, face-down flips, 2/7/10, clears, refill and finishes.
- W2 attack, counter, accept and empty-pile skip, with card ownership checks.
- W1 turn resolution anchored to the original actor.
- Ready → PLAYING; per-seat private views; indexed card actions; optimistic
  room version, duplicate-request checks.
- Web browser control panel for game actions. No outside accounts or billing.

## Deliberate development gaps (NOT completed W4)

- Uses seat 0 and clockwise for match start, not D-019's lowest-card
  starting-player/direction algorithm.
- Attack/counter supports a single spent power per request, not all grouped
  attack+extra-skip rules or fully merged blind-power counter paths.
- No match persistence, AFK/forfeit policy, invitation security, authentication
  beyond a development token, production rate limits or internet deployment.
- No human-browser playtest, performance test, or complete automated full-match
  simulation through all seat counts. Not ready for public play.
- The W3 ordinary reducer and W1/W2 source remain unchanged.

## Run on localhost

```sh
python -m pip install fastapi uvicorn httpx pytest
python -m uvicorn server.app.main:app --host 127.0.0.1 --port 8000
```

Visit http://127.0.0.1:8000. Use another browser window to join a second seat.

Merge only after reviewing tests and owner approval. No hosting expense.
