
# App-wide unslop (UI + in-app copy)

> **Status:** Direction approved 2026-11-18 (Agent execution). Scope defaults locked. Baselines: code audit in §4; visual screenshots deferred to Wave 9 dogfood/UAT.

> **For agentic workers:** Execute **one wave per Agent session**. Stop for human review + screenshots after each wave. REQUIRED later: `executing-plans` or native Agent with `verification-before-completion`; SPA UAT via `agent-browser` + `browser-uat-analyst`; desktop via `qa` / `exploratory-qa` / `dogfood`; post-wave `ponytail-review` or `code-review`.

**Goal:** Quiet chrome, craft in 1–2 product moments, copy that sounds like Audio Tools — without changing features, flows, section order, or engine behavior.

**Architecture:** Inventory → audit → Direction approval gate → sequential surface waves. Each wave runs `unslop-ui` nine passes in order (Spacing → Color → Icons → Copy → Type → Layout → Details → Visuals → Motion), with `impeccable` `quieter` / `distill` / `clarify` / `typeset` / `layout` / `polish` only where they reinforce the same Direction. `ponytail`: smallest correct diffs. Never one-shot the whole app.

**Tech stack:** React/Vite SPA (`web/`), Streamlit desktop (`ui/`), three committed Vite iframe builds (mixer / region-picker / mix-tabs). Shared engine out of scope.

**Spec / durable plan path (write on approval):** [`docs/plans/unslop/2026-11-18-app-unslop.md`](docs/plans/unslop/2026-11-18-app-unslop.md)

**Skills used (this Plan session):** `graphify` (surface map) → `brainstorming` (Direction) → `writing-plans` + `planning-and-task-breakdown` (waves) → `ponytail` (diff constraint) → `unslop-ui` + `unslop` (audit) → `impeccable` (quieter/distill/clarify/typeset/layout/polish as plan phases only; never `bolder` / `overdrive` / `delight`). Verification skills listed for later Agent waves only.

---

## 1. Skills + locks (carry forward)

| Lock | Rule |
|------|------|
| Home Moises geometry | Measured sizes in [`docs/plans/moises-parity/10-MOISES-UI-CRAFT.md`](docs/plans/moises-parity/10-MOISES-UI-CRAFT.md) §13; tasks in [`11-DESKTOP-UI-REDESIGN.md`](docs/plans/moises-parity/11-DESKTOP-UI-REDESIGN.md) §12. Do not re-derive pixels. |
| Home-scoped neutrals | [`ui/design_tokens.py`](ui/design_tokens.py) navy `#192542` / blue `#2A4467` / amber `#F6AD49`. Do not retint global theme presets for Home "consistency." |
| Mixer palette | Do not swap mixer colors "for consistency" with Home or SPA. Edit [`ui/stem_mixer_component/frontend/src/`](ui/stem_mixer_component/frontend/src/) then `make mixer-build`. |
| Dual Lite | Desktop Interface Lite ≠ hosted processing mode `lite`. Never unify copy or UX. |
| Engine | No changes under `src/audio_to_tab/**` unless a string already surfaces in UI (then copy-only, flag separately). |
| Builds | Never hand-edit `frontend/build/**`. Rebuild: `make mixer-build` / `make region-picker-build` / `make mix-tabs-build` / `make home-build` if Home iframe touched. |
| Brand | Product name stays "Audio Tools". Do not copy Moises artwork, fonts, or markup. |

---

## 2. Scope confirmation (answer before Wave 0 executes)

Defaults below are **encoded in the wave plan**. Correct them if wrong:

1. **`ui/home_component/`** — treat as **no-slop / locked** (≤3 optional refinements only if a real tell remains). Do **not** open a redesign wave against §13 geometry.
2. **Shared [`src/design-tokens.css`](src/design-tokens.css) `purple-gold` accent preset** — keep as an optional ThemeSelector choice; do **not** make it default; do **not** use purple in chrome unslop. Ask before deleting the preset.
3. **Legal (`/legal/*`, markdown)** — **Read-mode**: audit for AI-tells only; no visual redesign wave.

IN (confirmed): `web/src/**`, `ui/**` Streamlit chrome/pages/help, three iframe `frontend/src/**`, shared CSS/tokens only when required to fix audited slop without violating locks above.

