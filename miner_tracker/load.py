import os
from typing import Any, Optional, Dict
import logging

# Import components from within our plugin package
try:
    from .models import MiningSpot
    from .database import DatabaseManager
    from .journal_handler import JournalHandler
    from .overlay_client import OverlayClient
    from .gui import MinerTrackerGUI
    from .events_dispatcher import dispatcher
    from .status_flags import StatusFlags, StatusFlags2
except ImportError:
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys_path_added = False
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    from models import MiningSpot
    from database import DatabaseManager
    from journal_handler import JournalHandler
    from overlay_client import OverlayClient
    from gui import MinerTrackerGUI
    from events_dispatcher import dispatcher

    try:
        from status_flags import StatusFlags, StatusFlags2
    except ImportError:
        StatusFlags = None
        StatusFlags2 = None

logger = logging.getLogger("MinerTracker")


class MinerTrackerPlugin:
    def __init__(self, plugin_dir: str):
        db_path = os.path.join(plugin_dir, "miner_tracker.db")
        self.db_manager = DatabaseManager(db_path)
        self.overlay = OverlayClient("MinerTracker")
        self.journal_handler = JournalHandler(self.db_manager)
        self._gui: Optional[MinerTrackerGUI] = None

        # Current game state tracking
        self.current_location: Optional[Dict[str, Any]] = None
        self.is_on_surface: bool = False

    def handle_event(
        self,
        cmdr: str,
        is_beta: bool,
        system: str,
        station: str,
        entry: Any,
        state: Dict[str, Any],
    ):
        # 1. Update internal state from the latest game status
        self._update_internal_state(entry, state)

        # 2. Process journal events via handler
        self.journal_handler.handle_event(cmdr, is_beta, system, station, entry, state)

    def _update_internal_state(self, entry: Any, state: Dict[str, Any]):
        """Updates location and surface status from the journal/status data."""
        # Get System name (priority to state for current status)
        system_name = state.get("SystemName") or entry.get("StarSystem")
        # Get Body name
        raw_body_name = state.get("BodyName") or entry.get("Body")

        if system_name and raw_body_name:
            # Fix Issue 1: Remove star system from body name if it's concatenated
            clean_body_name = str(raw_body_name)
            system_str = str(system_name)
            if system_str in clean_body_name:
                clean_body_name = clean_body_name.replace(system_str, "").strip()

            self.current_location = {
                "star_system": str(system_name),
                "body_name": clean_body_name,
                "latitude": state.get("Latitude"),
                "longitude": state.get("Longitude"),
            }

        # Determine if we are on surface using status flags
        self._determine_surface_status(state)

    def _determine_surface_status(self, state: Dict[str, Any]):
        """Determines if the player is on a planet surface using status flags."""
        if not StatusFlags or not StatusFlags2:
            # Fallback to simple coordinate check if enums aren't loaded
            self.is_on_surface = (
                state.get("Latitude") is not None and state.get("Longitude") is not None
            )
            return

        flags = StatusFlags(state.get("Flags", 0))
        flags2 = StatusFlags2(state.get("Flags2", 0))

        is_on_surface = False
        if StatusFlags.HAVE_LATLONG in flags:
            if StatusFlags.IN_SHIP in flags or StatusFlags.IN_FIGHTER in flags:
                if StatusFlags.LANDED in flags:
                    is_on_surface = True
            elif StatusFlags.IN_SRV in flags or StatusFlags.LANDED in flags:
                is_on_surface = True
            elif (
                StatusFlags2.ON_FOOT in flags2
                and StatusFlags2.PLANET_ON_FOOT in flags2
                and StatusFlags2.SOCIAL_ON_FOOT not in flags2
                and StatusFlags2.STATION_ON_FOOT not in flags2
            ):
                is_on_surface = True

        self.is_on_surface = is_on_surface
        if self._gui:
            self._gui.set_current_location(self.current_location, self.is_on_surface)

    def get_gui(self, parent) -> Optional[MinerTrackerGUI]:
        if self._gui is None:
            self._gui = MinerTrackerGUI(parent, self.db_manager, self.overlay)
            # Initial state sync
            self._gui.current_location = self.current_location
            self._gui.is_on_surface = self.is_on_surface
        return self._gui

    def update_gui_state(self, location: Optional[Dict[str, Any]], on_surface: bool):
        if self._gui:
            self._gui.set_current_location(location, on_surface)


# Global plugin instance for EDMC to hold onto
_instance = None


def plugin_start3(plugin_dir: str) -> str:
    global _instance
    _instance = MinerTrackerPlugin(plugin_dir)
    return "Miner Tracker"


def journal_entry(cmdr, is_beta, system, station, entry, state):
    if _instance:
        _instance.handle_event(cmdr, is_beta, system, station, entry, state)


def dashboard_entry(cmdr: str, is_beta: bool, entry: Dict[str, Any]) -> str:
    """The specific hook for Status updates (Dashboard)."""
    if _instance:
        # The Dashboard entry provides the 'entry' which is the status dictionary.
        _instance._update_internal_state(entry, entry)
        return ""
    return ""


def plugin_app(parent):
    if _instance:
        return _instance.get_gui(parent)
    return None


def shutdown():
    global _instance
    if _instance and hasattr(_instance, "_gui") and _instance._gui:
        _instance._gui.destroy()
