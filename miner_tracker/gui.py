import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .database import DatabaseManager
from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .models import SurfaceSpot
from .overlay_client import OverlayClient
from .player_location import PlayerLocation, SurfacePoint


class AddSpotDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        db_manager: DatabaseManager,
        current_location: PlayerLocation | None = None,
    ):
        super().__init__(parent)
        self.title("Add [Mining] Spot")
        self.geometry("300x450")
        self.db_manager = db_manager

        container = ttk.Frame(self, padding="15")
        container.pack(fill=tk.BOTH, expand=True)

        # Form Fields
        fields = [
            ("Star System:", "system"),
            ("Body Name:", "body"),
            ("Mineral Type:", "mineral"),
            ("Latitude:", "lat"),
            ("Longitude:", "lon"),
            ("Spot #:", "spot"),
        ]

        self.entries: dict[str, Any] = {}
        for label_text, key in fields:
            ttk.Label(container, text=label_text).pack(anchor=tk.W)
            entry = ttk.Entry(container)
            entry.pack(fill=tk.X, pady=(0, 10))
            self.entries[key] = entry

        # Auto-populate from current location if available and fields are not disabled
        if current_location:
            if current_location.star_system:
                self.entries["system"].insert(0, str(current_location.star_system))
                self.entries["system"].config(state="disabled")
            if current_location.body_name:
                self.entries["body"].insert(0, str(current_location.body_name))
                self.entries["body"].config(state="disabled")
            if current_location.latitude is not None:
                self.entries["lat"].insert(0, str(current_location.latitude))
                self.entries["lat"].config(state="disabled")
            if current_location.longitude is not None:
                self.entries["lon"].insert(0, str(current_location.longitude))
                self.entries["lon"].config(state="disabled")

        ttk.Button(container, text="Save Spot", command=self._save).pack(
            pady=20, fill=tk.X
        )

    def _save(self):
        try:
            # Handle empty spot number string
            spot_num = self.entries["spot"].get().strip()
            spot_num_val = int(spot_num) if spot_num else None

            spot = SurfaceSpot(
                star_system=self.entries["system"].get(),
                body_name=self.entries["body"].get(),
                latitude=float(self.entries["lat"].get()),
                longitude=float(self.entries["lon"].get()),
                mineral_type=self.entries["mineral"].get()
                if self.entries["mineral"].get()
                else None,
                spot_number=spot_num_val,
            )
            if spot.star_system and spot.body_name:
                if self.db_manager.add_spot(spot):
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save to database.")
            else:
                messagebox.showwarning("Input Error", "System and Body are required.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numbers: {e}")


class MinerTrackerGUI(ttk.Frame):
    def __init__(
        self, parent: tk.Tk, db_manager: DatabaseManager, overlay_client: OverlayClient
    ):
        super().__init__(parent)
        self.db_manager = db_manager
        self.overlay = overlay_client
        self.current_location: PlayerLocation | None = None
        self.has_coords: bool = False

        self._setup_ui()
        self._load_data()

        dispatcher.subscribe(
            KnownEvents.RHINO_MINING_DETECTED, self._on_mining_record_found
        )
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
        # Initial button state
        self._btn_add.config(state="disabled")

    def _load_data(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for spot in self.db_manager.get_planetary_spots(self.current_location):
            self._tree.insert(
                "",
                tk.END,
                values=(
                    spot.notes or "Unnamed Mark",
                    spot.mineral_type or "-",
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

    def _on_mining_record_found(self, data: EventParams):
        # TODO: Implement logic: if latest mark is in close radius to latest known position and it has missing fields,
        # then update it DB record by those mining data. Note, it should be somehow cached to avoid repeated checks,
        # as mining signal is expected to repeated often while user keeps doing it.
        # Another note, probably logic must be in DB handler.
        # self._refresh()
        pass

    def _refresh(self):
        self._load_data()

    def _open_add_dialog(self):
        if not self.has_coords:
            messagebox.showwarning(
                "Location Error", "You must be on a planet surface to add a spot."
            )
            return

        parent: Any = self.winfo_toplevel()
        AddSpotDialog(
            parent=parent,
            db_manager=self.db_manager,
            current_location=self.current_location,
        )

    def _set_current_location(self, data: EventParams):
        """Update the GUI's knowledge of where we are and whether we are on surface."""
        self.current_location = data.location
        self.has_coords = (
            self.current_location is not None
            and self.current_location.player_coord is not None
        )
        if self.has_coords:
            self._btn_add.config(state="normal")
        else:
            self._btn_add.config(state="disabled")
