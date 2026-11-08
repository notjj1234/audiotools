# UI motion audit

Calm, restrained motion for the React app in `web/`. No animation library. `smooth-ui` wins where the motion skills disagree: no bounce, no decorative blur on large surfaces, exits about 65–75% of the entrance, and `prefers-reduced-motion` keeps a short fade plus the static cue (color, label, or a still progress mark).

`ui/` (Streamlit) was read only. It was not restyled.

## Lab conditions

Local only. CrUX field data is unavailable for localhost.

| Item | Value |
| --- | --- |
| App | Vite 5.4.21 at `http://127.0.0.1:5173` |
| API | Stub on `127.0.0.1:8000` so the shell can render. It is not the real job runner. |
| Browser | Cursor browser, device metrics 1440×900 and 375×812 |
| CPU | 4× on the timed loads below |
| Cache | Warm |

A reload with the real API down paints the session-error screen (Retry) instead of the page. That path is unchanged.

## Baseline (before)

| Signal | Conditions | Observed |
| --- | --- | --- |
| CLS | `/login` then client navigation to `/settings`, layout-shift observer | **0.000** (no entries) |
| INP | Settings click and consent checkbox. Event Timing observer | **No entries.** Automation clicks were not reported as interactions. |
| Frames | `requestAnimationFrame` for 900ms on `/login` | **1 frame.** The tab was backgrounded, so this is timer throttling, not a measured drop. |
| Load | 1440px, 4× CPU, `/login` | DOMContentLoaded **220ms**, load **223ms** |
| Long tasks | Same load | None |

Screenshots: `baseline-login-1440.png`, `baseline-login-375.png`, `baseline-isolate-1440.png`, `baseline-isolate-375.png`, `baseline-settings-1440.png`, `baseline-settings-375.png`, `baseline-tab-1440.png`, `baseline-tab-375.png` (Cursor screenshot temp folder).

What those shots showed:

- The shell paints. There is no full-page blank during session boot, but the nav says “Anonymous” until the session returns, then swaps text.
- `.login-hero` runs `rise` (opacity + 12px, **700ms**, `ease`, both) on first paint.
- At 375px the cookie banner was `position: sticky; bottom: 0` and sat on top of the sign-in button, the isolate track list, and the tab form.
- Job progress, when a job exists, is text only. The web job payload has no `percent` (`backend/contracts.py` `JobResponse`). The desktop app computes percent; the website does not receive it.

## Inventory (original)

