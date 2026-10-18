# W4 browser-based Shithead — local preview

This is a live 2–6-player match server and browser prototype built with
FastAPI and WebSockets. It is not a public deployment or production app.

## What works (in the completion PR)

- 54/108 distinct physical cards dealt 3 face-down, 3 face-up and 3 in hand.
- Owner D-019 start seat (lowest three ranks) and direction (lower adjacent
  neighbour), except an unresolved exact third-card tie, which yields a
  recoverable error instead of an invented rule.
- Higher-or-equal ordinary play; grouping; special 2, 7, 10; four-of-a-kind;
  hand refills; face-up/face-down; pickup; winner/loser logic.
- Multi-card 3/Joker attacks, extra skips, redirects, acceptance and skipped
  seats relative to the original actor.
- Server-authoritative, versioned socket actions; private hand snapshots;
  per-tab credentials; rejoin with existing seat and SQLite restart recovery.
- Deterministic action-trace, conservation and endgame tests for seats 2–6.

## Run on Windows

Install Python 3.12 or later and install requirements in Command Prompt:

    py -3 -m pip install -r requirements.txt

Then double-click "Start Shithead.bat" or run "py -3 run_local.py".

Start a 2-player room, open a second browser tab, join with the same room
code and another player name, and mark both players ready. Gameplay begins.

SQLite data is saved in ~/.shithead/local_rooms.sqlite3 (Windows user home).
Seat credentials are tab-specific; refreshing retains an existing seat. Data
is stored locally, never uploaded to a hosting provider. Keep the original
browser tab open so you can reconnect after server restart.

## Product limitations

- Remains localhost only (127.0.0.1). No cloud hosting, guest accounts,
  matchmaking, mobile clients or paid services.
- Exact three-card starting tie remains an owner decision, not guessed.
- AFK, disconnect timeout/forfeit policy needs owner instruction. Disconnecting
  leaves that seat occupied for a possible reconnect.
- SQLite process is designed for a single local worker, not multi-worker
  public matchmaking. A launch needs security and operational QA.
- There is no substitute for two real humans testing the complete browser
  experience; automated tests cover reducers, API/WebSocket, recovery and
  representative legal traces, not every possible play.
