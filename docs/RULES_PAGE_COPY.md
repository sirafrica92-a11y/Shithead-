# In-app "How to Play" page — approved copy and contradiction report

**Status:** DRAFT COPY FOR OWNER APPROVAL. Nothing here is a new rule.
**Date:** 19 October 2026.
**Sources of truth:** `docs/RULES.md`, `docs/source/OWNER_RULES_PART_1.md`, `docs/source/OWNER_RULES_PART_2.md`, `docs/DECISION_LOG.md`, `docs/OPEN_DECISIONS.md`.

Every sentence of the page copy in Part 1 below traces to a CONFIRMED line in those documents. Where a point is recorded as OPEN, the copy is silent on it and the omission is listed in Part 3. The owner's draft design text was used for structure, tone and the power-card headline names only — not as a rules source.

British English. Short sentences. Written for a phone screen.

---

## 1. Final page copy

### Screen 1 — How to Play

#### Objective

<!-- Source: docs/RULES.md:9 (D-018); docs/DECISION_LOG.md:24 -->

Be rid of your cards. All of them: your hand, your three face-up cards and your three face-down cards.

Finishing does not end the match. Play carries on until one player is left holding cards. That player is the Shithead.

#### Setting up

<!-- Source: docs/RULES.md:8, 10, 11 (D-011, D-019); docs/DECISION_LOG.md:17, 25 -->

Two to six players.

You are dealt three cards face down, three cards face up on top of them, and three cards in your hand.

Whoever holds the lowest card starts.

#### Turn Rules

<!-- Source: docs/RULES.md:16, 18, 19, 20 (D-012, D-016); docs/DECISION_LOG.md:18, 22 -->

On your turn, play a card of equal or higher rank than the top of the pile.

Rank order is 3, 4, 5, 6, 7, 8, 9, 10, J, Q, K, A. Ace is highest.

You may play several cards of the same rank together as one move.

If you have no legal play, pick up the whole pile. Your turn ends there.

Four cards of the same rank in a row clear the pile. Whoever lays the fourth card plays again.

#### Keeping three in hand

<!-- Source: docs/RULES.md:19 (D-016); docs/DECISION_LOG.md:22 -->

Once your move has fully resolved, draw from the stock to bring your hand back up to three cards.

You never draw in the middle of a move, an attack or a counter chain. Cards drawn afterwards cannot join the move that just ended.

When the stock runs out, there is nothing to draw.

### Screen 2 — Power Cards

<!-- Source: docs/RULES.md:25-51; docs/source/OWNER_RULES_PART_1.md:14, 17, 18, 19, 20; docs/source/OWNER_RULES_PART_2.md:5-34; docs/DECISION_LOG.md:7, 11, 19, 20, 21 -->

#### Three and Joker — The Hand-Off

A Three and a Joker do exactly the same thing. Either one is removed from the game once played. It never sits in the pile.

If there is a pile, send the whole pile to any other player.

That player chooses. They may accept the pile, even if they hold a Three or a Joker. Or they may counter with a Three or a Joker, which is also removed from the game, and send the pile on to any other player — including back to you.

The chain continues until someone accepts.

If the player who accepts was the next player anyway, they lose that turn and play passes on. If they were not next, the normal next player takes their turn as usual.

If the pile is empty, a Three or a Joker skips the next player instead. Play another and you skip the player after that. Once every opponent has been skipped, you play again. You may choose to spend a Three or a Joker this way even when you hold a card you could legally play.

You may combine them in one move: send the pile to one player, and skip others with the rest.

#### Ten — Clear

<!-- Source: docs/RULES.md:39 (D-005); docs/DECISION_LOG.md:11 -->

Clears the pile at once and lifts any Seven lock. You play again immediately.

#### Seven — Lock

<!-- Source: docs/RULES.md:44, 45 (D-013); docs/DECISION_LOG.md:19 -->

A Seven can be played on any card.

After a Seven, the next ordinary play must be rank **seven or lower**.

A Seven on a Seven is legal, and locks the next player again. Four Sevens in a row clear the pile, and that player plays again.

A Two or a Ten still overrides the lock.

Once a legal card other than a Seven is played, the lock is satisfied and normal comparison resumes from that card.

#### Two — Free Pass

