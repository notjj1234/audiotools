# Moises desktop (macOS) — UI/UX strip

Inventory of what a user sees and touches in the installed Mac app, so Audio Tools can decide what to
replicate, adapt, or skip. Competitor inventory, not a spec. No Moises source, CSS, markup, fonts,
icons, images, or song content (lyrics, library titles) are reproduced here; behavior is described in
original prose.

## Header

| Field | Value |
|---|---|
| App path | `/Applications/Moises.app` |
| Version | **2.1.0** (`CFBundleShortVersionString`) — `E-PL` |
| Build | **`261021a1gygumpb`** (`CFBundleVersion`) — `E-PL` |
| Bundle | `com.todesktop.220410vabqjud82`, ToDesktop-packaged Electron, arm64, min macOS 12.0 — `E-PL`, `E-FU` |
| Executable SHA-256 | `c23ee797…bc98d` |
| `app.asar` SHA-256 | `6a42619e…f05a` (6,516 files) — `E-INV` |
| Date | 2026-11-07 (UTC+9) |
| Window (measured) | id 1250, title "Moises Studio", **1260 × 800 pt** at screen (192, 106); every screenshot 1260 × 800 px, 1 px = 1 pt — `E-UI1`…`E-UI8` |
| What was open | One main window, already running and signed in. Five tabs: Home, "Moises Studio", "フルスピード・ボーイ" (a song with Vocals, Drums, Bass, Other and a Metronome row), "The Augments セ…", "Bacteria-12_witho…". Metronome row was muted before the walk started. |
| How screens were reached | REA could not press inside the window (see blocked). The user clicked each step; REA captured passively after each click. Steps: Home tab → "Moises Studio" tab → song tab + Lyrics → Chords → Shapes → Stems + solo Vocals → clear solo + Play (two frames 2 s apart) → Pause. Nothing was purchased, uploaded, sent, or deleted. |
| What was blocked | (1) The macOS accessibility tree exposes only the window and its three traffic-light buttons (13 nodes); Chromium page content is not exposed, so REA scripted presses had nothing to target. (2) No Chrome DevTools endpoint is listening (only the bundled plugin server on 127.0.0.1:6647), so Electron target listing is unavailable. (3) Every page below the tab strip loads from `https://studio.moises.ai` into a separate content view (`S-MAIN`); its UI code is not in the bundle, so static facts cover the **shell only**. Hover states could not be captured: the user had to leave Moises to confirm each step. |
| Relation to prior notes | Same version and build string as the Windows 2.1.0 scan in `REFERENCE.md`, and the same local renderer bundle name (`index-C76vPLoN.js`). Consistent with "the local renderer does not mount the mixer": the mixer seen here is remote page content. Prices, which that scan did not find, were visible on a page already open in a tab (Screen 7). |

### Labels and evidence pointers

- **observed** = seen in a runtime screenshot. **static** = read from shipped bytes (not proof of runtime
  behavior). **inferred** = reasoned from observed frames. **unknown** = not established.
- Placement is in window points, origin top-left of the 1260 × 800 window. `M` = measured from
  screenshot pixels (±1–2 pt); `≈` = read visually from a 1:1 crop (±3 pt).

| Pointer | What it is |
|---|---|
| `E-PL` | REA `inspect_plist`, `ev_8525801c…` |
| `E-FU` | REA `inspect_electron_fuses`, `ev_dc040e43…` (Inspector CLI flags honored; ASAR integrity not enforced) |
| `E-INV` | REA `analyze_javascript_application` inventory, `ev_f55a9d04…` |
| `E-JS` | REA `analyze_javascript_application` over main, both preloads, renderer HTML and bundle, `ev_789bcb3b…`: 2 windows, 2 context-bridge APIs (79 members), 68 literal IPC channels, 1 utility process |
| `S-MAIN` | Main-process file `out/main/index.js` (SHA-256 `7aee9bab…`): tab manager, menus, overlays, routes |
| `S-RJS` | Local renderer bundle `index-C76vPLoN.js` (SHA-256 `00cdb566…`): shell components |
| `S-RCSS` | Local renderer stylesheet `index-D1VDwdG1.css` (SHA-256 `76bed764…`): shell sizes and motion |
| `E-UI1` | `observe_native_ui`, song tab, Stems, paused at 0:00, `ev_4fe34c14…` (png `d04998bb…`) |
| `E-UI2` | Home tab, `ev_b182253b…` (png `b7d140ad…`) |
| `E-UI3` | "Moises Studio" tab, pricing page, `ev_f149b67e…` (png `aae83564…`) |
| `E-UI4` | Song tab, Lyrics panel, `ev_1a86180f…` (png `7c8f10e5…`) |
| `E-UI5` | Song tab, Chords panel, `ev_985b2706…` (png `954ebede…`) |
| `E-UI6` | Song tab, Shapes panel, `ev_709a866c…` (png `236092a4…`) |
| `E-UI7` | Song tab, Stems, Vocals soloed, `ev_f89fd32e…` (png `a6be4eb1…`) |
| `E-UI8` | `capture_native_ui_scenario` wait-only, two frames 2 s apart while playing, `ev_01ff57cb…` (png `2c6119b8…`, `65344f7b…`) |

---

## Screen 1 — App shell (window, tab strip, overlays, menus)

**Purpose:** a browser-like frame that hosts every Moises tool as a tab over one remote web app.

### Region map

