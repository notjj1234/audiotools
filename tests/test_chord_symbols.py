"""One grammar: parse, render, the basic product name, capo, and chord tones."""

from __future__ import annotations

import re

import pytest

from audio_to_tab.chord_symbols import (
    PITCHES,
    TEMPLATE_QUALITIES,
    Chord,
    basic_from_text,
    basic_symbol,
    capo_shape,
    chord_tones,
    parse,
    parse_render,
    render,
    transpose,
)
from audio_to_tab.chords import _TEMPLATE_NAMES


def test_round_trip_every_template():
    assert len(_TEMPLATE_NAMES) == 12 * len(TEMPLATE_QUALITIES)
    for name in _TEMPLATE_NAMES:
        chord = parse(name)
        assert chord is not None
        assert chord.quality in TEMPLATE_QUALITIES
        assert render(chord) == name
        assert basic_symbol(chord) == name


def test_flats_in_sharps_out_and_slash_bass():
    assert render(parse("Bb")) == "A#"
    assert render(parse("Bbm7")) == "A#m7"
    assert render(parse("Eb")) == "D#"
    chord = parse("C/E")
    assert chord is not None
    assert chord.bass == "E"
    assert render(chord) == "C/E"


def test_garbage_is_none():
    assert parse("H") is None
    assert parse("N") is None
    assert parse("") is None
    assert parse(None) is None
    assert parse("not-a-chord") is None
    assert parse("C/E/G") is None
    assert parse_render("Cadd9") is None
    assert parse("Cadd9") is not None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("C", "C"),
        ("Cmaj7", "C"),
        ("F#7", "F#"),
        ("Bb", "A#"),
        ("Bbm7", "A#m"),
        ("E5", "E"),
        ("Csus4", "C"),
        ("Csus2", "C"),
        ("Caug", "C"),
        ("C6", "C"),
        ("Cadd9", "C"),
        ("C/E", "C"),
        ("G7b9/F", "G"),
        ("Bdim", "Bm"),
        ("F#m7b5", "F#m"),
        ("Cdim7", "Cm"),
        ("CmMaj7", "Cm"),
        ("Dm6", "Dm"),
        ("Am/G", "Am"),
        ("N", "N"),
        ("", "N"),
        (None, "N"),
        ("not-a-chord", "not-a-chord"),
    ],
)
def test_basic_name_is_root_plus_optional_m_in_sharps(raw, expected):
    assert basic_from_text(raw) == expected


def test_basic_symbol_ignores_extension_and_bass():
    assert basic_symbol(Chord("G", "7b9", "F")) == "G"
    assert basic_symbol(Chord("C", "maj9")) == "C"
    assert basic_symbol(Chord("A", "m9", "G")) == "Am"


def test_capo_matches_frontend_shapes():
    assert render(capo_shape(parse("G"), 2)) == "F"
    assert render(capo_shape(parse("Am"), 2)) == "Gm"
    assert render(capo_shape(parse("G/B"), 2)) == "F/A"


def test_chord_tones_and_transpose():
    assert chord_tones(parse("Cmaj7")) == ("C", "E", "G", "B")
    assert chord_tones(parse("Dm7")) == ("D", "F", "A", "C")
    assert chord_tones(parse("C/E")) == ("C", "E", "G")
    assert render(transpose(parse("C"), 2)) == "D"
    assert render(transpose(parse("C/E"), 1)) == "C#/F"
    assert set(PITCHES) == {render(transpose(parse("C"), step)) for step in range(12)}


def test_auto_spelling_follows_the_key():
    assert render(parse("A#"), spelling="auto", key="F") == "Bb"
    assert render(parse("A#"), spelling="auto", key="Dm") == "Bb"
    assert render(parse("A#"), spelling="auto", key="D") == "A#"
    assert render(parse("A#"), spelling="sharp") == "A#"


def test_btc_mir_eval_symbols_are_basic_names():
    """Every symbol `_mir_eval_to_symbol` can emit is a root plus optional m."""
    from audio_to_tab.chord_neural import _mir_eval_to_symbol

    labels = (
        "C",
        "C:min",
        "C:maj",
        "C:maj7",
        "C:min7",
        "C:minmaj7",
        "C:7",
        "C:dim",
        "C:aug",
        "C:sus2",
        "C:sus4",
        "C:dim7",
        "C:hdim7",
        "C:min6",
        "C:maj6",
        "G#:min",
        "N",
        "X",
    )
    for label in labels:
        symbol = _mir_eval_to_symbol(label)
        assert re.fullmatch(r"[A-G]#?m?|N", symbol), (label, symbol)
