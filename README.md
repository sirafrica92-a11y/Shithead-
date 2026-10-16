# Shithead / Shit Face

A multiplayer card-game project built around Africa's custom Shithead rules.

**Status:** Repository initialised; game foundation and implementation are being prepared for review. **There is no playable build yet.**

- **Shithead:** The core strategic card game for 2–6 players.
- **Shit Face:** An optional drinking-mode presentation layer. Drinking rules must never change game logic.
- **Key mechanic:** 3s and Jokers can redirect the playing pile; players may counterattack and strategically manipulate turn order.

The detailed rulebook, test cases, technical architecture, and development handover will be proposed on a separate foundation branch before being adopted as canonical.

## Ownership and project boundaries

This repository is the source of truth for the card game. SOUL and Claude Code can work on it, but neither may silently invent or override game rules. The SOUL application is a **separate** project and must not be modified as part of this game's setup.

> This repository is **public**. Do not commit secrets, API keys, personal information, or unreleased private assets.
