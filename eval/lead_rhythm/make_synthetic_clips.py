#!/usr/bin/env python3
"""Generate synthetic Lead/Rhythm eval clips under eval/lead_rhythm/clips/ (gitignored).

Does not download audio. Useful for smoke-scoring the post-process and for the
mild-pan binary-pass case documented in README.md / RESEARCH.md.

  export PYTHONPATH=src:.
  python eval/lead_rhythm/make_synthetic_clips.py
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

SR = 44100
DUR = 2.0


def _write_stereo(path: Path, left: np.ndarray, right: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stereo = np.column_stack([left, right]).astype(np.float32)
    sf.write(str(path), stereo, SR, subtype="PCM_16")


def _write_mono_as_stereo(path: Path, mono: np.ndarray) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    stereo = np.column_stack([mono, mono]).astype(np.float32)
    sf.write(str(path), stereo, SR, subtype="PCM_16")


def hard_pan(clips: Path) -> dict:
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    lead = np.sin(2 * np.pi * 659.25 * t)  # E5
    rhythm = np.sin(2 * np.pi * 146.83 * t)  # D3
    guitar = clips / "hard_pan_example" / "guitar.wav"
    _write_stereo(guitar, lead, rhythm)
    _write_mono_as_stereo(guitar.parent / "gt_lead.wav", lead)
    _write_mono_as_stereo(guitar.parent / "gt_rhythm.wav", rhythm)
    return {
        "id": "hard_pan_example",
        "path": "hard_pan_example/guitar.wav",
        "gt_parts": 2,
        "gt_lead": "left",
        "mix_type": "hard_pan",
        "gt_lead_wav": "hard_pan_example/gt_lead.wav",
        "gt_rhythm_wav": "hard_pan_example/gt_rhythm.wav",
    }


def mild_pan(clips: Path) -> dict:
    """55/45 pan of distinct lead/rhythm tones (corr ~0.98) — binary-pass case."""
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    lead = np.sin(2 * np.pi * 659.25 * t)
    rhythm = np.sin(2 * np.pi * 146.83 * t)
    left = 0.55 * lead + 0.45 * rhythm
    right = 0.45 * lead + 0.55 * rhythm
    guitar = clips / "mild_pan_example" / "guitar.wav"
    _write_stereo(guitar, left, right)
    _write_mono_as_stereo(guitar.parent / "gt_lead.wav", lead)
    _write_mono_as_stereo(guitar.parent / "gt_rhythm.wav", rhythm)
    return {
        "id": "mild_pan_example",
        "path": "mild_pan_example/guitar.wav",
        "gt_parts": 2,
        "gt_lead": "a",
        "mix_type": "mild_pan",
        "gt_lead_wav": "mild_pan_example/gt_lead.wav",
        "gt_rhythm_wav": "mild_pan_example/gt_rhythm.wav",
    }


def mono_single(clips: Path) -> dict:
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    mono = np.sin(2 * np.pi * 440.0 * t)
    guitar = clips / "mono_single" / "guitar.wav"
    _write_stereo(guitar, mono, mono)
    return {
        "id": "mono_single",
        "path": "mono_single/guitar.wav",
        "gt_parts": 1,
        "gt_lead": None,
        "mix_type": "mono_single",
    }


def centered_overlap(clips: Path) -> dict:
    """Same-register-ish overlap, L≡R — not a pass gate for trained separators."""
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    a = np.sin(2 * np.pi * 330.0 * t)
    b = np.sin(2 * np.pi * 349.0 * t)
    mix = 0.5 * a + 0.5 * b
    guitar = clips / "centered_overlap" / "guitar.wav"
    _write_stereo(guitar, mix, mix)
    return {
        "id": "centered_overlap",
        "path": "centered_overlap/guitar.wav",
        "gt_parts": 2,
        "gt_lead": None,
        "mix_type": "centered_overlap",
    }


def double_track_wide(clips: Path) -> dict:
    t = np.linspace(0, DUR, int(SR * DUR), endpoint=False)
    rng = np.random.RandomState(0)
    take = np.sin(2 * np.pi * 220.3 * t) + 0.02 * rng.randn(len(t))
    left = 0.55 * take
    right = 0.45 * take
    guitar = clips / "double_track_wide" / "guitar.wav"
    _write_stereo(guitar, left, right)
    return {
        "id": "double_track_wide",
        "path": "double_track_wide/guitar.wav",
        "gt_parts": 1,
        "gt_lead": None,
        "mix_type": "double_track",
    }


def _harmonic_tone(freq: float, dur: float, *, vib: float = 0.0, bend: float = 0.0) -> np.ndarray:
    """Guitar-ish tone: 6 decaying harmonics, optional vibrato / 1-semitone-style bend."""
    t = np.arange(int(dur * SR)) / SR
    inst = freq * (1.0 + vib * np.sin(2 * np.pi * 5.5 * t))
    inst = inst * 2.0 ** ((bend * np.clip(t / 0.15, 0.0, 1.0)) / 12.0)
    phase = 2 * np.pi * np.cumsum(inst) / SR
    return sum((0.6**k) * np.sin((k + 1) * phase) for k in range(6))


def strummed_chords(dur: float, seed: int = 0) -> np.ndarray:
    """Four-chord progression, a strum every 0.5 s with a fast decay (rhythm-like)."""
    rng = np.random.RandomState(seed)
    out = np.zeros(int(dur * SR))
    progression = [[110, 165, 220, 277], [98, 147, 196, 247], [123, 185, 247, 311], [82, 123, 165, 208]]
    step = 0.5
    i = 0
    while i * step < dur:
        chord = progression[(i // 4) % 4]
        a = int(i * step * SR)
        n = min(int(step * SR), len(out) - a)
        env = np.exp(-np.arange(n) / SR * 4.0)
        seg = sum(_harmonic_tone(f * (1 + 0.002 * rng.randn()), n / SR) for f in chord)[:n]
        out[a : a + n] += 0.15 * seg * env
        i += 1
    return out


def single_note_solo(dur: float) -> np.ndarray:
    """Single-note line in a higher register with vibrato and bends (lead-like)."""
    out = np.zeros(int(dur * SR))
    notes = [440, 494, 523, 587, 659, 587, 523, 494, 440, 392]
    step = 0.4
    i = 0
    while i * step < dur:
        a = int(i * step * SR)
        n = min(int(step * SR), len(out) - a)
        seg = _harmonic_tone(
            notes[i % len(notes)],
            n / SR,
            vib=0.006 if i % 3 == 0 else 0.0,
            bend=1.0 if i % 5 == 0 else 0.0,
        )[:n]
        out[a : a + n] += 0.35 * seg * np.exp(-np.arange(n) / SR * 1.0)
        i += 1
    return out


def sung_line(dur: float) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    f = 220 * (1 + 0.01 * np.sin(2 * np.pi * 4 * t))
    return 0.2 * np.sin(2 * np.pi * np.cumsum(f) / SR) * (0.6 + 0.4 * np.sin(2 * np.pi * 0.5 * t) ** 2)


def role_switch_song(
    layout: list[tuple[str, float]], seed: int = 0
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    One guitar track that changes role over time.

    ``layout`` is a list of (kind, seconds), kind in ``chords`` (strumming with
    vocals), ``solo`` (single-note lead, vocals silent) or ``lead_only`` (single
    notes with no vocals). Returns (guitar mono, vocals mono, gt lead, gt rhythm).
    """
    g, v, lead, rhythm = [], [], [], []
    for k, (kind, dur) in enumerate(layout):
        n = int(dur * SR)
        chords = strummed_chords(dur, seed + k) if kind == "chords" else np.zeros(n)
        solo = single_note_solo(dur) if kind in ("solo", "lead_only") else np.zeros(n)
        vocal = sung_line(dur) if kind == "chords" else np.zeros(n)
        g.append(chords + solo)
        v.append(vocal)
        lead.append(solo)
        rhythm.append(chords)
    return (
        np.concatenate(g).astype(np.float32),
        np.concatenate(v).astype(np.float32),
        np.concatenate(lead).astype(np.float32),
        np.concatenate(rhythm).astype(np.float32),
    )


