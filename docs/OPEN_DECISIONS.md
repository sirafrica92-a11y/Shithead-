# Unresolved rule decisions — do not guess

These items are not a request to re-explain the whole game. The owner already supplied sufficient *generalised turn logic* for 2–6 seats. Ask only when implementing a specific case depends on a missing detail.

## Blocking for complete playable rules engine

1. **Full deal / decks:** cards per player for hand, face-up and face-down; standard 52-card vs multiple decks; Joker count; initial player and direction.
2. **Ordinary comparisons:** Part 1 says higher than top. Is equal rank permitted, and may matching cards be played in one action?
3. **Seven-lock:** compare against 7 or current effective top? Does lock persist until cleared by 2/10 only, or through pick-ups? Is another 7 ordinary play?
4. **Counterattack + multi-card turn:** A declares attack and extra skips; B counters. Which steps remain pending, and who may choose timing/target? Do not treat earlier assistant interpretation as owner approval.
5. **Hand / table endgame:** does a player fully exhaust hand before face-up, then face-down? If a blind card fails, where do collected cards go; when may table play resume?
6. **Finishing:** when is a player out, does game end at first-out or last/loser, and how do attacks or skipped turns interact with already finished seats?
7. **Empty-pile choice:** owner describes a 3/Joker skip when only those cards are playable; whether a player may spend one for a skip while ordinary cards are available is unresolved.
8. **Live versus non-live ownership:** Part One requires exactly one active player at all times, but a zero-player LOBBY and completed FINISHED game have no obvious legal actor. Resolve how nonplaying phases represent this without inventing a turn.

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

Decision process: add a numbered dated owner decision in `docs/DECISION_LOG.md`, reflect it in `docs/RULES.md` and scenario/test fixtures, then change implementation. No silent assumptions. The specific open decision IDs are enumerated in `docs/DECISION_LOG.md`.
