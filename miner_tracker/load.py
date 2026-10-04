import logging
import os
from collections.abc import Mapping, MutableMapping
from typing import Any

# Import components from within our plugin package
try:
    from .database import DatabaseManager
    from .gui import MinerTrackerGUI
    from .mining_event_detector import MiningEventDetector
    from .overlay_client import OverlayClient
    from .player_location import PlayerLocation
    from .status_flags import StatusFlags
except ImportError:
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    from database import DatabaseManager
    from gui import MinerTrackerGUI
    from mining_event_detector import MiningEventDetector
    from overlay_client import OverlayClient
    from player_location import PlayerLocation
    from status_flags import StatusFlags

logger = logging.getLogger("MinerTracker")


class MinerTrackerPlugin:
    def __init__(self, plugin_dir: str):
        db_path = os.path.join(plugin_dir, "miner_tracker.db")
        self.db_manager = DatabaseManager(db_path)
        self.overlay = OverlayClient("MinerTracker")
        self.mining_detector = MiningEventDetector(self.db_manager)
        self._gui: MinerTrackerGUI | None = None

        # Current game state tracking
        self.current_location: PlayerLocation | None = None
        self.is_on_surface: bool = False

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

        self._extract_location_from_journal(system, entry, state)
        self._update_gui_state()
        self.mining_detector.handle_journal_entry(
            cmdr, is_beta, system, station, entry, state
        )

    def _extract_location_from_journal(
        self, system: str, entry: Mapping[str, Any], state: MutableMapping[str, Any]
    ):
        """Extracts location information from journal entries."""
        new_body: str = ""
        new_lat: float | None = None
        new_lon: float | None = None

        # Keeping as much as possible of existing data until we fly away.
        match entry["event"]:
            case "Location":
                if "Latitude" in entry and not entry.get("Taxi", False):
                    new_lat = entry["Latitude"]
                    new_lon = entry["Longitude"]
            case "StartJump" | "LeaveBody" | "Resurrect":
                self.current_location = None
                return
            case "ApproachBody" | "Touchdown" | "Liftoff" | "Embark" | "Disembark":
                new_body = entry.get("Body") or ""
            case _:
                pass

        # We need to have location recorded or new body provided to create the record or both to update.
        if not new_body and not self.current_location:
            return

        old_location = (
            self.current_location
            if self.current_location
            else PlayerLocation(star_system=system)
        )
        old_body = old_location.body_name

        flew_to_other_body: bool = bool(new_body and (new_body != old_body))
        if flew_to_other_body or not self.current_location:
            final_body_name = self._clean_body_name(
                system, new_body or str(old_body or "")
            )
            self.current_location = PlayerLocation(
                star_system=system,
                body_name=final_body_name,
                latitude=new_lat,  # Most likely None
                longitude=new_lon,  # Most likely None
            )
            return

        # Update location if present as body remains the same yet.
        if new_lat is not None and new_lon is not None:
            self.current_location.latitude = new_lat
            self.current_location.longitude = new_lon

    def handle_dashboard_update(self, cmdr: str, is_beta: bool, entry: dict[str, Any]):
        """Called by EDMC when a Status update occurs (Dashboard)."""
        self._extract_location_from_status(entry)
        self._update_gui_state()

    def _extract_location_from_status(self, entry: dict[str, Any]):
        """Extracts location information from dashboard (Status) entries."""
        # Are we in deep space?
        if not self.current_location:
            return

        status_body = self._clean_body_name(
            self.current_location.star_system,
            entry.get("BodyName") or self.current_location.body_name,
        )

        # Are we in deep space?
        if not status_body:
            return

        # If we got different body - reset everything, status updates more often.
        if status_body != self.current_location.body_name:
            self.current_location = PlayerLocation(
                star_system=self.current_location.star_system, body_name=status_body
            )

        flags = StatusFlags(entry.get("Flags", 0))
        if StatusFlags.FSD_JUMP_IN_PROGRESS in flags:
            # Jump animation started? We're not there for sure now.
            self.current_location = None
            return

        # Do we have lat/lon at all ?
        if StatusFlags.HAS_LATLONG in flags:
            lat = entry.get("Latitude")
            lon = entry.get("Longitude")
            if lat is not None and lon is not None:
                self.current_location.longitude = lon
                self.current_location.latitude = lat
        if (h := entry.get("Heading")) is not None:
            self.current_location.heading = h
        if (r := entry.get("PlanetRadius")) is not None:
            self.current_location.radius = r

    def _clean_body_name(self, system_name: str, raw_body_name: str) -> str:
        """Removes star system prefix from body name."""
        if raw_body_name.startswith(system_name + " "):
            body_name = raw_body_name[len(system_name + " ") :]
        else:
            body_name = raw_body_name
        return body_name

    def _update_gui_state(self):
        if self._gui:
            self._gui.set_current_location(self.current_location)

    def create_gui(self, parent: Any) -> MinerTrackerGUI | None:
        if self._gui is None:
            self._gui = MinerTrackerGUI(parent, self.db_manager, self.overlay)
            self._gui.current_location = self.current_location
            self._gui.has_coords = self.is_on_surface
        return self._gui

    def shutdown(self):
        if self._gui:
            self._gui.destroy()


# Global plugin instance for EDMC to hold onto
_instance: MinerTrackerPlugin | None = None


def plugin_start3(plugin_dir: str) -> str:
    global _instance
    _instance = MinerTrackerPlugin(plugin_dir)
    return "Miner Tracker"


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


def plugin_app(parent: Any) -> MinerTrackerGUI | None:
    if _instance:
        return _instance.create_gui(parent)
    return None


def shutdown():
    if _instance:
        _instance.shutdown()
