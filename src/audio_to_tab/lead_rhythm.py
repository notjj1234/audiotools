"""Lead vs Rhythm guitar post-process for Demucs guitar stems.

Spatial + register (STFT band) candidates, then Basic Pitch role features with a
confidence gate. HPSS spectral pairs are kept for diagnostics only and never
emitted as Lead/Rhythm. Emits lead_guitar / rhythm_guitar only when confident;
always keeps the original guitar stem when attempted.

Root cause (2026-07-17): most real two-guitar mixes are not hard-panned to
opposite channels (that is a stylistic choice, not the norm), yet
``build_spatial_pair``'s admission gate was a single raw L/R sample-correlation
ceiling (``SPATIAL_CORR_MAX``). Raw correlation of a stereo mix of two
*independent* sources panned with coefficients (p, 1-p) is ``2p(1-p) /
(p^2 + (1-p)^2)`` — it rises toward 1.0 as panning approaches center
*regardless of how different the underlying content is* (e.g. two fully
independent tones panned 55/45 already correlate ~0.98). So the old gate
conflated "one guitar duplicated identically into both channels" (corr -> 1.0,
truly inseparable) with "two genuinely distinct guitars mixed with mild/no hard
panning" (corr can also land at 0.92-0.99, but the channels are NOT identical).
Everything short of hard panning was rejected before role classification ever
ran, matching the eval README's documented ambiguous cases.

Published solo/accompaniment guitar research (Foulon et al. 2013, "Automatic
Classification of Guitar Playing Modes"; Pati & Lerch 2017, "A Dataset and
Method for Electric Guitar Solo Detection in Rock Music") shows that
predominant-pitch strength/confidence, computed directly on a signal, reliably
discriminates a foregrounded melodic (lead) voice from denser/chordal
(rhythm) material *without first splitting the audio into two streams* via
panning or spectral means. That evidence is independent of how the mix is
panned, so it can rescue exactly the high-correlation-but-genuinely-distinct
case above: ``build_spatial_pair`` now allows a higher correlation ceiling
(``SPATIAL_CORR_RELAXED_MAX``) only when each channel's dominant spectral peak
("predominant pitch" proxy; no split required) diverges by at least
``PITCH_DIVERGENCE_SEMITONES_MIN`` semitones and at least one channel has a
clear-enough peak (``PITCH_CONFIDENCE_MIN``). Identical/near-identical channels
(mono duplicated into both) always show zero divergence, so they remain
rejected — the existing "prefer ambiguous over wrong" guarantee is unchanged:
this only widens *evidence* for admitting a candidate pair, the separability
floor and role-margin gates downstream still decide whether to actually emit.
No new dependency was added: the peak-picking helper is plain FFT (same style
as ``score_candidate_pair`` / ``_spectral_centroid_hz`` already in this file).
True same-register, fully-simultaneous, dead-centered (identical L=R) overlap
of two guitars remains architecturally unsolvable without a trained source
separator — that case correctly stays ``ambiguous`` (out of scope here; adding
such a model was explicitly excluded).

v2 (2026-11-24, REVIEW_AND_PLAN.md LR-1/LR-2):

- Every emitted stem is **stereo** and covers the **whole song**. Candidate
  streams are rendered with STFT masks in 30 s blocks (bounded RAM), never by
  per-sample L/R switching (which distorted hard-panned parts) and never by
  padding a 90 s analysis window with silence.
- Spatial = per-bin pan-index mask; Mid/Side = per-bin "centered and in phase"
  mask applied to both channels (the rhythm keeps its width).
- New **temporal** method: short windows are scored lead-like or rhythm-like
  from predominant-pitch confidence (pYIN), pitch-class concentration, register,
  pitch movement (bends/vibrato) and vocal silence (from the vocal stem), then
  smoothed into sections. Lead = guitar during lead sections, Rhythm = the rest,
  so Lead + Rhythm sums back to the guitar stem. When a confident simultaneous
  (spatial / mid-side) split exists, it is used inside lead sections.
- Near-silent guitar stems are skipped. Every outcome carries a ``reason_code``
  and a plain ``user_message`` the UI shows when the guitar is kept whole.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any, Literal

import numpy as np
import soundfile as sf

Outcome = Literal["lead_rhythm", "ambiguous", "skipped"]
Method = Literal["spatial", "midside", "register", "spectral", "temporal", "none"]
# confident:    emit only when every gate passes.
# prefer_split: what the app uses when the person ticks "Split lead and rhythm":
#               emit whenever two distinct parts were found, even if which one is
#               the lead is a best guess (flagged, and swappable in the mixer).
#               Still keeps one Guitar when there is only one part.
# best_effort:  always emit something (eval / legacy ``dual_guitar``).
EmitMode = Literal["confident", "prefer_split", "best_effort"]
EMIT_MODES = ("confident", "prefer_split", "best_effort")


def resolve_lead_rhythm_mode(
    lead_rhythm_mode: str | None = None,
    *,
    lead_rhythm: bool = False,
) -> EmitMode:
    """Map API/UI flags to emit policy. Default is confident-only emit."""
    if lead_rhythm_mode is not None and str(lead_rhythm_mode).strip():
        mode = str(lead_rhythm_mode).strip().lower()
        if mode not in EMIT_MODES:
            raise ValueError(
                f"lead_rhythm_mode must be one of {', '.join(EMIT_MODES)}, got {lead_rhythm_mode!r}"
            )
        return mode  # type: ignore[return-value]
    if lead_rhythm:
        return "best_effort"
    return "confident"

SEPARABILITY_FLOOR = 0.22
ROLE_MARGIN_MIN = 0.18
# HPSS harmonic/residual is not musically Lead/Rhythm; spectral pairs are
# diagnostics-only (never emitted) unless allow_spectral_emit is explicitly on.
SPECTRAL_SEPARABILITY_FLOOR = 0.55
SPECTRAL_ROLE_MARGIN_MIN = 0.28
REGISTER_SEPARABILITY_FLOOR = 0.28
MIDSIDE_SEPARABILITY_FLOOR = 0.22
ANALYZE_WINDOW_SEC = 90.0
SPATIAL_BALANCE_MIN = 0.12
SPATIAL_CORR_MAX = 0.92
REGISTER_CROSSOVER_HZ = 400.0
# Side channel must carry some energy vs Mid (rejects true mono / L≡R).
MIDSIDE_SIDE_RATIO_MIN = 0.04

# Pitch-divergence evidence (spatial-split-independent) that can rescue a
# mildly-panned-but-genuinely-distinct pair above SPATIAL_CORR_MAX — see the
# module docstring "Root cause" note. Never overrides SPATIAL_CORR_RELAXED_MAX,
# so identical/near-identical channels (mono duplicated) are still rejected.
SPATIAL_CORR_RELAXED_MAX = 0.985
PITCH_DIVERGENCE_SEMITONES_MIN = 3.0
PITCH_CONFIDENCE_MIN = 0.08
PITCH_PROXY_FMIN_HZ = 70.0
PITCH_PROXY_FMAX_HZ = 1500.0

# Below this mean level the guitar stem is treated as absent (no split attempt).
GUITAR_PRESENT_DBFS_MIN = -50.0
# Pan-index clusters closer than this carry no usable left/right evidence.
SPATIAL_PAN_SPREAD_MIN = 0.05
# Width of the pan-index sigmoid as a fraction of the cluster spread.
SPATIAL_SOFTNESS_FRACTION = 0.1
# STFT render settings (blocks bound RAM on long songs).
RENDER_N_FFT = 2048
RENDER_HOP = 512
RENDER_BLOCK_SEC = 30.0
RENDER_OVERLAP_SEC = 1.0
# A rendered stream quieter than this vs the source counts as empty.
STREAM_EMPTY_RATIO = 0.02

# Temporal (who-plays-when) segmentation.
TEMPORAL_ANALYSIS_SR = 11025
# pYIN frame hop at 11 kHz (~93 ms). pYIN dominates the split's run time; 2 s
# windows still get ~21 frames and boundaries are refined at this resolution.
TEMPORAL_ANALYSIS_HOP = 1024
TEMPORAL_WIN_SEC = 2.0
TEMPORAL_HOP_SEC = 1.0
TEMPORAL_SMOOTH_WINDOWS = 5
TEMPORAL_MIN_SEGMENT_SEC = 4.0
TEMPORAL_FADE_SEC = 0.15
TEMPORAL_MIN_ROLE_SEC = 6.0
TEMPORAL_MIN_ROLE_SHARE = 0.05
# Between-cluster share of lead-score variance (1D 2-means). A single
# Gaussian gives ~0.64, so this asks for genuinely two-sided material.
TEMPORAL_R2_MIN = 0.7
# Lead sections must sound clearly more single-voiced than rhythm sections.
TEMPORAL_LEAD_VOICED_MIN = 0.3
TEMPORAL_VOICED_GAP_MIN = 0.08
TEMPORAL_ACTIVE_DB = -35.0


@dataclass
class LeadRhythmThresholds:
    """Tunable gates for eval/CLI ablation (defaults match module constants)."""

    separability_floor: float = SEPARABILITY_FLOOR
    role_margin_min: float = ROLE_MARGIN_MIN
    spectral_separability_floor: float = SPECTRAL_SEPARABILITY_FLOOR
    spectral_role_margin_min: float = SPECTRAL_ROLE_MARGIN_MIN
    register_separability_floor: float = REGISTER_SEPARABILITY_FLOOR
    midside_separability_floor: float = MIDSIDE_SEPARABILITY_FLOOR
    midside_side_ratio_min: float = MIDSIDE_SIDE_RATIO_MIN
    analyze_window_sec: float = ANALYZE_WINDOW_SEC
    # Spectral emit quarantined by default (HPSS ≠ Lead/Rhythm).
    allow_spectral_emit: bool = False
    spatial_balance_min: float = SPATIAL_BALANCE_MIN
    spatial_corr_max: float = SPATIAL_CORR_MAX
    spatial_corr_relaxed_max: float = SPATIAL_CORR_RELAXED_MAX
    pitch_divergence_semitones_min: float = PITCH_DIVERGENCE_SEMITONES_MIN
    pitch_confidence_min: float = PITCH_CONFIDENCE_MIN
    guitar_present_dbfs_min: float = GUITAR_PRESENT_DBFS_MIN
    temporal_enabled: bool = True
    temporal_r2_min: float = TEMPORAL_R2_MIN
    temporal_min_role_sec: float = TEMPORAL_MIN_ROLE_SEC
    temporal_min_role_share: float = TEMPORAL_MIN_ROLE_SHARE

    @classmethod
    def from_env(cls, base: LeadRhythmThresholds | None = None) -> LeadRhythmThresholds:
        """Overlay ATT_LR_* environment variables onto defaults or ``base``."""
        t = base or cls()
        mapping = {
            "ATT_LR_SEPARABILITY_FLOOR": ("separability_floor", float),
            "ATT_LR_ROLE_MARGIN_MIN": ("role_margin_min", float),
            "ATT_LR_SPECTRAL_SEPARABILITY_FLOOR": ("spectral_separability_floor", float),
            "ATT_LR_SPECTRAL_ROLE_MARGIN_MIN": ("spectral_role_margin_min", float),
            "ATT_LR_REGISTER_SEPARABILITY_FLOOR": ("register_separability_floor", float),
            "ATT_LR_MIDSIDE_SEPARABILITY_FLOOR": ("midside_separability_floor", float),
            "ATT_LR_MIDSIDE_SIDE_RATIO_MIN": ("midside_side_ratio_min", float),
            "ATT_LR_ANALYZE_WINDOW_SEC": ("analyze_window_sec", float),
            "ATT_LR_ALLOW_SPECTRAL_EMIT": ("allow_spectral_emit", _env_bool),
            "ATT_LR_SPATIAL_CORR_RELAXED_MAX": ("spatial_corr_relaxed_max", float),
            "ATT_LR_PITCH_DIVERGENCE_SEMITONES_MIN": (
                "pitch_divergence_semitones_min",
                float,
            ),
            "ATT_LR_PITCH_CONFIDENCE_MIN": ("pitch_confidence_min", float),
            "ATT_LR_GUITAR_PRESENT_DBFS_MIN": ("guitar_present_dbfs_min", float),
            "ATT_LR_TEMPORAL_ENABLED": ("temporal_enabled", _env_bool),
            "ATT_LR_TEMPORAL_R2_MIN": ("temporal_r2_min", float),
            "ATT_LR_TEMPORAL_MIN_ROLE_SEC": ("temporal_min_role_sec", float),
        }
        updates: dict[str, Any] = {}
        for env_key, (field_name, caster) in mapping.items():
            raw = os.environ.get(env_key)
            if raw is None or raw == "":
                continue
            updates[field_name] = caster(raw)
        return replace(t, **updates) if updates else t


def _env_bool(raw: str) -> bool:
    return raw.strip().lower() in ("1", "true", "yes", "on")


@dataclass
class LeadRhythmDiagnostics:
    """Diagnostics for an attempted lead/rhythm split."""

    outcome: Outcome
    reason: str
    attempted: bool = True
    separability_score: float | None = None
    role_confidence: float | None = None
    method: Method = "none"
    correlation: float | None = None
    balance_ratio: float | None = None
    # True when Lead/Rhythm WAVs were written despite failed gates (best-effort).
    forced_emit: bool = False
    low_confidence: bool = False
    features: dict[str, Any] = field(default_factory=dict)
    # Short machine code + plain sentence for the mixer (see user_message_for).
    reason_code: str = ""
    user_message: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def write_json(self, path: Path) -> Path:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        if not self.reason_code:
            self.reason_code = _infer_reason_code(self)
        if not self.user_message:
            self.user_message = user_message_for(
                self.reason_code,
                method=self.method,
                features=self.features,
            )
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        return path


REASON_CODES = (
    "missing",
    "not_present",
    "too_short",
    "one_part",
    "overlap",
    "unclear_roles",
    "split",
    "split_low_confidence",
    "split_labels_unsure",
)
SPLIT_REASON_CODES = frozenset({"split", "split_low_confidence", "split_labels_unsure"})

_METHOD_PHRASE = {
    "temporal": "when each part plays",
    "spatial": "where each guitar sits left and right in the mix",
    "midside": "centered versus wide placement in the mix",
    "register": "high versus low range",
    "spectral": "tone (experimental)",
}


def _format_mmss(seconds: float) -> str:
    seconds = max(0, round(float(seconds)))
    return f"{seconds // 60}:{seconds % 60:02d}"


def lead_section_summary(features: dict[str, Any] | None, *, limit: int = 3) -> str:
    """'1:12–1:40, 3:05–3:30' for temporal splits; empty otherwise."""
    temporal = (features or {}).get("temporal") or {}
    spans = [
        s for s in temporal.get("segments", []) if isinstance(s, dict) and s.get("role") == "lead"
    ]
    parts = [f"{_format_mmss(s['start'])}–{_format_mmss(s['end'])}" for s in spans[:limit]]
    if len(spans) > limit:
        parts.append(f"+{len(spans) - limit} more")
    return ", ".join(parts)


def user_message_for(
    reason_code: str,
    *,
    method: str = "none",
    features: dict[str, Any] | None = None,
) -> str:
    """Plain-language sentence shown in the mixer for a split outcome."""
    if reason_code == "missing":
        return "No guitar track was made for this song, so there was nothing to split."
    if reason_code == "not_present":
        return "The guitar track is almost silent, so it was kept as one Guitar track."
    if reason_code == "too_short":
        return "The guitar part is too short to tell lead from rhythm, so it was kept as one Guitar track."
    if reason_code == "one_part":
        return "Only one guitar part was found, so it was kept as one Guitar track."
    if reason_code == "unclear_roles":
        return (
            "Two guitar parts were found, but it wasn't clear which one is the lead, "
            "so they were kept together as one Guitar track."
        )
    if reason_code == "overlap":
        return (
            "The guitar parts play together in the same place in the mix, so they "
            "couldn't be pulled apart cleanly. Kept as one Guitar track."
        )
    phrase = _METHOD_PHRASE.get(str(method), "the guitar's playing style")
    simultaneous = (features or {}).get("simultaneous_method")
    if method == "temporal" and simultaneous in _METHOD_PHRASE:
        phrase = f"{phrase} and {_METHOD_PHRASE[simultaneous]}"
    sections = lead_section_summary(features)
    where = f" Lead found at {sections}." if sections else ""
    if reason_code == "split_labels_unsure":
        return (
            f"Two guitar parts were found and split (by {phrase}). It wasn't certain "
            "which one is the lead, so the labels are a best guess: use Swap if "
            f"they're the wrong way round.{where}"
        )
    if reason_code == "split_low_confidence":
        return (
            f"Split into Lead and Rhythm as a best guess (by {phrase}); the labels may "
            f"be wrong.{where}"
        )
    return f"Split into Lead and Rhythm by {phrase}.{where}"


def infer_reason_code(
    outcome: str,
    method: str,
    *,
    forced_emit: bool = False,
    low_confidence: bool = False,
) -> str:
    """Reason code for diagnostics written before ``reason_code`` existed."""
    if outcome == "lead_rhythm":
        return "split_low_confidence" if (forced_emit or low_confidence) else "split"
    if outcome == "skipped":
        return "missing"
    if method in ("spatial", "midside"):
        return "overlap"
    return "one_part"


def _infer_reason_code(diag: LeadRhythmDiagnostics) -> str:
    return infer_reason_code(
        diag.outcome,
        diag.method,
        forced_emit=diag.forced_emit,
        low_confidence=diag.low_confidence,
    )


@dataclass
class _CandidatePair:
    method: Method
    a: np.ndarray  # mono float32
    b: np.ndarray
    sr: int
    separability: float
    correlation: float | None = None
    balance_ratio: float | None = None
    detail: str = ""
    pitch_evidence: dict[str, float] | None = None
    # Full-length (n, 2) renders written as the stems; a/b above are analysis
    # monos (first analyze window). ``render`` produces the full-length pair on
    # demand, so only the chosen candidate is rendered for the whole song.
    a_stereo: np.ndarray | None = None
    b_stereo: np.ndarray | None = None
    render: Any = None

    def full_stereo(self) -> tuple[np.ndarray, np.ndarray]:
        if self.render is not None:
            self.a_stereo, self.b_stereo = self.render()
            self.render = None
        a = self.a_stereo if self.a_stereo is not None else _mono_to_stereo(self.a)
        b = self.b_stereo if self.b_stereo is not None else _mono_to_stereo(self.b)
        return np.asarray(a, dtype=np.float32), np.asarray(b, dtype=np.float32)


def _analysis_window(data: np.ndarray, sr: int, thr: LeadRhythmThresholds) -> np.ndarray:
    return data[: max(int(thr.analyze_window_sec * sr), 1024)]


def _stereo_analysis_mono(stereo: np.ndarray) -> np.ndarray:
    """Mono view for scoring: Mid, or Side when the stream is mostly out of phase."""
    st = np.asarray(stereo, dtype=np.float32)
    mid = (st[:, 0] + st[:, 1]) * 0.5
    side = (st[:, 0] - st[:, 1]) * 0.5
    return (mid if _rms(mid) >= _rms(side) else side).astype(np.float32)


def stft_mask_render(
    stereo: np.ndarray,
    sr: int,
    mask_fn: Any,
    *,
    n_fft: int = RENDER_N_FFT,
    hop: int = RENDER_HOP,
    block_sec: float = RENDER_BLOCK_SEC,
    overlap_sec: float = RENDER_OVERLAP_SEC,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Split a stereo signal into two stereo streams with a soft STFT mask.

    ``mask_fn(spec_left, spec_right, freqs) -> mask_a`` (values in [0, 1]). The
    same mask is applied to both channels, so each stream keeps its stereo
    placement, and ``a + b`` reconstructs the input. Processed in overlapping
    blocks with linear crossfades so long songs never hold a full-song STFT.
    """
    import librosa

    st = np.asarray(stereo, dtype=np.float32)
    n = len(st)
    out_a = np.zeros((n, 2), dtype=np.float32)
    out_b = np.zeros((n, 2), dtype=np.float32)
    weight = np.zeros(n, dtype=np.float32)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    block = max(int(block_sec * sr), n_fft * 4)
    ov = max(int(overlap_sec * sr), hop * 2)
    start = 0
    while start < n:
        end = min(n, start + block + ov)
        seg = st[start:end]
        seg_len = len(seg)
        if seg_len < n_fft:
            seg = np.pad(seg, ((0, n_fft - seg_len), (0, 0)))
        spec_l = librosa.stft(seg[:, 0], n_fft=n_fft, hop_length=hop)
        spec_r = librosa.stft(seg[:, 1], n_fft=n_fft, hop_length=hop)
        mask = np.clip(np.asarray(mask_fn(spec_l, spec_r, freqs), dtype=np.float32), 0.0, 1.0)
        a_l = librosa.istft(spec_l * mask, hop_length=hop, length=len(seg))[:seg_len]
        a_r = librosa.istft(spec_r * mask, hop_length=hop, length=len(seg))[:seg_len]
        # The masks sum to 1 and the ISTFT is linear, so the second stream is
        # the input minus the first: half the inverse transforms, exact sum.
        b_l = seg[:seg_len, 0] - a_l
        b_r = seg[:seg_len, 1] - a_r
        w = np.ones(seg_len, dtype=np.float32)
        if start > 0:
            w[:ov] = np.linspace(0.0, 1.0, ov, dtype=np.float32)
        if end < n:
            w[-ov:] = np.minimum(w[-ov:], np.linspace(1.0, 0.0, ov, dtype=np.float32))
        out_a[start:end] += w[:, None] * np.column_stack([a_l, a_r])
        out_b[start:end] += w[:, None] * np.column_stack([b_l, b_r])
        weight[start:end] += w
        if end >= n:
            break
        start += block
    weight = np.maximum(weight, 1e-6)[:, None]
    return out_a / weight, out_b / weight


