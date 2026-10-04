import logging
from dataclasses import dataclass
from enum import Enum, auto

from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .player_location import NavigationUtils, PlayerLocation, SurfacePoint

try:
    try:
        from EDMCOverlay import edmcoverlay  # type: ignore
    except ImportError:
        from edmcoverlay import edmcoverlay  # type: ignore
except ImportError:
    edmcoverlay = None

logger = logging.getLogger("SurfaceNavigator")


@dataclass(slots=True)
class OverlayTextConf:
    left: int = 10
    top: int = 250
    color: str = "#F013C8C8"
    color_reached: str = "#E4173DC7"
    size: str = "normal"


class NavigationStatus(Enum):
    """Navigation statuses"""

    APPROACHING = auto()
    REACHED = auto()


class OverlayClient:
    """Main class to communicate with binary overlay."""

    # Timeout should be long enough to cover log update to avoid flickering,
    # and it should be short enough to avoid annoyance.
    TEXT_TIMEOUT_SEC: int = 10
    DEFAULT_PLANET_RADIUS = 6371000.0
    MESSAGE_ID = "navigator_message"

    def __init__(self, conf: OverlayTextConf):
        self._config = conf
        self._overlay = None

        self._destination: SurfacePoint | None = None
        self._location: PlayerLocation | None = None

        self._has_multiline = False
        self._has_multiline = self.supports_multiline()

        self._has_svg = False
        self._has_svg = self.supports_svg()

        if edmcoverlay:
            try:
                from edmcoverlay import Overlay

                self._overlay = Overlay()
            except Exception as e:  # noqa: BLE001
                logger.error(f"Failed to initialize overlay client: {e}")

        dispatcher.subscribe(KnownEvents.POSITION_UPDATED, self._update_location)

    def _update_location(self, data: EventParams):
        self._location = data.location
        self._update_navigation()

    def is_available(self) -> bool:
        return self._overlay is not None

    def supports_svg(self) -> bool:
        return self._has_svg or (
            self._overlay is not None
            and hasattr(self._overlay, "is_svg_supported")
            and callable(self._overlay.is_svg_supported)
            and self._overlay.is_svg_supported()
        )

    def supports_multiline(self) -> bool:
        return self._has_multiline or (
            self._overlay is not None
            and hasattr(self._overlay, "is_multiline_supported")
            and callable(self._overlay.is_multiline_supported)
            and self._overlay.is_multiline_supported()
        )

    @staticmethod
    def _get_navigation_status(dist: float) -> NavigationStatus:
        THRESHOLD_METERS = 10.0
        if dist < THRESHOLD_METERS:
            return NavigationStatus.REACHED
        else:
            return NavigationStatus.APPROACHING

    def _update_navigation(self):
        if (
            self._destination is None
            or self._location is None
            or self._location.player_coord is None
            or self._overlay is None
        ):
            return

        dist = NavigationUtils.haversine_distance(
            self._location.player_coord,
            self._destination,
            self._location.radius_meters or OverlayClient.DEFAULT_PLANET_RADIUS,
        )
        status = OverlayClient._get_navigation_status(dist)
        if status == NavigationStatus.REACHED:
            # Drop target.
            self._destination = None
            # Overlay will show message for given time, than auto hide it.
            self._overlay.send_message(
                OverlayClient.MESSAGE_ID,
                "Target Reached!",
                self._config.color_reached,
                self._config.left,
                self._config.top,
                OverlayClient.TEXT_TIMEOUT_SEC,
                self._config.size,
            )
            return

        bearing = NavigationUtils.calculate_bearing(
            self._location.player_coord, self._destination
        )
        if self.supports_multiline():
            txt = f"Bearing: {bearing:.2f}°\nDistance: {dist:.2f}(m)"
            self._overlay.send_message(
                # Using the same ID will replace existing message on overlay and set fresh timeout.
                OverlayClient.MESSAGE_ID,
                txt,
                self._config.color,
                self._config.left,
                self._config.top,
                OverlayClient.TEXT_TIMEOUT_SEC,
                self._config.size,
            )
            return
        # Backup plan for other older overlay implementations which support only 1 strict line output.
        self._overlay.send_message(
            OverlayClient.MESSAGE_ID,
            f"Bearing: {bearing:.2f}(deg)",
            self._config.color,
            self._config.left,
            self._config.top,
            OverlayClient.TEXT_TIMEOUT_SEC,
            self._config.size,
        )
        self._overlay.send_message(
            # Different ID so we don't erase 1st line.
            OverlayClient.MESSAGE_ID + "1",
            f"Distance: {dist:.2f}(m)",
            self._config.color,
            self._config.left,
            self._config.top + 20,  # Estimated vertical size of the 1st line.
            OverlayClient.TEXT_TIMEOUT_SEC,
            self._config.size,
        )

    def is_navigating(self):
        return self._destination is not None and self.is_available()

    def navigate_to(self, point: SurfacePoint | None):
        self._destination = None
        if point is None or not self.is_available():
            return
        self._destination = point
        self._update_navigation()