| Region | Contents | Placement | Size | Label / evidence |
|---|---|---|---|---|
| Window | Frameless, hidden title bar, dark background | screen (192, 106) | 1260 × 800 default, min 480 × 320 | observed `E-UI1`; static default/min `S-MAIN` |
| Traffic-light zone | Close / minimize / zoom | x 12–71, y 12–25 | three 14 pt circles at x 12, 35, 58 | observed `M`; static position (12, 12) `S-MAIN` |
| Tab strip | Home tab, page tabs, new-tab button, free drag space | x 0–1259, y 0–39 | 40 pt tall (≈5 % of height) | observed `M`; static 40 pt `S-MAIN`, `S-RCSS` |
| Tab row | Tabs separated by 1 pt dividers | x 84–945 | Home ≈98 pt, "Moises Studio" ≈165 pt, song tab 195 pt, two long titles 200 pt each | observed `M` |
| New-tab button | "+" glyph | x 947–982 | 36 pt wide, full strip height | observed `M`; static width `S-RCSS` |
| Right strip space | Window drag area; hosts memory button and update pill when shown | x 983–1259 | — | observed (empty in all frames); static `S-RJS` |
| Content view | Active tab's remote page | x 0–1259, y 40–799 | window height − 40 | static `S-MAIN`; observed in every frame |
| Overlay window | Transparent, always-on-top, click-through layer for tab preview card and drag ghost | follows cursor or tab | preview card 260 pt wide | static `S-MAIN`, `E-JS` |

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Traffic lights | Window controls (macOS) | x 12–71, y 12–25 | Colored when the window is focused | Grey when the window is not focused | Click | Close / minimize / zoom (OS) | OS default | `E-UI2` (colored), `E-UI1`/`E-UI8` (grey) | observed |
| Home tab | Pinned first tab | x 84–181 | House glyph + "Home" | Active: background matches the page | Click; Cmd+T | Shows the Home page | Background/text 150 ms ease | `E-UI2`; `S-MAIN`; `S-RCSS` | observed |
| Home tab — locks | Constraint | — | No close button; cannot be dragged | Context menu shows only "Go to Home" | Right-click | Native menu | — | `E-UI2` (no "×" when active); `S-RJS`, `S-MAIN` | observed (no ×) + static |
| Page tab (inactive) | Tab | e.g. x 545–744 | Tinted glyph + title, secondary text color | Hover: lighter background, primary text, close "×" fades in | Pointer enter | Hover style; preview card after a delay | 150 ms ease | `M`; `S-RCSS` | observed (default); static (hover) |
| Page tab (active) | Selected tab | e.g. x 349–543 | Background matches page, title in primary text, "×" visible | — | Click; Enter on focused tab | Activates tab, swaps the content view | No transition seen between frames | `E-UI1`…`E-UI3`; `S-RJS` (tab role, Enter key, roving focus) | observed + static |
| Tab title | Label | Inside tab, after glyph | 12 pt, medium weight, ellipsis at 200 pt tab width | — | — | — | — | `M`; `S-RCSS` | observed + static |
| Tab glyph | Page-type icon | Left of title, 14 pt inset | Tinted by page type (Studio, Play, Mastering, Voice Studio, Lyric Writer, Setlist each have a hue; Home white) | — | — | — | — | `S-RJS`; all four non-Home tabs showed the same muted teal | static (map); observed (tint); page-type mapping of these four tabs **unknown** |
| Tab close "×" | Button | Right end of tab (x ≈523 on song tab, ≈325 on "Moises Studio") | Hidden on inactive tabs, visible on active | Hover: raised square background | Click; Cmd+W | Closes tab | Opacity 150 ms ease | `E-UI1`, `E-UI3`; `S-RCSS`, `S-MAIN` | observed (active) + static |
| Playing-audio badge | Status | Tab action slot, 20 × 20 | Hidden | Shown only on **inactive** tabs producing sound | Background tab plays audio | Animated equalizer badge, tooltip "Playing audio" | Looping Lottie, timing unknown | `S-RJS`, `S-RCSS`; not shown on the active playing tab in `E-UI8` (consistent) | static |
| New-tab "+" | Button | x 947–982, y 0–39 | Secondary color | Hover: lighter background | Click | Opens new-tab popup below the button (signed-in only) | 150 ms ease | `M`; `S-RJS`, `S-MAIN` | observed (presence); static |
| New-tab popup | Popover window | Below "+" | Hidden | Open | "+" click | Header "New Tab"; one 56 pt row per tool with a 48 pt rounded tile: Play, Studio, Mastering, Voice Studio, Lyric Writer | Fade-in 110 ms; closes on blur, resize, or select | `S-MAIN`, `S-RCSS`, `S-RJS` | static |
| Memory button | Warning icon button | Right of "+" | Hidden | Visible when open tab count reaches a RAM-based cap | Tab count ≥ cap | Shows; click opens memory panel | Hover 150 ms | `S-MAIN`, `S-RJS` | static |
| Memory panel | Dialog | Under memory button, arrow at top-right | Hidden | Auto-opens once when the cap is crossed | Cap crossed; click; Esc or "Dismiss" closes | Title "Tabs are affecting performance", one line of advice to close tabs, "Dismiss" | Fade + 4 pt drop, 120 ms | `S-MAIN`, `S-RJS`, `S-RCSS` | static |
| RAM-based tab cap | Rule | — | ≤10 GB RAM → 5 tabs; ≤20 GB → 10; otherwise 20 | — | Tab opened | Memory button + panel | — | `S-MAIN` | static |
| Update pill | Button | Right strip, after memory button | Hidden | Shown after an update downloads | Update downloaded | Two lines, "New update" / "Click to restart"; click restarts and installs | Unknown | `S-RJS`, `E-JS` | static |
| Tab hover preview | Floating card | Below hovered tab | Hidden | Title strip, tinted glyph, page thumbnail | Hover 450 ms (75 ms if another preview closed in the last 400 ms) | 260 pt card with a 150 pt thumbnail of that tab | Pop-in 130 ms, scale 0.96 → 1 with fade; thumbnail fades in 100 ms | `S-MAIN`, `S-RJS` | static |
| Tab drag | Gesture | Tab row | — | Floating tab at 95 % opacity with shadow; others slide to open a slot | Press and move > 5 pt (not Home) | Reorder; drop into another window; or drop outside to detach | Slot shift 200 ms cubic-bezier(0.2, 0, 0, 1); ghost instant | `S-RJS`, `S-RCSS`, `S-MAIN` | static |
| Tab context menu | Native menu | At cursor | — | Items disabled when not applicable | Right-click tab | Duplicate Tab; Detach to New Window; Close Tab; Close Other Tabs; Close Tabs to the Right | OS default | `S-MAIN` | static |
| App menu bar | Native menu | macOS menu bar | — | — | Menu or shortcut | Settings…, File (Go to Home, New Window, Open Audio…, Close Tab, Close Window, New Project), Edit, View (Reload, zoom), Tabs (Next/Previous), Window; "Enable VST plugins"; "Desktop Settings…" | OS default | `S-MAIN` | static |
| Desktop Settings panel | Local panel | Unknown | — | Plugin server: starting, running, stopping, error | "Desktop Settings…" | "Settings", "Enable VST plugins", "Debug" disclosure with Start/Stop/Restart and an "Output" log | Status dot pulses 1.1 s while starting/stopping; chevron rotates 150 ms | `S-RJS`, `S-RCSS` | static |
| Windows-only window controls | Buttons | Right of strip | Not rendered on macOS | Close hover turns red | — | — | 150 ms | `S-RCSS` | static (n/a on Mac) |

### Whole-screen states

