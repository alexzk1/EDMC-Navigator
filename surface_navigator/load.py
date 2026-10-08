import logging
import os
from collections.abc import Mapping, MutableMapping
from typing import Any

# Import components from within our plugin package
try:
    from .database import DatabaseManager
    from .events_dispatcher import EventParams, KnownEvents, dispatcher
    from .events_suppression_zone import surface_scan_suppression_manager
    from .main_gui_widget import MainGUIWidget
    from .mined_names import Commodities
    from .mining_event_detector import RhinoMiningEventDetector
    from .models import SurfaceSpot, RingScanStatus, StarSystem
    from .nav_config import GC_MAX_AGE_SECS, OverlayTextConf
    from .overlay_client import OverlayClient
    from .player_location import PlayerLocation, SurfacePoint, in_game_timestamp
    from .rhino_db_updater import RhinoMiningDbUpdater
    from .spot_flags import SurfaceSpotFlags
    from .status_flags import StatusFlags
except ImportError:
    import sys

    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)

    from database import DatabaseManager
    from events_dispatcher import EventParams, KnownEvents, dispatcher
    from events_suppression_zone import surface_scan_suppression_manager
    from main_gui_widget import MainGUIWidget
    from mined_names import Commodities
    from mining_event_detector import RhinoMiningEventDetector
    from models import SurfaceSpot, RingScanStatus, StarSystem
    from nav_config import GC_MAX_AGE_SECS, OverlayTextConf
    from overlay_client import OverlayClient
    from player_location import PlayerLocation, SurfacePoint, in_game_timestamp
    from rhino_db_updater import RhinoMiningDbUpdater
    from spot_flags import SurfaceSpotFlags
    from status_flags import StatusFlags

logger = logging.getLogger("SurfaceNavigator")


