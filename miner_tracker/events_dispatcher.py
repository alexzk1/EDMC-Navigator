from typing import Callable, Dict, List

class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        if event_type not in self._listeners:
            self._listeners[event_type] = []
        self._listeners[event_type].append(callback)

    def dispatch(self, event_type: str, *args, **kwargs):
        if event_type in self._listeners:
            for callback in self._listeners[event_type]:
                try:
                    callback(*args, **kwargs)
                except Exception as e:
                    import logging
                    logging.getLogger("MinerTracker").error(f"Error dispatching {event_type}: {e}")

# Global instance for the plugin to use
dispatcher = EventDispatcher()
