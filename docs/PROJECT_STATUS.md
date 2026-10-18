# Project status

**Date:** 16 October 2026
**State:** foundation proposed on branch `foundation/v0.1-proposed` in draft PR #1. `main` contains only the initial README until an owner-approved merge. W1 (turn-seat selector) and W2 (pile-pass reducer) are implemented and verified on `build/w1-turn-seat-selector`; W3 (ordinary-play reducer) is not yet built.

## Established

- Existing owner-created GitHub repository `sirafrica92-a11y/Shithead-`.
- 2–6-player competitive multiplayer custom Shithead concept.
- Shit Face cosmetic-only optional mode.
- Owner's original master prompt and later 2-, 3-, 4-player tactical scenario descriptions.
- Owner's general logic scales to 5 and 6 seats (derived, not new rules).
- Server-authoritative FastAPI + WebSockets is the later explicit backend choice; React Native iOS/Android is the original primary client target.
- SOUL-first supervised product-development intention, with Claude filling tooling gaps.
- **W1** `server/app/rules/turns.py` — turn-seat selector, verified.
- **W2** `server/app/rules/pile_pass.py` — pile-pass reducer, verified.
- Test suite green: **56 passed, 2 skipped** (the 2 skips are pending owner decisions O-09/O-10).

## Not established

- Approved final rules for deal, seven-lock, special multi-card counter sequencing, endgame and finish semantics.
- W3 ordinary-play reducer, and a playable browser or mobile game.
- Hosting, domain connection, player accounts or deployment.
- Production QA / CI beyond the local test suite.
- Completed owner review of this proposed foundation.

## Next gate

Owner settles the three W3 gameplay decisions (four-of-a-kind clearing, the 2's effect, group plays under seven-lock), then W3 begins from the scope in `docs/WORK_PACKETS.md`.

## Update convention

Record each branch/commit, specific changes, what was actually executed and verified, outstanding decisions and the owner approval that allowed it.
