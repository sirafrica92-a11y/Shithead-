# SHITHEAD / SHIT FACE — foundation v0.1 (PROPOSED)

**Owner:** Africa. **Status:** proposed, not approved as the final rulebook.  
**Project:** online 2–6-player card game with tactical pile attacks, counters and turn control.  
**Authority:** the owner's documented rules and decisions, not standard Shithead conventions or agent guesses.

## Read first

1. `docs/RULES.md`: gameplay contract, with confirmed rules distinct from interpretations.
2. `docs/TURN_ENGINE.md`: server-authoritative state-machine design and deterministic turn order.
3. `docs/TEST_PLAN.md`: behavioural examples and fault/QA strategy.
4. `docs/ARCHITECTURE.md`: technical decisions and implementation boundaries.
5. `docs/OPEN_DECISIONS.md`: details that must not be invented.
6. `docs/SOUL_AND_CLAUDE.md`: roles, approval flow and handover.
7. `docs/PROJECT_STATUS.md`: facts, progress, evidence and next action.
8. `docs/source/OWNER_RULES_PART_1.md` and `docs/source/OWNER_RULES_PART_2.md`: original owner-authored requirements and scenario accounts, preserved for traceability.

## Design pillars

- **Correctness first.** The server decides legality, phase, active actor and next turn. Clients only submit intentions.
- **Strategy preserved.** A 3 and Joker are interchangeable pile-attack/counter cards; targeting the immediate next player differs from targeting someone else.
- **No silent rule changes.** Where documents conflict, the owner's later scenario explanation is stronger than the earlier generic formulation, but unresolved interactions require a question or flagged test rather than invention.
- **No soft locks.** Every nonterminal server state has an available action or a bounded recovery policy; duplicate and stale requests are harmless.
- **Small working vertical slices.** Core pure rules engine and tests, local playable 2-player game, then full 2–6 real-time multiplayer, then optional modes and polish.
- **Provenance and ownership.** SOUL, Claude and future tools may propose; only the owner approves rule changes and production deployment.

## Scope

**In v0.1:** rulebook, engine contract, automated tests plan, web-first prototype option, future iOS/Android plan, authority/approval boundaries.

**Not yet built:** server, clients, database, WebSocket protocol, hosting, matchmaking, drinking effects, UI, domain, release, or deployed game.

## Canonicalisation

This proposed branch can be reviewed and then accepted into `main` by the owner. Do **not** automatically merge it. After acceptance, docs under `docs/` become implementation requirements subject to the confirmed-vs-open labels.

**Visibility:** the repository was public when this foundation was created. Never add secrets, private account data or unpublished assets without an explicit visibility decision.