| State | What changes | Label |
|---|---|---|
| Window focused / unfocused | Traffic lights colored / grey | observed |
| Logged out | New-tab popup refuses to open; login is a remote `/auth/…` page in the content view | static `S-MAIN` |
| Signed in, Free plan | Sidebar footer shows the account and a "Free" plan label | observed `E-UI2` |
| Many tabs open | Memory button appears; memory panel auto-opens once | static |
| Update ready | Update pill appears in the strip | static |
| Background playback | Inactive tab shows the playing-audio badge | static |

---

## Screen 2 — Home

**Purpose:** a library landing page: product navigation on the left, the user's processed songs in a
sortable table on the right.

Observed in `E-UI2`. The Home tab showed the **Play** library: the sidebar highlights "Play", not "Home".
Static code points the Home tab at `/home` (`S-MAIN`). Whether that page redirects or the user had
navigated inside the tab is unknown.

### Region map

| Region | Contents | Placement | Size | Label |
|---|---|---|---|---|
| Sidebar | Logo, nav, setlists, footer | x 0–239, y 40–799; 1 pt divider at x 240 | 240 pt wide (19 % of width) | observed `M` |
| Sidebar header | Wordmark logo, collapse button | logo x 24–134, y 74–90; collapse x 201–214 | logo 111 × 17 | observed `M` |
| Nav list | Home; "PRODUCTS" label; Play, Studio, Mastering, Voice Studio, Lyric Writer | Home y ≈131; label y 165–173; product rows centered at y ≈203, 239, 275, 311, 348 | 36 pt row pitch; selected row 216 × 36 at (12, 186) | observed `M` |
| Setlists | "SETLISTS" label; "New Setlist"; three setlist rows with 40 pt art and an owner line | label y 381–389; rows at y ≈423, 459, 497, 541 | ≈44 pt pitch | observed `M` |
| Sidebar footer | Downloads, Upgrade Plan, account row | y ≈660, 696; account row y 736–775 | avatar 40 × 40 at (12, 736); ⋮ at x 221 | observed `M` |
| Page header | Title + count, toggle, search, filter, sort, add | y 65–98 | see element table | observed `M` |
| Table header | Column labels with sort arrow | y 138–151; divider y 171 | — | observed `M` |
| Table body | One row per song | rows from y 192, 56 pt pitch | tile 48 × 48 at x 275; title x 336 | observed `M` |

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Wordmark logo | Brand | (24, 74) | — | — | — | — | — | `E-UI2` | observed |
| Collapse sidebar | Icon button | x 201–214, y 76–87 | Panel glyph | Unknown | Click | Collapses sidebar (inferred from glyph) | Unknown | `E-UI2` | observed; result unknown |
| Nav: Home | Link | y ≈131 | Unselected | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| "PRODUCTS" label | Section label | y 165–173, x 17 | Small caps, muted | — | — | — | — | `E-UI2` | observed |
| Nav: Play | Link | pill (12, 186) 216 × 36 | **Selected**: raised rounded pill, primary text | — | Click | Shows the Play library | Unknown | `E-UI2` | observed |
| Nav: Studio | Link | y ≈239 | Unselected, with a "New" badge 36 × 20 at (180, 230) | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| Nav: Mastering, Voice Studio, Lyric Writer | Links | y ≈275, 311, 348 | Unselected | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| "SETLISTS" label | Section label | y 381–389 | Small caps, muted | — | — | — | — | `E-UI2` | observed |
| New Setlist | Action row | y ≈423 | "+" tile + label | Unknown | Click | Unknown | Unknown | `E-UI2` | observed (not clicked) |
| Setlist row | Link | y ≈459, 497, 541 | 40 pt artwork, name, owner line | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| Downloads | Link | y ≈660 | Glyph + label | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| Upgrade Plan | Link | y ≈696 | Glyph + label | Unknown | Click | Store page (inferred) | Unknown | `E-UI2` | observed (not clicked by rule) |
| Account row | Menu | y 736–775 | Round avatar with initials, name, plan "Free", ⋮ | Unknown | Click ⋮ | Unknown | Unknown | `E-UI2` | observed |
| Page title | Heading | (274, 72) | "Play", ≈24 pt, with muted "60 files" count at x 333 | — | — | — | — | `E-UI2` | observed |
| "Try the New Player" | Toggle pill | (553, 65) 176 × 34 | On (teal switch) | Off look unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| Search | Text field | (741, 66) 315 × 32 | Magnifier + placeholder "Search" | Unknown | Type | Filters list (inferred) | Unknown | `E-UI2` | observed |
| Filter | Icon button | (1068, 66) 32 × 32 | Funnel-like glyph | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| Sort | Icon button | (1112, 66) 28 × 32 | Up/down arrows | Unknown | Click | Unknown | Unknown | `E-UI2` | observed |
| "+ Add" | Primary button | (1156, 66) 74 × 32 | Light fill, dark label | Unknown | Click | Upload (inferred) | Unknown | `E-UI2` | observed (not clicked by rule) |
| Column headers | Sort controls | y 138–151; Title x 275, Created x 639, Genre x 755, BPM x 871, Key x 987, Duration x 1103 | "Created" shows an up arrow (active sort) | Unknown | Click | Sort (inferred) | Unknown | `E-UI2` | observed |
| Song row | Table row | 56 pt pitch from y 192 | 48 pt tile with stems glyph; title + artist line; date; genre ("-" when empty); BPM; key; duration | Hover/selected unknown | Click | Opens the song (inferred) | Unknown | `E-UI2` | observed |

### Whole-screen states

| State | Seen? | Notes | Label |
|---|---|---|---|
| Library with files | Yes | 60 files | observed |
| Empty library | No | — | unknown |
| Logged out | No | — | unknown |
| Upload / processing row | No | — | unknown |

---

## Screen 3 — Song player: Stems panel (mixer)

**Purpose:** play one song as separated stems on a bar timeline, with per-stem level, mute, solo and
pan, a chord strip on top, and a transport at the bottom.

All rows come from the remote page. Frames: paused at 0:00 (`E-UI1`), Vocals soloed (`E-UI7`), and
playing (`E-UI8`). The route is unknown.

### Region map

