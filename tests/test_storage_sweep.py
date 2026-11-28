"""Automatic cleanup of old upload staging folders and region previews."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path

import pytest

import ui.common as common
import ui.isolate_jobs as jobs

OLD = time.time() - 30 * 86400


@pytest.fixture()
def data(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(common, "DATA_DIR", tmp_path)
    monkeypatch.setattr(jobs, "DATA_DIR", tmp_path)
    monkeypatch.setattr(jobs, "_SWEPT", False)
    return tmp_path


def _age(path: Path, when: float = OLD) -> None:
    for item in [*path.rglob("*"), path] if path.is_dir() else [path]:
        os.utime(item, (when, when))


def _folder(data: Path, *names: str, old: bool = True) -> Path:
    folder = data / str(uuid.uuid4())
    folder.mkdir()
    for name in names:
        (folder / name).write_bytes(b"x" * 10)
    if old:
        _age(folder)
    return folder


def _job(job_id: str, status: str, **spec) -> None:
    jobs._ensure_job_dir(job_id)
    jobs._write_json(jobs._spec_path(job_id), spec)
    jobs.write_status(job_id, status=status)


def test_sweep_removes_old_uploads_only(data: Path):
    upload = _folder(data, "song.mp3", ".DS_Store")
    video = _folder(data, "clip.mp4", "clip.extracted.wav")
    empty = _folder(data)
    recent = _folder(data, "new.wav", old=False)

    assert jobs.sweep_uploads() == (3, 40)
    assert not upload.exists() and not video.exists() and not empty.exists()
    assert recent.is_dir()
    assert jobs.sweep_uploads() == (0, 0)


def test_sweep_judges_age_by_the_folder_too(data: Path):
    """copy2 keeps the user's old file date, so a fresh copy must survive."""
    folder = _folder(data, "old-song.wav", old=False)
    os.utime(folder / "old-song.wav", (OLD, OLD))
    assert jobs.sweep_uploads() == (0, 0)
    assert folder.is_dir()


def test_sweep_keeps_songs_unknown_content_and_other_folders(data: Path):
    song = _folder(data, "meta.json", "guitar.wav")
    analysed = _folder(data, "guitar.wav", "analysis.json")
    nested = _folder(data, "a.wav")
    (nested / "tab").mkdir()
    _age(nested)
    named = data / "isolate_extra"
    named.mkdir()
    (named / "a.wav").write_bytes(b"x")
    _age(named)
    outside = data.parent / f"{data.name}-outside"
    outside.mkdir()
    (outside / "a.wav").write_bytes(b"x")
    _age(outside)
    (data / str(uuid.uuid4())).symlink_to(outside, target_is_directory=True)

    assert jobs.sweep_uploads() == (0, 0)
    for path in (song, analysed, nested, named, outside):
        assert path.is_dir(), path
    assert (outside / "a.wav").is_file()


@pytest.mark.parametrize("status", ["queued", "running", "pausing", "paused", "failed"])
def test_sweep_keeps_the_source_of_an_unfinished_job(data: Path, status: str):
    upload = _folder(data, "song.mp3")
    _job("j", status, audio_path=str(upload / "song.mp3"), output_dir=str(data / "out"))
    assert jobs.sweep_uploads() == (0, 0)
    assert (upload / "song.mp3").is_file()


def test_sweep_frees_a_finished_upload_but_keeps_job_outputs(data: Path):
    upload = _folder(data, "song.mp3")
    reseparate_out = _folder(data, "lead.wav")
    _job("j", "succeeded", audio_path=str(upload / "song.mp3"), output_dir=str(reseparate_out))
    assert jobs.sweep_uploads() == (1, 10)
    assert not upload.exists()
    assert (reseparate_out / "lead.wav").is_file()


@pytest.mark.parametrize("where", ["", "library_trash"])
def test_sweep_keeps_a_folder_that_a_song_still_references(data: Path, where: str):
    stems = _folder(data, "lead.wav")
    song = data / where / "song"
    song.mkdir(parents=True)
    (song / "meta.json").write_text(
        json.dumps({"artifacts": {"lead": str(stems / "lead.wav")}}), encoding="utf-8"
    )
    assert jobs.sweep_uploads() == (0, 0)
    assert stems.is_dir()


def test_prune_previews_drops_old_files_and_caps_the_total(data: Path):
    cache = data / "region_previews"
    cache.mkdir()
    now = time.time()
    for name, age in (("stale", 3 * 86400), ("older", 7200), ("newer", 3600), ("live", 5)):
        path = cache / f"{name}.wav"
        path.write_bytes(b"x" * 100)
        _age(path, now - age)

    assert jobs.prune_region_previews(max_bytes=250) == 200
    assert sorted(p.name for p in cache.iterdir()) == ["live.wav", "newer.wav"]
    # A preview written moments ago is in use, even over the cap.
    assert jobs.prune_region_previews(max_bytes=0) == 100
    assert [p.name for p in cache.iterdir()] == ["live.wav"]


def test_prune_previews_ignores_a_symlinked_cache(data: Path):
    outside = data / "keep"
    outside.mkdir()
    (outside / "a.wav").write_bytes(b"x")
    _age(outside / "a.wav")
    (data / "region_previews").symlink_to(outside, target_is_directory=True)
    assert jobs.prune_region_previews() == 0
    assert (outside / "a.wav").is_file()


def test_sweep_storage_once_runs_once_per_process(data: Path):
    first = _folder(data, "a.wav")
    jobs.sweep_storage_once()
    assert not first.exists()
    second = _folder(data, "b.wav")
    jobs.sweep_storage_once()
    assert second.is_dir()
