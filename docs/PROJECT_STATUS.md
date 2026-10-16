# Project status

**Date:** 16 October 2026  
**State:** foundation proposed on branch `foundation/v0.1-proposed` in draft PR #1. `main` contains only the initial README until an owner-approved merge. No game code has been implemented, built, tested or deployed.

## Established

- Existing owner-created GitHub repository `sirafrica92-a11y/Shithead-`.
- 2–6-player competitive multiplayer custom Shithead concept.
- Shit Face cosmetic-only optional mode.
- Owner's original master prompt and later 2-, 3-, 4-player tactical scenario descriptions.
- Owner's general logic scales to 5 and 6 seats (derived, not new rules).
- Server-authoritative FastAPI + WebSockets is the later explicit backend choice; React Native iOS/Android is the original primary client target.
- SOUL-first supervised product-development intention, with Claude filling tooling gaps.

## Not established

- Approved final rules for deal, seven-lock, special multi-card counter sequencing, endgame and finish semantics.
- Playable browser or mobile game.
- Hosting, domain connection, player accounts or deployment.
- Running CI/test suite, production QA, game-server implementation.
- Completed owner review of this proposed foundation.

## Foundation QA pass (documentation only)

- Added `SOUL_START_HERE.md` for real SOUL navigation, source pinning, study and review limitations.
- Added `AGENTS.md`, `docs/SCENARIO_MATRIX.md`, `docs/DECISION_LOG.md`, `docs/WORK_PACKETS.md` and `docs/FOUNDATION_QA.md`; included a draft PR template.
- Cross-checked the later owner scenarios against the generalised 2–6-seat rule without claiming missing multi-counter decisions were resolved.
- No runtime tests performed and no game code built. The revised materials still require Africa's review.

## Next gate

Owner reviews `FOUNDATION.md`, `docs/FOUNDATION_QA.md`, the concrete scenario matrix and open decisions; approve or request edits. Then use the correct pinned commit in SOUL Projects and run W0 (read-only comprehension). Only after that should implementation begin with a small pure resolver (W1).

## Update convention

Record each branch/commit, specific changes, what was actually executed and verified, outstanding decisions and the owner approval that allowed it.
