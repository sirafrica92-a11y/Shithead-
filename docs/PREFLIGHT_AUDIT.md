# Preflight audit: 2026-10-19

Development code was reviewed against OWNER_RULES_PART_1/2, RULES, DECISION_LOG,
TURN_ENGINE, TEST_PLAN, W4 protocol, browser UI and suite coverage.

## Confirmed preflight issues repaired in this change
- Browser HTML embedded an out-of-date statement that no game was connected.
- The client only held room/seat credentials in JS variables. Refresh lost the token
  and could prompt users to join another seat. It now retains the current tab's
  credential in sessionStorage and re-authenticates on reload.
- WebSocket rejected-action snapshots were sent but ignored by the browser,
  leaving users stuck with stale version. New client renders authoritative
  stateSnapshot and announces errors; server includes message and allowedActions.
- The client now ignores older-version snapshots, preventing stale UI rollback.
- Browser code moved to /client.js; the server serves that path explicitly.
- Adds HTTP/WebSocket preflight tests for serving, recovery and rejoining.

## Remaining blockers: do NOT call the game release-ready
- D-019 starter/direction algorithm is not implemented; seat 0 clockwise used.
  Unresolved third-card tie needs owner decision; do not guess it.
- Grouped 3/Joker attack + extra skips (D-014) are not in live match orchestration.
- Complete 2–6-player full-match simulations, finished-player chain cases and
  two-human browser playtest are still required.
- Mid-match restart loses in-memory state; persistence, AFK/disconnect rules,
  identity and public-host security hardening remain open.
- No published website, deployed server or supported mobile clients.
- Earlier docs/PROJECT_STATUS.md is stale; the source/working suite take precedence.

This PR is a targeted preflight repair, not an assertion that every outstanding
game rule or multiplayer requirement is implemented. Do not deploy publicly.
