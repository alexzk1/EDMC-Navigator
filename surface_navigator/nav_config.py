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
    # Direction arrow: top-left corner of its square + side length in pixels.
    # The arrow is inscribed in that square. Defaults are tentative -- tune in-game.
    arrow_x: int = int((1920 - 80) / 2)
    arrow_y: int = 320
    arrow_size: int = 80


# How long (seconds) an overlay message/SVG stays on screen.
OVERLAY_TEXT_TIMEOUT_SEC: int = 10

# Identifier used for overlay messages (namespaced with a suffix per message).
MESSAGE_ID: str = "navigator_message"

# Distance (meters) under which navigation is considered "reached".
NAVIGATION_THRESHOLD_METERS: float = 20.0


# ---------------------------------------------------------------------------
# External star data (EDSM + Spansh)
# ---------------------------------------------------------------------------
# Per-request timeout (seconds) for the EDSM/Spansh star lookups done by the
# star resolver. Kept short so an unreachable host fails fast instead of
# hanging a search.
STAR_API_TIMEOUT_SEC: int = 20