def role_switch(clips: Path) -> dict:
    """Verse strumming → solo (vocals stop) → verse, all on ONE centered guitar track."""
    guitar_m, vocals, lead, rhythm = role_switch_song([("chords", 20), ("solo", 15), ("chords", 20)])
    guitar = clips / "role_switch" / "guitar.wav"
    _write_mono_as_stereo(guitar, guitar_m)
    _write_mono_as_stereo(guitar.parent / "vocals.wav", vocals)
    _write_mono_as_stereo(guitar.parent / "gt_lead.wav", lead)
    _write_mono_as_stereo(guitar.parent / "gt_rhythm.wav", rhythm)
    return {
        "id": "role_switch",
        "path": "role_switch/guitar.wav",
        "vocals": "role_switch/vocals.wav",
        "gt_parts": 2,
        "gt_lead": None,
        "mix_type": "role_switch",
        "gt_lead_wav": "role_switch/gt_lead.wav",
        "gt_rhythm_wav": "role_switch/gt_rhythm.wav",
    }


def chords_only(clips: Path) -> dict:
    """One rhythm part with vocals throughout: must stay a single Guitar stem."""
    guitar_m, vocals, _, _ = role_switch_song([("chords", 50)], seed=5)
    guitar = clips / "chords_only" / "guitar.wav"
    _write_mono_as_stereo(guitar, guitar_m)
    _write_mono_as_stereo(guitar.parent / "vocals.wav", vocals)
    return {
        "id": "chords_only",
        "path": "chords_only/guitar.wav",
        "vocals": "chords_only/vocals.wav",
        "gt_parts": 1,
        "gt_lead": None,
        "mix_type": "single_role",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--clips-dir",
        type=Path,
        default=Path(__file__).resolve().parent / "clips",
    )
    parser.add_argument(
        "--write-manifest",
        type=Path,
        default=None,
        help="Optional path to write a ready-to-run manifest.json",
    )
    args = parser.parse_args()
    clips = args.clips_dir
    clips.mkdir(parents=True, exist_ok=True)

    entries = [
        hard_pan(clips),
        mild_pan(clips),
        mono_single(clips),
        centered_overlap(clips),
        double_track_wide(clips),
        role_switch(clips),
        chords_only(clips),
    ]
    print(f"Wrote {len(entries)} clip trees under {clips}")
    if args.write_manifest is not None:
        import json

        args.write_manifest.write_text(
            json.dumps({"clips": entries}, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {args.write_manifest}")


if __name__ == "__main__":
    main()
