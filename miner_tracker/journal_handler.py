import logging
from typing import Any, Dict, Optional
from .models import MiningSpot
from .database import DatabaseManager
from .events_dispatcher import dispatcher

logger = logging.getLogger("MinerTracker")

class JournalHandler:
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        # Track the latest location to associate with mining events
        self._last_location: Optional[Dict[str, Any]] = None

    def handle_journal_entry(
        self, 
        cmdr: str, 
        is_beta: bool, 
        system: str, 
        station: str, 
        entry: Dict[str, Any], 
        state: Dict[str, Any]
    ) -> Optional[str]:
        """Main entry point for journal events from EDMC."""
        event_type = entry.get("event")

        # Update last known location/body information via the state object provided by EDMC
        if event_type in ["Location", "ApproachBody"] or "Body" in state:
            self._update_last_location(entry, state)

        # Check if this is a mining-related event (Rhino SRV extraction)
        if self._is_mining_event(entry):
            self._process_mining_record(system, entry)

        return None

    def _update_last_location(self, entry: Dict[str, Any], state: Dict[str, Any]):
        """Extracts location data from journal or current state."""
        # Prioritize 'state' as it is more reliable and up-to-date in EDMC plugins
        body = state.get("Body") 
        system_name = state.get("SystemName") or entry.get("StarSystem")

        if body and system_name:
            self._last_location = {
                "star_system": system_name,
                "body_name": str(body)
            }

    def _is_mining_event(self, entry: Dict[str, Any]) -> bool:
        """Identifies if the event is a mining/extraction record."""
        # "MiningRefined" matches what user indicated in log example
        return entry.get("event") == "MiningRefined"

    def _process_mining_record(self, system: str, entry: Dict[str, Any]):
        """Processes a mining record and triggers notification."""
        mineral = entry.get("Type", "Unknown Mineral")
        logger.info(f"MinerTracker: Processing {mineral} in {system}")
        
        # Dispatch event so the UI can refresh or show overlay messages
        dispatcher.dispatch("mining_record_detected", {"star_system": system, "mineral": mineral})