class SurfaceNavigatorPlugin:
    def __init__(self, plugin_dir: str):
        db_path = os.path.join(plugin_dir, "surface_navigator.db")
        self.db_manager = DatabaseManager(db_path)

        # Sweep expired temporary marks (gc_temporaries). Cheap: sub-ms even on
        # thousands of rows, so safe to run at startup.
        self.db_manager.gc_temporaries(GC_MAX_AGE_SECS)

        # Automatic DB update if user do not enter whole description and just starts mining near the marked spot.
        self.rhino_auto_update_db = RhinoMiningDbUpdater(self.db_manager)

        # TODO: add settings to configure overlay position
        self._overlay = OverlayClient(OverlayTextConf())
        self._mining_detector = RhinoMiningEventDetector()
        self._gui: MainGUIWidget | None = None

        # Current game state tracking
        self.current_location: PlayerLocation | None = None
        self.last_system: StarSystem = StarSystem(star_name="")

    def handle_journal_event(
        self,
        cmdr: str,
        is_beta: bool,
        system: str,
        station: str,
        entry: Mapping[str, Any],
        state: MutableMapping[str, Any],
    ):
        """Called by EDMC when a journal event occurs."""
        system_changed = self._update_last_system(system, entry)
        # Galactic coordinates only arrive on a jump, so only then enrich the DB.
        # ``CarrierJump`` (fleet carrier jump) carries ``StarPos`` too.
        if entry.get("event") in {"FSDJump", "CarrierJump"}:
            self.db_manager.update_existing_star_coords(self.last_system)
        if self._extract_location_from_journal(system, entry, state) or system_changed:
            self._emit_location()
        self._mining_detector.handle_journal_entry(
            cmdr, is_beta, system, station, entry, state
        )
        if entry.get("event") == "SAASignalsFound":
            self._handle_ring_scan(entry)
        if entry.get("event") == "CodexEntry":
            self._handle_codex_entry(entry)

    def _update_last_system(self, system: str, entry: Mapping[str, Any]) -> bool:
        """Rebuilds ``self.last_system`` from the event and reports whether we
        changed systems.

        The destination name always comes from the event. ``systemid`` (from
        ``SystemAddress``) and galactic coordinates (from ``StarPos``) are
        attached to the object only when the event provides them, so a value we
        never learn is never clobbered.
        """
        changed = system != self.last_system.star_name
        if changed:
            self.current_location = None
            self.last_system = StarSystem(star_name=system)

        if self.last_system.systemid is None:
            addr = entry.get("SystemAddress")
            if addr is not None:
                self.last_system.systemid = addr
                changed = True

        if (coords := self._parse_star_pos(entry)) is not None:
            self.last_system.x, self.last_system.y, self.last_system.z = coords

        return changed

    def _parse_star_pos(
        self, entry: Mapping[str, Any]
    ) -> tuple[float, float, float] | None:
        """Returns galactic ``StarPos`` ``[x, y, z]`` as floats, or None when the
        event carries no usable position (e.g. ``LoadGame`` resting in a system)."""
        star_pos = entry.get("StarPos")
        if not star_pos or len(star_pos) < 3:
            return None
        try:
            return float(star_pos[0]), float(star_pos[1]), float(star_pos[2])
        except (TypeError, ValueError):
            return None

    def _extract_location_from_journal(
        self, system: str, entry: Mapping[str, Any], state: MutableMapping[str, Any]
    ) -> bool:
        """Extracts location information from journal entries."""
        dirty_new_body: str = ""
        new_point: SurfacePoint | None = None
        loc_update_in_srv: bool = False
        had_approach: bool = False

        # Keeping as much as possible of existing data until we fly away.
        # Detect the body and/or coordinates in event.
        match entry["event"]:
            case "Location" | "CodexEntry":
                if "Latitude" in entry:
                    loc_update_in_srv = entry.get("InSRV", False)
                    new_point = SurfacePoint(
                        latitude=entry["Latitude"], longitude=entry["Longitude"]
                    )
            case "FSDJump" | "CarrierJump" | "LeaveBody" | "Resurrect":
                self.current_location = None
                # Reset any stored navigation in overlay, we're out...
                self._overlay.navigate_to(None)
                return True
            case (
                "ApproachBody"
                | "Touchdown"
                | "Liftoff"
                | "Embark"
                | "Disembark"
                | "SupercruiseExit"
            ):
                dirty_new_body = entry.get("Body") or ""
                if dirty_new_body == system:
                    dirty_new_body = ""
                had_approach = True
            case "ApproachSettlement":
                dirty_new_body = entry.get("BodyName") or ""
                had_approach = True
            case _:
                pass

        # We need to have location recorded or new body provided to create the record or both to update.
        if not dirty_new_body and not self.current_location:
            return False

        old_location = (
            self.current_location
            if self.current_location
            else PlayerLocation(star_system=self.last_system)
        )
        old_body = old_location.body_name
        new_body = self._clean_body_name(system, dirty_new_body)

        def refresh_srv_location() -> bool:
            # If record is related to the taxi / station -> do nothing....we could call taxi and left SRV,
            # though it has no sense, as SRV will explode later.
            if (
                entry.get("Taxi", False)
                or not entry.get("OnPlanet", False)
                or not self.current_location
            ):
                return False
            # That is was location update clearly stating we're in SRV.
            if loc_update_in_srv:
                self.current_location.srv_coord = self.current_location.player_coord
                self.current_location.is_boarded_srv = True
                return True

            if entry.get("SRV", False):
                match entry["event"]:
                    # Player enter SRV or ship launches SRV with player inside.
                    case "Embark" | "LaunchSRV":
                        self.current_location.srv_coord = (
                            self.current_location.player_coord
                        )
                        self.current_location.is_boarded_srv = True
                        return True
                    # Player exits SRV.
                    case "Disembark":
                        self.current_location.srv_coord = (
                            self.current_location.player_coord
                        )
                        self.current_location.is_boarded_srv = False
                        return True
                    # SRV is destroyed or back to ship.
                    case "SRVDestroyed" | "DockSRV":
                        self.current_location.is_boarded_srv = False
                        self.current_location.srv_coord = None
                        return True
                    case _:
                        pass
            # If some other events happen, and we're in SRV, update.
            if self.current_location.is_boarded_srv:
                self.current_location.srv_coord = self.current_location.player_coord
            # SRV coordinate update will be send as player coordinate update.
            return False

        flew_to_other_body: bool = bool(new_body and (new_body != old_body))
        if flew_to_other_body or not self.current_location:
            final_body_name = new_body or str(old_body or "")
            self.current_location = PlayerLocation(
                star_system=self.last_system,
                body_name=final_body_name,
                player_coord=new_point,
            )
            refresh_srv_location()
            return True

        # Update location if present as body remains the same yet.
        has_new_point: bool = new_point is not None
        if has_new_point:
            self.current_location.player_coord = new_point
        return had_approach or has_new_point or refresh_srv_location()

    def handle_dashboard_update(self, cmdr: str, is_beta: bool, entry: dict[str, Any]):
        """Called by EDMC when a Status update occurs (Dashboard)."""
        if self._extract_location_from_status(entry):
            self._emit_location()

    def _extract_location_from_status(self, entry: dict[str, Any]) -> bool:
        """Extracts location information from dashboard (Status) entries."""
        # Are we in deep space?
        if not self.current_location:
            return False

        status_body = self._clean_body_name(
            self.current_location.star_system.star_name,
            entry.get("BodyName") or self.current_location.body_name,
        )

        # Are we in deep space?
        if not status_body:
            return False

        flags = StatusFlags(entry.get("Flags", 0))
        had_changes = (
            self.current_location.is_boarded_srv != StatusFlags.IN_SRV in flags
            or StatusFlags.FSD_JUMP_IN_PROGRESS in flags
        )

        # If we got different body - reset everything, status updates more often.
        if status_body != self.current_location.body_name:
            self.current_location = PlayerLocation(
                star_system=self.current_location.star_system, body_name=status_body
            )
            had_changes = True

        self.current_location.is_boarded_srv = StatusFlags.IN_SRV in flags

        # Do we have lat/lon at all ?
        if StatusFlags.HAS_LATLONG in flags:
            lat = entry.get("Latitude")
            lon = entry.get("Longitude")
            if lat is not None and lon is not None:
                had_changes = True
                self.current_location.player_coord = SurfacePoint(
                    latitude=lat, longitude=lon
                )
                if self.current_location.is_boarded_srv:
                    self.current_location.srv_coord = self.current_location.player_coord
        if (h := entry.get("Heading")) is not None:
            had_changes = True
            self.current_location.heading_deg = h
        if (r := entry.get("PlanetRadius")) is not None:
            had_changes = True
            self.current_location.radius_meters = r
        return had_changes

    def _clean_body_name(self, system_name: str, raw_body_name: str) -> str:
        """Removes star system prefix from body name."""
        if raw_body_name.startswith(system_name + " "):
            body_name = raw_body_name[len(system_name + " ") :]
        else:
            body_name = raw_body_name
        return body_name

    def _handle_ring_scan(self, entry: Mapping[str, Any]) -> None:
        """Registers rings that contain Tritium (He3 fuel) from SAASignalsFound.

        Only tritium rings are worth remembering - fuel is found in random
        places, while every other material is mined at a single known location.
        For each signal we resolve its name through the fuzzy matcher and let
        the DB decide (match + dedup + insert).
        """
        signals = entry.get("Signals")
        if not signals:
            return
        system_name = self.last_system.star_name
        body = self._clean_body_name(system_name, entry.get("BodyName", ""))
        for signal in signals:
            name_from_log = signal.get("Type")
            if not name_from_log:
                continue
            fuzzy_matched_name = Commodities.resolve_db_value(name_from_log)
            added = self.db_manager.ensure_tritium_recorded(
                RingScanStatus(
                    system=self.last_system,
                    body=body,
                    name_from_log=name_from_log,
                    fuzzy_matched_name=fuzzy_matched_name,
                )
            )
            if added:
                break

    def _handle_codex_entry(self, entry: Mapping[str, Any]) -> None:
        """Drops a short-lived temporary mark for a scanned surface object.

        When the pilot scans something near the surface (composition scanner on
        the ship or SRV) we bookmark their current position so they can find
        their way back a few days later. We deliberately do not try to identify
        what was scanned - that is nobody's business but the pilot's and other
        plugins'. Marks are temporary (removed by ``gc_temporaries`` after a few
        days).

        A scan only counts when we have a known surface position - a CodexEntry
        without coordinates is an object scanned in space, so we ignore it. To
        keep a single settlement from becoming a cloud of bookmarks we suppress
        scans that fall inside the current exclusion zone.
        """
        loc = self.current_location
        if loc is None or loc.player_coord is None:
            # No known surface position - this is a scan of an object in space.
            return

        # One bookmark per area, not one per scan. Checked before touching the
        # DB so a settlement of scans collapses into a single mark.
        if surface_scan_suppression_manager.is_current_player_location_suppressed():
            return

        spot = SurfaceSpot(
            star_system=loc.star_system.star_name,
            body_name=loc.body_name,
            latitude=loc.player_coord.latitude,
            longitude=loc.player_coord.longitude,
            # In-game date (real UTC + 1286 years), e.g. "Scan at 3312-10-08 ...".
            notes=f"Scan at {in_game_timestamp()}",
            flags=SurfaceSpotFlags.IS_TEMPORARY_MARK,
        )
        if not self.db_manager.add_spot(spot):
            return

        # Record the area as suppressed. Done after the write: add_spot resets
        # exclusion zones on DATABASE_MODIFIED, so we add the zone last.
        surface_scan_suppression_manager.set_exclusion_zone_at_player_location()

    def _emit_location(self):
        dispatcher.dispatch(
            KnownEvents.POSITION_UPDATED,
            EventParams(
                system=self.last_system,
                location=self.current_location,
            ),
        )

    def create_gui(self, parent: Any) -> MainGUIWidget | None:
        if self._gui is None:
            self._gui = MainGUIWidget(parent, self.db_manager, self._overlay)
            self._gui.current_location = self.current_location
        return self._gui

    def shutdown(self):
        if self._gui:
            self._gui.destroy()


# Global plugin instance for EDMC to hold onto
_instance: SurfaceNavigatorPlugin | None = None


def plugin_start3(plugin_dir: str) -> str:
    global _instance
    _instance = SurfaceNavigatorPlugin(plugin_dir)
    return "Surface Navigator"


def journal_entry(
    cmdr: str,
    is_beta: bool,
    system: str,
    station: str,
    entry: Mapping[str, Any],
    state: MutableMapping[str, Any],
):
    if _instance:
        _instance.handle_journal_event(cmdr, is_beta, system, station, entry, state)


def dashboard_entry(cmdr: str, is_beta: bool, entry: dict[str, Any]) -> str:
    """The specific hook for Status updates (Dashboard)."""
    if _instance:
        _instance.handle_dashboard_update(cmdr, is_beta, entry)
        return ""
    return ""


def plugin_app(parent: Any) -> MainGUIWidget | None:
    if _instance:
        return _instance.create_gui(parent)
    return None


def shutdown():
    if _instance:
        _instance.shutdown()
