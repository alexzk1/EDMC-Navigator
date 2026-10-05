from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .player_location import NavigationUtils, PlayerLocation, SurfacePoint


class EventsSuppressionManager:
    """
    Tracks locations where events are ignored.
    When we have detected mined mineral we're not interested in mining events any more for performance reasons.
    Zones are active during current session only (we can spend some time and rebuild it on next visit).
    """

    def __init__(self, radius_meters: float):
        self.radius = radius_meters
        self._active_zones: list[SurfacePoint] = []
        self._location: PlayerLocation | None = None

        dispatcher.subscribe(
            KnownEvents.POSITION_UPDATED, self._location_update_listener
        )

    def is_suppressed(self, current_pos: SurfacePoint) -> bool:
        """Checks if given point is inside exclusion zone."""

        for zone_pos in self._active_zones:
            dist = NavigationUtils.haversine_distance(
                current_pos, zone_pos, self.radius
            )
            if dist <= self.radius:
                return True

        return False

    def is_current_srv_location_suppressed(self):
        """Check if latest known SRV position is in exclusion zone."""
        if self._location is None or self._location.srv_coord is None:
            return True
        return self.is_suppressed(self._location.srv_coord)

    def add_exclusion_zone_center(self, point: SurfacePoint):
        """Create new exclusion zone if we have known location, otherwise ignored as we could be in space."""
        if self._location is not None:
            self._active_zones.append(point)

    def _location_update_listener(self, data: EventParams):
        self._location = data.location
        # Location None is sent only when we left the planet for KnownEvents.POSITION_UPDATED.
        if self._location is None:
            self._active_zones = []


SUPPRESSION_RADIUS_METERS: int = 70
events_suppression_manager = EventsSuppressionManager(SUPPRESSION_RADIUS_METERS)
