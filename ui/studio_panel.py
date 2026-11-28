"""Settings and song controls for the Phase 3 local products."""

from __future__ import annotations

import json
from pathlib import Path

import streamlit as st

from audio_to_tab.phase3 import (
    GENERATION_MESSAGE,
    INSTRUMENTS,
    VOICE_MESSAGE,
    add_comment,
    add_midi_note,
    add_note,
    apply_bus,
    auto_mix_volumes,
    create_share,
    delete_midi_note,
    export_setlist,
    generation_result,
    import_setlist,
    load_session,
    load_studio,
    name_voice,
    open_library_song,
    open_share,
    peak_master,
    remember_library_folder,
    remember_sync_folder,
    remove_clip,
    restore_library,
    restore_project,
    save_custom_voice,
    save_prompt,
    save_session,
    save_song_to_library,
    save_studio,
    set_bus,
    set_chosen_take,
    set_clip_automation,
    set_stem_trim,
    snapshot_project,
    stem_catalogue,
    sync_library,
    upsert_clip,
    write_daw_zip,
    write_dawproject,
    write_musicxml,
)
from ui.common import DATA_DIR
from ui.desktop_export import choose_export_dir
from ui.isolate_state import (
    ISOLATE_UI_STATE_FILENAME,
    isolate_ui_state_payload,
    write_isolate_ui_state,
)
from ui.project import load_project, save_project


def _persist() -> None:
    write_isolate_ui_state(
        DATA_DIR / ISOLATE_UI_STATE_FILENAME,
        isolate_ui_state_payload(st.session_state),
    )


def render_library_tools() -> None:
    st.subheader("Library folder")
    folder = str(st.session_state.get("library_folder") or "")
    st.caption(folder or "No library folder yet.")
    if folder and Path(folder).is_dir():
        songs = [
            path.name
            for path in Path(folder).iterdir()
            if path.is_dir() and (path / "meta.json").is_file()
        ]
        if songs:
            choice = st.selectbox("Library songs", songs, key="phase3_library_song")
            if st.button("Open library song", key="phase3_open_library_song"):
                open_selected_library_song(choice)
                st.caption("Opened that song on this computer.")
    if st.button("Choose library folder", key="phase3_library_folder"):
        picked = choose_export_dir()
        if picked:
            remembered = remember_library_folder(dict(st.session_state), str(picked))
            st.session_state["library_folder"] = remembered["library_folder"]
            _persist()
            st.rerun()
    sync = str(st.session_state.get("sync_folder") or "")
    st.caption(sync or "No sync folder yet.")
    if st.button("Choose sync folder", key="phase3_sync_folder"):
        picked = choose_export_dir()
        if picked:
            remembered = remember_sync_folder(dict(st.session_state), str(picked))
            st.session_state["sync_folder"] = remembered["sync_folder"]
            _persist()
            st.rerun()
    if folder and sync and st.button("Sync library", key="phase3_sync"):
        count = sync_library(Path(folder), Path(sync))
        st.caption(f"Synced {count} song(s).")
    if folder and sync and st.button("Restore library", key="phase3_restore_sync"):
        count = restore_library(Path(sync), Path(folder))
        st.caption(f"Restored {count} song(s).")

    st.subheader("27 stems")
    for row in stem_catalogue():
        state = "installed" if row["installed"] else "not installed"
        st.caption(f"{row['name']} — {state}")

    st.subheader("Studio")
    result = generation_result()
    st.caption(result["message"])
    st.caption("Sample generation: " + GENERATION_MESSAGE)
    st.caption(VOICE_MESSAGE)
    for item in INSTRUMENTS:
        st.caption(f"{item['name']} — not installed")
    st.caption("Lite and Pro stay the only plan switch.")
    code = st.text_input("Session code", key="phase3_session_code")
    if st.button("Load session", key="phase3_load_session") and code.strip():
        loaded = load_session(DATA_DIR, code.strip())
        if loaded:
            st.json(loaded.get("mixer") or {})
        else:
            st.caption("No session with that code on this computer.")
    token = st.text_input("Share token", key="phase3_share_token")
    if st.button("Open share", key="phase3_open_share") and token.strip():
        found = open_share(DATA_DIR, token.strip())
        if found:
            st.session_state["isolate_viewing_run_dir"] = str(found)
            st.session_state["isolate_run_dir"] = str(found)
            st.caption("Opened that song on this computer.")
        else:
            st.caption("No song has that token.")


_STUDIO_SECTIONS = {
    "edit": "Edit",
    "notes": "Notes",
    "ideas": "Ideas & voice",
    "midi": "MIDI & takes",
    "share": "Share & export",
}


