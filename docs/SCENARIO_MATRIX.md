# Seat order scenarios (2–6 players)

**Status:** proposed acceptance examples. CONFIRMED = explicitly described by owner; DERIVED = application of the owner's general rule. Not a replacement for the original owner source.

Assumptions: seats A, B, C, D, E, F in order, A initiates, nonempty playing pile, one 3 or Joker attack, no additional skip cards, no counters, target accepts, all players remain eligible.

| Seats | Target | Collector | Next actor | Evidence |
| --- | --- | --- | --- | --- |
| A B | B | B | A | DERIVED |
| A B C | B | B | C | CONFIRMED |
| A B C | C | C | B | CONFIRMED |
| A B C D | B | B | C | CONFIRMED |
| A B C D | C | C | B | DERIVED |
| A B C D | D | D | B | CONFIRMED |
| A B C D E | B | B | C | DERIVED |
| A B C D E | C/D/E | selected target | B | DERIVED |
| A B C D E F | B | B | C | DERIVED |
| A B C D E F | C/D/E/F | selected target | B | DERIVED |

## Redirect examples

A targets C, C redirects to B, B accepts: in a three-seat game C plays next (DERIVED). A targets E, E redirects to C, C redirects to B, B accepts: in a six-seat game C plays next (DERIVED).

The original actor remains the turn-order anchor throughout redirects; the current recipient owns only the response decision. A receiver can accept even if holding a counter card.

## Empty-pile examples

A uses one 3 or Joker: in a two-seat game A plays again; with three or more seats, C acts next. These one-card examples follow the owner's case where only 3/Joker cards are playable. Whether the action is optional when other cards could be played is OPEN.

In a four-seat game with enough such cards: A attacks B, B accepts, then C and D are skipped, so A acts again. Or A attacks D, D accepts, then B and C are skipped, so D acts next. These two multi-card examples are owner-supplied. Five- and six-seat multi-skip versions are DERIVED, require enough distinct cards, and must not be mistaken for established deck composition.

## Unresolved combined effect

If the pile recipient counters while the initiator has declared additional skips, card commitment, sequencing and turn outcome have not been approved. Do not choose an answer to this edge case without an owner decision.

## Test assertions

For every row verify: phase, active player, original turn anchor, decision owner, final collector, pile transfer, card removal, next scheduled seat, turn version, allowed actions and no duplicate card identity. Mark pending scenarios with unresolved mechanics instead of inventing an expected answer.
