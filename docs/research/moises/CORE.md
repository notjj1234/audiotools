# Moises functional core — macOS 2.1.0 — 2026-11-07

This is the stripped core of the Moises app installed on this Mac. A row is one user-facing capability. Proprietary implementation is named and then discarded. Static evidence does not prove a running session.

Read [PARITY-BACKLOG.md](PARITY-BACKLOG.md) before any port. Evidence ids are in [evidence-index.md](evidence-index.md).

## Identity

| Fact | Value | Status | Evidence |
|---|---|---|---|
| Bundle | `/Applications/Moises.app` | observed | one match under `/Applications`; `~/Applications` had none |
| Version | `2.1.0` | observed | `CFBundleShortVersionString`; `package.json` `version` |
| Build | `261021a1gygumpb` | observed | `CFBundleVersion`; `package.json` `tdBuildId` |
| Bundle id | `com.todesktop.220410vabqjud82` | observed | Info.plist via `plutil`. `inspect_plist` failed and has no id |
| Platform | macOS arm64 | observed | `open_binary` executable SHA-256 `c23ee797e063a4fdacc5427f1a005a6a7e47bf18db9ec6b8a68ac74cbe5bc98d` |
| Electron framework | `43.4.1` | observed | framework `CFBundleVersion`. This is the framework bundle version, not a runtime `process.versions` reading |
| Asar | 60,980,438 bytes, SHA-256 `6a42619e39f7ca3c98085e2c2cbcd8fa90397ace6dd133c40c551eee070ef05a` | observed | E-ASAR-MCP |
| Shell graph | 5 JS files, 22,852 AST nodes, 68 channels, 79 bridge members | observed | E-SHELL-MAC / E-SHELL-MAC-SUM |
| Prior Windows asar | SHA-256 `e7242b3d…` | different archive | 2026-10-23 index. Shell slice hashes match. Renderer hash does not |

Fuses, E-FUSES-MAC: RunAsNode enabled, cookie encryption disabled, node CLI inspect arguments honored, embedded ASAR integrity not enforced, app not restricted to `app.asar`. Fuse state does not prove an Inspector port is open.

MCP `analyze_javascript_application` on the raw asar parsed 0 JavaScript files (`invalid utf-8`). The CLI parse used an offset-corrected extract at `/tmp/moises-mac-2.1.0-shell`. That extract and `/tmp/moises-rea-mac-2.1.0/shell-evidence.json` stay outside the repo.

The hosted product was not logged in, uploaded to, or purchased. `GET https://studio.moises.ai/play` returned HTTP 200 HTML and was not executed, so it does not establish a logged-out interior.

## What was discarded

Minified function bodies, menu icon files, CSS, the Sentry DSN literal in main, and the unpacked plugin-server binary. Native capture behavior is taken from the shipped README and from API-name strings in `capture.node`, not from decompilation. No model-weight file was copied or hashed in full.

## C01 — Tabbed shell for hosted Moises pages

- Outcome: the person works in desktop tabs that load hosted Moises pages, and can create, close, activate, reorder, duplicate, and close neighboring tabs.
- Entry: process start. The shell creates a Home tab and persists `tabs.json` under the user-data path. Menu labels include Go to Home, New Window, Duplicate Tab, Close Other Tabs, and Close Tabs to the Right.
- States: tabs change through `tab:*` and `tabs:updated`. A second construction loads the webview preload. Drag channels `drag:*` and preview channels `tab:preview-show` / `tab:preview-hide` exist. Session restore from `tabs.json` is a write path in main; this run did not read a live session file.
- Inputs and outputs: tab ids and hosted URLs in, a tab list out. The hosted page is not drawn by the local HTML.
- Where: local shell. Main is `out/main/index.js`. The shell preload is `out/preload/index.cjs`. Hosted pages get `out/preload/webview.cjs`.
- Status: observed as syntax and menu labels. Runtime clicks were not performed.
- Evidence: E-SHELL-MAC. Slice SHA-256 values are in the evidence index. REA: 2 browser windows, 2 context-bridge APIs, 79 exposed members, 68 literal channels, 54 renderer transmissions all paired, 51 main handlers, 18 renderer listeners, 0 dynamic channels, 0 sender-validation observations, 1 utility process. Preference literals set `contextIsolation` true and `nodeIntegration` false. One hosted-view literal contains a conditional `webSecurity: false` branch. Whether that branch runs is unknown.
- Discarded: the minified tab manager.

