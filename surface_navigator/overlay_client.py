import logging
import time
from enum import Enum, auto

from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .nav_config import (
    MESSAGE_ID as CONFIG_MESSAGE_ID,
)
from .nav_config import (
    NAVIGATION_THRESHOLD_METERS,
    OVERLAY_TEXT_TIMEOUT_SEC,
    OverlayTextConf,
)
from .player_location import (
    DEFAULT_PLANET_RADIUS,
    NavigationUtils,
    PlayerLocation,
    SurfacePoint,
)
from .time_scheduler import scheduler
from .velocity_extrapolator import VelocityExtrapolator

try:
    try:
        from EDMCOverlay import edmcoverlay  # type: ignore
    except ImportError:
        from edmcoverlay import edmcoverlay  # type: ignore
except ImportError:
    edmcoverlay = None

logger = logging.getLogger("SurfaceNavigator")


class NavigationStatus(Enum):
    """Navigation statuses"""

    APPROACHING = auto()
    REACHED = auto()


class OverlayClient:
    """Main class to communicate with binary overlay."""

    # Timeout should be long enough to cover log update to avoid flickering,
    # and it should be short enough to avoid annoyance.
    TEXT_TIMEOUT_SEC: int = OVERLAY_TEXT_TIMEOUT_SEC
    MESSAGE_ID = CONFIG_MESSAGE_ID
    # Extrapolation only kicks in once real positions stop arriving. Keeping the
    # threshold below the game's ~2s Status cadence keeps the display fresh
    # between updates without spamming redundant projected positions.
    STALE_THRESHOLD_SEC: float = 1.0

    def __init__(self, conf: OverlayTextConf):
        self._config = conf
        self._overlay = None

        self._destination: SurfacePoint | None = None
        self._location: PlayerLocation | None = None

        # Position extrapolation keeps the overlay fresh between sparse game
        # updates. The overlay feeds it (single source of truth) and owns the
        # timer that drives the projection.
        self._extrapolator: VelocityExtrapolator = VelocityExtrapolator()
        self._last_real_ts: float = 0.0
        self._timer_id: int | None = None

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
        had_navigation: bool = self._location is not None and bool(
            self._location.body_name
        )
        will_have_navigation = data.location is not None and bool(
            data.location.body_name
        )
        self._location = data.location
        # ``data.location`` is None when we leave a body (in space) - there is
        # no surface coordinate to feed the extrapolator. The type checker also
        # needs this guard narrowed on ``self._location`` before we touch
        # ``.player_coord`` / ``.radius_meters``.
        if self._location is not None and self._location.player_coord is not None:
            self._extrapolator.update_pos(
                time.time(),
                self._location.player_coord,
                self._location.radius_meters or DEFAULT_PLANET_RADIUS,
            )
            self._last_real_ts = time.time()
        self._update_navigation()

        if had_navigation != will_have_navigation:
            self._visualize_navigation_switch(will_have_navigation)

    def _visualize_navigation_switch(self, is_going_on: bool):
        if self._overlay is None:
            return

        if self.supports_svg():
            approaching: str = """
            <svg xmlns:xlink="http://www.w3.org/1999/xlink" height="36" width="160" xmlns="http://www.w3.org/2000/svg" ><defs ></defs> <rect x="0" rx="18.0" ry="18.0" y="0" height="36" width="160" stroke="#00FF88" stroke-width="1.5" fill="rgba(0, 0, 0, 0.12)" /> <circle cx="20" cy="18.0" r="5" fill="#00FF88" /> <text x="35" y="23.0" font-weight="bold" font-family="Arial, sans-serif" font-size="14" fill="#00FF88" >APPROACHING</text></svg>
            """
            leaving: str = """<svg xmlns:xlink="http://www.w3.org/1999/xlink" height="36" width="160" xmlns="http://www.w3.org/2000/svg" ><defs ></defs> <rect x="0" rx="18.0" ry="18.0" y="0" height="36" width="160" stroke="#FF3344" stroke-width="1.5" fill="rgba(0, 0, 0, 0.12)" /> <circle cx="20" cy="18.0" r="5" fill="#FF3344" /> <text x="35" y="23.0" font-weight="bold" font-family="Arial, sans-serif" font-size="14" fill="#FF3344" >LEAVING</text></svg>"""
            self._overlay.send_svg(
                OverlayClient.MESSAGE_ID + "svg",
                approaching if is_going_on else leaving,
                self._config.left,
                self._config.top,
                OverlayClient.TEXT_TIMEOUT_SEC,
            )
        else:
            self._overlay.send_message(
                OverlayClient.MESSAGE_ID + "svg",
                "Approaching" if is_going_on else "Leaving",
                "#00FF88" if is_going_on else "#FF3344",
                self._config.left,
                self._config.top,
                OverlayClient.TEXT_TIMEOUT_SEC,
                self._config.size,
            )

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
        THRESHOLD_METERS = NAVIGATION_THRESHOLD_METERS
        if dist < THRESHOLD_METERS:
            return NavigationStatus.REACHED
        else:
            return NavigationStatus.APPROACHING

    def _update_navigation(self, position: SurfacePoint | None = None):
        # ``position`` overrides the live coordinate for a projected (fake)
        # update; otherwise we reuse the real player coordinate. Extrapolation
        # only makes sense while the player has a valid surface coordinate --
        # if either the location or the coordinate is gone, there is nothing to
        # navigate.
        player_coord = (
            position
            if position is not None
            else (self._location.player_coord if self._location else None)
        )
        if (
            self._destination is None
            or player_coord is None
            or self._location is None
            or self._overlay is None
        ):
            return

        dist = NavigationUtils.haversine_distance(
            player_coord,
            self._destination,
            self._location.radius_meters or DEFAULT_PLANET_RADIUS,
        )
        # A projected (extrapolated) position is only shown -- it must never
        # drop the active target or fire "Target Reached!". Real updates
        # (``position is None``) keep that behaviour.
        if position is None:
            status = OverlayClient._get_navigation_status(dist)
            if status == NavigationStatus.REACHED:
                # Drop target.
                self._destination = None
                self._stop_timer()
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

        bearing = NavigationUtils.calculate_bearing(player_coord, self._destination)
        dist_txt = NavigationUtils.format_distance(dist)
        if self.supports_multiline():
            txt = f"NAVIGATING:\n\tBearing: {bearing:.2f}°\n\tDistance: {dist_txt} (surface)"
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
            OverlayClient.MESSAGE_ID + "n",
            "NAVIGATING:",
            self._config.color,
            self._config.left,
            self._config.top,
            OverlayClient.TEXT_TIMEOUT_SEC,
            self._config.size,
        )
        self._overlay.send_message(
            OverlayClient.MESSAGE_ID,
            f"Bearing: {bearing:.2f}(deg)",
            self._config.color,
            self._config.left + 5,
            self._config.top + 20,
            OverlayClient.TEXT_TIMEOUT_SEC,
            self._config.size,
        )
        self._overlay.send_message(
            # Different ID so we don't erase 1st line.
            OverlayClient.MESSAGE_ID + "1",
            f"Distance: {dist_txt} (surface)",
            self._config.color,
            self._config.left + 5,
            self._config.top + 40,  # Estimated vertical size of the 1st line.
            OverlayClient.TEXT_TIMEOUT_SEC,
            self._config.size,
        )

    def is_navigating(self):
        return self._destination is not None and self.is_available()

    def navigate_to(self, point: SurfacePoint | None):
        self._destination = None
        self._stop_timer()
        if point is None or not self.is_available():
            return
        self._destination = point
        self._update_navigation()
        if not self._start_timer():
            # Navigation is only ever started from a GUI button, so a missing
            # GUI root here means something got out of order (Buratino?). We
            # still navigate -- just without the extrapolation timer.
            logger.warning(
                "Navigation started without a GUI root -- no extrapolation "
                "timer (did Buratino break the order again?)."
            )

    def _start_timer(self) -> bool:
        """Start the extrapolation timer. Returns False if no GUI root yet."""
        if self._timer_id is not None or not scheduler.has_gui():
            return False
        self._timer_id = scheduler.schedule(1000, self._tick)  # type: ignore
        return True

    def _stop_timer(self) -> None:
        if self._timer_id is not None:
            scheduler.cancel(self._timer_id)
            self._timer_id = None

    def _tick(self) -> None:
        if self._destination is not None and (
            time.time() - self._last_real_ts >= self.STALE_THRESHOLD_SEC
        ):
            est = self._extrapolator.extrapolate(time.time(), self._destination)
            if est is not None:
                self._update_navigation(position=est)
        self._timer_id = scheduler.schedule(1000, self._tick)  # type: ignore
