"""Tests for OverlayClient._update_location.

The event can arrive with ``location=None`` -- that is the "in space" signal
sent on FSDJump / CarrierJump / LeaveBody / Resurrect (``current_location`` is
set to None, then ``_emit_location`` dispatches POSITION_UPDATED with it).

The extrapolator only has anything useful to say while the player has a valid
surface coordinate, so this method must:

  * not crash when the location is None (the regression this file guards), and
  * only feed the extrapolator when both a location and a coordinate exist.
"""

from surface_navigator.events_dispatcher import EventParams
from surface_navigator.overlay_client import OverlayClient
from surface_navigator.player_location import PlayerLocation, SurfacePoint
from surface_navigator.velocity_extrapolator import VelocityExtrapolator


def _client():
    """An OverlayClient built without ``__init__`` so the test does not
    subscribe to the global dispatcher or open an overlay connection."""
    client = OverlayClient.__new__(OverlayClient)
    client._overlay = None
    client._destination = None
    client._location = None
    client._extrapolator = VelocityExtrapolator()
    client._last_real_ts = 0.0
    return client


def test_update_location_none_location_does_not_crash():
    """A POSITION_UPDATED with location=None (in space) must be handled
    gracefully -- the old code raised AttributeError on .player_coord."""
    client = _client()
    client._update_location(EventParams(location=None))
    assert client._location is None


def test_update_location_none_location_does_not_feed_extrapolator():
    """No location -> no sample recorded in the extrapolator."""
    client = _client()
    before = len(client._extrapolator._samples)
    client._update_location(EventParams(location=None))
    assert len(client._extrapolator._samples) == before


def test_update_location_fed_with_valid_coord():
    """A valid location with a coordinate feeds the extrapolator exactly once."""
    client = _client()
    before = len(client._extrapolator._samples)
    location = PlayerLocation(
        star_system=None,
        body_name="Aurelia",
        player_coord=SurfacePoint(1.0, 2.0),
        radius_meters=1234.0,
    )
    client._update_location(EventParams(location=location))
    assert len(client._extrapolator._samples) == before + 1
    assert client._location is location
