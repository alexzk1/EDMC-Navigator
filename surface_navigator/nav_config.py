"""Global plugin configuration.

Tunable values live here as module-level constants for now. A settings UI will
read/write these later; until then everything is a hardcoded default.

``OverlayTextConf`` is the config *object*: ``load.py`` builds one instance and
hands it to the overlay. Later the UI can build a new instance with modified
values and pass that in instead.
"""

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Temporary marks (gc_temporaries)
# ---------------------------------------------------------------------------
# Expired temporary marks (IS_TEMPORARY_MARK) older than this are swept at
# startup. Currently 3 days.
GC_MAX_AGE_SECS: int = 3 * 24 * 60 * 60  # 259200


# ---------------------------------------------------------------------------
# Overlay text / position
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class OverlayTextConf:
    left: int = 10
    top: int = 320
    color: str = "#62FF00"
    color_reached: str = "#FF0000"
    size: str = "normal"


# How long (seconds) an overlay message/SVG stays on screen.
OVERLAY_TEXT_TIMEOUT_SEC: int = 10

# Identifier used for overlay messages (namespaced with a suffix per message).
MESSAGE_ID: str = "navigator_message"

# Distance (meters) under which navigation is considered "reached".
NAVIGATION_THRESHOLD_METERS: float = 20.0
