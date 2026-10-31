# SHITHEAD Games — Android / Google Play

**Status:** PWA/TWA preparation only, NOT a built Android application or a Play Store submission. This folder deliberately contains no signing key, credentials, production app bundle or generated Android project. The existing browser/Railway games remain the source of truth.

## Architecture
- Keep the existing FastAPI + WebSocket server and all six multiplayer engines + three existing Solo modes on `play.shithead.games`.
- A **Trusted Web Activity (TWA)** runs the same HTTPS web application fullscreen in a Chrome-backed Android app. Native Android and web players share room codes and authoritative game state. No second backend or separate player pool.
- `/manifest.webmanifest` provides the app name, launch path, scope, colours and source-logo icons.
- `/service-worker.js` uses **network-only** navigation; when offline it tells the player that online play is unavailable. Do NOT cache authenticated rooms, game state, tokens, APIs, or playable content.
- No push notifications, ads, analytics SDK or intrusive permissions are included.

## Build when the PWA branch has been tested and deployed
1. Install Node.js 18+, a suitable JDK and Android SDK on a trusted developer computer, using the current official Bubblewrap guide.
2. Install the Bubblewrap CLI: `npm install -g @bubblewrap/cli` (not with sudo).
3. Run `bubblewrap init --manifest=https://play.shithead.games/manifest.webmanifest` in a clean **local** directory. Check app label, icon, domain, package ID and target SDK. As of October 2026, new Play Store apps must target **API 36 or later**, subject to current Play rules.
4. **Owner must select and confirm the permanent package ID** (e.g. `games.shithead.play`, only a suggestion), create/store signing credentials privately and own the Play Console registration. Do NOT upload signing files or passwords to GitHub, Railway, screenshots or chat.
5. Run `bubblewrap build` (or build through Android Studio) to produce a signed test APK and Android App Bundle. Test the APK on a real Android device **before** using the bundle in Play Console.
6. In Play Console, use the actual **app-signing certificate SHA-256** issued/accepted for the released app (not an invented value); run `bubblewrap fingerprint add` / `bubblewrap fingerprint generateAssetLinks` and serve a valid `/.well-known/assetlinks.json` from the existing site. A missing/wrong digital asset link can make the TWA show a Chrome toolbar rather than fullscreen.
7. Prepare policy-compliant listing title, promotional artwork, screenshots of real gameplay, privacy policy, content rating, Data safety declaration, tester access and feedback. Do not guarantee Google approval or use profanity in marketing metadata without checking Google policy.
8. Validate on Android that the website, rooms, saved seats, Back behaviour, six games, the three Solo modes, reconnection, orientation, screenshots and Play-installed updates work as expected. New Android code should not be merged into the Railway web deployment unless it only changes public web metadata.

## Signing and ownership
Release key material must remain off-repo and managed by the owner. When enrolled in Play App Signing, use the Play **app signing** certificate fingerprint for verified installs; the upload certificate can differ. No public `assetlinks.json` is added until the actual package name and certificate hash are known.

## Release gates
- PWA manifest JSON and icon dimensions verified.
- Existing full Python, WebSocket and JS regression suites pass.
- Mobile installability audit (Chrome DevTools / Lighthouse equivalent) and verified service-worker registration.
- Real Android TWA APK test (not yet done), browser-to-app multiplayer test (not yet done), actual app link validation (not yet done).
- Play Console identity/payment/closed testing (owner-controlled, not yet done).
- An Android version/package/signing convention and owner review before production.

**Production is NOT changed by this branch until the owner approves a tested merge.**

Official references: https://github.com/GoogleChromeLabs/bubblewrap and https://developer.android.com/google/play/requirements/target-sdk
