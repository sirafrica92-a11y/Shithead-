# Ludo integration review — 30 October 2026

Owner requested review and safe merge of PR #13 into the existing Shithead app,
keeping its original logo and a simple homepage like the supplied reference.
Reviewed starting head: 38633d6257d866f6dc4c8831d3386d52eb5a3345.
Target: deploy/railway-shithead-games-staging (9d9ddfe).

## Changes from reviewed head

- server/app/static/index.html: restore a prominent unaltered original logo,
  Shithead title, simple two-game selector, name and room buttons; add a visible
  Ludo connection/action status. Small inline SVG game icons avoid missing emoji.
- server/app/static/client.js: route Rules to the selected game and return to the
  originating screen; expose transport errors on Ludo; use existing saved-seat
  reconnect/sync behaviour for Ludo Refresh.
- server/tests/test_ludo_release_safety.py: late joins and host finish/restart,
  finished-game switching with persisted seat credentials, server-owned dice,
  duplicate roll protection.
- scripts/qa_ludo_browser.py: repeatable full browser matches with separate
  mobile/desktop browser contexts, reload, disconnected refresh, winner and rematch.
  Optional Playwright dependency; not required by the app or Python unit suite.
- .github/workflows/python-tests.yml: syntax-check the Ludo client as well.

The Shithead engine, existing card rules and original logo assets are unchanged.
No production room database was accessed or modified by QA.

## Executed evidence

- Existing full suite: 339 passed. Initial local failures were caused by the
  environment's SOCKS proxy dependency; rerunning with proxy variables removed
  for local loopback tests passed. No application changes were made for this.
- Additional release regression tests: 2 passed (341 total test cases).
- Chromium browser: full two-player match, 291 ordinary roll/move actions.
- Chromium browser: full three-player match, 389 actions.
- Chromium browser: full four-player match, 540 actions.
- Each browser match: page reload restores seat, disconnected Refresh reconnects,
  correct named winner appears, unanimous rematch starts. Zero JS page errors.
- Mobile emulation 390px plus desktop contexts; no horizontal overflow.
- Final homepage image inspected; both home Rules paths and back navigation pass.
- node --check on both client.js and ludo.js; git diff --check pass.
- Pre-review GitHub CI at 38633d6 passed; final-head CI must pass before merge.

## Limits

Browser checks use automated isolated Chromium contexts and mobile emulation,
not physical phones or two humans. Railway rollout/live smoke is separate from
merge verification. Existing dependency deprecation warnings remain non-fatal.
