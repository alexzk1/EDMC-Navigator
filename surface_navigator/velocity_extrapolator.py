"""Estimate the player's position between sparse game updates.

The game's ``Status.json`` (driving ``POSITION_UPDATED``) arrives in bursts with
gaps up to ~20s. To keep the overlay's bearing/distance fresh we project the
player's recent motion forward.

Projection is a plain linear step in degrees -- that is, in fact, the physically
correct position, because the distance and bearing we compute afterwards via
:class:`NavigationUtils` already account for the sphere. What matters is that the
estimate is only produced while the player is genuinely closing on the target,
so standing, spinning or flying away never yields a bogus position.

The class does NOT subscribe to any event itself. The overlay feeds it via
:meth:`update_pos`, so the player position has a single source of truth and
there are no callback-ordering surprises.
"""

from collections import deque

from .player_location import DEFAULT_PLANET_RADIUS, NavigationUtils, SurfacePoint


class VelocityExtrapolator:
    # Rolling window of recent positions used for the "approaching" trend.
    WINDOW = 5
    # Minimum closing speed (m/s) to trust that we are really approaching the
    # target. Filters out standing / spinning in place (position jitter).
    MIN_APPROACH_MS = 0.5

    def __init__(self) -> None:
        self._samples: deque[tuple[float, SurfacePoint]] = deque(
            maxlen=self.WINDOW
        )
        self._radius: float = DEFAULT_PLANET_RADIUS

    def update_pos(self, ts: float, coord: SurfacePoint, radius: float) -> None:
        """Record one known position. ``ts`` is wall-clock seconds."""
        self._radius = radius or DEFAULT_PLANET_RADIUS
        self._samples.append((ts, coord))

    def is_approaching(self, target: SurfacePoint) -> bool:
        """True while the target distance is shrinking faster than the noise."""
        if len(self._samples) < 2:
            return False
        d_start = NavigationUtils.haversine_distance(
            self._samples[0][1], target, self._radius
        )
        d_end = NavigationUtils.haversine_distance(
            self._samples[-1][1], target, self._radius
        )
        dt = self._samples[-1][0] - self._samples[0][0]
        if dt <= 0:
            return False
        return (d_start - d_end) / dt >= self.MIN_APPROACH_MS

    def extrapolate(self, now: float, target: SurfacePoint) -> SurfacePoint | None:
        """Project the latest position forward to ``now``.

        Returns ``None`` when the estimate is not trustworthy: too few samples,
        no forward time, or the player is not closing on the target.
        """
        if not self.is_approaching(target):
            return None
        prev_ts, prev = self._samples[-2]
        now_ts, current = self._samples[-1]
        dt = now_ts - prev_ts
        if dt <= 0:
            return None
        span = now - now_ts
        dlat_dt = (current.latitude - prev.latitude) / dt
        dlon_dt = (current.longitude - prev.longitude) / dt
        return SurfacePoint(
            latitude=current.latitude + dlat_dt * span,
            longitude=current.longitude + dlon_dt * span,
        )
