# Rule and product decision register

Only a direct decision from Africa changes the game's canonical rules. This register links what is **decided** to its owner source and avoids mistaking an agent's suggestion for a decision.

| ID | Status | Decision / principle | Evidence |
| --- | --- | --- | --- |
| D-001 | CONFIRMED | 3 and Joker share attack and defence powers; counter may redirect to any other player, including a previous attacker | Owner Part Two |
| D-002 | CONFIRMED | Whether a pile collector loses an immediate turn depends on whether they were the originally scheduled next player; counter chains do not automatically redefine regular turn order | Owner Part Two |
| D-003 | CONFIRMED | With an empty pile, a 3/Joker can skip the next seat; the owner explicitly gave a case with only 3s/Jokers available | Owner Part Two |
| D-004 | CONFIRMED | Multiple 3/Jokers may create a pile attack followed by successive skips; full counter interaction is not defined | Owner Part Two |
| D-005 | CONFIRMED | 10 clears, resets all constraints, same player again; 2 resets, 7 imposes lower-play rule | Owner Part One |
| D-006 | CONFIRMED | Server-authoritative finite state machine with four named phases, recoverable rejected actions, explicit actors | Owner Part One |
| D-007 | CONFIRMED | Later FastAPI + WebSockets instruction supersedes earlier Node.js + Socket.IO line | Owner Part One |
| D-008 | CONFIRMED | React Native iOS/Android was selected as mobile client target; browser-first is only a prototype recommendation | Owner Part One |
| D-009 | CONFIRMED | Shit Face is optional and cosmetic; no drinking consequences affect the engine | Owner Part One |
| D-010 | CONFIRMED | SOUL will lead as she gains tools, with Claude Code initially doing the technical steps she cannot perform | Owner's 16 Oct project discussion |

## Open decision IDs

| ID | Needs owner clarification | Why it matters |
| --- | --- | --- |
| O-01 | Deal, stock, number of decks and Jokers | Realistic card inventories and valid initial state |
| O-02 | Equal rank, group plays and rank order including Ace/Jack | Basic legality |
| O-03 | Seven-lock exact comparison, duration and four-7 exception | Power-card compatibility |
| O-04 | Multi-card attack + counter chain, timing and skip ordering | Avoid deadlocks, double spending and surprises |
| O-05 | May an empty-pile 3/Joker skip when another playable card is available? | Preserve strategic constraint |
| O-06 | Refill timing after played/countered 3/Joker and after grouped cards | Card conservation |
| O-07 | Endgame transition and face-down failure handling | Finishing a real match |
| O-08 | Win/loss/last-player conditions and elimination effect on seat rotation | Terminal state |
| O-09 | AFK/disconnect, timeout, reconnect and forfeit | Multiplayer recovery |
| O-10 | LOBBY/FINISHED ownership nullability (Part One says exactly one actor "at all times") | Model state invariant |
| O-11 | Authentication, persistence, hosting and prototype platform | Public release |
| O-12 | Specific Shit Face party prompts and age-appropriate design | Optional mode |

## How to add a decision

`D-011 | CONFIRMED | Precise owner decision, with date | Owner message / review URL`

Also update `docs/RULES.md`, `docs/OPEN_DECISIONS.md`, `docs/TURN_ENGINE.md` and tests that depend on it. Append; never silently replace an older entry or pretend one was approved.