def render_song_studio(run_dir: Path) -> None:
    """One section at a time, each input beside its button.

    Every control used to stack full width (about 35 rows), which buried the
    mixer under a form. The More tools label already names the panel.
    """
    project, _warning = load_project(run_dir)
    studio = load_studio(run_dir)
    section = st.segmented_control(
        "Studio section",
        options=list(_STUDIO_SECTIONS),
        format_func=lambda key: _STUDIO_SECTIONS[key],
        default="edit",
        key=f"studio_section_{run_dir.name}",
        label_visibility="collapsed",
    ) or "edit"
    if section == "edit":
        _render_studio_edit(run_dir, project, studio)
    elif section == "notes":
        _render_studio_notes(run_dir, studio)
    elif section == "ideas":
        _render_studio_ideas(run_dir, studio)
    elif section == "midi":
        _render_studio_midi(run_dir, studio)
    else:
        _render_studio_share(run_dir)


def _render_studio_edit(run_dir: Path, project: dict, studio: dict) -> None:
    trims = project.get("stem_trims") if isinstance(project.get("stem_trims"), dict) else {}
    st.markdown("**Trim a stem**")
    if trims:
        for name, trim in trims.items():
            st.caption(f"{name} trim {trim.get('start')}–{trim.get('end')} s")
    name_col, start_col, end_col, save_col = st.columns([2, 1, 1, 1], vertical_alignment="bottom")
    with name_col:
        stem = st.text_input("Stem trim name", value="vocals", key=f"trim_name_{run_dir.name}")
    with start_col:
        start = st.number_input("Trim start", value=0.0, key=f"trim_start_{run_dir.name}")
    with end_col:
        end = st.number_input("Trim end", value=0.0, key=f"trim_end_{run_dir.name}")
    with save_col:
        if st.button("Save trim", key=f"trim_save_{run_dir.name}", width="stretch"):
            snapshot_project(run_dir)
            set_stem_trim(project, stem, float(start), float(end))
            save_project(run_dir, project, force=True)
            st.rerun()

    st.markdown("**Clips**")
    for clip in studio.get("clips") or []:
        points = clip.get("automation") or []
        point_text = ", ".join(f"{point['time']}s {point['db']} dB" for point in points)
        st.caption(f"{clip['label']} {clip['start']}–{clip['end']} {point_text}".rstrip())
    label_col, cstart_col, cend_col = st.columns([2, 1, 1])
    with label_col:
        label = st.text_input("Clip label", value="verse", key=f"clip_label_{run_dir.name}")
    with cstart_col:
        clip_start = st.number_input("Clip start", value=0.0, key=f"clip_start_{run_dir.name}")
    with cend_col:
        clip_end = st.number_input("Clip end", value=8.0, key=f"clip_end_{run_dir.name}")
    save_clip, remove, points_col = st.columns(3)
    with save_clip:
        if st.button("Save clip", key=f"clip_save_{run_dir.name}", width="stretch"):
            upsert_clip(studio, label, float(clip_start), float(clip_end))
            save_studio(run_dir, studio)
            st.rerun()
    with remove:
        if st.button("Remove clip", key=f"clip_remove_{run_dir.name}", width="stretch"):
            remove_clip(studio, label)
            save_studio(run_dir, studio)
            st.toast("Clip removed. The audio file stays on disk.")
            st.rerun()
    with points_col:
        if st.button("Add volume points", key=f"clip_auto_{run_dir.name}", width="stretch"):
            set_clip_automation(studio, label, [(0.0, -6.0), (float(clip_end), 0.0)])
            save_studio(run_dir, studio)
            st.toast("Volume points are shown. Listen does not apply them.")
            st.rerun()

    st.markdown("**Bus**")
    bname_col, bstems_col, bvol_col, bsave_col = st.columns([1, 2, 1, 1], vertical_alignment="bottom")
    with bname_col:
        bus_name = st.text_input("Bus name", value="Band", key=f"bus_name_{run_dir.name}")
    with bstems_col:
        bus_stems = st.text_input("Bus stems", value="drums,bass", key=f"bus_stems_{run_dir.name}")
    with bvol_col:
        bus_volume = st.number_input("Bus volume", value=-3.0, key=f"bus_vol_{run_dir.name}")
    with bsave_col:
        if st.button("Save bus", key=f"bus_save_{run_dir.name}", width="stretch"):
            names = [part.strip() for part in bus_stems.split(",") if part.strip()]
            set_bus(studio, bus_name, names, float(bus_volume))
            apply_bus(project, studio, bus_name)
            save_studio(run_dir, studio)
            save_project(run_dir, project, force=True)
            st.rerun()

    st.markdown("**Mix**")
    strength_col, auto_col, master_col = st.columns([2, 1, 1], vertical_alignment="bottom")
    with strength_col:
        strength = st.slider("Auto Mix strength", 0, 100, 100, key=f"automix_{run_dir.name}")
    with auto_col:
        if st.button("Auto Mix", key=f"automix_btn_{run_dir.name}", width="stretch"):
            volumes = project.setdefault("mixer", {}).setdefault("volumesDb", {})
            project["mixer"]["volumesDb"] = auto_mix_volumes(volumes, strength)
            save_project(run_dir, project, force=True)
            st.rerun()
    with master_col:
        master = st.button("Master", key=f"master_{run_dir.name}", width="stretch")
    if master:
        wavs = sorted(run_dir.glob("*.wav"))
        if not wavs:
            st.caption("Save a mix first.")
        else:
            peak_master(wavs[0], run_dir / "master.wav")
            st.caption("Master")
    if st.button("Restore previous project", key=f"undo_{run_dir.name}", type="tertiary"):
        if restore_project(run_dir):
            st.toast("Restored the previous project.")
        st.rerun()


