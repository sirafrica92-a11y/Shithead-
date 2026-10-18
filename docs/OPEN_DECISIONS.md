# Unresolved rule decisions — do not guess

The owner has ruled on the core rules engine (O-01 to O-08 -> D-011 to D-018, and O-01a -> D-019 in `docs/DECISION_LOG.md`). What genuinely remains open is below.

## Resolved (recorded in DECISION_LOG.md)

- Deal / decks / Jokers — D-011.
- Starting player, second player and direction of play (O-01a) — D-019. Only the residual sub-case of a tie still standing after the third card comparison is unresolved; the owner did not give a rule for it and none may be invented.
- Ordinary comparisons, equal rank, group plays, rank order — D-012.
- Seven-lock exact comparison and duration — D-013.
- Counterattack + multi-card turn / skip ordering — D-014.
- Elective empty-pile skip — D-015.
- Refill timing — D-016.
- Endgame transition and face-down failure — D-017.
- Finishing / win-loss / finished seats — D-018.

## Still open

1. **Live versus non-live ownership (O-10):** Part One requires exactly one active player at all times, but a zero-player LOBBY and a completed FINISHED game have no obvious legal actor. Resolve how non-playing phases represent this without inventing a turn.
2. **AFK / disconnect / timeout (O-09):** multiplayer recovery. A pure reducer has no wall clock, so timeouts must be an outer (server) concern.
3. **Residual starting-procedure tie (D-019 sub-case):** if players remain tied after comparing lowest, second-lowest and third-lowest cards, the owner has not ruled how the start is settled. Do not guess.

## Deployment / product choices (not blockers for pure engine)

- Login as guest vs account, rooms/invites, matchmaking, chat, moderation and abuse handling.
- Web-first vs React Native-first playable prototype.
- Hosting architecture/budget, whether/when to attach a .tech domain.
- Drinking overlay settings, regional gating and nonalcoholic equivalent.
- Game art, UI design, localisation, sound, leaderboards and monetisation.

## Internal consistency notes

- Part 1 says "each resolved 3 skips exactly one player" and "advance from target"; Part 2 specifies **target dependent** turn loss and preserves the initiating player's normal turn sequence. The more specific later explanation governs, and the earlier wording must not be reintroduced verbatim as reducer logic.
- In the owner's 4-player explanation, one phrase mentions targeting "C or D" while the worked result says "D picks up". Treat it as illustrative ambiguity, **not** permission to change target after declaring it.
- Earlier assistance extrapolated five- and six-player cases from four seats. Those cases are **derived examples** for owner review, not additional separately authenticated owner instructions.

Decision process: add a numbered dated owner decision in `docs/DECISION_LOG.md`, reflect it in `docs/RULES.md` and scenario/test fixtures, then change implementation. No silent assumptions.
