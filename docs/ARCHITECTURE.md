# Technical architecture — practical build plan

**Status:** proposed. Implement incrementally; nothing has been deployed.

## Decision history

Owner's initial combined master prompt proposed **Node.js + Socket.IO**, React Native, iOS and Android; the **later explicit instruction replaced the server requirement with FastAPI + WebSockets**. Treat FastAPI as the accepted server choice unless owner later changes it. No reason to include Node.js solely because it appeared earlier.

## Target architecture

- **Authoritative engine:** Python 3.12+ pure functions, typed state and explicit phase transition reducer, completely separate from network/UI and storage.
- **Server:** FastAPI and standard WebSockets; validates seat/session, move ownership, version/replay IDs, game phase, legal choices and deadlines before invoking reducer.
- **State persistence:** future decision (transactional database needed before production); serialise reducers per match to prevent concurrent turn races. No in-memory-only claims of crash recovery.
- **Client target:** React Native (iOS/Android) as originally selected. **Prototype recommendation:** a minimal responsive browser client first, using either shared web-compatible UI or a tiny independent web front end; owner approval required before changing the committed primary client strategy.
- **Deployment:** unspecified. Owning a `.tech` name is separate from hosting a persistent WebSocket backend. Hosting, identity, database, moderation, monitoring, uptime and ongoing costs require decisions.
- **Mode:** Shit Face is client-only cosmetic presentation driven by ordinary server events; no separate game engine.

## Proposed folder layout (not created until implementation)

```text
server/
  app/main.py               FastAPI app
  app/models.py             validated types
  app/rules/reducer.py      pure game logic
  app/rules/turns.py        one turn resolver
  app/rules/cards.py        legality and effect definitions
  app/realtime.py           WebSocket session, authentication and broadcast
  tests/                   rules / property / protocol / multi-seat tests
client/
  ...                       responsive first playable client
docs/                        approved game requirements
```

## Required interface

Intent messages: `matchId, playerId/auth, requestId, expectedVersion, actionType, payload`. Only the server assigns `activePlayerId`, validates `cardId` ownership, resolves shuffled/dealt cards and issues snapshots/events. Keep hidden cards secret: do **not** send all player hands or unflipped cards in `stateSnapshot`. Filter by authorised viewer even in rejected-action replies.

Client never performs rule transitions optimistically as fact. After reconnect, it renders fresh authoritative state with proper secret redaction.

## Threats / correctness

- A player must not choose cards absent from their hand or inspect opponents' private cards.
- Concurrent accepted requests cannot consume the same turn or card twice.
- Counters do not move ordinary turn anchor.
- Phase-specific action whitelists, structured recoverable rejects and stale-version responses.
- Reconnection, timeouts/AFK and persistence must not produce duplicate events.
- Tests must simulate 2–6 humans, chained redirects, final pickup, disconnections, random legal-play sequences and crashing/restarting rooms.

## Build order

1. Owner-reviewed rule gaps prioritised; choose rule examples that can be implemented without inventing endgame/dealing.
2. Pure engine + robust deterministic tests.
3. Small 2-player local playable vertical slice.
4. 3–6-player real-time rooms, reconnect and persistence.
5. React Native clients, matchmaking and privacy/security QA.
6. Optional Shit Face overlay, deployment/domain and monitoring.
