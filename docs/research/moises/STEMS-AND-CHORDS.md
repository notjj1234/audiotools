# Stems and chords — Moises macOS 2.1.0 — 2026-11-07

Same install as [CORE.md](CORE.md). This run reused E-SHELL-MAC. It did not open the asar again and it did not log in, upload, or start a separation. The song was already open. Screenshots stayed in `/tmp` and are not part of this repo. Our column is code behavior, not a paired listening: `separate_stems()`, `detect_chords()`, and `detect_chords_btc()` were not run on this clip.

## Identity

| Fact | Value | Status |
|---|---|---|
| Bundle | `/Applications/Moises.app` | observed, same path as CORE |
| Version | `2.1.0` | observed, carried forward |
| Build | `261021a1gygumpb` | observed, carried forward |
| Asar SHA-256 | `6a42619e39f7ca3c98085e2c2cbcd8fa90397ace6dd133c40c551eee070ef05a` | observed, E-ASAR-MCP / CORE |
| Shell evidence | E-SHELL-MAC `ev_7be46619691e43141db26504f846bce4e818e945c87b5d949b14a758958e4231` | reused. No new REA id |
| Page | Play, song title **フルスピード・ボーイ** | observed on the tab and in `tabs.json` |
| Transport | `0:39 / 4:50`, `30 bar / 224 bars`, `186 bpm / E`, time signature shown as 1 2 over 3 4 | observed. The playhead was not moved |

`tabs.json` lists that tab as a `/play/<id>` URL with `project_open_source=library` on `https://studio.moises.ai`. The id is an account resource and is not copied here.

## What the shell search added

The offset-corrected extract `/tmp/moises-mac-2.1.0-shell` was still on disk: eight files, no weight file in the tree. One case-insensitive search of those files found `upload/split` twice, `studio.moises.ai` once, and `studio-stage.moises.ai` once. The same search found no `.onnx`, `.safetensors`, `.tflite`, `.mlmodel`, `.ckpt`, `.pth`, or `.gguf` name, and no Demucs, Spleeter, Roformer, ONNX Runtime, TensorFlow, Essentia, librosa, CREPE, Chordino, or Basic Pitch name. That search has no REA id. The other files inside the asar were not searched.

Inferred from that search plus E-SHELL-MAC: the shell’s split entry is a hosted Play URL, not a model stored in those eight files. Unknown: a weight file outside that extract, and whether the hosted page then runs the math in the browser or on a server. No request was captured, so there is no method, path, or JSON field from a live call.

## Stems

### Where it runs

Hosted Play page inside the desktop window. The local shell does not contain a stem model in the files searched above. The result on screen is the hosted page. Which process produced the waveforms was not visible. `DevToolsActivePort` named port 9333, and nothing was listening there, so the page was not inspected through a debugger.

### Entry the user takes

The song was already loaded from the library. The view has a **Stems** control next to Lyrics, Chords, and Shapes. A **Separate Stems** button sits above the lanes. That button was not clicked. The lanes already had waveforms, so this is a finished split, not a split started in this run.

### Input and output observed

Input on screen: one song, 4:50, 224 bars. Output lanes, top to bottom:

| Lane | What was on screen |
|---|---|
| Vocals | Its own waveform, volume slider, M, S |
| Drums | One lane. Not split into kick, snare, or hats |
| Bass | Its own waveform, M, S |
| Other | Its own waveform, M, S. No lane named Guitar or Piano |
| Metronome | A tick lane. M was amber when the screen was first opened. S was not |

Pressing S on Vocals turned that S teal and turned the Drums, Bass, and Other waveforms gray. Vocals stayed bright. The metronome M stayed amber. S was pressed again and returned to gray, then the view was put back on Chords. Audio was not heard, so the teal S is a visible solo state, not a listened mix. Export was not clicked.

### Method

Known: the shell routes a new split at `/upload/split/3` on `https://studio.moises.ai` (E-SHELL-MAC, CORE C03). This song was opened from the library, and the waveforms were already there. No model name, package name, or response field was on screen. No weight file was opened. Unknown: the model, whether drums could be split from another control, and whether Other is the remainder after vocals, drums, and bass.