| Region | Contents | Placement | Size | Label |
|---|---|---|---|---|
| Chord strip | Row of chord blocks (one block per beat, inferred) | x 12–1259, y 48–105 | 58 pt tall; blocks ≈92 pt wide, 4–5 pt gaps, ≈12 pt gap after every 4 blocks | observed `M` |
| Tool row (left) | "Separate Stems" button, square icon button | x 12–267, y 118–157 | 208 × 40 and 40 × 40 | observed `M` |
| Bar ruler | Bar numbers every 16 bars, minor ticks | x ≈283–1180, labels y ≈120–130, ticks y ≈138–169 | ≈68.5 pt per 16 bars (≈4.3 pt per bar) | observed `M` |
| Timeline tools (right) | Two icon buttons | x 1184–1251, y 114–149 | each 32 × 36 | observed `M` |
| Stem header column | One header per stem | x 0–279, y 170–569 | 280 pt wide; rows 80 pt (79 + 1 pt divider) | observed `M` |
| Lane area | One waveform lane per stem | x 281–1259, y 170–569 | 979 pt wide; whole 224-bar song fits at this zoom | observed `M` |
| Empty canvas | Below last lane | x 281–1259, y 570–705 | 136 pt | observed `M` |
| Playhead | Vertical line with a white marker at the ruler | x 287 at 0:00, y 138–705 | 1–2 pt line | observed `M` |
| Panel switcher | Floating pill, four segments | x 336–923, y 584–641 | 588 × 58, centered on the **window**; segments ≈142 pt | observed `M` |
| Help button | Round teal button | x 1200–1239, y 647–686 | 40 × 40 | observed `M` |
| Song progress line | Thin bar along the transport's top edge | y ≈706, from x 0 | Width = elapsed fraction of the song × window width | observed `E-UI8` |
| Transport bar | Track identity (left), transport (center), tempo/metronome (right) | x 0–1259, y 708–799 below a 2 pt divider at y 706–707 | 92 pt | observed `M` |

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Chord block (current) | Position marker | At 0:00: first block, x 12–104. While playing: fixed slot x ≈589–681 | Lighter fill, bright 2 pt left edge | — | Playback | Strip scrolls left under the fixed slot | Scroll; continuous vs stepped unknown | `E-UI1`, `E-UI8` | observed |
| Chord block | Display | Repeating, ≈92 pt | Dark fill | — | — | — | Scrolls with playback | `M` | observed |
| Chord label | Text | Top-left of a block at a bar start | Bright when the chord changes; dim when it repeats the previous chord | — | — | — | — | `E-UI1`, `E-UI5` (same pattern in the grid) | observed; dim = repeat is inferred |
| Bar-start edge | Divider | Left edge of each bar's first block | Light-grey 2 pt edge | — | — | — | — | `M` | observed |
| Separate Stems | Primary button | x 12–219, y 118–157 | Teal fill, stems glyph + label | Unknown | Click | Unknown | Unknown | `M` | observed; not clicked |
| Icon button beside it | Button | x 228–267, y 118–157 | Raised dark square, pen/pick-like glyph | Unknown | Click | Unknown | Unknown | `M` | observed; purpose unknown |
| Bar numbers | Ruler labels | y ≈120–130, every ≈68.5 pt | 1, 17, 33 … | — | — | — | — | `M` | observed |
| Playhead | Position line | x 287 (0:00) → 339 (bar 12) → 347 (bar 13) | White line + top marker | Moves while playing; lanes did not scroll | Play | — | Advances ≈4 pt per bar at this zoom | `E-UI1`, `E-UI8` | observed |
| Timeline tool 1 | Icon button | x 1184–1215, y 114–149 | Gear-like glyph | Unknown | Click | Unknown | Unknown | `M` | observed; purpose unknown |
| Timeline tool 2 | Icon button | x 1220–1251, y 114–149 | Magnifier-with-plus glyph | Unknown | Click | Zoom (inferred) | Unknown | `M` | observed; result unknown |
| Stem name | Label | x 16, row top + 18 | "Vocals", "Drums", "Bass", "Other", "Metronome" | — | — | — | — | `M` | observed |
| Stem ⋮ menu | Button | x ≈259, row top + 19 | Three vertical dots | Unknown | Click | Unknown | Unknown | `M` | observed |
| Volume slider | Slider | Track x 16–188, 4 pt tall, row top + 55 | Teal fill left of a white ≈20 × 12 pill thumb (all stems equal) | Unknown | Drag (inferred) | Stem level | Unknown | `M` | observed |
| M (mute) | Toggle | x 197–214, row top + 47 | Off: dark square, grey "M" | **Explicit mute:** amber fill, dark "M" (Metronome). **Implied mute while another stem is soloed:** dark square, amber "M" | Click; another stem's S | Mutes stem | Unknown | `E-UI1`, `E-UI7` | observed |
| S (solo) | Toggle | x 219–238, row top + 47 | Off: dark square, grey "S" | **On:** cyan fill, dark "S" | Click | Solos the stem; clicking again clears | Unknown | `E-UI7`, `E-UI8` | observed |
| Pan knob | Rotary | x 250–269, row top + 47 | 20 pt circle, indicator at center | Unknown | Drag (inferred) | Pan | Unknown | `M` | observed |
| Stem lane | Waveform | x 281–1259, same row as header | Solid cyan fill with dark waveform; hue shifts slightly from Vocals to Other | **Muted by solo:** fill removed, waveform turns grey on dark | Solo another stem | — | Unknown | `E-UI1`, `E-UI7` | observed |
| Metronome lane | Click waveform | y 490–568 | Dark lane, thin grey click band (y ≈512–545) | Muted (unchanged by solo) | — | — | Unknown | `E-UI1`, `E-UI7` | observed |
| Panel switcher segment | Tab-like button | Stems x ≈345–487, Lyrics ≈487–627, Chords, Shapes at ≈142 pt pitch | Selected: teal-tinted pill, teal label + glyph | Unselected: light label + glyph | Click | Swaps the whole area above the transport (Screens 3–6) | End states only; transition unknown | `E-UI1`, `E-UI4`–`E-UI6` | observed |
| Help "?" | Button | x 1200–1239, y 647–686 | Round teal | Unknown | Click | Unknown | Unknown | `M` | observed |
| Artwork tile | Display | x 20–67, y 731–778 | 48 × 48 tile, music-note placeholder | — | — | — | — | `M` | observed |
| Track title | Label | x 86–123, y 739–769 | Two lines, ellipsis | — | — | — | — | `M` | observed |
| Track ⋮ | Button | x 144–163, y 740–771 | Outlined 20 × 32 | Unknown | Click | Unknown | Unknown | `M` | observed |
| Export | Button | x 176–267, y 740–771 | Outlined 92 × 32, label + share glyph | Unknown | Click | Unknown | Unknown | `M` | observed; not clicked |
| Speaker | Icon button | x 494–509, y 745–758 | Speaker glyph | Unknown | Click/hover | Unknown | Unknown | `M` | observed; purpose unknown |
| Rewind / Fast-forward | Buttons | x 546–569 / 690–713 | Double-arrow glyphs | Unknown | Click | Unknown | Unknown | `M` | observed |
| Stop | Button | x 596–615 | Square | Unknown | Click | Unknown | Unknown | `M` | observed |
| Play / Pause | Toggle | x 645–664, y 740–762 | Triangle when stopped | **Playing:** two-bar pause glyph (x 647–660) | Click | Starts / pauses playback | Glyph swap; transition unknown | `E-UI1`, `E-UI8` | observed |
| Loop | Toggle | x 750–765 | Loop glyph, off look | Unknown | Click | Unknown | Unknown | `M` | observed |
| Time readout | Display | x 552–707, y 779–787, centered | "0:00 - 4:50 \| 1 bar - 224 bars" | While playing: elapsed time and current bar update ("0:15 … 12 bar" → "0:17 … 13 bar") | Playback | — | Text update | `E-UI1`, `E-UI8` | observed |
| Tempo / key pill | Dropdown | x 992–1104, y 738–769 | "186 bpm / E" with chevron | Unknown | Click | Unknown | Unknown | `M` | observed |
| Metronome split button | Toggle + dropdown | x 1117–1172, y 738–769 | Metronome glyph, separate chevron | Unknown | Click | Unknown | Unknown | `M` | observed |
| Third split button | Toggle + dropdown | x 1185–1239, y 738–769 | Glyph shows "1 2 / 3 4", separate chevron | Unknown | Click | Unknown (count-in or meter are guesses only) | Unknown | `M` | observed; purpose unknown |

