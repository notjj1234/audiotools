# Review and improvement plan — AudioTools (desktop + website)

Date: 2026-11-24 · Phase 1 only (review + plan). **Nothing in the app was changed.** Phase 2 starts only after you approve items from §6.

How this was made:
- I read the code (`src/audio_to_tab/`, `ui/`, `backend/`, `web/src/`), the project's own research (`docs/research/moises/*`, `docs/plans/moises-parity/*`, `eval/lead_rhythm/RESEARCH.md` + `RESULTS.md`), and I ran the project's lead/rhythm scorer plus one extra probe (§4.2).
- **Follow-up 2026-11-24:** a second online pass (public APIs of Hugging Face, GitHub, arXiv, Zenodo, MVSep, the Moises help center, plus the LALAL.AI homepage) is in **§4.5**. It updates the Moises, LALAL.AI and MVSep rows below.
- **Online research limit (first pass):** this session had no web-browsing tool. Competitor facts below come from (a) your repo's own dated research with its cited sources, or (b) my general knowledge, marked **[unverified]**. The [unverified] items include a link you can check. I did not re-open Moises.app (2.1.0 is installed). Your repo already has a 2.1.0 static teardown, and Moises' player is hosted, so a local static pass would add little.

---

## 1. Map of the current app

### 1.1 Products and screens
| Product | Screens / surfaces | Runtime |
|---|---|---|
| **Desktop** (Streamlit in a native window, `packaging/launcher.py`) | Home (library, recents, setlists) · Audio Isolation (Home\|mix\|+ tab strip, upload/YouTube search, Lite outcome cards or Pro stem grid, region picker, queue, live mixer with optional synced video, Downloads) · YouTube to MP3 (save only) · Tab PDF · Settings | Local; serial isolate queue (`ui/isolate_jobs.py`) |
| **Website** (FastAPI + React + Caddy) | `/login`, `/isolate` (upload, processing mode, region picker, Web Audio mixer, practice sheet), `/tab` | Postgres/Redis/MinIO + arq worker |
| **Shared engine** `audio_to_tab` | isolate, separate, roformer, scnet, lead_rhythm, metronome, analysis (chords/key/sections/lyrics/chart), tab pipeline | — |

### 1.2 User flow (desktop)
Home → Audio Isolation → pick file or YouTube → Lite: choose an outcome ("Every part separately", "Guitar on its own", "Vocals + backing track", "Vocals on its own") with auto speed/device, or Pro: pick stems, engine, speed, and advanced guitar options → optional section (region) → queue → stages: separate → fold/diagnostics → (optional lead/rhythm) → presence → metronome → analysis → tab → mix tab opens: solo/mute/volume/pan per stem, master, rate 0.5–1.5×, ±semitones, A/B loop, count-in 0–2 bars, live metronome (accent/rate/sound), Chords/Sections/Lyrics/Tab panel, synced picture → Save current mix → export.

### 1.3 Separation pipeline (what actually runs)
| Stage | Default | Opt-in alternatives |
|---|---|---|
| Stage-1 model | **`htdemucs_6s`** (Demucs v4, 6 stems), `quality="fast"` → `--shifts 0 --overlap 0.25`, `--segment 8`, `--jobs 1` (`isolate.py:130-131, 846-880`). Guitar jobs get a quality floor of `balanced` (`GUITAR_QUALITY_FLOOR`, shifts 1). | `htdemucs`/`htdemucs_ft` (4-stem, guitar stays in `other`), BS-RoFormer-SW 6-stem, MelBand-RoFormer guitar refine, SCNet 4-stem, community `htdemucs_6s_guitar_ft` (~330 MB), two-pass (4-stem then 6s on residual), RoFormer+Demucs guitar ensemble |
| Quality presets | fast 0/0.25 · balanced 1/0.25 · high 3/0.5 · extreme 5/0.75 (shifts/overlap) | Pro overrides |
| Post-process | `fold_other_mode="best_effort"` (fold leftover `other` into guitar unless it looks like keys/silence), guitar-stem quality diagnostics | bleed gate, adaptive fold gain, bass-bleed HPF, sub-bass de-bleed, low-end restore, pre/refined guitar variants |
| Lead/Rhythm | **Off.** Pro-only checkbox "Split lead and rhythm guitar", enabled only for `htdemucs_6s` (`ui/pages/isolate.py:1956`, `ui/isolate_state.py:2689`) | `confident` (default) or `best_effort` emit; CLI thresholds |
| Device | GPU-first (CUDA, or MPS at ≥12 GB RAM); CPU floor on 8 GB Macs | — |
| After stems | stem presence, metronome click stem, analysis (beats → key → chords → sections → lyrics → chart), tab (Basic Pitch → tab → PDF) | BTC neural chords (`ATT_CHORD_MODEL=1`) |

