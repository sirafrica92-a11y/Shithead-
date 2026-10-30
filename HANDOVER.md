# SHITHEAD GAMES — SINGLE ACTIVE HANDOVER
Updated: 2026-10-30 | Owner: Africa | Read this BEFORE changes.

## Platform purpose (owner-approved)
SHITHEAD Games is an online multiplayer home for approachable traditional games from different cultures. Each game should invite and develop a distinct quality through play: adaptation, patience, foresight, sacrifice, pattern recognition or collaboration. Entertaining human-to-human play is the priority, not a classroom or a clone of chess. Accessible rules are non-negotiable: the owner should be able to understand/test a game without learning highly complex systems.

**Brand:** near-black #0b0b0e, dark charcoal #171416/#241d1b, antique gold #c7a06a, cream #f1e2cc, crimson #d3323a. KEEP original Shithead logo/jester and existing functions. Mobile-first, Android-friendly.
**Repository:** `sirafrica92-a11y/Shithead-`. Active deployed source: `deploy/railway-shithead-games-staging`. GitHub `main` is NOT the source of live functionality.
**Website:** https://play.shithead.games
**Railway:** project `Shithead Games Test`, `production` env, `shithead-web` service, GitHub branch above, one worker, SQLite persistent volume `match-data` at `/data`. Never alter or detach volume as part of adding a game.

## Current verified live state
- **Shithead** live: owner-custom cards and 3/Joker/7/2/10 mechanisms; preserve authoritative decisions in `docs/RULES.md`, `docs/DECISION_LOG.md` and `docs/source/`. Never substitute standard card rules.
- **Ludo** live: two–four players; server-controlled dice, blockades, rematches and recovery.
- **Unified dark/gold redesign** merged via PR #14, merge `241a347b4b9f12f8b12d2f2eb78f528cf1ce5c7c`; Railway deployment `ca34d9ae-52a7-456b-854e-9b290f1ef969` reported **SUCCESS**, online 1/1 on 2026-10-30. This is a server-health report, NOT proof of hands-on device visual QA.
- Earlier Ludo browser review: `docs/LUDO_RELEASE_REVIEW_2026-10-30.md` contains actual Chromium runs with 2, 3 and 4 players. Historical evidence, not the current CI state.

## ONE ACTIVE DEVELOPMENT GAME — keep only unfinished work in this section
### Awalé (Côte d'Ivoire / West Africa) — PR #15, IN REVIEW / NOT LIVE
Branch: `feature/awale-third-game-20261030`.
Game: 2-player Oware / Awalé Abapa rules; 12 houses, 48 seeds, sowing, feeding, opposing 2/3 capture chains, cancelled grand-slam captures, scoring, repeat-end logic; independent server engine `server/app/awale.py`. Integrates `server/app/lobby.py`, `server/app/main.py`, `server/app/static/client.js`, responsive wooden board and rules `server/app/static/index.html`, `server/app/static/awale.js`; focused tests `server/tests/test_awale_platform.py`.

Verified earlier CI at `e3c56ba`: **350 passed**, JS checks on Shithead/Ludo passed. After that, added extra safety tests at commit `deb25ffe` for 80 complete random-play games, real two-client WebSocket actions, UI served paths. **These new tests MUST pass CI before anyone can merge**; browser full-playthrough, mobile visual QA and independent rules review remain release gates. Never claim these passed without actual evidence.

**Risks / checks + proposed solutions:**
1. Abapa variant edge cases (grand slam, no-feeding, repeated states, scoring/48 seed conservation): review authoritative published Oware rules, run seeded complete games, document edge-case decisions. Do not quietly change rules to satisfy tests.
2. Two-user browser progression, turns, illegal actions, rematch, reconnect, refresh: exercise independently authenticated WebSockets and real Chromium contexts. Existing `scripts/qa_ludo_browser.py` provides a pattern; write Awalé-specific repeatable smoke with screenshots at mobile/desktop widths.
3. UI orientation: south houses 0..5 are player 1, top houses 11..6 are player 2; render count/selection must correspond to server seat and remain usable on small screens.
4. Merging into existing live branch: inspect full diff, validate no Shithead/Ludo engine changes or jester asset modifications, run full regression CI. Only merge with owner consent; only release if safe. Verify Railway commit SHA, running replica, volume and actual game smoke after deploy. Previous release is rollback target.
5. Roadmap docs and onboarding may be stale; use this file for CURRENT direction; preserve source decisions and provenance without treating historical status text as live instructions.

