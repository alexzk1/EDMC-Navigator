import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .add_spot_dialog import AddSpotDialog
from .coordinate import CoordinateFormatter
from .database import DatabaseManager
from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .models import StarSystem, SurfaceSpot
from .overlay_client import OverlayClient
from .player_location import (
    DEFAULT_PLANET_RADIUS,
    NavigationUtils,
    PlayerLocation,
    SurfacePoint,
    in_game_timestamp,
)
from .presets import PresetManager
from .spot_flags import SurfaceSpotFlags
from .ui_tooltip import Tooltip

# A manually navigated point is only recorded as a temporary mark when it is not
# within this many metres of an existing spot -- otherwise walking to a saved
# bookmark (or pasting your own earlier coordinate) would clutter the DB with a
# duplicate mark. Reuses the same flat-earth distance as the mining-spot query.
MANUAL_NAV_DEDUP_METERS = 50.0


def render_note(spot: SurfaceSpot) -> str:
    """Renders the note column for the main table.

    Tritium rings (TRITIUM_RING_PRESENT) get a fuel-pump marker so they stand
    out - this is fuel found in random places, worth remembering on its own.
    Temporary marks (IS_TEMPORARY_MARK) get a clock emoji prefix instead.
    """
    if SurfaceSpotFlags.TRITIUM_RING_PRESENT in spot.flags:
        return "\u26fd " + (spot.notes or "Tritium Ring")
    note = spot.notes or "-"
    if SurfaceSpotFlags.IS_TEMPORARY_MARK in spot.flags:
        note = f"\U0001f550 {note}"
    return note


def is_navigable(
    target: PlayerLocation,
    current_location: PlayerLocation | None,
    current_system: StarSystem | None,
) -> bool:
    """Whether a navigation target can be reached from the current position.

    We can only navigate to a spot we are actually standing on: the player must
    be on a surface (``current_location`` set) in the same star and on the same
    body as the target. A target in another system or body is a valid search
    result, but not a navigation target until the player gets there.
    """
    if (
        current_location is None
        or current_system is None
        or target.player_coord is None
    ):
        return False
    return (
        target.body_name == current_location.body_name
        and target.star_system.star_name == current_system.star_name
    )