<!-- Source: docs/RULES.md:50 (D-005); docs/DECISION_LOG.md:11 -->

A Two can be played on any card. It resets the restrictions. The next player may play whatever they like.

### Screen 3 — Endgame

#### Your face-up cards

<!-- Source: docs/RULES.md:55 (D-017); docs/DECISION_LOG.md:23 -->

When your hand is empty, you play from your three face-up cards. You choose which one each turn.

You cannot touch your face-up cards while you still hold cards in hand.

#### Your face-down cards

<!-- Source: docs/RULES.md:56, 57 (D-017); docs/DECISION_LOG.md:23 -->

When your face-up cards are gone, you play your face-down cards blind, one at a time.

If the card you turn over cannot legally stay in play, you take the pile into your hand. You then play out your hand as normal, and only return to your table cards once your hand is empty again.

#### Finishing

<!-- Source: docs/RULES.md:9 (D-018); docs/DECISION_LOG.md:24 -->

You are out when nothing remains in your hand, face up or face down. Out players are skipped from then on. The last player still holding cards is the Shithead.

### Shit Face mode (optional)

<!-- Source: docs/RULES.md:62 (D-009); docs/DECISION_LOG.md:16 -->

Shit Face is an optional drinking-mode presentation only. It never changes the cards, the turn order or what is legal.

---

## 2. Contradiction table

Row by row: the owner's draft design text, what the canonical documents say, and the wording used in Part 1 above.