| Surface | Where | What it did | Timing | Properties | Reduced motion | Blocks input? | Class |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Session boot | `App.tsx` shell, `auth.tsx` `loading` | Shell renders immediately. Nav label flips from “Anonymous” to the email. Test forbids a “Loading…” gate. | none | none | n/a | no | missing |
| Session error | `App.tsx` early return | Replaces the shell with a message and Retry. | none | none | n/a | no | fine (left as-is; rewriting the shell would duplicate the header) |
| Route change | React Router `<Outlet>` | Instant swap. | none | none | n/a | no | missing |
| Login entrance | `styles.css` `.login-hero` | Rise on first paint. | 700ms ease | opacity, transform | not covered | no | excessive |
| Sign-in button | `LoginPage.tsx` | Label swaps to “Signing in…”, button disabled. Width changes. | none | none | n/a | yes, while the request runs | clunky |
| Isolate / tab submit | `isolateSubmit.ts`, `IsolatePage.tsx`, `TabPage.tsx` | Same label swap. No progress graphic. | none | none | n/a | yes, while pending or the job runs | clunky |
| Delete account | `SettingsPage.tsx` | “Deleting…” swap. | none | none | n/a | yes | clunky |
| Job progress | `JobProgress.tsx`, `.progress` | Status text and message. No bar, no delayed spinner. | none | none | n/a | no | missing |
| File upload | `api.uploadAudio` | No upload percent. The submit button covers the wait. Fetch was not rewritten. | none | none | n/a | via the submit button | missing graphic, acceptable |
| Stem load | `StemMixer.tsx` status, `engine.ts` `onProgress` | Status text only (“Loading stems…”). Controls render at full layout immediately. Engine was not edited. | none | none | n/a | controls were live during load | missing |
| Results | isolate / tab results cards | Pop in. | none | none | n/a | no | missing |
| Region wave | `RegionPicker.tsx`, `.region-picker-wave` min-height 96px | Empty box until WaveSurfer is ready. Play starts disabled. | none | none | n/a | play disabled until ready | missing |
| Processing mode | `ProcessingModeSelect.tsx` | Fallback modes paint immediately, then the hint text updates. Already stale-while-revalidate. Hint height can change. | none | none | n/a | no | fine, height reserved now |
| Theme groups | `ThemeSelector.tsx` ~71 | Unmount on close. Chevron `transform` 150ms, default ease. | 150ms | transform | not covered | no | clunky |
| Theme presets | `ThemeSelector.tsx` ~173 | `transition: all 0.15s ease` | 150ms ease | all | not covered | no | janky |
| Cookie banner | `CookieBanner.tsx` | `useEffect` shows it after first paint. Dismiss is instant. Sticky bar covered controls. | none | none | n/a | yes, it covered buttons | clunky |
| Mixer panels | `StemMixer.tsx` `hidden` | `display: none` snap for Mix, Speed & Key, Practice. | none | none | n/a | closed content not tabbable | clunky |
| Toggles | `.mixer button.toggle` | Background/color/border 160ms plus `scale(0.97)` on press. | 120–160ms | background, color, border, transform | those rules only | no | excessive (the scale) |
| Hover | buttons, `.stack-secondary:hover`, ghost underline | No press tint on most buttons. Hover not limited to `@media (hover: hover)`. | 150–200ms where present | opacity | partial | no | missing / sticky on touch |
| Focus | `:focus-visible` | 3px outline, not transitioned. | none | outline | n/a | no | fine |
| Errors | `.error` | Instant text. Color is the cue. | none | none | n/a | no | fine, now a short fade when mounted |
| Tables / legal | `LegalPage` | Static. | none | none | n/a | no | fine |
| Nav active | `.nav a.active` | Underline and color, no motion. | none | none | n/a | no | fine |
| Stack dim | `.stack` opacity 200ms | Secondary stacks fade. Hover and focus both raise opacity. | 200ms ease | opacity | not covered | no | fine |

## Ranked fixes

1. Stop the sticky cookie banner covering the primary controls, and show it on first paint instead of after an effect.
2. Determinate `scaleX` progress when `percent` exists; otherwise an indeterminate bar. Spinner after 200ms, held at least 500ms. Stable status line.
3. Pending buttons keep one width, show an inline spinner on that same delay, and stay disabled while the action runs.
4. Stem list and the region wave reserve their box and crossfade a skeleton into the real control.
5. One token set. No `transition: all`. No press scale. Hover only where the device can hover. Reduced motion is a short opacity/color fade.
6. Route, results, and errors fade in. Panels open with a clip plus opacity. First paint does not rise.

## What changed

Tokens in `styles.css` `:root`: 80 / 150 / 220 / 350 / 500ms, ease-out `cubic-bezier(0.22, 1, 0.36, 1)`, ease-in `cubic-bezier(0.55, 0, 1, 0.45)`, ease-in-out `cubic-bezier(0.65, 0, 0.35, 1)`. Linear is only the spinner and the progress mark.

- Login rise removed. First paint is the finished hero (`animation-name: none`, opacity 1).
- Cookie banner reads `localStorage` during the first render. Dismiss fades and moves 8px (150ms, ease-in) then unmounts. It is in normal flow, not sticky, so it no longer sits on the sign-in button.
- `JobProgress` draws a 4px track. `scaleX` follows `percent` (0–1, or 0–100 when the number is above 1). No percent and still running: a sliding `scaleX(0.35)` loop. Succeeded with no percent fills the track. Spinner slot is always reserved.
- `StableLabel` stacks every label in one grid cell and parks the spinner in a fixed left pad, so the button width does not jump.
- Stem rows stay in the layout under a skeleton (`data-stems="loading"`), `inert` until `loadStems` settles, then crossfade.
- Region wave keeps 96px and fades a skeleton when WaveSurfer fires `ready`.
- Mix, Speed & Key, Practice, and theme color groups use `.fold`: `grid-template-rows` 0fr/1fr (350ms ease-out open, 220ms ease-in close) plus opacity/transform. Closed panels are `inert`. This is the one layout interpolation. Reduced motion snaps it.
- Route changes add `.route-fade` after the first path, via `useLayoutEffect`, so Strict Mode does not drop the class. 6px rise, 220ms ease-out. Not on first paint.
- Hover tint is a `::before` opacity, only under `@media (hover: hover)`. Press is a darker tint, not a scale. Focus outline is not transitioned.
- Reduced motion forces transitions onto opacity, color, background, and border at 80ms, kills loops, and keeps reveals as an 80ms fade. A running spinner becomes a still ring. Indeterminate progress becomes a still 40% mark.