## C02 — Open a local audio or MIDI file

- Outcome: the person picks one or more local files in an Open Audio dialog and the shell hands them to the hosted app.
- Entry: File menu label Open Audio. Dialog options include `openFile` and `multiSelections`. The extension map is `mp3`, `mp2`, `wav`, `m4a`, `aac`, `flac`, `ogg`, `opus`, `wma`, `amr`, `caf`, `mid`, `midi`. Info.plist registers those types with role Editor. `import:consume` is the webview bridge.
- States: dialog cancelled or files chosen. A Play import URL is built as `/upload/split/3` plus `desktopImport=1` on the packaged host. What the hosted page does with the file was not run.
- Inputs and outputs: local file paths in. A desktop-import URL out. MIDI is accepted by the dialog. Playback or editing of MIDI was not observed.
- Where: local shell dialog, then a hosted page.
- Status: dialog and extension map observed. The hosted import result is unknown.
- Evidence: E-SHELL-MAC plus the Info.plist document types. Search boundary for the extension object: the `mp3`…`midi` map in `out/main/index.js`.
- Discarded: dialog implementation and icon resources.

## C03 — Play, library, and stem upload

- Outcome: the person opens Play, including a library URL or a stem-upload URL.
- Entry: product menu title Play, icon `play`, new-project path `/upload/split/3`. Match paths are `/play`, `/play/`, `/library`, and `/upload/split`.
- States: menu selection only. The meaning of the `3` suffix was not found as a comment or a second definition in the shell files searched.
- Inputs and outputs: a path in, a `https://studio.moises.ai` URL with `client=desktop` out when the app is packaged. Unpackaged builds point the same paths at `https://studio-stage.moises.ai`.
- Where: local menu, hosted page.
- Status: route table observed. Separation quality, stem list, and player controls on that page are unknown.
- Evidence: E-SHELL-MAC. Logged-out GET of `/play` and `/library` returned 200 HTML and was not executed.
- Discarded: hosted page source, which is not in this asar.

## C04 — Home

- Outcome: the person opens the hosted Home page.
- Entry: menu title Home, paths `/home` and `/home/`. Packaged default tab URL is `https://studio.moises.ai/home?client=desktop`.
- States: initial tab and Go to Home. The page interior was not executed.
- Inputs and outputs: none beyond the URL.
- Where: local menu, hosted page.
- Status: URL construction observed. Page contents unknown.
- Evidence: E-SHELL-MAC.
- Discarded: hosted Home markup.

## C05 — Studio

- Outcome: the person opens the hosted Studio DAW, including a new project.
- Entry: menu title Studio, icon `sparkbars`, new-project path `/studio/new`, match `/studio`. A path or hash containing `daw` also matches Studio.
- States: new project versus an existing project URL. The timeline, tracks, and export were not opened.
- Inputs and outputs: project URL in, hosted Studio out. `desktopImport=1` can be appended to the new-project URL.
- Where: local menu, hosted page.
- Status: routing observed. DAW behavior unknown.
- Evidence: E-SHELL-MAC. The logged-out `/play` HTML contains a boot-cover comment that names a DAW access guard. That comment is not a walk of Studio.
- Discarded: DAW implementation. `sparkbars` is the Studio icon id.

## C06 — Mastering

- Outcome: the person opens Mastering or its upload path.
- Entry: menu title Mastering, new-project `/mastering/upload`, also `/mastering` and `/upload/master`.
- States: destination only.
- Inputs and outputs: path in, hosted URL out.
- Where: local menu, hosted page.
- Status: routing observed. Mastering processing unknown.
- Evidence: E-SHELL-MAC.
- Discarded: hosted mastering implementation.

## C07 — Voice Studio

- Outcome: the person opens Voice Studio or its upload path.
- Entry: menu title Voice Studio, new-project `/voice-studio/upload`, match `/voice-studio`.
- States: destination only.
- Inputs and outputs: path in, hosted URL out.
- Where: local menu, hosted page.
- Status: routing observed. Voice processing unknown.
- Evidence: E-SHELL-MAC.
- Discarded: hosted voice implementation.

## C08 — Lyric Writer

