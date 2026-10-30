# SHITHEAD GAMES — SINGLE ACTIVE HANDOVER
Updated: 2026-10-30 (five-game milestone) | Owner: Africa | Read this BEFORE changes.

## Platform purpose (owner-approved)
SHITHEAD Games is an online multiplayer home for approachable traditional games from different cultures. Each game should invite and develop a distinct quality through play: adaptation, patience, foresight, sacrifice, pattern recognition or collaboration. Entertaining human-to-human play is the priority, not a classroom or a clone of chess. Accessible rules are non-negotiable: the owner should be able to understand/test a game without learning highly complex systems.

**Brand:** near-black #0b0b0e, dark charcoal #171416/#241d1b, antique gold #c7a06a, cream #f1e2cc, crimson #d3323a. KEEP original Shithead logo/jester and existing functions. Mobile-first, Android-friendly.
**Repository:** `sirafrica92-a11y/Shithead-`. Active deployed source: `deploy/railway-shithead-games-staging`. GitHub `main` is NOT the source of live functionality.
**Website:** https://play.shithead.games
**Railway:** project `Shithead Games Test`, `production` env, `shithead-web` service, GitHub branch above, one worker, SQLite persistent volume `match-data` at `/data`. Never alter or detach volume as part of adding a game.

## Current verified live state
- **Shithead** live: owner-custom cards and 3/Joker/7/2/10 mechanisms; preserve authoritative decisions in `docs/RULES.md`, `docs/DECISION_LOG.md` and `docs/source/`. Never substitute standard card rules.
- **Ludo** live: two–four players; server-controlled dice, blockades, rematches and recovery.
- **Yoté** live: 2-player West African 5x6 tactical board game with placements and jump/bonus captures; merged PR #18 as commit `c1de263e9ff908013bcecb504517938bfea4b68d`. Railway deployment `7ae9aae4-99e6-4310-98d7-7e143c473211` reported SUCCESS. One full CI run at the exact release head passed **383 tests** and all five JavaScript syntax checks. See risk notes for one intermittent legacy CI failure and browser QA remaining.
- **Dara** live: 2-player 5x6 Nigerian strategy game; merged PR #17 as commit `244b66a5b734b5cdd057add6145b72da3ee771b3`, Railway reported SUCCESS. CI on PR head `14dbaa36` passed 374 tests, four JS syntax checks. Still require manual live-device playthrough for end-to-end visual confirmation.
- **Awalé** live: two players, authoritative 12-pit Abapa engine. PR #15 merged after PR #16 safe catalogue and 364 passing regressions; deployed commit `30c44ed47af4f09b1ade162c8302603d408b86f7` via Railway deployment `5a1244b3-7b03-4dd2-bdd4-f59878dbba15`, SUCCESS, 1/1 online. Real live-device full-playthrough not independently evidenced.
- **Unified dark/gold redesign** merged via PR #14, merge `241a347b4b9f12f8b12d2f2eb78f528cf1ce5c7c`; Railway deployment `ca34d9ae-52a7-456b-854e-9b290f1ef969` reported **SUCCESS**, online 1/1 on 2026-10-30. This is a server-health report, NOT proof of hands-on device visual QA.
- Earlier Ludo browser review: `docs/LUDO_RELEASE_REVIEW_2026-10-30.md` contains actual Chromium runs with 2, 3 and 4 players. Historical evidence, not the current CI state.

## Current development queue
**No game is under active construction.** Five games are merged and deployed. Future games remain research candidates; begin only one new game after selecting and documenting its exact rules with the owner.

## Post-release verification / known risks and proposed solutions
1. **Yoté manual gameplay:** GitHub passed 383 tests and five JS checks, including two authenticated players and illegal-action/reconnect contracts. No independent post-deploy multi-device browser playthrough is recorded. Mitigation: repeat real 2-device game including captures, bonus removal, rematch, refresh and 360px/390px mobile screenshots; correct issues on a separate branch.
2. **Flaky legacy Shithead start:** One Yoté CI run at the identical head returned a failure in the existing Shithead refresh-resync fixture because the starting-match object was None after readiness; another run at that same head passed 383. Likely D-019 random start-tie test nondeterminism. Mitigation: independently reproduce and fix the test setup in isolation, without changing D-019 gameplay or tie policy. Do not conceal the intermittent failure.
3. **Regional Yoté variant:** Document that our version uses one jump followed by one chosen bonus removal, with no automatic capture chaining and threefold repetition draw. Mitigation: compare against primary published rules and adjust only through owner-approved, separately tested changes.
4. **Platform integration scaling:** Each new game still needs minimal cases in main/lobby/client. Mitigation: retain independent reducers and immutable game catalogue; add contract tests before extracting any further shared routing abstractions. Do not refactor working games merely for abstraction.
5. **Deployment/data:** Railway successful for all five, mounted `match-data` at `/data`. Mitigation: verify mount/replicas and existing room restores after future releases; never replace the volume.

## LOCKED FUTURE GAME QUEUE — do not build simultaneously
1. **Dominoes** — cross-cultural; proposed cooperative/team mode, approachable rules. Choose precise format before implementation.
2. **Morabaraba** — Southern Africa; pattern recognition and long-range planning. Research first; not yet approved for implementation.

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
