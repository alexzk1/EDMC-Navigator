"""Tests for surface navigation math and the event suppression zone.

The suppression zone collapses many scans in a small area into a single
bookmark. A bug once passed the *exclusion radius* to the haversine formula
instead of the *planet radius* - turning every distance into a tiny fraction of
a metre. A 100 m flight then looked like 0 m and everything got suppressed, so
marks never appeared after moving away. These tests pin that down: the planet
radius must be used, and points beyond the exclusion radius must NOT be
suppressed.
"""

import pytest

from surface_navigator.events_dispatcher import EventParams, KnownEvents, dispatcher
from surface_navigator.events_suppression_zone import (
    SURFACE_SCAN_SUPPRESSION_RADIUS_METERS,
    SUPPRESSION_RADIUS_METERS,
    EventsSuppressionManager,
    mining_events_suppression_manager,
    surface_scan_suppression_manager,
)
from surface_navigator.player_location import (
    DEFAULT_PLANET_RADIUS,
    IN_GAME_YEAR_OFFSET,
    NavigationUtils,
    PlayerLocation,
    SurfacePoint,
    in_game_timestamp,
)
from surface_navigator.models import StarSystem


@pytest.fixture()
def manager() -> EventsSuppressionManager:
    """A fresh manager with no zones and no tracked location."""
    return EventsSuppressionManager(200.0)


def _loc(lat: float, lon: float, radius: float | None = DEFAULT_PLANET_RADIUS):
    return PlayerLocation(
        star_system=StarSystem(star_name="Test"),
        body_name="Test Body",
        player_coord=SurfacePoint(latitude=lat, longitude=lon),
        radius_meters=radius,
    )


def _set_location(mgr: EventsSuppressionManager, loc: PlayerLocation):
    mgr._location = loc


# --- haversine math ---------------------------------------------------------


def test_haversine_zero_distance_is_zero():
    a = SurfacePoint(10.0, 20.0)
    assert NavigationUtils.haversine_distance(a, a, DEFAULT_PLANET_RADIUS) == 0.0


def test_haversine_uses_planet_radius():
    # One degree of latitude is ~111.2 km on a 6371 km planet. If the caller
    # passes the exclusion radius (200 m) instead of the planet radius, the
    # result would be ~0.004 m - this guards against that.
    a = SurfacePoint(0.0, 0.0)
    b = SurfacePoint(1.0, 0.0)
    dist = NavigationUtils.haversine_distance(a, b, DEFAULT_PLANET_RADIUS)
    assert 110_000 < dist < 112_000


def test_haversine_is_symmetric():
    a = SurfacePoint(3.0, 4.0)
    b = SurfacePoint(7.0, 8.0)
    assert (
        NavigationUtils.haversine_distance(a, b, DEFAULT_PLANET_RADIUS)
        == NavigationUtils.haversine_distance(b, a, DEFAULT_PLANET_RADIUS)
    )


# --- exclusion zone ---------------------------------------------------------


def test_not_suppressed_without_zones(manager: EventsSuppressionManager):
    _set_location(manager, _loc(0.0, 0.0))
    assert manager.is_suppressed(SurfacePoint(0.0, 0.0)) is False


def test_not_suppressed_when_location_unknown(manager: EventsSuppressionManager):
    # No location tracked yet - nothing to compare against, so nothing is
    # suppressed (and we do not crash on a None location).
    assert manager.is_suppressed(SurfacePoint(0.0, 0.0)) is False


def test_suppressed_within_radius(manager: EventsSuppressionManager):
    _set_location(manager, _loc(0.0, 0.0))
    manager.add_exclusion_zone_center(SurfacePoint(0.0, 0.0))
    # ~111 m away (0.001 deg of latitude) - inside a 200 m zone.
    assert manager.is_suppressed(SurfacePoint(0.001, 0.0)) is True


def test_not_suppressed_beyond_radius(manager: EventsSuppressionManager):
    # The regression: a flight of more than 100 m must NOT be suppressed. With
    # the old bug (planet radius replaced by the 200 m exclusion radius) the
    # distance reads as ~0 m and this point is wrongly suppressed.
    _set_location(manager, _loc(0.0, 0.0))
    manager.add_exclusion_zone_center(SurfacePoint(0.0, 0.0))
    # ~333 m away (0.003 deg of latitude) - outside a 200 m zone.
    assert manager.is_suppressed(SurfacePoint(0.003, 0.0)) is False


def test_is_current_player_location_uses_player_coord(manager: EventsSuppressionManager):
    # Player stands ~333 m (0.003 deg) from the zone centre at the origin.
    _set_location(manager, _loc(0.003, 0.0))
    manager.add_exclusion_zone_center(SurfacePoint(0.0, 0.0))
    # Player is outside the 200 m zone -> not suppressed.
    assert manager.is_current_player_location_suppressed() is False


def test_current_srv_location_suppressed(manager: EventsSuppressionManager):
    loc = _loc(0.0, 0.0)
    loc.srv_coord = SurfacePoint(0.0, 0.0)
    _set_location(manager, loc)
    manager.add_exclusion_zone_center(SurfacePoint(0.0, 0.0))
    # SRV sits on the zone -> suppressed.
    assert manager.is_current_srv_location_suppressed() is True


def test_zones_reset_when_location_none(manager: EventsSuppressionManager):
    _set_location(manager, _loc(0.0, 0.0))
    manager.add_exclusion_zone_center(SurfacePoint(0.0, 0.0))
    assert manager.is_suppressed(SurfacePoint(0.0, 0.0)) is True
    # Leaving the planet (location None) clears the zones.
    manager._location_update_listener(EventParams(location=None))
    assert manager.is_suppressed(SurfacePoint(0.0, 0.0)) is False


def test_default_managers_have_expected_radii():
    assert mining_events_suppression_manager.radius() == SUPPRESSION_RADIUS_METERS
    assert (
        surface_scan_suppression_manager.radius()
        == SURFACE_SCAN_SUPPRESSION_RADIUS_METERS
    )
    # The surface scanner zone is looser than the mining one.
    assert SURFACE_SCAN_SUPPRESSION_RADIUS_METERS > SUPPRESSION_RADIUS_METERS


# --- in-game calendar -------------------------------------------------------


def test_in_game_timestamp_shifts_year_only():
    import datetime as _dt

    fixed = _dt.datetime(2026, 10, 8, 12, 34, 56, tzinfo=_dt.timezone.utc)
    # Month, day and time of day are preserved; only the year is shifted.
    assert in_game_timestamp(now=fixed) == f"{2026 + IN_GAME_YEAR_OFFSET}-10-08 12:34:56"


def test_in_game_timestamp_keeps_impossible_feb29():
    import datetime as _dt

    # 2028-02-29 is a real leap day; the in-year 3314 is NOT a leap year, yet we
    # render it verbatim (like the game) instead of raising ValueError.
    fixed = _dt.datetime(2028, 2, 29, 0, 0, 0, tzinfo=_dt.timezone.utc)
    assert in_game_timestamp(now=fixed) == f"{2028 + IN_GAME_YEAR_OFFSET}-02-29 00:00:00"
