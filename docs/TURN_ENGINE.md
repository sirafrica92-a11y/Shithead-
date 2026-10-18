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

## Match start (D-019, owner ruling O-01a)

The player holding the **lowest card** starts the game.

- **Ties:** compare the tied players' **second-lowest** cards; if still tied, compare their **third-lowest** cards.
- **Second turn:** compare the **lowest** cards of the players **immediately left and right** of the starter, using the same three-card tie-breaking procedure.
- **Direction of play:** the **winner** of that second comparison plays second, establishing the direction of play for the remainder of the game — `direction` is set so that this player is the next in the turn order after the starter — subject to existing confirmed turn-order mechanics.
- **Residual tie (OPEN):** the owner gave no rule for a tie still standing after the third card comparison. That sub-case stays **unresolved**; no rule may be invented for it. Implementations must treat it as an explicit owner-decision gate, not default to seat order or any other convention.

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

**Important:** A pile attack consumes the pile at acceptance, so subsequent skip cards use empty-pile semantics.

**Resolved by D-014 (owner ruling O-04):** Extra skips declared with an attack remain attached to the original attack through any counter/redirect chain. They do **not** resolve mid-chain, and a counter does not erase them. Once the chain settles, resolve the collector outcome first, then apply the validated skips. Turn advancement remains anchored to the **original actor** (W1). This replaces the earlier note that recorded no owner decision yet existed — one now does.

## Avoiding soft locks

- Deterministic event reducer: `reduce(state, validatedIntent) -> (newState, events)`.
- Snapshot/version required for every response; request IDs are idempotent.
- Reject action outside phase with `reasonCode,message,allowedActions,stateSnapshot` without mutating game.
- Atomic state transition and event append.
- Reconnect returns authoritative snapshot, not client reconstruction.
- If active actor disconnects, enforce an **owner-approved** timeout/auto-choice/forfeit policy; do not silently choose whether to surrender or counter.
- In development, invariants raise immediately. In production, flag corrupted state, stop accepting harmful writes, and offer controlled recovery rather than looping forever.
- Property-based/stateful simulations should establish no actionless states, conservation of cards, predictable active player, and replay determinism. No finite test suite can mathematically guarantee every match finishes under malicious/nonparticipating players.

## Refill timing (D-016, owner ruling O-06)

No player draws replacement cards during the middle of a declared action, group play, attack or counter chain. The entire action/chain resolves first; only then do affected players refill from the stock, drawing only enough to restore the hand to its required size, subject to remaining stock. Cards drawn after resolution cannot retroactively join or continue the action that just ended. This prevents a player drawing into a fresh counter during an unresolved chain.

## Seven-lock (D-013, owner ruling O-03)

Playing a 7 means the NEXT ordinary play must be rank 7 OR LOWER. Another 7 is therefore legal on a 7 and re-imposes the same restriction on the following player. Once a legal non-7 ordinary card is played, the special 7 restriction has been satisfied and normal comparison resumes from that new effective top card. Existing 2/10 overrides remain valid. Never describe this as "lower than 7" — that would incorrectly make another 7 illegal and conflict with the confirmed four-7 clear.

## Ambiguity stops

For points labelled OPEN in `docs/OPEN_DECISIONS.md`, implement interface/stub or a failing pending test only; do not quietly assign conventional Shithead rules.
