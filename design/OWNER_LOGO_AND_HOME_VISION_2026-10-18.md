# SHITHEAD — owner-approved logo and home-screen vision

**Date received:** 18 October 2026  
**Source:** Two reference images supplied directly by Africa in ChatGPT.  
**Status:** **DESIGN DIRECTION ONLY — NOT IMPLEMENTED**. Preserve all existing game rules and logic.

## 1. Logo reference (original supplied image)
- Supplied as `1000103883.png` (actual source file contains JPEG image data), 1536 × 1536.
- Square composition with four ivory playing cards arranged like a fan/cross around a dominant central black card.
- Centre artwork: a theatrical jester face, cream mask, red-and-gold two-pointed hat, small gold bells, asymmetrical smile.
- Top-left card: dark **II** and broken black circular arrow.
- Top-right card: red **3** and three curved red cycle arrows.
- Bottom-left card: red **7** and stacked downward red chevrons.
- Bottom-right card: black **X** and split/slashed black shape.
- Background: near-black charcoal grain; playing cards warm ivory with gentle shadows.
- Feel: premium, intriguing, slightly mischievous; recognizable at small mobile-icon sizes.
- **Do not reinterpret the artwork's card marks as changes to canonical gameplay rules.**

## 2. Mobile home-page reference (original supplied image)
- Supplied as `1000103884.png` (actual JPEG data), 1024 × 1536 portrait.
- Dark charcoal almost-black textured background, subtle warm highlights/sparks.
- The same logo artwork centered at the top, followed by a large **SHITHEAD** bold metallic-silver italic/slanted wordmark.
- Subtitle: **Mobile Multiplayer Card Game**, small grey type.
- Central translucent dark rounded panel with faint border:
  - Caption **ENTER YOUR NAME**;
  - Name field placeholder **Player Name**;
  - Two prominent side-by-side actions **Create Room** (light silver) and **Join Room** (dark charcoal).
- Separate centered rounded **Rules** button lower down.
- Generous margins, legible text, high touch-target contrast, stacked layout suitable for mobile.

## 3. Implementation contract for the builder
- **These references are the owner's desired visual identity and lobby/home screen direction.**
- Preserve existing W1 turn logic, W2 pile-pass logic, W3 ordinary-play work, W4 lobby room behavior and any active branch/worktree; design implementation must be a distinct reviewed task.
- Layout should adapt to narrow phones; keep text entry accessible, controls clearly labelled, and small icon/brand variants legible.
- The **Create Room** and **Join Room** labels describe intended home-screen actions. Do not claim they are already wired or working in the app until the W4 implementation is actually verified.
- Do not silently invent the Rules page content; source canonical rules from owner-approved repository documents.
- Prefer implementing from the **actual supplied reference files**, not making an AI-generated approximation. Check licenses/provenance before eventual commercial publication if needed.

## 4. Original supplied reference images and integrity

The original two images were attached in the 18 October 2026 conversation and retained **without alteration** in the owner-facing ChatGPT reference bundle `shithead-brand-home-vision.zip`. This GitHub design note records the intended look and filenames, **but does not embed the original image bytes**. Import the actual attachments or bundle into `design/references/` during the approved asset-ingestion step rather than substituting inaccurate recreations.

| Intended repo asset | Dimensions | JPEG SHA-256 |
| --- | --- | --- |
| `design/references/shithead-logo.jpg` | 1536 × 1536 | `e74983544f46b887aca6ed1772b42d7fdb54356d6102d3a41e3df0cdf4ea8cf2` |
| `design/references/shithead-home-screen-vision.jpg` | 1024 × 1536 | `16e5cf32aaa721c517c24925440210ed1ce69153fc8a096e8461f80d08388f32` |

The images were uploaded with `.png` names but their contents are JPEG; use `.jpg` when importing unchanged bytes, or transcode deliberately and record the new checksums.

## 5. Scope guard

**No engine edits, app code edits, unrelated document changes, merges, live deployment or PR approvals are authorized by this design-note commit.** Only the owner can approve the final design implementation and integration.
