"""Streamlit page: Settings — appearance + legal / local data (compliance)."""

from __future__ import annotations

import streamlit as st

from ui.common import DATA_DIR, clear_all_local_runs, legal_docs_dir
from ui.isolate_jobs import prune_region_previews, reclaim_checkpoints, sweep_uploads
from ui.library_song import empty_library_trash, trash_usage
from ui.studio_panel import render_library_tools
from ui.isolate_state import (
    THEME_MODE_KEY,
    save_theme_state,
)

_MODE_LABELS = {"light": "Light", "dark": "Dark", "system": "System"}

_STORAGE_FLASH_KEY = "settings_storage_flash"

_LEGAL_FILES = (
    ("Privacy policy", "privacy.md"),
    ("Terms of service", "terms.md"),
    ("Refund policy", "refund.md"),
    ("Cookie policy", "cookies.md"),
    ("Notices (fonts & images)", "NOTICES.md"),
    ("Third-party SDKs", "THIRD_PARTY_SDKS.md"),
)
_LEGAL_TITLES = [title for title, _ in _LEGAL_FILES]
_LEGAL_BY_TITLE = {title: filename for title, filename in _LEGAL_FILES}


def _persist_theme() -> None:
    # Streamlit calls on_change with no arguments. The widget value is already
    # in session_state, so this wrapper supplies the mapping save_theme_state needs.
    save_theme_state(st.session_state)


def _format_bytes(size: int) -> str:
    if size >= 1024**3:
        return f"{size / 1024**3:.1f} GB"
    return f"{size / 1024**2:.1f} MB"


def _render_storage_cleanup() -> None:
    # The result is flashed through session_state so the rerun can redraw the totals.
    flash = st.session_state.pop(_STORAGE_FLASH_KEY, None)
    if flash:
        message, is_error = flash
        (st.error if is_error else st.success)(message)

    count, size = trash_usage(DATA_DIR)
    st.markdown(f"**Deleted songs: {count} ({_format_bytes(size)})**")
    confirm_trash = st.checkbox(
        "I understand deleted songs can no longer be recovered",
        value=False,
        key="settings_empty_trash_confirm",
    )
    if st.button(
        "Empty deleted songs",
        type="secondary",
        disabled=not confirm_trash or not count,
        key="settings_empty_trash",
    ):
        purged, failed = empty_library_trash(DATA_DIR)
        if failed:
            message = f"Removed {purged} deleted song(s); {failed} could not be removed."
        else:
            message = f"Permanently removed {purged} deleted song(s)."
        st.session_state[_STORAGE_FLASH_KEY] = (message, bool(failed))
        st.rerun()

    st.markdown("**Reclaim space**")
    st.caption(
        "Removes leftover working files from finished separations, section previews, "
        "and the app's copies of uploads or downloads older than 7 days that no "
        "unfinished job needs. Songs, stems, job history, paused jobs and your own "
        "files are kept. After an upload copy is removed, add the file again to "
        "separate that song another way. The app also cleans old uploads and "
        "previews by itself."
    )
    confirm_reclaim = st.checkbox(
        "I understand this permanently deletes leftover working files",
        value=False,
        key="settings_reclaim_confirm",
    )
    if st.button(
        "Reclaim space",
        type="secondary",
        disabled=not confirm_reclaim,
        key="settings_reclaim",
    ):
        jobs_pruned, freed = reclaim_checkpoints()
        uploads, upload_bytes = sweep_uploads()
        preview_bytes = prune_region_previews(max_bytes=0)
        total = freed + upload_bytes + preview_bytes
        st.session_state[_STORAGE_FLASH_KEY] = (
            f"Freed {_format_bytes(total)}: {jobs_pruned} finished job(s), "
            f"{uploads} old upload(s), {_format_bytes(preview_bytes)} of previews.",
            False,
        )
        st.rerun()


def main() -> None:
    st.title("Settings")
    current_mode = st.session_state.get(THEME_MODE_KEY, "dark")
    if current_mode not in _MODE_LABELS:
        current_mode = "dark"
    st.radio(
        "Appearance",
        options=list(_MODE_LABELS.keys()),
        format_func=lambda key: _MODE_LABELS[key],
        index=list(_MODE_LABELS.keys()).index(current_mode),
        key=THEME_MODE_KEY,
        horizontal=True,
        on_change=_persist_theme,
    )
    st.caption("The palette is dark Tyrian blue and yellow-orange.")

    st.divider()
    st.subheader("Local data")
    st.caption(
        f"Run outputs and uploads for this Desktop UI live under `{DATA_DIR}`. "
        "Clear local run data deletes saved Tab PDF runs (and any other run folder with "
        "metadata that is not a library song). It keeps library songs, deleted songs, "
        "job history, region previews, uploads without run metadata, and your original files."
    )
    confirm = st.checkbox(
        "I understand this permanently deletes local Tab PDF run folders",
        value=False,
        key="settings_clear_runs_confirm",
    )
    if st.button(
        "Clear local run data",
        type="secondary",
        disabled=not confirm,
        key="settings_clear_runs",
    ):
        deleted, failed = clear_all_local_runs()
        if failed:
            st.error(f"Cleared {deleted} run folder(s); {failed} could not be removed.")
        else:
            st.success(f"Cleared {deleted} local run folder(s).")

    _render_storage_cleanup()

    st.divider()
    render_library_tools()
    st.divider()
    st.subheader("Legal")
    st.caption("Demo draft · not legal advice")
    st.markdown("[orallojohnjames@gmail.com](mailto:orallojohnjames@gmail.com)")

    legal_root = legal_docs_dir()
    if not legal_root.is_dir():
        st.info(
            "Legal markdown was not found next to this install. "
            "See `docs/legal/` in the source repository, or the hosted website Legal pages."
        )
    else:
        with st.expander("View policies", expanded=False):
            selected = st.selectbox(
                "Document",
                options=_LEGAL_TITLES,
                key="settings_legal_doc",
            )
            path = legal_root / _LEGAL_BY_TITLE[selected]
            if path.is_file():
                st.markdown(path.read_text(encoding="utf-8"))
            else:
                st.info(f"That document file is missing ({path.name}).")


if __name__ == "__main__":
    main()
