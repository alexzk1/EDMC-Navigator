from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .player_location import NavigationUtils, PlayerLocation, SurfacePoint


class EventsSuppressionManager:
    """
    Tracks locations where events are ignored.
    When we have detected mined mineral we're not interested in mining events any more for performance reasons.
    Zones are active during current session only (we can spend some time and rebuild it on next visit).
    """

    def __init__(self, radius_meters: float):
        self._radius = radius_meters
        self._location: PlayerLocation | None = None

        self._active_zones: list[SurfacePoint] = []

        dispatcher.subscribe(
            KnownEvents.POSITION_UPDATED, self._location_update_listener
        )
        dispatcher.subscribe(
            KnownEvents.DATABASE_MODIFIED, self._new_db_record_listener
        )

    def location(self):
        return self._location

    def radius(self):
        return self._radius

    def is_suppressed(self, current_pos: SurfacePoint) -> bool:
        """Checks if given point is inside exclusion zone."""

        for zone_pos in self._active_zones:
            dist = NavigationUtils.haversine_distance(
                current_pos, zone_pos, self._radius
            )
            if dist <= self._radius:
                return True

        return False

    def is_current_srv_location_suppressed(self):
        """Check if latest known SRV position is in exclusion zone."""
        if self._location is None or self._location.srv_coord is None:
            return True
        return self.is_suppressed(self._location.srv_coord)

    def is_current_player_location_suppressed(self):
        """Check if latest known player position is in exclusion zone."""
        if self._location is None or self._location.player_coord is None:
            return True
        return self.is_suppressed(self._location.player_coord)

    def add_exclusion_zone_center(self, point: SurfacePoint):
        """Create new exclusion zone if we have known location, otherwise ignored as we could be in space."""
        if self._location is not None:
            self._active_zones.append(point)

    def set_exclusion_zone_at_srv_location(self):
        if self._location is None or self._location.srv_coord is None:
            return
        self.add_exclusion_zone_center(self._location.srv_coord)

    def set_exclusion_zone_at_player_location(self):
        if self._location is None or self._location.player_coord is None:
            return
        self.add_exclusion_zone_center(self._location.player_coord)

    def _location_update_listener(self, data: EventParams):
        self._location = data.location
        # Location None is sent only when we left the planet for KnownEvents.POSITION_UPDATED.
        if self._location is None:
            self._active_zones = []

    def _new_db_record_listener(self, data: EventParams):
        # This is situation when mining started, zone got excluded as "no marks here" and then user adds the mark.
        if data.params.get("new_record", False):
            # For simplicity, reset all current exclusion zones when new mark is added and let'em rebuilt.
            # Note, we could make complex check and find closest to new mark.
            self._active_zones = []


SUPPRESSION_RADIUS_METERS: int = 90
mining_events_suppression_manager = EventsSuppressionManager(SUPPRESSION_RADIUS_METERS)
