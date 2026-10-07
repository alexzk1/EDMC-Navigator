"""Tests for the pure note-rendering helper used by the main table."""

from surface_navigator.main_gui_widget import render_note
from surface_navigator.models import SurfaceSpot
from surface_navigator.spot_flags import SurfaceSpotFlags


def test_render_note_plain_when_no_flag():
    spot = SurfaceSpot(notes="tritium spot")
    assert render_note(spot) == "tritium spot"


def test_render_note_defaults_to_dash():
    assert render_note(SurfaceSpot(notes=None)) == "-"


def test_render_note_prefixes_clock_for_temporary_mark():
    spot = SurfaceSpot(notes="temp here", flags=SurfaceSpotFlags.IS_TEMPORARY_MARK)
    # 🕐 clock face one o'clock followed by the note.
    assert render_note(spot) == f"\U0001F550 temp here"


def test_render_note_clock_with_empty_notes():
    spot = SurfaceSpot(notes=None, flags=SurfaceSpotFlags.IS_TEMPORARY_MARK)
    assert render_note(spot) == f"\U0001F550 -"
