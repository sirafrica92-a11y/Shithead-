# SHITHEAD Games

> **RAILWAY RELEASE REMINDER:** Before any deployment, **update/verify the GitHub deployment branch `deploy/railway-shithead-games-staging` FIRST**, then verify Railway is tracking it and the intended SHA reaches `SUCCESS`. This is a GitHub branch update, **not** a routine source reconnect. Preserve the live games and `match-data` volume at `/data`. See [Railway First Check](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/docs/RAILWAY_FIRST_CHECK.md).

**Six traditional games. One multiplayer home.**

Play online: **[play.shithead.games](https://play.shithead.games)**

SHITHEAD Games is a browser-based, mobile-friendly collection of traditional social games from different cultures. Start a room, share its four-character code and play together. The focus is on accessible games with personality, strategy and human interaction—not a complicated competitive platform.

What began as a custom multiplayer **Shithead** card game has grown into a six-game platform while keeping the original jester logo and dark, antique-gold, cream and crimson identity.

> **Current status (31 October 2026):** Six live multiplayer games, two existing computer-opponent modes (Solo Ludo/Awalé) and a social-first **choose game → separate room setup → lobby/Ready → play** flow. Current live GitHub SHA **`5cf59c7`**, Railway deployment **`a6a7f97b-025d-4072-9ca7-afb14ddfa175` SUCCESS**, `/health` HTTP 200, one online worker, existing `/data` volume intact. PR #33 restores connections automatically; PR #34 improves names/scoring/labels; PR #35 separates setup and shows each computer roll/move/seed action. **Solo Dara PR #30 remains parked, unmerged and NOT live; no additional Solo games.** Independent real-device visual/playthrough/reconnect testing is still outstanding.

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

## Live quality improvements

- **Reliable multiplayer recovery:** the browser retries dropped WebSocket connections using the existing protected seat token, requests read-only server state when the connection is quiet and never replays a game move for the player. Released in [PR #33](https://github.com/sirafrica92-a11y/Shithead-/pull/33), with automated disconnect/reconnect tests.
- **Clearer play screens:** player names in public game events, named Awalé finish information, Jamaican Dominoes Six Love explanation, partner teams shown while waiting, correct remaining tile and piece counts, Yoté/Dara colour labels, corrected browser title and a portable Jamaican flag. Released in [PR #34](https://github.com/sirafrica92-a11y/Shithead-/pull/34); game rules unchanged.
- **Still outstanding:** independent real-phone connection recovery, 360px/390px layout checks, and completed-multiplayer/CPU-turn real-device playthroughs. The separate setup and CPU action playback are **live in [PR #35](https://github.com/sirafrica92-a11y/Shithead-/pull/35)**; the obsolete original PR #32 was **closed unmerged** after two defects were repaired and integrated safely. No further Solo games are planned.

## Play solo — against the computer

When friends are unavailable, **Solo Play** requires no lobby, invitation or room code. It is separate from the guest multiplayer system and uses the same existing server-side game rules.

| Solo mode | Live? | Where | Notes |
| --- | --- | --- | --- |
| **Ludo** | **Live** | [Solo Ludo](https://play.shithead.games/solo/ludo) | Computer-controlled opponent; existing Ludo dice/rules |
| **Awalé** | **Live** | [Solo Awalé](https://play.shithead.games/solo/awale) | Legal sowing, capture and feeding from existing Abapa engine |
| **Dara** | **Not live — work parked** | [Draft PR #30](https://github.com/sirafrica92-a11y/Shithead-/pull/30) | Implemented and CI-tested, retained for another agent; **do not merge/deploy without renewed owner approval** |
| **Yoté, Shithead, Jamaican Dominoes** | Not implemented for Solo Play | — | Future possibilities, not a released feature |

Solo sessions currently require internet and are held in server memory. A server restart can end a solo match; offline play, persisted solo saves and difficulty selection are **not supported**. Existing multiplayer game modes are unaffected.

**Now live — social-first navigation:** Selecting one of the six game cards opens a separate selected-game screen, with game heading, name entry, Create Room / Join Room and Back to games. The existing room-code, lobby, Ready handshake and multiplayer game screens follow unchanged. The approved dark/gold design and original logo stay. Solo is a smaller secondary link on supported games.

**Now live — clearer existing computer turns:** The original server-authoritative Ludo and Awalé engines still run CPU actions automatically; new ordered action traces let the player watch rolls, movements, sowing and captures without pressing for the computer. Move history, skip playback and reduced-motion support are included. The original PR #32 lost the `api()` helpers in both Solo clients and omitted the Shithead `screen-table` from navigation; the rebuilt PR #35 restored them and passed dynamic JavaScript tests. Independent real-phone experience remains to be verified.

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

**Verified releases:** PR #35 social-first setup and existing CPU action playback passed **436 Python tests (31 warnings), five WebSocket simulator tests, three actual-client navigation/API tests, and JavaScript syntax checks** in GitHub Actions `41227370028`; Railway release `5cf59c7` reached **SUCCESS**. Original PR #32 closed unmerged as superseded. PR #33 automatic multiplayer recovery passed 426 Python tests, five simulated WebSocket tests and ten JS syntax checks; Railway `55049fa` SUCCESS. PR #34 presentation improvements passed 429 Python tests on the merged PR #33 branch (including an integration contract preventing loss of recovery code) plus JS syntax checks, and Railway `d6595d0` SUCCESS. Earlier Awalé Solo PR #29 passed 424 Python tests and ten JS checks, Railway `3854becb` SUCCESS. Dara Solo PR #30 at `c0043f2` passed **429 tests (31 warnings) and eleven JavaScript syntax checks** in GitHub Actions workflow `41215614376`, but this is a **draft, unmerged development branch**. To validate that branch separately, check it out and include `solo-dara.js` in the JavaScript checks. Do not mistake draft-only test success for deployment.

**Known verification limits:** an intermittent legacy Shithead start-tie test failure was observed on one earlier CI run, although the verified five-game release run passed. Full manual two-device/mobile-browser playthroughs for the newest games are not yet independently recorded. See [HANDOVER.md](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md) for reproducible concerns and follow-up checks. Automated green checks and a healthy server do not by themselves establish zero gameplay issues.

## Safe development and deployment

- **Production source:** `deploy/railway-shithead-games-staging`, **not `main`**.
- **Infrastructure:** Railway service `shithead-web` uses an attached `match-data` volume at `/data`. Preserve this volume and existing rooms.
- **Rules:** Owner-defined Shithead behaviour must not be replaced with assumed standard rules. Each additional game must have its own rules contract, engine and tests.
- **Release discipline:** work in a branch, inspect the changed files, run the existing regression suite and new game's full-match/recovery checks, review browser behaviour, then merge and verify the exact Railway deployment.
- **Ownership:** the project's concepts, game choices, product requirements and rules decisions are owner-led; AI coding assistance is used for implementation and testing under review.

This is an accessible **public preview** rather than a mature account-based games service. Guest room codes are not accounts; full moderation, real user accounts and wider operational safeguards are not implemented. Don't commit secrets, private credentials or personal information to this public repository.

### What's next?

The six-game multiplayer milestone and two live Solo Play modes are complete. **The owner has ended Solo Play game expansion:** Dara is the final planned computer-opponent title, with finished code deliberately parked in draft [PR #30](https://github.com/sirafrica92-a11y/Shithead-/pull/30), unmerged and not live. **Do not build Solo Play versions of Yoté, Shithead, Jamaican Dominoes or other games.** The social-first screens and clearer existing CPU turns are live. Priority now is **real-phone UX verification**, reconnection/replay checks, player feedback and encouraging friends to invite each other to rooms; maintain the existing games and rules. **Morabaraba** is a separate multiplayer research candidate only; Fanorona is excluded.

---

**[Play SHITHEAD Games](https://play.shithead.games)** · [Live application code](https://github.com/sirafrica92-a11y/Shithead-/tree/deploy/railway-shithead-games-staging) · [Platform handover](https://github.com/sirafrica92-a11y/Shithead-/blob/deploy/railway-shithead-games-staging/HANDOVER.md)


### Owner analytics, operations and demand monitoring
The owner-only dashboard code is deployed, but access remains disabled until private Railway authentication settings are configured. Preferred Google owner sign-in uses all three service variables: `SHITHEAD_GOOGLE_CLIENT_ID`, `SHITHEAD_OWNER_EMAIL`, `SHITHEAD_ADMIN_SESSION_SECRET`; configure an authorised Google JavaScript origin of `https://play.shithead.games`. The older HTTP Basic option uses `SHITHEAD_ADMIN_PASSWORD` when Google mode is not configured. Do not commit credentials or make the admin dashboard public.
Analytics records daily aggregate page loads, game starts/completions and denied room-creation attempts (not unique visitors). Owner-only Incidents, Problems and Changes registers record manual operations entries. The Railway billing date/usage/budget fields are optional **manual figures**, not linked to Railway invoices. Capacity remains 100 allocated/saved rooms (not 100 simultaneously active matches); existing joins continue at capacity. There is no real waiting list or guaranteed five-minute availability.
