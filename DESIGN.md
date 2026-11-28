---
name: Audio Tools (desktop)
description: A free, local stem-separation and practice app. Navy ground, amber signal, nothing moves unless you moved it.
colors:
  navy: "#192542"
  navy-card: "#2A4467"
  navy-highlight: "#35557C"
  navy-inset: "#142033"
  amber: "#F6AD49"
  amber-hover: "#FFAB0F"
  text: "#F4F7FB"
  text-secondary: "#D5DEEA"
  text-muted: "#B7C3D4"
  hairline: "rgba(168, 184, 204, 0.28)"
  danger: "#E85D5D"
typography:
  title:
    fontFamily: "Satoshi, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 700
    lineHeight: 1.1
  section:
    fontFamily: "Satoshi, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 700
    lineHeight: 1.3
  body:
    fontFamily: "Satoshi, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  caption:
    fontFamily: "Satoshi, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.45
rounded:
  sm: "4px"
  md: "8px"
  lg: "10px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
components:
  button-primary:
    backgroundColor: "{colors.amber}"
    textColor: "{colors.navy}"
    rounded: "{rounded.md}"
  button-secondary:
    backgroundColor: "{colors.navy-card}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
  card:
    backgroundColor: "{colors.navy-card}"
    textColor: "{colors.text}"
    rounded: "{rounded.lg}"
  panel-inset:
    backgroundColor: "{colors.navy-inset}"
    textColor: "{colors.text}"
    rounded: "{rounded.sm}"
---

# Design System: Audio Tools (desktop)

Scope: the desktop Streamlit app (`ui/`) and its three iframe components (`ui/mix_tabs_component`, `ui/region_picker_component`, `ui/stem_mixer_component`). The hosted website (`web/`) has its own styles. Product context lives in `PRODUCT.md`; the Audio Isolation direction contract is in `.impeccable/surfaces/ui-pages-isolate-py.md`.

## Overview

A practice tool for one musician at their own computer. The interface is an instrument, not a dashboard: one navy surface, one amber signal, and one obvious next step on every screen. It should feel calm and immediate. Clutter is folded away rather than deleted, so Pro users still reach every control.

Three rules carry the system:

1. **One primary action per state.** Audio Isolation is always in exactly one of four states, each with one amber button: Drop (pick a file), Choose (Separate), Working (watch one card), Mix (play).
2. **Nothing moves unless the user moved it.** No idle reruns, no banners in page flow, no iframe height steps, and no scroll jumps the user did not ask for.
3. **Amber means "this one".** It marks the primary action, the current selection and headings. It is never body text.

## Colors

The owner chose the palette, and it is binding (`PRODUCT.md`). The tokens live in `ui/theme_presets.py` (`TYRIAN_BASE_DARK`, the default preset) and `ui/design_tokens.py` (Home). Iframes receive them as `themeVars` and read them through `iframe-theme.css`.

### Primary
- **Amber `#F6AD49`**: the primary button fill, the selected tile, the active tab indicator, headings and links.

### Neutral
- **Navy `#192542`**: the page ground.
- **Navy card `#2A4467`**: cards, inputs, secondary buttons, the drop and YouTube tiles.
- **Navy highlight `#35557C`**: hover, and the selected span in the region picker.
- **Navy inset `#142033`**: waveforms and the metronome panel, the recessed surfaces.
- **Text `#F4F7FB`**, **secondary `#D5DEEA`**, **muted `#B7C3D4`**: body, labels and captions. Each clears 8:1 on navy.

### Named Rules
- **No green, no near-black.** The old Forest values (`#0a0f0a`, `#141a14`, teal overlays) are fallbacks only. If one shows on screen, a component is not applying `themeVars`. The one exception is the fixed signal set (`--color-signal-low` teal `#4ecdc4`, mid `#ffcc53`, high `#ff6b6b`), which is colour-blind safe and theme-independent; the metronome lane uses it on purpose.
- **Accent tints over navy turn brown.** Lift with navy highlight instead. This covers selected segments and pills, the region-picker span (18% at most, because it paints over amber bars) and any `rgba(amber, low alpha)` fill.
- **Fields inside an open expander** sit on the navy ground, not navy card, or they lose their edge.

## Typography

Satoshi, bundled from `ui/fonts/` (never a CDN). One family carries everything.

### Hierarchy
- **Title** (3rem, bold, amber): the page name only.
- **Section** (1.375rem, bold, amber): for example "Section (optional)" and "Separate tracks".
- **Body** (1rem, text): labels and controls.
- **Caption** (0.875rem, muted): at most two per state. Explanations go in `help=` tooltips.
- Time, percent and ETA text uses `font-variant-numeric: tabular-nums` so ticking digits never change width.