OUT (hard): engine/algorithms, packaging/CI/Docker, inventing features/claims, renaming product, global rebrand, unifying Lites, hand-editing hashed builds.

---

## 3. Surface inventory

| Surface | Path | Mode | Slop density | Key files |
|---------|------|------|--------------|-----------|
| SPA shell | `/` shell | Operate | **Light–heavy** (chrome wash) | [`web/src/App.tsx`](web/src/App.tsx), [`web/src/styles.css`](web/src/styles.css) |
| SPA Login | `/login` | Persuade+Operate | **Light** (honest copy; hero sits on wash) | [`web/src/pages/LoginPage.tsx`](web/src/pages/LoginPage.tsx) |
| SPA Isolate | `/isolate` | Operate | **Light** | [`IsolatePage.tsx`](web/src/pages/IsolatePage.tsx), [`trackOptions.ts`](web/src/trackOptions.ts), [`RegionPicker.tsx`](web/src/components/RegionPicker.tsx), [`JobProgress.tsx`](web/src/components/JobProgress.tsx), [`ProcessingModeSelect.tsx`](web/src/components/ProcessingModeSelect.tsx) |
| SPA StemMixer | isolate result | Operate | **Light** (some type/chrome tells) | [`StemMixer.tsx`](web/src/components/StemMixer.tsx), [`PracticeSheet.tsx`](web/src/components/PracticeSheet.tsx), mixer CSS in `styles.css` |
| SPA Tab PDF | `/tab` | Operate | **Light** (honest warning already) | [`TabPage.tsx`](web/src/pages/TabPage.tsx) |
| SPA Settings | `/settings` | Operate | **Light** | [`SettingsPage.tsx`](web/src/pages/SettingsPage.tsx), [`ThemeSelector.tsx`](web/src/components/ThemeSelector.tsx) |
| SPA Legal / footer / cookies | `/legal/*` | Read | **None–light** | [`LegalPage.tsx`](web/src/pages/LegalPage.tsx), [`SiteFooter.tsx`](web/src/components/SiteFooter.tsx), [`CookieBanner.tsx`](web/src/components/CookieBanner.tsx) |
| Shared tokens | — | — | **Risk** (purple preset; dual identity) | [`src/design-tokens.css`](src/design-tokens.css), [`web/src/theme/`](web/src/theme/) |
| Desktop shell | Streamlit multipage | Operate | **Light** | [`ui/app.py`](ui/app.py), [`ui/design_tokens.py`](ui/design_tokens.py), [`ui/satoshi_font.py`](ui/satoshi_font.py) |
| Desktop Home | boot | Operate | **None–light** (locked) | [`ui/pages/home.py`](ui/pages/home.py), [`ui/home_component/frontend/src/`](ui/home_component/frontend/src/) |
| Desktop Isolate | page | Operate | **Light** (copy density / Streamlit chrome) | [`ui/pages/isolate.py`](ui/pages/isolate.py), [`ui/isolate_state.py`](ui/isolate_state.py) (`OUTCOME_CARDS`) |
| Desktop YouTube→MP3 | page | Operate | **Light** | [`ui/pages/youtube_audio.py`](ui/pages/youtube_audio.py) |
| Desktop Tab PDF | page | Operate | **Light** | [`ui/pages/tab_pdf.py`](ui/pages/tab_pdf.py) |
| Iframe mix-tabs | Isolate strip | Operate | **None–light** | [`ui/mix_tabs_component/frontend/src/`](ui/mix_tabs_component/frontend/src/) |
| Iframe region picker | Isolate Home | Operate | **None–light** | [`ui/region_picker_component/frontend/src/`](ui/region_picker_component/frontend/src/) |
| Iframe stem mixer | mix tab | Operate | **Light** (chrome polish only) | [`ui/stem_mixer_component/frontend/src/`](ui/stem_mixer_component/frontend/src/) |

**Intentional exclusions:** `src/audio_to_tab/**` behavior; `backend/**` except flag user-visible API error strings separately; packaging; fixtures; Moises research assets.

---

## 4. Audit findings (file-anchored)

### SPA / shared

