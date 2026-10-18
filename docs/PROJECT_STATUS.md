# Project status

**Branch:** `build/w1-turn-seat-selector` (at commit `bd48ad9` + approved corrections)
**Phase:** W1 and W2 complete and verified; W3 authorised, awaiting three owner rule rulings before the match reducer is built.

## Verified so far

- **W1 — turn/seat selector:** `server/app/rules/turns.py` resolves the next actor for all 2–6 seat cases, anchored to the original actor; counter chains never move the anchor (D-002, D-014).
- **W2 — pile-pass reducer:** `server/app/rules/pile_pass.py` is a pure, deterministic reducer covering attack, counter chains, accept, empty-pile skip and multi-skip, with mandatory actor validation on every action (wrong/missing actor rejected), stale-version rejection and structured errors.
- **W1↔W2 composition:** `server/tests/test_w1_w2_composition.py` pins the seam where the match engine will thread the reducer's terminal state into `resolve_next_actor`.

## Test suite

`python -m pytest server/tests -q` → **53 passed, 0 skipped** (verified against the current tree).

## Awaiting the owner

Three rule gaps must be ruled on before the W3 match reducer is built. No rule has been guessed and no W3 work has started:

1. Four-of-a-kind clear: does any four-of-a-kind clear the pile or only four 7s, and does the streak count consecutive pile cards or one player's cards?
2. How a played 2 sets the next comparison, and whether a 2 counts toward a four-of-a-kind.
3. Whether same-rank groups may be played under a seven-lock.

## Working rules for this project

- Africa alone decides rules; OPEN items are never filled with conventional Shithead conventions.
- Preserve completed milestones; no rewrites of W1/W2.
- No code changes, commits, pushes or merges except through the Work → Repos approval flow with Africa's explicit approval.
