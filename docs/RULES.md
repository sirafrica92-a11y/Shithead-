# Game rules — owner-grounded working specification

**Status:** v0.1 PROPOSED; distinct between **CONFIRMED**, **DERIVED**, and **OPEN**.  
**Precedence:** Owner's detailed scenarios (Part 2) override broad, conflicting turn formulations in Part 1. An interpretation is not an approved rule.

## Goal and players

- **CONFIRMED:** Shithead is intended for 2–6 players; "Shit Face" is an optional drinking-mode presentation overlay, never a change to gameplay.
- **CONFIRMED (D-018):** A player is finished/out when no cards remain in hand, face-up or face-down after their final play fully resolves. Finished players are permanently removed from turn rotation. Play continues until only one eligible player remains; that final player is the loser ("shithead"). The match does **not** end when the first player finishes.
- **CONFIRMED (D-011):** Every player is dealt 3 face-down, 3 face-up and 3 cards in hand. 2–4 players: one standard 52-card deck plus 2 Jokers. 5–6 players: two standard 52-card decks plus 4 Jokers.
- **CONFIRMED (D-019):** The player holding the lowest card starts the game. Ties are broken by comparing the tied players' second-lowest cards, then their third-lowest cards if still tied. For the second turn, the lowest cards of the players immediately left and right of the starter are compared with the same three-card tie-breaking procedure; the winner plays second, establishing the direction of play for the remainder of the game (the direction is set so that this player is next in the turn order after the starter), subject to existing confirmed turn-order mechanics.
- **OPEN (D-019 sub-case):** The owner gave no rule for a tie that remains after the third card comparison; that sub-case stays unresolved and must not be guessed. Also open: direction changes during play beyond the initial establishment (none are assumed).

## Ordinary play

- **CONFIRMED (D-012):** On a normal pile, play a card **higher-or-equal** to the current effective top rank, unless a power-card rule overrides it. Normal rank order is 3,4,5,6,7,8,9,10,J,Q,K,A with Ace high.
- **CONFIRMED (D-012):** Multiple cards of the same rank may be played together as one action.
- **CONFIRMED:** If a player has no valid play, they pick up the playing pile, and their turn ends immediately.
- **CONFIRMED (D-023, 24 Oct 2026):** A player may also **choose** to collect a nonempty playing pile even when holding a legal ordinary or power card. This is tactical and ends that player's turn; playable cards need not be revealed or spent. This applies to hand and face-up play. It does **not** permit a player in the blind face-down stage to bypass flipping, collect an empty pile, or avoid resolving a pending 3/Joker attack or blind power. All existing turn and seven-lock outcomes remain unchanged.
- **CONFIRMED (D-016, amended narrowly by D-024 and D-025):** No player draws replacement cards in the middle of a declared ordinary action or grouped power play. **D-025 exception:** after each complete 3/Joker attack or counter action, that player immediately replenishes their hand towards three while stock remains, even if the larger counter battle is still active. Newly drawn powers may be used if that player is targeted again. Draws never join the action just committed. Resolve the entire action first; then replenish the hand towards three cards while stock remains. Normally the next scheduled player acts. **D-024 exception for ordinary hand plays only:** if replenishment draws a card of the exact rank just played and the pile remains in play, the original player may play one or more of **those newly drawn matching cards** immediately or keep them and end the opportunity. Only the cards drawn after the particular play qualify, plus any still-unplayed eligible draw from that same optional sequence. Already held cards and face-up cards absorbed on stock exhaustion do not qualify. The choice is private, does not change the scheduled next-player anchor, and is not offered during 3/Joker chains or after a clear (which already gives an extra turn).
- **CONFIRMED:** Four consecutive cards of identical rank clear the pile; the player who completes the four plays again.
- **OPEN:** How rank runs are counted around special cards.

## Power cards

### 3 and Joker: same attack and defence

