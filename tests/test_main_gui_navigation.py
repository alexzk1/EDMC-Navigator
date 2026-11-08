"""Tests for the manual-coordinate navigation wiring in ``MainGUIWidget``.

Neither a full ``tk.Frame`` nor a real overlay needs instantiating: the widget
is built via ``__new__`` and the handful of attributes the methods touch are
replaced with light fakes (a fake tree, entry and overlay). The DB is real where
a navigation mark actually has to be written.
"""

import math
import tkinter as tk
from unittest.mock import patch

# ``icons_cache`` builds ``PhotoImage``s at import time, which needs a default
# Tk root to exist first. Create one here -- this mirrors the app, where the GUI
# root is created before any icon is loaded.
tk.Tk()

from surface_navigator.coordinate import CoordinateFormatter
from surface_navigator.main_gui_widget import (
    MANUAL_NAV_DEDUP_METERS,
    MainGUIWidget,
)
from surface_navigator.models import StarSystem, SurfaceSpot
from surface_navigator.player_location import (
    DEFAULT_PLANET_RADIUS,
    PlayerLocation,
    SurfacePoint,
)
from surface_navigator.spot_flags import SurfaceSpotFlags

# Columns in the exact order ``MainGUIWidget`` uses.
COLUMNS = ("#", "dist", "mineral", "body", "note", "rigs", "nav", "lat", "lon", "db_id")


class FakeEntry:
    """Records delete/insert and returns the last inserted text from ``get``."""

    def __init__(self, text: str = "") -> None:
        self._text = text
        self.calls: list = []

    def get(self) -> str:
        return self._text

    def delete(self, start: object, end: object) -> None:
        self.calls.append(("delete", start, end))
        self._text = ""

    def insert(self, index: object, text: str) -> None:
        self.calls.append(("insert", index, text))
        self._text = text

    def selection_range(self, start: object, end: object) -> None:
        self.calls.append(("selection_range", start, end))

    def focus(self) -> None:
        self.calls.append(("focus",))


class FakeTree:
    """A minimal Treeview stand-in: rows, a selection and the ``columns`` key."""

    def __init__(self, rows: dict[str, tuple]) -> None:
        self._rows = rows
        self._selection: list[str] = []

    def __getitem__(self, key: str):
        if key == "columns":
            return list(COLUMNS)
        raise KeyError(key)

    def item(self, item: str, option: str | None = None):
        if option == "values":
            return self._rows[item]
        raise NotImplementedError

    def selection(self) -> list[str]:
        return self._selection


class FakeOverlay:
    def __init__(self, navigable: bool = True) -> None:
        self.navigable = navigable
        self.destination = None
        self.navigate_calls: list[SurfacePoint] = []

    def navigate_to(self, point):
        self.navigate_calls.append(point)
        self.destination = point

    def is_navigating(self) -> bool:
        return self.navigable and self.destination is not None


def _location() -> PlayerLocation:
    return PlayerLocation(
        star_system=StarSystem(star_name="Alpha"),
        body_name="b4",
        player_coord=SurfacePoint(0.0, 0.0),
        radius_meters=DEFAULT_PLANET_RADIUS,
    )


def _widget(db=None, navigable: bool = True) -> MainGUIWidget:
    w = MainGUIWidget.__new__(MainGUIWidget)
    w.current_location = _location()
    w.current_system = w.current_location.star_system
    w.overlay = FakeOverlay(navigable)
    w.db_manager = db
    w._coord_entry = FakeEntry()
    return w


def _row(lat: float, lon: float, item: str = "row1") -> tuple:
    values = list(COLUMNS)
    values[7] = lat  # lat
    values[8] = lon  # lon
    return tuple(values)


# ---- _on_table_select -------------------------------------------------------


def test_table_select_overwrites_field_with_full_precision():
    w = _widget()
    w._tree = FakeTree({"row1": _row(1.23456789, 2.98765432)})
    w._tree._selection = ["row1"]

    w._on_table_select()

    assert w._coord_entry.get() == CoordinateFormatter.to_string(
        SurfacePoint(1.23456789, 2.98765432)
    )
    # The field was cleared and refilled (delete then insert).
    assert ("delete", 0, tk.END) in w._coord_entry.calls
    assert ("focus",) in w._coord_entry.calls