def _render_studio_notes(run_dir: Path, studio: dict) -> None:
    for note in studio.get("notes") or []:
        st.caption(f"{note.get('author')}: {note.get('text')}")
    author_col, body_col, add_col = st.columns([1, 3, 1], vertical_alignment="bottom")
    with author_col:
        author = st.selectbox("Note author", ["Owner", "Listener"], key=f"note_author_{run_dir.name}")
    with body_col:
        body = st.text_input("Note", key=f"note_body_{run_dir.name}")
    with add_col:
        if st.button("Add note", key=f"note_add_{run_dir.name}", width="stretch") and body.strip():
            add_note(studio, author, body)
            save_studio(run_dir, studio)
            st.rerun()
    for comment in studio.get("comments") or []:
        st.caption(f"{comment.get('time')}s {comment.get('author')}: {comment.get('text')}")
    time_col, comment_col, cadd_col = st.columns([1, 3, 1], vertical_alignment="bottom")
    with time_col:
        when = st.number_input("Comment time", value=0.0, key=f"comment_time_{run_dir.name}")
    with comment_col:
        comment_body = st.text_input("Comment", key=f"comment_body_{run_dir.name}")
    with cadd_col:
        if st.button("Add comment", key=f"comment_add_{run_dir.name}", width="stretch") and comment_body.strip():
            add_comment(studio, author, comment_body, float(when))
            save_studio(run_dir, studio)
            st.rerun()
    if st.button("Seek comment", key=f"comment_seek_{run_dir.name}", type="tertiary") and studio.get("comments"):
        st.session_state["isolate_seek_sec"] = float(studio["comments"][-1]["time"])
        st.caption(f"Seek {studio['comments'][-1]['time']} s")


def _render_studio_ideas(run_dir: Path, studio: dict) -> None:
    prompt_col, save_col, gen_col = st.columns([3, 1, 1], vertical_alignment="bottom")
    with prompt_col:
        prompt = st.text_input("Prompt", key=f"prompt_{run_dir.name}")
    with save_col:
        if st.button("Save prompt", key=f"prompt_save_{run_dir.name}", width="stretch") and prompt.strip():
            save_prompt(studio, prompt)
            save_studio(run_dir, studio)
            st.rerun()
    with gen_col:
        generate = st.button("Generate", key=f"generate_{run_dir.name}", width="stretch")
    for earlier in studio.get("prompts") or []:
        st.caption(earlier)
    if generate:
        result = generation_result()
        st.caption(result["message"])
        st.caption("No audio. No MIDI.")

    voice_col, convert_col = st.columns([3, 2], vertical_alignment="bottom")
    with voice_col:
        voice = st.text_input("Target voice", key=f"voice_{run_dir.name}")
    with convert_col:
        convert = st.button("Convert voice", key=f"voice_convert_{run_dir.name}", width="stretch")
    if convert:
        st.caption(name_voice(studio, voice))
        save_studio(run_dir, studio)
    ref_col, ref_save_col = st.columns([3, 2], vertical_alignment="bottom")
    with ref_col:
        reference = st.text_input("Custom voice reference", key=f"voice_ref_{run_dir.name}")
    with ref_save_col:
        save_voice = st.button("Save custom voice", key=f"voice_save_{run_dir.name}", width="stretch")
    if save_voice:
        save_custom_voice(studio, voice or "Voice", reference)
        save_studio(run_dir, studio)
        st.caption("Saved the voice name and reference file.")