| # | Draft design text | Canonical rule (`file:line`) | Corrected wording |
| --- | --- | --- | --- |
| 1 | "On your turn, play a card higher than the previous card." | Ordinary legality is **higher-or-equal** to the current effective top card. `docs/RULES.md:16`; `docs/DECISION_LOG.md:18` (D-012) | "Play a card of equal or higher rank than the top of the pile." |
| 2 | "Cards must be played in asceeding order." (ascending) | Same as #1 — equal ranks are legal, so play is non-decreasing, not ascending. Equal-rank group plays are explicitly legal. `docs/RULES.md:16`; `docs/DECISION_LOG.md:18` | Dropped the "ascending order" framing entirely. Replaced with the equal-or-higher rule plus "You may play several cards of the same rank together as one move." |
| 3 | "Power cards ignore normal order rules." | Only partly true. Part One's "power cards ignore rank" is a broad formulation (`docs/source/OWNER_RULES_PART_1.md:11`), and `docs/RULES.md:4` gives precedence to the specific rules over broad Part One wording. A **7** does not ignore order — it imposes one (`docs/RULES.md:44`). A **2** and a **10** override restrictions (`docs/RULES.md:39, 50`). A 3/Joker's interaction with an active Seven lock is **not ruled** (`docs/OPEN_DECISIONS.md:23`). | Removed the blanket claim. Each power card's own behaviour is stated separately, and nothing is claimed about a 3/Joker against an active lock. |
| 4 | "Power cards can be played at any time, even on other power cards." | No document supports play out of turn. A 7 and a 2 "may be played on anything" (`docs/source/OWNER_RULES_PART_1.md:17, 18`; `docs/RULES.md:44, 50`); an empty-pile 3/Joker spend is elective (`docs/RULES.md:32`, D-015). "At any time" is an overstatement with no source. | Removed. The per-card statements say "can be played on any card" only where the documents say so (7 and 2). |
| 5 | "Maintain Three Cards: As long as there are cards in the draw pile, you must always have a[t least] 3 cards in [hand]" | Refill happens **only after the whole action or chain resolves**, and only draws back **up to** three — never mid-action, and holding more than three is possible. `docs/RULES.md:19`; `docs/DECISION_LOG.md:22` (D-016) | "Once your move has fully resolved, draw from the stock to bring your hand back up to three cards. You never draw in the middle of a move, an attack or a counter chain." |
| 6 | Hand-Off: "Pass the entire pile to any player you choose." | The target must be **any other** player — not yourself. `docs/RULES.md:28`; `docs/source/OWNER_RULES_PART_2.md:8` | "send the whole pile to any other player." |
| 7 | Hand-Off: "If that player has a Three, they can send it back or pass it to someone else." | A Joker has identical powers and can also counter. `docs/RULES.md:27`; `docs/DECISION_LOG.md:7` (D-001); `docs/source/OWNER_RULES_PART_2.md:5-9` | "counter with a Three or a Joker". |
| 8 | Hand-Off: "This can chain until someone gne gets stuck." | The chain ends when a target **accepts**, and accepting is a free choice — a target may accept deliberately while holding a counter. Nobody has to be "stuck". `docs/RULES.md:29`; `docs/source/OWNER_RULES_PART_2.md:10` | "They may accept the pile, even if they hold a Three or a Joker… The chain continues until someone accepts." |
| 9 | Hand-Off: omits that a played 3/Joker leaves the game | A played 3 or Joker is **removed from the game**, never left in the pile. `docs/RULES.md:27`; `docs/source/OWNER_RULES_PART_2.md:9` | Added: "Either one is removed from the game once played. It never sits in the pile." |
| 10 | Hand-Off: omits the empty-pile skip and the turn-loss condition | On an empty pile a 3/Joker **skips** the next player and may be spent electively; whether the collector loses a turn depends on whether they were the scheduled next player. `docs/RULES.md:30, 31, 32`; `docs/DECISION_LOG.md:8` (D-002), `:21` (D-015) | Added both paragraphs ("If the pile is empty…" and "If the player who accepts was the next player anyway…"). |
| 11 | "Ten — Clear: Instantly clears the pile. You get to play again immediately." | Accurate, but incomplete: a 10 also resets all constraints including the Seven lock. `docs/RULES.md:39, 46`; `docs/DECISION_LOG.md:11` (D-005) | "Clears the pile at once and lifts any Seven lock. You play again immediately." |
| 12 | "Seven — Lock: … After a Seven: only lowerd pr nod or can be played." (garbled) | The next ordinary play must be rank **7 or lower**. D-013 states explicitly that it must never be worded as "lower than 7", because that would forbid a 7 on a 7 and break the four-Seven clear. `docs/RULES.md:44`; `docs/DECISION_LOG.md:19` (D-013) | "After a Seven, the next ordinary play must be rank seven or lower. A Seven on a Seven is legal, and locks the next player again." **Garbling note:** the run most likely intended Part One's "only lower or power cards" (`docs/source/OWNER_RULES_PART_1.md:17`). That is an inference and the draft string is **not unambiguous**; the copy follows D-013's precise wording instead, which is the later, more specific ruling. |
| 13 | Seven: omits the four-Seven clear, the lock's end, and the 2/10 overrides | Four Sevens in sequence clear the pile and grant another play; the lock lifts once a legal non-7 ordinary card is played; 2 and 10 override. `docs/RULES.md:44, 45, 46`; `docs/DECISION_LOG.md:19` | Added all three sentences. |
| 14 | "Two — Free Pass: Can be played on any card. The next player can play any card they want." | Matches `docs/RULES.md:50` and `docs/source/OWNER_RULES_PART_1.md:18`. **No contradiction.** But the follow-on question — what counts as the effective top rank after that free play — is OPEN (`docs/RULES.md:51`). | Kept almost verbatim, with "It resets the restrictions" added. Deliberately silent on the effective top rank afterwards (see Part 3, item 2). |
| 15 | "Face-Up Cards: Once the draw pile, you must play your 3 ace-up [face-up] wisely" — i.e. face-up play is triggered by the draw pile emptying | **Wrong trigger.** The transition is hand → face-up → face-down and is gated on your **hand** being empty, not on the stock running out. A player cannot voluntarily use face-up cards while hand cards remain. `docs/RULES.md:55`; `docs/DECISION_LOG.md:23` (D-017). Part One's looser "After stock empties, play face-up…" (`docs/source/OWNER_RULES_PART_1.md:18`) is superseded by D-017 under the precedence rule at `docs/RULES.md:4`. | "When your hand is empty, you play from your three face-up cards." |
| 16 | Face-up: ".ı. order matters." | No document rules any required order for face-up cards; D-017 only forbids using them early. The three are freely chosen. `docs/RULES.md:55` | Replaced with "You choose which one each turn." The draft's "order matters" is strategic advice, not a rule, so it is not stated as one. |
| 17 | "Face-Down Cards (Luck Phase): After face-up cards … are gone, play face-down cards, one a a time." | Correct in substance, and the cards are played **blind**. `docs/RULES.md:56`; `docs/DECISION_LOG.md:23` | "you play your face-down cards blind, one at a time." The label "Luck Phase" is dropped from the rule text — it is a design label, not a documented game term. |
| 18 | Face-down: "You can only pick another if you have" (truncated) | Canonical consequence of a failed blind card: you collect the pile into your **hand**, resume hand play until the hand is empty again, and only then return to table cards. There is no free choice between zones. `docs/RULES.md:56`; `docs/DECISION_LOG.md:23` | "If the card you turn over cannot legally stay in play, you take the pile into your hand. You then play out your hand as normal, and only return to your table cards once your hand is empty again." **Garbling note:** the truncated string is **not unambiguous** and was not reconstructed; the canonical D-017 wording is used instead. |
| 19 | Objective: "Get rid of all your cards before everyone else." | Risks implying the match ends when someone finishes. It does not: play continues until one player remains. `docs/RULES.md:9`; `docs/DECISION_LOG.md:24` (D-018) | Added "Finishing does not end the match. Play carries on until one player is left holding cards." |
| 20 | Draft omits player count, the deal, who starts, four-of-a-kind, and Shit Face's cosmetic-only status | All CONFIRMED: `docs/RULES.md:8, 10, 11, 20, 62`; `docs/DECISION_LOG.md:11, 16, 17, 25` | Added as the "Setting up" block, the four-of-a-kind line in Turn Rules, and the Shit Face note. |