def _weighted_two_means(values: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    """1D weighted 2-means; returns (low_center, high_center)."""
    v = np.asarray(values, dtype=np.float64).reshape(-1)
    w = np.asarray(weights, dtype=np.float64).reshape(-1)
    if v.size == 0 or float(np.sum(w)) <= 0:
        return 0.0, 0.0
    lo, hi = float(np.percentile(v, 25)), float(np.percentile(v, 75))
    for _ in range(25):
        mid = 0.5 * (lo + hi)
        low_sel = v <= mid
        high_sel = ~low_sel
        w_lo = float(np.sum(w[low_sel]))
        w_hi = float(np.sum(w[high_sel]))
        new_lo = float(np.sum(v[low_sel] * w[low_sel]) / w_lo) if w_lo > 0 else lo
        new_hi = float(np.sum(v[high_sel] * w[high_sel]) / w_hi) if w_hi > 0 else hi
        if abs(new_lo - lo) < 1e-6 and abs(new_hi - hi) < 1e-6:
            break
        lo, hi = new_lo, new_hi
    return lo, hi


def _pan_index(spec_l: np.ndarray, spec_r: np.ndarray) -> np.ndarray:
    mag_l = np.abs(spec_l)
    mag_r = np.abs(spec_r)
    return (mag_l - mag_r) / (mag_l + mag_r + 1e-9)


def _estimate_pan_split(stereo: np.ndarray, sr: int, window_sec: float) -> tuple[float, float, float]:
    """(split point, softness, cluster spread) of energy-weighted per-bin pan index."""
    import librosa

    max_n = int(max(1.0, window_sec) * sr)
    st = stereo[:max_n]
    spec_l = librosa.stft(st[:, 0], n_fft=RENDER_N_FFT, hop_length=RENDER_HOP * 2)
    spec_r = librosa.stft(st[:, 1], n_fft=RENDER_N_FFT, hop_length=RENDER_HOP * 2)
    pan = _pan_index(spec_l, spec_r).reshape(-1)
    energy = (np.abs(spec_l) ** 2 + np.abs(spec_r) ** 2).reshape(-1)
    # Ignore faint window-leakage bins: their pan index is noise.
    keep = energy > (np.max(energy) * 1e-4 if energy.size else 0.0)
    if not np.any(keep):
        return 0.0, 0.01, 0.0
    lo, hi = _weighted_two_means(pan[keep], energy[keep])
    split = 0.5 * (lo + hi)
    # Energy-weighted distance from the split point: ~c for two clusters at
    # split±c, ~0 when the energy sits at one pan position (centered or
    # polarity-inverted material, which per-bin pan cannot separate).
    w = energy[keep]
    wsum = float(np.sum(w)) + 1e-12
    center = float(np.sum(pan[keep] * w) / wsum)
    spread = 2.0 * float(np.sum(np.abs(pan[keep] - center) * w) / wsum)
    return split, max(0.01, SPATIAL_SOFTNESS_FRACTION * spread), spread


# Tuned 2026-11-24 on synthetic doubled-rhythm + centered-lead clips (see
# eval/lead_rhythm/README.md): ~128 ms smoothing and a strict coherence floor
# took lead/rhythm SI-SDR from ~7/3.5 dB (mid/side ratio mask) to ~12/10 dB.
# 0.85 scored slightly higher but would push more of a real lead's stereo
# echo into the rhythm stem.
CENTER_SMOOTH_FRAMES = 11
CENTER_MASK_FLOOR = 0.8
CENTER_MASK_SPAN = 0.18


def _smooth_tf(x: np.ndarray, frames: int) -> np.ndarray:
    """Moving average along time (and ±1 frequency bin) of a (freq, time) array."""
    from scipy.ndimage import uniform_filter

    if np.iscomplexobj(x):
        return _smooth_tf(x.real, frames) + 1j * _smooth_tf(x.imag, frames)
    return uniform_filter(x, size=(3, max(1, frames)), mode="nearest")


def _center_mask(spec_l: np.ndarray, spec_r: np.ndarray, _freqs: np.ndarray) -> np.ndarray:
    """
    1 for centered, in-phase, coherent bins (one source sent equally to L and R);
    0 for one-sided, out-of-phase or decorrelated bins (panned or doubled parts).

    Uses short-time inter-channel coherence (primary/ambient-style center
    extraction): |<L R*>| / sqrt(<|L|²><|R|²>), times level balance and phase
    alignment, smoothed over ~80 ms. Two separately played takes panned left and
    right drift in timing and pitch, so their coherence is low even in bins
    where their instantaneous levels happen to match; a single centered part
    stays coherent. A plain mid/side energy ratio could not tell those apart.
    """
    cross = _smooth_tf(spec_l * np.conj(spec_r), CENTER_SMOOTH_FRAMES)
    pl = _smooth_tf(np.abs(spec_l) ** 2, CENTER_SMOOTH_FRAMES)
    pr = _smooth_tf(np.abs(spec_r) ** 2, CENTER_SMOOTH_FRAMES)
    geo = np.sqrt(pl * pr) + 1e-12
    coherence = np.clip(np.abs(cross) / geo, 0.0, 1.0)
    balance = 2.0 * geo / (pl + pr + 1e-12)
    phase = np.clip(np.real(cross) / (np.abs(cross) + 1e-12), 0.0, 1.0)
    score = coherence * balance * phase
    return np.clip((score - CENTER_MASK_FLOOR) / CENTER_MASK_SPAN, 0.0, 1.0)


def _stream_is_empty(stream: np.ndarray, source: np.ndarray) -> bool:
    return _rms(stream) < STREAM_EMPTY_RATIO * max(_rms(source), 1e-9)


def _load_stereo(path: Path) -> tuple[np.ndarray, int]:
    data, sr = sf.read(str(path), always_2d=True)
    if data.shape[1] == 1:
        data = np.repeat(data, 2, axis=1)
    elif data.shape[1] > 2:
        data = data[:, :2]
    return data.astype(np.float32), int(sr)


def _mono_to_stereo(mono: np.ndarray) -> np.ndarray:
    m = np.asarray(mono, dtype=np.float32).reshape(-1)
    return np.column_stack([m, m])


def _rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x)) + 1e-12))


