# SHITHEAD Games — catalogue & release roadmap
Owner direction captured: 30 October 2026

## Product identity
The platform celebrates traditional games from different communities and countries.
Each game should challenge players in a *different* useful way, without turning
play into a formal lesson. Cultural variety is a deliberate editorial principle.
Existing Shithead logo, dark/gold/cream/crimson brand and social multiplayer
experience remain the shared identity.

## Release order / owner decisions

| Order | Game | Region / tradition | Player challenge | Decision |
| --- | --- | --- | --- | --- |
| 1 | Shithead | Cards | Tactical adaptability, risk and opponent reading | Already live; protect its established custom rules |
| 2 | Ludo | Cross-cultural traditional race game | Patience, resilience and risk under chance | Already live; protect the existing dice/token rules |
| 3 | Awalé (Oware / Abapa variant) | Côte d'Ivoire / West Africa | Foresight, planning, resource stewardship | **Active third-game development: draft PR #15**; finish and verify before release |
| 4 | Dara | Nigeria / Sahel | Spatial reasoning, alignment, patience | **NEXT after Awalé is completed and verified** |
| Later candidate | Yoté | West Africa | Sacrifice, tactical calculation | Research before approval |
| Later candidate | Dominoes | Widespread traditional game | Cooperation and tactical coordination, if a partner format is chosen | Research before approval |
| Excluded | Fanorona | Madagascar | — | **Owner removed from catalogue**; do not build or keep on release shortlist |
| Not prioritised | Chess | Global | — | Not part of the near-term roadmap |

The owner explicitly prefers **one development and release at a time**, even
if research identifies several possible titles. Do not begin Dara implementation
while Awalé remains unfinished. Never silently add a removed game back.

## Why one at a time
- Keep the working Shithead and Ludo engines, controls, persistence, assets,
  rules and Railway release untouched unless a change is essential to
  add the new game.
- Each traditional game's rules have variants. First select the precise
  documented version, then create an isolated authoritative engine and explicit
  safety/edge-case tests.
- Reuse room codes, authentication, seat recovery, WebSockets, lobby, reactions,
  rematches and shared visual design; minimise changes to existing game branches.
- Validate multiple completed games, invalid moves, turn management, refresh
  and reconnection, SQLite recovery, mobile interaction and full legacy suite.
- Commit on a game-specific branch, open a PR, review and require explicit owner
  approval before merging or deploying; preserve ability to roll back.

## Research-first note for Dara (NOT an implementation contract)
Broadly established rules: 2 players, a 5-by-6 board, 12 pieces per player,
first take turns placing pieces, then move one square orthogonally. Forming
a new row or column of three in the movement phase enables a capture.
Never assume the finer details are universal.

Variant questions to settle from trustworthy sources **before coding**:
- Are threes forbidden during the initial placement, or permitted without
  awarding captures?
- Must captured pieces be outside an existing three-in-a-row when possible?
- Can a blocked player pass or does that immediately end the match?
- What qualifies as a draw, and how are repeated positions handled?
- Are groups of four or more illegal or merely non-scoring?

Research pointers (the rule source chosen for the app must be specified):
- https://mathsweek.scot/news/how-to-play-dara
- https://c.tabletopia.com/games/ludos-africa/rules/dara-rulebook/en
- https://www.bead.game/games/traditional/dara

## Completion bar for Awalé
Draft PR #15 is *not* release approval. Require complete CI, rule-variant
review, interactive two-person browser/playthrough tests and responsive visual
checks. No merge or Railway deployment merely to meet a roadmap date.
