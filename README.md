# SHITHEAD Games

**Six traditional games. One multiplayer home.**

Play online: **[play.shithead.games](https://play.shithead.games)**

SHITHEAD Games is a browser-based, mobile-friendly collection of traditional social games from different cultures. Start a room, share its four-character code and play together. The focus is on accessible games with personality, strategy and human interaction—not a complicated competitive platform.

What began as a custom multiplayer **Shithead** card game has grown into a six-game platform while keeping the original jester logo and dark, antique-gold, cream and crimson identity.

> **Current status (31 October 2026):** Six games merged and deployed as a public preview. This is a **working application**, not a proposed concept. Live-server health and automated tests are verified; independent real-device playthroughs of every new game are still a release-quality follow-up.

## Play the games

| Game | Players | What you play | What it rewards |
| --- | --- | --- | --- |
| **Shithead** | 2–6 | The original card game, with owner-defined 3/Joker hand-offs and counter-chains, 7 locks, 2 resets, 10 clears and tactical pile pickups | Adaptation, reading opponents and timing |
| **Ludo** | 2–4 | Race four tokens home using server-rolled dice, safe squares, blockades, captures and extra turns | Patience, risk and opportunity |
| **Awalé** | 2 | West African Oware/Abapa-style seed sowing across 12 houses, with feeding and two-or-three-seed captures | Foresight and calculation |
| **Dara** | 2 | Nigerian 5×6 board strategy: place stones, move orthogonally, form new lines of three and capture | Pattern recognition and positioning |
| **Yoté** | 2 | West African 5×6 tactical game: place stones, move and jump-capture, then choose a bonus removal | Tactics and sacrifice |
| **Jamaican Dominoes** | 4 | Partner 2-v-2 (default) or Cut Throat individual; double-six tiles and defined six-point variants | Reading the table, timing and teamwork |

Each game has its own on-site **How to play** screen. Traditional games have regional variants; the implementation follows the rules documented for **this platform**, not necessarily every local version. The exact custom Shithead rules are recorded in [RULES.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/docs/RULES.md) and [DECISION_LOG.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/docs/DECISION_LOG.md).

## Playing together

1. Open [play.shithead.games](https://play.shithead.games), choose a game and enter a player name.
2. **Create a room** and share its four-character code; friends choose **Join room** and enter that code.
3. When everyone is in, mark yourselves **Ready** to start.
4. Play in real time. The server validates the rules and whose turn it is.
5. After a match, vote for a rematch or, where permitted, have the host switch games within the room.

**Platform features:** guest access without registration; room codes; server-authoritative turns; per-seat tokens and private views where applicable; refresh/reconnection; saved room/match state; rematch voting; quick reactions; and mobile-oriented game boards. Some game and mid-match-joining behaviours intentionally differ by game.

## Built and running

- **Backend:** Python, FastAPI, authenticated WebSockets and server-owned game logic.
- **Six isolated rule engines:** `gameplay.py` (Shithead), `ludo.py`, `awale.py`, `dara.py` `yote.py` and `dominoes.py`.
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

Run the complete automated checks from the deployment branch:

~~~bash
python -m pytest -q server/tests
python -m py_compile run_local.py
node --check server/app/static/client.js
node --check server/app/static/ludo.js
node --check server/app/static/awale.js
node --check server/app/static/dara.js
node --check server/app/static/yote.js
node --check server/app/static/dominoes.js
node --check server/app/static/owner.js
~~~

At the **six-game milestone** on 30 October 2026, the verified release checks reported **397 passing Python tests**, 31 warnings and successful JavaScript syntax checks for all six game client files. The project also has specific complete-game, multiplayer, persistence and regression tests.

**Known verification limits:** an intermittent legacy Shithead start-tie test failure was observed on one earlier CI run, although the verified five-game release run passed. Full manual two-device/mobile-browser playthroughs for the newest games are not yet independently recorded. See [HANDOVER.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md) for reproducible concerns and follow-up checks. Automated green checks and a healthy server do not by themselves establish zero gameplay issues.

## Owner analytics (under development — not yet deployed)

The `feature/owner-analytics-dashboard-20261031` branch adds an owner-only dashboard at `/owner/analytics`, including homepage views, referral categories, rooms created, joins, **server-confirmed match starts and completions**, rankings across six games, live connected seats and aggregated CSV export.

- Stored in a separate `analytics.sqlite3` file on the same persistent volume. Does **not** modify rooms or save player names, room codes, IPs, cookies, visitor IDs or full referral URLs.
- Privacy-minimal aggregate daily counters; gameplay continues if analytics becomes unavailable. Match actions do **not** trigger a per-move analytics write.
- Disabled by default: `SHITHEAD_ADMIN_PASSWORD` must be supplied as a **private Railway environment variable of at least 20 characters**; admin username is `owner` and login uses HTTPS HTTP Basic. Never put the password in GitHub or share it in a URL.
- No historical traffic is backfilled; homepage views are not unique visitors and may include bots. No analytics claims are valid until the feature is deployed and verified.
- The current branch is a draft review proposal, not a deployed owner portal; preserve the existing six-game runtime while testing it.

## Safe development and deployment

- **Production source:** `deploy/railway-shithead-games-staging`, **not `main`**.
- **Infrastructure:** Railway service `shithead-web` uses an attached `match-data` volume at `/data`. Preserve this volume and existing rooms.
- **Rules:** Owner-defined Shithead behaviour must not be replaced with assumed standard rules. Each additional game must have its own rules contract, engine and tests.
- **Release discipline:** work in a branch, inspect the changed files, run the existing regression suite and new game's full-match/recovery checks, review browser behaviour, then merge and verify the exact Railway deployment.
- **Ownership:** the project's concepts, game choices, product requirements and rules decisions are owner-led; AI coding assistance is used for implementation and testing under review.

This is an accessible **public preview** rather than a mature account-based games service. Guest room codes are not accounts; full moderation, real user accounts and wider operational safeguards are not implemented. Don't commit secrets, private credentials or personal information to this public repository.

### What's next?

The six-game target has been reached. The current priority is **hands-on testing, owner analytics and polish**, not adding more games at the expense of stability. Morabaraba is a research candidate, not an implemented game. Fanorona is excluded from the roadmap.

---

**[Play SHITHEAD Games](https://play.shithead.games)** · [Live application code](https://github.com/sirafrica92-a11y/Shithead-/tree/deploy/railway-shithead-games-staging) · [Platform handover](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md)