- Outcome: the person opens Lyric Writer.
- Entry: menu title Lyric Writer, new-project `/lyrics/new`, match `/lyrics` and `/lyric-writer`.
- States: destination only.
- Inputs and outputs: path in, hosted URL out.
- Where: local menu, hosted page.
- Status: routing observed. Generation behavior unknown.
- Evidence: E-SHELL-MAC.
- Discarded: hosted lyric implementation.

## C09 — Setlist

- Outcome: the person opens a Setlist destination from the product menu.
- Entry: menu title Setlist, icon `setlist`, match `/setlist`. The local renderer bundle also contains class-name fragments `_setlistsSection`, `_setlistsScrollArea`, `_setlistsContent`, and `_setlistExpandButton`.
- States: menu route observed. Create, rename, reorder, and playback of a setlist were not run. The class names do not prove the section is mounted.
- Inputs and outputs: path `/setlist` in, hosted URL out.
- Where: local menu and local bundle text, hosted page.
- Status: route observed. Setlist operations unknown.
- Evidence: E-SHELL-MAC for the route. Renderer SHA-256 `00cdb566cdaccc4d8d262c203865e18795e7822501dd300e874a3c22261f9844`. Bounded search: those four class fragments in that file.
- Discarded: the class-name stylesheet and any hosted setlist API.

## C10 — Account and auth handoff

- Outcome: the hosted page can tell the shell that the person is signed in, and the shell can sign out.
- Entry: channels `auth:is-signed-in`, `auth:changed`, `auth:state`, `auth:sign-out`. Login URL `/auth/login` on the studio host. Main also names `/auth/` and `/__/auth/`, plus host strings for Microsoft, Firebase, Facebook, Google, Tone3000, and SoundCloud login pages.
- States: signed-in flag as an IPC payload. No account was used.
- Inputs and outputs: auth state messages. Credentials were not observed and were not entered.
- Where: local shell bridge and hosted auth pages.
- Status: bridge and host allowlist observed. Login, signup, and billing are blocked.
- Evidence: E-SHELL-MAC.
- Discarded: auth provider implementation and any token handling.

## C11 — In-app update

- Outcome: the shell can check for a desktop update and install one that has downloaded.
- Entry: channels `updates:get-state`, `updates:check`, `updates:install`, `updates:downloaded`, and webview `app:update-desktop-app`. `app-update.yml` sets provider `generic`, url `https://download.todesktop.com/220410vabqjud82`, channel `latest`.
- States: the feed was not requested in this run. Whether this build is current on the feed is unknown for 2026-11-07.
- Inputs and outputs: update state in the shell. No download was started.
- Where: local shell, ToDesktop feed.
- Status: channels and feed URL observed. A live update check was not run.
- Evidence: E-SHELL-MAC and `Contents/Resources/app-update.yml`.
- Discarded: updater transport code.

## C12 — Theme

- Outcome: the shell page can read the theme and hear theme changes.
- Entry: `theme:get`, `theme:changed` on the shell preload.
- States: the values those channels carry were not executed.
- Inputs and outputs: unknown payload.
- Where: local shell.
- Status: channels observed. The visible theme is unknown.
- Evidence: E-SHELL-MAC. Bounded search: those two literals in `out/preload/index.cjs`.
- Discarded: theme tokens and stylesheets.

## C13 — Memory panel

- Outcome: the shell can open a memory panel and show or hide a memory icon.
- Entry: `memory-panel:*`, `memory-icon:visible`, `memory-chrome:state`, `memory-chrome:consume-auto-open`. The renderer bundle contains the literal `memory-panel` five times.
- States: show, hide, ready, auto-open. The condition that opens it was not isolated.
- Inputs and outputs: panel visibility events. The metric it displays is unknown.
- Where: local shell.
- Status: channels observed. Trigger and contents unknown.
- Evidence: E-SHELL-MAC. Renderer count is a case-sensitive literal count in `index-C76vPLoN.js`, not a runtime trace.
- Discarded: panel markup.

## C14 — Plugin server and VST or AAX install

