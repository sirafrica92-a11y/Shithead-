# Turn engine — deterministic state-machine contract

**Status:** design for review, **not** an executable implementation.

## Authority and state

Server is the sole rule arbiter. Clients submit intention plus match version / unique request ID and render authoritative snapshots.

```text
GamePhase = LOBBY | PLAYING | PILE_PASS_DECISION | FINISHED

MatchState:
  phase
  players[]                 # stable seating, eligibility/finished markers
  direction                 # initially clockwise; rule changes not assumed
  activePlayerId            # exactly one in a live, non-lobby, nonterminal state
  turnAnchorPlayerId        # player whose play initiated the current effect
  scheduledNextPlayerId     # normal first next player after anchor (before skips)
  pile[]                    # played, not removed-from-game cards
  removedFromGame[]         # used 3s/Jokers etc.
  hands{}; faceUp{}; faceDown{}; drawPile[]
  activeSevenConstraint     # explicit, may be null
  consecutiveRankCounter
  pendingPass:
    sourcePlayerId          # original actor
    currentTargetId
    affectedPileSnapshot
    playedAttackCardIds[]
    pendingSkipCardIds[]    # only if multi-play predeclaration approved
    visitedCounterHops[]    # audit history, not a ban on repeat targets
  turnVersion
  actionHistory[]
```

The **counter recipient owns the current decision**, but **does not become the base of ordinary clockwise advancement**. This corrects an overly broad Part 1 instruction to advance from the target.

## Phase transitions

| Current phase | Intent | Next state |
| --- | --- | --- |
| LOBBY | join, leave, configure, ready/start (validated) | LOBBY or PLAYING |
| PLAYING | play valid ordinary card(s) | PLAYING; next eligible player, unless extra-turn effect |
| PLAYING | play 10 / fourth same rank | PLAYING; same actor, reset relevant pile constraints |
| PLAYING | play 2 | PLAYING; next eligible player gets unrestricted first play |
| PLAYING | play 7 | PLAYING; locked constraint passed to next actor |
| PLAYING | play 3/Joker on nonempty pile | PILE_PASS_DECISION; targeted player owns decision |
| PLAYING | play 3/Joker on empty pile | PLAYING; next seat skipped, resolve remaining declared skips |
| PLAYING | forced pickup | PLAYING; next eligible actor, relative to actor |
| PILE_PASS_DECISION | acceptPile | PLAYING; apply owner's target-versus-next-player condition and any authorised skip budget |
| PILE_PASS_DECISION | counterWithThree (3 or Joker) | PILE_PASS_DECISION; new target owns decision |
| any live | validated finish condition | FINISHED |
| any | illegal or stale action | same state; recoverable response and current snapshot |

**Required invariants:** exactly one action owner while PLAYING/PASS (nonterminal); a decision belongs only to target; no client-assumed turn math; unique card location; no duplicate or replayed event; "discarded" vs "removed" tracked separately; each transition has next legal action(s) or an explicit policy.

## Owner's counterexamples to naive turn advancement

Seating is A → B → C → ... → A. A originally plays a 3/Joker while a pile exists.

- **3 seats:** A targets **B**, B accepts → **C acts next**. A targets **C**, C accepts → **B acts next**.
- **4 seats:** A targets **B**, B accepts → **C acts next**. A targets **D**, D accepts → **B acts next**.
- **6 seats (derived by scaling 4-seat logic):** A targets **F**, F accepts → **B acts next**. A targets **B**, B accepts → **C acts next**.
- **Counters:** A targets E; E counters C; C counters B; B accepts → scheduled B is bypassed, so **C acts next**, despite intervening temporary decision owners.

## Multi-3/Joker sequencing

The owner allows consecutive skips in one turn, including:

- 4 seats: A targets B, B accepts, then two further skip cards remove C and D's turns → A plays again.
- 4 seats: A targets D, D accepts, then two further skip cards skip B and C → D plays next.
- 5 seats (derived): A targets B plus 3 skips (C,D,E) → A again.
- 6 seats (derived): A targets F plus 4 skips (B,C,D,E) → F next.

**Important:** A pile attack consumes the pile at acceptance, so subsequent skip cards use empty-pile semantics. They must be resolved only according to an explicit approved atomic/batched-action policy, **not assumed automatically during a counter chain**. A reply in the earlier discussion suggested "counter first then skips"; that is a *proposal*, not a confirmed owner decision.

## Avoiding soft locks

- Deterministic event reducer: `reduce(state, validatedIntent) -> (newState, events)`.
- Snapshot/version required for every response; request IDs are idempotent.
- Reject action outside phase with `reasonCode,message,allowedActions,stateSnapshot` without mutating game.
- Atomic state transition and event append.
- Reconnect returns authoritative snapshot, not client reconstruction.
- If active actor disconnects, enforce an **owner-approved** timeout/auto-choice/forfeit policy; do not silently choose whether to surrender or counter.
- In development, invariants raise immediately. In production, flag corrupted state, stop accepting harmful writes, and offer controlled recovery rather than looping forever.
- Property-based/stateful simulations should establish no actionless states, conservation of cards, predictable active player, and replay determinism. No finite test suite can mathematically guarantee every match finishes under malicious/nonparticipating players.

## Ambiguity stops

For points labelled OPEN in `docs/OPEN_DECISIONS.md`, implement interface/stub or a failing pending test only; do not quietly assign conventional Shithead rules.