def _dominant_pitch_estimate(mono: np.ndarray, sr: int) -> tuple[float, float]:
    """
    Cheap "predominant pitch + confidence" proxy computed directly on one
    channel — no spatial/spectral split required (see module docstring).

    Approximates the predominant-pitch features used by solo/accompaniment
    guitar classifiers (Pati & Lerch 2017; Foulon et al. 2013): the strongest
    spectral peak in the guitar-relevant band stands in for predominant pitch,
    and its share of total spectral magnitude stands in for confidence (a
    clear, foregrounded single-note voice concentrates energy into one peak;
    denser/chordal or noisy content spreads it out). Plain FFT peak-picking —
    same style as ``score_candidate_pair`` / ``_spectral_centroid_hz`` already
    in this module — so it adds no new dependency and works even without
    librosa.

    Returns (peak_freq_hz, confidence) or (0.0, 0.0) if the signal is too
    short/quiet to estimate.
    """
    x = np.asarray(mono, dtype=np.float32).reshape(-1)
    win = min(len(x), sr * 4)
    if win < 256:
        return 0.0, 0.0
    spectrum = np.abs(np.fft.rfft(x[:win] * np.hanning(win)))
    freqs = np.fft.rfftfreq(win, 1.0 / sr)
    band = (freqs >= PITCH_PROXY_FMIN_HZ) & (freqs <= PITCH_PROXY_FMAX_HZ)
    total = float(np.sum(spectrum)) + 1e-12
    if not np.any(band) or total <= 1e-9:
        return 0.0, 0.0
    band_spectrum = spectrum[band]
    band_freqs = freqs[band]
    idx = int(np.argmax(band_spectrum))
    return float(band_freqs[idx]), float(band_spectrum[idx] / total)


def _pitch_divergence_semitones(freq_a: float, freq_b: float) -> float:
    if freq_a <= 0.0 or freq_b <= 0.0:
        return 0.0
    return float(abs(12.0 * np.log2(freq_a / freq_b)))


