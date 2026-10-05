import logging
from collections.abc import Mapping, MutableMapping
from typing import Any

from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .mined_names import Commodities

logger = logging.getLogger("SurfaceNavigator")


class RhinoMiningEventDetector:
    """
    Pure logs processor which detects that some material was mined by Rhino.
    Produces the signal that material with 'name' was mined right now.
    """

    def __init__(self):
        # Note on location tracking, user may leave SRV to collect stuff and walk away -> location update is changed.
        pass

    def handle_journal_entry(
        self,
        cmdr: str,
        is_beta: bool,
        system: str,
        station: str,
        entry: Mapping[str, Any],
        state: MutableMapping[str, Any],
    ) -> str | None:
        """Main entry point for journal events from EDMC."""

        # Check if this is a mining-related event (Rhino SRV extraction)
        if self._is_mining_event(entry):
            self._process_mining_record(system, entry)

        return None

    def _is_mining_event(self, entry: Mapping[str, Any]) -> bool:
        """Identifies if the event is a mining/extraction record."""
        return entry.get("event") == "MiningRefined"

    def _process_mining_record(self, system: str, entry: Mapping[str, Any]):
        """Processes a mining record and triggers notification."""

        mineral = entry.get("Type")
        if not mineral:
            return
        fuzzy_mineral = Commodities.resolve_db_value(mineral)
        # Dispatch event so the UI can refresh or show overlay messages
        dispatcher.dispatch(
            KnownEvents.RHINO_MINING_DETECTED,
            EventParams(
                params={
                    "mineral_in_log": mineral,
                    "mineral_db": fuzzy_mineral,
                }
            ),
        )
