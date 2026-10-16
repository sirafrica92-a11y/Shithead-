# Instructions for SOUL, Claude Code and other coding agents

**Read `SOUL_START_HERE.md` first. This is a proposed foundation, not an order to deploy or merge.**

## Non-negotiable priorities

1. **Africa decides game rules.** Never replace a missing detail with a familiar Shithead variant. Distinguish **CONFIRMED** (owner source), **DERIVED** (extrapolation or implementation rationale) and **OPEN** (requires owner decision).
2. **Specific owner examples outrank generic conflicting text.** Part Two's targeting examples clarify Part One's overly broad "advance from target / every 3 skips" language.
3. **Never let current counter decision ownership rewrite the original turn anchor.** A 3/Joker targets any other seat; only the final recipient accepts. If they were due to play next, they miss that imminent turn; if not, normal turn flow continues. Test all 2–6-seat variants.
4. **Keep Shithead separate from SOUL.** No writes to SOUL code, memory, grants, handovers, credentials or running app.
5. **Use server-authoritative FastAPI + WebSockets** (Part One's final explicit stack instruction). React Native iOS/Android remains the original mobile target. Browser-first prototype is a *proposal*, not a silent platform replacement.
6. **No fabricated execution evidence.** Distinguish static review from actual tests and live validation. Write passing tests for confirmed behaviour, and explicitly pending tests/spec markers for unanswered behaviour. Never force a test green by changing an owner rule.
7. **No unapproved irreversible action.** No automatic merge, main push, deploy, spend, repository visibility change, account access, or sharing of private project data. The owner's review gates apply even when agent tools permit an action.

## Work protocol

- State the scope and a small acceptance plan before making code edits.
- Use `docs/WORK_PACKETS.md` and `docs/TEST_PLAN.md` to pick one bounded deliverable.
- Make a feature branch; leave approved foundation/rules files intact unless proposing an explicit owner-reviewed rule change.
- Record exact changed files, tests **actually run**, their results, any blockers, and remaining open decisions in a dated handover/PR.
- Keep source provenance alongside decisions. If an earlier document conflicts with the owner's original wording, raise it instead of rewriting history.
- Review output for leaked secrets, other players' private cards, duplicate requests and out-of-phase actions.
- If you lack a tool, say what is missing and hand that step to the owner/Claude. **Do not pretend to act via ordinary chat.**

## Practical first slice

Read `docs/WORK_PACKETS.md` packet W0. Do not implement dealing, seven-lock details, the endgame, matchmaking or drinking effects until the owner settles their dependencies.
