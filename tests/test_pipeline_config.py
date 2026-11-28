"""PipelineConfig validation — quality tokens must match isolate/API/CLI."""

from __future__ import annotations

import pytest

from audio_to_tab.pipeline import PipelineConfig


@pytest.mark.parametrize("quality", ["fast", "balanced", "high", "extreme"])
def test_pipeline_config_accepts_isolate_quality_tokens(quality: str):
    cfg = PipelineConfig(demucs_quality=quality)
    assert cfg.demucs_quality == quality


def test_pipeline_config_aliases_legacy_best_to_high():
    cfg = PipelineConfig(demucs_quality="best")
    assert cfg.demucs_quality == "high"


def test_pipeline_config_rejects_unknown_quality():
    with pytest.raises(ValueError, match="Invalid demucs_quality"):
        PipelineConfig(demucs_quality="ultra")
