"""Library trash: usage and permanent delete."""

from __future__ import annotations

from pathlib import Path

from ui.library_song import (
    delete_library_song,
    empty_library_trash,
    list_trashed_songs,
    purge_trashed_song,
    recover_library_song,
    trash_usage,
)


def _trashed(data: Path, name: str, size: int = 10) -> Path:
    run = data / name
    run.mkdir(parents=True)
    (run / "meta.json").write_text("{}", encoding="utf-8")
    (run / "guitar.wav").write_bytes(b"x" * size)
    moved = delete_library_song(run, data)
    assert moved is not None
    return moved


def test_trash_usage_counts_songs_and_bytes(tmp_path: Path):
    assert trash_usage(tmp_path) == (0, 0)
    _trashed(tmp_path, "a", 10)
    _trashed(tmp_path, "b", 30)
    assert trash_usage(tmp_path) == (2, 44)


def test_purge_trashed_song_removes_one_and_the_rest_still_recovers(tmp_path: Path):
    gone = _trashed(tmp_path, "gone")
    kept = _trashed(tmp_path, "kept")
    assert purge_trashed_song(gone, tmp_path) is True
    assert not gone.exists()
    assert list_trashed_songs(tmp_path) == [kept]
    restored = recover_library_song(kept, tmp_path)
    assert restored == tmp_path / "kept"
    assert (restored / "guitar.wav").is_file()


def test_purge_trashed_song_refuses_anything_outside_the_trash(tmp_path: Path):
    live = tmp_path / "live"
    live.mkdir()
    trashed = _trashed(tmp_path, "a")
    nested = trashed / "nested"
    nested.mkdir()
    link = trashed.parent / "link"
    link.symlink_to(live, target_is_directory=True)
    sibling_link = trashed.parent / "sibling"
    sibling_link.symlink_to(trashed, target_is_directory=True)
    for bad in (live, tmp_path, trashed.parent, nested, trashed.parent / "..", link, sibling_link):
        assert purge_trashed_song(bad, tmp_path) is False, bad
    assert live.is_dir()
    assert nested.is_dir()


def test_empty_library_trash_reports_counts_and_leaves_live_songs(tmp_path: Path):
    _trashed(tmp_path, "a")
    _trashed(tmp_path, "b")
    live = tmp_path / "live"
    live.mkdir()
    assert empty_library_trash(tmp_path) == (2, 0)
    assert empty_library_trash(tmp_path) == (0, 0)
    assert live.is_dir()
    assert trash_usage(tmp_path) == (0, 0)


def test_empty_library_trash_counts_a_refused_entry_as_failed(tmp_path: Path):
    _trashed(tmp_path, "a")
    live = tmp_path / "live"
    live.mkdir()
    (tmp_path / "library_trash" / "link").symlink_to(live, target_is_directory=True)
    assert empty_library_trash(tmp_path) == (1, 1)
    assert live.is_dir()