- [`web/src/styles.css`](web/src/styles.css) L44–47 — body uses **radial green/sand washes + hue-leaning linear gradient** on chrome → quiet tinted-neutral paper (unslop Surfaces).
- [`web/src/styles.css`](web/src/styles.css) L1421–1431 — **infinite shimmer** on skeletons → keep brief loading affordance or static muted block; no looping decorative motion on chrome.
- [`web/src/styles.css`](web/src/styles.css) L590–596 — `.practice-heading` **uppercase + wide tracking + weight 700** → sentence case, weight ≤500, normal tracking.
- [`web/src/styles.css`](web/src/styles.css) L388, L592 — **font-weight 700** in chrome hierarchy → prefer size/color over heavy weight.
- [`src/design-tokens.css`](src/design-tokens.css) L68–76 — **`purple-gold` accent preset** is a classic AI-purple tell if defaulted; leave optional, never default chrome.
- Dual identity: SPA moss/paper vs desktop Tyrian/amber — **do not merge**; unslop each shell in its own world.
- Functional mixer range `linear-gradient` fills ([`styles.css`](web/src/styles.css) L658+) are **progress fills**, not hue chrome — keep.
- Copy sample: Login/Tab honesty is already good ([`LoginPage.tsx`](web/src/pages/LoginPage.tsx) L38–41, [`TabPage.tsx`](web/src/pages/TabPage.tsx) L60–65). Track labels are blunt ([`trackOptions.ts`](web/src/trackOptions.ts)). No `AI-powered` / emoji-icon hits found in `web/src` UI strings.

### Desktop

- [`ui/design_tokens.py`](ui/design_tokens.py) + [`ui/home_component/frontend/src/style.css`](ui/home_component/frontend/src/style.css) — real brand (Tyrian/amber/Satoshi); treat as **no-slop lock**.
- [`ui/pages/home.py`](ui/pages/home.py) L49–70 — legacy Home CSS includes **hover transform transition**; under V2 prefer Home component; if legacy path remains, strip hover scale/transform noise.
- [`ui/isolate_state.py`](ui/isolate_state.py) L426–457 — `OUTCOME_CARDS` copy is product-specific and honest; **unslop pass = tighten wording only**, not rewrite voice into marketing.
- [`ui/app.py`](ui/app.py) L1313–1325 — Interface Lite/Pro help is correct; **never** rename or equate with hosted `lite`.
- Mix-tabs edge fades ([`mix_tabs_component/.../style.css`](ui/mix_tabs_component/frontend/src/style.css) L63–70) are **neutral scroll fades** — keep.
- Stem mixer CSS gradients for faders/chevrons are mostly **control chrome**, not purple blobs — polish density/type only; **do not retint stem palette**.

### Template / Moments check

If "Audio Tools" were swapped for another name and the SPA still read as a generic green-wash SaaS form, Direction failed — push Moments (stem waveforms, practice sheet) and Signature (honest bleed caveats, Satoshi, amber/moss signal), not more chrome effects.

---

## 5. Direction (APPROVAL GATE — do not execute waves until approved)

Derived from product truth + existing Tyrian Nocturne craft ([`10-MOISES-UI-CRAFT.md`](docs/plans/moises-parity/10-MOISES-UI-CRAFT.md) §4 / §13), not trends:

- **Product.** Audio Tools separates stems and runs a practice mixer for musicians who need honest local/hosted tools, not a demo that overclaims.
- **Character.** Exact, night-studio, blunt.
- **World.** A practice desk after dark — deep surfaces, one lamp, instruments and waveforms as the material.
- **Moments.** (1) Live stem waveforms + practice sheet in the mixer; (2) Desktop Home library cards / outcome picks. Chrome stays quiet around them.
- **Signature.** Honest limit-and-bleed copy as voice; Satoshi; one signal accent (amber on Tyrian desktop; moss on hosted paper) used rarely.

**STOP.** Approve, edit, or reject this Direction before Wave 0. Changing Direction later redoes every pass.

**Approach (locked):** polish-first per surface (light/none) with full nine-pass only where audit is heavy (SPA body chrome). No rebrand. No palette unification across desktop Home ↔ mixer ↔ SPA.

---

## 6. Wave plan

### Global constraints for every wave (embed for executor)