**Static design-system parts in the local bundle (not proven mounted):** a level meter with peak and
0 dB marks, a track header with an instrument icon and pan, a mute/solo/record/auto-mute button set,
a waveform preview card with skeleton and playing states, a reorderable project table, and a level
readout with clip and blink states (`S-RJS`). The observed implied-mute look matches the auto-mute
state by name only.

### Whole-screen states

| State | Seen? | Notes | Label |
|---|---|---|---|
| Stopped/paused at 0:00 | Yes | Play glyph, playhead at bar 1, current chord block at far left | observed |
| Playing | Yes | Pause glyph, readout and playhead advance, chord strip scrolls, progress line grows | observed |
| A stem muted | Yes | Metronome M amber-filled | observed |
| A stem soloed | Yes | S cyan; other stems show implied mute and grey lanes | observed |
| Processing / separating | No | — | unknown |
| No stems (before separation) | No | "Separate Stems" suggests such a state exists | unknown |

---

## Screen 4 — Song player: Lyrics panel

**Purpose:** read the song's lyrics with chord symbols above the syllables, with the transport still
docked at the bottom. Observed in `E-UI4` (stopped, not playing).

### Region map

| Region | Contents | Placement | Size | Label |
|---|---|---|---|---|
| Lyrics column | Section label, chord-sequence line, lyric lines with chords above | x 220–1030, y 75–641 | ≈810 pt wide, left-aligned | observed `M` |
| Right tool stack | Three round buttons | x 1196–1235, y 306 / 354 / 402 | 40 × 40 each, 8 pt gaps | observed `M` |
| Panel switcher, help, transport | Same as Screen 3, "Lyrics" selected | as Screen 3 | — | observed |

The chord strip, tool row, ruler, stem headers and lanes are all hidden in this panel.

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Section label | Heading | x 221, y 75–83 | Small letter-spaced caps (e.g. "INSTRUMENTAL") | — | — | — | — | `E-UI4` | observed |
| Chord-sequence line | Text | y 114–125 | Chord names for an instrumental passage, space-separated | — | — | — | — | `E-UI4` | observed |
| Chord over syllable | Text | 12 pt band above each lyric line | Small chord names aligned to syllables | — | — | — | — | `E-UI4` | observed |
| Lyric line | Text | ≈32 pt bands, wraps | Large text; all lines the same dim grey while stopped | Current-line highlight while playing unknown | Playback (inferred) | Unknown | Unknown | `E-UI4` | observed (stopped) |
| Bottom fade | Overlay | Lines near the switcher | Lines fade out toward the bottom | — | — | — | — | `E-UI4` | observed |
| Right tool 1 | Toggle | y 306 | Teal fill (on) | Unknown | Click | Unknown | Unknown | `E-UI4` | observed; purpose unknown |
| Right tool 2 | Toggle | y 354 | Teal fill, glyph resembles "A" over a script character | Unknown | Click | Unknown | Unknown | `E-UI4` | observed; purpose unknown |
| Right tool 3 | Button | y 402 | Grey, copy-like glyph | Unknown | Click | Unknown | Unknown | `E-UI4` | observed; purpose unknown |

---

## Screen 5 — Song player: Chords panel

**Purpose:** see the song's chords laid out as a bar grid. Observed in `E-UI5` (stopped).

### Region map

| Region | Contents | Placement | Size | Label |
|---|---|---|---|---|
| Bar numbers | Odd bar numbers (1, 3, 5 …) | right-aligned at x ≈240 | — | observed `M` |
| Chord grid | Rows of two bars × four beat cells | x 258–1039, rows from y 72 | cells ≈92 × 56; 4–5 pt beat gaps; ≈16 pt bar gap; 80 pt row pitch | observed `M` |
| Right tool stack | Four round buttons | x 1196–1235, y ≈283 / 333 / 380 / 426 | 40 × 40 | observed `M` |
| Panel switcher, help, transport | Same as Screen 3, "Chords" selected | as Screen 3 | — | observed |

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Beat cell | Display | Grid | Dark rounded cell | Current-beat highlight while playing unknown | Playback (inferred) | Unknown | Unknown | `E-UI5` | observed (stopped) |
| Bar-start edge | Divider | Left edge of each bar's first cell | Light-grey 2 pt edge | — | — | — | — | `E-UI5` | observed |
| Chord label | Text | Top-left of a cell | Bright on a chord change, dim on a repeat | — | — | — | — | `E-UI5` | observed; meaning inferred |
| Rest glyph | Text | Bar 1 | Marks no chord | — | — | — | — | `E-UI5` | observed |
| Bottom fade | Overlay | Rows near the switcher | Rows fade out | — | — | — | — | `E-UI5` | observed |
| Right tool 1 | Toggle | y ≈283 | Teal fill (on), same glyph as Lyrics tool 1 | Unknown | Click | Unknown | Unknown | `E-UI5` | observed; purpose unknown |
| Right tools 2–4 | Buttons | y ≈333, 380, 426 | Grey; glyphs resemble "A/B", a hand or pick, and a gear | Unknown | Click | Unknown | Unknown | `E-UI5` | observed; purpose unknown |

