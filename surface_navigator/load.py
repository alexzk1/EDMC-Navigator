import logging
import os
from collections.abc import Mapping, MutableMapping
from typing import Any

# Import components from within our plugin package
try:
    from .database import DatabaseManager
    from .events_dispatcher import EventParams, KnownEvents, dispatcher
    from .main_gui_widget import MainGUIWidget
    from .mining_event_detector import RhinoMiningEventDetector
    from .overlay_client import OverlayClient, OverlayTextConf
    from .player_location import PlayerLocation, SurfacePoint
    from .rhino_db_updater import RhinoMiningDbUpdater
    from .status_flags import StatusFlags
except ImportError:
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    from database import DatabaseManager
    from events_dispatcher import EventParams, KnownEvents, dispatcher
    from main_gui_widget import MainGUIWidget
    from mining_event_detector import RhinoMiningEventDetector
    from overlay_client import OverlayClient, OverlayTextConf
    from player_location import PlayerLocation, SurfacePoint
    from rhino_db_updater import RhinoMiningDbUpdater
    from status_flags import StatusFlags

logger = logging.getLogger("SurfaceNavigator")


class SurfaceNavigatorPlugin:
    def __init__(self, plugin_dir: str):
        db_path = os.path.join(plugin_dir, "surface_navigator.db")
        self.db_manager = DatabaseManager(db_path)

        # Automatic DB update if user do not enter whole description and just starts mining near the marked spot.
        self.rhino_auto_update_db = RhinoMiningDbUpdater(self.db_manager)

        # TODO: add settings to configure overlay position
        self._overlay = OverlayClient(OverlayTextConf())
        self._mining_detector = RhinoMiningEventDetector()
        self._gui: MainGUIWidget | None = None

        # Current game state tracking
        self.current_location: PlayerLocation | None = None

    def handle_journal_event(
        self,
        cmdr: str,
        is_beta: bool,
        system: str,
        station: str,
        entry: Mapping[str, Any],
        state: MutableMapping[str, Any],
    ):
        """Called by EDMC when a journal event occurs."""

        if self._extract_location_from_journal(system, entry, state):
            self._emit_location()
        self._mining_detector.handle_journal_entry(
            cmdr, is_beta, system, station, entry, state
        )

    def _extract_location_from_journal(
        self, system: str, entry: Mapping[str, Any], state: MutableMapping[str, Any]
    ) -> bool:
        """Extracts location information from journal entries."""
        dirty_new_body: str = ""
        new_point: SurfacePoint | None = None
        loc_update_in_srv: bool = False
        had_approach: bool = False

        # Keeping as much as possible of existing data until we fly away.
        # Detect the body and/or coordinates in event.
        match entry["event"]:
            case "Location":
                if "Latitude" in entry:
                    loc_update_in_srv = entry.get("InSRV", False)
                    new_point = SurfacePoint(
                        latitude=entry["Latitude"], longitude=entry["Longitude"]
                    )
            case "FSDJump" | "LeaveBody" | "Resurrect":
                self.current_location = None
                # Reset any stored navigation in overlay, we're out...
                self._overlay.navigate_to(None)
                return True
            case (
                "ApproachBody"
                | "Touchdown"
                | "Liftoff"
                | "Embark"
                | "Disembark"
                | "SupercruiseExit"
            ):
                dirty_new_body = entry.get("Body") or ""
                had_approach = True
            case "ApproachSettlement":
                dirty_new_body = entry.get("BodyName") or ""
                had_approach = True
            case _:
                pass

        # We need to have location recorded or new body provided to create the record or both to update.
        if not dirty_new_body and not self.current_location:
            return False

        old_location = (
            self.current_location
            if self.current_location
            else PlayerLocation(star_system=system)
        )
        old_body = old_location.body_name
        new_body = self._clean_body_name(system, dirty_new_body)

        def refresh_srv_location() -> bool:
            # If record is related to the taxi / station -> do nothing....we could call taxi and left SRV,
            # though it has no sense, as SRV will explode later.
            if (
                entry.get("Taxi", False)
                or not entry.get("OnPlanet", False)
                or not self.current_location
            ):
                return False
            # That is was location update clearly stating we're in SRV.
            if loc_update_in_srv:
                self.current_location.srv_coord = self.current_location.player_coord
                self.current_location.is_boarded_srv = True
                return True

            if entry.get("SRV", False):
                match entry["event"]:
                    # Player enter SRV or ship launches SRV with player inside.
                    case "Embark" | "LaunchSRV":
                        self.current_location.srv_coord = (
                            self.current_location.player_coord
                        )
                        self.current_location.is_boarded_srv = True
                        return True
                    # Player exits SRV.
                    case "Disembark":
                        self.current_location.srv_coord = (
                            self.current_location.player_coord
                        )
                        self.current_location.is_boarded_srv = False
                        return True
                    # SRV is destroyed or back to ship.
                    case "SRVDestroyed" | "DockSRV":
                        self.current_location.is_boarded_srv = False
                        self.current_location.srv_coord = None
                        return True
                    case _:
                        pass
            # If some other events happen, and we're in SRV, update.
            if self.current_location.is_boarded_srv:
                self.current_location.srv_coord = self.current_location.player_coord
            # SRV coordinate update will be send as player coordinate update.
            return False

        flew_to_other_body: bool = bool(new_body and (new_body != old_body))
        if flew_to_other_body or not self.current_location:
            final_body_name = new_body or str(old_body or "")
            self.current_location = PlayerLocation(
                star_system=system,
                body_name=final_body_name,
                player_coord=new_point,
            )
            refresh_srv_location()
            return True

        # Update location if present as body remains the same yet.
        has_new_point: bool = new_point is not None
        if has_new_point:
            self.current_location.player_coord = new_point
        return had_approach or has_new_point or refresh_srv_location()

    def handle_dashboard_update(self, cmdr: str, is_beta: bool, entry: dict[str, Any]):
        """Called by EDMC when a Status update occurs (Dashboard)."""
        if self._extract_location_from_status(entry):
            self._emit_location()

    def _extract_location_from_status(self, entry: dict[str, Any]) -> bool:
        """Extracts location information from dashboard (Status) entries."""
        # Are we in deep space?
        if not self.current_location:
            return False

        status_body = self._clean_body_name(
            self.current_location.star_system,
            entry.get("BodyName") or self.current_location.body_name,
        )

        # Are we in deep space?
        if not status_body:
            return False

        flags = StatusFlags(entry.get("Flags", 0))
        had_changes = (
            self.current_location.is_boarded_srv != StatusFlags.IN_SRV in flags
            or StatusFlags.FSD_JUMP_IN_PROGRESS in flags
        )

        # If we got different body - reset everything, status updates more often.
        if status_body != self.current_location.body_name:
            self.current_location = PlayerLocation(
                star_system=self.current_location.star_system, body_name=status_body
            )
            had_changes = True

        self.current_location.is_boarded_srv = StatusFlags.IN_SRV in flags

        # Do we have lat/lon at all ?
        if StatusFlags.HAS_LATLONG in flags:
            lat = entry.get("Latitude")
            lon = entry.get("Longitude")
            if lat is not None and lon is not None:
                had_changes = True
                self.current_location.player_coord = SurfacePoint(
                    latitude=lat, longitude=lon
                )
                if self.current_location.is_boarded_srv:
                    self.current_location.srv_coord = self.current_location.player_coord
        if (h := entry.get("Heading")) is not None:
            had_changes = True
            self.current_location.heading_deg = h
        if (r := entry.get("PlanetRadius")) is not None:
            had_changes = True
            self.current_location.radius_meters = r
        return had_changes

    def _clean_body_name(self, system_name: str, raw_body_name: str) -> str:
        """Removes star system prefix from body name."""
        if raw_body_name.startswith(system_name + " "):
            body_name = raw_body_name[len(system_name + " ") :]
        else:
            body_name = raw_body_name
        return body_name

    def _emit_location(self):
        dispatcher.dispatch(
            KnownEvents.POSITION_UPDATED, EventParams(location=self.current_location)
        )

    def create_gui(self, parent: Any) -> MainGUIWidget | None:
        if self._gui is None:
            self._gui = MainGUIWidget(parent, self.db_manager, self._overlay)
            self._gui.current_location = self.current_location
        return self._gui

    def shutdown(self):
        if self._gui:
            self._gui.destroy()


# Global plugin instance for EDMC to hold onto
_instance: SurfaceNavigatorPlugin | None = None


def plugin_start3(plugin_dir: str) -> str:
    global _instance
    _instance = SurfaceNavigatorPlugin(plugin_dir)
    return "Surface Navigator"


def journal_entry(
    cmdr: str,
    is_beta: bool,
    system: str,
    station: str,
    entry: Mapping[str, Any],
    state: MutableMapping[str, Any],
):
    if _instance:
        _instance.handle_journal_event(cmdr, is_beta, system, station, entry, state)


def dashboard_entry(cmdr: str, is_beta: bool, entry: dict[str, Any]) -> str:
    """The specific hook for Status updates (Dashboard)."""
    if _instance:
        _instance.handle_dashboard_update(cmdr, is_beta, entry)
        return ""
    return ""


def plugin_app(parent: Any) -> MainGUIWidget | None:
    if _instance:
        return _instance.create_gui(parent)
    return None


def shutdown():
    if _instance:
        _instance.shutdown()
