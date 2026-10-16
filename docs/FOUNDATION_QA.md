# Foundation quality audit — 16 October 2026

**Scope:** documentation and engineering requirements in draft PR #1; **no application implementation or runtime QA**. This note is for SOUL's future re-checks and Africa's review.

## Verified against owner messages

- The canonical gameplay innovation is **target-dependent** pile collection and turn order, not a global "every 3 skips" rule.
- Pile-pass decision owner can change during counters while the regular turn anchor remains fixed.
- Target can collect deliberately even if holding a 3/Joker; 3 and Joker are interchangeable and leave the game when played.
- Mixed attack and additional skips exist, but their interaction with an interrupted counter chain is not specified.
- Three-player targeting B vs C, four-player target B vs D, and scalable five/six-seat outcomes have explicit examples, each labelled as direct or derived.
- FastAPI + WebSockets is the **last explicit** server stack instruction. React Native is the mobile target; browser-first was an assistant recommendation.
- Optional Shit Face does not alter core rules.
- Parts One and Two are preserved as structured **non-verbatim** transcriptions under `docs/source/`; exact original wording still resides in Africa's chat, not in this repository. Never call the transcriptions raw or verbatim.

## Engineering traps now flagged

1. **Stale branch:** SOUL cannot study the full documents from current default `main` until the owner reviews/merges PR #1 or grants read access specifically to the proposed version.
2. **Ambiguous actions:** `counterWithThree` must handle **both** card 3 and Joker. It is an API action name, not a rank restriction.
3. **Phase mismatch:** "exactly one activePlayerId at all times" is underspecified for a lobby with zero players and after the match finishes. Resolve O-10; for a live PLAYING/PASS phase there must be exactly one action owner.
4. **Empty pile:** the owner gives a skip example when only 3/Jokers are available; whether the skip is freely elective is unknown. A rule-engine agent must not silently broaden this.
5. **Physical cards:** five skips in a six-seat match require five distinct 3/Joker cards in the actor's playable cards; the deck/Joker count is still unspecified.
6. **Sevens:** four consecutive sevens must be possible despite the lower-rank lock, but precise implementation (power exception, comparison bound and resets) requires O-03.
7. **Endgame:** "draw pile empty" does not unambiguously specify when a player may start using face-up vs face-down cards; hand exhaustion and pickup interactions need O-07.
8. **Termination:** a reducer can guarantee a next legal action but cannot guarantee progress if a player disconnects without an approved AFK policy.
9. **Privacy:** server snapshots, including error snapshots and reconnects, must not reveal another player's hand or facedown cards.
10. **Operational evidence:** a GitHub document or passing unit test is not proof a Windows SOUL installation has a tool enabled, or a game server has been deployed.

## Sign-off checklist

- [x] Documents have direct entry points for agent and owner.
- [x] Sources distinguish owner-confirmed, derived, and unanswered behaviour.
- [x] 2–6-player attack/no-extra-skip acceptance cases are written down.
- [x] Real SOUL navigation and feature boundaries described.
- [x] Rule/engineering decision register and first bounded task exist.
- [ ] Africa approves foundation.
- [ ] Foundation on approved GitHub revision; SOUL source grant pinned to it.
- [ ] SOUL actually studies the project and passes packet W0.
- [ ] Owner resolves blockers for W3/full-playable build.
- [ ] Code/tests/live gameplay exist and are validated.

This document must not be treated as an assertion that code or tests ran; its checked items are documentation review only.