### Garbled strings — resolved vs not resolved

| Draft string | Treatment |
| --- | --- |
| "asceeding" | Unambiguous: "ascending". The word is then dropped anyway, because the rule is equal-or-higher (row 2). |
| "a sinte 3 cards in" | Reads as "at least 3 cards in hand". Intent clear enough, but the rule itself is wrong (row 5). |
| "someone gne gets stuck" | Unambiguous: "someone gets stuck". Framing is wrong (row 8). |
| "only lowerd pr nod or can be played" | **NOT unambiguous.** Best guess is "only lower or power cards can be played". Resolved by falling back to D-013, not by reconstruction (row 12). |
| "3 ace-up wisely .ı. order matters" | "ace-up" = "face-up" is clear. ".ı." is **not** recoverable; most likely a dash or ellipsis. No meaning assigned (rows 15, 16). |
| "after face-up cards up ee ver cards are gone" | **NOT unambiguous.** Probably "after face-up cards … are gone", possibly with a reference to the draw pile. Resolved by using D-017's trigger instead (row 17). |
| "one a a time" | Unambiguous: "one at a time". |
| "You can only pick another if you have" | Truncated mid-sentence. **NOT recoverable.** Not reconstructed (row 18). |

---

## 3. Open rules this page deliberately does not state

The page is silent on each of the following, because `docs/OPEN_DECISIONS.md` or `docs/RULES.md` records it as unruled. None of these has been filled in with a conventional Shithead convention.