---

## Screen 6 — Song player: Shapes panel

**Purpose:** follow guitar chord diagrams for the current and upcoming chords, with the current lyric
line under them. Observed in `E-UI6` (stopped).

### Region map

| Region | Contents | Placement | Size | Label |
|---|---|---|---|---|
| Chord names | Large chord names above cards | y 119–143 | ≈25 pt cap height | observed `M` |
| Chord cards | Three fretboard diagrams | x 545, 755, 965; y 162–376 | 170 × 215 each, 40 pt gaps; group sits right of center | observed `M` |
| Beat progress | Five short segments | x 606–877, y ≈436 | 48 × 4 each, 8 pt gaps | observed `M` |
| Current lyric | Large centered text, wraps | x 340–918, y 478–555 | centered on window | observed `M` |
| Next lyric | Dim line below, fading under the switcher | y ≈570+ | — | observed |
| Right tool stack | Three round buttons | x 1196–1235, y 306 / 354 / 402 | 40 × 40 | observed `M` |
| Panel switcher, help, transport | Same as Screen 3, "Shapes" selected | as Screen 3 | — | observed |

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Chord card | Diagram | 170 × 215 | Light card; six strings, frets, numbered finger dots, open (O) and muted (X) marks above the nut, string names under the board | Unknown | — | — | Unknown | `E-UI6` | observed |
| Card ⋮ | Button | Top-right of each card, x ≈702 / 912 / 1122, y 122 | Two-dot glyph | Unknown | Click | Unknown (voicing choice is a guess) | Unknown | `E-UI6` | observed |
| Card order | Layout | Left to right | Current chord first, then the next two (matches the chord sequence) | Advance while playing unknown | Playback (inferred) | Unknown | Unknown | `E-UI6`, `E-UI5` | observed; advance inferred |
| Beat progress | Indicator | x 606–877, y ≈436 | First segment white, middle grey, last lighter with a tiny chord name above | Unknown | Playback (inferred) | Unknown | Unknown | `E-UI6` | observed; meaning inferred |
| Current lyric line | Text | centered, y 478–555 | Large, primary color | — | — | — | Unknown | `E-UI6` | observed |
| Next lyric line | Text | below | Dim, fading | — | — | — | Unknown | `E-UI6` | observed |
| Right tool 1 | Toggle | y 306 | Teal fill (on) | Unknown | Click | Unknown | Unknown | `E-UI6` | observed; purpose unknown |
| Right tools 2–3 | Buttons | y 354, 402 | Grey; hand/pick and gear glyphs | Unknown | Click | Unknown | Unknown | `E-UI6` | observed; purpose unknown |

---

## Screen 7 — Pricing page (open in the "Moises Studio" tab)

**Purpose:** sell plan upgrades. It was already open in the user's second tab and was only observed;
nothing on it was clicked. `E-UI3`.

### Region map

| Region | Contents | Placement | Size | Label |
|---|---|---|---|---|
| Sidebar | Same as Home | x 0–239 | 240 pt | observed |
| Promo banner | One-line upsell with an "Upgrade to PRO" link and a close "×" | x 241–1259, y 40–83; × at (1218, 45) | 44 pt tall, full content width, cyan | observed `M` |
| Hero | Two-line heading and subheading | centered, y ≈150–255 | — | observed |
| Billing toggle | Monthly / Yearly | (632, 312) | 222 × 40 | observed `M` |
| Savings note | Teal one-liner | y ≈395 | — | observed |
| Plan cards | Free, Premium (dark panel), PRO (light card) | y ≈420 downward | page scrolls; thumb covers ≈30 % of the track | observed `M` |

### Element table

| Name | Role | Placement | Default | Other states | Trigger | Result | Motion | Evidence | Label |
|---|---|---|---|---|---|---|---|---|---|
| Promo banner × | Button | (1218, 45) 32 × 35 | Visible | Unknown | Click | Hides banner (inferred) | Unknown | `E-UI3` | observed; not clicked |
| Billing toggle | Segmented | (632, 312) | **Yearly** selected (light pill) | Monthly look unknown | Click | Changes prices (inferred) | Unknown | `E-UI3` | observed; not clicked |
| Free card | Plan | left | "¥0", "Free includes:" list starting with stem separation limits | — | — | — | — | `E-UI3` | observed |
| Premium card | Plan | middle | "¥583" per month, paid annually; "Upgrade now" button | — | — | — | — | `E-UI3` | observed (as displayed to this account, JPY, Yearly) |
| PRO card | Plan | right, light card raised above the others | "PRO" badge; "¥2,625" per month, paid annually; "Upgrade now" | — | — | — | — | `E-UI3` | observed (same caveat) |

---

## Motion catalog

