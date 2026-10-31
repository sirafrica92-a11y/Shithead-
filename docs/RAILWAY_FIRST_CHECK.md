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
- Owner correctly reminded the assistant that **updating Railway's source branch first** has resolved similar failures before, and that this must be the initial check rather than a lengthy reauthorisation checklist.
- The assistant called `connect_service_source` for this existing service using the production branch. Railway accepted the request and queued another deployment `4c4f42fb-0b42-4c02-a32b-1b5c14bd0204`, for commit `20f619b...`.
- **Important nuance:** a subsequent `describe_environment` still returned `source.branch: null`, and the deployment was **still QUEUED**. So it was a valid first corrective action, **not proof that the outage was resolved**. Verify again; do not assert this step fixed it until the correct SHA is SUCCESS.
- **Correction and resolution:** Updating the GitHub deployment branch and reconnecting Railway are different. The owner explicitly corrected the earlier confusion. PR #25 commit `20f619b7037f7d346cd8785240f9a78518bdb2e4` later reached Railway **SUCCESS** via `5bfd40d8-f699-4e9b-879c-09673fbd937a` at 13:09 UTC. PR #26 merged as `39d289b767fe6ee7080f00d6c39bc85599cf2564`, and Railway `4d3b6c28-b05f-4d8b-a26a-10e1d6415efd` reached **SUCCESS** at 13:32 UTC. One worker online and same `/data` volume preserved; Google owner access awaits secure environment configuration and live phone UI checks remain outstanding. One earlier WebSocket `502` at 13:03 UTC preceded this final release.

**Definition of done:** Confirm exact expected SHA has a successful Railway deployment; healthy one-worker service, working public website and original logo/six game choices, functioning player create/join/reconnect and existing `match-data` volume still attached. Record the real deployment SHA, ID and verification outcome in the living handover.

**Remember the lesson: UPDATE THE GITHUB DEPLOYMENT BRANCH FIRST. CHECK RAILWAY'S EXISTING SOURCE. VERIFY THE EXACT SHA. PROTECT THE LIVE SERVICE.**
