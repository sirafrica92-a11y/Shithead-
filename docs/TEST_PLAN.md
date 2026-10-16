# Acceptance tests and quality bar

**Status:** specification, not passing tests. Never describe these as built or verified.

## Every test must assert

Current `GamePhase`, `activePlayerId`, `turnAnchorPlayerId`, scheduled next actor, affected hands/pile/removed-from-game cards, rank-lock state, version and allowed actions. Verify no hidden information leaks in per-player snapshots.

## Known fixtures / expected outcomes

See `docs/SCENARIO_MATRIX.md` for explicit 2–6-seat input/output rows and which are directly owner-supplied versus extrapolated. **Derived rows are proposed acceptance cases, not owner-approved additions to the rulebook.**

| ID | Setup and action | Expected |
| --- | --- | --- |
| AT-01 | 2 seats A,B; A attacks B with nonempty pile, B accepts | B receives pile; A plays next (B's next turn lost) |
| AT-02 | 2 seats A,B; A attacks B, B counters A, A counters B, B accepts | Each played 3/Joker removed; one pile pickup; next is A |
| AT-03 | 2 seats; empty pile, A spends one 3/Joker | B skipped; A next |
| AT-04 | 3 seats A,B,C; A attacks B; B accepts | B receives pile; C next |
| AT-05 | 3 seats A,B,C; A attacks C; C accepts | C receives pile; B next |
| AT-06 | 3 seats; empty pile, A uses one skip | C next |
| AT-07 | 4 seats A,B,C,D; A attacks D; D accepts | D receives pile; B next |
| AT-08 | 4 seats; empty pile, A uses three skips | B,C,D skipped; A again |
| AT-09 | 3 seats; A attacks C; C counters B; B accepts | B receives pile; C next (counter did not shift anchor) |
| AT-10 | 5 seats A..E; A attacks E; E accepts | B next |
| AT-11 | 6 seats A..F; A attacks B; B accepts | C next |
| AT-12 | A plays valid 10 | pile empty, seven-lock cleared, A again |
| AT-13 | Four consecutive same rank completed by X | pile clear, X again |
| AT-14 | During seven-lock, power card is played | accepted subject to card-specific effect |
| AT-15 | 2 resets constraints | next player free to play any valid ordinary card |
| AT-16 | No legal play; actor picks up | actor's turn ends; next valid player |
| AT-17 | 3/Joker pile-pass phase: wrong actor plays or tries ordinary card | rejected with structured response and unchanged state |
| AT-18 | User retries accepted `requestId`, stale `expectedVersion` or disconnect/reconnect | no duplicate effect, authoritative resync |
| AT-19 | Draw-stack refill toward 3 | conservation of card identities and hand count |
| AT-20 | 10 / skip / pile pickup while one or more seats already finished | only eligible seats participate; exact finish semantics pending |
| AT-21 | Failed blind face-down card | player collects pile and turn ends, subject to confirmed face-down policy |
| AT-22 | Normal vs Shit Face overlay on same action stream | **identical** engine state and outcomes |
| AT-23 | Crafted action or client snapshot tries to reveal opponent's hand | no hidden card exposure |
| AT-24 | 6-seat randomly generated legal action traces | invariants always hold; no actionless nonterminal state |

## Pending-owner tests (must not be marked passed by default)

- Whether an empty-pile 3/Joker skip is permitted when other cards are playable (the owner described only a rare all-3/Joker case).
- Lobby and finished-phase active-player nullability; only PLAYING and PILE_PASS_DECISION require exactly one action owner.

- Multi-card 3/Joker declaration with a counter mid-sequence.
- Whether successive skips run *after* chain resolution, if that is the owner's chosen rule.
- Exact seven-lock value comparison and persistence.
- Ordinary equal-rank card legality and group play.
- Deal, Joker count and blind face-down use.
- AFK, disconnect, timeout, surrender and finish rules.

## Test depth

1. Unit tests on pure reducer and resolver.
2. Property-based tests: card conservation, at-most-one location/card, allowed phase transitions, never zero/multiple active players (except lobby/finished), deterministic replay.
3. Protocol tests: authentication, seat binding, stale and duplicate requests, secret-safe reject snapshots.
4. WebSocket tests: two connections compete for same turn, disconnect during pile pass, refresh/rejoin.
5. Persistence tests: restart mid-counter and resume without a second attack.
6. Real device/network smoke testing before a public release.

## Exit gates

**Gate A:** rulebook approved for subset; reducer passes focused and stateful tests.

**Gate B:** two humans can finish a full game in browser on separate devices; counter chain and reconnection verified.

**Gate C:** 2–6 real players, matchmaking/rooms, security, endgame, reconnection and crash recovery checked.

**Gate D:** release hardening, monitoring, mobile clients, licensing, privacy and user acceptance.

"No freeze" is an engineering target subject to measured evidence, not a claim to make before it has been tested.