def build_spatial_pair(
    guitar_path: Path,
    *,
    thresholds: LeadRhythmThresholds | None = None,
) -> _CandidatePair | None:
    """L/R dominance pair when stereo gate passes (evolved dual-guitar heuristic)."""
    thr = thresholds or LeadRhythmThresholds()
    if not guitar_path.exists():
        return None
    data, sr = _load_stereo(guitar_path)
    if data.shape[1] < 2 or len(data) < 1024:
        return None

    left = data[:, 0]
    right = data[:, 1]
    rms_l = _rms(left)
    rms_r = _rms(right)
    max_rms = max(rms_l, rms_r, 1e-9)
    balance = min(rms_l, rms_r) / max_rms
    if balance < thr.spatial_balance_min:
        return None
    if np.std(left) < 1e-6 or np.std(right) < 1e-6:
        return None

    corr = float(np.corrcoef(left, right)[0, 1])
    if not np.isfinite(corr):
        return None

    pitch_evidence: dict[str, float] | None = None
    detail = "stereo L/R dominance"
    if corr > thr.spatial_corr_max:
        # Raw correlation alone conflates "one guitar duplicated identically
        # into both channels" (corr -> 1.0) with "two genuinely distinct
        # guitars mixed with mild/no hard panning" (also corr ~0.92-0.99, but
        # NOT identical content). See module docstring "Root cause". Only look
        # for spatial-independent pitch-divergence evidence to rescue the
        # latter — never for correlations near-indistinguishable from a true
        # duplicate.
        if corr > thr.spatial_corr_relaxed_max:
            return None
        freq_l, conf_l = _dominant_pitch_estimate(left, sr)
        freq_r, conf_r = _dominant_pitch_estimate(right, sr)
        divergence = _pitch_divergence_semitones(freq_l, freq_r)
        if (
            divergence < thr.pitch_divergence_semitones_min
            or max(conf_l, conf_r) < thr.pitch_confidence_min
        ):
            return None
        pitch_evidence = {
            "left_hz": freq_l,
            "right_hz": freq_r,
            "divergence_semitones": divergence,
            "left_confidence": conf_l,
            "right_confidence": conf_r,
        }
        detail = (
            "stereo L/R dominance (mild pan; admitted via pitch-divergence "
            f"evidence, Δ={divergence:.1f} semitones)"
        )

    try:
        import librosa  # noqa: F401
    except ImportError:
        return None
    # Per-bin pan index (ADRess-style): every time-frequency bin goes to the
    # left-leaning or right-leaning source by its own L/R level, at any pan
    # amount. Replaces per-sample L/R switching, which distorted the audio.
    split_at, softness, spread = _estimate_pan_split(data, sr, thr.analyze_window_sec)
    if spread < SPATIAL_PAN_SPREAD_MIN:
        return None

    def _pan_mask(spec_l: np.ndarray, spec_r: np.ndarray, _freqs: np.ndarray) -> np.ndarray:
        z = np.clip((_pan_index(spec_l, spec_r) - split_at) / softness, -40.0, 40.0)
        return 1.0 / (1.0 + np.exp(-z))

    window = _analysis_window(data, sr, thr)
    a_st, b_st = stft_mask_render(window, sr, _pan_mask)
    if _stream_is_empty(a_st, window) or _stream_is_empty(b_st, window):
        return None
    a = _stereo_analysis_mono(a_st)
    b = _stereo_analysis_mono(b_st)
    detail = f"{detail}; per-bin pan mask (spread={spread:.2f})"
    sep = score_candidate_pair(a, b, sr)
    # Boost spatial score slightly when corr is low (more independent channels).
    sep = min(1.0, sep + max(0.0, (thr.spatial_corr_max - corr) * 0.15))
    return _CandidatePair(
        method="spatial",
        a=a,
        b=b,
        sr=sr,
        separability=sep,
        correlation=corr,
        balance_ratio=balance,
        detail=detail,
        pitch_evidence=pitch_evidence,
        render=lambda: stft_mask_render(data, sr, _pan_mask),
    )


def build_midside_pair(
    guitar_path: Path,
    *,
    thresholds: LeadRhythmThresholds | None = None,
    relax_side_floor: bool = False,
) -> _CandidatePair | None:
    """
    Mid/Side pair for centered lead + wide-panned rhythm (common mix layout).

    Mid = (L+R)/2, Side = (L-R)/2. Rejects true mono (L≡R) unless
    ``relax_side_floor`` (last-resort forced emit only).
    """
    thr = thresholds or LeadRhythmThresholds()
    if not guitar_path.exists():
        return None
    data, sr = _load_stereo(guitar_path)
    if data.shape[1] < 2 or len(data) < 1024:
        return None

    left = data[:, 0].astype(np.float32)
    right = data[:, 1].astype(np.float32)
    mid = ((left + right) * 0.5).astype(np.float32)
    side = ((left - right) * 0.5).astype(np.float32)
    rms_mid = _rms(mid)
    rms_side = _rms(side)
    if rms_mid < 1e-6:
        return None
    side_ratio = rms_side / max(rms_mid, 1e-9)
    if not relax_side_floor and side_ratio < thr.midside_side_ratio_min:
        return None
    if rms_side < 1e-6 and not relax_side_floor:
        return None

    a_st: np.ndarray | None = None
    b_st: np.ndarray | None = None
    try:
        import librosa  # noqa: F401

        has_librosa = True
    except ImportError:
        has_librosa = False
    if has_librosa and rms_side >= 1e-6:
        # Per-bin "centered and in phase" mask on both channels: the centered
        # part (often the lead) vs everything panned or wide (often a doubled
        # rhythm), and the wide part keeps its stereo image.
        window = _analysis_window(data, sr, thr)
        a_st, b_st = stft_mask_render(window, sr, _center_mask)
        if _stream_is_empty(a_st, window) or _stream_is_empty(b_st, window):
            if not relax_side_floor:
                return None
            a_st = b_st = None
    render = None
    if a_st is not None and b_st is not None:
        a = _stereo_analysis_mono(a_st)
        b = _stereo_analysis_mono(b_st)
        a_st = b_st = None  # window only; the full song renders on demand

        def render():
            return stft_mask_render(data, sr, _center_mask)

        detail = (
            f"centered vs wide per-bin coherence mask (side/mid RMS ratio={side_ratio:.3f})"
        )
    else:
        # Forced last resort (best-effort only): Mid vs Side, or a quiet
        # complementary copy when Side is silent. Labels are low-confidence.
        a = mid
        b = side if rms_side >= 1e-6 else (mid * 0.15).astype(np.float32)
        a_st = np.column_stack([a, a]).astype(np.float32)
        b_st = (
            np.column_stack([side, -side]).astype(np.float32)
            if rms_side >= 1e-6
            else np.column_stack([b, b]).astype(np.float32)
        )
        detail = f"Mid/Side split (side/mid RMS ratio={side_ratio:.3f})"

    sep = score_candidate_pair(a, b, sr)
    return _CandidatePair(
        method="midside",
        a=a,
        b=b,
        sr=sr,
        separability=sep,
        balance_ratio=side_ratio,
        detail=detail,
        a_stereo=a_st,
        b_stereo=b_st,
        render=render,
    )


def build_register_pair(
    guitar_path: Path,
    *,
    thresholds: LeadRhythmThresholds | None = None,
) -> _CandidatePair | None:
    """
    Soft-split the guitar into low vs high register via a fixed STFT crossover.

    Last-resort candidate only: a crossover is an EQ, not a part split (power
    chords have strong harmonics above it, low-string leads sit below it), so
    the temporal and spatial methods are preferred and this rarely passes the
    confident gates.
    """
    thr = thresholds or LeadRhythmThresholds()
    if not guitar_path.exists():
        return None
    try:
        import librosa  # noqa: F401
    except ImportError:
        return None

    data, sr = _load_stereo(guitar_path)
    if len(data) < 1024:
        return None

    def _high_mask(_spec_l: np.ndarray, _spec_r: np.ndarray, freqs: np.ndarray) -> np.ndarray:
        high_w = 1.0 - 1.0 / (1.0 + np.exp((freqs - REGISTER_CROSSOVER_HZ) / 40.0))
        return np.broadcast_to(high_w[:, None], _spec_l.shape)

    # Whole song, stereo (v1 rendered only the first analyze window and then
    # padded silence, so both stems went quiet after 90 s).
    window = _analysis_window(data, sr, thr)
    high_st, low_st = stft_mask_render(window, sr, _high_mask)
    high = high_st.mean(axis=1).astype(np.float32)
    low = low_st.mean(axis=1).astype(np.float32)
    if _rms(low) < 1e-5 or _rms(high) < 1e-5:
        return None
    sep = score_candidate_pair(high, low, sr)
    return _CandidatePair(
        method="register",
        a=high,
        b=low,
        sr=sr,
        separability=sep,
        detail=f"STFT register split @{REGISTER_CROSSOVER_HZ:.0f}Hz (last resort)",
        render=lambda: stft_mask_render(data, sr, _high_mask),
    )


def build_spectral_pair(
    guitar_path: Path,
    *,
    thresholds: LeadRhythmThresholds | None = None,
) -> _CandidatePair | None:
    """HPSS harmonic vs residual (diagnostics / research only; not musical Lead/Rhythm)."""
    thr = thresholds or LeadRhythmThresholds()
    if not guitar_path.exists():
        return None
    try:
        import librosa
    except ImportError:
        return None

    data, sr = _load_stereo(guitar_path)
    if len(data) < 1024:
        return None
    mono = data.mean(axis=1).astype(np.float32)
    max_samples = int(thr.analyze_window_sec * sr)
    mono_work = mono[:max_samples] if len(mono) > max_samples else mono
    harm, perc = librosa.effects.hpss(mono_work)
    harm = harm.astype(np.float32)
    perc = perc.astype(np.float32)
    # Do not pad identical mono into both streams (legacy bug). Silence-pad only.
    if len(mono) > max_samples:
        pad = len(mono) - max_samples
        harm = np.concatenate([harm, np.zeros(pad, dtype=np.float32)])
        perc = np.concatenate([perc, np.zeros(pad, dtype=np.float32)])

    if _rms(harm) < 1e-5 or _rms(perc) < 1e-5:
        return None
    sep = score_candidate_pair(harm, perc, sr)
    return _CandidatePair(
        method="spectral",
        a=harm,
        b=perc,
        sr=sr,
        separability=sep,
        detail="HPSS harmonic vs residual (quarantined emit)",
    )