- Outcome: the shell can start a local plugin server and the hosted page can ask it to install or report plugin versions.
- Entry: `plugin-server:status|start|stop|restart|connection`, `plugin:check-version-release`, `plugin:check-version-user`, `plugin:install`, `vst-host:connection`. Menu label Enable VST plugins. Host `https://plugins.moises.ai`. Filenames `Stems.vst3`, `Stems.aaxplugin`, `Stems.component`, `Studio.vst3`, `Studio.aaxplugin`, `Studio.component`, `Mastering.vst3`, `Mastering.aaxplugin`, `Mastering.component`. Install-path strings include `/Library/Audio/Plug-Ins/VST3`, `/Library/Audio/Plug-Ins/Components`, and `/Library/Application Support/Avid/Audio/Plug-Ins`.
- States: menu label `VST plugins:` plus a status string. The server was not started. New Project menu item is present with `enabled: false` in the tray template that was read.
- Inputs and outputs: version and install calls. No plugin was installed.
- Where: local shell and unpacked `@moises-ai/plugin-server` `0.8.40` (`plugin-server-darwin-arm64`). Hosted page for the install request.
- Status: IPC, filenames, and package version observed. A running VST host was not observed. REA marked the unpacked `MoisesPluginServer` bytes untrusted against the asar integrity record.
- Evidence: E-SHELL-MAC. Package version read from the unpacked `package.json`.
- Discarded: the plugin-server binary and installer scripts.

## C15 — Live audio capture

- Outcome: a hosted page can list input devices, open an input stream, and hear device changes through a local capture host.
- Entry: webview channels `audio-capture:capabilities`, `devices`, `open`, `close`, `watch`, `closed`, `devices-changed`, and `audio-capture:port`. The utility name string is `MoisesAudioCapture`. The host module is `out/main/audio-capture-host.js`.
- States: README says a missing addon fails with `addon-unavailable`, a rate change without the allow flag is `rate-mismatch`, and a disconnected device is reported. Those codes are in the README and the host file. This run did not open a device. Microphone purpose string: "Moises records audio from your microphone and audio interface into Studio projects."
- Inputs and outputs: README exports `listDevices`, `openStream`, `watchDevices`, interleaved Float32 blocks, overflow and lost-frame counts, and peaks. Sample rate and channel count used by Studio were not observed at runtime.
- Where: native addon `native/capture/prebuilds/darwin-arm64/capture.node`, utility host in the shell, consumer is a hosted page. API map: darwin default `coreaudio`; the darwin-arm64 build lists `coreaudio` only. `wasapi` and `asio` are the win32-x64 list. A win32 `capture.node` is also present in this Mac asar’s unpacked tree.
- Status: protocol and README observed. No stream was opened. REA `resolved_native_addon_bindings` is 0, and the addon’s integrity record does not match the asar, so the binding is untrusted against that hash. Strings in the unpacked addon include `RtAudio`, `CoreAudio`, `WASAPI`, and `ASIO`.
- Evidence: E-SHELL-MAC, capture API chunk SHA-256 `b9d7961159f43cb667e3d72e2d209945c96139344c81c1188cb42e3e7beb6639`, README SHA-256 `319a84c897bf05e127653b086ea7a9833b07c0079b47edcba1b748f018510c63`.
- Discarded: RtAudio patch source and the addon binary. The README says audify shipped through 2.0 and this addon is RtAudio 6.0.1. That sentence is the shipped README, not a disassembly.

## C16 — Pause hosted playback from the shell

- Outcome: the shell can tell the hosted page to pause playback.
- Entry: `desktop:pause-playback` on the webview preload.
- States: the event exists. What audio it stops was not run.
- Inputs and outputs: a pause event. No playback session was started.
- Where: local shell to hosted page.
- Status: channel observed. Effect unknown.
- Evidence: E-SHELL-MAC.
- Discarded: the player that would receive it.

## C17 — Waveform, track header, and tempo text in the local bundle

