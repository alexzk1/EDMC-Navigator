from typing import Any, Protocol, runtime_checkable

from .models import StarSystem
from .player_location import PlayerLocation


class EventParams:
    """Dispatch event, it may have valid self.params, valid self.location or any of them or none of them.
    Context of the self.params is defined by issuer."""

    def __init__(
        self,
        params: dict[str, Any] | None = None,
        location: PlayerLocation | None = None,
        system: StarSystem | None = None,
    ):
        self.params: dict[str, Any] = params or {}
        self.location = location
        self.system = system


@runtime_checkable
class EventCallback(Protocol):
    """Subscribers interface"""

    def __call__(self, data: EventParams) -> None: ...


class EventDispatcher:
    """Global events dispatcher. It can send event from anybody to anybody subscribed via single global instance."""

    def __init__(self):
        self._listeners: dict[str, list[EventCallback]] = {}

    def subscribe(self, event_type: str, callback: EventCallback):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def dispatch(self, event_type: str, params: EventParams):
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(params)
                except Exception as e:  # noqa: BLE001
                    import logging

                    logging.getLogger("SurfaceNavigator").error(
                        f"Error dispatching {event_type}: {e}"
                    )


# Global instance for the plugin to use
dispatcher = EventDispatcher()


class KnownEvents:
    RHINO_MINING_DETECTED: str = "mining_record_detected"
    DATABASE_MODIFIED: str = "data_base_modified"
    # Provides valid location field (on body!) or None if location should be reset (player is not near the body).
    # Provides system field, at least .star_name is set there.
    POSITION_UPDATED: str = "position_updated"