Optimistic UI was not added. Mode select already shows fallback modes, then replaces the hint. Upload progress was not added, because that would rewrite `fetch`.

## After

| Signal | Conditions | Observed |
| --- | --- | --- |
| CLS | `/login`, then settings and isolate navigations, same observer | **0.000** |
| Hero | `/login`, computed style | `animation-name: none`, opacity **1** |
| Button transition | submit button | `background-color, color, border-color, opacity` (not `all`) |
| Route | client navigation to `/isolate` | `main` class `route-fade`, animation `rise-in` |
| Reduced motion | emulated `reduce`, 375px, 4× CPU, `/login` | matches **true**. Button transition limited to opacity/color/background/border, duration **0.08s**. Hero animation **none**. |
| Load under that pass | 375px, 4× CPU, reduced motion | DOMContentLoaded **126ms**, load **131ms**. Not comparable to the 1440px baseline. |
| Long tasks | both timed loads | None |
| INP | Event Timing | Still **no entries**. Not a field INP. |
| Frames | background tab | Still not a usable frame trace. |
| Cookie | 375px `/login` hit-test on the sign-in button | `elementFromPoint` hit the “Sign in” label, not the banner. |
| Isolate submit | click with no file | Error “Choose an audio file”. Button stayed focused. Name stayed “Start isolation”. |
| Consent | checkbox click | Button enabled. Focus stayed on the checkbox. |
| Theme groups | custom preset | Closed group height **0** and `inert`. Open group height **116** and not inert. |
| Cookie dismiss | OK | Button entered the leaving state, then the banner was gone and the ack was stored. Ack was cleared afterward so this browser is not left dismissed. |
| Theme preset | localStorage | A click during the audit set `custom`. Restored to `forest-dark` / `system`. |

Screenshots: `after-login-1440.png`, `after-login-375.png`, `after-isolate-375.png`, `after-tab-375.png`, `after-settings-375.png`. Desktop isolate, tab, and settings were exercised in the same session (full controls in the accessibility tree, route animation confirmed). A 1440px after-shot of every route was not repeated after the cookie bar left sticky positioning; the 375px shots are the ones that show that fix.

`npm test`: 11 files, **71 passed**. `npm run build`: success. CSS gzip about **5.7 kB**. Main JS gzip about **105 kB**.

## Streamlit (`ui/`), not changed

- `ui/app.py` global overlay: spinner `0.75s linear`, dim fade `0.18s` after `0.4s`. Reduced motion stops the spinner and drops `backdrop-filter`. The dim fade is not fully turned off.
- Mode switch sets `pointer-events: none` on `body *`, which blocks the page for that rerun.
- `ui/pages/isolate.py` uses `st.spinner`, `st.status`, and `st.progress(percent)` (determinate).
- `ui/pages/tab_pdf.py`, `youtube_audio.py`, and `home.py` use `st.spinner` / `st.status`.

Those are Streamlit’s own widgets. React timing tokens were not copied in.

## Repo risk (motion scope)

Assumed load: one person on the demo site, jobs one at a time.

1. **The website cannot show a real percent yet** (`web/src/api.ts` type, `backend/contracts.py` `JobResponse`). The bar is indeterminate until a payload includes `percent`. Inventing a percent from the stage name would lie.
2. **Session failure still drops the chrome** (`App.tsx` early return). The boot path itself is not blank.
3. **Expand/collapse interpolates `grid-template-rows`.** That is a layout pass on a small panel. Reduced motion snaps it. Nothing else animates height, width, top, left, margin, padding, or box-shadow.

Not checked: backend auth, the job runner, and the audio engine.

## Left alone

- Copy, color, type, and routes.
- `engine.ts`, backend, `ui/` Python, legal text.
- No new dependencies. `web/package-lock.json` was restored after `npm install` filled missing `node_modules` (wavesurfer and SoundTouch were already declared and absent locally).
