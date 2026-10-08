"""Tests for the pure note-rendering helper used by the main table."""

from surface_navigator.main_gui_widget import render_note
from surface_navigator.models import SurfaceSpot
from surface_navigator.spot_flags import SurfaceSpotFlags

# Fuel-pump marker (U+26FD) shown for tritium rings in the note column.
TRITIUM_RING_NOTE = "\u26FD Trit Ring"


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


def test_render_note_tritium_ring_marker():
    # Tritium rings carry no note, but the fuel-pump marker makes them stand out.
    spot = SurfaceSpot(mineral_type="tritium", flags=SurfaceSpotFlags.TRITIUM_RING_PRESENT)
    assert render_note(spot) == TRITIUM_RING_NOTE


def test_render_note_tritium_wins_over_clock():
    # A ring is not a temporary mark; the tritium marker takes precedence.
    spot = SurfaceSpot(
        notes="Scan at 3312-01-01 00:00:00",
        flags=SurfaceSpotFlags.TRITIUM_RING_PRESENT | SurfaceSpotFlags.IS_TEMPORARY_MARK,
    )
    assert render_note(spot) == TRITIUM_RING_NOTE


def test_render_note_tritium_uses_fuel_pump_glyph():
    # Pin the exact glyph: U+26FD FUEL PUMP, not U+26BE (BASEBALL) or U+2622
    # (RADIATION) - the symbol is the whole point of the marker.
    assert TRITIUM_RING_NOTE.startswith("\u26FD")
    assert "\u26BE" not in TRITIUM_RING_NOTE
    assert "\u2622" not in TRITIUM_RING_NOTE
