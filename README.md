# SHITHEAD Games

**Live multiplayer platform:** [play.shithead.games](https://play.shithead.games)

Shithead Games brings approachable traditional games from different cultures into one mobile-friendly multiplayer home. The original Shithead card game has grown into a multi-game platform while retaining its original jester logo and dark, gold and crimson visual identity.

## Verified status — 30 October 2026

| Game | Players | Status |
| --- | --- | --- |
| Shithead | 2–6 | Live; owner-defined card rules, including 3/Joker counterplay |
| Ludo | 2–4 | Live; server-controlled dice, blockades and rematches |
| Awalé (Oware Abapa) | 2 | Live; 12-pit sowing, feeding, captures and scoring |
| Dara | 2 | In development, **not live**; draft PR #17 |

The live Railway deployment is commit `30c44ed47af4f09b1ade162c8302603d408b86f7` on `deploy/railway-shithead-games-staging`. The release CI recorded **364 passing Python tests** plus JavaScript syntax checks. Railway reported a successful deployment and healthy replica. This does **not** replace independent real-device multiplayer testing.

## Repository layout and development status

**Important:** GitHub's default `main` branch is an initial historical snapshot, **not the live application's source code**. Inspect the [active deployment branch](https://github.com/sirafrica92-a11y/Shithead-/tree/deploy/railway-shithead-games-staging) for the actual server, frontend, tests, rules and [single living handover](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md).

- `server/app/` — FastAPI multiplayer rooms, authenticated WebSockets and separate server-authoritative game engines.
- `server/app/static/` — branded responsive game interfaces.
- `server/tests/` — rule, multiplayer, recovery and existing-game regression tests.
- `docs/RULES.md`, `docs/DECISION_LOG.md` — authoritative custom Shithead decisions; do not substitute standard rules.
- `HANDOVER.md` — current game roadmap, safe integration rules and release gates.

Dara is being developed independently. Its draft PR's latest CI passed **374 tests**, but rules-variant review and browser checks remain release gates. Do not call it shipped.

## Engineering principles

Preserve existing games while adding new ones: isolated game engines, shared room/seat infrastructure, private player state, persistent match recovery, reviewable pull requests and regression testing. Never merge or deploy unfinished games without owner approval. The live SQLite volume must remain attached at `/data`.

**Portfolio note:** This is a functioning, deployed product, not just a proposed game. The public default branch is deliberately documented as a historical pointer until the live application is safely reconciled with it.
