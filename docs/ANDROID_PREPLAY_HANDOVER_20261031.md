# Android pre-payment handover — 31 October 2026

## Approved Play Store name

- **SH: African & Classic Games** — owner approved, 27 characters, **store-facing only**.
- Play listing draft: [android/PLAY_STORE_LISTING_DRAFT.md](../android/PLAY_STORE_LISTING_DRAFT.md).
- Short and full descriptions reference the implemented games naturally: Ludo, Awalé (Oware-style), Dara, Yoté, Jamaican Dominoes, and the custom card game (without profane store-facing text).
- Existing Shithead website, jester artwork and actual game names/rules **must not be silently renamed**. Google Play listing artwork/screenshots still require a policy check and owner approval.
- Permanent Android application ID, public support email, signing keys, Play Console account and privacy/data-safety final approvals **not yet chosen**. Do not make these decisions on the owner's behalf.

## Live website

- Source of truth is `sirafrica92-a11y/Shithead-`, production code on `deploy/railway-shithead-games-staging`, **not** the default `main` README-only branch.
- [PR #36](https://github.com/sirafrica92-a11y/Shithead-/pull/36) PWA release merged as `aae4f67b3384696002d2e20f5db459a169875865`.
- Railway production deployment `5e8ad18b-9322-4438-8813-57d13e53dcad` reached **SUCCESS** for that exact SHA. No Android preview branch code has been deployed to Railway.
- Preserve existing `match-data` volume at `/data` and live games; follow [Railway First Check](./RAILWAY_FIRST_CHECK.md) before future deployments.

## Android APK preview — SUCCESSFUL BUILD, not phone-tested

- Branch: `feature/android-preview-test-kit-20261031` (separate from production).
- GitHub Actions [run #41240788621](https://github.com/sirafrica92-a11y/Shithead-/actions/runs/41240788621) completed **SUCCESS** on commit `010fc5e79783f9405db23de5b6245aad57f5061c`.
- Uploaded artifact: `sh-games-preview-debug-apk-NOT-FOR-PLAY`, artifact ID `13057003877`, about 4.5 MB ZIP; GitHub shows expiry **14 November 2026**. Download through the run's **Artifacts** section; unzip to get `app-debug.apk`.
- CI verifies Android assembly and APK archive integrity. It **does not** verify physical install, browser/app room joining, rules, saved seats or fullscreen site verification.
- Earlier failures fixed on the preview branch: locate the preinstalled `sdkmanager` explicitly, and set `android.useAndroidX=true`.
- Preview app label is `SH Games (Test)`; test-only package ID `games.jestertable.preview`, signed with ephemeral debug credentials. Do **not** upload that APK to Google Play or reuse its signing key/package ID for release.
- Until owner-controlled certificate/Digital Asset Links setup is complete, a Chrome Custom Tab toolbar is expected and is not a release defect.

## Next steps before payment

1. Owner installs the **live PWA** on Android from `https://play.shithead.games` and verifies home-screen launch.
2. Owner downloads the successful preview ZIP on a trusted device, extracts and installs the **debug APK**, then opens it. Grant temporary install-from-source permission only for the APK install.
3. Test fresh rooms between APK on phone A and browser on phone B, in both directions. Check Ready/turns, reconnect, rematch, screen fit, offline messaging and the **six multiplayer / three solo** modes. Never interfere with real users' rooms.
4. Record actual observations in [android/PHONE_TEST_MATRIX.md](../android/PHONE_TEST_MATRIX.md), with no false PASS entries.
5. Prepare/policy-review the approved Play title, original-brand icon/feature graphic, genuine screenshots, public privacy notice and Data safety working sheet. Verify all statements against real hosting/processors before approval.
6. Owner selects permanent package ID, public support identity, intended age range and signing arrangement; owner privately controls signing material.
7. Only when financially ready: Play registration/payment, account identity/device verification, the required tester programme (where applicable), app bundle, Play App Signing certificate association, final Data safety declarations, Google review and publication.

**Hard boundary:** An APK being built and hosted as a GitHub artifact is **not** a Play release, physical-phone test, verified production TWA, or proof of browser/app multiplayer. No spend, production re-deployment or game-rule modifications are authorised by this handover.