### 1.4 Palette — every color in use (none will be changed)
**Desktop shell** (`ui/design_tokens.py`, `.streamlit/config.toml`, `ui/home_component`):
`#192542` page navy · `#2A4467` card blue · `#35557C` card hover · `#142033` art/darkest · `#F6AD49` amber accent (also Streamlit `primaryColor` and `textColor`) · `#F4F7FB` text · `#D5DEEA` text secondary · `#C5D0E0` meta/chip · `#B7C3D4` muted · `#A8B8CC` line.
`ui/app.py` adds `#E7E5E4`, `#FFFFFF`/`#FFF`.

**Desktop mixer iframe** (`ui/stem_mixer_component/frontend/src/style.css`, `main.ts`):
`#FF4B4B` (red, mute/solo/active states) · `#FFFFFF` · `#F6AD49` · `#192542` · `#F0F2F6` · `#31333F` · `rgba(49,51,63,0.14 / 0.18 / 0.2)` · `rgba(0,0,0,0.28 / 0.45)`.

**Theme presets** (`ui/theme_presets.py`, website `ThemeSelector.tsx`):
`#0A0F0A #0F150F #141A14 #163626 #1A1F1C #1E261E #1E4533 #255840 #2A342A #2F6B4F #2F8F87 #3AA8A0 #3ABDB4 #4ECDC4 #5F6368 #9AA0A6 #C4B498 #D4C4A8 #E4E7EB #E6B84A #E7EDF6 #E8EFE6 #F0F2F5 #F7F8FA #FFF6DC #FFFFFF #FBBF24 #FFCC53 #FFAB0F #F59E0B #F6AD49 #FF6B6B #E85D5D #8B5CF6 #7C3AED #A855F7 #9333EA #0EA5E9 #0284C7 #0369A1 #075985 #192542 #2A4467`.

**Website** (`web/src/styles.css`, `RegionPicker.tsx`): `#F7FAF7 #FDECEC #C45C26 #FFFFFF #000000 #1E4533 #2F6B4F #4A8F8A`, plus the CSS variables from the active theme preset.

Tints I may propose in Phase 2 (all from existing colors, none new): `#F6AD49` at 12% / 24% alpha (amber badge/fill on navy), `#A8B8CC` at 40% alpha (disabled/hairline), and the existing `rgba(49,51,63,…)` steps.

---

## 2. Teardown: Moises and similar tools

