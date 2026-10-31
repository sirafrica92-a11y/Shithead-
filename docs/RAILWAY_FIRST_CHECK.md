# Railway deployment — FIRST CHECK on every release

**STOP AND READ BEFORE ANY RAILWAY CHANGE.** The recurring mistake was confusing an **update of the GitHub production DEPLOYMENT BRANCH** with a Railway source reconnect. **Merge the approved release into the existing GitHub deployment branch FIRST; never reconnect Railway merely because there is a new commit.**

## Identity — never substitute `main`
- Repo: `sirafrica92-a11y/Shithead-`
- **Production branch:** `deploy/railway-shithead-games-staging` (the `main` branch is not the application)
- Project: `Shithead Games Test` (`03fa414d-cf8b-4932-83d1-bec9c413e6e1`)
- Service: `shithead-web` (`0f1ad0cd-602a-488a-a378-d91f4bb7b46d`)
- Environment: `production` (`0206be2e-8ecf-4c24-8d62-364e7f1c7163`)
- Domain: https://play.shithead.games
- **Persistent match data:** existing volume `match-data` at `/data`. Never detach, replace, recreate, wipe, restore or relocate this volume as a deployment fix.
- One live worker; replacing a running deployment can interrupt real-time matches.

## Exact GitHub-branch-first release workflow

1. **Inspect before acting:** read `HANDOVER.md`, approved PR changes and tests, GitHub production-branch HEAD, last successful Railway SHA, pending/queued deployments, service state, source branch, volume and `/health`. Preserve current successful deployment while work is queued.
2. **Update GitHub production branch FIRST:** merge the approved, CI-passing PR into `deploy/railway-shithead-games-staging` and independently verify its HEAD equals the intended release SHA. This is **not** a Railway source reconnect. If already merged, do not push a dummy commit.
3. **Check existing Railway source:** it must follow `sirafrica92-a11y/Shithead-` on the exact deployment branch. When correct, **do not reconnect**. Only if an actual mismatch is confirmed, correct the same service using `connect_service_source` with repo + branch and **without `commitSha`**. The environment screen may report `branch: null` even when deployment metadata correctly identifies the branch; compare evidence first.
4. **Watch the intended release SHA:** inspect Railway deployments and follow `QUEUED` → `BUILDING` → `DEPLOYING` → `SUCCESS`. A queued build is not live. If there is no new deployment, check auto-deploy triggers, CI permissions/approvals and Railway queue. Railway MCP `redeploy` reuses an existing build and **does not deploy the new GitHub SHA**; never treat it as a source update. Do not repeatedly reconnect, restart, create another service or make dummy commits to clear a queue.
5. **Verify safe release:** confirmed exact SHA `SUCCESS`, one healthy worker, `/health`, homepage, original jester and six game choices, room create/join/reconnect, attached `/data`, private owner routes and no new failures. Do not alter real production rooms to test. Clearly label any unavailable post-release browser check **unverified**.
6. **Update living handover:** record exact merge commit, Railway deployment ID/status, CI evidence, timestamp, any risk and follow-up; stage docs separately so unrelated documentation does not cause unnecessary production redeployments.

## What actually happened on 31 October 2026

- GitHub PR #24 homepage and PR #25 analytics/capacity were safely merged. PR #25 created production commit `20f619b7037f7d346cd8785240f9a78518bdb2e4`; CI at that commit passed.
- Railway was still successfully serving the **previous six-game build** `1240844275556784030e923706eb8dcfe143cabc`. Two newer deployments sat at `QUEUED` without build logs.
- Owner correctly reminded the assistant that **updating the actual GitHub deployment branch first** was the missing workflow step; this is distinct from reconnecting Railway's already-correct source. The assistant initially confused these operations.
- The assistant called `connect_service_source` for this existing service using the production branch. Railway accepted the request and queued another deployment `4c4f42fb-0b42-4c02-a32b-1b5c14bd0204`, for commit `20f619b...`.
- **Important nuance:** a subsequent `describe_environment` still returned `source.branch: null`, and that deployment was **still QUEUED**. The reconnect had not proven anything and was unnecessary for routine releases; the correct routine sequence is **merge into the GitHub deployment branch, then verify Railway's deployment SHA**.
- **Correction and resolution:** Updating the GitHub deployment branch and reconnecting Railway are different. The owner explicitly corrected the earlier confusion. PR #25 commit `20f619b7037f7d346cd8785240f9a78518bdb2e4` later reached Railway **SUCCESS** via `5bfd40d8-f699-4e9b-879c-09673fbd937a` at 13:09 UTC. PR #26 merged as `39d289b767fe6ee7080f00d6c39bc85599cf2564`, and Railway `4d3b6c28-b05f-4d8b-a26a-10e1d6415efd` reached **SUCCESS** at 13:32 UTC. One worker online and same `/data` volume preserved; Google owner access awaits secure environment configuration and live phone UI checks remain outstanding. One earlier WebSocket `502` at 13:03 UTC preceded this final release.

