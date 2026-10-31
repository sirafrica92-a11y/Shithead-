# Privacy notice and Google Play Data safety — REVIEW DRAFT

**Not an approved privacy policy, not published to a public URL and not a completed Play Console declaration.** Prepared against the repository's application/analytics/room implementation on 31 October 2026. Verify hosting logs, retention, legal basis, data processors, support contact, cookies and compliance with current policies before publication.

## Draft visitor-facing text

**Who runs the service** — [Owner/public legal name or trading name to confirm], [public support and privacy email to confirm]. The service is accessible at https://play.shithead.games and may be opened from an Android app.

**What is collected or processed when you play**
- The name/nickname you choose for a room, its four-character room code, your seat/session recovery token (stored/handled as a token or token digest), game participation, moves and match state, so matches can be created, played, reconnected and recovered.
- Network and request security data, including IP addresses or other request information, may be processed by the app, the hosting platform and intermediaries to connect players, serve requests and limit guessing of room codes. **Actual server/hosting log content and retention still require verification.**
- Coarse, aggregated statistics: page views, referral channel categories, room creation, joining, match starts/completions and room-capacity refusals. The app analytics database does **not** store player names, tokens, room codes, raw IPs, full referrer URLs or visitor IDs.
- For the private owner administration only, a separate Google login can be enabled later; it is not required to play. The current production Railway environment has no enabled Google OAuth variables.

**Why we use this data** — to provide multiplayer rooms, authenticate each seat for reconnection, persist current matches, protect room lookups, troubleshoot incidents and count aggregate game usage. [Controller must confirm the lawful bases under UK GDPR, where applicable.]

**Sharing and services** — Our hosting provider Railway and connected infrastructure may process technical data needed to operate the site. An Android Trusted Web Activity uses the browser on the device to display this website. [Verify exact processors, hosting region and any additional services before publication.]

**Storage** — Room/seat/match data persist using SQLite on a Railway volume, whereas Solo games use temporary server memory. Aggregated daily analytics and owner operational records use separate SQLite storage. Browser storage may retain seat recovery information. **No verified retention/deletion schedule is established yet; owner must agree to one before publication.**

**Controls and contact** — Players can avoid using a real name when choosing a nickname. To ask about personal data access, deletion or other rights, contact [approved public privacy email]. [Define how the owner will find and honour requests relating to room data and logs, including limits.]

**Children, international transfers, changes** — [Owner must verify intended age audience, any age-restricted features, hosting/data-transfer terms and effective date before public release.]

## Play Console Data safety pre-assessment — not final checkboxes

| Potential data | Purpose | Status / check before declaring |
| --- | --- | --- |
| Player nickname | Multiplayer display and seat recovery | Confirm whether Google classifies as personal information and how long it persists |
| Room, seat and gameplay events | App functionality, fraud/security, gameplay | Verify persistence, device/browser storage and whether externally accessible |
| Seat token or digest | Authenticate and restore one seat | Verify browser storage/security and handling |
| IP / HTTP request logs | Networking, host operations, rate-limit abuse | Validate Railway/proxy logging and retention before the form |
| Aggregate engagement counts | Product analytics | App-side analytics excludes raw player identifiers; check processors |
| Owner Google account details | Private administration, if activated | Feature is currently not enabled; document if activated |
| Advertising identifiers | None intentionally collected in app code | Confirm libraries/Android Browser Helper, default Chrome behavior and third parties |
| Payment information | None collected by guest games | Verify no third-party billing introduced before release |

**Never answer all Data safety questions 'No' merely because no tracking SDK was added.** Re-check network logs, SDK library disclosures, transfer, encryption, collection vs sharing, privacy URL availability, user data deletion rules and relevant jurisdictions. This repo's analytics privacy guarantee only describes the aggregate database, not the entire hosting chain.

## External references
- Google Play user data: https://support.google.com/googleplay/android-developer/answer/10144311
- Google Play Data safety: https://support.google.com/googleplay/android-developer/answer/10787469