class MainGUIWidget(ttk.Frame):
    # Width (px) of the narrow numeric-style columns: "#", "body", "rigs", "nav".
    _NUMERIC_COLUMNS_WIDTH: int = 15
    # Width (px) of the distance column ("340 m" / "12.3 km").
    _DISTANCE_COLUMN_WIDTH: int = 70
    # Minimum seconds between two GUI refreshes driven by position updates.
    # Coordinate events arrive every ~1-2s, but re-sorting the table that often
    # would flicker; 5s keeps it smooth while staying responsive.
    REFRESH_INTERVAL_SEC: float = 5.0

    def __init__(
        self,
        parent: tk.Tk,
        db_manager: DatabaseManager,
        overlay_client: OverlayClient,
        preset_manager: PresetManager,
    ):
        super().__init__(parent)
        self.last_known_full_body = ""
        # Wall-clock time of the last GUI refresh; gates the distance re-sort.
        self._last_gui_refresh: float = 0.0
        self.db_manager = db_manager
        self.overlay = overlay_client
        self.preset_manager = preset_manager
        self.current_location: PlayerLocation | None = None
        self.current_system: StarSystem | None = None

        # Reference to the single floating builder, or None when closed.
        # We never cache an "open" flag: a self-destroyed builder reports
        # winfo_exists() == 0, so this double as the "is it alive" check.
        self._query_builder: Any = None

        self._setup_ui()
        self._load_data()

        dispatcher.subscribe(KnownEvents.DATABASE_MODIFIED, self._on_db_modified)
        dispatcher.subscribe(KnownEvents.POSITION_UPDATED, self._set_current_location)

    def _setup_ui(self):
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_container, text="📍🗺️ Surface Spots", font=("Helvetica", 12, "bold")
        ).pack()

        # Toolbar (Horizontal layout for buttons)
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(5, 5))

        self._btn_add = ttk.Button(
            toolbar, text="📝 Record Spot", command=self._open_add_dialog
        )
        self._btn_add.pack(side=tk.LEFT, padx=2)

        self._btn_navigate = ttk.Button(
            toolbar, text="🧭 Navigate To", command=self._on_navigate
        )
        self._btn_navigate.pack(side=tk.RIGHT, padx=2)

        self._btn_manage = ttk.Button(
            toolbar, text="💼 Manage", command=self._open_query_builder
        )
        self._btn_manage.pack(side=tk.RIGHT, padx=2)

        # Manual coordinate entry -- a full-width cell between the toolbar and
        # the table. Paste/dict a ``{"lat": ..., "lon": ...}`` string here and
        # press Navigate; clicking a row overwrites the field with that row's
        # coordinates. The field is the single source for navigation, so it is
        # never cleared by position/system events (see ``_on_table_select``).
        coord_frame = ttk.Frame(main_container)
        coord_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(coord_frame, text="Coordinates:").pack(side=tk.LEFT)
        self._coord_entry = ttk.Entry(coord_frame)
        self._coord_entry.pack(fill=tk.X, side=tk.LEFT, expand=True)

        # Treeview with scrollbar
        tree_container = ttk.Frame(main_container)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = (
            "#",
            "dist",
            "mineral",
            "body",
            "note",
            "rigs",
            "nav",
            "lat",
            "lon",
            "db_id",
        )
        self._tree = ttk.Treeview(
            tree_container, columns=columns, show="headings", height=8
        )
        for col in columns:
            if col in ["lat", "lon", "db_id"]:
                self._tree.column(col, width=0, stretch=False)
                self._tree.heading(col, text="")
            else:
                width = 50
                if col == "note":
                    width = 80
                if col in ["rigs", "nav", "#"]:
                    width = self._NUMERIC_COLUMNS_WIDTH
                if col == "dist":
                    width = self._DISTANCE_COLUMN_WIDTH
                self._tree.column(col, width=width)
                self._tree.heading(col, text=col.capitalize())
        self._sync_view_columns(missing_body=True)
        scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self._tree.yview,  # type: ignore
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # Selecting a row overwrites the manual coordinate field with that row's
        # coordinates (full precision). See ``_on_table_select``.
        self._tree.bind("<<TreeviewSelect>>", self._on_table_select)

        # Static hover tooltips -- nothing here changes at runtime, so one pass
        # in ``_setup_ui`` covers every control.
        self._bind_tooltips()

    def _bind_tooltips(self) -> None:
        """Attach a short, static hover tooltip to each main control."""
        Tooltip(
            self._tree,
            "Your saved surface spots in current system or on current body.\nSelect one, then navigate to it.",
        )
        Tooltip(
            self._btn_add,
            "Record a surface spot at your current location or at any manually entered.",
        )
        Tooltip(
            self._btn_navigate,
            "Navigate to the coordinates in the field above. Click a row to fill "
            "the field, or paste/dict coordinates and press Navigate.",
        )
        Tooltip(
            self._btn_manage,
            "Advanced usage of the local spots database.",
        )

    def _sync_view_columns(self, missing_body: bool):
        """Toggle the ``body`` and ``#`` (numbering) columns for the current view.

        When body information is missing we are looking at a whole system, so
        spots can belong to different bodies - show the ``body`` column and hide
        the per-body numbering. Once we are on a specific body every spot belongs
        to it, so hide ``body`` and reveal the ``#`` numbering column instead.
        The two columns are exact inverses of each other.
        """
        if missing_body:
            self._tree.column("body", width=self._NUMERIC_COLUMNS_WIDTH, stretch=True)
            self._tree.heading("body", text="Body")
            self._tree.column("#", width=0, stretch=False)
            self._tree.heading("#", text="")
            self._tree.column("dist", width=0, stretch=False)
            self._tree.heading("dist", text="")
        else:
            self._tree.column("body", width=0, stretch=False)
            self._tree.heading("body", text="")
            self._tree.column("#", width=self._NUMERIC_COLUMNS_WIDTH, stretch=False)
            self._tree.heading("#", text="#")
            self._tree.column("dist", width=self._DISTANCE_COLUMN_WIDTH, stretch=False)
            self._tree.heading("dist", text="Dist")

    def _load_data(self):

        is_system_list: bool = self.current_location is None
        for item in self._tree.get_children():
            self._tree.delete(item)
        spots = (
            self.db_manager.get_system_spots(self.current_system)
            if is_system_list
            else self.db_manager.get_planetary_spots(self.current_location)
        )

        for number, spot in enumerate(spots, start=1):
            self._tree.insert(
                "",
                tk.END,
                values=(
                    number,
                    "—",  # filled by _sort_by_distance; hidden in system view
                    (spot.mineral_type or spot.mineral_original or "-").capitalize(),
                    spot.body_name or "-",
                    render_note(spot),
                    spot.max_miners,
                    spot.spot_number or "-",
                    spot.latitude,
                    spot.longitude,
                    spot.id,
                ),
            )

    def _on_navigate(self) -> None:
        """Navigate to the coordinate in the manual entry field.

        The field is the single source of truth: it is parsed with
        :class:`CoordinateFormatter` and must yield a valid point, otherwise the
        click cancels any active navigation (an empty or unparseable field means
        "go nowhere"). When the point matches the currently selected row it is
        just navigation to a saved bookmark; otherwise it is a manual navigation
        and a temporary mark is recorded (unless an existing spot is already
        within ``MANUAL_NAV_DEDUP_METERS``).
        """
        point = self._parse_navigation_field()
        if point is None:
            # Empty or unparseable field -> "go nowhere": cancel any active
            # navigation arrow rather than leaving a stale one on screen.
            self.overlay.navigate_to(None)
            return

        selection = self._tree.selection()
        selected = self._selected_point(selection[0]) if selection else None
        # A plain table click fills the field with the selected row's exact
        # coordinates, so a match means "navigate to a saved spot".
        is_saved_spot = selected is not None and selected == point

        if not self._do_navigation(point):
            return  # overlay error already shown

        if not is_saved_spot:
            self._maybe_record_manual_navigation(point)

    def _on_table_select(self, _event: Any = None) -> None:
        """Overwrite the manual field with the selected row's coordinates.

        Full precision is used (see ``CoordinateFormatter.to_string``) so the
        field navigates exactly. An empty selection leaves the field untouched -
        a deselection must not erase a manually entered coordinate, and neither
        does jumping / entering / leaving a body (those never touch the field).
        """
        selection = self._tree.selection()
        if not selection:
            return
        point = self._selected_point(selection[0])
        if point is None:
            return
        self._coord_entry.delete(0, tk.END)
        self._coord_entry.insert(0, CoordinateFormatter.to_string(point))
        self._coord_entry.selection_range(0, tk.END)
        self._coord_entry.focus()

    def _parse_navigation_field(self) -> SurfacePoint | None:
        """Parse the manual coordinate field, or ``None`` when empty/invalid."""
        ret = CoordinateFormatter.parse(self._coord_entry.get())
        if ret is not None:
            self._coord_entry.delete(0, tk.END)
            self._coord_entry.insert(0, CoordinateFormatter.to_string(ret))
        return ret

    def _selected_point(self, item: str | None) -> SurfacePoint | None:
        """The full-precision coordinate of a selected row, or ``None``."""
        if not item:
            return None
        row = dict(zip(self._tree["columns"], self._tree.item(item, "values")))
        try:
            return SurfacePoint(float(row["lat"]), float(row["lon"]))
        except (ValueError, KeyError, TypeError):
            return None

    def _do_navigation(self, point: SurfacePoint) -> bool:
        """Send ``point`` to the overlay; returns ``True`` if it started.

        Shows the appropriate warning and returns ``False`` when there is no
        body to navigate on or the overlay is not installed/active.
        """
        if self.current_location is None:
            self.overlay.navigate_to(None)
            messagebox.showwarning(
                "Navigation Error",
                "Cannot navigate to system markers. Please approach a body first.",
            )
            return False
        self.overlay.navigate_to(point)
        if not self.overlay.is_navigating():
            messagebox.showwarning(
                "Navigation Error",
                "Navigation was not started. Most likely overlay is not installed.",
            )
            return False
        return True

    def _maybe_record_manual_navigation(self, point: SurfacePoint) -> None:
        """Record a manual navigation as a ~1 hour temporary mark.

        Skipped when we have no current body, or when an existing spot is already
        within ``MANUAL_NAV_DEDUP_METERS`` (a manual navigation onto a bookmark
        is not a new point to remember). The mark's note stamps the time, e.g.
        "manually navigated at 14:30:05".
        """
        if self.current_location is None:
            return
        body = self.current_location.body_name
        system = self.current_location.star_system
        if not body or system is None:  # type: ignore
            return
        radius = self.current_location.radius_meters or DEFAULT_PLANET_RADIUS
        if self.db_manager.find_any_spot_near(
            system, body, point, MANUAL_NAV_DEDUP_METERS, radius
        ):
            return
        note = f"manually navigated at {in_game_timestamp('%H:%M:%S')}"
        self.db_manager.create_manual_navigation_mark(system, body, point, note)

    def _navigate_from_builder(self, target: PlayerLocation) -> None:
        """Navigate to a spot the query builder assembled from a results row.

        The builder only forwards a target when all four fields are present;
        here we validate *context* -- we must actually be standing on that body.
        """
        if not is_navigable(target, self.current_location, self.current_system):
            if self.current_location is None:
                messagebox.showwarning(
                    "Navigation Error",
                    "Cannot navigate to system markers. Please approach a body first.",
                )
            else:
                messagebox.showwarning(
                    "Navigation Error",
                    "That spot is not in your current system and body. "
                    "Travel there first.",
                )
            return
        self.overlay.navigate_to(target.player_coord)
        if not self.overlay.is_navigating():
            messagebox.showwarning(
                "Navigation Error",
                "Navigation was not started. Most likely overlay is not installed.",
            )

    def _on_db_modified(self, data: EventParams | None = None) -> None:
        """Rebuild the whole table after a DB change (add/update/delete, possibly
        done in bulk) and re-sort by distance.

        The 5s throttle is intentionally skipped here: a DB change is a real,
        already-known event that must be reflected immediately.
        """
        selected_ids = self._capture_selected_ids()
        self._rebuild_and_sort()
        self._restore_selection(selected_ids)
        self._last_gui_refresh = time.time()

    def _rebuild_and_sort(self) -> None:
        """Rebuild the table from the DB (rows come back in ``id`` order) and then
        order them by distance to the player.

        When no coordinates are available (e.g. aboard a carrier) distance
        sorting is a no-op, so the freshly loaded ``id`` order is kept as-is.
        """
        self._load_data()
        self._sort_by_distance()

    def _sort_by_distance(self) -> None:
        """Reorder the *existing* rows by great-circle distance to the player.

        Rows are only moved (never rebuilt), so the selection survives untouched.
        A no-op when the player has no surface coordinates - the rows are then
        already in ``id`` order straight from the DB.
        """
        loc = self.current_location
        if loc is None or loc.player_coord is None:
            return
        radius = loc.radius_meters or DEFAULT_PLANET_RADIUS
        player = SurfacePoint(loc.player_coord.latitude, loc.player_coord.longitude)
        rows: list[tuple[str, float]] = []
        for item in self._tree.get_children():
            row = dict(zip(self._tree["columns"], self._tree.item(item, "values")))
            try:
                lat = float(row["lat"])
                lon = float(row["lon"])
            except (ValueError, KeyError):
                continue
            rows.append(
                (
                    item,
                    NavigationUtils.haversine_distance(
                        player, SurfacePoint(lat, lon), radius
                    ),
                )
            )
        rows.sort(key=lambda pair: pair[1])
        for item, dist in rows:
            self._tree.set(item, "dist", NavigationUtils.format_distance(dist))
        for item, _ in rows:
            self._tree.move(item, "", "end")

    def _capture_selected_ids(self) -> list[int]:
        ids: list[int] = []
        for item in self._tree.selection():
            row = dict(zip(self._tree["columns"], self._tree.item(item, "values")))
            try:
                ids.append(int(row["db_id"]))
            except (KeyError, ValueError, TypeError):
                pass
        return ids

    def _restore_selection(self, ids: list[int]) -> None:
        if not ids:
            return
        for item in self._tree.selection():
            self._tree.selection_remove(item)
        for item in self._tree.get_children():
            row = dict(zip(self._tree["columns"], self._tree.item(item, "values")))
            try:
                if int(row["db_id"]) in ids:
                    self._tree.selection_add(item)
            except (KeyError, ValueError, TypeError):
                pass

    def _set_current_location(self, data: EventParams):
        """Update the GUI's knowledge of where we are and whether we are on surface.

        A rebuild fires on a view toggle (system <-> surface), a body change
        (landing, take off, carrier jump) or a system change (a jump to a new
        star, or the very first event after startup - when ``current_system``
        goes from ``None`` to a real value). A pure position move while staying
        on the same body is throttled to once per ``REFRESH_INTERVAL_SEC`` so the
        re-sort does not flicker on the ~1-2s coordinate stream.
        """
        was_on_surface = self.current_location is not None
        prev_system = self.current_system
        self.current_location = data.location
        self.current_system = data.system
        body = ""
        if self.current_location is not None:
            self.current_system = self.current_location.star_system
            body = (
                self.current_location.star_system.star_name
                + " "
                + self.current_location.body_name
            )
        need_switch = was_on_surface != (self.current_location is not None)
        system_changed = prev_system is None or (
            self.current_system is not None
            and prev_system.star_name != self.current_system.star_name
        )
        body_changed = body != self.last_known_full_body
        if need_switch or body_changed or system_changed:
            if need_switch:
                self._sync_view_columns(missing_body=self.current_location is None)
            self.last_known_full_body = body
            self._rebuild_and_sort()
            self._last_gui_refresh = time.time()
        elif (
            self.current_location is not None
            and time.time() - self._last_gui_refresh >= self.REFRESH_INTERVAL_SEC
        ):
            self._sort_by_distance()
            self._last_gui_refresh = time.time()

    def _open_add_dialog(self):
        parent: Any = self.winfo_toplevel()
        AddSpotDialog(
            parent=parent,
            db_manager=self.db_manager,
            current_location=self.current_location,
        )

    def _open_query_builder(self):
        """Open the non-modal query-builder window (selection only).

        The builder is a ``Toplevel`` so it can float on a second monitor while
        the main window stays usable. Destructive actions stay on explicit
        buttons inside the builder -- never inline in the builder itself.

        Only one builder exists at a time: a repeat click raises the
        already-open window instead of spawning a second one.
        """
        builder = self._query_builder
        if builder is not None and builder.winfo_exists():
            # Already open (possibly on another monitor): bring it forward.
            builder.raise_window()
            builder.focus_set()
            return

        from .query_builder.builder_window import QueryBuilderWindow
        from .star_resolver import StarDataResolver

        parent: Any = self.winfo_toplevel()
        # Pass a PlayerLocation on a body, or just the system in space (both is
        # what the builder's ``loc`` param expects). When the game is not
        # running this is None, and the builder copes (see its constructor).
        loc = self.current_location or self.current_system
        self._query_builder = QueryBuilderWindow(
            parent,
            db_manager=self.db_manager,
            preset_manager=self.preset_manager,
            loc=loc,
            star_resolver=StarDataResolver(self.db_manager),
            navigate=self._navigate_from_builder,
        )