| Trigger | What moves | Duration / easing | Evidence | Label |
|---|---|---|---|---|
| Hover a tab | Background and text color | 150 ms ease | `S-RCSS` | static |
| Hover a tab | Close "×" fades in | 150 ms ease | `S-RCSS` | static |
| Hover "+", memory button, window controls | Background and color | 150 ms ease | `S-RCSS` | static |
| Hover a tab and wait | Preview card appears | Waits 450 ms (75 ms if a preview closed in the last 400 ms); 130 ms pop-in, fade + scale 0.96 → 1, cubic-bezier(0.2, 0, 0, 1) | `S-RJS`, `S-MAIN` | static |
| Preview thumbnail arrives | Image cross-fades in | 100 ms ease | `S-MAIN` | static |
| Drag a tab | Other tabs slide to open a slot | 200 ms cubic-bezier(0.2, 0, 0, 1) | `S-RCSS` | static |
| Drag a tab into another window | Spacer widens in the target strip | 200 ms, same curve | `S-RCSS` | static |
| Drag a tab | Floating tab follows the pointer | Instant; 95 % opacity, shadow | `S-RCSS` | static |
| Open new-tab popup | Panel fades in | 110 ms, same curve | `S-RCSS` | static |
| Open memory panel | Panel fades in and drops 4 pt | 120 ms, same curve | `S-RCSS` | static |
| Background tab playing | Equalizer badge loops | Lottie; timing unknown | `S-RJS` | static |
| Plugin server starting/stopping | Status dot pulses to 35 % opacity | 1.1 s ease-in-out, infinite | `S-RCSS` | static |
| Settings "Debug" disclosure | Chevron rotates | 150 ms ease | `S-RCSS` | static |
| Tooltips, dropdown menus | Slide-and-fade in four directions | Keyframes present; timing not resolved | `S-RJS` | static |
| Switch tabs | Content view swaps | No shell transition found; no animation visible between frames | `S-MAIN`, `E-UI1`–`E-UI3` | static + observed (end states) |
| Switch panel (Stems / Lyrics / Chords / Shapes) | Whole area above the transport is replaced; selected pill moves | Only end states seen; duration unknown | `E-UI4`–`E-UI6` | observed (end states) |
| Play | Play glyph → pause glyph | Unknown | `E-UI8` | observed (end state) |
| Playing | Playhead advances across lanes | ≈4 pt per bar at this zoom (x 339 → 347 over ~2 s); smooth vs stepped unknown | `E-UI8` | observed |
| Playing | Chord strip scrolls left under a fixed current-block slot | Rate follows tempo; easing unknown | `E-UI8` | observed |
| Playing | Song progress line grows along the transport top | x 66 → 77 over ~2 s | `E-UI8` | observed |
| Playing | Time and bar readout | Updates in place | `E-UI8` | observed |
| Solo / mute | Lane fill drops to grey; M switches to implied-mute look | Transition unknown | `E-UI7` | observed (end state) |
| Lyrics / Chords / Shapes while playing | Current line, cell, or card advance | Not captured | — | unknown |
| Meters | Level bars | None visible in any frame | — | unknown |
| Loading / processing | Spinners, skeletons | Skeleton state exists in design system; page use unknown | `S-RJS` | static / unknown |

---

## Interaction catalog

| Input | Target | Effect | Status |
|---|---|---|---|
| Click | Tab | Activate; content view swaps | **confirmed** (user clicks, `E-UI2`, `E-UI3`, `E-UI4`) |
| Click | Panel switcher segment | Replaces the panel above the transport | **confirmed** (`E-UI4`–`E-UI7`) |
| Click | Stem S | Solo; other stems show implied mute; click again clears | **confirmed** (`E-UI7`, `E-UI8`) |
| Click | Play / Pause | Starts / pauses playback; glyph swaps | **confirmed** (`E-UI8`) |
| Enter | Focused tab | Activate (tab role, roving focus) | static |
| Right-click | Tab | Native context menu; Home gets "Go to Home" only | static |
| Drag > 5 pt | Non-Home tab | Reorder, move to another window, or detach | static |
| Hover | Tab | Preview card after 450 ms / 75 ms | static |
| Click | "+" | New-tab popup (signed-in only) | static |
| Esc | Memory panel | Close | static |
| Cmd+T / Cmd+W / Shift+Cmd+W | App | Go to Home / close tab / close window | static |
| Ctrl+Tab / Ctrl+Shift+Tab | App | Next / previous tab | static |
| Cmd+N, Cmd+O, Cmd+, | App | New window, Open Audio…, Settings… | static |
| Cmd+R, Shift+Cmd+R, Cmd+0/+/− | App | Reload, force reload, zoom | static |
| Finder "Open With" | Audio files | App registers for mp3, mp2, wav, m4a, aac, flac, ogg, opus, wma, amr, caf, mid, midi; a pending-import bridge hands the file to the page | static `E-PL`, `E-JS` |
| Resize | Window | Min 480 × 320; content view refits below the 40 pt strip | static |
| Scroll | Pricing page | Vertical scroll (scrollbar visible) | observed (scrollbar only) |
| Drag | Volume slider, pan knob | Unknown | unknown |
| Click | M, stop, rewind/ff, loop, tempo pill, metronome, Export, menus, help | Unknown | unknown |
| Scroll / zoom | Timeline, lyrics, chord grid | Unknown | unknown |
| Keyboard | Page shortcuts (space to play, etc.) | Unknown | unknown |

---

## Audio Tools matrix

Replicate = layout or interaction idea only. Adapt = the job fits Audio Tools constraints (local stems,
Home, mixer, tab). Skip = account, store, hosted DAW, or asset clone.

