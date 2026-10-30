# SHITHEAD GAMES — SINGLE ACTIVE HANDOVER
Updated: 2026-10-30 (Dara development) | Owner: Africa | Read this BEFORE changes.

## Platform purpose (owner-approved)
SHITHEAD Games is an online multiplayer home for approachable traditional games from different cultures. Each game should invite and develop a distinct quality through play: adaptation, patience, foresight, sacrifice, pattern recognition or collaboration. Entertaining human-to-human play is the priority, not a classroom or a clone of chess. Accessible rules are non-negotiable: the owner should be able to understand/test a game without learning highly complex systems.

**Brand:** near-black #0b0b0e, dark charcoal #171416/#241d1b, antique gold #c7a06a, cream #f1e2cc, crimson #d3323a. KEEP original Shithead logo/jester and existing functions. Mobile-first, Android-friendly.
**Repository:** `sirafrica92-a11y/Shithead-`. Active deployed source: `deploy/railway-shithead-games-staging`. GitHub `main` is NOT the source of live functionality.
**Website:** https://play.shithead.games
**Railway:** project `Shithead Games Test`, `production` env, `shithead-web` service, GitHub branch above, one worker, SQLite persistent volume `match-data` at `/data`. Never alter or detach volume as part of adding a game.

## Current verified live state
- **Shithead** live: owner-custom cards and 3/Joker/7/2/10 mechanisms; preserve authoritative decisions in `docs/RULES.md`, `docs/DECISION_LOG.md` and `docs/source/`. Never substitute standard card rules.
- **Ludo** live: two–four players; server-controlled dice, blockades, rematches and recovery.
- **Awalé** live: two players, authoritative 12-pit Abapa engine. PR #15 merged after PR #16 safe catalogue and 364 passing regressions; deployed commit `30c44ed47af4f09b1ade162c8302603d408b86f7` via Railway deployment `5a1244b3-7b03-4dd2-bdd4-f59878dbba15`, SUCCESS, 1/1 online. Real live-device full-playthrough not independently evidenced.
- **Unified dark/gold redesign** merged via PR #14, merge `241a347b4b9f12f8b12d2f2eb78f528cf1ce5c7c`; Railway deployment `ca34d9ae-52a7-456b-854e-9b290f1ef969` reported **SUCCESS**, online 1/1 on 2026-10-30. This is a server-health report, NOT proof of hands-on device visual QA.
- Earlier Ludo browser review: `docs/LUDO_RELEASE_REVIEW_2026-10-30.md` contains actual Chromium runs with 2, 3 and 4 players. Historical evidence, not the current CI state.

## ONE ACTIVE DEVELOPMENT GAME — Dara (Nigeria / Sahel), Game 04
**Status: independent development branch, NOT MERGED/NOT LIVE.**
Branch: `feature/dara-game04-20261030`. Independent server-authoritative engine `server/app/dara.py`; uses existing room infrastructure with `room.dara` isolated state, new `/dara.js` browser renderer and themed 5x6 UI. `server/tests/test_dara_platform.py` covers rules, persistence and old-game room creation. **Do not claim verification before the latest CI and browser playthrough actually succeed.**

**Selected variant:** Maths Week Scotland-style 5x6 12 pieces/player, placement without lines of three, then orthogonal single-step movement, line-of-three captures, prohibited four-plus rows and loss below three pieces. Rules vary by region/source (some allow 3 during placement; some pass on blocked moves rather than losing). The present draft chooses blocked-player loss, threefold repetition draw, and protects opposing lines of three when other captures exist. **Review these explicit variant choices against sources and user expectations before release**; adapt code, rules screen and tests together, never silently.

**Release blockers / mitigations:**
1. Ensure full Python suite + JS syntax checks pass for ALL four games; repair any Dara regressions in the branch, preserve older engines byte-for-byte.
2. Run 2 authenticated player WebSocket complete-match, illegal-action, rematch and SQLite restart/reconnect tests. Add deterministic flows before claiming readiness.
3. Run local Chromium mobile 390px/360px and desktop screenshots, verify token selection and touch targets, no overflow, rules navigation and original logo.
4. Independently review differences in Dara published variants, capture and blocked-turn logic. Correct implementation and its explainer to one sourced rule contract.
5. Review shared `main.py`, `lobby.py`, `client.js` diff for isolated Dara routing, no changed behavior for prior games, proper seat limit and old SQLite restores.
6. Owner approval required separately before merge and Railway deployment. Verify actual deployed SHA + health, /data persistent volume and browser matches afterwards.

**At completion:** remove this active subsection, add concise verified completion record under live games, then promote only next approved game (Yoté) after owner go-ahead.

## LOCKED FUTURE GAME QUEUE — do not build simultaneously
1. **Yoté** — West African traditional game; sacrifice, tactics. Pending rule research and owner go-ahead.
2. **Dominoes** — cross-cultural; proposed cooperative/team mode, approachable rules. Choose precise format before implementation.
3. **Morabaraba** — Southern Africa; pattern recognition and long-range planning. Research first; not yet approved for implementation.

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
