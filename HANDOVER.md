# SHITHEAD GAMES — SINGLE ACTIVE HANDOVER
Updated: 2026-10-31 (six-game milestone; analytics and capacity release candidate) | Owner: Africa | Read this BEFORE changes.

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

## Game 06 — now merged and deployed
- **Jamaican Dominoes** deployed: four players, Partner mode by default (2 teams) with optional individual Cut Throat scoring, rule-set details in `server/app/dominoes.py`. PR #20 merge `1240844275556784030e923706eb8dcfe143cabc`, Railway deployment `01a54176-1b5a-41b8-aeae-3071392e9537` SUCCESS. Latest-head 397 automated Python tests and six client JS syntax checks passed before merge; successful deployment and healthy single replica. Live four-device browser playthrough and game-variant review still recommended. Retain the original jester brand and the shared `/data` volume.

## Owner-only analytics dashboard — integrated release (production activation pending)
Combined release branch `release/owner-analytics-capacity-home-20261031` is based on production `5d39f18` (which already contains the featured SHITHEAD / Other Games homepage). Original source PRs: #22 and #23; integrated PR #25. The six game engines and persistent room database are unchanged. Require exact-head CI, deployment verification and separately configured admin secret.

The requested problem is not existing gameplay; it is missing first-party visibility into visitors and which games actually start. Add a separate observer with zero change to six independent game engines:
- `server/app/analytics.py` creates `analytics.sqlite3` alongside `rooms.sqlite3` on the existing persistent Railway volume, using a separate aggregate-only table. No migration or modification of the live rooms schema.
- Page views are homepage GETs (not unique people); coarse source from UTM/referrer (not raw URLs); rooms and joins are counted after successful server actions.
- Match starts are **actual successful Ready, unanimous rematch, or approved host restart**, not a game picker click or room creation. Match completions are counted only on the first verified transition to finished. Individual moves deliberately do not write analytics to avoid adding latency to gameplay. Domino modes reported distinctly.
- `/owner/analytics`, `/owner/api/analytics`, `/owner/api/analytics.csv` owner-only, guarded by `SHITHEAD_ADMIN_PASSWORD` via HTTPS HTTP Basic username `owner`. **By default these endpoints return 404 until a strong secret is configured in Railway environment variables. Never hardcode, commit, or publish this password.** No browser-accessible public reporting endpoint.
- Data limits: daily aggregated counters; no stored room codes, player names, tokens, IP addresses, unique visitor IDs, raw referrers, or cookie tracking. UTC reporting and export; report can be filtered to 7/30/90/365 days or all time.
- Fail-open: if analytics storage fails, gameplay must continue. Authenticated admin report responds 503 instead of falsely showing zero.
- Admin `owner.html` and `owner.js` are separate from the game home UI and never alter its logo or screens. No external libraries, trackers or network calls.
- **Release gates:** run complete existing six-game Python suite and syntax checks including owner.js; cover owner auth, blocked unauthenticated access, source privacy, counters, creation/join/start/completion/restart and duplicate messages, persistence across restart, broken analytics database, existing game rules unchanged. Independently check the live browser owner UI at desktop and mobile, HTTPS-only access, room/mode reporting, and the persistent volume.
- **No historical backfill:** numbers start when event instrumentation actually reaches production, not before. A homepage view is not a unique visitor and may include bots.

**Operational next step:** Once PR #25 is merged/deployed, verify the exact Railway SHA, single running worker and preserved `/data` mount. Configure the private `SHITHEAD_ADMIN_PASSWORD` (20+ characters) directly in Railway settings; before configuration, owner routes intentionally return 404. Afterward, privately verify authenticated owner dashboard and export over HTTPS. Never put the password in GitHub or publicly show analytics.

## Capacity demand signal — included in integrated release PR #25
Integrated from feature PR #23 into the clean production-based release PR #25, without overwriting homepage PR #24. It adds a typed full-slot error for the **100 allocated/saved room limit**, a structured 503 `room_capacity_reached` with five-minute retry *suggestion* (not availability guarantee), and a branded home-page prompt that lets players join existing rooms. No queue or reservation exists. **Never claim 100 active games or people from 100 allocated room slots.**

Privacy-minimal analytics `capacity_rejections` counts each **failed new-room attempt** (per day and selected game/mode), including repeat attempts by the same visitor; not unique users, waitlist signups, concurrent play, or room popularity. Admin dashboard shows the measure separately. No rooms are removed, no capacity raised, no engine rules changed. Existing room join and reconnect remain possible at allocation cap. `server/tests/test_capacity_communication.py` provides contract and persistence checks.

Safety: full six-game CI plus owner.js syntax checks on the exact integrated release head are required. Verify mobile notice, ordinary new room creation, existing room joins, 100 allocated rooms vs active sessions and private owner authentication. Owner approval to merge and deploy has been provided in the current conversation; do not bypass any failed tests. Do not claim a real queue or 100 active players. Keep the /data volume unchanged. If expanding capacity later, measure real active sessions, test load and protect existing SQLite and game rooms. Don't imply the site has a true waiting list until a queue with durable position and acknowledgement is implemented.