## Layout

- A single column under a compact header: title, then a sticky row with the 48px tab strip and Queue / Refresh.
- **Drop:** two equal 40rem tiles, centred. One dropped file advances to Choose by itself. Continue appears only for batches or after Back.
- **Choose:** name, section picker, outcome tiles, then **Advanced** (collapsed; every engine, device and speed control), then a one-line "You get:" summary. A **sticky bottom bar** holds Back (tertiary) and Separate (primary).
- **Working:** one centred card, 640px wide with a 196px minimum height, holding the title, progress bar, stage and ETA line, and a hint row that always renders.
- **Mix:** the listening row, then the mixer as the hero (its slot reserves 520px before the iframe reports in), then **Export** (collapsed), then **More tools**. More tools is a segmented control with one panel at a time: Guitar tools, Song studio, Add tracks, Break down a stem (Pro), Tab PDF.
- Overlays stay out of page flow: the job status strip and key/chord progress float bottom-right, and notices are `st.toast`.
- `scrollbar-gutter: stable` on the main pane, so page length never changes the content width.

## Elevation & Depth

Flat surfaces separated by tone (navy → card → highlight, with inset for recessed areas). Only floating overlays cast a shadow: `0 8px 24px rgba(10, 16, 32, 0.45)` for the status strip and analysis notice, and `0 10px 32px rgba(0, 0, 0, 0.38)` for the Queue panel.

## Shapes

An 8px radius on buttons and inputs, 10px on cards and floating panels, and 4px inside iframes. Dashed 1px borders mark drop targets only.

## Components

### Buttons
- **Primary:** amber fill, navy text. Exactly one per state.
- **Secondary:** navy card fill, text colour, hairline border.
- **Tertiary:** text only. Used for Back, "Separate another song" and Clear in search dialogs.
- **Disabled:** dimmed to 45%. A disabled primary drops to the navy card fill with muted text, because faded amber reads brown.
- A dialog follows the same rule: its one primary is the dialog's main action (Search), and per-row actions such as Use are secondary.
- **Chord names** are a root plus an optional "m", always in sharps (`F`, `F#m`, `A#`). No sevenths, suspensions, power chords, slash basses or flats, and no detail or spelling switches.
- **Links** are amber (`linkColor`). Never put a link inside `st.caption`: captions are drawn at 60% opacity, which turns it brown.
- Focus: a 2px amber outline with a 2px offset. Hover and colour changes take 120ms with ease-out-quart.

### Cards / Containers
The outcome tiles are cards with an icon above the label; the selected tile fills amber. The Working card and the More tools panel are bordered navy containers.

### Navigation
- The tab strip is navy, with an amber underline on the active tab and an amber progress underline on a busy tab.
- It always reports a fixed height (`STRIP_HEIGHT_PX`, 48), never an auto-measured one.
- Tabs shrink (to 112px) before the strip scrolls, so + stays visible, and a tab shows the song name only.

### Motion
- Tokens: `--att-dur-fast` 120ms, `--att-dur` 200ms, `--att-dur-slow` 320ms, `--att-ease` cubic-bezier(0.25, 1, 0.5, 1).
- Only opacity and transform animate.
- Panels that mount on a click (More tools panel, Queue) rise in over 200ms. Anything a poll repaints never animates.
- `prefers-reduced-motion` turns all of it off.

## Do's and Don'ts

### Do:
- Reserve the final height of anything that loads: skeleton slots, min-heights, always-painted hint rows.
- Gate polling on real work: `st.fragment(fn, run_every=JOB_POLL_SECONDS if jobs_active() else None)`.
- Pass `get_iframe_theme_vars()` to every component and apply it in the component's render handler.
- Keep component keys stable. Use an echoed `revision` arg, not a new key, to mark stale component values.

### Don't:
- Use `@st.fragment(run_every=...)` with a fixed interval on anything that can sit idle. That includes desktop-only watchers, which `make ui` never exercises: the launcher sets env vars the browser dev server does not. Trigger those on window focus instead.
- Write a tag (angle brackets) anywhere inside an `st.html` style block, even in a comment: the sanitizer drops the whole block (pinned by a test).
- Put a banner (`st.info` / `st.success`) in page flow for a one-off notice. Use a toast.
- Nest expanders. Inside Advanced, use `_advanced_section` groups.
- Hard-code hex in page CSS. Use `var(--color-*, fallback)`.
- Change the mixer's audio graph, wake hooks or "Save current mix" export when restyling (AGENTS.md invariants).
