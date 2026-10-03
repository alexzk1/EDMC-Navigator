import os
from typing import Any

# Import components from within our plugin package
try:
    from .models import MiningSpot
    from .database import DatabaseManager
    from .journal_handler import JournalHandler
    from .overlay_client import OverlayClient
    from .gui import MinerTrackerGUI
    from .events_dispatcher import dispatcher
except ImportError as e:
    import sys
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.append(current_dir)
    from models import MiningSpot
    from database import DatabaseManager
    from journal_handler import JournalHandler
    from overlay_client import OverlayClient
    from gui import MinerTrackerGUI
    from events_dispatcher import dispatcher

class MinerTrackerPlugin:
    def __init__(self, plugin_dir: str):
        db_path = os.path.join(plugin_dir, "miner_tracker.db")
        self.db_manager = DatabaseManager(db_path)
        self.overlay = OverlayClient("MinerTracker")
        self.journal_handler = JournalHandler(self.db_manager)

    def handle_event(self, cmdr: str, is_beta: bool, system: str, station: str, entry: Any, state: Any):
        return self.journal_handler.handle_journal_entry(cmdr, is_beta, system, station, entry, state)

    def get_gui(self, parent) -> MinerTrackerGUI:
        from .gui import MinerTrackerGUI # Local import to avoid issues during early load if any
        return MinerTrackerGUI(parent, self.db_manager, self.overlay)

# Global plugin instance for EDMC to hold onto
_instance = None

def plugin_start3(plugin_dir: str) -> str:
    global _instance
    _instance = MinerTrackerPlugin(plugin_dir)
    return "Miner Tracker"

def journal_entry(cmdr, is_beta, system, station, entry, state):
    if _instance:
        _instance.handle_event(cmdr, is_beta, system, station, entry, state)

def plugin_app(parent):
    """The main hook for EDMC to inject our UI."""
    if _instance:
        return _instance.get_gui(parent)
    return None

def shutdown():
    global _instance
    # If we had a running GUI loop, we would stop it here.
    # But since it's embedded in EDMC, the main thread handles closure.
    pass
