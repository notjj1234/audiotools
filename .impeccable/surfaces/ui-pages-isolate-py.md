---
version: 1
slug: "ui-pages-isolate-py"
primary_target: "ui/pages/isolate.py"
related_targets: ["ui/stem_mixer_component","ui/region_picker_component","ui/mix_tabs_component"]
---

# Audio Isolation (desktop)

Scope: `ui/pages/isolate.py` plus the three iframe components it hosts (mix tabs, region picker, stem mixer). Mode: **Operate**. Build path: code-led.

Audience and job: the owner (and testers) want to get a song into a practice mix. Quality beats speed when they conflict. Constraints: Streamlit full-script reruns, committed component builds, Lite/Pro split, mixer invariants (AGENTS.md).

## Direction contract
THESIS: One instrument, four states. The page is a single column that is always in exactly one state (Drop, Choose, Working, Mix), each with one primary action. It refuses the settings-wall default: no stack of captions, expanders and radio groups before the first action.

OWN-WORLD: the owner's navy `#192542` ground, card `#2A4467`, inset `#142033`, amber `#F6AD49` reserved for primary action, selection and headings. Body text `#F4F7FB` / `#C5D0E0`. Satoshi only, fixed scale, tabular numerals for time. Hairline `#A8B8CC33` dividers, 8px radius. No green, no near-black.

STORY: drop a song, see what will come out, press Separate, watch one calm progress card, land in the mixer and play. Everything else (engines, device, exports, fix-ups) is one click away and never in the way.

FIRST VIEWPORT: compact header row (title left; 40px tab strip; Queue icon with count right). Below it, the current state's card centered at a max width of 880px. In Choose, a sticky footer bar holds the summary line and the amber Separate button.

FORM: state-machine single column, 1st on my list. seed: none (unavailable). The direction is pinned by the user-approved plan, so no roll was run.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance

## Signature interaction and motion grammar
- State changes cross-fade in 200 ms (opacity plus 4px translate) inside a reserved-height slot.
- Loading regions show skeletons at their final height. Pending buttons keep their width.
- Durations are 120 / 200 / 320 ms with ease-out-quart. Only opacity and transform animate. Reduced motion means instant changes.

## Unresolved
- Whether Export lives in a popover or a dialog (prefer a popover; operate.md warns against reaching for a modal first).
