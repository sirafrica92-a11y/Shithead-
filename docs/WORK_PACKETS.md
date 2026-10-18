# SOUL's development packets — bounded jobs, not a fictional roadmap

Every packet has a narrow exit condition. **Only W0 is ready immediately.** Others require the stated owner approvals and working tools. No agent may claim tests ran or a release exists without evidence.

## W0 — Understand the game (SOUL first)

**Prerequisite:** Africa authorises a read-only source grant to the correct foundation commit and SOUL successfully studies it.

**Ask SOUL in Projects/Cowork:** Summarise 3/Joker attacks/counters and derive 2–6-seat results, with citations. Explain why Part One's blanket "skip one" description is too broad. Separate confirmed rules from derived examples and blockers. Propose a minimal testable engineering task.

**Acceptance:** no invented game rules, all 2–6-seat single-target scenarios correct, no conflation of original turn anchor with current pass target, correct disclosure of source version, clear unanswered case for "attack+extra skips+counter".

**Evidence:** SOUL's actual response and Africa's verdict. Do not claim the model was retrained; this is project-specific study.

## W1 — Pure turn-seat selector (SOUL guided, Claude tests if necessary)

**Prerequisite:** W0 accepted. Does **not** require full dealing/endgame rules.

**Scope:** Implement a pure deterministic resolver operating on a seat list, original actor, final collector and number of validated skip effects. Write tests for the **single-attack, no-extra-skip** rows in `docs/SCENARIO_MATRIX.md`. No FastAPI server or frontend yet.

**Exit:** next actor always comes from original scheduled sequence, not the last countering player. Explicitly test each target in 2–6 seats, including final collector = original actor after a counter.

**Do not:** silently settle unresolved combined/multi-card counter sequencing, or pretend you can produce a fully playable game from only this slice.

## W2 — Pile-pass state-machine reducer

**Prerequisite:** W1 and approved action/card-source assumptions for the slice.

**Scope:** `PLAYING` → `PILE_PASS_DECISION` → `PLAYING`, one 3/Joker attack, optional counter chain, accepted pickup, allowed-action whitelist, removed-from-game cards and authoritative error responses. Test no replay, wrong actor, stale versions, never two action owners.

**Exit:** deterministic pure reducer + focused tests; no WebSockets, UI or payment systems.

## W3 — Ordinary play and endgame

**Status:** **Delivered** (test execution still pending — see note below).

**Prerequisite:** owner resolves O-01 to O-08 in `docs/DECISION_LOG.md`.

**Scope:** 2/7/10, rank comparator, four-in-a-row, draw/refill, hand/face-up/face-down and finish semantics. Then full-match simulation with all 2–6 seating cases.

**Exit:** card conservation, no undefined action, repeatable tests, no secret leaks.

**Delivered scope:** `server/app/rules/ordinary.py` implementing the ordinary-play reducer — seven-lock, 10 clear with extra turn, 2 reset clearing the lock and counting toward quads, four-of-a-kind clear regardless of contributors, refill after action resolves, hand/face-up/face-down zones, blind face-down pickup, and finish detection. Tests: `server/tests/test_ordinary.py`, plus an extended `server/tests/test_w1_w2_composition.py` composing W3 with W1/W2. Docs updated: `docs/WORK_PACKETS.md`, `docs/OPEN_DECISIONS.md`, `docs/DECISION_LOG.md`, `docs/TURN_ENGINE.md`. W1/W2 files unchanged. Pure and deterministic; no persistence or network.

**Test execution note:** pytest could **not** be run in the sandbox — the RUN guard refused the source due to dunder/path tokens. The tests must **not** be treated as passing until Africa runs `python -m pytest -q` in `server/` after approval.

## W4 — Actual playable multiplayer and public launch

**Prerequisite:** complete rules, reconnect/AFK policy, owner host/budget approval.

**Scope:** FastAPI + WebSockets, auth/rooms/state storage and replay-safe event protocol; browser prototype if Africa agrees, then React Native iOS/Android client. Security/reconnect/network tests and measured latency. Only after acceptance consider Shit Face as purely cosmetic UI and optional domain/hosting.

## Capability transfer ledger (append for each packet)

| Packet/date | SOUL completed herself | Claude/owner had to do | Missing SOUL tool or approval | Verification |
| --- | --- | --- | --- | --- |
| W0 | Not attempted | — | Source connection/study pending | None |
| W3 | `server/app/rules/ordinary.py` ordinary-play reducer, `server/tests/test_ordinary.py`, extended `server/tests/test_w1_w2_composition.py`, docs updates | Run `python -m pytest -q` in `server/` and confirm results | Sandbox RUN guard refused source (dunder/path tokens), so pytest could not execute | None yet — tests written but not executed |

New capability must be demonstrated with a real task and actual test results, not inferred from source-code presence.
