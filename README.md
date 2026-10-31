# SHITHEAD Games

> **RAILWAY RELEASE REMINDER:** Before any deployment, **update/verify the GitHub deployment branch `deploy/railway-shithead-games-staging` FIRST**, then verify Railway is tracking it and the intended SHA reaches `SUCCESS`. This is a GitHub branch update, **not** a routine source reconnect. Preserve the live games and `match-data` volume at `/data`. See [Railway First Check](docs/RAILWAY_FIRST_CHECK.md).

**Six traditional games. One multiplayer home.**

Play online: **[play.shithead.games](https://play.shithead.games)**

SHITHEAD Games is a browser-based, mobile-friendly collection of traditional social games from different cultures. Start a room, share its four-character code and play together. The focus is on accessible games with personality, strategy and human interaction—not a complicated competitive platform.

What began as a custom multiplayer **Shithead** card game has grown into a six-game platform while keeping the original jester logo and dark, antique-gold, cream and crimson identity.

> **Current status (31 October 2026):** Six multiplayer games and two computer-opponent **Solo Play** modes (Ludo and Awalé) are deployed on Railway at release `3854becb`. Solo Dara is developed and tested but **parked, unmerged and not live** as draft PR #30. Server/CI status is verified; real-device end-to-end visual checks remain a follow-up.

## Play the games

| Game | Players | What you play | What it rewards |
| --- | --- | --- | --- |
| **Shithead** | 2–6 | The original card game, with owner-defined 3/Joker hand-offs and counter-chains, 7 locks, 2 resets, 10 clears and tactical pile pickups | Adaptation, reading opponents and timing |
| **Ludo** | 2–4 | Race four tokens home using server-rolled dice, safe squares, blockades, captures and extra turns | Patience, risk and opportunity |
| **Awalé** | 2 | West African Oware/Abapa-style seed sowing across 12 houses, with feeding and two-or-three-seed captures | Foresight and calculation |
| **Dara** | 2 | Nigerian 5×6 board strategy: place stones, move orthogonally, form new lines of three and capture | Pattern recognition and positioning |
| **Yoté** | 2 | West African 5×6 tactical game: place stones, move and jump-capture, then choose a bonus removal | Tactics and sacrifice |
| **Jamaican Dominoes** | 4 | Four-player double-six tile game, Partner (2 vs 2) by default or optional Cut Throat free-for-all | Collaboration and strategy |

Each game has its own on-site **How to play** screen. Traditional games have regional variants; the implementation follows the rules documented for **this platform**, not necessarily every local version. The exact custom Shithead rules are recorded in [RULES.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/docs/RULES.md) and [DECISION_LOG.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/docs/DECISION_LOG.md).

## Play solo — against the computer

When friends are unavailable, **Solo Play** requires no lobby, invitation or room code. It is separate from the guest multiplayer system and uses the same existing server-side game rules.

| Solo mode | Live? | Where | Notes |
| --- | --- | --- | --- |
| **Ludo** | **Live** | [Solo Ludo](https://play.shithead.games/solo/ludo) | Computer-controlled opponent; existing Ludo dice/rules |
| **Awalé** | **Live** | [Solo Awalé](https://play.shithead.games/solo/awale) | Legal sowing, capture and feeding from existing Abapa engine |
| **Dara** | **Not live — work parked** | [Draft PR #30](https://github.com/sirafrica92-a11y/Shithead-/pull/30) | Implemented and CI-tested, retained for another agent; **do not merge/deploy without renewed owner approval** |
| **Yoté, Shithead, Jamaican Dominoes** | Not implemented for Solo Play | — | Future possibilities, not a released feature |

Solo sessions currently require internet and are held in server memory. A server restart can end a solo match; offline play, persisted solo saves and difficulty selection are **not supported**. Existing multiplayer game modes are unaffected.

**Upcoming navigation improvement (not yet implemented):** The current theme and logo stay. Selecting one of the six game cards should lead to a separate screen with that game's header, name entry and Create Room / Join Room actions; from there, the existing room code, readiness and multiplayer game flow continue unchanged. This avoids stacking game selection and seat entry on the same long home page. Solo Play remains a small secondary option, not the main invitation to play.

**Existing Solo Play quality improvement (not yet implemented):** The server already executes Ludo and Awalé computer moves automatically, but its current snapshots skip intermediate action visuals. The next agent must reproduce the reported phone behaviour and display each server-generated CPU roll/move/capture in sequence, then return control to the human without requiring an extra click for the CPU. Full rules, security, room and regression checks are required. Details and acceptance criteria live in [HANDOVER.md](HANDOVER.md) on the documentation branch.

## Playing together

1. Open [play.shithead.games](https://play.shithead.games), choose a game and enter a player name.
2. **Create a room** and share its four-character code; friends choose **Join room** and enter that code.
3. When everyone is in, mark yourselves **Ready** to start.
4. Play in real time. The server validates the rules and whose turn it is.
5. After a match, vote for a rematch or, where permitted, have the host switch games within the room.

**Platform features:** guest access without registration; room codes; server-authoritative turns; per-seat tokens and private views where applicable; refresh/reconnection; saved room/match state; rematch voting; quick reactions; and mobile-oriented game boards. Some game and mid-match-joining behaviours intentionally differ by game.

## Built and running

- **Backend:** Python, FastAPI, authenticated WebSockets and server-owned game logic.
- **Six isolated multiplayer rule engines:** `gameplay.py` (Shithead), `ludo.py`, `awale.py`, `dara.py`, `yote.py` and `dominoes.py`.
- **Shared foundation:** lobby, seat management, room state, message validation, reconnection, rematches and a small game-capacity catalogue.
- **Frontend:** HTML, CSS and vanilla JavaScript with dedicated boards/renderers for the non-card games.
- **Persistence:** SQLite for saved rooms, seats and matches; Railway's persistent volume mounted at `/data`.
- **Hosting:** Railway, with a single application worker and a health endpoint at `/health`.

Game rules and state transitions remain separate from the shared multiplayer infrastructure. New additions should not change existing games merely to reuse their code.

### Repository layout

**Important:** The GitHub default `main` branch currently contains **only this README**. It is *not* the live application code. The implementation, tests and active handover live on **[`deploy/railway-shithead-games-staging`](https://github.com/sirafrica92-a11y/Shithead-/tree/deploy/railway-shithead-games-staging)**.

| Path on the deployment branch | Purpose |
| --- | --- |
| `server/app/main.py` | FastAPI routes, authenticated multiplayer WebSockets and game actions |
| `server/app/lobby.py` | Room and seat lifecycle, broadcasting, SQLite persistence |
| `server/app/gameplay.py`, `server/app/rules/` | Custom Shithead engine and rule boundaries |
| `server/app/{ludo,awale,dara,yote,dominoes}.py` | Separate server-authoritative game engines |
| `server/app/game_catalog.py` | Supported game names and player-capacity contracts |
| `server/app/solo_ludo.py`, `server/app/solo_awale.py` | Live independent computer-opponent APIs; ephemeral private solo sessions |
| `server/app/solo_dara.py` *(draft PR #30 only)* | Completed/tested Dara Solo Play implementation, not yet in production |
| `server/app/static/` | Responsive interfaces, individual game renderers and original brand assets |
| `server/tests/` | Rule contracts, game simulations, WebSocket, recovery and regression tests |
| `docs/` | Rule decisions, architecture, scenarios and verification history |
| `HANDOVER.md` | Single current platform handover, risks, remaining QA and proposed next steps |
| `railway.json` | Railway build, start command and health-check configuration |

## Run locally

Use Python 3.12 (the version tested in CI), then run:

~~~bash
git clone https://github.com/sirafrica92-a11y/Shithead-.git
cd Shithead-
git checkout deploy/railway-shithead-games-staging
python -m pip install -r requirements.txt
python run_local.py
~~~

The launcher starts the local server at **http://127.0.0.1:8000** and opens a browser. A Windows `Start Shithead.bat` launcher is also included. The local-only launcher binds to localhost; the hosted website is the intended way to play remotely with friends.

Run the full regression suite and JavaScript syntax checks from the deployment branch:

~~~bash
python -m pytest -q server/tests
python -m py_compile run_local.py
for file in client ludo awale dara yote dominoes owner owner-login solo-ludo solo-awale; do
  node --check "server/app/static/$file.js"
done
~~~

**Verified releases:** Awalé Solo Play PR #29 tested 424 Python tests and ten JavaScript syntax checks before merge; Railway release `3854becb` reached **SUCCESS**. Dara Solo Play PR #30 at `c0043f2` passed **429 tests (31 warnings) and eleven JavaScript syntax checks** in GitHub Actions workflow `41215614376`, but this is a **draft, unmerged development branch**. To validate that branch separately, check it out and include `solo-dara.js` in the JavaScript checks. Do not mistake draft-only test success for deployment.

**Known verification limits:** an intermittent legacy Shithead start-tie test failure was observed on one earlier CI run, although the verified five-game release run passed. Full manual two-device/mobile-browser playthroughs for the newest games are not yet independently recorded. See [HANDOVER.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md) for reproducible concerns and follow-up checks. Automated green checks and a healthy server do not by themselves establish zero gameplay issues.

## Safe development and deployment

- **Production source:** `deploy/railway-shithead-games-staging`, **not `main`**.
- **Infrastructure:** Railway service `shithead-web` uses an attached `match-data` volume at `/data`. Preserve this volume and existing rooms.
- **Rules:** Owner-defined Shithead behaviour must not be replaced with assumed standard rules. Each additional game must have its own rules contract, engine and tests.
- **Release discipline:** work in a branch, inspect the changed files, run the existing regression suite and new game's full-match/recovery checks, review browser behaviour, then merge and verify the exact Railway deployment.
- **Ownership:** the project's concepts, game choices, product requirements and rules decisions are owner-led; AI coding assistance is used for implementation and testing under review.

This is an accessible **public preview** rather than a mature account-based games service. Guest room codes are not accounts; full moderation, real user accounts and wider operational safeguards are not implemented. Don't commit secrets, private credentials or personal information to this public repository.

### What's next?

The six-game multiplayer milestone and two live Solo Play modes are complete. **The owner has ended Solo Play game expansion:** Dara is the final planned computer-opponent title, with finished code deliberately parked in draft [PR #30](https://github.com/sirafrica92-a11y/Shithead-/pull/30), unmerged and not live. **Do not build Solo Play versions of Yoté, Shithead, Jamaican Dominoes or other games.** Priority now is simplifying the game-selection → separate selected-game setup → existing room lobby journey, making human multiplayer prominent, and showing existing CPU turns automatically and clearly in live Ludo/Awalé. **Morabaraba** is a separate multiplayer research candidate only; Fanorona is excluded.

---

**[Play SHITHEAD Games](https://play.shithead.games)** · [Live application code](https://github.com/sirafrica92-a11y/Shithead-/tree/deploy/railway-shithead-games-staging) · [Platform handover](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md)


### Owner analytics, operations and demand monitoring
The owner-only dashboard code is deployed, but access remains disabled until private Railway authentication settings are configured. Preferred Google owner sign-in uses all three service variables: `SHITHEAD_GOOGLE_CLIENT_ID`, `SHITHEAD_OWNER_EMAIL`, `SHITHEAD_ADMIN_SESSION_SECRET`; configure an authorised Google JavaScript origin of `https://play.shithead.games`. The older HTTP Basic option uses `SHITHEAD_ADMIN_PASSWORD` when Google mode is not configured. Do not commit credentials or make the admin dashboard public.
Analytics records daily aggregate page loads, game starts/completions and denied room-creation attempts (not unique visitors). Owner-only Incidents, Problems and Changes registers record manual operations entries. The Railway billing date/usage/budget fields are optional **manual figures**, not linked to Railway invoices. Capacity remains 100 allocated/saved rooms (not 100 simultaneously active matches); existing joins continue at capacity. There is no real waiting list or guaranteed five-minute availability.