| # | Point not stated | Open-item reference |
| --- | --- | --- |
| 1 | How a tie is settled if players remain tied after comparing lowest, second-lowest and third-lowest cards. The copy says only "whoever holds the lowest card starts" and gives no tie-break procedure. | `docs/OPEN_DECISIONS.md:22` (item 3); `docs/RULES.md:12` (D-019 sub-case) |
| 2 | What becomes the effective top rank after the free play that follows a 2, and whether a 2 counts toward a four-of-a-kind streak. The copy says the next player may play anything, and stops there. | `docs/RULES.md:51` |
| 3 | Whether a group play of several 7s creates one lock or a stacked lock. | `docs/OPEN_DECISIONS.md:23` (item 4a) |
| 4 | Whether a pile clear (a 10 or four-of-a-kind) while a lock is active also clears the lock, or the lock survives onto the empty pile. The copy states only that a 10 lifts the lock, which is directly confirmed. | `docs/OPEN_DECISIONS.md:23` (item 4b); confirmed part at `docs/RULES.md:39, 46` |
| 5 | What happens to a pending lock if the locked player finishes before taking the locked turn. | `docs/OPEN_DECISIONS.md:23` (item 4c) |
| 6 | Whether a blind-revealed 2, 7 or 10 exerts its power as normal. The copy says power cards remain effective in the endgame (confirmed at `docs/RULES.md:57`) but says nothing about blind reveals specifically. | `docs/OPEN_DECISIONS.md:24` (item 5a) |
| 7 | How a blind reveal interacts with an active Seven lock, and exactly what is picked up on failure in that case. | `docs/OPEN_DECISIONS.md:24` (item 5b) |
| 8 | Whether blind face-down play on an empty pile is always legal. | `docs/OPEN_DECISIONS.md:24` (item 5c) |
| 9 | Whether a player who finishes by playing a 10 is out immediately with the extra turn lapsing. | `docs/OPEN_DECISIONS.md:25` (item 6a) |
| 10 | Whether finishing while a Seven lock is pending dissolves or transfers the lock. | `docs/OPEN_DECISIONS.md:25` (item 6b) |
| 11 | The ordering of finish detection against refill when the stock is already exhausted. | `docs/OPEN_DECISIONS.md:25` (item 6c) |
| 12 | How rank runs are counted around special cards — i.e. whether a four-of-a-kind run can be interrupted by a power card. The copy says only "four cards of the same rank in a row". | `docs/RULES.md:21` |
| 13 | How a 10 resolves if it appears among simultaneously played cards. | `docs/RULES.md:40` |
| 14 | Whether opponents must be able to see the powers of exposed face-up cards, and whether the pile clears once the table is exhausted. | `docs/RULES.md:58` |
| 15 | Whether the direction of play can change during a game beyond its initial establishment. The copy does not mention direction at all. | `docs/RULES.md:12` |
| 16 | Whether declared extra skip cards must be consumed after a counter chain, and how a combined move is submitted and validated. The copy says a combined move is possible (confirmed at `docs/RULES.md:33`) but not how it is entered or sequenced against counters. | `docs/source/OWNER_RULES_PART_2.md:50`; partially addressed by D-014 at `docs/RULES.md:34` |
| 17 | Specific drink prompts, age gating, regional restrictions and accessibility substitutes for Shit Face mode. The copy states only that the mode is cosmetic. | `docs/RULES.md:63`; `docs/OPEN_DECISIONS.md:34` |
| 18 | Any statement about disconnects, AFK players, timeouts or forfeits. | `docs/OPEN_DECISIONS.md:21` (item 2, O-09); `docs/RULES.md:69` |

---

## 4. Owner questions — needed before this copy is final

1. **Ascending vs equal-or-higher on screen.** D-012 makes equal-or-higher the rule, so the draft's "ascending order" panel heading is inaccurate. Do you want the heading changed to "Playing Order — equal or higher", or kept as "Playing Order" with the rule in the body (as drafted here)?
2. **The Seven lock wording.** D-013 insists on "seven or lower" and forbids "lower than seven". Your draft also hints at Part One's "only lower **or power cards**". Should the page tell players explicitly which power cards beat an active lock? A 2 and a 10 are confirmed; a 3 or a Joker against an active lock is unruled (open item 4). Confirm whether to stay silent or whether you want to rule on it now.
3. **The face-up trigger.** Your draft gates face-up play on the draw pile emptying; D-017 gates it on your hand being empty. The copy follows D-017. Please confirm D-017 is still the rule, since Part One's looser line reads the other way.
4. **"Order matters" for face-up cards.** Is free choice among the three face-up cards correct, or do you want to rule an order? Nothing in the documents rules one.
5. **Hand-Off naming.** The page calls it "The Hand-Off" per your draft, and states that a Joker does exactly what a Three does. Do you want the headline to read "Three and Joker" on screen, or just "The Hand-Off" with the Joker explained in the body?
6. **Whether to show the setup block at all.** Player count, the 3/3/3 deal and "lowest card starts" are confirmed but were not in your draft. Keep them on screen 1, move them to a separate "Setup" screen, or drop them?
7. **"Luck Phase" label.** Keep it as a design label over the face-down section, or drop it? It is not a documented game term.
8. **Shit Face note placement.** Should the cosmetic-only disclaimer appear on this page, or only in the mode's own settings screen?
9. **Starting-tie text.** Open item 3 means the page cannot explain a persistent tie. Are you happy for the page to say nothing, or do you want to rule the sub-case so the page can be complete?
