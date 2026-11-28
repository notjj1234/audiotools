"""Tests for lead/rhythm guitar post-process."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import soundfile as sf

from audio_to_tab.lead_rhythm import (
    ROLE_MARGIN_MIN,
    SEPARABILITY_FLOOR,
    SPATIAL_CORR_MAX,
    SPATIAL_CORR_RELAXED_MAX,
    SPECTRAL_SEPARABILITY_FLOOR,
    LeadRhythmDiagnostics,
    LeadRhythmThresholds,
    build_midside_pair,
    build_register_pair,
    build_spatial_pair,
    build_spectral_pair,
    classify_lead_rhythm_roles,
    extract_role_features_from_notes,
    score_candidate_pair,
    split_lead_rhythm_guitar,
    RoleFeatures,
)


def _write_stereo(path: Path, left: np.ndarray, right: np.ndarray, sr: int = 44100) -> None:
    sf.write(str(path), np.column_stack([left, right]).astype(np.float32), sr, subtype="PCM_16")


def _dominant_hz(x: np.ndarray, sr: int) -> float:
    x = np.asarray(x, dtype=np.float64)
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x))))
    return float(np.fft.rfftfreq(len(x), 1.0 / sr)[int(np.argmax(spec))])


def _si_sdr(est: np.ndarray, ref: np.ndarray) -> float:
    n = min(len(est), len(ref))
    est = np.asarray(est[:n], dtype=np.float64)
    ref = np.asarray(ref[:n], dtype=np.float64)
    target = (np.dot(est, ref) / (np.dot(ref, ref) + 1e-12)) * ref
    noise = est - target
    return float(10 * np.log10((np.dot(target, target) + 1e-12) / (np.dot(noise, noise) + 1e-12)))


def test_diagnostics_json_roundtrip(tmp_path: Path):
    diag = LeadRhythmDiagnostics(
        outcome="ambiguous",
        reason="test",
        separability_score=0.1,
        method="none",
    )
    path = diag.write_json(tmp_path / "guitar_split_diagnostics.json")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "ambiguous" in text
    assert diag.to_dict()["reason"] == "test"


def test_spatial_pair_hard_pan(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
    left = np.sin(2 * np.pi * 220 * t)
    right = np.sin(2 * np.pi * 880 * t)
    path = tmp_path / "guitar.wav"
    _write_stereo(path, left, right, sr)
    pair = build_spatial_pair(path)
    assert pair is not None
    assert pair.method == "spatial"
    assert pair.separability >= SEPARABILITY_FLOOR * 0.5


def test_spatial_pair_rejects_identical_channels(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    mono = np.sin(2 * np.pi * 440 * t)
    path = tmp_path / "guitar.wav"
    _write_stereo(path, mono, mono, sr)
    assert build_spatial_pair(path) is None


def _mild_pan_two_guitar_signal(
    sr: int = 44100, dur: float = 2.0, lead_hz: float = 659.25, rhythm_hz: float = 146.83
) -> tuple[np.ndarray, np.ndarray]:
    """
    Two genuinely distinct guitar-like tones (E5 "lead" / D3 "rhythm") summed with
    only slight panning (55/45), not hard-panned. Raw sample correlation for two
    independent sources panned (p, 1-p) is 2p(1-p)/(p^2+(1-p)^2), which is already
    ~0.98 here — above SPATIAL_CORR_MAX — even though the channels are genuinely
    distinct (see lead_rhythm.py module docstring "Root cause").
    """
    t = np.linspace(0, dur, int(sr * dur), endpoint=False)
    lead = np.sin(2 * np.pi * lead_hz * t)
    rhythm = np.sin(2 * np.pi * rhythm_hz * t)
    left = 0.55 * lead + 0.45 * rhythm
    right = 0.45 * lead + 0.55 * rhythm
    return left, right


def test_spatial_pair_accepts_mild_pan_with_pitch_divergence(tmp_path: Path):
    """
    Old single-correlation-gate behavior would reject this (corr > SPATIAL_CORR_MAX)
    even though the channels carry clearly different predominant pitch content.
    Pitch-divergence evidence (no split required) rescues it below the relaxed
    ceiling.
    """
    sr = 44100
    left, right = _mild_pan_two_guitar_signal(sr)
    corr = float(np.corrcoef(left, right)[0, 1])
    assert SPATIAL_CORR_MAX < corr < SPATIAL_CORR_RELAXED_MAX

    path = tmp_path / "guitar.wav"
    _write_stereo(path, left, right, sr)
    pair = build_spatial_pair(path)
    assert pair is not None
    assert pair.method == "spatial"
    assert pair.correlation == pytest.approx(corr, abs=1e-4)
    assert pair.pitch_evidence is not None
    assert pair.pitch_evidence["divergence_semitones"] >= 3.0


def test_spatial_pair_still_rejects_mild_pan_same_pitch(tmp_path: Path):
    """
    Double-tracked-style content (same fundamental in both channels, just mildly
    panned) must NOT be rescued by pitch-divergence evidence — there is no real
    divergence to find, so it stays rejected (prefer ambiguous over mislabeling).
    """
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    rng = np.random.RandomState(0)
    take1 = np.sin(2 * np.pi * 220.3 * t) + 0.02 * rng.randn(len(t))
    take2 = np.sin(2 * np.pi * 219.7 * t) + 0.02 * rng.randn(len(t))
    left = 0.55 * take1 + 0.45 * take2
    right = 0.45 * take1 + 0.55 * take2
    corr = float(np.corrcoef(left, right)[0, 1])
    assert corr > SPATIAL_CORR_MAX

    path = tmp_path / "guitar.wav"
    _write_stereo(path, left, right, sr)
    assert build_spatial_pair(path) is None


def test_split_lead_rhythm_detects_mild_pan_two_guitar(tmp_path: Path):
    """
    End-to-end: a genuinely two-guitar signal that is mildly panned (not hard-panned,
    not dead-centered) now resolves to lead_rhythm via the spatial method, where the
    pre-fix single-correlation-gate logic would have found no admissible candidate
    pair at all and returned ambiguous.
    """
    sr = 44100
    left, right = _mild_pan_two_guitar_signal(sr)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, left, right, sr)

    extra, diag = split_lead_rhythm_guitar(guitar, tmp_path, use_basic_pitch=False)
    assert diag.outcome == "lead_rhythm"
    assert diag.method == "spatial"
    assert "lead_guitar" in extra and "rhythm_guitar" in extra
    assert diag.features.get("pitch_evidence") is not None


def test_score_candidate_pair_similar_is_low():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    a = np.sin(2 * np.pi * 440 * t).astype(np.float32)
    b = (a * 0.95).astype(np.float32)
    assert score_candidate_pair(a, b, sr) < SEPARABILITY_FLOOR


def test_score_candidate_pair_distinct_is_higher():
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    a = np.sin(2 * np.pi * 200 * t).astype(np.float32)
    b = np.sin(2 * np.pi * 2000 * t).astype(np.float32)
    assert score_candidate_pair(a, b, sr) > score_candidate_pair(a, a * 0.9, sr)


def test_classify_roles_clear_margin():
    lead = RoleFeatures(78.0, 12.0, 2.0, 1.1, 95.0, 0.4)
    rhythm = RoleFeatures(52.0, 4.0, 6.0, 2.8, 70.0, 0.12)
    assignment, margin, _ = classify_lead_rhythm_roles(lead, rhythm)
    assert assignment == "a_lead"
    assert margin >= ROLE_MARGIN_MIN


def test_classify_roles_ambiguous_when_similar():
    a = RoleFeatures(60.0, 5.0, 3.0, 1.5, 80.0, 0.2)
    b = RoleFeatures(61.0, 5.0, 3.1, 1.5, 80.0, 0.2)
    assignment, margin, _ = classify_lead_rhythm_roles(a, b)
    assert assignment == "ambiguous"
    assert margin < ROLE_MARGIN_MIN


def test_extract_role_features_from_notes():
    notes = [
        SimpleNamespace(pitch=76, velocity=90, start=0.0, end=0.4),
        SimpleNamespace(pitch=79, velocity=88, start=0.5, end=0.9),
        SimpleNamespace(pitch=72, velocity=85, start=1.0, end=1.3),
    ]
    feat = extract_role_features_from_notes(notes, duration_sec=2.0)
    assert feat.pitch_median == pytest.approx(76.0)
    assert feat.note_density == pytest.approx(1.5)
    assert feat.pitch_iqr >= 0.0


def test_role_scores_use_iqr_sustain_velocity():
    wide = RoleFeatures(70.0, 16.0, 2.0, 1.2, 100.0, 0.5)
    narrow = RoleFeatures(70.0, 2.0, 2.0, 1.2, 50.0, 0.1)
    assert wide.lead_score() > narrow.lead_score()
    assert narrow.rhythm_score() > wide.rhythm_score()


def test_split_lead_rhythm_success_without_basic_pitch(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    left = np.sin(2 * np.pi * 900 * t)  # lead-ish high
    right = 0.6 * np.sin(2 * np.pi * 180 * t)  # rhythm-ish low
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, left, right, sr)

    extra, diag = split_lead_rhythm_guitar(guitar, tmp_path, use_basic_pitch=False)
    assert diag.outcome == "lead_rhythm"
    assert "lead_guitar" in extra and "rhythm_guitar" in extra
    assert "guitar_split_diagnostics" in extra
    assert extra["guitar_split_diagnostics"].exists()
    assert guitar.exists()


def test_split_lead_rhythm_mono_skips_by_default(tmp_path: Path):
    """Mono guitar does not emit Lead/Rhythm in confident mode."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    mono = np.sin(2 * np.pi * 440 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, mono, mono, sr)
    extra, diag = split_lead_rhythm_guitar(guitar, tmp_path, use_basic_pitch=False)
    assert diag.outcome == "ambiguous"
    assert "lead_guitar" not in extra
    assert "rhythm_guitar" not in extra
    assert diag.forced_emit or diag.low_confidence
    assert "guitar_split_diagnostics" in extra
    assert guitar.exists()


