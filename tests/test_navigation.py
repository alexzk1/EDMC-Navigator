"""Tests for the query-builder -> main-widget navigation wiring.

Three pure helpers carry the new logic so neither a full ``Toplevel`` builder
nor a ``MainGUIWidget`` needs instantiating:

* :func:`navigation_target` assembles a navigation target from a results row's
  star, body and surface point -- the three things navigation needs.
* :func:`is_navigable` checks that target against the current position: we can
  only navigate to a spot we are actually standing on.
* :meth:`QueryBuilderWindow._navigable_target` gates the target on two things:
  a navigation callback exists, and the row is a surface spot, not a Tritium
  Ring in space.
"""

import datetime
import tkinter as tk

# ``icons_cache`` builds ``PhotoImage``s at import time, which needs a default
# Tk root to exist first. Create one here -- this mirrors the app, where the GUI
# root is created before any icon is loaded.
_root = tk.Tk()

from surface_navigator.main_gui_widget import is_navigable
from surface_navigator.models import StarSystem, SurfaceSpot
from surface_navigator.player_location import PlayerLocation, SurfacePoint
from surface_navigator.query_builder.builder_window import (
    SORTABLE_RESULT_COLUMNS,
    QueryBuilderWindow,
    navigation_target,
    sort_results,
)
from surface_navigator.spot_flags import SurfaceSpotFlags


def _target(
    system: str = "Sol",
    body: str = "Earth",
    lat: str = "1.0",
    lon: str = "2.0",
) -> PlayerLocation:
    return PlayerLocation(
        star_system=StarSystem(star_name=system),
        body_name=body,
        player_coord=SurfacePoint(float(lat), float(lon)),
    )


def _current(
    system: str = "Sol", body: str = "Earth"
) -> tuple[PlayerLocation, StarSystem]:
    loc = PlayerLocation(
        star_system=StarSystem(star_name=system),
        body_name=body,
        player_coord=SurfacePoint(0.0, 0.0),
    )
    return loc, loc.star_system


# ---- navigation_target -----------------------------------------------------


def test_navigation_target_assembles_all_fields():
    target = navigation_target("Sol", "Earth", SurfacePoint(1.5, -2.5))
    assert target is not None
    assert target.body_name == "Earth"
    assert target.star_system.star_name == "Sol"
    assert target.player_coord == SurfacePoint(1.5, -2.5)


def test_navigation_target_rejects_missing_system():
    assert navigation_target("", "Earth", SurfacePoint(1.0, 2.0)) is None


def test_navigation_target_rejects_missing_body():
    assert navigation_target("Sol", "", SurfacePoint(1.0, 2.0)) is None


# ---- is_navigable ----------------------------------------------------------


def test_is_navigable_true_when_here():
    loc, system = _current()
    assert is_navigable(_target(), loc, system)


def test_is_navigable_false_when_not_on_surface():
    assert is_navigable(_target(), None, StarSystem(star_name="Sol")) is False


def test_is_navigable_false_when_no_system_known():
    loc, _ = _current()
    assert is_navigable(_target(), loc, None) is False


def test_is_navigable_false_in_different_system():
    loc, system = _current(system="Sol")
    assert is_navigable(_target(system="Kepler-442"), loc, system) is False


def test_is_navigable_false_on_different_body():
    loc, system = _current(body="Earth")
    assert is_navigable(_target(body="Europa"), loc, system) is False


def test_is_navigable_false_when_no_coordinates():
    loc, system = _current()
    no_coord = PlayerLocation(
        star_system=StarSystem(star_name="Sol"), body_name="Earth"
    )
    assert is_navigable(no_coord, loc, system) is False


# ---- _navigable_target -----------------------------------------------------


def _navigate(_target: PlayerLocation) -> None:
    pass


def test_navigable_target_none_when_no_callback():
    # No navigation callback wired -- there is nothing to navigate to.
    assert (
        QueryBuilderWindow._navigable_target(
            0, "Sol", "Earth", SurfacePoint(1.0, 2.0), None
        )
        is None
    )


def test_navigable_target_builds_for_surface_spot():
    # A plain surface spot with a callback wired produces a real target.
    target = QueryBuilderWindow._navigable_target(
        0, "Sol", "Earth", SurfacePoint(1.0, 2.0), _navigate
    )
    assert target is not None
    assert target.star_system.star_name == "Sol"
    assert target.body_name == "Earth"
    assert target.player_coord == SurfacePoint(1.0, 2.0)


def test_navigable_target_none_for_tritium_ring():
    # A Tritium Ring is a spot in space, not a surface point -- no target.
    assert (
        QueryBuilderWindow._navigable_target(
            SurfaceSpotFlags.TRITIUM_RING_PRESENT.value,
            "Sol",
            "Earth",
            SurfacePoint(1.0, 2.0),
            _navigate,
        )
        is None
    )