| Moises behavior | Verdict | Audio Tools surface | Reason |
|---|---|---|---|
| Pinned first Home tab that cannot close or move | Replicate | mix tabs | Matches the existing Home \| mix \| + strip and gives a fixed anchor. |
| Close "×" hidden until hover, always shown on the active tab | Replicate | mix tabs | Keeps a crowded strip calm without hiding the obvious action. |
| Tab width cap with ellipsis | Replicate | mix tabs | Long song titles are common; a cap keeps several mixes visible. |
| Tab tint by tool type | Adapt | mix tabs | Useful only if tabs hold more than one job type; reuse the existing palette. |
| Playing-audio badge on background tabs | Adapt | mix tabs | Worth it only if mixer playback keeps running when switching tabs. |
| Hover preview with a page thumbnail | Adapt | mix tabs | A text tooltip (stems, length, tempo) gives most of the value without capturing iframes. |
| Drag to reorder tabs with a small movement threshold | Adapt | mix tabs | Nice to have; must not fight Streamlit reruns or drop mixer state. |
| Detach tab to a new window, cross-window drag | Skip | mix tabs | Desktop is one Streamlit window behind the launcher. |
| RAM-based tab cap with a dismissible performance notice | Adapt | Desktop Home / mix tabs | Fits 8–16 GB targets; warn instead of block, and keep isolation jobs serial. |
| New-tab popup listing tools | Adapt | mix tabs | "+" could offer Audio Tools' own jobs (Audio Isolation, YouTube to MP3, Tab PDF). |
| Update-ready pill in the title strip | Skip | Desktop Home | Desktop ships manual, unsigned installers with no in-app updater. |
| Tab keyboard shortcuts (Home, close, next/prev) | Adapt | mix tabs | Only where the launcher's browser frame lets the keys through. |
| Left sidebar: tools list, then collections, then account footer | Adapt | Desktop Home | A tool list fits Home's three tools; drop the account footer. |
| Song library table: title, created, BPM, key, duration, sortable headers, search | Adapt | Desktop Home | A local list of separated songs with detected tempo is directly useful; key only if detected. |
| "+ Add" primary action at the top right of the library | Adapt | Desktop Home | Maps to picking a local file for isolation; no upload. |
| "Try the New Player" toggle | Skip | Desktop Home | A/B rollout control, not a user job. |
| Setlists in the sidebar | Skip | Desktop Home | Cloud collections and shared lists are out of scope. |
| Chord strip above the timeline with a fixed current-block slot | Adapt | stem mixer | Chords and tab are the product core; a chord row tied to playback fits. |
| Bright chord name on a change, dim on a repeat | Replicate | stem mixer, Tab PDF | Cheap way to make changes stand out in a dense chord row. |
| "Separate Stems" in the track view | Adapt | Desktop Home / stem mixer | One clear entry to run local, serial isolation on the loaded song. |
| Stem header row: name, menu, volume, M, S, pan in one 80 pt row aligned with its lane | Replicate | stem mixer, hosted web | Dense, scannable row layout; layout idea only. |
| Per-stem filled lane with waveform on top | Adapt | stem mixer | Keep the existing mixer palette; only the idea of a filled lane. |
| Solo greys out the other lanes and marks their M as implied-muted | Replicate | stem mixer, hosted web | Shows at a glance why a stem is silent, without changing its own mute. |
| Explicit mute and implied mute look different | Replicate | stem mixer, hosted web | Users can tell "I muted this" from "solo is silencing this". |
| Metronome as its own mixer row with M/S/volume | Adapt | stem mixer | Audio Tools already renders clicks; a row makes them mixable without re-tracking. |
| Floating panel switcher over the canvas | Adapt | stem mixer | Switch between Stems, Chords, and Tab views of the same song. |
| Chords panel as a bar grid with bar numbers | Adapt | stem mixer / Tab PDF | Same layout works for a chord chart from the existing tab engine. |
| Shapes panel: current and next chord diagrams with the current lyric line | Adapt | stem mixer | A play-along chord-shape view fits the guitar-tab focus; draw original diagrams, no lyrics. |
| Lyrics panel with chords over syllables | Skip | stem mixer | No lyrics feature; would need lyric sourcing. |
| Right-edge round tool stack per panel | Adapt | stem mixer | Per-view toggles live next to the content they affect; tool meanings still unknown. |
| Centered transport with time and bar readout beneath | Replicate | stem mixer, hosted web | Familiar transport; the bar readout suits practice. |
| Song progress line along the transport's top edge | Replicate | stem mixer, hosted web | Whole-song position without a second timeline. |
| Tempo / key pill in the transport | Adapt | stem mixer | Show tempo from the metronome grid; key only if the engine provides it. |
| Metronome split button (toggle + options) | Adapt | stem mixer | Matches the existing metronome; options behind the chevron. |
| Export next to the track title | Adapt | stem mixer | Must stay built on "Save current mix" (I-607), not on every control change. |
| Artwork tile with a two-line title | Replicate | stem mixer | Cheap identity cue for the loaded song. |
| Bar ruler with labels every N bars | Adapt | stem mixer | Needs the stored beat grid; bars help practice loops. |
| Timeline zoom button in the corner | Adapt | stem mixer | Only if the mixer gains a zoomable timeline. |
| Floating round help button | Adapt | Desktop Home | Could open local help; low priority. |
| Short shell motion (150 ms hover, 110–130 ms popovers, 200 ms reorder, one ease-out curve) | Replicate | mix tabs, Desktop Home | Timing guide only. |
| "Open With" registration for audio file types | Adapt | Desktop Home | A frozen desktop app could accept a file and start a local job. |
| Pricing page, promo banner, plan cards, "Upgrade Plan" link | Skip | — | Store and account. |
| Sign-in gate on new tabs; pages served from studio.moises.ai | Skip | hosted web | Account and hosted-app model; Desktop is local and no-login. |
| VST plugin server, audio input capture, Studio DAW | Skip | hosted web | Hosted DAW feature set, outside both products. |
| Mastering, Voice Studio, Lyric Writer, Setlist tools | Skip | — | Not in Audio Tools scope. |
| Moises icons, illustrations, Lottie files, fonts, chord-diagram artwork | Skip | — | Asset clone; forbidden. |

---

## Coverage ledger

| Item | Status | Detail |
|---|---|---|
| App shell | Observed + static | Default states seen; hover, drag, preview, popups and menus static only. |
| Home | Observed | One frame showing the Play library; clicks inside not tried. |
| Stems panel | Observed | Paused, soloed, playing. M, slider, knob, loop, stop, rewind/ff, tempo pill, Export not exercised. |
| Lyrics, Chords, Shapes panels | Observed (stopped) | Playing behavior inside these panels not captured. |
| Pricing page | Observed | Already open in a tab; nothing clicked. |
| Studio, Mastering, Voice Studio, Lyric Writer, Setlist pages | Not opened | Known from sidebar labels and the shell route table only (`S-MAIN`). |
| Downloads, account ⋮, New Setlist, Upgrade Plan | Not opened | Upgrade Plan avoided by rule (store). |
| New-tab popup, memory panel, tab preview card, tab context menu, app menu, Desktop Settings | Not opened | Static only. |
| All page dropdowns and dialogs (stem ⋮, track ⋮, Export, tempo pill, metronome and third split buttons, help, card ⋮, filter, sort) | Not opened | Not in the declared walk. |
| Hover and pressed states | Not observed | The user had to leave Moises to confirm each step, which ends any hover. |
| Page motion timing | Not measured | Only end states and two 2 s-apart frames. |
| Exact meaning of unlabeled icon buttons (beside Separate Stems, two timeline tools, third split button, right-edge stacks) | Unknown | Glyphs read visually only. |
| Login wall | Not encountered | Session was signed in. |
| Paywall | Seen as a page | Not interacted with. Prices recorded as displayed (JPY, Yearly). |
| Screen Recording | Granted | All screenshots captured. |
| Accessibility | Granted at OS level | Chromium did not expose page content (window + traffic lights only). |
| Electron targets | Blocked | No DevTools endpoint; only 127.0.0.1:6647 (plugin server). Fuses would honor Inspector flags (`E-FU`), but that needs a relaunch, which this pass did not do. |
| Static coverage | Partial by design | Main, preloads, renderer HTML and bundle analyzed; 6,510 other inventoried files out of scope (`E-JS`). Two unpacked native binaries differ from their packed integrity hashes (expected macOS signing) and were recorded as untrusted. |
| Static vs runtime | One difference | Home tab is wired to `/home` (`S-MAIN`) but showed the Play library with "Play" selected (`E-UI2`); cause unknown. Window 1260 × 800, traffic lights (12, 12), 40 pt strip and 200 pt tab cap all match. |
| Naming overlap | Noted | Window title "Moises Studio" is the local shell page title; the second tab is also titled "Moises Studio" but showed the pricing page. |
