"""Desktop local run clearing (compliance C20)."""

from __future__ import annotations

from pathlib import Path

import ui.common as common


def _folder(root: Path, name: str, meta: str | None) -> Path:
    path = root / name
    path.mkdir(parents=True)
    if meta is not None:
        (path / "meta.json").write_text(meta, encoding="utf-8")
    return path


def test_clear_all_local_runs(tmp_path: Path, monkeypatch):
    data = tmp_path / "ui_runs"
    data.mkdir()
    tab = _folder(data, "tab-run", '{"page": "tab_pdf"}')
    kept = [
        _folder(data, "song", '{"page": "isolate"}'),
        _folder(data, "staging", None),
        _folder(data, "unreadable", "not json"),
        # Reserved names are skipped even if a meta.json lands in them.
        _folder(data, "isolate_jobs", '{"page": "tab_pdf"}'),
        _folder(data, "library_trash", '{"page": "tab_pdf"}'),
        _folder(data, "region_previews", '{"page": "tab_pdf"}'),
    ]
    (data / "stray.txt").write_text("x", encoding="utf-8")
    monkeypatch.setattr(common, "DATA_DIR", data)

    assert common.clear_all_local_runs() == (1, 0)
    assert not tab.exists()
    for path in kept:
        assert path.is_dir(), path
    assert (data / "stray.txt").exists()