- Outcome: unknown. The local renderer bundle contains player text that may or may not mount.
- Entry: `out/renderer/index.html` loads `./assets/index-C76vPLoN.js`. Title is Moises Studio. CSP is `default-src 'none'` and `connect-src 'self'`, so this document cannot call the network.
- States: case-sensitive counts in that bundle: `wavesurfer` 6, `TrackHeader` 1, `bpm` 5, `memory-panel` 5, `electronAPI` 50, `sparkbars` 2, `player` 4. Nearby `bpm` text includes `onTempoChange`, `timeSignatureTop`, `timeSignatureBottom`, `rootKey`, and `handleAIDetect`. Counts of 0 in the same file: `guitar`, `chord`, `tablature`, `metronome`, `pitch`, `tempo`, `capo`, `youtube`. The word `stem` and `isolate` occur only inside unrelated identifiers (`eventSystem`, CSS `isolation`).
- Inputs and outputs: not established. The HTML mounts `<div id="root">` and does not name a mixer.
- Where: local renderer. This bundle is not the hosted Studio page.
- Status: literals observed. Which of those components mount on the shell page is unknown. The 2026-10-23 renderer hash `791aa79e…` is not this file.
- Evidence: file SHA-256 `00cdb566cdaccc4d8d262c203865e18795e7822501dd300e874a3c22261f9844`. E-SHELL-MAC did not select this file. Bounded search: the literals listed above.
- Discarded: the bundle source, waveform renderer, and CSS.

## C18 — Guitar tab in the local shell and renderer

- Outcome: the shipped local app does not contain a guitar-tab surface in the files that were searched.
- Entry: none found.
- States: none found.
- Inputs and outputs: none found.
- Where: local shell and local renderer only. This row does not describe hosted Play.
- Status: observed absence inside a bounded search. Case-sensitive `guitar`, `chord`, `tablature`, and `metronome` are 0 in the renderer bundle. The same words were not in the shell literal set extracted from the five JavaScript files.
- Evidence: E-SHELL-MAC for the shell files. Renderer hash under C17. Search boundary: those five files plus `index-C76vPLoN.js`. Unselected asar files were not searched, so this is not an absence claim for the whole archive.
- Discarded: nothing was copied.

## C19 — Guitar tab inside hosted Play or a player route

- Outcome: unknown.
- Entry: not found in the shell route table. There is no `/player` literal in `out/main/index.js` (`player` count 0 in that file).
- States: not walked.
- Inputs and outputs: unknown.
- Where: hosted page, if it exists.
- Status: unknown. Logged-out HTML was not executed.
- Evidence: route-literal search of `out/main/index.js` for `/player` and `player`. No evidence id beyond E-SHELL-MAC for that negative search.
- Discarded: hosted bundles, which are not in the asar.

## C20 — YouTube download in the local shell

- Outcome: the shipped shell and local renderer that were searched do not mention YouTube.
- Entry: none found.
- States: none found.
- Inputs and outputs: none found.
- Where: local shell and local renderer only.
- Status: observed absence in the same bounded search as C18. Case-sensitive `youtube` count is 0 in the renderer bundle and the shell literal extract did not contain it.
- Evidence: E-SHELL-MAC and the renderer hash. Unselected asar files and hosted pages were not searched.
- Discarded: nothing was copied.

## C21 — YouTube inside hosted pages

- Outcome: unknown.
- Entry: not in the shell route table.
- States: not walked.
- Inputs and outputs: unknown.
- Where: hosted page, if it exists.
- Status: unknown.
- Evidence: same negative shell search as C20. Hosted JavaScript was not downloaded.
- Discarded: hosted bundles.

## C22 — Unsaved-changes guard

- Outcome: the shell can ask before leaving when it decides there are unsaved changes.
- Entry: dialog title Unsaved Changes, message "You have unsaved changes. Are you sure you want to leave?", buttons Yes and No.
- States: the function returns true only for the Yes response. The condition that calls it was not traced to a user action in this pass.
- Inputs and outputs: a confirmation. No project was left dirty.
- Where: local shell.
- Status: dialog text observed. The user action that raises it is unknown.
- Evidence: E-SHELL-MAC. Bounded read of the dialog literal in `out/main/index.js`.
- Discarded: the call-site implementation.

## Searches that stay bounded

- Shell behavior: `package.json`, `out/main/index.js`, `out/main/audio-capture-host.js`, `out/main/chunks/capture-apis-J4FdMrZ-.js`, `out/preload/index.cjs`, `out/preload/webview.cjs`, `out/renderer/index.html`.
- Renderer behavior: `out/renderer/assets/index-C76vPLoN.js` only, by literal count, not by REA graph.
- Not searched: the other 6,509 asar files, hosted JavaScript on `studio.moises.ai`, and a logged-in session.
- Native capture was not disassembled. `resolved_native_addon_bindings` is 0.
- `app:set-should-prevent-navigation` is a real channel in the webview preload. It is part of C01’s navigation guard, and its effect when fired is unknown.
