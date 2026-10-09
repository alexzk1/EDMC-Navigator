import time
import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .add_spot_dialog import AddSpotDialog
from .database import DatabaseManager
from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .models import StarSystem, SurfaceSpot
from .overlay_client import OverlayClient
from .player_location import DEFAULT_PLANET_RADIUS, NavigationUtils, PlayerLocation, SurfacePoint
from .spot_flags import SurfaceSpotFlags


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
        self, parent: tk.Tk, db_manager: DatabaseManager, overlay_client: OverlayClient
    ):
        super().__init__(parent)
        self.last_known_full_body = ""
        # Wall-clock time of the last GUI refresh; gates the distance re-sort.
        self._last_gui_refresh: float = 0.0
        self.db_manager = db_manager
        self.overlay = overlay_client
        self.current_location: PlayerLocation | None = None
        self.current_system: StarSystem | None = None

        self._setup_ui()
        self._load_data()

        dispatcher.subscribe(KnownEvents.DATABASE_MODIFIED, self._on_db_modified)
        dispatcher.subscribe(KnownEvents.POSITION_UPDATED, self._set_current_location)

    def _setup_ui(self):
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            main_container, text="Surface Spots", font=("Helvetica", 12, "bold")
        ).pack()

        # Toolbar (Horizontal layout for buttons)
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(5, 5))

        self._btn_add = ttk.Button(
            toolbar, text="Record Spot", command=self._open_add_dialog
        )
        self._btn_add.pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="Navigate To", command=self._on_navigate).pack(
            side=tk.RIGHT, padx=2
        )

        # Treeview with scrollbar
        tree_container = ttk.Frame(main_container)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ("#", "dist", "mineral", "body", "note", "rigs", "nav", "lat", "lon", "db_id")
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
        selection = self._tree.selection()
        if not selection:
            if self.overlay.is_navigating():
                # Cancel navigation (is it possible to reset selection though?)
                self.overlay.navigate_to(None)
            else:
                messagebox.showwarning("Warning", "Please select a spot first.")
            return

        if self.current_location is None:
            self.overlay.navigate_to(None)
            messagebox.showwarning(
                "Navigation Error",
                "Cannot navigate to system markers. Please approach a body first.",
            )
            return

        columns = self._tree["columns"]
        values = self._tree.item(selection[0], "values")
        row_dict = dict(zip(columns, values))

        try:
            lat = float(row_dict["lat"])
            lon = float(row_dict["lon"])
            self.overlay.navigate_to(SurfacePoint(lat, lon))
            if not self.overlay.is_navigating():
                raise RuntimeError(
                    "Navigation was not started. Most likely overlay is not installed."
                )
        except (ValueError, IndexError, RuntimeError) as e:
            messagebox.showwarning("Navigation error", f"{e}")

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
            self._tree.set(item, "dist", self._format_distance(dist))
        for item, _ in rows:
            self._tree.move(item, "", "end")

    @staticmethod
    def _format_distance(dist: float) -> str:
        if dist == float("inf"):
            return "—"
        if dist < 1000:
            return f"{dist:.0f} m"
        return f"{dist / 1000:.1f} km"

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