def score_candidate_pair(a: np.ndarray, b: np.ndarray, sr: int) -> float:
    """Cheap separability in [0, 1]: residual energy, centroid gap, onset-rate gap."""
    a = np.asarray(a, dtype=np.float32).reshape(-1)
    b = np.asarray(b, dtype=np.float32).reshape(-1)
    n = min(len(a), len(b))
    if n < 512:
        return 0.0
    a = a[:n]
    b = b[:n]
    ra, rb = _rms(a), _rms(b)
    if ra < 1e-6 or rb < 1e-6:
        return 0.0

    proj = (np.dot(a, b) / (np.dot(b, b) + 1e-12)) * b
    residual = a - proj
    residual_ratio = min(1.0, _rms(residual) / (ra + 1e-12))

    win = min(n, sr * 4)
    aa = np.abs(np.fft.rfft(a[:win] * np.hanning(win)))
    bb = np.abs(np.fft.rfft(b[:win] * np.hanning(win)))
    freqs = np.fft.rfftfreq(win, 1.0 / sr)
    ca = float(np.sum(freqs * aa) / (np.sum(aa) + 1e-12))
    cb = float(np.sum(freqs * bb) / (np.sum(bb) + 1e-12))
    centroid_gap = min(1.0, abs(ca - cb) / 2000.0)

    hop = max(1, sr // 100)
    ea = np.array([_rms(a[i : i + hop]) for i in range(0, n - hop, hop)])
    eb = np.array([_rms(b[i : i + hop]) for i in range(0, n - hop, hop)])
    flux_a = float(np.mean(np.maximum(0.0, np.diff(ea, prepend=ea[:1]))))
    flux_b = float(np.mean(np.maximum(0.0, np.diff(eb, prepend=eb[:1]))))
    onset_gap = min(1.0, abs(flux_a - flux_b) / (max(flux_a, flux_b, 1e-9)))

    score = 0.45 * residual_ratio + 0.35 * centroid_gap + 0.20 * onset_gap
    return float(max(0.0, min(1.0, score)))


@dataclass
class RoleFeatures:
    pitch_median: float
    pitch_iqr: float
    note_density: float
    polyphony: float
    mean_velocity: float
    sustain: float

    def lead_score(self) -> float:
        # Higher pitch, lower polyphony, sparser notes, longer sustain, brighter velocity.
        pitch_n = min(1.0, max(0.0, (self.pitch_median - 50.0) / 30.0))
        poly_n = 1.0 - min(1.0, self.polyphony / 3.0)
        dens_n = 1.0 - min(1.0, self.note_density / 8.0)
        iqr_n = min(1.0, self.pitch_iqr / 18.0)  # melodic range
        sust_n = min(1.0, self.sustain / 0.6)
        vel_n = min(1.0, max(0.0, (self.mean_velocity - 40.0) / 60.0))
        return (
            0.35 * pitch_n
            + 0.20 * poly_n
            + 0.15 * dens_n
            + 0.15 * iqr_n
            + 0.10 * sust_n
            + 0.05 * vel_n
        )

    def rhythm_score(self) -> float:
        pitch_n = 1.0 - min(1.0, max(0.0, (self.pitch_median - 45.0) / 30.0))
        poly_n = min(1.0, self.polyphony / 3.0)
        dens_n = min(1.0, self.note_density / 8.0)
        # Tight pitch IQR and shorter notes → chordal rhythm-like.
        iqr_n = 1.0 - min(1.0, self.pitch_iqr / 18.0)
        sust_n = 1.0 - min(1.0, self.sustain / 0.6)
        return 0.25 * pitch_n + 0.30 * poly_n + 0.25 * dens_n + 0.10 * iqr_n + 0.10 * sust_n

    def to_dict(self) -> dict[str, float]:
        return {
            "pitch_median": self.pitch_median,
            "pitch_iqr": self.pitch_iqr,
            "note_density": self.note_density,
            "polyphony": self.polyphony,
            "mean_velocity": self.mean_velocity,
            "sustain": self.sustain,
        }


def extract_role_features_from_notes(
    notes: list[Any],
    duration_sec: float,
) -> RoleFeatures:
    """Feature extraction from pretty_midi-like notes (testable without Basic Pitch)."""
    if not notes or duration_sec <= 0:
        return RoleFeatures(60.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    pitches = np.array([n.pitch for n in notes], dtype=np.float64)
    velocities = np.array([n.velocity for n in notes], dtype=np.float64)
    durs = np.array([max(0.0, n.end - n.start) for n in notes], dtype=np.float64)
    starts = np.array([n.start for n in notes], dtype=np.float64)

    # Notes sounding at each onset (start <= s < end), via sorted searches
    # instead of an all-pairs loop (dense strumming has thousands of notes).
    ends = np.array([n.end for n in notes], dtype=np.float64)
    started = np.searchsorted(np.sort(starts), starts, side="right")
    ended = np.searchsorted(np.sort(ends), starts, side="right")
    poly = float(np.mean(started - ended)) if len(starts) else 0.0

    return RoleFeatures(
        pitch_median=float(np.median(pitches)),
        pitch_iqr=float(np.subtract(*np.percentile(pitches, [75, 25]))),
        note_density=float(len(notes) / duration_sec),
        polyphony=poly,
        mean_velocity=float(np.mean(velocities)),
        sustain=float(np.mean(durs)),
    )


def _average_role_features(feats: list[RoleFeatures]) -> RoleFeatures:
    if not feats:
        return RoleFeatures(60.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    n = float(len(feats))
    return RoleFeatures(
        pitch_median=sum(f.pitch_median for f in feats) / n,
        pitch_iqr=sum(f.pitch_iqr for f in feats) / n,
        note_density=sum(f.note_density for f in feats) / n,
        polyphony=sum(f.polyphony for f in feats) / n,
        mean_velocity=sum(f.mean_velocity for f in feats) / n,
        sustain=sum(f.sustain for f in feats) / n,
    )


def extract_role_features(
    audio_mono: np.ndarray,
    sr: int,
    *,
    thresholds: LeadRhythmThresholds | None = None,
) -> RoleFeatures:
    """Run Basic Pitch on mono (first + last analyze windows) and extract features."""
    thr = thresholds or LeadRhythmThresholds()
    import pretty_midi
    from basic_pitch.inference import predict

    from audio_to_tab.transcribe import basic_pitch_model_path

    window = int(thr.analyze_window_sec * sr)
    n = len(audio_mono)
    if n < sr // 4:
        return RoleFeatures(60.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    starts = [0]
    if n > window + sr:
        starts.append(max(0, n - window))

    feats: list[RoleFeatures] = []
    model_path = basic_pitch_model_path()
    for start in starts:
        clip = audio_mono[start : start + window].astype(np.float32)
        if len(clip) < sr // 4:
            continue
        stereo = _mono_to_stereo(clip)
        with tempfile.TemporaryDirectory() as tmp:
            wav_path = Path(tmp) / "clip.wav"
            sf.write(str(wav_path), stereo, sr, subtype="PCM_16")
            _, midi_data, _ = predict(
                str(wav_path),
                model_or_model_path=model_path,
                onset_threshold=0.5,
                frame_threshold=0.3,
                minimum_note_length=58.0,
            )
            mid_path = Path(tmp) / "clip.mid"
            midi_data.write(str(mid_path))
            pm = pretty_midi.PrettyMIDI(str(mid_path))
            notes = [note for inst in pm.instruments for note in inst.notes]
            feats.append(extract_role_features_from_notes(notes, duration_sec=len(clip) / sr))
    return _average_role_features(feats)


def classify_lead_rhythm_roles(
    feat_a: RoleFeatures,
    feat_b: RoleFeatures,
    *,
    margin_min: float | None = None,
) -> tuple[Literal["a_lead", "b_lead", "ambiguous"], float, dict[str, Any]]:
    """
    Assign which stream is lead vs rhythm.

    Returns (assignment, confidence_margin, detail).
    """
    floor = ROLE_MARGIN_MIN if margin_min is None else float(margin_min)
    s1 = 0.5 * (feat_a.lead_score() + feat_b.rhythm_score())
    s2 = 0.5 * (feat_b.lead_score() + feat_a.rhythm_score())
    margin = abs(s1 - s2)
    detail = {
        "stream_a": feat_a.to_dict(),
        "stream_b": feat_b.to_dict(),
        "score_a_lead": s1,
        "score_b_lead": s2,
        "margin": margin,
        "margin_min": floor,
    }
    if margin < floor:
        return "ambiguous", float(margin), detail
    if s1 >= s2:
        return "a_lead", float(margin), detail
    return "b_lead", float(margin), detail


@dataclass
class TemporalResult:
    """Outcome of the who-plays-when analysis (see ``analyze_temporal_roles``)."""

    confident: bool
    reason: str
    gain: np.ndarray | None = None  # per-sample lead gain in [0, 1] at the source rate
    segments: list[dict[str, Any]] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)
    too_short: bool = False


def _zscore(x: np.ndarray) -> np.ndarray:
    x = np.asarray(x, dtype=np.float64)
    sd = float(np.std(x))
    if sd < 1e-9:
        return np.zeros_like(x)
    return (x - float(np.mean(x))) / sd


def _majority_smooth(labels: np.ndarray, size: int) -> np.ndarray:
    if size <= 1 or labels.size < size:
        return labels.copy()
    half = size // 2
    padded = np.pad(labels.astype(np.float64), (half, half), mode="edge")
    out = np.array(
        [padded[i : i + size].mean() >= 0.5 for i in range(labels.size)], dtype=bool
    )
    return out


def _merge_short_runs(labels: np.ndarray, min_len: int) -> np.ndarray:
    """Relabel runs shorter than ``min_len`` windows to their longer neighbour."""
    lab = labels.copy()
    if min_len <= 1 or lab.size == 0:
        return lab
    for _ in range(lab.size):
        runs: list[tuple[int, int]] = []
        start = 0
        for i in range(1, lab.size + 1):
            if i == lab.size or lab[i] != lab[start]:
                runs.append((start, i))
                start = i
        short = [(e - s, s, e) for s, e in runs if e - s < min_len]
        if not short or len(runs) == 1:
            break
        _, s, e = min(short)
        lab[s:e] = ~lab[s]
    return lab


def _segments_from_labels(
    labels: np.ndarray, centers_sec: np.ndarray, duration_sec: float
) -> list[dict[str, Any]]:
    segs: list[dict[str, Any]] = []
    if labels.size == 0:
        return segs
    start_t = 0.0
    for i in range(1, labels.size + 1):
        if i == labels.size or labels[i] != labels[i - 1]:
            end_t = (
                duration_sec
                if i == labels.size
                else 0.5 * (float(centers_sec[i - 1]) + float(centers_sec[i]))
            )
            segs.append(
                {
                    "start": round(start_t, 3),
                    "end": round(end_t, 3),
                    "role": "lead" if labels[i - 1] else "rhythm",
                }
            )
            start_t = end_t
    return segs


def _refine_boundaries(
    segments: list[dict[str, Any]],
    voiced_prob: np.ndarray,
    frame_sec: float,
    *,
    target: float,
    search_sec: float = 1.5,
) -> list[dict[str, Any]]:
    """
    Move each lead/rhythm boundary to where the frame-level single-note
    confidence actually crosses halfway between the two roles (2 s windows
    otherwise blur the edge by up to a second).
    """
    if len(segments) < 2 or voiced_prob.size == 0:
        return segments
    k = max(1, round(0.3 / frame_sec))
    smooth = np.convolve(voiced_prob, np.ones(k) / k, mode="same")
    segs = [dict(s) for s in segments]
    for i in range(1, len(segs)):
        tb = float(segs[i]["start"])
        i0 = max(0, int((tb - search_sec) / frame_sec))
        i1 = min(smooth.size, int((tb + search_sec) / frame_sec) + 1)
        if i1 - i0 < 3:
            continue
        window = smooth[i0:i1]
        above = np.where(window >= target)[0]
        if above.size == 0:
            continue
        if segs[i]["role"] == "lead":  # rhythm → lead: first frame above target
            new_tb = (i0 + int(above[0])) * frame_sec
        else:  # lead → rhythm: just after the last frame above target
            new_tb = (i0 + int(above[-1]) + 1) * frame_sec
        lo = float(segs[i - 1]["start"]) + 0.5
        hi = float(segs[i]["end"]) - 0.5
        if lo < hi:
            new_tb = min(max(new_tb, lo), hi)
            segs[i]["start"] = round(new_tb, 3)
            segs[i - 1]["end"] = round(new_tb, 3)
    return segs


def _gain_from_segments(segments: list[dict[str, Any]], n: int, sr: int) -> np.ndarray:
    """Per-sample lead gain with short raised-cosine crossfades at boundaries."""
    gain = np.zeros(n, dtype=np.float32)
    for seg in segments:
        if seg["role"] == "lead":
            a = int(max(0, round(seg["start"] * sr)))
            b = int(min(n, round(seg["end"] * sr)))
            gain[a:b] = 1.0
    fade = max(2, int(TEMPORAL_FADE_SEC * sr))
    for seg in segments[1:]:
        center = round(seg["start"] * sr)
        a = max(0, center - fade // 2)
        b = min(n, a + fade)
        if b - a < 2:
            continue
        g0 = float(gain[a - 1]) if a > 0 else float(gain[a])
        g1 = float(gain[b]) if b < n else float(gain[b - 1])
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0.0, np.pi, b - a, dtype=np.float32))
        gain[a:b] = g0 + (g1 - g0) * ramp
    return gain


def _load_mono_resampled(path: Path | None, target_sr: int) -> np.ndarray | None:
    if path is None or not Path(path).is_file():
        return None
    try:
        import librosa

        data, sr = sf.read(str(path), always_2d=True)
        mono = data.mean(axis=1).astype(np.float32)
        if sr != target_sr:
            mono = librosa.resample(mono, orig_sr=sr, target_sr=target_sr)
        return mono.astype(np.float32)
    except Exception:
        return None


def analyze_temporal_roles(
    guitar_stereo: np.ndarray,
    sr: int,
    *,
    vocals_path: Path | None = None,
    thresholds: LeadRhythmThresholds | None = None,
) -> TemporalResult:
    """
    Decide, window by window, whether the guitar is playing a lead-like or a
    rhythm-like part, then smooth the decisions into sections.

    Features per 2 s window (1 s hop), all song-relative except the anchors:
    predominant-pitch confidence (pYIN voiced probability; single-note lines
    score high, chords low), pitch-class concentration (one note's chroma is
    peaky, a chord's is spread), register (median f0), pitch movement inside
    notes (bends / vibrato), loudness, and vocal silence from the vocal stem
    (solos usually happen when nobody sings). A 1D 2-means on the combined score
    must explain at least ``temporal_r2_min`` of its variance, lead sections must
    be clearly more single-voiced than rhythm sections, and each role needs
    ``temporal_min_role_sec`` seconds and ``temporal_min_role_share`` of the
    active guitar time. Otherwise the result is not confident.
    """
    import librosa

    thr = thresholds or LeadRhythmThresholds()
    st = np.asarray(guitar_stereo, dtype=np.float32)
    n = len(st)
    duration = n / float(sr)
    if duration < 2.0 * thr.temporal_min_role_sec:
        return TemporalResult(False, "guitar too short for a lead/rhythm split", too_short=True)

    asr = TEMPORAL_ANALYSIS_SR
    mono = st.mean(axis=1)
    y = librosa.resample(mono, orig_sr=sr, target_sr=asr) if sr != asr else mono
    y = np.asarray(y, dtype=np.float32)
    hop = TEMPORAL_ANALYSIS_HOP
    f0, vflag, vprob = librosa.pyin(
        y, fmin=75.0, fmax=1400.0, sr=asr, frame_length=2048, hop_length=hop
    )
    rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=hop)[0]
    chroma = librosa.feature.chroma_stft(y=y, sr=asr, n_fft=2048, hop_length=hop)
    frames = int(min(len(f0), rms.size, chroma.shape[1]))
    vocal_rms = None
    vocals = _load_mono_resampled(vocals_path, asr)
    if vocals is not None and len(vocals) >= 2048:
        vr = librosa.feature.rms(y=vocals, frame_length=2048, hop_length=hop)[0]
        vocal_rms = np.zeros(frames, dtype=np.float64)
        m = min(frames, vr.size)
        vocal_rms[:m] = vr[:m]

    frame_sec = hop / float(asr)
    win = max(2, round(TEMPORAL_WIN_SEC / frame_sec))
    step = max(1, round(TEMPORAL_HOP_SEC / frame_sec))
    starts = list(range(0, max(1, frames - win + 1), step))
    ref = float(np.percentile(rms[:frames], 95)) + 1e-12
    vprob = np.nan_to_num(np.asarray(vprob, dtype=np.float64))
    f0 = np.asarray(f0, dtype=np.float64)
    vflag = np.asarray(vflag, dtype=bool)

    n_w = len(starts)
    level_db = np.zeros(n_w)
    voiced = np.zeros(n_w)
    conc = np.zeros(n_w)
    register = np.full(n_w, np.nan)
    movement = np.zeros(n_w)
    vocal_level = np.zeros(n_w)
    centers = np.zeros(n_w)
    for k, s in enumerate(starts):
        e = min(frames, s + win)
        r = rms[s:e]
        level_db[k] = 20.0 * np.log10(float(np.mean(r)) / ref + 1e-12)
        voiced[k] = float(np.mean(vprob[s:e]))
        c = chroma[:, s:e] * r[None, : e - s]
        cs = c.sum(axis=1)
        tot = float(cs.sum())
        if tot > 1e-12:
            p = np.clip(cs / tot, 1e-12, 1.0)
            conc[k] = 1.0 - float(-(p * np.log(p)).sum() / np.log(12.0))
        f = f0[s:e][vflag[s:e]]
        f = f[np.isfinite(f) & (f > 0)]
        if f.size >= 3:
            semis = 12.0 * np.log2(f / 440.0) + 69.0
            register[k] = float(np.median(semis))
            d = np.abs(np.diff(semis))
            d = d[d < 0.8]
            movement[k] = float(np.mean(d)) if d.size else 0.0
        if vocal_rms is not None:
            vocal_level[k] = float(np.mean(vocal_rms[s:e]))
        centers[k] = (s + 0.5 * (e - s)) * frame_sec

    active = level_db > TEMPORAL_ACTIVE_DB
    hop_sec = step * frame_sec
    active_sec = float(np.sum(active)) * hop_sec
    detail: dict[str, Any] = {"n_windows": n_w, "active_sec": round(active_sec, 2)}
    if active_sec < 2.0 * thr.temporal_min_role_sec or int(np.sum(active)) < 4:
        return TemporalResult(
            False, "too little guitar playing for a lead/rhythm split", detail=detail, too_short=True
        )

    a_idx = np.where(active)[0]
    reg = register[a_idx]
    reg = np.where(np.isfinite(reg), reg, np.nanmedian(reg) if np.any(np.isfinite(reg)) else 60.0)
    score = (
        1.0 * _zscore(voiced[a_idx])
        + 0.7 * _zscore(conc[a_idx])
        + 0.5 * _zscore(reg)
        + 0.4 * _zscore(movement[a_idx])
        + 0.2 * _zscore(level_db[a_idx])
    )
    used_vocals = False
    if vocal_rms is not None:
        v = vocal_level[a_idx]
        v_ref = float(np.percentile(v, 90)) if v.size else 0.0
        if v_ref > 1e-4:
            silence = 1.0 - np.clip(v / (0.25 * v_ref), 0.0, 1.0)
            score = score + 1.2 * _zscore(silence)
            used_vocals = True
    detail["used_vocals"] = used_vocals

    lo, hi = _weighted_two_means(score, np.ones_like(score))
    cut = 0.5 * (lo + hi)
    is_lead = score > cut
    tss = float(np.sum((score - score.mean()) ** 2)) + 1e-12
    if np.any(is_lead) and np.any(~is_lead):
        bcss = float(
            np.sum(is_lead) * (score[is_lead].mean() - score.mean()) ** 2
            + np.sum(~is_lead) * (score[~is_lead].mean() - score.mean()) ** 2
        )
    else:
        bcss = 0.0
    r2 = bcss / tss
    detail["r2"] = round(r2, 3)

    # Window labels for every window (inactive ones take the nearest active label).
    labels = np.zeros(n_w, dtype=bool)
    labels[a_idx] = is_lead
    for k in range(n_w):
        if not active[k]:
            nearest = a_idx[int(np.argmin(np.abs(a_idx - k)))]
            labels[k] = labels[nearest]
    labels = _majority_smooth(labels, TEMPORAL_SMOOTH_WINDOWS)
    labels = _merge_short_runs(labels, max(1, round(TEMPORAL_MIN_SEGMENT_SEC / hop_sec)))

    lead_active = labels & active
    rhythm_active = (~labels) & active
    lead_sec = float(np.sum(lead_active)) * hop_sec
    rhythm_sec = float(np.sum(rhythm_active)) * hop_sec
    vp_lead = float(np.mean(voiced[lead_active])) if np.any(lead_active) else 0.0
    vp_rhythm = float(np.mean(voiced[rhythm_active])) if np.any(rhythm_active) else 0.0
    conc_lead = float(np.mean(conc[lead_active])) if np.any(lead_active) else 0.0
    conc_rhythm = float(np.mean(conc[rhythm_active])) if np.any(rhythm_active) else 0.0
    detail.update(
        {
            "lead_sec": round(lead_sec, 2),
            "rhythm_sec": round(rhythm_sec, 2),
            "voiced_lead": round(vp_lead, 3),
            "voiced_rhythm": round(vp_rhythm, 3),
            "concentration_lead": round(conc_lead, 3),
            "concentration_rhythm": round(conc_rhythm, 3),
        }
    )
    segments = _segments_from_labels(labels, centers, duration)
    segments = _refine_boundaries(
        segments,
        vprob[:frames],
        frame_sec,
        target=0.5 * (vp_lead + vp_rhythm),
    )
    detail["segments"] = segments

    problems: list[str] = []
    if r2 < thr.temporal_r2_min:
        problems.append(f"no clear two-sided pattern (r2 {r2:.2f} < {thr.temporal_r2_min})")
    min_share = thr.temporal_min_role_share * active_sec
    for name, secs in (("lead", lead_sec), ("rhythm", rhythm_sec)):
        if secs < max(thr.temporal_min_role_sec, min_share):
            problems.append(f"{name} sections too short ({secs:.0f} s)")
    single_voiced = vp_lead >= TEMPORAL_LEAD_VOICED_MIN and (
        vp_lead - vp_rhythm >= TEMPORAL_VOICED_GAP_MIN or conc_lead - conc_rhythm >= 0.08
    )
    if not single_voiced:
        problems.append("lead sections are not clearly single-note lines")
    if problems:
        return TemporalResult(False, "; ".join(problems), segments=segments, detail=detail)

    gain = _gain_from_segments(segments, n, sr)
    return TemporalResult(
        True,
        f"lead sections {lead_sec:.0f} s, rhythm sections {rhythm_sec:.0f} s (r2 {r2:.2f})",
        gain=gain,
        segments=segments,
        detail=detail,
    )


@dataclass
class _SimultaneousResult:
    """Best spatial / mid-side / register candidate with its role gates."""

    best: _CandidatePair | None
    candidates: list[_CandidatePair]
    lead_slot: str = "a"  # which stream of ``best`` is the lead
    forced: bool = True
    margin: float = 0.0
    gate_detail: str = ""
    feat_detail: dict[str, Any] = field(default_factory=dict)
    failure: str = ""
    low_sep: bool = False

    # Full-length renders happen only here, i.e. only when the split is used.
    @property
    def lead_stereo(self) -> np.ndarray:
        assert self.best is not None
        return _pair_stereo(self.best, self.lead_slot)

    @property
    def rhythm_stereo(self) -> np.ndarray:
        assert self.best is not None
        return _pair_stereo(self.best, "b" if self.lead_slot == "a" else "a")


def _pair_stereo(pair: _CandidatePair, which: str) -> np.ndarray:
    a_st, b_st = pair.full_stereo()
    return a_st if which == "a" else b_st


def _evaluate_simultaneous(
    guitar_path: Path,
    thr: LeadRhythmThresholds,
    *,
    use_basic_pitch: bool,
    emit_mode: EmitMode,
) -> _SimultaneousResult:
    candidates: list[_CandidatePair] = []
    for builder in (build_spatial_pair, build_midside_pair, build_register_pair):
        pair = builder(guitar_path, thresholds=thr)
        if pair is not None:
            candidates.append(pair)
    # HPSS is never emitted as Lead/Rhythm unless explicitly allowed, and it was
    # the slowest candidate, so it is only built when it could be used.
    if thr.allow_spectral_emit:
        spectral = build_spectral_pair(guitar_path, thresholds=thr)
        if spectral is not None:
            candidates.append(spectral)

    musical = [c for c in candidates if c.method != "spectral" or thr.allow_spectral_emit]
    if not musical:
        if emit_mode != "best_effort":
            return _SimultaneousResult(
                None,
                candidates,
                failure="no confident lead/rhythm candidate (parts too similar, centered, or unreadable)",
            )
        # Last resort for best-effort: register, then a relaxed Mid/Side.
        forced_pair = build_register_pair(guitar_path, thresholds=thr) or build_midside_pair(
            guitar_path, thresholds=thr, relax_side_floor=True
        )
        if forced_pair is None:
            return _SimultaneousResult(
                None,
                candidates,
                failure="no lead/rhythm candidate could be built (guitar too short or unreadable)",
            )
        musical = [forced_pair]
        candidates = [forced_pair]

    best = _pick_best_candidate(musical, thr)
    # When both placement splits (left/right and centered/wide) separate well,
    # keep the one whose streams differ most in single-note confidence: a
    # doubled rhythm panned wide under a centered lead splits on centered/wide,
    # not on left/right.
    voicing_cache: dict[int, dict[str, float] | None] = {}
    placement = [
        c
        for c in musical
        if c.method in ("spatial", "midside")
        and c.separability >= _separability_floor_for(c.method, thr)
    ]
    if len(placement) > 1:
        for cand in placement:
            voicing_cache[id(cand)] = _voicing_role_evidence(cand.a, cand.b, cand.sr, thr)
        decisive = [
            c
            for c in placement
            if voicing_cache.get(id(c))
            and abs(float(voicing_cache[id(c)]["voiced_gap"])) >= VOICING_GAP_DECISIVE
        ]
        if decisive:
            best = max(decisive, key=lambda c: abs(float(voicing_cache[id(c)]["voiced_gap"])))
    if best.method == "spectral" and not thr.allow_spectral_emit:
        non_spectral = [c for c in musical if c.method != "spectral"]
        if non_spectral:
            best = _pick_best_candidate(non_spectral, thr)
        else:
            forced = build_register_pair(guitar_path, thresholds=thr) or build_midside_pair(
                guitar_path, thresholds=thr, relax_side_floor=True
            )
            if forced is None:
                return _SimultaneousResult(
                    None,
                    candidates,
                    failure="spectral (HPSS) candidate quarantined and no fallback pair",
                )
            best = forced

    sep_floor = _separability_floor_for(best.method, thr)
    low_sep = best.separability < sep_floor
    analyze_a, analyze_b, analyze_sr = best.a, best.b, best.sr
    basic_pitch_error = ""
    if use_basic_pitch:
        try:
            feat_a = extract_role_features(analyze_a, analyze_sr, thresholds=thr)
            feat_b = extract_role_features(analyze_b, analyze_sr, thresholds=thr)
        except Exception as exc:  # missing/broken Basic Pitch → audio stats
            basic_pitch_error = f"{type(exc).__name__}: {exc}"
            feat_a = _features_from_audio_stats(analyze_a, analyze_sr, thresholds=thr)
            feat_b = _features_from_audio_stats(analyze_b, analyze_sr, thresholds=thr)
    else:
        feat_a = _features_from_audio_stats(analyze_a, analyze_sr, thresholds=thr)
        feat_b = _features_from_audio_stats(analyze_b, analyze_sr, thresholds=thr)

    role_floor = _role_floor_for(best.method, thr)
    # Zero margin floor → always a directional assignment; confidence is judged
    # against the real floor below.
    assignment, margin, feat_detail = classify_lead_rhythm_roles(feat_a, feat_b, margin_min=0.0)
    if best.pitch_evidence is not None:
        feat_detail["pitch_evidence"] = best.pitch_evidence
    if basic_pitch_error:
        feat_detail["basic_pitch_fallback"] = basic_pitch_error
    # Stream A is the primary slot in every builder (spatial: left-leaning,
    # midside: centered, register: high), so it is the default lead.
    if assignment == "ambiguous" or margin < 1e-9:
        assignment = "a_lead"
        feat_detail["defaulted_assignment"] = True
    # Second opinion from single-note confidence: a lead line is far more
    # "pitched" (pYIN voiced probability) than strummed chords. A clear gap
    # decides the labels even when the note-statistics margin is small.
    if best.method != "spectral" and not low_sep:
        evidence = (
            voicing_cache[id(best)]
            if id(best) in voicing_cache
            else _voicing_role_evidence(analyze_a, analyze_b, analyze_sr, thr)
        )
        if evidence is not None:
            feat_detail["voicing_evidence"] = evidence
            gap = float(evidence["voiced_gap"])
            if abs(gap) >= VOICING_GAP_DECISIVE:
                voiced_assignment = "a_lead" if gap > 0 else "b_lead"
                if voiced_assignment != assignment:
                    feat_detail["assignment_from_voicing"] = True
                assignment = voiced_assignment
                margin = max(float(margin), min(1.0, abs(gap)))
            else:
                # No single decisive cue: pool the weak ones for the best guess
                # (used when the person asked for the split anyway). Note
                # statistics + single-note confidence + brightness (a weak cue:
                # rhythm is often just as distorted), plus a small prior that a
                # centered part is the lead.
                cent_gap = (
                    _spectral_centroid_hz(analyze_a, analyze_sr)
                    - _spectral_centroid_hz(analyze_b, analyze_sr)
                ) / 4000.0
                guess = (
                    float(feat_detail.get("score_a_lead", 0.0))
                    - float(feat_detail.get("score_b_lead", 0.0))
                    + gap
                    + 0.25 * cent_gap
                    + (0.03 if best.method == "midside" else 0.0)
                )
                feat_detail["best_guess_score"] = round(guess, 4)
                if abs(guess) > 1e-6:
                    assignment = "a_lead" if guess > 0 else "b_lead"
    # A fixed high/low crossover is an EQ, not a part split: only trust it when
    # the high stream is clearly a single-note line and the low one is not.
    if best.method == "register" and not low_sep:
        ev = feat_detail.get("voicing_evidence")
        gap = float(ev["voiced_gap"]) if ev else 0.0
        lead_gap = gap if assignment == "a_lead" else -gap
        if lead_gap < VOICING_GAP_DECISIVE:
            margin = min(float(margin), max(0.0, lead_gap))
            feat_detail["register_needs_single_note_lead"] = True
    low_role = margin < role_floor
    reasons = []
    if low_sep:
        reasons.append(f"separability {best.separability:.3f} below floor {sep_floor}")
    if low_role:
        reasons.append(f"role margin {margin:.3f} below {role_floor}")
    lead_which = "a" if assignment == "a_lead" else "b"
    return _SimultaneousResult(
        best,
        candidates,
        lead_slot=lead_which,
        forced=bool(low_sep or low_role),
        low_sep=bool(low_sep),
        margin=float(margin),
        gate_detail=" ; ".join(reasons),
        feat_detail=feat_detail,
    )


VOICING_GAP_DECISIVE = 0.25


def _voicing_role_evidence(
    a: np.ndarray, b: np.ndarray, sr: int, thr: LeadRhythmThresholds
) -> dict[str, float] | None:
    """Mean pYIN voiced probability per stream (first analyze window, 11 kHz)."""
    try:
        import librosa
    except ImportError:
        return None
    asr = TEMPORAL_ANALYSIS_SR
    max_n = int(min(thr.analyze_window_sec, 60.0) * sr)
    out: dict[str, float] = {}
    for name, x in (("a", a), ("b", b)):
        clip = np.asarray(x[:max_n], dtype=np.float32)
        if len(clip) < sr // 2 or _rms(clip) < 1e-5:
            return None
        y = librosa.resample(clip, orig_sr=sr, target_sr=asr) if sr != asr else clip
        _, _, vprob = librosa.pyin(
            y, fmin=75.0, fmax=1400.0, sr=asr, frame_length=2048, hop_length=TEMPORAL_ANALYSIS_HOP
        )
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=TEMPORAL_ANALYSIS_HOP)[0]
        m = min(len(vprob), rms.size)
        w = rms[:m]
        out[f"voiced_{name}"] = float(
            np.sum(np.nan_to_num(vprob[:m]) * w) / (float(np.sum(w)) + 1e-12)
        )
    out["voiced_gap"] = out["voiced_a"] - out["voiced_b"]
    return out


