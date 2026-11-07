# Parity backlog — Moises macOS 2.1.0 versus this repo — 2026-11-07

One row per capability in [CORE.md](CORE.md). A later agent reimplements only a **Queue** id, in this repo’s architecture, and cites CORE.md. It does not copy Moises source, markup, fonts, icons, audio, model weights, or trademarks.

Our desktop product is Streamlit `ui/` behind `packaging/launcher.py`. Our hosted product is `backend/` plus `web/`. The shared engine is `src/audio_to_tab/`. Graphify was queried for isolation, tab PDF, YouTube, mix tabs, setlists, and open-file extensions before those files were read.

Verdict counts: missing 0, shared-moises-better 0, shared-equal 0, ours-ahead 2, unknown 11, out-of-scope 9.

## Rows

| Id | Verdict | Our counterpart | Why this verdict |
|---|---|---|---|
| C01 | out-of-scope | `mix_tabs()` in `ui/mix_tabs_component/__init__.py` and `bindTabStripDrag()` in `ui/mix_tabs_component/frontend/src/main.ts` | Moises tabs host the Moises web products. Our strip is Home plus local mix tabs. That is a different surface. |
| C02 | unknown | `OPENED_AUDIO_EXTENSIONS` in `ui/opened_audio.py`; `_handoff_opened_files()` in `packaging/launcher.py` | Both can open local media. Their dialog lists midi, opus, wma, amr, caf, and mp2. Ours lists mpeg, aiff, and video (`mp4`, `mov`, `webm`, `mkv`) and declines other extensions. What their hosted page does with MIDI was not run, so neither set is scored better. |
| C03 | unknown | `separate_stems()` in `src/audio_to_tab/isolate.py` | Play’s upload route is observed. Stem quality, stem list, and the player were not run. |
| C04 | unknown | `build_home_props()` and `library_rows()` in `ui/pages/home.py` | Their Home is a hosted URL. The page was not executed. Our Home is a local library. |
| C05 | out-of-scope | ABSENT. Search: graphify query for isolation, mixer, tab PDF, and YouTube did not surface a hosted DAW. | Studio is a hosted DAW route, including paths and hashes that match `daw`. |
| C06 | out-of-scope | ABSENT. Same search. No mastering product in the nodes returned. | Mastering is a separate hosted product. |
| C07 | out-of-scope | ABSENT. Same search. | Voice Studio is a separate hosted product. |
| C08 | out-of-scope | `chart_to_musicxml()` in `src/audio_to_tab/export_musicxml.py` writes lyric text onto a chart. That is not a lyric-generation product. | Lyric Writer is a hosted product route. Generation was not run. |
| C09 | unknown | `create_setlist()`, `add_song()`, and `load_setlists()` used from `ui/pages/home.py`; storage helper module `ui/setlists.py` | We can create a local setlist and add a song. Their menu opens `/setlist`. Their create, edit, and play behavior was not run. |
| C10 | out-of-scope | `backend/account.py` exists for this API’s accounts. It is not a Moises login bridge. | Their auth handoff is their account system. Login was not performed. |
| C11 | out-of-scope | ABSENT as an in-app ToDesktop updater. Search: no ToDesktop updater in the graphify audio query. Desktop release is the tag flow in `AGENTS.md`. | Updating the Moises shell is packaging, not an audio-tool behavior. The feed was not fetched. |
| C12 | unknown | `applyTheme()` in `ui/mix_tabs_component/frontend/src/main.ts` | Their theme channel exists. The payload and the visible result were not run. |
| C13 | unknown | ABSENT. Search: `memory-panel` is not a symbol in our mix-tab or home graphify results. | Their panel’s trigger and contents are unknown, so there is no outcome to port. |
| C14 | out-of-scope | ABSENT. The audio graphify query did not surface a VST or AAX host. | Plugin hosting and plugin install are a different product surface. The server was not started. |
| C15 | out-of-scope | ABSENT. No live-capture product in the audio graphify query. Our input is a file. | Live CoreAudio capture is the decision item named for this backlog. No stream was opened. |
| C16 | unknown | Mixer pause lives on the desktop mixer and `web/src/mixer/engine.ts` (`StemMixerEngine`). The exact pause symbol was not re-read in this pass. | Their pause channel was not fired, so it is not scored against our mixer. |
| C17 | unknown | Waveform and transport live in `ui/stem_mixer_component/` and `StemMixer()` in `web/src/components/StemMixer.tsx`. Tempo estimation is `estimate_tempo_from_audio()` in `src/audio_to_tab/tempo.py`. Home shows BPM through `analysis_summary()` in `ui/pages/home.py`. | Their bundle contains wavesurfer, TrackHeader, and tempo/time-signature/key editor strings. Mounting was not observed, so theirs is not scored better. |
| C18 | ours-ahead | `render_tab_pdf()` in `src/audio_to_tab/pdf_render.py`, `main()` in `ui/pages/tab_pdf.py`, `run_pipeline()` in `src/audio_to_tab/pipeline.py` | The searched local shell and renderer have no guitar, chord, tablature, or metronome literal. We generate a tab PDF. This does not score the hosted player. |
| C19 | unknown | Same tab pipeline as C18. | Hosted Play and any player route were not executed. `player` has 0 hits in `out/main/index.js`. |
| C20 | ours-ahead | `download_youtube_audio()` in `src/audio_to_tab/ingest.py`; `save_youtube_audio_to_folder()` in `ui/pages/youtube_audio.py` | The searched local shell and renderer have no YouTube literal. We download public YouTube audio to a file. This does not score hosted pages. |
| C21 | unknown | Same YouTube functions as C20. | Hosted JavaScript was not downloaded or run. |
| C22 | unknown | ABSENT as a matching dirty-project dialog. Search was the Moises dialog text, not a full pass over our save prompts. | Their dialog text is observed. The action that raises it is unknown. |

