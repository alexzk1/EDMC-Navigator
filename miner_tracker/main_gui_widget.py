import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .add_spot_dialog import AddSpotDialog
from .database import DatabaseManager
from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .overlay_client import OverlayClient
from .player_location import PlayerLocation, SurfacePoint


class MainGUIWidget(ttk.Frame):
    def __init__(
        self, parent: tk.Tk, db_manager: DatabaseManager, overlay_client: OverlayClient
    ):
        super().__init__(parent)
        self.last_known_full_body = ""
        self.db_manager = db_manager
        self.overlay = overlay_client
        self.current_location: PlayerLocation | None = None

        self._setup_ui()
        self._load_data()

        dispatcher.subscribe(
            KnownEvents.DATA_BASE_MODIFIED, lambda data: self._refresh()
        )
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

        columns = ("note", "mineral", "spot", "lat", "lon", "db_id")
        self._tree = ttk.Treeview(
            tree_container, columns=columns, show="headings", height=8
        )
        for col in columns:
            if col in ["lat", "lon", "db_id"]:
                self._tree.column(col, width=0, stretch=False)
                self._tree.heading(col, text="")
            else:
                self._tree.column(col, width=120 if col in ["note"] else 70)
                self._tree.heading(col, text=col.capitalize())

        scrollbar = ttk.Scrollbar(
            tree_container,
            orient="vertical",
            command=self._tree.yview,  # type: ignore
        )
        self._tree.configure(yscrollcommand=scrollbar.set)

        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_data(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for spot in self.db_manager.get_planetary_spots(self.current_location):
            self._tree.insert(
                "",
                tk.END,
                values=(
                    spot.notes or "Unnamed Mark",
                    spot.mineral_type or spot.mineral_original or "-",
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
        vals = self._tree.item(selection[0], "values")
        try:
            lat = float(vals[3])
            lon = float(vals[4])
            self.overlay.navigate_to(SurfacePoint(lat, lon))
            if not self.overlay.is_navigating():
                raise RuntimeError(
                    "Navigation was not started. Most likely overlay is not installed."
                )
        except (ValueError, IndexError, RuntimeError) as e:
            messagebox.showwarning("Navigation error", f"{e}")

    def _refresh(self):
        self._load_data()

    def _open_add_dialog(self):
        parent: Any = self.winfo_toplevel()
        AddSpotDialog(
            parent=parent,
            db_manager=self.db_manager,
            current_location=self.current_location,
        )

    def _set_current_location(self, data: EventParams):
        """Update the GUI's knowledge of where we are and whether we are on surface."""
        self.current_location = data.location
        body = ""
        if self.current_location is not None:
            body = (
                self.current_location.star_system
                + " "
                + self.current_location.body_name
            )
        if body != self.last_known_full_body:
            self.last_known_full_body = body
            self._refresh()
