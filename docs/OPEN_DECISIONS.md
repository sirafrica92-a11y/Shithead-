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
- Ordinary-play reducer (W3) — implements the above as written: seven-lock per D-013, 10 clearing the pile with an extra turn, 2 resetting the lock and counting toward quads, four-of-a-kind clearing regardless of contributors, refill after the action resolves per D-016, hand/face-up/face-down zones and blind face-down pickup per D-017, finish detection per D-018. Core ordinary play needed no rule beyond these decisions; the residual edge cases it exposed are listed as items 4 to 6 below. See the W3 record in `docs/DECISION_LOG.md`.

## Still open

1. **Live versus non-live ownership (O-10):** Part One requires exactly one active player at all times, but a zero-player LOBBY and a completed FINISHED game have no obvious legal actor. Resolve how non-playing phases represent this without inventing a turn.
2. **AFK / disconnect / timeout (O-09):** multiplayer recovery. A pure reducer has no wall clock, so timeouts must be an outer (server) concern.
3. **Residual starting-procedure tie (D-019 sub-case):** if players remain tied after comparing lowest, second-lowest and third-lowest cards, the owner has not ruled how the start is settled. Do not guess.
4. **Seven-lock scope edges (raised by W3):** D-013 fixes the exact comparison and the lock's duration, and the reducer resets the lock on a 2. The owner has not ruled on: (a) whether a group play of several 7s creates a single lock or a stacked lock; (b) whether a pile clear (10 or four-of-a-kind) while a lock is active also clears the lock, or the lock survives onto the empty pile; (c) what happens to a pending lock if the locked player finishes before taking the locked turn. Whatever the reducer currently does here is provisional, not a ruling.
5. **Blind face-down edges (raised by W3):** D-017 resolves the basic face-down failure (the player picks up the pile). Still unruled: (a) whether a blind-revealed 2, 7 or 10 exerts its special effect as normal; (b) how a blind reveal interacts with an active seven-lock — whether the revealed card must satisfy the lock and exactly what is picked up on failure; (c) whether blind play on an empty pile is simply always legal. Provisional reducer behaviour, not a ruling.
6. **Finish / endgame edges (raised by W3):** D-018 covers finishing, win-loss and finished seats. Still unruled: (a) whether a player who finishes by playing a 10 is out immediately with the extra turn lapsing; (b) whether finishing while a seven-lock is pending on the finisher or on the finisher's target dissolves or transfers the lock; (c) the ordering of finish detection against refill when the draw deck is already exhausted. Provisional reducer behaviour, not a ruling.

W3 did not close items 1 to 3; they are outside the ordinary-play reducer's scope. W3's tests (`server/tests/test_ordinary.py`, extended `server/tests/test_w1_w2_composition.py`) were written but could not be executed in the authoring sandbox (RUN guard refusal); run `python -m pytest -q` in `server/` and confirm a green run before relying on the reducer behaviour behind items 4 to 6.

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