- Only make changes the approved plan requests.
- Prefer positive craft over long ban lists, but MUST strip: hue gradients on chrome, gradient text, glows, emoji-as-icons, hype/AI-powered copy, looping decorative motion, `transition-all`, unverified claims.
- One accent; tinted neutral ramp; quiet chrome; richness only in Moments.
- Ask before: deleting files, adding dependencies, changing global theme tokens, changing mixer palette, touching Home Moises-measured geometry, or expanding scope.
- Stop after each wave for human review + screenshots.
- Never commit/push unless explicitly asked in that conversation.
- `ponytail`: smallest correct diff; reuse existing patterns; no new deps.
- `impeccable` allowed verbs only: `document` / `critique` / `quieter` / `distill` / `clarify` / `typeset` / `layout` / `polish` / `shape`. Forbidden as unslop path: `bolder`, `overdrive`, `delight`.

### Wave 0 — Direction freeze + inventory snapshot

**Files:** Create [`docs/plans/unslop/2026-11-18-app-unslop.md`](docs/plans/unslop/2026-11-18-app-unslop.md) from this plan (once approved). Optional: `impeccable document` notes pointing at existing tokens — do not invent a new DESIGN.md world.

- [ ] Confirm Direction text + three scope defaults
- [ ] Paste durable plan to `docs/plans/unslop/`
- [ ] Capture baseline screenshots: SPA `/login`, `/isolate`, `/tab`; desktop Home, Isolate Home, mix tab (human or later dogfood)

**Do not touch:** any product code.

**Done when:** Human approved Direction; plan file on disk; baselines noted.

---

### Wave 1 — SPA shell chrome (`quieter` + Color/Motion/Spacing)

**Modify:** [`web/src/styles.css`](web/src/styles.css) (body background, topbar density, skeleton motion). Touch [`web/src/App.tsx`](web/src/App.tsx) only if nav weight/copy needs quieting.

**Do not touch:** mixer engine ([`web/src/mixer/engine.ts`](web/src/mixer/engine.ts)), pan law, Home desktop tokens, `purple-gold` preset deletion, Isolate page logic.

**Passes:** Spacing → Color → Motion first (strip washes/shimmer); Icons/Copy only if shell strings offend.

- [ ] Replace body radial/linear hue washes with quiet paper from light ramp (`--paper` / tinted neutral)
- [ ] Replace infinite shimmer with static muted skeleton or one short fade
- [ ] Align topbar gaps to 4px grid; keep Satoshi brand mark
- [ ] Run: `cd web && npm test` · `npx tsc --noEmit`
- [ ] Screenshots: login + isolate empty state
- [ ] Human review stop

**Done when:** Shell no longer reads as "AI green nebula"; brand still moss/Satoshi; tests green.

---

### Wave 2 — SPA key pages + Operate copy (`clarify` / `distill`)

**Modify:** [`LoginPage.tsx`](web/src/pages/LoginPage.tsx), [`IsolatePage.tsx`](web/src/pages/IsolatePage.tsx), [`TabPage.tsx`](web/src/pages/TabPage.tsx), [`SettingsPage.tsx`](web/src/pages/SettingsPage.tsx), [`ProcessingModeSelect.tsx`](web/src/components/ProcessingModeSelect.tsx), [`JobProgress.tsx`](web/src/components/JobProgress.tsx), [`trackOptions.ts`](web/src/trackOptions.ts) **only if** labels need sentence-case / trailing-period / hype strip (preserve honesty caveats).

**Do not touch:** job APIs, hosted `lite` semantics, YouTube (SPA has none).

- [ ] Copy pass: no greetings, no `!`, no trailing periods on labels, keep bleed/weight caveats
- [ ] Hosted mode labels stay distinct from Desktop Interface Lite (`Low RAM (60 s)` stays)
- [ ] Empty/error states: blunt, product-specific
- [ ] Run: `cd web && npm test` · focused vitest for touched files
- [ ] Human review stop

**Done when:** Copy sounds like Audio Tools; no feature/flow change.

---

### Wave 3 — SPA StemMixer + PracticeSheet (`typeset` / `layout` / Moments)

