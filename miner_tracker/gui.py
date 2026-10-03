import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Dict, Any
from .models import MiningSpot
from .database import DatabaseManager
from .overlay_client import OverlayClient
from .events_dispatcher import dispatcher

class AddSpotDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, db_manager: DatabaseManager, callback, current_location: Optional[Dict[str, Any]] = None):
        super().__init__(parent)
        self.title("Add Mining Spot")
        self.geometry("300x450")
        self.db_manager = db_manager
        self.callback = callback

        container = ttk.Frame(self, padding="15")
        container.pack(fill=tk.BOTH, expand=True)

        # Form Fields
        fields = [
            ("Star System:", "system"),
            ("Body Name:", "body"),
            ("Mineral Type:", "mineral"),
            ("Latitude:", "lat"),
            ("Longitude:", "lon"),
            ("Spot #:", "spot")
        ]

        self.entries = {}
        for label_text, key in fields:
            ttk.Label(container, text=label_text).pack(anchor=tk.W)
            entry = ttk.Entry(container)
            entry.pack(fill=tk.X, pady=(0, 10))
            self.entries[key] = entry

        # Auto-populate from current location if available and fields are not disabled
        if current_location:
            if 'star_system' in current_location and current_location['star_system']:
                self.entries['system'].insert(0, str(current_location['star_system']))
                self.entries['system'].config(state='disabled')
            if 'body_name' in current_location and current_location['body_name']:
                self.entries['body'].insert(0, str(current_location['body_name']))
                self.entries['body'].config(state='disabled')
            if 'latitude' in current_location and current_location['latitude'] is not None:
                self.entries['lat'].insert(0, str(current_location['latitude']))
                self.entries['lat'].config(state='disabled')
            if 'longitude' in current_location and current_location['longitude'] is not None:
                self.entries['lon'].insert(0, str(current_location['longitude']))
                self.entries['lon'].config(state='disabled')

        ttk.Button(container, text="Save Spot", command=self._save).pack(pady=20, fill=tk.X)

    def _save(self):
        try:
            # Handle empty spot number string
            spot_num = self.entries['spot'].get().strip()
            spot_num_val = int(spot_num) if spot_num else None

            spot = MiningSpot(
                star_system=self.entries['system'].get(),
                body_name=self.entries['body'].get(),
                latitude=float(self.entries['lat'].get()),
                longitude=float(self.entries['lon'].get()),
                mineral_type=self.entries['mineral'].get() if self.entries['mineral'].get() else None,
                spot_number=spot_num_val
            )
            if spot.star_system and spot.body_name:
                if self.db_manager.add_spot(spot):
                    self.callback() 
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save to database.")
            else:
                messagebox.showwarning("Input Error", "System and Body are required.")
        except ValueError as e:
            messagebox.showerror("Input Error", f"Please enter valid numbers: {e}")

class MinerTrackerGUI(ttk.Frame):
    def __init__(self, parent, db_manager: DatabaseManager, overlay_client: OverlayClient):
        super().__init__(parent)
        self.db_manager = db_manager
        self.overlay = overlay_client
        self.current_location: Optional[Dict[str, Any]] = None
        self.is_on_surface: bool = False

        self._setup_ui()
        self._load_data()
        
        dispatcher.subscribe("mining_record_detected", self._on_mining_record_found)
        dispatcher.subscribe("spot_added", lambda _: self._refresh())

    def _setup_ui(self):
        main_container = ttk.Frame(self, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_container, text="Mining Spots Tracker", font=("Helvetica", 12, "bold")).pack()

        # Toolbar (Horizontal layout for buttons)
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(5, 5))
        
        self._btn_add = ttk.Button(toolbar, text="Add New Spot", command=self._open_add_dialog)
        self._btn_add.pack(side=tk.LEFT, padx=2)

        ttk.Button(toolbar, text="Navigate", command=self._on_navigate).pack(side=tk.RIGHT, padx=2)

        # Treeview with scrollbar
        tree_container = ttk.Frame(main_container)
        tree_container.pack(fill=tk.BOTH, expand=True)

        columns = ("system", "body", "mineral", "spot")
        self._tree = ttk.Treeview(tree_container, columns=columns, show="headings", height=8)
        for col in columns: 
            self._tree.heading(col, text=col.capitalize())
            self._tree.column(col, width=70 if col not in ["system", "body"] else 120)
        
        scrollbar = ttk.Scrollbar(tree_container, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _load_data(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for spot in self.db_manager.get_all_spots():
            self._tree.insert("", tk.END, values=(spot.star_system, spot.body_name, 
                                                 spot.mineral_type or "Unknown", spot.spot_number))

    def _on_navigate(self, event=None):
        selection = self._tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a spot first.")
            return
        vals = self._tree.item(selection[0], 'values')
        # vals is (system, body, mineral, spot)
        self.overlay.send_text_message("nav_info", f"Navigating to {vals[2]} in {vals[0]}", color="green")

    def _on_mining_record_found(self, data: dict):
        self._refresh()

    def _refresh(self):
        self._load_data()

    def _open_add_dialog(self):
        if not self.is_on_surface:
            messagebox.showwarning("Location Error", "You must be on a planet surface to add a spot.")
            return
        
        parent = self.winfo_toplevel()
        AddSpotDialog(parent, self.db_manager, self._refresh, current_location=self.current_location)

    def set_current_location(self, location: Optional[Dict[str, Any]], on_surface: bool):
        """Update the GUI's knowledge of where we are and whether we are on surface."""
        self.current_location = location
        self.is_on_surface = on_surface
        if self.is_on_surface:
            self._btn_add.config(state='normal')
        else:
            self._btn_add.config(state='disabled')
