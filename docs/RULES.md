# Game rules — owner-grounded working specification

**Status:** v0.1 PROPOSED; distinct between **CONFIRMED**, **DERIVED**, and **OPEN**.  
**Precedence:** Owner's detailed scenarios (Part 2) override broad, conflicting turn formulations in Part 1. An interpretation is not an approved rule.

## Goal and players

- **CONFIRMED:** Shithead is intended for 2–6 players; "Shit Face" is an optional drinking-mode presentation overlay, never a change to gameplay.
- **OPEN:** Exact win/loss scoring and loser naming, deck composition and number of Jokers, starting player, direction changes (if any), initial deal and hand/face-up/face-down configuration, legal choice and tie rules.

## Ordinary play

- **CONFIRMED:** On a normal pile, play a card **higher** than the effective top rank; power cards may ignore the rank restriction as specified below.
- **CONFIRMED:** If a player has no valid play, they pick up the playing pile, and their turn ends immediately.
- **CONFIRMED:** While the draw stack has cards, a player automatically draws back up toward **three cards in hand** after plays, if possible.
- **CONFIRMED:** Four consecutive cards of identical rank clear the pile; the player who completes the four plays again.
- **OPEN:** Whether equal ranks are normally permitted (the owner's Part 1 says *higher*, not *equal*), whether multiple identical cards may be played together, how rank runs are counted around special cards, and how draws interact with a 3/Joker attack and skips.

## Power cards

### 3 and Joker: same attack and defence

- **CONFIRMED:** A played 3 or Joker is **removed from the game**, never left in the playing pile. These cards have the same powers.
- **CONFIRMED:** If a playing pile exists, the acting player selects **any other player** to receive that pile.
- **CONFIRMED:** The target has a real choice: **accept** the pile, even if holding a 3/Joker, or **counter** using a 3/Joker, remove that counter from the game, and select any other player as the new target. The chain may redirect back to a previous attacker, and continues until acceptance.
- **CONFIRMED:** A target who accepts collects the entire playing pile. If they were the **next scheduled player** after the original actor, they lose that immediate turn; the following player plays. If they were not next, the next scheduled player plays normally and the target does not automatically lose a later turn.
- **CONFIRMED:** When the playing pile is **empty**, a 3/Joker instead skips the next scheduled player's turn. Another 3/Joker may skip another player; after all opponents have been skipped, the actor plays again.
- **CONFIRMED:** An actor can play multiple 3s/Jokers as a tactical combined action: with a pile, one card can send the pile to a target while additional cards skip successive players; without a pile, cards skip successive players.
- **OPEN:** Exact transaction structure of a multi-card declaration while a counter chain is unresolved; whether held face-up/face-down counters have different constraints; whether special-card draw replenishment happens between declarations and counter steps.
- **DERIVED:** Track the **original turn anchor** separately from the **current counter-decider**. Merely choosing a non-next target does not jump the normal turn sequence.

### 10: clear

- **CONFIRMED:** May be used as a power card; clears the pile immediately, resets all constraints (including seven-lock) and the **same actor plays again**. This explicitly overrides ordinary turn advancement.
- **OPEN:** If a 10 happens among simultaneously played cards, resolve grouping rules before implementing.

### 7: lower-than lock

- **CONFIRMED:** Can be played on any ordinary pile. It creates a constraint that the next play must be **lower** than the seven-related bound, or a power card; four sevens in sequence clear the pile and grant the same player another play.
- **OPEN:** Precise seven-lock comparison bound after a subsequent card (and whether a standard 7 can itself be played during an active lock), persistence through 2 and pickup, and interactions with face-down failure.
- **DERIVED:** The 10 explicitly cancels the lock. The 2 resets constraints as described below.

### 2: free pass

- **CONFIRMED:** Can be played on anything and resets constraints; the next player may play any card.
- **OPEN:** What exactly serves as the new effective top rank after that free play, and how the four-of-kind streak treats a 2.

## Endgame

- **CONFIRMED:** The owner specified that once the draw stack is empty players must move through face-up cards and then face-down cards **one at a time**, and a failed face-down card causes a pile pickup and turn end. Power cards remain effective.
- **DERIVED/COMMON BUT NOT AUTHORISED:** Many Shithead variants require exhausting the hand before face-up cards; this is not stated unambiguously in the source and must be approved before implementation.
- **OPEN:** Full hand → face-up transition, blindly drawn face-down mechanics, returning picked-up cards to hand, whether opponents must know exposed face-up powers, clearing once the table is exhausted, finishing/last-player rules.

## Shit Face overlay

- **CONFIRMED:** Optional drinking mode must not affect phase, moves, card legality, score or turn ordering. Only show cosmetic consequences.
- **OPEN:** Specific drink prompts, local age-appropriate controls, regional restrictions, accessibility substitutes.

## Recovery

- **CONFIRMED:** Invalid requests return `{reasonCode, message, allowedActions, stateSnapshot}`, do not consume an action, and never lock the UI.
- **ENGINE REQUIREMENT:** Every accepted action explicitly identifies current actor, turn anchor, current phase, legal next actions and transition; no blind "index + 1" after target changes.
- **LIMIT:** An engineering goal to avoid deadlocks does not prove that every real match terminates: disconnected/AFK players and deliberately unending strategies require timeout/reconnect/forfeit policies, currently **OPEN**.