- **CONFIRMED:** A played 3 or Joker is **removed from the game**, never left in the playing pile. These cards have the same powers.
- **CONFIRMED:** If a playing pile exists, the acting player selects **any other player** to receive that pile.
- **CONFIRMED:** The target has a real choice: **accept** the pile, even if holding a 3/Joker, or **counter** using a 3/Joker, remove that counter from the game, and select any other player as the new target. The chain may redirect back to a previous attacker, and continues until acceptance.
- **CONFIRMED:** A target who accepts collects the entire playing pile. If they were the **next scheduled player** after the original actor, they lose that immediate turn; the following player plays. If they were not next, the next scheduled player plays normally and the target does not automatically lose a later turn.
- **CONFIRMED:** When the playing pile is **empty**, a 3/Joker instead skips the next scheduled player's turn. Another 3/Joker may skip another player; after all opponents have been skipped, the actor plays again.
- **CONFIRMED (D-015):** On an empty pile a player **may elect** to spend a 3/Joker for its skip effect even while holding a playable ordinary card. This is optional, not mandatory. The spent card follows the confirmed removal-from-game rule.
- **CONFIRMED:** An actor can play multiple 3s/Jokers as a tactical combined action: with a pile, one card can send the pile to a target while additional cards skip successive players; without a pile, cards skip successive players.
- **CONFIRMED (D-014):** Extra skips declared with an attack remain attached to the original attack through any counter/redirect chain. They do **not** resolve mid-chain, and a counter does not erase them. Once the chain settles, resolve the collector outcome first, then apply the validated skips. Turn advancement remains anchored to the **original actor** (W1).
- **DERIVED:** Track the **original turn anchor** separately from the **current counter-decider**. Merely choosing a non-next target does not jump the normal turn sequence.

### 10: clear

- **CONFIRMED:** May be used as a power card; clears the pile immediately, resets all constraints (including seven-lock) and the **same actor plays again**. This explicitly overrides ordinary turn advancement.
- **OPEN:** If a 10 happens among simultaneously played cards, resolve grouping rules before implementing.

### 7: lower-or-equal lock

- **CONFIRMED (D-013):** Playing a 7 means the NEXT ordinary play must be rank **7 or lower**. Another 7 is legal on a 7 and re-imposes the same restriction on the following player. Once a legal non-7 ordinary card is played, the restriction is satisfied and normal comparison resumes from that new effective top card. Existing 2/10 overrides remain valid. Never described as "lower than 7", which would wrongly forbid a 7 on a 7 and break the four-7 clear.
- **CONFIRMED:** Four sevens in sequence clear the pile and grant the same player another play.
- **DERIVED:** The 10 explicitly cancels the lock. The 2 resets constraints as described below.
- **CONFIRMED (D-021):** A 3 or Joker may always be played; an active seven-lock never prevents it.

### 2: free pass

- **CONFIRMED:** Can be played on anything and resets constraints; the next player may play any card.
- **OPEN:** What exactly serves as the new effective top rank after that free play, and how the four-of-kind streak treats a 2.

## Endgame

- **CONFIRMED (D-017, amended by D-022):** Ordered transition **hand → face-up → face-down**. A player cannot voluntarily use face-down cards while any face-up remain.
- **CONFIRMED (D-022):** Once the stock is empty AND the player holds fewer than three cards in hand, all three face-up cards are taken into hand **automatically**, as a free action that does not consume a turn. Holding two cards therefore gives five in hand. The stock never refills, so from that point the trigger is effectively “hand below three” and may fire more than once in a match. This supersedes the earlier D-017 wording that face-up cards could not be used while any hand cards remained.
- **CONFIRMED (D-017):** Face-down cards are played blindly one at a time. If a blind face-down card cannot legally remain in play, the player collects the pile into their **hand** and resumes normal hand play until empty again before returning to the remaining table cards. There is no free choice between hand and table zones.
- **CONFIRMED (D-020):** A face-down card may only be flipped while the hand is empty, and the pickup on a failed flip takes the pile **and the revealed card** into hand. A blind-revealed power card exerts its normal power; nothing about power behaviour changes on a blind flip.
- **CONFIRMED:** Power cards remain effective in the endgame; a failed face-down card causes a pile pickup and turn end.
- **OPEN:** Whether opponents must know exposed face-up powers; clearing once the table is exhausted.

## Shit Face overlay

- **CONFIRMED:** Optional drinking mode must not affect phase, moves, card legality, score or turn ordering. Only show cosmetic consequences.
- **OPEN:** Specific drink prompts, local age-appropriate controls, regional restrictions, accessibility substitutes.

## Recovery

- **CONFIRMED:** Invalid requests return `{reasonCode, message, allowedActions, stateSnapshot}`, do not consume an action, and never lock the UI.
- **ENGINE REQUIREMENT:** Every accepted action explicitly identifies current actor, turn anchor, current phase, legal next actions and transition; no blind "index + 1" after target changes.
- **LIMIT:** An engineering goal to avoid deadlocks does not prove that every real match terminates: disconnected/AFK players and deliberately unending strategies require timeout/reconnect/forfeit policies, currently **OPEN**.
