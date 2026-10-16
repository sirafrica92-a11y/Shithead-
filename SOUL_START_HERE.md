# SOUL — Shithead project entry point

**Status: proposed foundation. No game engine has been built.** This is a short on-ramp for the SOUL app, Africa, and Claude Code. The SOUL source-code repository is a separate project and must remain untouched.

## Before SOUL studies this project

**Critical:** GitHub's default `main` currently contains only a README. The full foundation is on the **draft** branch `foundation/v0.1-proposed` (PR #1). Do not confuse seeing the repository with having read the foundation.

1. **Africa reviews and accepts PR #1 first**, or explicitly grants SOUL access to that proposed branch for read-only review. Do not merge it for him.
2. On the laptop in **SOUL > Connections > Manage sources**, connect `sirafrica92-a11y/Shithead-` with a *read-only* source grant. The grant must point at the **exact commit** containing the approved docs and include their paths, not stale `main`. Approve model disclosure only when Africa intends it.
3. In **Projects**, press **Study**, wait for the result, and confirm the studied version and included files. A source grant is pinned: later GitHub pushes are invisible until Africa authorises a new pin and SOUL studies again.
4. Use the project's **Projects/Cowork chat** to ask the first read-only assignment below. Chat cannot itself write code, run commands, merge, or deploy.

**If a file is missing from the grant, a study is incomplete, or SOUL has not actually read a source, say so. Never claim "I've studied the rules" based on a repository name.**

## SOUL's first real assignment (read-only)

Ask within the studied project:

> Read FOUNDATION.md, docs/RULES.md, docs/SCENARIO_MATRIX.md, docs/TURN_ENGINE.md and docs/OPEN_DECISIONS.md. Explain the 3/Joker targeting rule for 2, 3, 4, 5 and 6 players, with source citations. Explain why the current counter target is not the next-turn anchor. Identify contradictions and missing rules without inventing solutions. Propose the smallest first implementation task and the tests it needs. Do not write or commit anything.

**Pass:** She correctly distinguishes A targeting B from A targeting a non-next player; does not confuse counter recipient with ordinary turn order; treats the multi-card/counter interaction as unanswered; reports her actual access and evidence.

## When Africa chooses to let SOUL edit

1. **Claude/Git client, when needed:** clone this repository into its own local folder and create/check out a feature branch. SOUL's Repos feature **can push the checked-out branch, including main**; it cannot change branches or open a PR. To avoid accidental main commits, prepare a feature branch before handing her the folder.
2. **SOUL > Work:** Africa authorises that local folder, decides whether its text can be sent to the model, and requests one bounded change. SOUL proposes the exact diff; Africa reviews and approves before any write.
3. **SOUL > Repos:** Africa reviews the resulting full diff, explicitly chooses Commit then Push. Pushing is not publishing a game. A PR and merging require Claude/GitHub/owner review.
4. Claude handles development steps SOUL cannot yet execute: creating the initial environment, running a full pytest/WebSocket suite, servers, dependency installation, deployment and PR operations. Record each gap so SOUL's next capability is based on evidence.

SOUL's **Herself** page is for *SOUL's own code*, not Shithead. Never route this game through that page.

## Source order for the agent

1. `FOUNDATION.md` — project boundaries.
2. `docs/RULES.md` and `docs/SCENARIO_MATRIX.md` — confirmed vs derived behaviour.
3. `docs/TURN_ENGINE.md` and `docs/TEST_PLAN.md` — implementation contract.
4. `docs/OPEN_DECISIONS.md` — unresolved decisions.
5. `docs/source/` — owner provenance. Source text wins over summaries for what Africa actually said.
6. `docs/WORK_PACKETS.md` — next bounded task; `docs/PROJECT_STATUS.md` — progress.

**Remember:** Project study stores a useful knowledge index; it does not retrain SOUL's model or grant new tools. Her source and approvals remain explicitly scoped.