def test_split_lead_rhythm_mono_emits_best_effort(tmp_path: Path):
    """Mono guitar still gets Lead/Rhythm WAVs when best_effort is requested."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    mono = np.sin(2 * np.pi * 440 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, mono, mono, sr)
    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path, use_basic_pitch=False, emit_mode="best_effort"
    )
    assert diag.outcome == "lead_rhythm"
    assert "lead_guitar" in extra and "rhythm_guitar" in extra
    assert diag.forced_emit or diag.low_confidence
    assert "guitar_split_diagnostics" in extra
    assert guitar.exists()


def test_split_prefers_spatial_over_spectral(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    left = np.sin(2 * np.pi * 900 * t)
    right = 0.6 * np.sin(2 * np.pi * 180 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, left, right, sr)
    _, diag = split_lead_rhythm_guitar(guitar, tmp_path, use_basic_pitch=False)
    assert diag.outcome == "lead_rhythm"
    assert diag.method == "spatial"


def test_spectral_emit_quarantined_falls_back_to_musical_pair(tmp_path: Path):
    """HPSS-only path must not be the emit source; fallback still emits Lead/Rhythm."""
    sr = 44100
    t = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
    mono = np.sin(2 * np.pi * 440 * t) + 0.5 * np.random.RandomState(0).randn(len(t))
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, mono.astype(np.float32), mono.astype(np.float32), sr)
    assert build_spatial_pair(guitar) is None

    thr = LeadRhythmThresholds(
        register_separability_floor=0.99,
        allow_spectral_emit=False,
    )
    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path, use_basic_pitch=False, thresholds=thr, emit_mode="best_effort"
    )
    assert "lead_guitar" in extra and "rhythm_guitar" in extra
    assert diag.outcome == "lead_rhythm"
    assert diag.method != "spectral" or thr.allow_spectral_emit
    assert diag.method in ("register", "midside", "spatial")


def test_spectral_long_tail_silence_pad(tmp_path: Path):
    """Spectral pad must not duplicate mono into both streams."""
    sr = 8000  # lower rate → shorter arrays for HPSS
    thr = LeadRhythmThresholds(analyze_window_sec=1.0)
    n = int(sr * 1.5)
    t = np.linspace(0, 1.5, n, endpoint=False)
    mono = (0.3 * np.sin(2 * np.pi * 440 * t)).astype(np.float32)
    # Strong energy only in the post-window tail.
    mono[:sr] *= 0.05
    mono[sr:] = 0.6 * np.sin(2 * np.pi * 880 * t[sr:])
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, mono, mono, sr)
    pair = build_spectral_pair(guitar, thresholds=thr)
    assert pair is not None
    assert len(pair.a) == n and len(pair.b) == n
    tail_a = pair.a[sr:]
    tail_b = pair.b[sr:]
    assert float(np.max(np.abs(tail_a))) < 1e-3
    assert float(np.max(np.abs(tail_b))) < 1e-3
    # Legacy bug would have correlated identical mono tails:
    assert not np.allclose(tail_a, mono[sr:] * 0.65, atol=1e-3)


def test_register_pair_builds_for_broadband(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    mono = (np.sin(2 * np.pi * 200 * t) + 0.5 * np.sin(2 * np.pi * 1200 * t)).astype(
        np.float32
    )
    path = tmp_path / "guitar.wav"
    _write_stereo(path, mono, mono, sr)
    pair = build_register_pair(path)
    assert pair is not None
    assert pair.method == "register"
    assert pair.separability >= 0.0


def test_resolve_lead_rhythm_mode_defaults_and_alias():
    from audio_to_tab.lead_rhythm import resolve_lead_rhythm_mode

    assert resolve_lead_rhythm_mode(None) == "confident"
    assert resolve_lead_rhythm_mode("confident") == "confident"
    assert resolve_lead_rhythm_mode("best_effort") == "best_effort"
    assert resolve_lead_rhythm_mode(None, lead_rhythm=True) == "best_effort"


def test_thresholds_from_env(monkeypatch):
    monkeypatch.setenv("ATT_LR_SEPARABILITY_FLOOR", "0.33")
    monkeypatch.setenv("ATT_LR_ALLOW_SPECTRAL_EMIT", "true")
    thr = LeadRhythmThresholds.from_env()
    assert thr.separability_floor == pytest.approx(0.33)
    assert thr.allow_spectral_emit is True


def test_classify_roles_respects_custom_margin_min():
    lead = RoleFeatures(70.0, 4.0, 2.5, 1.3, 90.0, 0.3)
    rhythm = RoleFeatures(55.0, 10.0, 5.0, 2.2, 70.0, 0.15)
    assignment, margin, detail = classify_lead_rhythm_roles(
        lead, rhythm, margin_min=0.99
    )
    assert assignment == "ambiguous"
    assert detail["margin_min"] == 0.99
    assert margin < 0.99


def test_spectral_pair_runs(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 1.5, int(sr * 1.5), endpoint=False)
    left = np.sin(2 * np.pi * 440 * t) + 0.3 * np.random.RandomState(0).randn(len(t))
    right = left.copy()
    path = tmp_path / "guitar.wav"
    _write_stereo(path, left, right, sr)
    pair = build_spectral_pair(path)
    assert pair is None or pair.method == "spectral"


def test_eval_scorer_aggregate_metrics():
    from eval.lead_rhythm.score_lead_rhythm import ClipResult, aggregate

    rows = [
        ClipResult("a", "hard_pan", 2, "left", "lead_rhythm", "spatial", True, True, 0.3, 0.5, "ok", 0.1),
        ClipResult("b", "mono_single", 1, None, "ambiguous", "none", False, None, None, None, "no", 0.1),
        ClipResult("c", "centered_overlap", 2, None, "ambiguous", "register", False, None, 0.1, 0.2, "low", 0.1),
        ClipResult("d", "hard_pan", 2, "left", "lead_rhythm", "spatial", True, False, 0.2, 0.4, "ok", 0.1),
    ]
    s = aggregate(rows)
    assert s["n"] == 4
    assert s["split_precision"] == pytest.approx(1.0)  # both emits are gt_parts=2
    assert s["split_recall"] == pytest.approx(2 / 3)
    assert s["ambiguous_rate_on_gt_le1"] == pytest.approx(1.0)
    assert s["label_correctness"] == pytest.approx(0.5)


def test_midside_pair_centered_lead_wide_rhythm(tmp_path: Path):
    """Centered lead (Mid) + wide-panned rhythm (Side) should admit midside."""
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    lead = np.sin(2 * np.pi * 880 * t)  # center
    rhythm = np.sin(2 * np.pi * 220 * t)  # wide L/R opposite
    left = 0.7 * lead + 0.55 * rhythm
    right = 0.7 * lead - 0.55 * rhythm
    path = tmp_path / "guitar.wav"
    _write_stereo(path, left, right, sr)
    pair = build_midside_pair(path)
    assert pair is not None
    assert pair.method == "midside"
    assert pair.balance_ratio is not None and pair.balance_ratio >= 0.04


def test_midside_pair_rejects_identical_mono(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    mono = np.sin(2 * np.pi * 440 * t)
    path = tmp_path / "guitar.wav"
    _write_stereo(path, mono, mono, sr)
    assert build_midside_pair(path) is None


def test_split_midside_centered_lead_wide_rhythm(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    lead = np.sin(2 * np.pi * 880 * t)
    rhythm = 0.6 * np.sin(2 * np.pi * 180 * t)
    left = 0.7 * lead + rhythm
    right = 0.7 * lead - rhythm
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, left, right, sr)
    # v2 picks the centered-vs-wide split (v1 split left/right sample by sample).
    # Both parts are plain single-note tones, so which one is "lead" is genuinely
    # unclear: confident mode keeps one Guitar stem and says so.
    extra_conf, diag_conf = split_lead_rhythm_guitar(
        guitar, tmp_path / "conf", use_basic_pitch=False, emit_mode="confident"
    )
    assert diag_conf.outcome == "ambiguous"
    assert diag_conf.method == "midside"
    assert diag_conf.reason_code == "unclear_roles"
    assert "lead_guitar" not in extra_conf

    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path / "be", use_basic_pitch=False, emit_mode="best_effort"
    )
    assert diag.outcome == "lead_rhythm"
    assert diag.method == "midside"
    lead_audio, _ = sf.read(str(extra["lead_guitar"]))
    rhythm_audio, _ = sf.read(str(extra["rhythm_guitar"]))
    # Default lead = the centered part; it stays centered. The wide part keeps
    # its width instead of being folded to mono.
    assert _dominant_hz(lead_audio.mean(axis=1), sr) == pytest.approx(880, abs=5)
    lead_side = 0.5 * (lead_audio[:, 0] - lead_audio[:, 1])
    lead_mid = 0.5 * (lead_audio[:, 0] + lead_audio[:, 1])
    assert np.sqrt(np.mean(lead_side**2)) < 0.03 * np.sqrt(np.mean(lead_mid**2))
    side = 0.5 * (rhythm_audio[:, 0] - rhythm_audio[:, 1])
    assert _dominant_hz(side, sr) == pytest.approx(180, abs=5)
    assert np.sqrt(np.mean(side**2)) > 0.3


def test_default_isolate_selected_stems_combined_guitar_only():
    from ui.isolate_state import custom_selected_stems

    selected = custom_selected_stems(
        ["vocals", "guitar", "lead_guitar", "rhythm_guitar"],
        ("guitar",),
    )
    assert selected["guitar"] is True
    assert selected["lead_guitar"] is False
    assert selected["rhythm_guitar"] is False
    assert selected["vocals"] is False


def test_si_sdr_prefers_matching_assignment(tmp_path: Path):
    """Eval scorer SI-SDR helpers: identical signals score high; swap still finds best pair."""
    from eval.lead_rhythm.score_lead_rhythm import _best_si_sdr_pair, _si_sdr

    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    lead = np.sin(2 * np.pi * 660 * t).astype(np.float32)
    rhythm = np.sin(2 * np.pi * 150 * t).astype(np.float32)
    assert _si_sdr(lead, lead) > 40.0
    # Direct assignment
    dl, dr = _best_si_sdr_pair(lead, rhythm, lead, rhythm)
    assert dl > 40.0 and dr > 40.0
    # Swapped estimates still recover via best-of-two
    sl, sr_ = _best_si_sdr_pair(rhythm, lead, lead, rhythm)
    assert sl > 40.0 and sr_ > 40.0


def test_make_synthetic_clips_writes_mild_pan(tmp_path: Path):
    from eval.lead_rhythm.make_synthetic_clips import mild_pan

    entry = mild_pan(tmp_path)
    assert entry["mix_type"] == "mild_pan"
    guitar = tmp_path / "mild_pan_example" / "guitar.wav"
    assert guitar.exists()
    assert (tmp_path / "mild_pan_example" / "gt_lead.wav").exists()
    assert (tmp_path / "mild_pan_example" / "gt_rhythm.wav").exists()


def test_isolate_default_stage1_model_is_htdemucs_6s():
    from audio_to_tab.isolate import IsolateConfig, SUPPORTED_MODELS
    from ui.isolate_state import DEFAULT_TRACK_OPTIONS, resolve_track_selection

    assert IsolateConfig().model == "htdemucs_6s"
    assert "htdemucs_6s" in SUPPORTED_MODELS
    default = resolve_track_selection(DEFAULT_TRACK_OPTIONS)
    assert default["model"] == "htdemucs_6s"
    assert default["emit_stems"] == ("vocals", "guitar")
    assert "piano" not in default["emit_stems"]


# --- v2 (REVIEW_AND_PLAN.md LR-1 / LR-2 / LR-3) -----------------------------------


def test_stft_mask_render_reconstructs_across_blocks():
    from audio_to_tab.lead_rhythm import stft_mask_render

    sr = 8000
    rng = np.random.RandomState(0)
    x = (0.3 * rng.randn(sr * 5, 2)).astype(np.float32)

    def half(spec_l, _spec_r, _freqs):
        return np.full(spec_l.shape, 0.3)

    a, b = stft_mask_render(x, sr, half, block_sec=1.0, overlap_sec=0.25)
    assert a.shape == x.shape and b.shape == x.shape
    assert np.max(np.abs((a + b) - x)) < 1e-3
    assert np.max(np.abs(a - 0.3 * x)) < 1e-3


def test_spatial_split_keeps_stereo_and_full_length(tmp_path: Path):
    """Hard-panned parts: stems keep their side (v1 folded them to mono) and run to the end."""
    sr = 22050
    t = np.arange(int(sr * 12)) / sr
    rhythm = 0.4 * np.sin(2 * np.pi * 220 * t)
    lead = 0.4 * np.sin(2 * np.pi * 880 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, rhythm, lead, sr)
    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path / "out", use_basic_pitch=False, emit_mode="best_effort"
    )
    assert diag.method == "spatial"
    a, _ = sf.read(str(extra["lead_guitar"]))
    b, _ = sf.read(str(extra["rhythm_guitar"]))
    assert len(a) == len(t) and len(b) == len(t)
    for stem in (a, b):
        louder = int(np.argmax(np.sqrt(np.mean(stem**2, axis=0))))
        quieter = 1 - louder
        assert np.sqrt(np.mean(stem[:, quieter] ** 2)) < 0.1 * np.sqrt(np.mean(stem[:, louder] ** 2))
        assert np.sqrt(np.mean(stem[-sr:] ** 2)) > 0.05  # not silent at the end


def test_register_pair_renders_whole_song(tmp_path: Path):
    """v1 rendered only the analysis window and padded silence (stems went quiet after 90 s)."""
    sr = 8000
    thr = LeadRhythmThresholds(analyze_window_sec=1.0)
    t = np.arange(int(sr * 4)) / sr
    mono = (0.3 * np.sin(2 * np.pi * 150 * t) + 0.3 * np.sin(2 * np.pi * 1500 * t)).astype(np.float32)
    path = tmp_path / "guitar.wav"
    _write_stereo(path, mono, mono, sr)
    pair = build_register_pair(path, thresholds=thr)
    assert pair is not None
    a_full, b_full = pair.full_stereo()  # analysis uses a window; output is the whole song
    assert len(a_full) == len(t)
    tail = slice(3 * sr, 4 * sr)
    assert np.sqrt(np.mean(a_full[tail] ** 2)) > 0.1
    assert np.sqrt(np.mean(b_full[tail] ** 2)) > 0.1


def _write_role_switch(tmp_path: Path, layout):
    from eval.lead_rhythm.make_synthetic_clips import SR, role_switch_song

    guitar_m, vocals, lead, rhythm = role_switch_song(layout)
    guitar = tmp_path / "guitar.wav"
    vocals_path = tmp_path / "vocals.wav"
    _write_stereo(guitar, guitar_m, guitar_m, SR)
    sf.write(str(vocals_path), vocals, SR)
    return guitar, vocals_path, lead, rhythm, SR


def test_temporal_split_one_guitar_rhythm_then_solo(tmp_path: Path):
    """One centered track: verse strumming → solo (vocals stop) → verse.

    Quality is judged against the known parts: SI-SDR of each stem vs its ground
    truth, the solo boundaries within ~1 s, and Lead + Rhythm == Guitar.
    """
    guitar, vocals, gt_lead, gt_rhythm, sr = _write_role_switch(
        tmp_path, [("chords", 20), ("solo", 15), ("chords", 20)]
    )
    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path / "out", use_basic_pitch=False, vocals_path=vocals
    )
    assert diag.outcome == "lead_rhythm"
    assert diag.method == "temporal"
    assert diag.reason_code == "split"
    lead_segs = [s for s in diag.features["temporal"]["segments"] if s["role"] == "lead"]
    assert len(lead_segs) == 1
    assert lead_segs[0]["start"] == pytest.approx(20.0, abs=1.0)
    assert lead_segs[0]["end"] == pytest.approx(35.0, abs=1.0)
    lead, _ = sf.read(str(extra["lead_guitar"]))
    rhythm, _ = sf.read(str(extra["rhythm_guitar"]))
    src, _ = sf.read(str(guitar))
    assert _si_sdr(lead[:, 0], gt_lead) > 15.0
    assert _si_sdr(rhythm[:, 0], gt_rhythm) > 15.0
    assert np.max(np.abs(lead + rhythm - src)) < 2e-3
    assert "Lead found at 0:2" in diag.user_message


@pytest.mark.parametrize("mode", ["confident", "prefer_split"])
def test_temporal_refuses_single_rhythm_part(tmp_path: Path, mode: str):
    """Only strumming (with vocals): one part, so even prefer_split keeps one Guitar."""
    guitar, vocals, _, _, _ = _write_role_switch(tmp_path, [("chords", 40)])
    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path / "out", use_basic_pitch=False, vocals_path=vocals, emit_mode=mode
    )
    assert "lead_guitar" not in extra
    assert diag.outcome == "ambiguous"
    assert diag.features["temporal"]["confident"] is False
    assert "one Guitar track" in diag.user_message


def _centered_lead_wide_rhythm(tmp_path: Path) -> tuple[Path, int]:
    sr = 44100
    t = np.linspace(0, 2.0, sr * 2, endpoint=False)
    lead = np.sin(2 * np.pi * 880 * t)
    rhythm = 0.6 * np.sin(2 * np.pi * 180 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, 0.7 * lead + rhythm, 0.7 * lead - rhythm, sr)
    return guitar, sr


def test_prefer_split_emits_two_parts_when_labels_unsure(tmp_path: Path):
    """The person's report: two guitars found, roles unclear → confident merged them.

    prefer_split (what the app uses when the box is ticked) splits anyway, flags
    the labels as a best guess, and still puts the centered part in Lead.
    """
    guitar, sr = _centered_lead_wide_rhythm(tmp_path)
    _, conf = split_lead_rhythm_guitar(guitar, tmp_path / "c", use_basic_pitch=False)
    assert conf.reason_code == "unclear_roles"

    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path / "p", use_basic_pitch=False, emit_mode="prefer_split"
    )
    assert diag.outcome == "lead_rhythm"
    assert diag.reason_code == "split_labels_unsure"
    assert diag.features["two_parts_found"] is True
    assert "best guess" in diag.user_message and "Swap" in diag.user_message
    lead_audio, _ = sf.read(str(extra["lead_guitar"]))
    assert _dominant_hz(lead_audio.mean(axis=1), sr) == pytest.approx(880, abs=5)


def test_prefer_split_keeps_mono_single_part(tmp_path: Path):
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    mono = np.sin(2 * np.pi * 440 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, mono, mono, sr)
    extra, diag = split_lead_rhythm_guitar(
        guitar, tmp_path / "out", use_basic_pitch=False, emit_mode="prefer_split"
    )
    assert "lead_guitar" not in extra
    assert diag.outcome == "ambiguous"


def test_resolve_mode_accepts_prefer_split():
    from audio_to_tab.lead_rhythm import resolve_lead_rhythm_mode

    assert resolve_lead_rhythm_mode("prefer_split") == "prefer_split"
    with pytest.raises(ValueError):
        resolve_lead_rhythm_mode("sometimes")


def test_swap_lead_rhythm_stems(tmp_path: Path):
    import json

    from ui.guitar_fixup import swap_lead_rhythm_stems

    sr = 8000
    t = np.arange(sr) / sr
    lead = tmp_path / "lead_guitar.wav"
    rhythm = tmp_path / "rhythm_guitar.wav"
    _write_stereo(lead, np.sin(2 * np.pi * 880 * t), np.sin(2 * np.pi * 880 * t), sr)
    _write_stereo(rhythm, np.sin(2 * np.pi * 220 * t), np.sin(2 * np.pi * 220 * t), sr)
    (tmp_path / "guitar_split_diagnostics.json").write_text(
        json.dumps({"outcome": "lead_rhythm", "features": {}}), encoding="utf-8"
    )
    result = swap_lead_rhythm_stems(
        stem_paths={"lead_guitar": lead, "rhythm_guitar": rhythm}, run_dir=tmp_path
    )
    assert result.ok
    new_lead, _ = sf.read(str(lead))
    assert _dominant_hz(new_lead[:, 0], sr) == pytest.approx(220, abs=5)
    diag = json.loads((tmp_path / "guitar_split_diagnostics.json").read_text(encoding="utf-8"))
    assert diag["features"]["labels_swapped"] is True
    assert not list(tmp_path.glob("*.swap-tmp.wav"))
    assert not swap_lead_rhythm_stems(stem_paths={}, run_dir=tmp_path).ok


def test_near_silent_guitar_is_skipped(tmp_path: Path):
    sr = 22050
    t = np.arange(sr * 3) / sr
    quiet = 1e-4 * np.sin(2 * np.pi * 220 * t)
    guitar = tmp_path / "guitar.wav"
    _write_stereo(guitar, quiet, quiet, sr)
    extra, diag = split_lead_rhythm_guitar(guitar, tmp_path / "out", use_basic_pitch=False)
    assert "lead_guitar" not in extra
    assert diag.outcome == "skipped"
    assert diag.reason_code == "not_present"
    assert "almost silent" in diag.user_message


def test_missing_guitar_message(tmp_path: Path):
    extra, diag = split_lead_rhythm_guitar(tmp_path / "nope.wav", tmp_path, use_basic_pitch=False)
    assert diag.reason_code == "missing"
    data = (tmp_path / "guitar_split_diagnostics.json").read_text(encoding="utf-8")
    assert "nothing to split" in data


def test_user_message_for_every_code():
    from audio_to_tab.lead_rhythm import REASON_CODES, user_message_for

    for code in REASON_CODES:
        assert user_message_for(code, method="spatial").strip()
    msg = user_message_for(
        "split",
        method="temporal",
        features={
            "simultaneous_method": "midside",
            "temporal": {"segments": [{"start": 72, "end": 100, "role": "lead"}]},
        },
    )
    assert "when each part plays" in msg and "centered" in msg and "1:12–1:40" in msg
    assert "best guess" in user_message_for("split_low_confidence", method="register")


# --- Desktop wiring (LR-3 / LR-4 / FB-1) ------------------------------------------


def test_lead_rhythm_supported_for_any_engine_with_a_guitar_stem():
    from ui.isolate_state import lead_rhythm_supported

    assert lead_rhythm_supported("htdemucs_6s")
    assert lead_rhythm_supported("bs_roformer_sw")
    assert lead_rhythm_supported("htdemucs_6s", emit_stems=("vocals", "guitar"))
    assert not lead_rhythm_supported("htdemucs")  # 4-stem: no guitar stem
    assert not lead_rhythm_supported("htdemucs_6s", two_stems="vocals")
    assert not lead_rhythm_supported("htdemucs_6s", emit_stems=("vocals", "drums"))


def test_engine_fields_lead_rhythm_is_opt_in_in_lite_and_pro():
    from ui.isolate_state import resolve_pro_engine_job_fields

    kwargs = dict(
        model="htdemucs_6s",
        quality="fast",
        two_stems=None,
        two_pass=False,
        fold_other_into_guitar=True,
        fold_other_mode="best_effort",
    )
    for pro in (False, True):
        assert resolve_pro_engine_job_fields({}, is_pro=pro, **kwargs)["lead_rhythm"] is False
        on = resolve_pro_engine_job_fields({"isolate_lead_rhythm": True}, is_pro=pro, **kwargs)
        assert on["lead_rhythm"] is True
        # Ticking the box = the person wants Lead and Rhythm.
        assert on["lead_rhythm_mode"] == "prefer_split"
    blocked = resolve_pro_engine_job_fields(
        {"isolate_lead_rhythm": True}, is_pro=True, lead_rhythm_allowed=False, **kwargs
    )
    assert blocked["lead_rhythm"] is False


def test_mixer_shows_pair_or_combined_never_both():
    from ui.isolate_state import (
        LEAD_RHYTHM_VIEW_COMBINED,
        LEAD_RHYTHM_VIEW_SPLIT,
        mixer_stems_for_view,
    )

    stems = {"vocals": 1, "guitar": 2, "lead_guitar": 3, "rhythm_guitar": 4}
    assert set(mixer_stems_for_view(stems, LEAD_RHYTHM_VIEW_SPLIT)) == {
        "vocals",
        "lead_guitar",
        "rhythm_guitar",
    }
    assert set(mixer_stems_for_view(stems, None)) == {"vocals", "lead_guitar", "rhythm_guitar"}
    assert set(mixer_stems_for_view(stems, LEAD_RHYTHM_VIEW_COMBINED)) == {"vocals", "guitar"}
    plain = {"vocals": 1, "guitar": 2}
    assert mixer_stems_for_view(plain, LEAD_RHYTHM_VIEW_SPLIT) == plain


def test_guitar_split_notice_levels_and_v1_diagnostics():
    from ui.isolate_state import guitar_split_notice

    assert guitar_split_notice({}) is None
    ok = guitar_split_notice({"outcome": "lead_rhythm", "method": "temporal", "reason_code": "split", "user_message": "Split."})
    assert ok["level"] == "success" and ok["split"] and ok["text"] == "Split."
    # v1 file: no reason_code / user_message → mapped, still plain language.
    old_refused = guitar_split_notice({"outcome": "ambiguous", "method": "midside", "forced_emit": True})
    assert old_refused["level"] == "info" and "one Guitar track" in old_refused["text"]
    old_forced = guitar_split_notice({"outcome": "lead_rhythm", "method": "register", "forced_emit": True})
    assert old_forced["level"] == "warning" and old_forced["low_confidence"]


def test_split_finished_song_records_artifacts(tmp_path: Path):
    """Post-hoc 'Split guitar' on a finished run: new stems land in meta.json."""
    import json

    from eval.lead_rhythm.make_synthetic_clips import SR, role_switch_song
    from ui.guitar_fixup import split_mixer_guitar_lead_rhythm

    guitar_m, vocals, _, _ = role_switch_song([("chords", 20), ("solo", 15), ("chords", 20)])
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    guitar = run_dir / "guitar.wav"
    vocals_path = run_dir / "vocals.wav"
    _write_stereo(guitar, guitar_m, guitar_m, SR)
    sf.write(str(vocals_path), vocals, SR)
    (run_dir / "meta.json").write_text(
        json.dumps({"page": "isolate", "title": "t", "artifacts": {"guitar": str(guitar)}}),
        encoding="utf-8",
    )
    result = split_mixer_guitar_lead_rhythm(
        stem_paths={"guitar": guitar, "vocals": vocals_path}, run_dir=run_dir
    )
    assert result.ok
    assert "Lead and Rhythm" in result.message
    meta = json.loads((run_dir / "meta.json").read_text(encoding="utf-8"))
    assert {"guitar", "lead_guitar", "rhythm_guitar", "guitar_split_diagnostics"} <= set(
        meta["artifacts"]
    )
    assert meta["title"] == "t"
    assert guitar.exists()


def test_split_finished_song_without_guitar(tmp_path: Path):
    from ui.guitar_fixup import split_mixer_guitar_lead_rhythm

    result = split_mixer_guitar_lead_rhythm(stem_paths={}, run_dir=tmp_path)
    assert not result.ok and "no Guitar track" in result.message


def test_guitar_weights_fallback_diagnostics(tmp_path: Path):
    import json

    from audio_to_tab.isolate import write_guitar_weights_diagnostics

    path = write_guitar_weights_diagnostics(
        tmp_path, requested="htdemucs_6s_guitar_ft", reason="RuntimeError: no weights"
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["fallback"] is True and data["used"] == "htdemucs_6s"
    assert "standard" in data["user_message"]
