"""GET /v1/jobs/{id}/stems must read JobRecord.artifacts as a dict."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytest.importorskip("fastapi")

from tests.backend_test_utils import configure_backend, fake_wav_bytes, login_headers


def test_job_stem_names_from_artifact_dict(tmp_path, monkeypatch) -> None:
    main_mod = configure_backend(
        tmp_path,
        monkeypatch,
        ATT_REQUIRE_AUTH="false",
        ATT_DEMO_MODE="true",
    )
    with TestClient(main_mod.app) as client:
        headers = login_headers(client)
        upload = client.post(
            "/v1/uploads/audio",
            headers=headers,
            files={"file": ("mix.wav", fake_wav_bytes(), "audio/wav")},
        )
        assert upload.status_code == 200
        upload_id = upload.json()["upload_id"]

        async def noop_enqueue(*_args, **_kwargs):
            return None

        monkeypatch.setattr(main_mod, "_enqueue_or_run", noop_enqueue)
        created = client.post(
            "/v1/isolate/jobs",
            headers=headers,
            json={
                "upload_id": upload_id,
                "model": "htdemucs",
                "quality": "fast",
                "max_duration_sec": 15,
            },
        )
        assert created.status_code == 200, created.text
        job_id = created.json()["id"]

        for name in ("vocals", "drums", "bass", "guitar"):
            (tmp_path / f"{name}.wav").write_bytes(fake_wav_bytes())

        main_mod.job_manager.set_artifacts(
            job_id,
            {
                "vocals": str(tmp_path / "vocals.wav"),
                "drums": str(tmp_path / "drums.wav"),
                "bass": str(tmp_path / "bass.wav"),
                "guitar": str(tmp_path / "guitar.wav"),
            },
        )

        res = client.get(f"/v1/jobs/{job_id}/stems", headers=headers)
        assert res.status_code == 200, res.text
        stems = res.json()["stems"]
        assert "vocals" in stems
        assert "guitar" in stems