### Our counterpart

`separate_stems()` in `src/audio_to_tab/isolate.py` takes a local file and returns stem name to wav path. The default `IsolateConfig.model` is `htdemucs_6s`. The isolate CLI describes that model as six stems: drums, bass, other, vocals, guitar, piano. `htdemucs` and `htdemucs_ft` are the four-stem models. Lead and rhythm are a post-process and stay off unless asked. The mixer solo flag is `soloed` in `ui/stem_mixer_component/frontend/src/main.ts`: if any stem is soloed, the others are not the audible mix. A metronome id is part of that mixer. This was not run on フルスピード・ボーイ.

### Difference that matters

On this song their lanes are Vocals, Drums, Bass, Other, and Metronome. Guitar is not its own lane, and drums are one lane. Our default six-stem list is built to emit a guitar wav and a piano wav. That is a different stem list, not a listened quality comparison. Their S control visibly grays the other musical lanes. Split quality was not heard on either side.

### Discarded

No stem audio, no weight bytes, no page source. The screen captures were not committed.

## Chords

### Where it runs

The same hosted Play page. The chord grid is a view on that page, opened with the **Chords** control. The local shell search above found no chord library and no chord model. Unknown: whether the symbols were computed in the browser or returned by the host. No chord request was captured.

### Entry the user takes

The user opened Chords on this song. The grid was scrolled up so the first bars could be read. The transport stayed at 0:39, bar 30, so the grid can show bars away from the playhead. Lyrics sit under the rows. Those lines are not copied here.

### Input and output observed

The key and tempo box reads `186 bpm / E`. The time-signature box reads 1 2 over 3 4. Each row is eight cells with a wider gap after the fourth. The printed bar number is the odd number at the left of the row (1, then 3, then 5, and the same pattern at 25). Inferred from that gap and from the 4/4 box: one row is two bars, and one cell is one beat. The seconds below are not printed on the cells. A zero-based grid at 186 bpm and 4/4 puts bar 30 near 0:37, while the transport says bar 30 at 0:39, so those seconds are not the transport clock.

Every support cell is **unknown**. The clip was not heard. “Read” means the glyph was on screen. Blank cells between symbols had no letter. That blank is not labeled “hold” anywhere on screen.

| Bar | Beat | Symbol | How read | Support |
|---|---|---|---|---|
| 1 | 1 | A short stacked squiggle, not a letter | Zoomed cell | unknown |
| 1 | 2–4 | Blank | No bright pixels in those cells | unknown |
| 2 | 1 | E | Cell on the bar 1 row | unknown |
| 3 | 1 | E | Zoomed cell | unknown |
| 4 | 1 | E | Letter present; neighbors empty | unknown |
| 5 | 1 | E | Letter present; neighbors empty | unknown |
| 6 | 1 | E | Letter present; neighbors empty | unknown |
| 7 | 1 | E | Letter present; neighbors empty | unknown |
| 8 | 1 | E | Letter present | unknown |
| 8 | 2 | D# | Zoomed cell | unknown |
| 8 | 4 | D | Zoomed cell | unknown |
| 9 | 1 | C# | Zoomed cell | unknown |
| 9 | 3 | C | Zoomed cell | unknown |
| 9 | 4 | B | Zoomed cell | unknown |
| 10 | 1 | E | Letter present; neighbors empty | unknown |
| 11 | 1 | E | Letter present | unknown |
| 12 | 1 | G# | Zoomed cell | unknown |
| 25 | 1 | B | Zoomed cell | unknown |
| 26 | 1 | E | Zoomed cell | unknown |
| 27 | 1 | E | Letter present | unknown |
| 27 | 4 | E/G# | Zoomed cell | unknown |
| 28 | 1 | G#m | Zoomed cell | unknown |
| 29 | 1 | G#m | Zoomed cell | unknown |
| 30 | 1 | A | Zoomed cell | unknown |
| 30 | 4 | No letter. The cell is a light fill | Pixel color, while the transport said bar 30 | unknown |
| 31 | 1 | A | Zoomed cell | unknown |
| 32 | 1 | C | Zoomed cell | unknown |
| 33 | 1 | B | Visible beside the mode switch. The rest of that row was covered | unknown |