## Post-release verification / known risks and proposed solutions
1. **Yoté manual gameplay:** GitHub passed 383 tests and five JS checks, including two authenticated players and illegal-action/reconnect contracts. No independent post-deploy multi-device browser playthrough is recorded. Mitigation: repeat real 2-device game including captures, bonus removal, rematch, refresh and 360px/390px mobile screenshots; correct issues on a separate branch.
2. **Flaky legacy Shithead start:** One Yoté CI run at the identical head returned a failure in the existing Shithead refresh-resync fixture because the starting-match object was None after readiness; another run at that same head passed 383. Likely D-019 random start-tie test nondeterminism. Mitigation: independently reproduce and fix the test setup in isolation, without changing D-019 gameplay or tie policy. Do not conceal the intermittent failure.
3. **Regional Yoté variant:** Document that our version uses one jump followed by one chosen bonus removal, with no automatic capture chaining and threefold repetition draw. Mitigation: compare against primary published rules and adjust only through owner-approved, separately tested changes.
4. **Platform integration scaling:** Each new game still needs minimal cases in main/lobby/client. Mitigation: retain independent reducers and immutable game catalogue; add contract tests before extracting any further shared routing abstractions. Do not refactor working games merely for abstraction.
5. **Deployment/data:** Railway successful for all six games, mounted `match-data` at `/data`. Mitigation: verify mount/replicas and existing room restores after future releases; never replace the volume.

## LOCKED FUTURE GAME QUEUE — do not build simultaneously
1. **Morabaraba** — Southern Africa; pattern recognition and long-range planning. Research first; not yet approved for implementation.

**DO NOT BUILD:** Fanorona (specifically removed by owner as too complex / not worth learning to validate). Do not sneak it into the backlog. Do not add other complex games including chess to the near-term queue. No new game beyond these selections without explicit owner discussion. Research can cover queued games but **develop and deploy one game at a time**.


## Owner-only Google sign-in and Railway billing card — development PR (not deployed)
- No change to any public player journey: Shithead, Ludo, Awalé, Dara, Yoté and Jamaican Dominoes remain guest-access games. No player registration.
- Admin-only Google Identity Services sign-in at `/owner/login`, restricted by the verified Google ID-token email and issuer/audience/signature/expiry checks to the owner's account. Never trust an email typed in a form or an unsigned client claim.
- Google mode requires three Railway service environment variables: `SHITHEAD_GOOGLE_CLIENT_ID` (Google Cloud Web OAuth client ID, a public identifier), `SHITHEAD_OWNER_EMAIL` (the owner's allowlisted Google email), `SHITHEAD_ADMIN_SESSION_SECRET` (private random 32+ character signing key). Use Google's authorised JavaScript origin `https://play.shithead.games`. Configure via Railway secure variables, not GitHub; do not record or commit credentials here.
- Login nonce and origin check protect sign-in state changes, signed HttpOnly/Secure/SameSite Strict session cookie (8-hour limit). HTTP Basic is NOT a bypass when all three Google settings are enabled. Logout invalidates the browser cookie. This is not a payment processor.
- Private dashboard includes **next Railway payment/renewal date**, **monthly usage estimate in USD**, **monthly spending budget**, plus the original per-game popularity, match starts, completed matches, traffic sources, and day/game room-creation denials.
- Billing values are **manual owner-supplied values** from optional variables `SHITHEAD_RAILWAY_NEXT_DUE_DATE` (YYYY-MM-DD), `SHITHEAD_RAILWAY_USAGE_USD`, `SHITHEAD_RAILWAY_BUDGET_USD`. Do not claim automatic Railway invoice access, a guaranteed billing date, or exact current spend. Show Not set when missing; provide official Railway usage link.
- Google Cloud OAuth web client setup needs the owner's explicit account action (creating OAuth web client and configuring authorised origin). No credentials created in background. Test exact CI at development branch head before merge; no automatic deployment until owner approves.

## Owner IT service-management registers (feature PR #26; not deployed)
The owner dashboard now includes three adjacent, responsive columns: **Incidents** (restore interrupted service), **Problems** (investigate root causes or recurring incidents), **Changes** (record planned/deployed/rolled-back interventions). Each has a small manual form, reference ID, status and historical owner notes. These entries are persisted in a new `owner_operations.sqlite3` beside the existing databases on `/data`, not in live rooms. No game state, rules, deployment or operational alert is changed when an entry is added.
Owner-only endpoints: GET/POST `/owner/api/operations`, POST `/owner/api/operations/{id}/status`. Same authentication gate as analytics; mutating requests require the expected origin. No automatic incident detection or integrations are claimed. A 503 is returned when the operations database is unavailable. Run isolated auth/CRUD/persistence tests and the full six-game regression suite before merge.
 
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

## Current integrated release candidate (not deployed)
The live homepage redesign (featured original Shithead + Other Games) is preserved from PR #24 merge `5d39f18bbf65194dca10fb0cb775b1278717d61c`. This integration branch is based on that commit and carries the owner analytics plus room-capacity communication from draft PRs #22 and #23. Validate the exact combined head in CI before release. The owner dashboard requires a strong `SHITHEAD_ADMIN_PASSWORD` in Railway environment variables; without it the owner routes deliberately return 404. Never insert or log a password in a README or commit. Existing six game engines, rooms schema and attached /data volume are unchanged. On release, update this section with exact CI SHA, deployment ID, and manual security/visual QA results.