**Definition of done:** Confirm exact expected SHA has a successful Railway deployment; healthy one-worker service; public homepage and original logo/six game choices; working player create/join/reconnect verified on real devices where available; existing `match-data` volume attached. At 14:10 UTC, live Railway HTTP logs recorded `200` for `/` and all six game client JavaScript files after admin deployment. Manual multi-device gameplay and private Google login remain unverified, so do not claim them passed. Record all verification evidence and open risks in the living handover.

## 31 October 2026 — PR #33 release confirmed; exceptional trigger repair

- Merged tested [PR #33](https://github.com/sirafrica92-a11y/Shithead-/pull/33) into `deploy/railway-shithead-games-staging`, **verified GitHub HEAD `55049faefb9bce195f73c70ef72157b93da8c0e4` first**. CI: 426 Python tests, 5 simulated socket tests and 10 JS syntax checks, PASS.
- Railway still showed only the prior deployment `f6303b5a-989f-4a04-9534-f1e7db99810f` at `3854bec...`, **no queued/pending deployment**, while `describe_environment` showed source repository but `branch: null`; service volume remained live on `/data`. Verified new SHA, repo, service, no staged patch, and original volume **before changing anything**.
- **Exceptional, evidence-based fix:** called `connect_service_source` ONCE on existing `shithead-web` with `repo: sirafrica92-a11y/Shithead-`, `branch: deploy/railway-shithead-games-staging`, **without `commitSha`**. No new service, volume, database, or source commit was created. Railway immediately built **exact `55049fa...`**, deployment `d17f89c8-d923-4004-b714-f822f0496f0a`, reached `SUCCESS` with `/health` HTTP 200 and one healthy worker; original `match-data` volume still attached.
- **Future releases:** This was a one-off repair after a verified missing trigger; **do not repeat reconnects as a release step**. Merge CI-passing code into GitHub deployment branch, verify its HEAD, watch for *new* SHA and check missing-build causes first. `branch: null` alone is NOT proof that reconnecting is needed; past successful deploy metadata also showed the correct branch while this field was null. When the trigger works, leave service source untouched. Never use Railway MCP `redeploy` to fetch a new commit; it reuses an old build.
- Owner prioritises live rooms: one worker with persistent `/data` must remain intact. Test on staging/synthetic room wherever possible, do not disturb production matches. Docs-only updates belong in a separate PR to avoid unnecessary redeploys.

### PR #34 second release: missing trigger happened again (31 Oct 2026)

- **Order used:** GitHub PR #34 passed CI on **PR #33 merged production base** (429 tests, syntax checks), merged into the existing production deployment branch at `d6595d07a584537bdc2f0941b1016e0fc1fdf679`, independently confirmed GitHub HEAD FIRST. Expected Railway deployment **did not appear** (no pending work). Existing `shithead-web` showed repo but branch null; original `/data` volume and prior successful release were intact.
- After checking the runbook and **actual no-build condition**, a second **exceptional source correction** on the same service, same repo and production branch, without `commitSha`, queued Railway deployment `a6b8e8cf-8c1f-478b-85a5-d9eba78b60b2`; its exact SHA `d6595d0...` reached **SUCCESS** at 17:55 UTC with HTTP 200 `/health`, one worker and attached original volume.
- **Important unresolved operational problem:** GitHub auto-deploy is NOT reliably triggering on branch updates in the current Railway service. *Do not mistake a connector source reattachment that queued one build for permanent trigger repair.* Next owner/agent should inspect Railway service **Settings → Source / GitHub Integration → branch and automatic deployments (Enable)**, GitHub App permissions and installation access to `sirafrica92-a11y/Shithead-`, missing/skipped deployments and watch paths. Railway's official [GitHub autodeploy troubleshooting](https://docs.railway.com/deployments/github-autodeploys) recommends those checks. No tool-accessible switch has been verified, and the root cause is not proven. Do not routinely reconnect or redeploy an old build; perform a source correction only after confirming the exact new GitHub SHA, lack of new deployment and preserved service/volume in an explicit safety check.
- **Pending:** Repeat a normal future code-push deployment to establish that auto-deploy is fixed, rather than assuming it. The owner strongly requires this **GitHub branch first / exact Railway SHA** sequence on every release.

**Remember the lesson: UPDATE THE GITHUB DEPLOYMENT BRANCH FIRST. CHECK RAILWAY'S EXISTING SOURCE. VERIFY THE EXACT SHA. PROTECT THE LIVE SERVICE.**