def _write_stem(path: Path, stereo: np.ndarray, sr: int) -> Path:
    data = np.clip(np.asarray(stereo, dtype=np.float32), -1.0, 1.0)
    if data.ndim == 1:
        data = _mono_to_stereo(data)
    sf.write(str(path), data, sr, subtype="PCM_16")
    return path


def _match_length(stereo: np.ndarray, n: int) -> np.ndarray:
    st = np.asarray(stereo, dtype=np.float32)
    if len(st) >= n:
        return st[:n]
    return np.pad(st, ((0, n - len(st)), (0, 0)))


def split_lead_rhythm_guitar(
    guitar_path: Path,
    output_dir: Path,
    *,
    use_basic_pitch: bool = True,
    thresholds: LeadRhythmThresholds | None = None,
    emit_mode: EmitMode = "confident",
    vocals_path: Path | None = None,
) -> tuple[dict[str, Path], LeadRhythmDiagnostics]:
    """
    Attempt a lead/rhythm split of an isolated guitar stem.

    Order: skip near-silent guitar → temporal (who plays when; uses
    ``vocals_path`` when given) → simultaneous candidates (spatial, mid-side,
    register last). Writes ``guitar_split_diagnostics.json`` whenever a guitar
    stem exists (with ``reason_code`` and a plain ``user_message``). Emits stereo,
    full-length ``lead_guitar.wav`` + ``rhythm_guitar.wav`` only when a method
    passes its gates, or when ``emit_mode`` is ``best_effort``. In ``confident``
    mode a failed split keeps the single Guitar stem. Spectral candidates never
    emit unless ``thresholds.allow_spectral_emit``.
    """
    thr = LeadRhythmThresholds.from_env(thresholds)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    diag_path = out_dir / "guitar_split_diagnostics.json"

    def _finish(diag: LeadRhythmDiagnostics, extra: dict[str, Path] | None = None):
        diag.write_json(diag_path)
        result = dict(extra or {})
        result["guitar_split_diagnostics"] = diag_path
        return result, diag

    if not guitar_path.exists():
        return _finish(
            LeadRhythmDiagnostics(
                outcome="skipped",
                reason="guitar stem missing",
                attempted=False,
                reason_code="missing",
            )
        )

    data, sr = _load_stereo(guitar_path)
    level_dbfs = 20.0 * np.log10(_rms(data) + 1e-12)
    if level_dbfs < thr.guitar_present_dbfs_min:
        return _finish(
            LeadRhythmDiagnostics(
                outcome="skipped",
                reason=(
                    f"guitar stem near-silent ({level_dbfs:.1f} dBFS < "
                    f"{thr.guitar_present_dbfs_min:.1f}); combined Guitar kept"
                ),
                reason_code="not_present",
                features={"level_dbfs": round(float(level_dbfs), 2), "emit_mode": emit_mode},
            )
        )

    temporal: TemporalResult | None = None
    temporal_error = ""
    if thr.temporal_enabled:
        try:
            temporal = analyze_temporal_roles(
                data, sr, vocals_path=vocals_path, thresholds=thr
            )
        except Exception as exc:  # analysis must never fail the isolate job
            temporal_error = f"{type(exc).__name__}: {exc}"

    sim = _evaluate_simultaneous(
        guitar_path, thr, use_basic_pitch=use_basic_pitch, emit_mode=emit_mode
    )
    features: dict[str, Any] = dict(sim.feat_detail)
    features["emit_mode"] = emit_mode
    if temporal is not None:
        features["temporal"] = {
            **temporal.detail,
            "confident": temporal.confident,
            "reason": temporal.reason,
        }
    if temporal_error:
        features["temporal_error"] = temporal_error

    n = len(data)
    sim_ok = sim.best is not None and not sim.forced
    sim_method = sim.best.method if sim.best is not None else "none"

    # 1) Temporal: lead = guitar during lead sections; inside lead sections use
    #    a confident simultaneous split so the rhythm under a solo stays put.
    if temporal is not None and temporal.confident and temporal.gain is not None:
        g = temporal.gain[:, None]
        if sim_ok and sim_method in ("spatial", "midside"):
            lead_sim = _match_length(sim.lead_stereo, n)
            rhythm_sim = _match_length(sim.rhythm_stereo, n)
            lead = g * lead_sim
            rhythm = g * rhythm_sim + (1.0 - g) * data
            features["simultaneous_method"] = sim_method
        else:
            lead = g * data
            rhythm = (1.0 - g) * data
        lead_path = _write_stem(out_dir / "lead_guitar.wav", lead, sr)
        rhythm_path = _write_stem(out_dir / "rhythm_guitar.wav", rhythm, sr)
        return _finish(
            LeadRhythmDiagnostics(
                outcome="lead_rhythm",
                reason=f"split via temporal ({temporal.reason})",
                separability_score=sim.best.separability if sim_ok and sim.best else None,
                role_confidence=float(temporal.detail.get("r2", 0.0)),
                method="temporal",
                correlation=sim.best.correlation if sim.best else None,
                balance_ratio=sim.best.balance_ratio if sim.best else None,
                features=features,
                reason_code="split",
            ),
            {"lead_guitar": lead_path, "rhythm_guitar": rhythm_path},
        )

    # 2) No usable candidate at all.
    if sim.best is None:
        code = "too_short" if (temporal is not None and temporal.too_short) else "one_part"
        features["skipped_emit"] = True
        return _finish(
            LeadRhythmDiagnostics(
                outcome="ambiguous",
                reason=sim.failure,
                method="none",
                features=features,
                reason_code=code,
            )
        )

    best = sim.best
    if sim.forced:
        features["forced_emit"] = True
        features["low_confidence"] = True

    # Two distinct parts were found (they separate well), only the labels are
    # uncertain. A fixed register crossover never counts as "two parts" unless
    # its high stream is clearly a single-note line.
    two_parts = (
        not sim.low_sep
        and best.method in ("spatial", "midside", "register")
        and not sim.feat_detail.get("register_needs_single_note_lead")
    )
    labels_unsure = sim.forced and two_parts
    features["two_parts_found"] = bool(two_parts)

    # 3) The simultaneous split failed its gates and this mode won't emit it.
    refuse = sim.forced and (
        emit_mode == "confident" or (emit_mode == "prefer_split" and not two_parts)
    )
    if refuse:
        features["skipped_emit"] = True
        if temporal is not None and temporal.too_short and best.method not in ("spatial", "midside"):
            code = "too_short"
        elif not sim.low_sep:
            code = "unclear_roles"
        elif best.method in ("spatial", "midside"):
            code = "overlap"
        else:
            code = "one_part"
        return _finish(
            LeadRhythmDiagnostics(
                outcome="ambiguous",
                reason=(
                    f"Lead/Rhythm not emitted (confident mode): {best.method} candidate "
                    f"failed gates ({sim.gate_detail}); combined Guitar kept"
                ),
                separability_score=best.separability,
                role_confidence=sim.margin,
                method=best.method,
                correlation=best.correlation,
                balance_ratio=best.balance_ratio,
                forced_emit=True,
                low_confidence=True,
                features=features,
                reason_code=code,
            )
        )

    # 4) Emit the simultaneous split (confident, or best-effort).
    lead_path = _write_stem(out_dir / "lead_guitar.wav", _match_length(sim.lead_stereo, n), sr)
    rhythm_path = _write_stem(
        out_dir / "rhythm_guitar.wav", _match_length(sim.rhythm_stereo, n), sr
    )
    if sim.forced:
        reason = (
            f"best-effort split via {best.method} ({sim.gate_detail}); labels may be inaccurate"
        )
    else:
        reason = f"split via {best.method}; role margin {sim.margin:.3f}"
    return _finish(
        LeadRhythmDiagnostics(
            outcome="lead_rhythm",
            reason=reason,
            separability_score=best.separability,
            role_confidence=sim.margin,
            method=best.method,
            correlation=best.correlation,
            balance_ratio=best.balance_ratio,
            forced_emit=sim.forced,
            low_confidence=sim.forced,
            features=features,
            reason_code=(
                "split_labels_unsure"
                if labels_unsure
                else ("split_low_confidence" if sim.forced else "split")
            ),
        ),
        {"lead_guitar": lead_path, "rhythm_guitar": rhythm_path},
    )


