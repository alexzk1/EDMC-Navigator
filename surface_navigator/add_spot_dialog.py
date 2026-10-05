import tkinter as tk
from tkinter import messagebox, ttk
from typing import Any

from .database import DatabaseManager
from .mined_names import Commodities
from .models import SurfaceSpot
from .player_location import PlayerLocation


class AddSpotDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Tk,
        db_manager: DatabaseManager,
        current_location: PlayerLocation | None = None,
    ):
        super().__init__(parent)
        self.title("Add Spot...")
        self.db_manager = db_manager

        window_width = 400
        window_height = 550
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")

        container = ttk.Frame(self, padding="15")
        container.pack(fill=tk.BOTH, expand=True)

        # Form Fields
        fields = [
            ("Note", "note"),
            ("Mining Spot #:", "spot"),
            ("Mining Rigs Max:", "miners_count"),
            ("Mineral Type:", "mineral"),
            ("Star System:", "system"),
            ("Body Name:", "body"),
            ("Latitude:", "lat"),
            ("Longitude:", "lon"),
        ]

        self.entries: dict[str, Any] = {}
        for label_text, key in fields:
            ttk.Label(container, text=label_text).pack(anchor=tk.W)
            entry = ttk.Entry(container)
            entry.pack(fill=tk.X, pady=(0, 10))
            self.entries[key] = entry

        self.entries["miners_count"].insert(0, "1")

        # Auto-populate from current location
        if current_location:
            if current_location.star_system:
                self.entries["system"].insert(0, str(current_location.star_system))
                self.entries["system"].config(state="disabled")
            if current_location.body_name:
                self.entries["body"].insert(0, str(current_location.body_name))
                self.entries["body"].config(state="disabled")
            if current_location.player_coord is not None:
                self.entries["lat"].insert(
                    0, str(current_location.player_coord.latitude)
                )
                self.entries["lon"].insert(
                    0, str(current_location.player_coord.longitude)
                )
                self.entries["lat"].config(state="disabled")
                self.entries["lon"].config(state="disabled")

        button_frame = ttk.Frame(container)
        button_frame.pack(fill=tk.X, pady=(15, 0))
        save_btn = ttk.Button(button_frame, text="Save", command=self._save)
        save_btn.pack(side=tk.LEFT, expand=True, padx=2)
        cancel_btn = ttk.Button(button_frame, text="Cancel", command=self.destroy)
        cancel_btn.pack(side=tk.LEFT, expand=True, padx=2)
        unlock_btn = ttk.Button(
            button_frame, text="Unlock Inputs", command=self._unlock_inputs
        )
        unlock_btn.pack(side=tk.RIGHT, expand=True, padx=2)

    def _unlock_inputs(self):
        """Unlocks disabled inputs so user may enter something else than auto populated."""
        for key in ["lat", "lon", "body", "system"]:
            self.entries[key].config(state="normal")

    def _save(self):
        """Save to DB"""

        def empty_str_as_none(entry: str) -> str | None:
            val = self.entries[entry].get().strip()
            if not val:
                val = None
            return val

        try:
            try:
                lat = float(self.entries["lat"].get())
                lon = float(self.entries["lon"].get())
            except ValueError:
                raise ValueError("Latitude and Longitude must be valid numbers.")
            if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                raise ValueError("Coordinates out of range (-90 to 90, -180 to 180).")

            mineral = empty_str_as_none("mineral")
            spot_num_raw = empty_str_as_none("spot")
            rigs_count_raw = empty_str_as_none("miners_count")

            try:
                spot_number = int(spot_num_raw) if spot_num_raw else None
                if spot_number is not None and spot_number < 1:
                    raise ValueError("111")
            except ValueError:
                raise ValueError("Mining Spot # must be an positive integer.")

            try:
                rigs_count = int(rigs_count_raw) if rigs_count_raw else 1
                if rigs_count < 1:
                    raise ValueError("111")
            except ValueError:
                raise ValueError("Rigs Count must be an positive integer.")

            spot = SurfaceSpot(
                star_system=self.entries["system"].get(),
                body_name=self.entries["body"].get(),
                latitude=lat,
                longitude=lon,
                # Recording both - fuzzy and original input for post-mortem fixes.
                mineral_type=Commodities.resolve_db_value(mineral),
                mineral_original=mineral,
                spot_number=spot_number,
                notes=empty_str_as_none("note"),
                max_miners=rigs_count,
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
