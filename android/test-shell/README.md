# Android preview shell — phone testing only

This is a minimal **Android Browser Helper Trusted Web Activity launcher** around the **existing** live site at https://play.shithead.games. It has no duplicate game engine or backend and uses no app-owned user accounts.

## Hard boundaries
- Preview application ID **`games.jestertable.preview` is temporary** and is NOT an approved permanent Play identity.
- Launcher label **SH Games (Test)** is temporary. The existing website/logo remain unchanged.
- Compiles and targets API 36. Requires a compatible Android browser, internet and a working live Railway site.
- **Only debug signing:** the GitHub-hosted runner creates its own temporary debug key. The APK is for sideload testing and **must not be uploaded to Google Play** or called a release build. Builds from different CI runs may not install over each other because their keys differ; uninstall the prior preview first if Android reports a signature mismatch.
- **Expected limitation:** until a matching production certificate and `/.well-known/assetlinks.json` are installed on the domain, Android Browser Helper may open a Chrome Custom Tab **with a toolbar** instead of a verified fullscreen TWA. This is NOT evidence the final store app has been verified.
- No permanent signing keys, secrets, OAuth credentials, billing changes, Google Play registration, new permissions beyond INTERNET, or Railway changes.
- The logo resource references the **unchanged repository original jester logo**. Do not replace it with generic or newly invented art.

## How to get the APK
1. Open the **Android preview APK (test only)** GitHub Actions workflow on this feature branch. Wait for a successful run (do not treat queued/building as passed).
2. Open that run's **Artifacts** section and download **`sh-games-preview-debug-apk-NOT-FOR-PLAY`**.
3. Unzip it on the phone, install **`app-debug.apk`** through Android's Files app, and only grant install-from-this-source when the OS prompts. Disable that permission after installation.
4. Open **SH Games (Test)**. It should load the same server, homepage, six multiplayer games and three existing Solo modes. A visible browser toolbar is expected until Digital Asset Links verification is done.
5. On a *second device* open https://play.shithead.games in Chrome. Create a fresh private room using one device and join using the other. Check Ready, game turns, same room state, refresh/reconnect, rematch, and app/browser player identity. Never manipulate real users' existing rooms.
6. Test Android Back, network loss and return, rotated screen, app sleep/reopen, all six multiplayer screens, and each existing Solo mode.
7. Record the APK workflow run, observed results and device OS in `android/PHONE_TEST_MATRIX.md`. Do not mark untested items PASS.

## Developer build
With JDK 17, Gradle 8.11.1, Android SDK platform 36 and Build Tools 36.0.0:

```sh
gradle --project-dir android/test-shell :app:assembleDebug --no-daemon
```

The result is `android/test-shell/app/build/outputs/apk/debug/app-debug.apk`. Gradle's debug signing is ephemeral for CI and not the owner's Play release signing setup.

## Future production path — separate owner-controlled release
Select app title/package ID and support email; create the owner-controlled signing/upload credentials and Google Play Console account; generate the owner-controlled App Bundle; use the **Play app-signing certificate fingerprint**, not an invented or CI debug fingerprint, for production Digital Asset Links; publish a reviewed privacy page; complete Data safety and age ratings; test on real devices and in closed testing. Never reuse this temporary debug package or key as the permanent store identity.
