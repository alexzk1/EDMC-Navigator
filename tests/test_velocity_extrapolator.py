"""Tests for VelocityExtrapolator.

The extrapolator estimates the player's position between sparse game updates.
Its two gates matter most: it must only project while the player is genuinely
closing on the target (never while standing, spinning or flying away), and the
projection must move forward along recent motion.
"""

from surface_navigator.player_location import DEFAULT_PLANET_RADIUS, SurfacePoint
from surface_navigator.velocity_extrapolator import VelocityExtrapolator


def _approaching_pair():
    """Two samples, player moving north toward a target to the north."""
    exp = VelocityExtrapolator()
    exp.update_pos(100.0, SurfacePoint(0.0, 0.0), DEFAULT_PLANET_RADIUS)
    # 0.01 deg north over 10s ~ 111 m/s -- well above the min approach speed.
    exp.update_pos(110.0, SurfacePoint(0.01, 0.0), DEFAULT_PLANET_RADIUS)
    return exp


def test_extrapolate_none_with_few_samples():
    exp = VelocityExtrapolator()
    assert exp.extrapolate(120.0, SurfacePoint(1.0, 0.0)) is None
    exp.update_pos(100.0, SurfacePoint(0.0, 0.0), DEFAULT_PLANET_RADIUS)
    assert exp.extrapolate(120.0, SurfacePoint(1.0, 0.0)) is None


def test_extrapolate_none_when_stationary():
    """Standing / spinning in place yields no estimate (distance is flat)."""
    exp = VelocityExtrapolator()
    exp.update_pos(100.0, SurfacePoint(0.0, 0.0), DEFAULT_PLANET_RADIUS)
    exp.update_pos(110.0, SurfacePoint(0.0, 0.0), DEFAULT_PLANET_RADIUS)
    assert exp.extrapolate(120.0, SurfacePoint(1.0, 0.0)) is None


def test_extrapolate_none_when_receding():
    """Flying away from the target yields no estimate (distance grows)."""
    exp = VelocityExtrapolator()
    exp.update_pos(100.0, SurfacePoint(0.5, 0.0), DEFAULT_PLANET_RADIUS)
    exp.update_pos(110.0, SurfacePoint(0.4, 0.0), DEFAULT_PLANET_RADIUS)
    assert exp.extrapolate(120.0, SurfacePoint(1.0, 0.0)) is None


def test_is_approaching_false_below_min_speed():
    """Sub-threshold jitter (noise) must not count as approaching."""
    exp = VelocityExtrapolator()
    exp.update_pos(100.0, SurfacePoint(0.0, 0.0), DEFAULT_PLANET_RADIUS)
    # ~1e-5 m/s -- effectively noise, below MIN_APPROACH_MS.
    exp.update_pos(110.0, SurfacePoint(0.0000001, 0.0), DEFAULT_PLANET_RADIUS)
    assert exp.is_approaching(SurfacePoint(1.0, 0.0)) is False


def test_extrapolate_projects_forward_on_approach():
    """While approaching, the projection advances along recent motion."""
    exp = _approaching_pair()
    est = exp.extrapolate(120.0, SurfacePoint(1.0, 0.0))
    assert est is not None
    # Moving north: the projected latitude is ahead of the latest known one.
    assert est.latitude > 0.01
    # lon was unchanged, so it stays put.
    assert est.longitude == 0.0


def test_extrapolate_uses_only_last_two_samples_for_velocity():
    """Velocity comes from the two most recent samples, not the whole window."""
    exp = VelocityExtrapolator()
    # Accelerating north: the window-averaged rate (0.003 deg/s) differs from
    # the last-two rate (0.005 deg/s), and motion is monotonic so we still
    # approach the target.
    exp.update_pos(100.0, SurfacePoint(0.0, 0.0), DEFAULT_PLANET_RADIUS)
    exp.update_pos(105.0, SurfacePoint(0.005, 0.0), DEFAULT_PLANET_RADIUS)
    exp.update_pos(110.0, SurfacePoint(0.03, 0.0), DEFAULT_PLANET_RADIUS)
    # span = 120 - 110 = 10s, last-two rate 0.005 -> 0.03 + 0.05 = 0.08.
    est = exp.extrapolate(120.0, SurfacePoint(1.0, 0.0))
    assert est is not None
    assert 0.07 < est.latitude < 0.09


def test_window_is_bounded_to_five():
    """The rolling window keeps at most WINDOW recent samples."""
    exp = VelocityExtrapolator()
    for i in range(8):
        exp.update_pos(float(i), SurfacePoint(0.0, float(i)), DEFAULT_PLANET_RADIUS)
    # Only the last 5 remain; the newest is the latest sample.
    assert len(exp._samples) == VelocityExtrapolator.WINDOW
    assert exp._samples[-1][0] == 7.0
