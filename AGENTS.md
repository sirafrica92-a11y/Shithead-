# Coding agent instructions — SHITHEAD Games

**FIRST: READ [HANDOVER.md](HANDOVER.md) IN FULL.** It is the single living platform handover and authoritative *current* direction. Verify its live/PR evidence yourself before proceeding. Do not treat old W0/W4 proposed-foundation instructions as the current roadmap.

## Owner requirements
1. **Protect existing live Shithead and Ludo gameplay.** Original card-rule owner sources (`docs/source/`, `docs/RULES.md`, `docs/DECISION_LOG.md`) outrank assumed standard card games. Never casually edit existing engines.
2. Platform vision: approachable traditional games across countries, each developing a distinct skill through play. **Game release order and exclusions are in HANDOVER.md.** Awalé in active review; Dara next; Yoté, Dominoes, Morabaraba later. **Do not add Fanorona.**
3. Preserve original SHITHEAD logo/jester, website, gold/cream/crimson dark brand, mobile usability, guest multiplayer, privacy and the persistent Railway `/data` volume.
4. Server is authoritative; keep room/auth/WebSocket/versioning/reconnect and persisted match state correct. Every game needs legal-move tests, full-playthrough tests and regression tests.
5. Work one game at a time. Use a branch, capture reproducible evidence, and obtain owner's explicit agreement before merge or production deployment. A passing unit suite alone does not establish UI or rules correctness.
6. Do not invent test results, successful deploys or screenshots. If an action or validation is unavailable, document the blocker, proposed resolution and exact next verification step.
7. **Living handover discipline:** completed games leave the active and pending sections after verified release; record a concise historical completion line instead. Note exact commits, CI, risks and proposed solutions so the next agent can independently assess and proceed or disagree.
8. No changes to the separate SOUL product repository, credentials, permissions or services while working on Shithead Games.

## Source hierarchy
- Present platform direction, active/queued work and takeover: `HANDOVER.md`
- Shithead owner rule contract: `docs/RULES.md`, `docs/source/`, `docs/DECISION_LOG.md`
- Architecture/tests/deploy details: `docs/ARCHITECTURE.md`, `docs/TEST_PLAN.md`, `docs/STAGING_DEPLOYMENT.md`
- Current truth: inspect actual GitHub branch, CI, code, PR and Railway deployment state; report any discrepancy in the living handover.
