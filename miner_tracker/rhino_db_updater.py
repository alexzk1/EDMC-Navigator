from .database import DatabaseManager
from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .events_suppression_zone import events_suppression_manager
from .player_location import DEFAULT_PLANET_RADIUS


class RhinoMiningDbUpdater:
    """
    Listens to the RhinoMiningEventDetector and tries to update DB if commodity/material was not manually entered.
    Once DB is complete, marks this point as exclusion zone.
    """

    def __init__(self, db_manager: DatabaseManager):
        self._db_manager = db_manager
        dispatcher.subscribe(
            KnownEvents.RHINO_MINING_DETECTED, self._on_mining_detected
        )

    def _on_mining_detected(self, data: EventParams):
        # Check is cheap, so we can do double check in case somebody will remove the same check in provider.
        if events_suppression_manager.is_current_srv_location_suppressed():
            return

        # Double check to make linter happy.
        loc = events_suppression_manager.location()
        if loc is None or loc.srv_coord is None:
            return
        # In any case, spot is seen and processed. Ignore more incoming events here.
        events_suppression_manager.set_exclusion_zone_at_srv_location()

        spot = self._db_manager.find_incomplete_surface_mining_spot(
            center=loc.srv_coord,
            radius_meters=events_suppression_manager.radius(),
            planet_radius_meters=loc.radius_meters or DEFAULT_PLANET_RADIUS,
        )
        # Known spot at SRV location, probably pilot just returned from outside the planet or no mark was set here.
        if spot is None or spot.id is None:
            return

        self._db_manager.update_spot(
            spot.id,
            mineral_type=data.params.get("mineral_db"),
            mineral_original=data.params.get("mineral_in_log"),
        )
