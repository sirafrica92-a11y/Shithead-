# Owner source Part One — master engineering prompt

**Provenance:** Africa supplied this master prompt in chat on 16 October 2026 and labelled it "Part one". This file is a **faithful structured transcription**, not a verbatim byte-for-byte archival copy. The owner later provided more precise counter/turn examples (Part Two); preserve that precedence.

## Absolute engineering requirements stated

- Server single source of truth. Clients submit intent only.
- All accepted actions explicitly determine who owns the turn and who acts next. Rejected actions return reasonCode, message, allowedActions and stateSnapshot.
- Game phases: `LOBBY`, `PLAYING`, `PILE_PASS_DECISION`, `FINISHED`.
- Track `activePlayerId` and `turnAnchorPlayerId` explicitly. Centralised turn resolution; no blind index-increment shortcuts.
- Normal play higher than pile top; power cards ignore rank; invalid/no available play means pile pickup, turn ends.
- Four consecutive same rank clear pile; completing player plays again.
- Draw to maintain three hand cards while stock lasts.
- 3 and Joker: removed from game; target any player; target may accept pile or counter by using 3/Joker; transfer decision ownership instantly. In pass phase, only `acceptPile` or `counterWithThree` allowed.
- 10 clears pile and seven-lock; same actor gets another turn.
- 7 may be played on anything; while locked only lower or power cards; four sevens clear.
- 2 may be played on anything; resets constraints; next player free to play any card.
- After stock empties, play face-up and later face-down cards one at a time; failed face-down picks up pile, turn ends.
- Shit Face drinking effects do not change game state.
- Reject illegal/stale moves safely; unambiguous transitions, stop/recovery and deterministic effects.
- Automated tests for 2–6 seats, 3/Joker attacks/counters/multiple cards, 10, seven-lock, pickup, face-down failures and full-game completion.
- Final engine should be production-ready, strongly tested and resistant to freezes.

## Technical decision history

Part One included two backend choices in sequence:

1. A `Node.js + Socket.IO` stack proposal, with React Native for iOS/Android.
2. A later **explicit instruction** to proceed with **FastAPI + WebSockets** for the server-authoritative state machine.

The later explicit backend instruction wins; React Native remained stated.

## Known contradiction

The original broad statement "each resolved 3 skips exactly one player" and "turn advances from target" does **not** agree with the owner's later concrete Part Two cases when the target is not next. Do not mechanically implement these broad phrases. See `docs/RULES.md` and `docs/TURN_ENGINE.md`.