**Modify:** [`StemMixer.tsx`](web/src/components/StemMixer.tsx), [`PracticeSheet.tsx`](web/src/components/PracticeSheet.tsx), mixer sections in [`styles.css`](web/src/styles.css) (practice heading, weights, spacing).

**Do not touch:** [`engine.ts`](web/src/mixer/engine.ts) wake hooks / pan / bounce math; desktop mixer (separate wave).

- [ ] Fix `.practice-heading` uppercase/tracking/700
- [ ] Quiet chrome around waveforms + practice sheet (Moments stay rich)
- [ ] Named transitions only; no `transition-all`; no hover-scale cards
- [ ] Run: `cd web && npm test` (engine/pan/practice tests)
- [ ] Human review stop

**Done when:** Mixer chrome quieter; waveforms/practice remain the bright element.

---

### Wave 4 — Desktop Streamlit chrome + pages (`quieter` / `clarify`)

**Modify:** [`ui/app.py`](ui/app.py) injected CSS/sidebar copy only as needed; page strings in [`isolate.py`](ui/pages/isolate.py), [`youtube_audio.py`](ui/pages/youtube_audio.py), [`tab_pdf.py`](ui/pages/tab_pdf.py); outcome/help strings in [`isolate_state.py`](ui/isolate_state.py).

**Do not touch:** [`ui/design_tokens.py`](ui/design_tokens.py) Home token values; Home §13 geometry; job queue/engine; Lite↔Pro logic.

- [ ] Strip decorative hover transforms / loud Streamlit chrome overrides that compete with Moments
- [ ] Copy pass on captions/help (keep Lite vs Pro wording accurate)
- [ ] Outcome cards: tighten only; keep blunt bleed honesty
- [ ] Run: `python -m pytest tests/test_ui_pages.py tests/test_isolate_state.py -q` (and any test asserting strings you change)
- [ ] Dogfood: Home → Isolate New → queue (human/`dogfood`)
- [ ] Human review stop

**Done when:** Desktop chrome quieter; Lite/Pro still clearly Interface mode; Home geometry intact.

---

### Wave 5 — Desktop Home component (optional ≤3 refinements)

**Modify:** [`ui/home_component/frontend/src/`](ui/home_component/frontend/src/) **only if** audit finds a residual tell.

**Do not touch:** measured widths/heights/gaps from §13; Home token hexes; global presets.

- [ ] At most three refinements (e.g. one spacing nudge, one type weight, one copy string)
- [ ] Rebuild: `make home-build`
- [ ] Run: relevant Home/component tests if present
- [ ] Human review stop — **skip wave entirely if no-slop confirmed**

---

### Wave 6 — mix-tabs iframe

**Modify:** [`ui/mix_tabs_component/frontend/src/main.ts`](ui/mix_tabs_component/frontend/src/main.ts), [`style.css`](ui/mix_tabs_component/frontend/src/style.css).

**Do not touch:** tab state protocol with Streamlit; 48px host height contract.

- [ ] Nine-pass polish; keep neutral edge fades
- [ ] Rebuild: `make mix-tabs-build`
- [ ] Run: `python -m pytest tests/test_mix_tabs_component.py -q`
- [ ] Human review stop

---

### Wave 7 — region-picker iframe

**Modify:** [`ui/region_picker_component/frontend/src/`](ui/region_picker_component/frontend/src/).

**Do not touch:** region report protocol / wavesurfer timing contracts.

- [ ] Quiet chrome; waveform remains Moment
- [ ] Rebuild: `make region-picker-build`
- [ ] Run: `python -m pytest tests/test_region_picker_component.py -q`
- [ ] Human review stop

---

### Wave 8 — stem-mixer iframe (desktop Moments)

**Modify:** [`ui/stem_mixer_component/frontend/src/style.css`](ui/stem_mixer_component/frontend/src/style.css), UI strings in [`main.ts`](ui/stem_mixer_component/frontend/src/main.ts) only as needed.

**Do not touch:** `pan.ts`, metronome click math, wake hooks (`installWakeHooks` parity with web), stem color palette, `--stem-wave-height` behavior, export-on-Save contract.

