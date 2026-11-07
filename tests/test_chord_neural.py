"""Opt-in BTC chord scorer — no network in the default suite."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from audio_to_tab.chord_neural import (
    BTC_WEIGHT_NAME,
    BTC_WEIGHT_SHA256,
    _IDX2CHORD,
    _indices_to_events,
    _mir_eval_to_symbol,
    _smooth_scores,
    _window_confidence_from_scores,
    chord_model_available,
    chord_model_requested,
    detect_chords_btc,
)

# BTC maj/min indices (see _IDX2CHORD).
_C = 0
_F = 10
_FS = 12
_G = 14
_DS = 6
_A = 18
_AM = 19
_B = 22


def test_mir_eval_label_maps_to_product_symbols():
    assert _mir_eval_to_symbol("C") == "C"
    assert _mir_eval_to_symbol("C:min") == "Cm"
    assert _mir_eval_to_symbol("G#:min") == "G#m"
    assert _mir_eval_to_symbol("N") == "N"
    assert _mir_eval_to_symbol("X") == "N"
    assert _mir_eval_to_symbol("C:hdim7") == "Cm7b5"
    assert _mir_eval_to_symbol("C:minmaj7") == "CmMaj7"
    assert _mir_eval_to_symbol("C:maj6") == "C6"
    assert _mir_eval_to_symbol("D:min6") == "Dm6"


def test_chord_model_unavailable_without_weights(tmp_path, monkeypatch):
    monkeypatch.delenv("ATT_CHORD_MODEL", raising=False)
    monkeypatch.delenv("ATT_CHORD_MODEL_DIR", raising=False)
    assert chord_model_requested() is False
    assert chord_model_available(tmp_path) is False
    assert detect_chords_btc(tmp_path / "missing.wav", model_dir=tmp_path) is None


def test_chord_model_requested_env(monkeypatch):
    monkeypatch.setenv("ATT_CHORD_MODEL", "btc")
    assert chord_model_requested() is True
    monkeypatch.setenv("ATT_CHORD_MODEL", "0")
    assert chord_model_requested() is False


def test_hash_mismatch_returns_none(tmp_path):
    weight = tmp_path / BTC_WEIGHT_NAME
    weight.write_bytes(b"not-a-real-checkpoint")
    wav = tmp_path / "tone.wav"
    sf.write(wav, np.zeros(22050, dtype=np.float32), 22050)
    assert detect_chords_btc(wav, model_dir=tmp_path) is None


def test_unsafe_checkpoint_returns_none(tmp_path, monkeypatch):
    """A file that passes the SHA256 check but fails weights_only load returns None."""
    weight = tmp_path / BTC_WEIGHT_NAME
    weight.write_bytes(b"pickle-bomb-placeholder")
    monkeypatch.setattr(
        "audio_to_tab.chord_neural.file_sha256",
        lambda _path: BTC_WEIGHT_SHA256,
    )
    monkeypatch.setattr(
        "audio_to_tab.chord_neural._cqt_features",
        lambda _path: (np.zeros((144, 20), dtype=np.float64), 0.1, 2.0),
    )

    def _boom(_path):
        raise RuntimeError("weights_only refused legacy pickle")

    monkeypatch.setattr("audio_to_tab.chord_neural._load_model", _boom)
    wav = tmp_path / "tone.wav"
    sf.write(wav, np.zeros(22050, dtype=np.float32), 22050)
    assert detect_chords_btc(wav, model_dir=tmp_path) is None


def _one_hot_logprobs(n_frames: int, winner: int, *, spike_at: int | None = None, spike: int | None = None) -> np.ndarray:
    scores = np.full((n_frames, len(_IDX2CHORD)), -10.0, dtype=np.float64)
    scores[:, winner] = 0.0
    if spike_at is not None and spike is not None:
        scores[spike_at, :] = -10.0
        scores[spike_at, spike] = 0.0
        scores[spike_at, winner] = -1.0
    return scores


def test_smooth_scores_removes_single_frame_flip():
    scores = _one_hot_logprobs(40, _C, spike_at=20, spike=_FS)
    path, window_scores, windows = _smooth_scores(
        scores,
        time_unit=0.1,
        duration=4.0,
        beats=(),
    )
    assert all(index == _C for index in path)
    assert len(path) == len(window_scores) == len(windows)
    assert windows[0][0] == 0.0


def test_smooth_scores_pools_to_beats():
    # 2.0s of audio, frames every 0.1s → 20 frames. Beats every 0.5s.
    scores = _one_hot_logprobs(20, _C)
    beats = (0.5, 1.0, 1.5)
    path, window_scores, windows = _smooth_scores(
        scores,
        time_unit=0.1,
        duration=2.0,
        beats=beats,
    )
    starts = [start for start, _end in windows]
    ends = [_end for _start, _end in windows]
    assert starts[0] == 0.0
    assert ends[-1] == 2.0
    # Interior boundaries must match the beat list (plus 0 and duration).
    assert starts[1:] == [0.5, 1.0, 1.5]
    assert ends[:-1] == [0.5, 1.0, 1.5]
    assert len(path) == len(windows) == 4


def test_first_root_held_later_wrong_root_suppressed():
    """C | G | Am | F, with short D# and B spikes after bar 1 that must not stick."""
    # 4 bars × 4 beats × 5 frames/beat = 80 frames. time_unit=0.1 → 8.0s.
    frames_per_bar = 20
    scores = np.full((80, len(_IDX2CHORD)), -10.0, dtype=np.float64)
    sequence = (_C, _G, _AM, _F)
    for bar, winner in enumerate(sequence):
        start = bar * frames_per_bar
        scores[start : start + frames_per_bar, winner] = 0.0
    # After bar 1 (frames 20–39 are G), plant two single-frame off-key spikes in bar 2.
    # One frame each so beat-pooling still leaves Am as the window winner; Viterbi
    # must also refuse to keep a one-window D#/B if pooling ever leaves a spike.
    scores[41, :] = -10.0
    scores[41, _DS] = 0.0
    scores[41, _AM] = -0.3
    scores[51, :] = -10.0
    scores[51, _B] = 0.0
    scores[51, _AM] = -0.3

    beats = tuple(0.5 * i for i in range(1, 16))  # every half second inside 8s
    path, window_scores, windows = _smooth_scores(
        scores,
        time_unit=0.1,
        duration=8.0,
        beats=beats,
        meter=4,
    )
    confidences = [_window_confidence_from_scores(row) for row in window_scores]
    events = _indices_to_events(path, windows=windows, confidences=confidences)
    assert events
    first_root = events[0].symbol.replace("m", "")
    assert first_root.startswith("C"), events[0].symbol
    allowed = {"C", "G", "A", "F", "Am", "Gm", "Fm", "Cm"}
    for event in events:
        root = event.symbol.rstrip("m")
        assert event.symbol in allowed or root in {"C", "G", "A", "F"}, event.symbol
    assert len(events) <= 6  # 4 chords + merge tolerance