| Tool | Stems / guitar | Player & practice | Lead vs rhythm |
|---|---|---|---|
| **Moises** (2.1.0 desktop shell; studio/player hosted) | Premium: Vocals, Lead/Background Vocals, Bass, Guitars, Acoustic/Electric Guitars, **Lead/Rhythm Guitars**, Strings, Piano, Grand Piano, Keys, Winds, Drums; up to 5 instruments per upload (verified 2026-11-24, help article updated 2026-11-23: https://help.moises.ai/hc/en-us/articles/29530520103324). Marketing also claims 27 stem types (not run). | Tempo, pitch/key, loop, metronome/count-in, Chord Finder, Capo Mode, lyrics. Free tier: 5 uploads, 5-minute stems, first minute of chords and lyrics (help text P-S6-61..63 in `PAGE-INVENTORY.md`). The hosted player interior was **not** opened in your scans. | **Yes, as a premium option** (verified, same article): for guitars you pick *Guitars*, **or** *Acoustic + Electric*, **or** *Lead + Rhythm*, not all three. How it works and how good it is: **[unverified]**, no public technical write-up found. |
| **LALAL.AI** | Homepage stem list (fetched 2026-11-24): Vocals, Instrumental, Drums, Bass, Guitars, Acoustic Guitar, Electric Guitar, Piano, Synthesizer, Strings, Wind (https://www.lalal.ai/) | Web/desktop splitter, little practice tooling **[unverified]** | **Not listed** on the homepage (verified absent there; a hidden or paid option is **[unverified]**). |
| **MVSep** | A model hub with a public algorithm API. Guitar group (fetched 2026-11-24 from https://mvsep.com/api/app/algorithms): MVSep Guitar (best variant "BS Roformer SW", SDR 9.05), Acoustic Guitar, Electric Guitar, **Lead/Rhythm Guitar**, Pedal Steel | Separation only | **Yes, a dedicated model** (details in §4.5). Hosted only; no downloadable weights found. |
| **Ultimate Vocal Remover (UVR5)** | Open-source GUI over MDX-Net/VR/Demucs/RoFormer models **[unverified]** | None | No dedicated lead/rhythm model in its default set **[unverified]** — https://github.com/Anjok07/ultimatevocalremovergui |
| **RipX DAW** | Note-level "rip" of a mix into instrument layers **[unverified]** | Pitch/time editing per note | Manual: select a part's notes and move them to a new layer **[unverified]** |
| **Songsterr** (tab UX) | n/a (tabs, not audio stems) | Per-track solo/mute, speed, loop, count-in, metronome, synced tab cursor **[unverified]** | Tabs are split by transcribers into named tracks ("Lead", "Rhythm") **[unverified]** — https://www.songsterr.com/ |

UX patterns worth borrowing (pattern only, no artwork or markup): Moises shows the guitar choice **before** processing as mutually exclusive groups. A stem group in the mixer is a disclosure row (your own `COMPETITIVE-INSPIRATION-PLAN.md` already specifies this). Songsterr names parts clearly and lets you solo one part while the others keep playing quietly.

Published research your repo already cites: GuitarDuets (HT-Demucs adapted to 2 guitar outputs; second-guitar SDR is often weak) https://arxiv.org/html/2507.01172v1 · dataset https://zenodo.org/records/12802440 · Pati & Lerch 2017 solo detection · Foulon et al. 2013 playing-mode classification.

---

## 3. Gap analysis

### 3.1 Functionality
| Gap | Severity |
|---|---|
| **Lead/rhythm exists but is buried:** Pro only, `htdemucs_6s` only, nothing in Lite and nothing on the website (the API accepts `lead_rhythm`, but `web/src` never sends it). It also can't be run after the fact on a finished song. | High |
| **The split can't handle the most common real case.** The existing heuristic only splits by panning or by a fixed 400 Hz crossover. In many songs the *same* track is rhythm in the verses and lead in the solo, or the two guitars take turns. A time-based split (who plays when) is missing. | High |
| No stem choice like Moises' "Acoustic + Electric" (needs a model → out of scope unless you approve one). | Low |
| Practice tools are at or above Moises parity (rate, pitch, loop, count-in, live metronome, chords, sections, lyrics, **tab**). Tab plus local processing is your edge. | — (strength) |

### 3.2 Visuals / UI (palette untouched)
- The mixer iframe still uses Streamlit's default red `#FF4B4B` / grey `#31333F` system, while the shell is navy/amber. I won't change those values. Spacing, type hierarchy and state styling (hover/focus/active) can still be made consistent with the existing values.
- Lead and Rhythm show up as two unrelated rows. They should be grouped under Guitar (disclosure row with indented children), with a "low confidence" badge when the split is best-effort.
- The Pro advanced block is a long, flat list of experimental checkboxes ("experimental", "Hi-Fi", "Two-pass", "Split lead and rhythm"…). It would read better grouped as "Guitar options" with one-line plain help and a disabled-state reason.

### 3.3 Drawbacks (found in code, two confirmed by running it)
1. **Lead/rhythm stems are written as mono.** `_mono_to_stereo(lead_audio)` (`lead_rhythm.py:932-933`) folds both outputs to identical L=R. The double-tracked rhythm loses its width, which is exactly what a player wants to hear. *Confirmed: probe shows `L==R: True`.*
2. **The register (and spectral) split only processes the first 90 s and pads the rest with silence** (`build_register_pair`, `mono_work = mono[:max_samples]`, `lead_rhythm.py:465-483`). On a 4-minute song, both stems go silent after 1:30. *Confirmed: probe RMS 0–90 s = 0.10, 95–120 s = 0.0000.* The 90 s window was meant for analysis but is used for rendering.
3. **The hard-pan split switches per sample** (`np.where(|L|>=|R|, L, L-0.5R)`, `lead_rhythm.py:374-375`). That's a non-linear operation that creates distortion. Even on clean, hard-panned test sines it scores only ~8 dB SI-SDR (`RESULTS.md`, reproduced). Passing L and R through, or masking per frequency bin, would score far higher.
4. **The "register" split is a crossover EQ, not a part split.** Power chords have strong harmonics above 400 Hz and lead notes on the low strings sit below it, so "high band = lead" is often wrong.
5. **The mild-pan path uses a static frequency mask** built from one dominant pitch measured in the first 4 s of each channel. That's an EQ, not tracking.
6. **Guitar-ft fallback is inconsistent and silent:** the isolate path falls back to stock weights with only a log warning (`isolate.py:2178`), while the Tab PDF path refuses (`separate.py:589-607`). The user isn't told which weights were used.
7. Lead/rhythm runs even when the guitar stem was judged near-silent (presence is checked after the split).
8. Performance: CPU-only 8 GB Macs are slow (by design, serial). Lead/rhythm with Basic Pitch adds two transcription passes per candidate stream. Role features use an O(n²) note-overlap loop (`extract_role_features_from_notes`), which is fine for 90 s windows but would hurt if windows grow.

### 3.4 Fallbacks
| Situation | What happens now | Fallback? |
|---|---|---|
| Lead/rhythm low confidence / one guitar | `confident` mode keeps the single Guitar and writes `guitar_split_diagnostics.json` with a reason | **Partial: the user is never told.** `_load_guitar_split_diagnostics()` (`ui/pages/isolate.py:1037`) is defined but **never called**. The split just silently doesn't appear. |
| Lead/rhythm `best_effort` | Always writes two stems, presence marks them "low confidence" | Labels can be wrong; no visible badge |
| RoFormer/SCNet not installed | Clear error before the job starts (`isolate.py:2302`, `ui/pages/isolate.py:4359`) | Yes (refuses with install hint) |
| Guitar-ft download/load fails | Isolate: silent fallback to stock · Tab PDF: hard error | Inconsistent (§3.3-6) |
| Guitar refine fails | Keeps first-pass guitar, log warning (`separate.py:355`) | Yes, silent |
| Mono file | Duplicated to stereo, so spatial/mid-side refuse and only register can split | Yes, but see §3.3-2/4 |
| Live recordings / heavy bleed | No special handling; bleed diagnostics only | None (acceptable; documented limit) |
| No guitar in the song | Presence marks guitar absent; lead/rhythm still runs on the near-silent stem | Weak |
| Very long files | Desktop doesn't clamp (by design, I-500); `--segment 8` bounds Demucs RAM; lead/rhythm loads the whole stem into RAM (fine to ~20 min) | Mostly OK |
| Separation crashes | Job marked failed, retry/dismiss strip, readable error (`format_job_error`) | Yes |

---

## 4. Lead vs rhythm guitar research

### 4.1 Which signals actually work
| Signal | Reliability | Why |
|---|---|---|
| **Polyphony** (chords vs single notes) | **High** | The best single discriminator. Basic Pitch (already a dependency) gives simultaneous-note counts per frame. |
| **Time / section role** (who is playing *when*) | **High** | Solos usually happen when **vocals are silent**, and the vocal stem already exists. Sections are already detected (`sections.py`). Many songs never have both parts in one region of the stem at once. |
| **Stereo placement** (per-frequency pan index, mid/side) | High *when present* | Double-tracked rhythm panned L/R with a centered lead is common in rock/metal. Useless on mono or centered mixes. |
| **Register** (median pitch of notes) | Medium | Lead tends to sit higher, but not always (low riff leads, high-voiced chords). Use pitch from notes, never a fixed EQ crossover. |
| **Articulation** (bends, vibrato, sustain vs repeated palm-muted onsets) | Medium | Pitch-curve deviation and onset regularity are measurable from Basic Pitch's pitch-bend output and the onset envelope. |
| **Gain / brightness / loudness** (your starting idea) | **Low as a primary cue** | Rhythm in rock/metal is often equally high-gain, so spectral flatness and centroid overlap heavily. Use it only as a tie-breaker. Loudness relative to the guitar stem's own average *does* help detect solo sections. |

### 4.2 Evidence from running your current implementation
- Project scorer (`score_lead_rhythm.py --no-basic-pitch`, confident mode, 5 synthetic clips): hard-pan and mild-pan emit with correct labels, while mono / centered-overlap / double-track correctly refuse. This matches your committed `RESULTS.md`, but hard-pan SI-SDR is only **8.0 dB** on clean sines.
- Extra probe (120 s synthetic centered stem, chords low + vibrato lead high, `best_effort`): method `register`, outputs **mono** and **silent after 90 s** (§3.3-1/2).
- No real-song test was possible: `eval/lead_rhythm/clips/` holds only synthetic clips, and real multitracks need rights you hold. **[unverified on real music]**

### 4.3 Three approaches compared
| | (a) Dedicated pretrained model | (b) Feature-based heuristic | (c) Hybrid (model-first, heuristic fallback) |
|---|---|---|---|
| Availability | **No open, downloadable lead/rhythm checkpoint exists** (re-checked 2026-11-24, §4.5). The strongest model is **MVSep's hosted "Lead/Rhythm Guitar"** (SDR 9.21), reachable only through their web API. Moises' version is closed and in-app only. Otherwise you'd have to train one yourself. | Exists today (`lead_rhythm.py`) and can be fixed and extended with **no new dependencies** (numpy, librosa, basic-pitch, pretty_midi are already in `pyproject.toml`). | Needs (a) for the "model" half. Until then it equals (b) plus a slot for a model. |
| Expected quality | Best on simultaneous, centered overlap, but published 2-guitar results are weak for the second guitar (GuitarDuets). | Good when parts are panned apart or alternate in time. Poor when both play at once, centered, in the same register. | Best of both, honest about it. |
| Runtime | One more Demucs-class pass on the guitar stem (≈ the cost of stage 1 on the guitar only; minutes on CPU), plus ~100–300 MB weights **[estimate]** | Seconds (DSP) to ~1–2 min (Basic Pitch on a full song, CPU) **[estimate]** | Model + heuristic |
| Dependencies | New weights download (SHA256-pinned urllib per your rules); possibly training infra | None new | Same as (a) |
| One guitar only | Still outputs two streams (one near-empty or a cut of the same part), so it needs a presence/correlation gate | A gate can refuse cleanly, *or* a time-based split can correctly assign verse riff → Rhythm and solo → Lead from a single player | Gate from (b) applies to both |

### 4.4 Recommendation
**(c) Hybrid, built now as a stronger (b) with a model slot**, so a model can later be plugged in only if you approve one:

1. **Time-role segmentation (new, main path).** Cut the guitar stem into beat-aligned windows (the beat grid already exists). Score each window as lead-like or rhythm-like from polyphony, note pitch, pitch-bend/vibrato, onset regularity and **vocal activity** (from the vocal stem). Smooth the decisions over time (no flicker), then route windows to Lead or Rhythm with short crossfades. This handles one player switching roles and two guitars taking turns, which is the case the current code can't do.
2. **Simultaneous parts, when the evidence exists:** a per-frequency-bin stereo mask (azimuth/pan index on the STFT) instead of per-sample switching, and a note-informed harmonic mask (from Basic Pitch notes of the monophonic top voice) instead of a fixed crossover. Output stays **stereo**.
3. **Gate and fallback (required):** the split is emitted only if (i) at least ~15% of the song's guitar time is assigned to each role, (ii) role confidence clears a threshold, and (iii) the guitar stem is actually present. Otherwise: keep a single **Guitar** stem and show a plain message in the mixer, for example *"Kept one Guitar track: only one guitar part was found"* / *"…the two parts play together in the same place in the mix, so they couldn't be pulled apart cleanly."* When split, show a confidence badge.
4. **Model slot:** a small interface (`split_lead_rhythm_guitar(..., backend="heuristic"|"model")`) so a future approved checkpoint runs first and the heuristic is the fallback. **No model is added in this plan.** After the 2026-11-24 research, the only real candidate for that slot is the optional MVSep cloud backend (**MODEL-1**, §6), which needs your separate approval.

Honest ceiling: two guitars playing at the same time, dead-center, in the same register will still not separate cleanly without a trained model. The gate is there so the app says so instead of producing wrong stems.

### 4.5 Model research — follow-up pass (2026-11-24)

Searched: Hugging Face model API ("rhythm guitar", "lead guitar", "lead rhythm", "guitar separation", every "guitar" model sorted by downloads, and the main community separation uploaders), GitHub repository search, the arXiv API, Zenodo, MVSep's public algorithm API, the UVR model list, ZFTurbo's Music-Source-Separation-Training model list, the Moises help center, and the LALAL.AI homepage.

| Candidate | What it is | Downloadable / runs locally? | License | Quality evidence | Fit for this app |
|---|---|---|---|---|---|
| **MVSep "Lead/Rhythm Guitar"** (algorithm id 98, added 2025-11-20) | Dedicated model. Outputs `lead-guitar`, `rhythm-guitar`, `all-guitar`, `no-guitar`. Two variants: **two-stage (SDR 9.21)** and one-stage (SDR 9.02). 16,070 uses, user rating 4.57/5 (79 votes). Source: https://mvsep.com/api/app/algorithms | **No.** Hosted on MVSep servers, reachable through their API with a user token. No weights found on Hugging Face, GitHub or in ZFTurbo's public model list. | Service terms; no open license (`nc_license` empty in their API) | MVSep's own SDR on their own test set. Not independently verified. Their architecture isn't documented, so "two-stage" probably means guitar first, then lead/rhythm **[unverified]**. | Best quality available today, but it **uploads the user's song to a third party**, needs internet and an MVSep account, and has usage limits (a third-party app's README says a free account allows 50 separations/day **[unverified]**: https://github.com/NikolajChristensen/ncosis). This breaks the app's local-first promise unless strictly opt-in. |
| **Moises Lead/Rhythm Guitars** | Premium in-app option (verified, help article updated 2026-11-23) | No (closed, in-app) | Proprietary | None published | Competitor reference only |
| **GuitarDuets** (ISMIR 2024, arXiv 2507.01172) | Training code for 2-guitar separation + dataset of ~3 h **classical** guitar duets | Code yes (https://github.com/mariosgly/guitarduets, **no license file**); dataset yes (https://zenodo.org/records/12802440, **CC-BY-4.0**); **no released checkpoint found** | Code: none stated; data: CC-BY-4.0 | Paper reports the second guitar is often poorly separated (from your 2026-08-24 notes) | Would need training **and** isn't about lead vs rhythm (two classical guitars, no electric, no roles). Weak fit without a lot of extra data work. |
| **becruily MelBand-RoFormer Guitar** (HF, already used by your refine step) | Guitar vs rest, **not** lead vs rhythm | Yes (`becruily_guitar.ckpt`) | **No license in the model card** (worth checking since you already ship support for it) | Community | Stage-1 quality only |
| **htdemucs-6s-guitar-ft**, **demucs-guitar-lora** (HF) | Guitar vs rest | Yes | Varies / unstated | Community | Stage-1 quality only |
| `Z301b/UlteriorMotives-RhythmGuitar` (HF) | The only HF name hit for "rhythm guitar": a single zip with no model card | Unknown | None | None | Not a usable separator; ignore |
| Other open apps (e.g. `quantumq1981/Guitar-Piano-Audio-Stem-Extract`, MIT) | Their README says lead/rhythm is a **DSP heuristic "because no openly licensed ML model exists yet"** | — | — | — | Confirms the gap is industry-wide in open source |
| arXiv | Nothing on lead-vs-rhythm electric guitar separation besides GuitarDuets. Related transcription papers exist (guitar rhythm-pattern transcription 2510.05756, strumming direction + chords 2508.07973) | — | — | — | Could inform role *features* later, not separation |

**Conclusion.** There is no strong, open, downloadable lead/rhythm model today. The only dedicated model with published numbers is MVSep's, and it's cloud-only. So the recommendation in §4.4 stands, with one addition: the "model" half of the hybrid can be an **optional, off-by-default MVSep cloud backend** (MODEL-1), and the improved local heuristic stays the default and the fallback. Training your own model (MODEL-2) is possible, but there is no ready lead/rhythm-labelled electric guitar dataset, so it's a research project rather than a feature.

---

## 5. Unknowns
- How Moises implements Lead + Rhythm and how good it is: **[unverified]** (that it exists is now verified).
- MVSep offers a lead/rhythm model (verified); how good it is on your songs, and its exact limits and terms for app use: **[unverified]**. LALAL.AI doesn't list one on its homepage.
- Quality on real songs: needs 2–3 rights-cleared clips from you (e.g. your own multitracks), or your listening judgement on songs you own.

---

## 6. Prioritized plan (approve any subset by ID)

All items: **no new dependencies, no model downloads, no schema changes, and the default separation flow is unchanged** (lead/rhythm stays off unless toggled). No palette value changes.

| ID | Item | Impact | Effort | Files | New dep |
|---|---|---|---|---|---|
| **LR-1** | Fix the existing split's defects: stereo output (no mono fold), render the **full song** (90 s window used for analysis only), replace per-sample L/R switching with per-bin STFT stereo masks, skip when the guitar stem is near-silent | High | S–M | `src/audio_to_tab/lead_rhythm.py`, `tests/test_lead_rhythm.py` | none |
| **LR-2** | Time-role segmentation engine (beat-aligned windows; polyphony, pitch, bend/vibrato, onset regularity, vocal-activity cue; smoothing + crossfades) as the primary method, with the existing spatial/mid-side as the simultaneous-part path and register demoted to a note-informed mask; new gate (min share per role + confidence + presence); model-slot interface | High | M–L | `src/audio_to_tab/lead_rhythm.py`, `src/audio_to_tab/isolate.py` (pass vocal stem + beat grid to the split), `tests/test_lead_rhythm.py`, `eval/lead_rhythm/make_synthetic_clips.py` (add a "one player switches role" and a "trade-off" clip), `eval/lead_rhythm/score_lead_rhythm.py` | none |
| **LR-3** | Tell the user why: show the split outcome in the mix tab (plain message when kept as one Guitar; "low confidence" badge when best-effort) by wiring the existing `_load_guitar_split_diagnostics` | High | S | `ui/pages/isolate.py`, `ui/isolate_state.py` (message helper), `tests/test_isolate_state.py` | none |
| **LR-4** | Make the toggle reachable: available for any engine that produces a guitar stem (Demucs 6s, guitar-ft, RoFormer, ensemble), offered on the Lite "Guitar on its own" / "Every part separately" cards as an off-by-default option, plus a "Split guitar into lead/rhythm" action on a finished run (post-process only; no re-separation) | High | M | `ui/isolate_state.py`, `ui/pages/isolate.py`, `ui/guitar_fixup.py`, `ui/isolate_jobs.py`, tests | none |
| **UI-1** | Mixer: group Lead + Rhythm under a Guitar disclosure row with indented children and a confidence badge; consistent hover/focus/active states and spacing in the mixer using existing colors only | Med | M | `ui/stem_mixer_component/frontend/src/main.ts`, `style.css`, rebuild (`make mixer-build`), `tests/test_stem_mixer_component.py` | none |
| **UI-2** | Pro advanced options: group into "Guitar options", each with one-line help and a stated reason when disabled; no colors changed | Med | S | `ui/pages/isolate.py` | none |
| **FB-1** | Guitar-ft honesty: record "used stock weights because …" in the run's diagnostics and show it (isolate path behavior unchanged, just surfaced) | Med | S | `src/audio_to_tab/isolate.py`, `ui/pages/isolate.py`, tests | none |
| **WEB-1** | Website parity: lead/rhythm toggle on `/isolate` (API already supports it) + show the split message in the web mixer | Med | M | `web/src/pages/IsolatePage.tsx`, `web/src/trackOptions.ts`, `web/src/components/StemMixer.tsx`, `web/src/api.ts`, vitest | none |
| **DOC-1** | Update `PROJECT_TREE.md`, `eval/lead_rhythm/README.md`, and append a `docs/ui-issues.md` entry from **I-624** | Low | S | docs | none |

Suggested order: **LR-1 → LR-3 → LR-2 → LR-4 → UI-1 → FB-1 → UI-2 → WEB-1 → DOC-1**. (LR-1 and LR-3 are quick wins that make the existing feature trustworthy. LR-2 is the real upgrade.)

Testing plan for lead/rhythm (Phase 2): unit tests on synthetic stems with known ground truth (hard-pan, mild-pan, one-player-switches-role, trade-off, centered overlap, mono single, no guitar). Pass criteria: correct labels, SI-SDR vs ground truth higher than the current implementation on hard/mild pan, stereo preserved, full-length output, and the gate refusing on mono-single and centered-overlap with the right user message. Plus `make test` and `ruff`. Real-song listening is up to you on tracks you own. I'll state that it wasn't verified by me.

Optional model items. Each needs your **separate, explicit approval** because each goes beyond "no new dependency / no download / local only":

| ID | Item | Impact | Effort | Files | Needs |
|---|---|---|---|---|---|
| **MODEL-1** | Opt-in **MVSep cloud** lead/rhythm backend: off by default; the user pastes their own MVSep token in Settings; a clear "this uploads the guitar stem to MVSep" notice; send only the already-isolated guitar stem (not the full song); fall back to the local heuristic on no network, errors or quota. Desktop only at first; on the website it must stay off. | High (best available quality) | M | new `src/audio_to_tab/lead_rhythm_mvsep.py`, `src/audio_to_tab/lead_rhythm.py` (backend slot), `ui/pages/isolate.py` + Settings, tests with a mocked HTTP server | No new pip package (stdlib `urllib`), but **network access, a third-party account, and sending user audio off the machine**. You'd also need to check MVSep's terms for use inside an app. |
| **MODEL-2** | Train your own 2-source lead/rhythm model (HT-Demucs-style second stage on the guitar stem). Needs a lead/rhythm-labelled electric guitar dataset that doesn't exist publicly (e.g. built from multitracks you have rights to). | High if it works | L+ (research) | new training code outside the app | Training data, GPU time, then a SHA256-pinned weights download |
| — | Acoustic/electric split model | Low | M | — | Model download |