def _separability_floor_for(method: Method, thr: LeadRhythmThresholds) -> float:
    if method == "spectral":
        return thr.spectral_separability_floor
    if method == "register":
        return thr.register_separability_floor
    if method == "midside":
        return thr.midside_separability_floor
    return thr.separability_floor


def _role_floor_for(method: Method, thr: LeadRhythmThresholds) -> float:
    if method == "spectral":
        return thr.spectral_role_margin_min
    return thr.role_margin_min


def _pick_best_candidate(
    candidates: list[_CandidatePair],
    thr: LeadRhythmThresholds,
) -> _CandidatePair:
    """Prefer hard-panned spatial; then midside; then register; spectral last."""
    spatial = [
        c
        for c in candidates
        if c.method == "spatial"
        and c.separability >= thr.separability_floor
        and c.correlation is not None
        and c.correlation < 0.35
    ]
    if spatial:
        return max(spatial, key=lambda c: c.separability)
    # Otherwise the better-separated of spatial / mid-side (a centered lead
    # over a wide rhythm has no left/right pan difference but splits cleanly
    # on centered-vs-wide).
    placement = [c for c in candidates if c.method in ("spatial", "midside")]
    if placement:
        return max(placement, key=lambda c: c.separability)
    register = [c for c in candidates if c.method == "register"]
    if register:
        return max(register, key=lambda c: c.separability)
    return max(candidates, key=lambda c: c.separability)


