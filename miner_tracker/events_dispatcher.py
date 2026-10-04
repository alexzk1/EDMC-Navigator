from typing import Any, Protocol, TypeAlias, runtime_checkable

EventParams: TypeAlias = dict[str, Any]


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

                    logging.getLogger("MinerTracker").error(
                        f"Error dispatching {event_type}: {e}"
                    )


# Global instance for the plugin to use
dispatcher = EventDispatcher()