- [ ] Spacing/type/details polish; strip any glow/`transition-all`/decorative loop
- [ ] Keep waveforms + practice panel as Moments
- [ ] Rebuild: `make mixer-build`
- [ ] Run: `python -m pytest tests/test_stem_mixer_component.py -q`
- [ ] If CSS vars shared with web mixer chrome: note parity; do not force palette merge
- [ ] Human review stop

---

### Wave 9 — Cross-surface verification

**Skills:** `verification-before-completion`; SPA `agent-browser` + `browser-uat-analyst`; desktop `qa` / `exploratory-qa` / `dogfood`; then `ponytail-review` or `code-review` on the branch diff.

- [ ] Template check on SPA + desktop Home + mix tab
- [ ] Confirm Lite labels never conflated
- [ ] Confirm no `frontend/build` hand-edits; builds committed after rebuilds
- [ ] Confirm Home §13 + mixer palette + global tokens untouched unless explicitly approved mid-wave
- [ ] Final human review

---

## 7. Risk register

| Risk | Mitigation |
|------|------------|
| Theme-token collision (`design-tokens.css` vs Home `design_tokens.py`) | Never "unify" Home into shared CSS for unslop; ask before global token edits |
| Mixer palette drift | Wave 8 do-not-touch palette; functional fills stay |
| Home Moises geometry regression | Wave 5 capped; §13 is source of truth |
| Streamlit full-rerun quirks | CSS/copy-only; restart Streamlit after `ui/` edits; no logic refactors |
| Committed build drift | Rebuild + pytest component tests every iframe wave |
| Dual brand (moss SPA vs Tyrian desktop) | Intentional; unslop within each world |
| String-asserting tests | Grep tests before renaming labels; update assertions in same wave |

---

## 8. Forbidden actions + stop conditions

- No feature invention, marketing pages, stats, unverified claims
- No product rename; no Moises asset/font/markup copy
- No `bolder` / `overdrive` / `delight` as the unslop path
- No unifying Desktop Interface Lite with hosted `lite`
- No hand-edit of hashed `frontend/build/**`
- No engine / metronome / hardware-gate / pan-law changes
- **Stop** if a wave needs global token or mixer palette change → ask human
- **Stop** after each wave for screenshots + review
- **Stop** if template check still passes with a swapped product name → push Moments/Signature/copy, not chrome effects

---

## 9. Suggested follow-up Agent prompts (one wave each)

1. **Wave 0:** "Load approved plan `docs/plans/unslop/2026-11-18-app-unslop.md`. Freeze Direction; write the durable plan file; capture baselines. No product code."
2. **Wave 1:** "Execute Wave 1 only (SPA shell chrome) from that plan. Skills: `executing-plans`, `unslop-ui` polish, `impeccable quieter`. Stop for screenshots."
3. **Wave 2:** "Execute Wave 2 only (SPA pages + copy). Skills: `unslop` clarify + `unslop-ui` copy pass. Preserve honesty caveats and hosted `lite` wording."
4. **Wave 3:** "Execute Wave 3 only (SPA StemMixer/PracticeSheet typeset/layout). Do not touch `mixer/engine.ts` math."
5. **Wave 4:** "Execute Wave 4 only (Streamlit chrome + page copy). Do not touch Home tokens or Lite↔Pro logic."
6. **Wave 5:** "Execute Wave 5 only if residual Home tells exist; else mark skipped. Max 3 refinements; `make home-build`."
7. **Wave 6:** "mix-tabs unslop + `make mix-tabs-build` + `tests/test_mix_tabs_component.py`."
8. **Wave 7:** "region-picker unslop + `make region-picker-build` + component test."
9. **Wave 8:** "stem-mixer iframe unslop; preserve palette/wake/pan/metronome; `make mixer-build` + component test."
10. **Wave 9:** "Verification wave only: `verification-before-completion`, SPA browser UAT, desktop dogfood, `ponytail-review`."

---

## Done when (this Plan session)

- [x] Skills loaded in order (explore subagents failed twice — continued with graphify + direct Read/Grep)
- [x] Inventory covers web + ui + three iframes (+ Home component documented as locked)
- [x] Audit lists concrete file-anchored findings
- [x] Direction written + explicit approval gate
- [x] Waves sequenced with rebuild/test/do-not-touch
- [x] Moises/Home/token/mixer locks + Lite non-unification explicit
- [x] No code edited in Plan mode