def _spectral_centroid_hz(mono: np.ndarray, sr: int) -> float:
    win = min(len(mono), sr * 2)
    if win < 64:
        return 0.0
    x = mono[:win] * np.hanning(win)
    mag = np.abs(np.fft.rfft(x))
    freqs = np.fft.rfftfreq(win, 1.0 / sr)
    return float(np.sum(freqs * mag) / (np.sum(mag) + 1e-12))


def _features_from_audio_stats(
    mono: np.ndarray,
    sr: int,
    *,
    thresholds: LeadRhythmThresholds | None = None,
) -> RoleFeatures:
    """Map centroid/flux into RoleFeatures when Basic Pitch is skipped (tests/fallback)."""
    thr = thresholds or LeadRhythmThresholds()
    window = int(thr.analyze_window_sec * sr)
    n = len(mono)
    starts = [0]
    if n > window + sr:
        starts.append(max(0, n - window))

    feats: list[RoleFeatures] = []
    for start in starts:
        clip = mono[start : start + window]
        if len(clip) < 64:
            continue
        c = _spectral_centroid_hz(clip, sr)
        pitch = 12.0 * np.log2(max(c, 80.0) / 440.0) + 69.0
        hop = max(1, sr // 100)
        energy = np.array(
            [_rms(clip[i : i + hop]) for i in range(0, max(1, len(clip) - hop), hop)]
        )
        flux = (
            float(np.mean(np.maximum(0.0, np.diff(energy, prepend=energy[:1]))))
            if len(energy)
            else 0.0
        )
        dens = min(8.0, flux * 40.0)
        poly = 1.0 + min(2.0, dens / 4.0)
        feats.append(
            RoleFeatures(
                pitch_median=float(pitch),
                pitch_iqr=6.0,
                note_density=float(dens),
                polyphony=float(poly),
                mean_velocity=80.0,
                sustain=0.2,
            )
        )
    return _average_role_features(feats)