def test_table_select_empty_selection_leaves_field():
    w = _widget()
    w._coord_entry = FakeEntry('{"lat": 5.0, "lon": 6.0}')  # manually entered
    w._tree = FakeTree({})

    w._on_table_select()

    # A deselection must not erase a manually entered coordinate.
    assert w._coord_entry.get() == '{"lat": 5.0, "lon": 6.0}'


# ---- _on_navigate -----------------------------------------------------------


def test_navigate_resets_on_empty_field():
    """An empty field means "go nowhere": cancel any active navigation."""
    w = _widget()
    w._coord_entry = FakeEntry("")
    w._tree = FakeTree({})

    w._on_navigate()

    assert w.overlay.navigate_calls == [None]


def test_navigate_resets_on_unparseable_field():
    """An unparseable field also cancels the current navigation."""
    w = _widget()
    w._coord_entry = FakeEntry("not coordinates")
    w._tree = FakeTree({})

    w._on_navigate()

    assert w.overlay.navigate_calls == [None]


def test_navigate_saved_spot_does_not_record_mark(db):
    """Navigating to the currently selected row is just navigation - no mark."""
    w = _widget(db=db)
    db.add_spot(SurfaceSpot(star_system="Alpha", body_name="b4", latitude=10.0, longitude=20.0))
    w._tree = FakeTree({"row1": _row(10.0, 20.0)})
    w._tree._selection = ["row1"]
    # Field as if it had just been filled by the table click.
    w._coord_entry = FakeEntry(CoordinateFormatter.to_string(SurfacePoint(10.0, 20.0)))

    w._on_navigate()

    assert w.overlay.navigate_calls == [SurfacePoint(10.0, 20.0)]
    # No temporary mark for navigating to a saved bookmark.
    marks = [s for s in db.get_system_spots("Alpha") if SurfaceSpotFlags.IS_TEMPORARY_MARK in s.flags]
    assert marks == []


def test_navigate_manual_records_temporary_mark(db):
    """Navigating to a point that is not the selected row records a mark."""
    w = _widget(db=db)
    db.add_spot(SurfaceSpot(star_system="Alpha", body_name="b4", latitude=10.0, longitude=20.0))
    w._tree = FakeTree({"row1": _row(10.0, 20.0)})
    w._tree._selection = ["row1"]
    # User typed a *different* point manually.
    w._coord_entry = FakeEntry(CoordinateFormatter.to_string(SurfacePoint(11.0, 21.0)))

    w._on_navigate()

    assert w.overlay.navigate_calls == [SurfacePoint(11.0, 21.0)]
    marks = [s for s in db.get_system_spots("Alpha") if SurfaceSpotFlags.IS_TEMPORARY_MARK in s.flags]
    assert len(marks) == 1
    assert marks[0].latitude == 11.0
    assert marks[0].longitude == 21.0
    assert "manually navigated at" in marks[0].notes


def test_navigate_manual_within_dedup_does_not_record(db):
    """A manual point already within NAV_DEDUP_METERS of an existing spot is not
    double-recorded."""
    w = _widget(db=db)
    db.add_spot(SurfaceSpot(star_system="Alpha", body_name="b4", latitude=10.0, longitude=20.0))
    w._tree = FakeTree({"row1": _row(10.0, 20.0)})
    w._tree._selection = []  # no selection -> definitely manual
    # ~25 m north of the existing spot: inside the dedup radius, so no mark.
    # The offset mirrors the DB's flat-earth degree conversion.
    deg_offset = (MANUAL_NAV_DEDUP_METERS / 2) / DEFAULT_PLANET_RADIUS * (180 / math.pi)
    near = SurfacePoint(10.0 + deg_offset, 20.0)
    w._coord_entry = FakeEntry(CoordinateFormatter.to_string(near))

    w._on_navigate()

    assert w.overlay.navigate_calls == [near]
    marks = [s for s in db.get_system_spots("Alpha") if SurfaceSpotFlags.IS_TEMPORARY_MARK in s.flags]
    assert marks == []


def test_navigate_overlay_not_installed_shows_error_and_no_mark():
    with patch("surface_navigator.main_gui_widget.messagebox.showwarning") as mock_warn:
        w = _widget(navigable=False)
        w._coord_entry = FakeEntry(CoordinateFormatter.to_string(SurfacePoint(11.0, 21.0)))
        w._tree = FakeTree({})

        w._on_navigate()

        assert mock_warn.called
        # No mark when navigation never actually started.
        assert w.overlay.navigate_calls == [SurfacePoint(11.0, 21.0)]
