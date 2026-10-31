# SH Games Android / browser compatibility testing

**State: NOT YET PERSONALLY VERIFIED.** The GitHub Android CI build, where successful, verifies an APK can be assembled; it does not play through games or verify domain association.

| Check | Device(s) / method | Status | Notes |
| --- | --- | --- | --- |
| Live PWA installed from Chrome | Android phone | NOT TESTED | Chrome > Install app / Add to Home screen; icon and standalone launch |
| Site loaded inside debug APK | Android phone | NOT TESTED | Signed test APK; toolbar may show before asset link |
| Same backend and lobby across app/browser | App on device A + Chrome device B | NOT TESTED | Fresh room only, do not touch real matches |
| App creates room, Chrome joins by 4-character code | Two devices | NOT TESTED | Ready and verify names |
| Chrome creates room, app joins | Two devices | NOT TESTED | Opposite direction |
| Shithead turns and reconnect | Two devices | NOT TESTED | Preserve current house rules, never change them for test |
| Ludo 2/4 player and reconnection | Two devices | NOT TESTED | Dice, movement and rematch |
| Awalé, Dara, Yoté | Two devices | NOT TESTED | Each rules-specific board and valid turn |
| Jamaican Dominoes partner/Cut Throat | Four devices or agreed controlled players | NOT TESTED | Team setup and correct 4-player lobby |
| Solo Ludo, Solo Awalé, Solo Dara | Android phone | NOT TESTED | Only three implemented solo modes |
| Background / sleep / reopen | Android phone | NOT TESTED | Check reconnect, no unexpected second seat |
| Network drop / return | Android phone | NOT TESTED | Should show offline notice; no offline play |
| Android Back / multitask / rotate | Android phone | NOT TESTED | No accidental exit or lost turn |
| Screen width, readability, 360px/390px | Android phones | NOT TESTED | Capture real screenshots |
| Asset Links TWA fullscreen verification | Release-signed app and live site | BLOCKED | Requires owner-selected package ID and actual Play signing fingerprint |
| Friendly tester feedback | At least two external phones | NOT TESTED | Document issues before store release |
| Formal Play closed test | At least 12 opted-in eligible testers / 14 days, when applicable | BLOCKED | Requires owner Play Console setup |

### Record each test
Date (UTC): ___
Tester/device/Android version: ___
App APK workflow run and package version: ___
Game/room scenario (avoid publishing real room code/token): ___
Pass/Fail/Blocked: ___
Evidence/screenshot (redacted): ___
Reproduction and fix link: ___

### Release gate
No Google Play submission until real-device app/browser cross-play is verified, the owner confirms permanent package/title/contact and signing, privacy/data-safety claims are substantiated and official Play testing requirements are fulfilled. No production game changes are authorised by this test plan.
