"""PipelineConfig quality allowlist vs API/CLI."""

from __future__ import annotations

import pytest

from audio_to_tab.pipeline import PipelineConfig


@pytest.mark.parametrize("quality", ["fast", "balanced", "high", "extreme"])
def test_pipeline_config_accepts_api_qualities(quality: str) -> None:
    cfg = PipelineConfig(demucs_quality=quality)
    assert cfg.demucs_quality == quality


def test_pipeline_config_aliases_best_to_high() -> None:
    cfg = PipelineConfig(demucs_quality="best")
    assert cfg.demucs_quality == "high"


def test_pipeline_config_rejects_unknown_quality() -> None:
    with pytest.raises(ValueError, match="Invalid demucs_quality"):
        PipelineConfig(demucs_quality="turbo")