# ---- _format_distance ------------------------------------------------------


def _dist(value: float | None) -> str:
    return QueryBuilderWindow._format_distance(value)  # pyright: ignore[reportPrivateUsage]


def test_format_distance_none_is_em_dash():
    # No current-system coords -> distance unavailable -> uniform dash.
    assert _dist(None) == "—"


def test_format_distance_rounds_to_two_decimals():
    assert _dist(3.0) == "3.00"
    assert _dist(17.320508) == "17.32"
    assert _dist(0.5) == "0.50"


def test_format_coords_joins_lat_lon_one_decimal():
    # Display-only: 1 decimal each, comma-separated. Full precision is kept in
    # the hidden ``_lat`` / ``_lon`` columns, so this never feeds navigation.
    assert QueryBuilderWindow._format_coords(12.345, -45.678) == "12.3, -45.7"  # pyright: ignore[reportPrivateUsage]
    assert QueryBuilderWindow._format_coords(0.0, 0.0) == "0.0, 0.0"  # pyright: ignore[reportPrivateUsage]


# ---- sort_results ----------------------------------------------------------


def _spot(
    system: str,
    body: str,
    *,
    distance: float | None = 0.0,
    mineral: str | None = None,
    notes: str | None = None,
    visit: str | None = None,
    id: int = 0,
) -> SurfaceSpot:
    return SurfaceSpot(
        id=id,
        star_system=system,
        body_name=body,
        mineral_type=mineral,
        notes=notes,
        distance_ly=distance,
        last_visit_time=(
            datetime.datetime.fromisoformat(visit) if visit else None
        ),
    )


def test_sort_results_distance_ascending_then_id():
    spots = [
        _spot("B", "b1", distance=10.0, id=2),
        _spot("A", "b1", distance=3.0, id=9),
        _spot("C", "b1", distance=7.0, id=1),
    ]
    ordered = sort_results(spots, "distance", reverse=False)
    assert [s.star_system for s in ordered] == ["A", "C", "B"]


def test_sort_results_distance_descending():
    spots = [
        _spot("A", "b1", distance=3.0, id=9),
        _spot("B", "b1", distance=10.0, id=2),
    ]
    ordered = sort_results(spots, "distance", reverse=True)
    assert [s.star_system for s in ordered] == ["B", "A"]


def test_sort_results_distance_ties_broken_by_id_ascending():
    spots = [
        _spot("same", "b1", distance=5.0, id=7),
        _spot("same", "b2", distance=5.0, id=3),
    ]
    ordered = sort_results(spots, "distance", reverse=False)
    assert [s.id for s in ordered] == [3, 7]


def test_sort_results_none_distance_sorts_last_both_directions():
    spots = [
        _spot("zero", "b1", distance=0.0, id=1),
        _spot("unknown", "b1", distance=None, id=2),
        _spot("near", "b1", distance=2.0, id=3),
    ]
    assert [s.star_system for s in sort_results(spots, "distance", False)] == [
        "zero",
        "near",
        "unknown",
    ]
    assert [s.star_system for s in sort_results(spots, "distance", True)] == [
        "near",
        "zero",
        "unknown",
    ]


def test_sort_results_by_name_case_insensitive():
    spots = [
        _spot("Rofoo", "b1", id=1),
        _spot("blooe", "b1", id=2),
        _spot("Cyaumie", "b1", id=3),
    ]
    asc = sort_results(spots, "full_name", False)
    assert [s.star_system for s in asc] == ["blooe", "Cyaumie", "Rofoo"]
    desc = sort_results(spots, "full_name", True)
    assert [s.star_system for s in desc] == ["Rofoo", "Cyaumie", "blooe"]


def test_sort_results_by_visit_time():
    spots = [
        _spot("late", "b1", visit="3312-11-01T00:00:00", id=1),
        _spot("early", "b1", visit="3312-10-01T00:00:00", id=2),
    ]
    ordered = sort_results(spots, "visit", False)
    assert [s.star_system for s in ordered] == ["early", "late"]


def test_sortable_columns_excludes_coords_and_hidden():
    # ``coords`` is two numbers in one cell; hidden columns are never user-facing.
    assert "coords" not in SORTABLE_RESULT_COLUMNS
    assert "system" not in SORTABLE_RESULT_COLUMNS
    assert "_lat" not in SORTABLE_RESULT_COLUMNS
    assert set(SORTABLE_RESULT_COLUMNS) == {
        "full_name",
        "distance",
        "mineral",
        "note",
        "visit",
    }

