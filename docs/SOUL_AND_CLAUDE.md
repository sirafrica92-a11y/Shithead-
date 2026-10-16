# SOUL-first development contract

**Owner:** Africa. **Lead project:** SOUL (as her current capabilities allow). **Implementation mentor / specialist:** Claude Code. This division will change as SOUL's tools improve.

## Project separation

- This repository is the game's canonical source.
- SOUL's own application repository remains separate; **do not** edit SOUL source, credentials or handover as a side effect of this game.
- The game must be built for 2–6 participants using the owner's rules, not default Shithead variants.
- Agents must read `FOUNDATION.md`, `docs/RULES.md`, `docs/TURN_ENGINE.md`, `docs/TEST_PLAN.md`, `docs/OPEN_DECISIONS.md` and `docs/PROJECT_STATUS.md` before coding.

## Responsibilities today

**SOUL:** Study the project; propose a bounded change; prepare code/documentation in an approved local folder; report exact diffs; ask owner to approve writes; where available use Repos to commit and push approved changes; preserve requirements and decision log.

**Claude:** Provide engineering skills SOUL does not yet have: full Python test suites, local servers, WebSocket integration tests, debugging and deployment/configuration. Explain each intervention plainly so it can later become a SOUL capability.

**Africa:** Decides ambiguous gameplay rules, grants scoped access, reviews consequential changes, approves commits/merges and authorises production deployment and spend.

## Working rules

1. Start with the owner-specified rules and run acceptance examples before UI polish.
2. Never claim an action, test, deployment or build occurred without evidence.
3. One bounded deliverable at a time; code and tests together.
4. Agents cannot silently alter confirmed owner rules.
5. Keep source-of-truth in GitHub; describe exact branch, commit and tests in every handover.
6. No automatic merge to `main`, production release, external payment or secrets.
7. Treat GitHub visibility as public; no secrets/personal data.
8. When Claude must take over, log **what SOUL lacked, what Claude did, and a later safe tool opportunity**.

## Recommended first cycle

1. SOUL studies approved docs and states how target-vs-next mechanics work.
2. Claude drafts a minimal typed `GameState` and pure 3/Joker reducer with two-seat and three-seat examples, no unsupported deck/finish assumptions.
3. SOUL reviews diff against the rulebook and proposes corrections if needed.
4. Claude runs tests and attaches results.
5. Africa approves next slice; SOUL leads as her tools allow.

The outcome goal is **SOUL learning through supervised delivery**, not prematurely asserting she can run complex tools unattended.
