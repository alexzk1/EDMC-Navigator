"""Tests for the query-builder -> main-widget navigation wiring.

Three pure helpers carry the new logic so neither a full ``Toplevel`` builder
nor a ``MainGUIWidget`` needs instantiating:

* :func:`navigation_target` assembles a navigation target from a results row's
  four fields (star, body, lat, lon) -- the four things navigation needs.
* :func:`is_navigable` checks that target against the current position: we can
  only navigate to a spot we are actually standing on.
* :meth:`QueryBuilderWindow._navigable_target` gates the target on two things:
  a navigation callback exists, and the row is a surface spot, not a Tritium
  Ring in space.
"""

import tkinter as tk

# ``icons_cache`` builds ``PhotoImage``s at import time, which needs a default
# Tk root to exist first. Create one here -- this mirrors the app, where the GUI
# root is created before any icon is loaded.
_root = tk.Tk()

from surface_navigator.main_gui_widget import is_navigable
from surface_navigator.models import StarSystem
from surface_navigator.player_location import PlayerLocation, SurfacePoint
from surface_navigator.query_builder.builder_window import (
    QueryBuilderWindow,
    navigation_target,
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


def test_navigation_target_assembles_all_four_fields():
    target = navigation_target("Sol", "Earth", "1.5", "-2.5")
    assert target is not None
    assert target.body_name == "Earth"
    assert target.star_system.star_name == "Sol"
    assert target.player_coord == SurfacePoint(1.5, -2.5)


def test_navigation_target_rejects_missing_system():
    assert navigation_target("", "Earth", "1.0", "2.0") is None


def test_navigation_target_rejects_missing_body():
    assert navigation_target("Sol", "", "1.0", "2.0") is None


def test_navigation_target_rejects_missing_lat():
    assert navigation_target("Sol", "Earth", "", "2.0") is None


def test_navigation_target_rejects_missing_lon():
    assert navigation_target("Sol", "Earth", "1.0", "") is None


def test_navigation_target_rejects_unparseable_coordinates():
    assert navigation_target("Sol", "Earth", "abc", "2.0") is None


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
            0, "Sol", "Earth", "1.0", "2.0", None
        )
        is None
    )


def test_navigable_target_builds_for_surface_spot():
    # A plain surface spot with a callback wired produces a real target.
    target = QueryBuilderWindow._navigable_target(
        0, "Sol", "Earth", "1.0", "2.0", _navigate
    )
    assert target is not None
    assert target.star_system.star_name == "Sol"
    assert target.body_name == "Earth"


def test_navigable_target_none_for_tritium_ring():
    # A Tritium Ring is a spot in space, not a surface point -- no target.
    assert (
        QueryBuilderWindow._navigable_target(
            SurfaceSpotFlags.TRITIUM_RING_PRESENT.value,
            "Sol",
            "Earth",
            "1.0",
            "2.0",
            _navigate,
        )
        is None
    )


def test_navigable_target_still_rejects_missing_fields():
    # Even with a callback and no ring, a row missing coordinates is not
    # navigable -- that check lives in navigation_target.
    assert (
        QueryBuilderWindow._navigable_target(
            0, "Sol", "Earth", "", "2.0", _navigate
        )
        is None
    )