## Queue

No ids. A missing or shared-moises-better outcome was not established inside the product boundary.

A later agent must not promote an unknown or an out-of-scope row into this list. The unknowns below are what block a queue.

## Decision

A later agent must not build these until this user approves that id.

| Id | Product boundary |
|---|---|
| C01 | Multi-product hosted shell. Our mix tabs stay a local mix strip. |
| C05 | Hosted Studio DAW, including realtime project editing. |
| C06 | Hosted mastering. |
| C07 | Hosted voice processing. |
| C08 | Hosted lyric generation. Chart lyric export we already have is not this product. |
| C10 | Their accounts, login providers, and billing. |
| C11 | Their desktop updater and ToDesktop feed. |
| C14 | VST, AAX, and Audio Unit hosting and install. |
| C15 | Live interface capture. Desktop isolation stays file-in, serial, and local. |

These stay in force if a future approval moves an id onto the queue: Python 3.10–3.12; MPS only at 12 GB RAM or more; desktop isolation stays serial; Desktop Interface Lite and hosted lite stay different products; desktop Lite does not clamp duration; YouTube to MP3 stays download-only; metronome click times stay on the stored grid and are not re-tracked; mixer export stays on save-current-mix; model downloads stay SHA256-pinned urllib; do not copy Moises artwork, font files, markup, or mixer laws; do not change global theme tokens.

## Unknowns that block a later implementation

- C03, C04, C09, C19, C21: hosted interiors were not executed. HTTP 200 from a logged-out GET only proves the SPA document is served.
- C17: tempo, waveform, and track-header strings in the local bundle were not shown mounted.
- C12, C13, C16, C22: channels or dialog text without a traced user action.
- C02: MIDI is accepted by their dialog and declined by `paths_from_argv()` when the extension is outside `OPENED_AUDIO_EXTENSIONS`. The hosted result of opening MIDI is unknown.
- Renderer file `index-C76vPLoN.js` SHA-256 `00cdb566…` replaces the 2026-10-23 hash `791aa79e…` for this Mac. Old needle counts must not be reused.
- Shell JavaScript slice hashes match the Windows 2026-10-23 slices. The asar hash does not. REA’s channel count on this parse is 68, with 123 IPC operations and 18 renderer listeners. Those operation counts are this tool run. They are not a second copy of the 2026-10-23 operation totals.
- Unselected asar files, about 6,509, were not searched. A negative finding is only the search named on the CORE row.
- `darwin-arm64/capture.node` and `MoisesPluginServer` contradict the asar integrity metadata. Their bytes are untrusted against that hash.