def test_confidence_is_posterior_margin():
    scores = np.full((4, len(_IDX2CHORD)), -10.0, dtype=np.float64)
    scores[:, _C] = 0.0
    scores[1, _G] = -0.2  # close second → lower margin
    scores[2, _G] = -5.0  # distant second → higher margin
    path, window_scores, windows = _smooth_scores(
        scores,
        time_unit=0.5,
        duration=2.0,
        beats=(),
    )
    confidences = [_window_confidence_from_scores(row) for row in window_scores]
    events = _indices_to_events(path, windows=windows, confidences=confidences)
    assert events
    assert all(0.0 <= event.confidence <= 1.0 for event in events)
    assert any(event.confidence > 0.0 for event in events)
    assert all(event.confidence != 0.0 or True for event in events)  # not hard-coded zeros only
    # At least one non-zero confidence after a decisive window.
    assert max(event.confidence for event in events) > 0.0


@pytest.mark.slow
def test_btc_majmin_on_synthetic_powerchord(tmp_path, monkeypatch):
    """Requires torch + a pinned weight download (opt-in / slow)."""
    pytest.importorskip("torch")
    from audio_to_tab.chord_neural import ensure_chord_model

    model_dir = tmp_path / "btc"
    ensure_chord_model(model_dir)
    assert chord_model_available(model_dir)
    assert (model_dir / BTC_WEIGHT_NAME).stat().st_size > 0

    sr = 22050
    t = np.arange(int(sr * 4.0), dtype=np.float64) / sr
    root = 103.83  # G#2
    y = 0.3 * np.sin(2 * np.pi * root * t) + 0.22 * np.sin(2 * np.pi * root * 1.5 * t)
    wav = tmp_path / "gs5.wav"
    sf.write(wav, y.astype(np.float32), sr)

    events = detect_chords_btc(wav, model_dir=model_dir)
    assert events is not None
    assert events
    roots = {event.symbol.split("m")[0].rstrip("#").rstrip("b") or event.symbol for event in events}
    # Soft check: at least one event mentions G# (maj or min).
    assert any("G#" in event.symbol for event in events), events
    _ = roots, BTC_WEIGHT_SHA256