When **Awalé is successfully finished and shipped**, remove its entire active-development subsection from this handover; move one brief completion line into the live-state section with PR, commit, tests and Railway deployment evidence. Do not leave completed work as 'to do'. Promote next approved game below.

## LOCKED FUTURE GAME QUEUE — do not build simultaneously
1. **Dara** — Nigeria / Sahel; NEXT immediately after verified Awalé release. Two players; placement then movement and captures by rows of three. Research rule variants, teach owner basic gameplay via short examples, select source-backed rules and complete tests before implementing. Develops planning, pattern recognition and restraint.
2. **Yoté** — West African traditional game; sacrifice, tactics. Pending rule research and owner go-ahead.
3. **Dominoes** — cross-cultural; proposed cooperative/team mode, approachable rules. Choose precise format before implementation.
4. **Morabaraba** — Southern Africa; pattern recognition and long-range planning. Research first; not yet approved for implementation.

**DO NOT BUILD:** Fanorona (specifically removed by owner as too complex / not worth learning to validate). Do not sneak it into the backlog. Do not add other complex games including chess to the near-term queue. No new game beyond these selections without explicit owner discussion. Research can cover queued games but **develop and deploy one game at a time**.

## NON-NEGOTIABLE ENGINEERING RULES
- The owner defines gameplay decisions. Protect established Shithead rules and Ludo rules, even where standard variants differ.
- Reuse already working multiplayer rooms, invitation codes, seat auth/token isolation, session recovery, WebSockets, serialization, rematches, reactions and the gold/cream/crimson design.
- Each new game gets its own server-authoritative rules engine, independent game state/persistence and test suite. Do not redesign the shared architecture unnecessarily.
- No regressions, broken UI, altered existing games, deleted live data or unwanted spending. Never merge/deploy without owner approval. Never manipulate production game state to test.
- BEFORE claiming a game finished: run complete suite, JS syntax checks INCLUDING the new game's JS, completed multiplayer match tests, illegal/out-of-turn actions, SQLite recovery, existing-game regression, mobile and desktop visuals, and verify expected game variant. Confirm code/asset diff.
- Prior to Railway update verify `deploy/railway-shithead-games-staging` contains approved commit. Deployment follows that source; reattachment to another branch is NOT routine. After deploy confirm status, commit SHA, health, gameplay smoke and database mount. Roll back if health or gameplay is affected.
- Distinguish proven PASS, unverified, and assumption clearly. A CI green run alone does not prove browser functionality.

## AGENT TAKEOVER PROTOCOL (mandatory)
1. Read THIS file first, then inspect branch, PRs, live Railway, authoritative rule docs, app code and current tests. Avoid stale W0/W4 onboarding as current instructions.
2. **Independently assess every previous agent's findings** and recommended solutions before agreeing. Identify gaps and report disagreements rather than automatically following a handover.
3. Record current branch+commit, **work actually completed**, tests actually executed with pass/fail evidence, changed files, incomplete work, observed and potential future risks, and a **proposed fix/mitigation for each risk** with validation steps.
4. Implement ONE next game or bounded improvement per branch, review diff, run full suite, open PR. Only merge/deploy after user authorizes it and verification is strong.
5. After completing a game, remove it from active/future handover tasks; add concise VERIFIED completion record to live-state section. Move exactly the next owner-approved title to 'active'; leave remaining queue tidy. Do not accumulate old handover notes; update this one canonical file.
6. If decisions or execution are blocked, document precisely what is missing and how the successor can check it. No invented successful tests, links, screenshots or claims.

## Historical sources retained for audit, NOT alternative current handovers
`docs/RULES.md`, `docs/DECISION_LOG.md`, `docs/source/`, `docs/SCENARIO_MATRIX.md`, `docs/TEST_PLAN.md`, `docs/STAGING_DEPLOYMENT.md`, `docs/LUDO_RELEASE_REVIEW_2026-10-30.md`. These contain important game rules and evidence; do not delete them merely to simplify onboarding.