def _render_studio_midi(run_dir: Path, studio: dict) -> None:
    for note in studio.get("midi") or []:
        st.caption(f"MIDI {note['pitch']} at {note['start']}s for {note['length']}s")
    add_col, del_col, _spacer = st.columns([1, 1, 2])
    with add_col:
        if st.button("Add MIDI note", key=f"midi_add_{run_dir.name}", width="stretch"):
            add_midi_note(studio, 60, 0.0, 0.5)
            save_studio(run_dir, studio)
            st.rerun()
    with del_col:
        if st.button("Delete MIDI note", key=f"midi_del_{run_dir.name}", width="stretch"):
            delete_midi_note(studio, 0)
            save_studio(run_dir, studio)
            st.rerun()

    extra = run_dir / "extra_tracks"
    takes = sorted(path.name for path in extra.glob("*") if path.is_file()) if extra.is_dir() else []
    if not takes:
        st.caption("Add a recorded take under Add tracks to choose between takes here.")
        return
    take_col, keep_col = st.columns([3, 1], vertical_alignment="bottom")
    with take_col:
        chosen = st.selectbox("Chosen take", takes, key=f"take_{run_dir.name}")
    with keep_col:
        keep = st.button("Keep this take", key=f"take_save_{run_dir.name}", width="stretch")
    if keep:
        set_chosen_take(studio, extra, chosen)
        save_studio(run_dir, studio)
        st.caption(f"Chosen take: {studio.get('chosen_take')}")


def _render_studio_share(run_dir: Path) -> None:
    share_col, session_col, lib_col = st.columns(3)
    with share_col:
        share = st.button("Share this song", key=f"share_{run_dir.name}", width="stretch")
    with session_col:
        session = st.button("Session code", key=f"session_{run_dir.name}", width="stretch")
    folder = str(st.session_state.get("library_folder") or "")
    with lib_col:
        to_library = bool(folder) and st.button(
            "Save song to library folder", key=f"lib_save_{run_dir.name}", width="stretch"
        )
    if share:
        st.caption(create_share(run_dir))
    if session:
        st.caption(save_session(run_dir))
    if to_library:
        save_song_to_library(run_dir, Path(folder))
        st.caption("Saved into the library folder.")

    st.markdown("**Export for other apps**")
    xml_col, daw_col, zip_col = st.columns(3)
    with xml_col:
        xml = st.button("MusicXML", key=f"xml_{run_dir.name}", width="stretch")
    with daw_col:
        dawproject = st.button("DAWproject", key=f"dawproject_{run_dir.name}", width="stretch")
    with zip_col:
        dawzip = st.button("DAW zip", key=f"dawzip_{run_dir.name}", width="stretch")
    if xml:
        analysis = _analysis(run_dir)
        dest = write_musicxml(analysis.get("chords") or [], analysis.get("measures") or [], run_dir / "score.musicxml")
        st.caption("Wrote score.musicxml." if dest else "This run has no chords and no tab.")
    if dawproject:
        stems = sorted(path.name for path in run_dir.glob("*.wav"))
        write_dawproject(stems, run_dir / "song.dawproject")
        st.caption("Wrote song.dawproject.")
    if dawzip:
        write_daw_zip({path.stem: path for path in run_dir.glob("*.wav")}, run_dir / "daw.zip")
        st.caption("Wrote daw.zip.")

    titles = st.text_area("Setlist titles", key=f"setlist_titles_{run_dir.name}")
    if st.button("Import setlist titles", key=f"setlist_import_{run_dir.name}"):
        rows = [{"title": line.strip(), "run_dir": str(run_dir)} for line in titles.splitlines() if line.strip()]
        matched = import_setlist({"titles": [row["title"] for row in rows]}, rows)
        st.caption(json.dumps(export_setlist({"id": "local", "name": "Imported", "titles": [row["title"] for row in rows]})))
        st.caption(f"Matched {len(matched)} song(s). Songs were not deleted.")


def open_selected_library_song(name: str) -> None:
    folder = str(st.session_state.get("library_folder") or "")
    if not folder or not name:
        return
    opened = open_library_song(Path(folder) / name, DATA_DIR)
    st.session_state["isolate_viewing_run_dir"] = str(opened)
    st.session_state["isolate_run_dir"] = str(opened)


def _analysis(run_dir: Path) -> dict:
    path = run_dir / "analysis.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError, UnicodeError):
        return {}
    return data if isinstance(data, dict) else {}
