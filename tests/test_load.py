"""Tests for surface_navigator.load event handling: last-system tracking.

The DB backfill itself lives in ``test_database.py`` (``update_existing_star_coords``);
here we verify that ``_update_last_system`` rebuilds ``self.last_system`` from
the event without clobbering values the event does not carry.

Plugin instances are built without ``__init__`` (via ``__new__``) so the tests
control ``last_system`` directly and do not touch the overlay or the mining
updater.
"""

from surface_navigator.load import SurfaceNavigatorPlugin
from surface_navigator.models import StarSystem


def _plugin():
    plugin = SurfaceNavigatorPlugin.__new__(SurfaceNavigatorPlugin)
    plugin.db_manager = None
    plugin.current_location = None
    plugin.last_system = StarSystem(star_name="")
    return plugin


# ---- _parse_star_pos -------------------------------------------------------


def test_parse_star_pos_returns_floats():
    plugin = _plugin()
    assert plugin._parse_star_pos({"StarPos": [1.0, -2.0, 3.5]}) == (1.0, -2.0, 3.5)


def test_parse_star_pos_none_without_pos():
    plugin = _plugin()
    # A jump event without StarPos (e.g. a plain LoadGame) yields no coords.
    assert plugin._parse_star_pos({"event": "FSDJump"}) is None


def test_parse_star_pos_none_on_bad_values():
    plugin = _plugin()
    assert plugin._parse_star_pos({"StarPos": [1.0, "x", 3.0]}) is None


# ---- _update_last_system ---------------------------------------------------


def test_update_last_system_sets_name_coords_and_systemid():
    plugin = _plugin()
    changed = plugin._update_last_system(
        "Sol", {"SystemAddress": 123, "StarPos": [1.0, 2.0, 3.0]}
    )
    assert changed is True
    assert plugin.last_system.star_name == "Sol"
    assert plugin.last_system.systemid == 123
    assert plugin.last_system.x == 1.0
    assert plugin.last_system.y == 2.0
    assert plugin.last_system.z == 3.0


def test_update_last_system_keeps_unknown_values():
    # Same system, event without SystemAddress/StarPos: nothing is clobbered.
    plugin = _plugin()
    plugin.last_system = StarSystem(star_name="Sol", systemid=999)
    changed = plugin._update_last_system("Sol", {"event": "LoadGame"})
    assert changed is False
    assert plugin.last_system.systemid == 999
    assert plugin.last_system.x is None


def test_update_last_system_carrier_jump_sets_coords():
    # A fleet carrier jump carries StarPos just like FSDJump - coordinates and
    # systemid are attached so the DB backfill can write them.
    plugin = _plugin()
    entry = {
        "event": "CarrierJump",
        "SystemAddress": 5363877956440,
        "StarPos": [-28.75, 25.0, 10.4375],
    }
    changed = plugin._update_last_system("Hermitage", entry)
    assert changed is True
    assert plugin.last_system.star_name == "Hermitage"
    assert plugin.last_system.systemid == 5363877956440
    assert plugin.last_system.x == -28.75
    assert plugin.last_system.y == 25.0
    assert plugin.last_system.z == 10.4375
