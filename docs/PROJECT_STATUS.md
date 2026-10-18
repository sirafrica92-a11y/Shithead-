# Shithead project status — W1–W4 local playable preview

Source of truth: owner rulebook in docs/RULES.md, docs/DECISION_LOG.md and
docs/source/OWNER_RULES_PART_1.md / OWNER_RULES_PART_2.md.

Canonical development branch: build/w1-turn-seat-selector.
Preflight/recovery/rules fixes are proposed in the W4 completion pull request;
check its merge status before claiming they are on the canonical branch.

## Integrated milestones

- W1: pure turn-seat resolver, original actor anchors redirected attacks.
- W2: pure 3/Joker pile-pass attack/counter/accept reducer.
- W3: ordinary-play, 2/7/10, four-of-a-kind, zone and finishing reducer.
- W4: FastAPI, private WebSockets, rooms for 2–6 seats, browser preview, live
  moves and per-seat hidden-card snapshots.

## W4 completion patch

- D-019: starter by three-card ordered comparison; second player sets direction.
  A residual exact tie after the third comparison is an explicit recoverable
  owner-decision gate — never silently settled by seating order.
- 3/Joker: atomic multi-card skip/attack and extra skips retained across W2
  counter chains. Cards tracked by physical ID and conservation asserted.
- Full-deck deterministic legal-action traces, every 2–6-player seat count.
  Engine cannot promise every possible game strategy terminates; arbitrary bot
  pickup cycles are allowed by the rules. Separately tests 2–6-player endgame
  completion from card-conserving near-terminal fixtures.
- Local SQLite restores rooms, seated players, matches and accepted-request
  replay IDs after a restart. Only SHA-256 digests, not seat bearer tokens,
  are saved in the database.
- Browser remembers a token per tab for refresh/reconnection and renders
  authoritative stale-action snapshots.

## Remaining owner/product decisions

- D-019 exact three-card tie has no approved tiebreaker (explicit error).
- AFK, forfeit, timeout and spectator rules remain owner decisions.
- Internet hosting, identity/security hardening, React Native mobile clients
  and launch controls remain separate from the localhost preview.
- Real multi-person browser playtesting, especially long 3/Joker chains and
  third-card ties, must happen before any public deployment.

## Run on Windows without PowerShell

Use the canonical development branch after the repair PR is merged.
Install Python 3.12+. In Command Prompt, once in the repo folder:

    py -3 -m pip install -r requirements.txt

Double-click "Start Shithead.bat". The app opens in a browser at
http://127.0.0.1:8000. Keep the launcher window open to play.

This starts localhost only and costs no hosting fees.
