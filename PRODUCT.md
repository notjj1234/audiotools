# Product

<!-- impeccable:product-schema 1 -->

Scope: the **desktop app** (Streamlit `ui/` behind `packaging/launcher.py`). The hosted website (`web/`) is a separate surface and is not covered here.

## Platform

web

## Users
The owner built the app for themselves. They wanted to cover a song, Moises cost too much, and Audacity was too complicated. The primary user is a musician working alone on their own computer who wants to pull a song apart to learn and play it, without paying a subscription and without learning a DAW. Testers install the same unsigned desktop build (`DESKTOP.md`).

## Product Purpose
Audio Tools separates a song into parts (vocals, guitar, bass, drums, piano, other) locally, then lets the player practice against them: mute or solo parts, loop a section, change speed and key, and follow a click and chords. Success means getting a song into a usable practice mix with no reading or setup. **When quality and speed conflict, quality wins.**

## Positioning
A free, local, private alternative to Moises-style apps. Audio never leaves the machine, there is no account, and every engine (Demucs, BS-RoFormer, MelBand) is available, with a Lite mode that picks sensible settings automatically.

## Operating Context
- Single machine, offline, macOS (Apple silicon and Intel) and Windows (CPU or CUDA), 8–16 GB RAM.
- Separation runs one job at a time and takes from tens of seconds to minutes.
- Typical flow: open the app → Audio Isolation → drop a file (or a public YouTube link) → choose outcome → separate → practice in the mixer → optionally export stems or make a tab PDF.

## Capabilities and Constraints
- Two interface levels: **Lite** auto-profiles speed, device and guitar engine. **Pro** exposes every control. Desktop Lite never clamps audio length.
- The mixer (stem volume/mute/solo/pan, loop, count-in, metronome, speed and key) runs in a Web Audio iframe. Export is built on "Save current mix".
- Constraints: Streamlit reruns the whole script on interaction, the iframe components ship committed builds, and the MPS GPU path is used only at ≥12 GB RAM.
- Terms: "stem" (a separated track), "run" or "mix" (one separated song), "Lite" / "Pro".

## Brand Commitments
- Name: **Audio Tools**.
- The owner's chosen palette and font are binding: navy `#192542`, card `#2A4467`, amber `#F6AD49`, and Satoshi.
- Do not copy Moises artwork, font files or markup.

## Evidence on Hand
No testimonials, user counts or benchmarks exist. Do not invent any. The only real content is the user's own songs and the test fixtures in `eval/fixtures/` and `data/smoke_test_30s.wav`.

## Product Principles
1. **Quality first, then speed.** Never trade separation quality for a faster-looking UI.
2. **One obvious next step.** Every screen has one primary action. Everything else is reachable but folded away.
3. **Nothing moves unless the user moved it.** No layout shift, flicker or idle churn.
4. **Simple by default, complete on demand.** Lite hides choices. Pro keeps every control, but out of the way.
5. **Local and private.** No accounts, no uploads, no tracking.

## Accessibility & Inclusion
No product-specific standard has been set. Follow WCAG AA contrast (the tokens in `ui/design_tokens.py` already note their contrast ratios), keep keyboard focus visible, and honor `prefers-reduced-motion`.
