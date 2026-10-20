"""Tests for OverlayClient._update_location.

The event can arrive with ``location=None`` -- that is the "in space" signal
sent on FSDJump / CarrierJump / LeaveBody / Resurrect (``current_location`` is
set to None, then ``_emit_location`` dispatches POSITION_UPDATED with it).

The extrapolator only has anything useful to say while the player has a valid
surface coordinate, so this method must:

  * not crash when the location is None (the regression this file guards), and
  * only feed the extrapolator when both a location and a coordinate exist.
"""

import math

from surface_navigator.events_dispatcher import EventParams
from surface_navigator.overlay_client import OverlayClient
from surface_navigator.player_location import PlayerLocation, SurfacePoint
from surface_navigator.velocity_extrapolator import VelocityExtrapolator


def _client():
    """An OverlayClient built without ``__init__`` so the test does not
    subscribe to the global dispatcher or open an overlay connection."""
    client = OverlayClient.__new__(OverlayClient)
    client._overlay = None  # pyright: ignore[reportPrivateUsage]
    client._destination = None  # pyright: ignore[reportPrivateUsage]
    client._location = None  # pyright: ignore[reportPrivateUsage]
    client._extrapolator = VelocityExtrapolator()  # pyright: ignore[reportPrivateUsage]
    client._last_real_ts = 0.0  # pyright: ignore[reportPrivateUsage]
    return client


def test_update_location_none_location_does_not_crash():
    """A POSITION_UPDATED with location=None (in space) must be handled
    gracefully -- the old code raised AttributeError on .player_coord."""
    client = _client()
    client._update_location(EventParams(location=None))  # pyright: ignore[reportPrivateUsage]
    assert client._location is None  # pyright: ignore[reportPrivateUsage]


def test_update_location_none_location_does_not_feed_extrapolator():
    """No location -> no sample recorded in the extrapolator."""
    client = _client()
    before = len(client._extrapolator._samples)  # pyright: ignore[reportPrivateUsage]
    client._update_location(EventParams(location=None))  # pyright: ignore[reportPrivateUsage]
    assert len(client._extrapolator._samples) == before  # pyright: ignore[reportPrivateUsage]


def test_update_location_fed_with_valid_coord():
    """A valid location with a coordinate feeds the extrapolator exactly once."""
    client = _client()
    before = len(client._extrapolator._samples)  # pyright: ignore[reportPrivateUsage]
    location = PlayerLocation(
        star_system=None,  # type: ignore
        body_name="Aurelia",
        player_coord=SurfacePoint(1.0, 2.0),
        radius_meters=1234.0,
    )
    client._update_location(EventParams(location=location))  # pyright: ignore[reportPrivateUsage]
    assert len(client._extrapolator._samples) == before + 1  # pyright: ignore[reportPrivateUsage]
    assert client._location is location  # pyright: ignore[reportPrivateUsage]


def test_arrow_apex_points_forward_at_rel_zero():
    """At rel=0 the apex sits straight "up" (screen-up = smaller y) over the
    center, since heading == bearing means the target is straight ahead."""
    cx, cy, r = 100.0, 100.0, 40.0
    pts = OverlayClient._arrow_points(cx, cy, r, 0.0)  # pyright: ignore[reportPrivateUsage]
    apex = pts[0]
    assert apex["x"] == round(cx)
    assert apex["y"] == round(cy - r)  # above center


def test_arrow_apex_swings_right_for_east_target():
    """A target 90 deg clockwise from facing (East) puts the apex to the right
    of center on screen."""
    cx, cy, r = 100.0, 100.0, 40.0
    apex = OverlayClient._arrow_points(cx, cy, r, 90.0)[0]  # pyright: ignore[reportPrivateUsage]
    assert apex["x"] == round(cx + r)
    assert apex["y"] == round(cy)


def test_arrow_svg_rotates_by_relative_angle():
    """The SVG points the static up-triangle through rel via transform, so C++
    does the rotation. rel=0 keeps apex up; rel=90 swings it clockwise."""
    svg0 = OverlayClient._arrow_svg(80, 0.0, "#62FF00")  # pyright: ignore[reportPrivateUsage]
    assert "rotate(0.0 40.0 40.0)" in svg0
    assert "points=" in svg0 and "url(#navArrow)" in svg0

    svg90 = OverlayClient._arrow_svg(80, 90.0, "#62FF00")  # pyright: ignore[reportPrivateUsage]
    assert "rotate(90.0 40.0 40.0)" in svg90


def test_smoothing_snaps_to_target_on_first_call():
    """First reading has no history, so we start with zero lag."""
    client = _client()
    client._arrow_rel = None  # pyright: ignore[reportPrivateUsage]
    assert client._smooth_arrow_rel(45.0, 0.0) == 45.0  # pyright: ignore[reportPrivateUsage]


def test_smoothing_does_not_move_when_time_has_not_passed():
    """dt == 0 -> factor == 0 -> no move, so a same-tick re-entry is a no-op."""
    client = _client()
    client._arrow_rel = 30.0  # pyright: ignore[reportPrivateUsage]
    client._arrow_ts = 100.0  # pyright: ignore[reportPrivateUsage]
    assert client._smooth_arrow_rel(90.0, 100.0) == 30.0  # pyright: ignore[reportPrivateUsage]


def test_smoothing_moves_toward_target_by_exponential_factor():
    """One tau elapses -> factor = 1 - e^-1, so we cover that fraction of the
    gap toward the target."""
    client = _client()
    client._arrow_rel = 0.0  # pyright: ignore[reportPrivateUsage]
    client._arrow_ts = 0.0  # pyright: ignore[reportPrivateUsage]
    result = client._smooth_arrow_rel(90.0, OverlayClient.ARROW_TAU_SECS)  # pyright: ignore[reportPrivateUsage]
    expected = 90.0 * (1 - math.exp(-1.0))
    assert abs(result - expected) < 1e-6


def test_smoothing_takes_shortest_way_across_359_1():
    """350 -> 10 is +20 deg, not -340; the filter must cross the boundary, not
    spin the long way around."""
    client = _client()
    client._arrow_rel = 350.0  # pyright: ignore[reportPrivateUsage]
    client._arrow_ts = 0.0  # pyright: ignore[reportPrivateUsage]
    result = client._smooth_arrow_rel(10.0, 2.0 * OverlayClient.ARROW_TAU_SECS)  # pyright: ignore[reportPrivateUsage]
    factor = 1 - math.exp(-2.0)
    expected = (350.0 + ((10.0 - 350.0 + 180.0) % 360.0 - 180.0) * factor) % 360.0
    assert abs(result - expected) < 1e-6
    assert result < 20.0  # landed near 10, proving the short path
