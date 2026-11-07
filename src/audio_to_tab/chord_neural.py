"""Optional BTC neural chord scorer (opt-in).

Code is MIT (vendored under ``audio_to_tab.btc``). The pretrained checkpoint was
trained on Isophonics / Robbie Williams / UsPop2002 labels with audio collected
from commercial services — weight redistributability is **undocumented**. We
download only when explicitly requested (``ensure_chord_model`` /
``ATT_CHORD_MODEL=1``) and never enable this path by default.

25-class maj/min vocabulary — deliberately avoids the template stack's maj7 /
mMaj7 spam on dense mixes.

Frame log-softmax scores are beat-pooled when beats are available, then
smoothed with the shared Viterbi decoder from ``audio_to_tab.chords``.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Sequence
from pathlib import Path

import numpy as np

from audio_to_tab.analysis import ChordEvent
from audio_to_tab.chord_symbols import parse
from audio_to_tab.chords import (
    _OFF_DOWNBEAT_PENALTY,
    _ON_DOWNBEAT_BONUS,
    _boundaries,
    _decorate,
    _is_downbeat,
    _merge_events,
    _slash_bass,
    _viterbi,
    _window_confidence,
)
from audio_to_tab.roformer import download_sha256_file, file_sha256

logger = logging.getLogger(__name__)

# Upstream: jayg996/BTC-ISMIR19 test/btc_model.pt (25-class maj/min).
BTC_WEIGHT_URL = (
    "https://raw.githubusercontent.com/jayg996/BTC-ISMIR19/master/test/btc_model.pt"
)
BTC_WEIGHT_SHA256 = "71c2c5db17e8c43b8a9a9da5db36ef2d667158c07a214eba16344c154c00bf54"
BTC_WEIGHT_NAME = "btc_model.pt"
BTC_WEIGHT_BYTES = 12_154_754

_IDX2CHORD = (
    "C",
    "C:min",
    "C#",
    "C#:min",
    "D",
    "D:min",
    "D#",
    "D#:min",
    "E",
    "E:min",
    "F",
    "F:min",
    "F#",
    "F#:min",
    "G",
    "G:min",
    "G#",
    "G#:min",
    "A",
    "A:min",
    "A#",
    "A#:min",
    "B",
    "B:min",
    "N",
)

_DEFAULT_DIR = Path.home() / ".cache" / "audio_to_tab" / "chord-btc"
_SONG_HZ = 22050
_INST_LEN = 10.0
_N_BINS = 144
_BINS_PER_OCTAVE = 24
_HOP = 2048
_TIMESTEP = 108
# Log-prob change cost. Measured on scratch powerchord clips: 2.0 collapses a
# held G# to N; 1.0 keeps the root and still absorbs single-frame flips.
_BTC_CHANGE_PENALTY = 1.0

_MODEL_CONFIG = {
    "feature_size": 144,
    "timestep": 108,
    "num_chords": 25,
    "input_dropout": 0.2,
    "layer_dropout": 0.2,
    "attention_dropout": 0.2,
    "relu_dropout": 0.2,
    "num_layers": 8,
    "num_heads": 4,
    "hidden_size": 128,
    "total_key_depth": 128,
    "total_value_depth": 128,
    "filter_size": 128,
    "loss": "ce",
    "probs_out": False,
}


def default_chord_model_dir() -> Path:
    configured = os.environ.get("ATT_CHORD_MODEL_DIR")
    return Path(configured) if configured else _DEFAULT_DIR


def chord_model_requested() -> bool:
    """True when the product asked for the neural path (env or explicit model_dir)."""
    flag = (os.environ.get("ATT_CHORD_MODEL") or "").strip().lower()
    return flag in {"1", "true", "yes", "on", "btc"}


def chord_model_available(model_dir: Path | None = None) -> bool:
    path = Path(model_dir) if model_dir is not None else default_chord_model_dir()
    weight = path / BTC_WEIGHT_NAME
    if not weight.is_file() or weight.stat().st_size <= 0:
        return False
    try:
        import torch  # noqa: F401
    except Exception:
        return False
    try:
        return file_sha256(weight) == BTC_WEIGHT_SHA256
    except OSError:
        return False


def ensure_chord_model(
    model_dir: Path | None = None,
    *,
    progress: Callable[[str], None] | None = None,
) -> Path:
    """Download the pinned BTC maj/min checkpoint into ``model_dir``."""
    path = Path(model_dir) if model_dir is not None else default_chord_model_dir()
    path.mkdir(parents=True, exist_ok=True)
    destination = path / BTC_WEIGHT_NAME
    try:
        if destination.is_file() and file_sha256(destination) == BTC_WEIGHT_SHA256:
            return path
    except OSError:
        pass
    _notify(progress, "chords: downloading BTC maj/min weights (opt-in neural)")
    logger.warning(
        "Downloading BTC chord weights. Code is MIT; training-audio provenance is "
        "undocumented — keep ATT_CHORD_MODEL off for redistribution-sensitive builds."
    )
    download_sha256_file(BTC_WEIGHT_URL, destination, BTC_WEIGHT_SHA256, timeout=600)
    return path


def _notify(progress: Callable[[str], None] | None, message: str) -> None:
    if progress is None:
        return
    try:
        progress(message)
    except Exception:
        logger.debug("Chord neural progress callback failed", exc_info=True)


def _mir_eval_to_symbol(label: str) -> str:
    text = (label or "").strip()
    if not text or text.upper() in {"N", "X"}:
        return "N"
    if text.endswith(":min"):
        root = text[: -len(":min")]
        return f"{root}m"
    if ":" in text:
        root, quality = text.split(":", 1)
        mapping = {
            "maj": "",
            "min": "m",
            "maj7": "maj7",
            "min7": "m7",
            "minmaj7": "mMaj7",
            "7": "7",
            "dim": "dim",
            "aug": "aug",
            "sus2": "sus2",
            "sus4": "sus4",
            "dim7": "dim7",
            "hdim7": "m7b5",
            "min6": "m6",
            "maj6": "6",
        }
        suffix = mapping.get(quality, "")
        if quality in mapping:
            return f"{root}{suffix}"
    chord = parse(text)
    return text if chord is None else f"{chord.root}{'' if chord.quality == 'maj' else ('m' if chord.quality == 'min' else chord.quality)}"


def _window_confidence_from_scores(row: np.ndarray) -> float:
    """Top-1 minus top-2 posterior margin for one window of log-probs."""
    return _window_confidence(np.asarray(row, dtype=np.float64))


def _cqt_features(audio_path: Path) -> tuple[np.ndarray, float, float]:
    import librosa

    wav, sr = librosa.load(str(audio_path), sr=_SONG_HZ, mono=True)
    if wav.size < int(sr * 0.2):
        raise ValueError("audio too short for BTC features")
    chunks: list[np.ndarray] = []
    cursor = 0
    window = int(sr * _INST_LEN)
    while cursor + window < wav.size:
        piece = librosa.cqt(
            wav[cursor : cursor + window],
            sr=sr,
            n_bins=_N_BINS,
            bins_per_octave=_BINS_PER_OCTAVE,
            hop_length=_HOP,
        )
        chunks.append(piece)
        cursor += window
    tail = librosa.cqt(
        wav[cursor:],
        sr=sr,
        n_bins=_N_BINS,
        bins_per_octave=_BINS_PER_OCTAVE,
        hop_length=_HOP,
    )
    chunks.append(tail)
    feature = np.concatenate(chunks, axis=1)
    feature = np.log(np.abs(feature) + 1e-6)
    feature_per_second = _INST_LEN / float(_TIMESTEP)
    duration = float(wav.size) / float(sr)
    return feature, feature_per_second, duration


def _numpy_checkpoint_allowlist() -> list[object]:
    """NumPy globals the pinned BTC checkpoint pickles for mean/std.

    PyTorch's weights_only unpickler matches allowlist entries by the
    ``module.name`` string in the pickle, so reconstruct/scalar must be
    registered as ``(object, "qualified.name")`` tuples.
    """
    allow: list[object] = [np.ndarray, np.dtype]
    for scalar in (
        np.bool_,
        np.int8,
        np.int16,
        np.int32,
        np.int64,
        np.uint8,
        np.uint16,
        np.uint32,
        np.uint64,
        np.float16,
        np.float32,
        np.float64,
        np.complex64,
        np.complex128,
    ):
        allow.append(scalar)
        allow.append(type(np.dtype(scalar)))
    for module_name in ("numpy.core.multiarray", "numpy._core.multiarray"):
        try:
            module = __import__(module_name, fromlist=["_reconstruct", "scalar"])
        except ImportError:
            continue
        reconstruct = getattr(module, "_reconstruct", None)
        scalar_fn = getattr(module, "scalar", None)
        if reconstruct is not None:
            allow.append((reconstruct, f"{module_name}._reconstruct"))
        if scalar_fn is not None:
            allow.append((scalar_fn, f"{module_name}.scalar"))
    return allow


def _load_model(weight_path: Path):
    import torch

    from audio_to_tab.btc.btc_model import BTC_model

    device = torch.device("cpu")
    model = BTC_model(config=dict(_MODEL_CONFIG)).to(device)
    safe_globals = getattr(torch.serialization, "safe_globals", None)
    if safe_globals is None:
        raise RuntimeError("PyTorch build lacks weights_only safe_globals")
    try:
        with safe_globals(_numpy_checkpoint_allowlist()):
            checkpoint = torch.load(str(weight_path), map_location=device, weights_only=True)
    except Exception as exc:
        raise RuntimeError(f"BTC checkpoint refused weights_only load: {exc}") from exc
    mean = np.asarray(checkpoint["mean"], dtype=np.float64)
    std = np.asarray(checkpoint["std"], dtype=np.float64)
    model.load_state_dict(checkpoint["model"])
    model.eval()
    return model, mean, std, device


def _predict_frame_scores(
    feature: np.ndarray,
    mean: np.ndarray,
    std: np.ndarray,
    model,
    device,
) -> np.ndarray:
    """Return (frames, num_chords) log-softmax scores. Does not edit vendored BTC."""
    import torch
    import torch.nn.functional as F

    frames = feature.T  # (time, bins)
    frames = (frames - mean) / (std + 1e-9)
    n_timestep = _TIMESTEP
    num_pad = (n_timestep - (frames.shape[0] % n_timestep)) % n_timestep
    if num_pad:
        frames = np.pad(frames, ((0, num_pad), (0, 0)), mode="constant")
    num_instance = frames.shape[0] // n_timestep
    rows: list[np.ndarray] = []
    with torch.no_grad():
        tensor = torch.tensor(frames, dtype=torch.float32).unsqueeze(0).to(device)
        for block in range(num_instance):
            chunk = tensor[:, n_timestep * block : n_timestep * (block + 1), :]
            self_attn_output, _ = model.self_attn_layers(chunk)
            logits = model.output_layer.output_projection(self_attn_output)
            log_probs = F.log_softmax(logits, dim=-1).squeeze(0).cpu().numpy()
            for step in range(n_timestep):
                absolute = n_timestep * block + step
                if absolute >= frames.shape[0] - num_pad and block == num_instance - 1:
                    break
                rows.append(np.asarray(log_probs[step], dtype=np.float64))
    if not rows:
        return np.zeros((0, len(_IDX2CHORD)), dtype=np.float64)
    return np.stack(rows, axis=0)


def _frame_windows(n_frames: int, time_unit: float, duration: float) -> list[tuple[float, float]]:
    windows: list[tuple[float, float]] = []
    for index in range(n_frames):
        start = min(duration, time_unit * index)
        end = min(duration, time_unit * (index + 1))
        if end <= start and index == n_frames - 1:
            end = duration
        if end > start:
            windows.append((start, end))
        elif not windows:
            windows.append((0.0, duration))
    if windows and windows[-1][1] < duration:
        start, _ = windows[-1]
        windows[-1] = (start, duration)
    return windows


def _pool_scores_to_beats(
    scores: np.ndarray,
    *,
    time_unit: float,
    duration: float,
    beats: Sequence[float],
) -> tuple[np.ndarray, list[tuple[float, float]]]:
    boundaries, _tolerance = _boundaries(beats, duration)
    windows = [(boundaries[i], boundaries[i + 1]) for i in range(len(boundaries) - 1)]
    if not windows:
        return scores, _frame_windows(scores.shape[0], time_unit, duration)
    pooled: list[np.ndarray] = []
    kept: list[tuple[float, float]] = []
    n_frames = scores.shape[0]
    for start, end in windows:
        if end <= start:
            continue
        first = max(0, min(n_frames, int(np.floor(start / time_unit + 1e-9))))
        last = max(first + 1, min(n_frames, int(np.ceil(end / time_unit - 1e-9))))
        pooled.append(scores[first:last].mean(axis=0))
        kept.append((float(start), float(end)))
    if not pooled:
        return scores, _frame_windows(n_frames, time_unit, duration)
    return np.stack(pooled, axis=0), kept


def _smooth_scores(
    scores: np.ndarray,
    *,
    time_unit: float,
    duration: float,
    beats: Sequence[float] = (),
    downbeats: Sequence[float] | None = None,
    meter: int = 4,
) -> tuple[list[int], np.ndarray, list[tuple[float, float]]]:
    """Beat-pool (when possible) then Viterbi-smooth BTC log-probs.

    Returns ``(path_indices, window_scores, windows)``.
    """
    matrix = np.asarray(scores, dtype=np.float64)
    if matrix.ndim != 2 or matrix.shape[0] == 0:
        return [], matrix.reshape(0, matrix.shape[-1] if matrix.ndim == 2 else 0), []

    valid_beats = [
        float(beat)
        for beat in beats
        if isinstance(beat, (int, float)) and np.isfinite(float(beat)) and 0.0 < float(beat) < duration
    ]
    if len(valid_beats) >= 2:
        window_scores, windows = _pool_scores_to_beats(
            matrix,
            time_unit=time_unit,
            duration=duration,
            beats=valid_beats,
        )
    else:
        window_scores = matrix
        windows = _frame_windows(matrix.shape[0], time_unit, duration)
        if len(windows) != window_scores.shape[0]:
            # Keep scores and windows aligned if duration rounding shortens the tail.
            count = min(len(windows), window_scores.shape[0])
            window_scores = window_scores[:count]
            windows = windows[:count]

    meter = max(1, int(meter or 4))
    downbeat_times = tuple(downbeats or ())
    beat_times = tuple(valid_beats)
    _, tolerance = _boundaries(valid_beats, duration) if valid_beats else ( [0.0, duration], 0.08 )
    penalties = np.full(len(windows), _BTC_CHANGE_PENALTY + _OFF_DOWNBEAT_PENALTY, dtype=np.float64)
    for index, (start, _end) in enumerate(windows):
        if _is_downbeat(
            start,
            downbeats=downbeat_times,
            beats=beat_times,
            meter=meter,
            tolerance=tolerance,
        ):
            penalties[index] = _BTC_CHANGE_PENALTY - _ON_DOWNBEAT_BONUS
    path = _viterbi(window_scores, penalties)
    return path, window_scores, windows


def _indices_to_events(
    indices: Sequence[int],
    *,
    windows: Sequence[tuple[float, float]],
    confidences: Sequence[float] | None = None,
    bass_vectors: Sequence[np.ndarray] | None = None,
    # Backward-compatible kwargs used by older call sites / tests.
    time_unit: float | None = None,
    duration: float | None = None,
) -> list[ChordEvent]:
    """Collapse consecutive identical labels before the min-duration merge.

    Frame windows are often shorter than ``_MIN_EVENT_SEC``. Dropping them
    individually would delete a held chord; collapse first, then merge.
    """
    if not indices:
        return []
    if not windows and time_unit is not None and duration is not None:
        windows = _frame_windows(len(indices), float(time_unit), float(duration))
    if len(windows) != len(indices):
        count = min(len(windows), len(indices))
        indices = list(indices)[:count]
        windows = list(windows)[:count]
    if not windows:
        return []

    events: list[ChordEvent] = []
    run_start = 0
    prev = int(indices[0])

    def _emit(start_index: int, end_index: int, label_index: int) -> None:
        start = float(windows[start_index][0])
        end = float(windows[end_index - 1][1])
        if end <= start:
            return
        symbol = _mir_eval_to_symbol(
            _IDX2CHORD[label_index] if 0 <= label_index < len(_IDX2CHORD) else "N"
        )
        if bass_vectors is not None and start_index < len(bass_vectors) and symbol != "N":
            # Slash from the first window of the run (stable bass peak).
            symbol = _slash_bass(symbol, np.asarray(bass_vectors[start_index], dtype=np.float64))
        if confidences is not None:
            run_conf = [float(confidences[i]) for i in range(start_index, end_index) if i < len(confidences)]
            confidence = float(min(run_conf)) if run_conf else 0.0
        else:
            confidence = 0.0
        simple, medium = _decorate(symbol) if symbol != "N" else ("N", "N")
        events.append(
            ChordEvent(
                start=start,
                end=end,
                symbol=symbol,
                confidence=confidence,
                simple=simple,
                medium=medium,
            )
        )

    for index in range(1, len(indices)):
        current = int(indices[index])
        if current == prev:
            continue
        _emit(run_start, index, prev)
        run_start = index
        prev = current
    _emit(run_start, len(indices), prev)
    return _merge_events(events)


def _bass_vectors_for_windows(
    audio_path: Path,
    windows: Sequence[tuple[float, float]],
    *,
    bass_path: Path | None,
) -> list[np.ndarray] | None:
    if bass_path is None or not Path(bass_path).is_file() or not windows:
        return None
    try:
        import librosa

        from audio_to_tab.chords import _BINS_PER_OCTAVE, _bass_chroma, estimate_tuning_semitones
        from audio_to_tab.chords import _HOP as _CHROMA_HOP
    except Exception:
        return None
    try:
        y, sr = librosa.load(str(audio_path), sr=_SONG_HZ, mono=True)
        if y.size < int(sr * 0.2):
            return None
        tuning = estimate_tuning_semitones(y, int(sr))
        tuning_bins = tuning * (_BINS_PER_OCTAVE / 12.0)
        chroma = _bass_chroma(y, int(sr), bass_path=Path(bass_path), tuning_bins=tuning_bins)
    except Exception:
        logger.debug("BTC slash bass chroma failed", exc_info=True)
        return None
    vectors: list[np.ndarray] = []
    n_frames = chroma.shape[1]
    for start, end in windows:
        first = max(0, min(n_frames - 1, int(librosa.time_to_frames(start, sr=sr, hop_length=_CHROMA_HOP))))
        last = max(first + 1, min(n_frames, int(librosa.time_to_frames(end, sr=sr, hop_length=_CHROMA_HOP)) + 1))
        vectors.append(chroma[:, first:last].mean(axis=1))
    return vectors


def detect_chords_btc(
    audio_path: Path,
    *,
    model_dir: Path | None = None,
    progress: Callable[[str], None] | None = None,
    beats: Sequence[float] = (),
    downbeats: Sequence[float] | None = None,
    beats_per_measure: int = 4,
    bass_path: Path | None = None,
) -> list[ChordEvent] | None:
    """Run BTC maj/min recognition. Returns ``None`` when unavailable so callers fall back."""
    path = Path(audio_path)
    if not path.is_file():
        return None
    try:
        import torch  # noqa: F401
    except Exception:
        logger.info("BTC chord model skipped: torch not installed")
        return None
    weight_dir = Path(model_dir) if model_dir is not None else default_chord_model_dir()
    weight = weight_dir / BTC_WEIGHT_NAME
    if not weight.is_file():
        return None
    try:
        if file_sha256(weight) != BTC_WEIGHT_SHA256:
            logger.warning("BTC weight hash mismatch at %s; refusing to load", weight)
            return None
    except OSError:
        return None
    try:
        _notify(progress, "chords: BTC feature extract")
        feature, time_unit, duration = _cqt_features(path)
        _notify(progress, "chords: BTC inference")
        model, mean, std, device = _load_model(weight)
        scores = _predict_frame_scores(feature, mean, std, model, device)
        path_indices, window_scores, windows = _smooth_scores(
            scores,
            time_unit=time_unit,
            duration=duration,
            beats=beats,
            downbeats=downbeats,
            meter=beats_per_measure,
        )
        confidences = [_window_confidence_from_scores(row) for row in window_scores]
        bass_vectors = _bass_vectors_for_windows(path, windows, bass_path=bass_path)
        events = _indices_to_events(
            path_indices,
            windows=windows,
            confidences=confidences,
            bass_vectors=bass_vectors,
        )
        _notify(progress, f"chords: BTC {len(events)} segments")
        return events
    except Exception:
        logger.warning("BTC chord recognition failed; falling back to templates", exc_info=True)
        return None


__all__ = [
    "BTC_WEIGHT_NAME",
    "BTC_WEIGHT_SHA256",
    "BTC_WEIGHT_URL",
    "chord_model_available",
    "chord_model_requested",
    "default_chord_model_dir",
    "detect_chords_btc",
    "ensure_chord_model",
]
