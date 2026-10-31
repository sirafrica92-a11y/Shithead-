# SHITHEAD Games — Free preparation before Google Play registration

**Status at 31 October 2026:** PR [#36](https://github.com/sirafrica92-a11y/Shithead-/pull/36) is a draft on `feature/android-pwa-play-store-prep-20261031` based on the verified production branch. Latest exact-head GitHub Actions `41233623379` **SUCCESS: 447 Python tests, five WebSocket recovery tests, three client-side simulator tests and JavaScript syntax checks**. Logo-derived 192 px and 512 px maskable icons have also been generated and dimension-checked. Nothing in PR #36 has been merged, deployed or published to the Play Store. Existing web app, room storage and Railway production remain untouched.

## Goal

Do **all free preparation first**, using one shared online game service and a PWA + Trusted Web Activity. Do not sign up for a paid Google Play Console developer account before the owner is comfortable spending the **one-time US$25** fee. A Google Play Console account/app listing cannot be fully created in advance of the developer registration/payment; the finished assets and descriptions can be held locally/in this repository instead.

## Pre-payment milestones

| Gate | Assistant / coding-agent work | Owner's part | Current state |
|---|---|---|---|
| 1. PWA readiness | Review draft PR #36, verify icon sizes, offline handling and all game regressions; merge only after owner authorisation; follow `docs/RAILWAY_FIRST_CHECK.md` for production release | Approve the release after review | Code and CI complete; draft PR, not yet live |
| 2. On-phone PWA | Verify manifest, HTTPS, real icon and installation flow after deploy; write precise test instructions | Install via Chrome **Add to Home screen / Install app** and test it on a physical Android phone | Not tested on phone |
| 3. Store identity | Propose compliant title, short/full descriptions, category, keywords, store graphics; do not rename the user's original artwork or gameplay | Decide public Play title, confirm the permanent Android package ID, support email, contact/brand details, age audience and whether ads are planned | Decisions pending; working title only |
| 4. Legal and trust | Audit actual server data collection; draft a privacy policy and Google Play Data safety *working sheet*, then add policy URL only once approved | Review for accuracy, confirm public contact email and any organisational details, approve publication of privacy notice | Not complete |
| 5. Store artwork | Prepare 512px icon, 1024×500 feature graphic plan and compliant actual-game screenshot layouts | Approve visuals and capture/provide phone screenshots of real games if needed | Icons ready; feature graphic and screenshots pending |
| 6. Android project | Generate Bubblewrap/Android project from the *deployed* PWA, set Android 16/API 36 target or higher, verify signing and package settings, prepare AAB build instructions | Generate and **privately retain/back up** an upload signing key on a computer under your control; never put keys or passwords in chat or GitHub | Not built |
| 7. Prepayment test | Run Android build checks where tools permit; confirm browser-to-app shared rooms, same-seat reconnection, three Solo modes, Android Back button, permissions, and airplane-mode behaviour | Install and test a **sideloaded APK** on a real phone, ideally test with a friend on web, report/screenshots | Not performed |
| 8. Play testing recruitment | Draft 14-day closed-test instructions and issue template | Identify at least **12 willing Google-account testers** before the fee, to reduce delays afterwards | Not begun |
| **PAYMENT GATE** | Deliver exact build package, listing draft, screenshots and readiness checklist | Register paid Google Play Console account and pay one-time **US$25** | **No payment yet** |

## What cannot be completed until the paid account exists

- Create the actual Google Play Console app record and upload an Android App Bundle to an official Play testing track.
- Complete Google Play developer identity/device verification under the account owner's credentials. For new personal accounts Google requires real-device verification using the Play Console mobile app.
- Complete the final Play App Signing setup and verify the **actual Google Play app-signing SHA-256 certificate** in the website's `/.well-known/assetlinks.json` (can pretest local developer certificate earlier, but final Play fingerprint may differ).
- Finalize Play Console Data safety, ads, age-targeting/content rating and store fields (we can draft them before payment).
- Start the required Google Play *closed testing* window for new personal accounts: at least 12 opted-in testers for 14 uninterrupted days; apply for production access after, subject to review.
- Submit for Google review, obtain approval and publish. No listing, ranking or downloads can be promised.

## Owner decisions to settle at no cost

1. **Store-facing name**, provisionally `SH Games: Play With Friends` — keep the original SHITHEAD Games branding and six game rules on the website, subject to Play policies.
2. **Permanent package ID**, suggested only (not reserved): `games.shithead.play`. It must be unique and carefully checked before official release; do not assume we own it.
3. **Developer type**: individual vs existing verified organisation (Google requirements differ).
4. **Public support email**, which may become visible in the listing. Do not supply private login credentials.
5. **Audience/monetisation:** intended age range, free download, ads vs no ads, in-app payments vs none.
6. **Privacy/data handling:** confirm whether to retain current basic usage analytics, how to handle player names/room codes, support requests and abuse reporting. Reconcile against the actual code before policy publication.
7. **Testers**: collect at least 12 willing participants' Google email addresses *privately*, not in the public repository. Ideally recruit extras.

## Release guardrails

- **No merge or Railway deployment without owner approval.** Follow the exact GitHub production branch first, Railway exact-SHA SUCCESS and original `match-data` at `/data`. Do not create a new backend.
- No new Solo games; web player pool and rules stay identical.
- No signing keys, passwords, phone numbers, private tester lists or payment credentials in commits.
- Do not pretend an APK/AAB has been built or a real Android test completed until verified.
- A Google Play **free limited-distribution** Android developer route is not a substitute for a publicly discoverable Google Play Store listing.

Official references:
- Registration fee: https://support.google.com/googleplay/android-developer/answer/6112435
- Closed testing: https://support.google.com/googleplay/android-developer/answer/14151465
- Device verification: https://support.google.com/googleplay/android-developer/answer/14316361
- Current API-level requirements: https://developer.android.com/google/play/requirements/target-sdk
- Trusted Web Activity setup: https://developer.chrome.com/docs/android/trusted-web-activity/quick-start