The first chord letter is E, on bar 2. Bar 1 beat 1 is the squiggle. After a run of E, bar 8 is E then D# then D, and bar 9 is C# then C then B. The key box says E. Whether D#, D, C, or C# occur in the song was not heard, so this is not scored as a wrong chord. E/G# is a slash symbol on beat 4 of bar 27. G#m is the only quality suffix in this stretch. The light cell on bar 30 has no symbol. Nothing on screen said what the squiggle means, or what a blank cell means during silence.

### Method

Unknown beyond the symbols and the grid. No chord-model name was on screen. A filename in the app would not explain these symbols. The hosted route from E-SHELL-MAC is the stem upload route, not a chord API.

### Our counterpart

`detect_chords()` in `src/audio_to_tab/chords.py` returns `ChordEvent` values from `src/audio_to_tab/analysis.py`: `start`, `end`, `symbol`, `confidence`, `simple`, `medium`. Silence inside a file is an `N` event. Slash bass is appended only when the low-chroma peak is strong and is a chord tone of the chosen quality (`_slash_bass()`). `Chord` in `src/audio_to_tab/chord_symbols.py` stores `root`, `quality`, and optional `bass`. `estimate_key()` in `src/audio_to_tab/key.py` returns a key name and a confidence, using the chord list when those chords parse. `detect_chords_btc()` in `src/audio_to_tab/chord_neural.py` is the opt-in maj/min network. It returns `None` when the pinned weight is missing, and `detect_chords()` then stays on the template path. None of these were run on this song.

### Difference that matters

Their grid can put a new root on the next beat. Bar 8 shows E, D#, and D inside one bar, and bar 9 shows C#, C, and B. Our template path also scores beat windows and can emit a slash and an `N`. The BTC path, when it runs, is maj/min labels rather than this slash. Because this clip was not heard, and because our detector was not run on it, there is no evidence here that their timeline is steadier, or that it avoids the “first chord fits, later chords do not belong” pattern. The first letter on their grid is E, which matches the key box. The later chromatic cells are on the screen. They were not judged true or false.

### Discarded

No chord audio, no hosted chord payload, no lyric lines, no page source.

## Verdicts

| Outcome on this song | Verdict | Why |
|---|---|---|
| Where the split and the chords are shown | out-of-scope | Both are the hosted Play page. The shell files that were searched have no stem or chord model. Copying that host is not a local engine change. |
| Named guitar stem | ours-ahead | Their lanes were Vocals, Drums, Bass, Other, Metronome. Our default `htdemucs_6s` list includes guitar and piano. This clip was not separated here, so this is the stem list, not a quality win. |
| Drums as one lane | shared-equal | Their Drums row is one lane. Our default list has one drums stem, not a kit split. |
| Solo a stem | shared-equal | Their Vocals S turned teal and the other musical waveforms turned gray. Our mixer uses `soloed` the same way in code. This song was not played through our mixer. |
| Muteable metronome in the mix | shared-equal | Their Metronome M was amber on arrival. Our mixer has a metronome id and mute. The click audio was not compared. |
| Split quality | unknown | The waveforms were not heard. |
| Chord symbols on a beat grid, including a slash | shared-equal | Their grid shows roots, one `m`, and `E/G#`. Our `ChordEvent` has start, end, and symbol, and `_slash_bass()` can add a bass. Not run on this clip. |
| Chords match the song | unknown | Not heard. The first letter is E. Later cells include D#, D, C#, and C while the key box says E. That pattern was not scored true or false. |

## Queue

Nothing from this run is a missing or shared-moises-better stem or chord outcome inside the local engine. [PARITY-BACKLOG.md](PARITY-BACKLOG.md) was not given a new queue id. A model-weight port was not considered.
