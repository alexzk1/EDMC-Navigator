import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional
from .models import MiningSpot
from .database import DatabaseManager
from .overlay_client import OverlayClient
from .events_dispatcher import dispatcher

class AddSpotDialog(tk.Toplevel):
    def __init__(self, parent: tk.Tk, db_manager: DatabaseManager, callback):
        super().__init__(parent)
        self.title("Add Mining Spot")
        self.geometry("300x450")
        self.db_manager = db_manager
        self.callback = callback

        container = ttk.Frame(self, padding="10")
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Star System:").pack(anchor=tk.W)
        self.ent_system = ttk.Entry(container)
        self.ent_system.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(container, text="Body Name:").pack(anchor=tk.W)
        self.ent_body = ttk.Entry(container)
        self.ent_body.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(container, text="Mineral Type:").pack(anchor=tk.W)
        self.ent_mineral = ttk.Entry(container)
        self.ent_mineral.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(container, text="Latitude:").pack(anchor=tk.W)
        self.ent_lat = ttk.Entry(container)
        self.ent_lat.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(container, text="Longitude:").pack(anchor=tk.W)
        self.ent_lon = ttk.Entry(container)
        self.ent_lon.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(container, text="Save", command=self._save).pack(pady=20, fill=tk.X)

    def _save(self):
        try:
            spot = MiningSpot(
                star_system=self.ent_system.get(),
                body_name=self.ent_body.get(),
                latitude=float(self.ent_lat.get()),
                longitude=float(self.ent_lon.get()),
                mineral_type=self.ent_mineral.get() if self.ent_mineral.get() else None,
            )
            if spot.star_system and spot.body_name:
                if self.db_manager.add_spot(spot):
                    self.callback() 
                    self.destroy()
                else:
                    messagebox.showerror("Error", "Failed to save to database.")
            else:
                messagebox.showwarning("Input Error", "System and Body are required.")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric coordinates.")

class MinerTrackerGUI(ttk.Frame):
    def __init__(self, parent, db_manager: DatabaseManager, overlay_client: OverlayClient):
        super().__init__(parent)
        self.db_manager = db_manager
        self.overlay = overlay_client

        self._setup_ui()
        self._load_data()
        
        dispatcher.subscribe("mining_record_detected", self._on_mining_record_found)
        dispatcher.subscribe("spot_added", lambda _: self._refresh())

    def _setup_ui(self):
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Mining Spots", font=("Helvetica", 12, "bold")).pack()

        columns = ("system", "body", "mineral", "spot")
        self._tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=8)
        for col in columns: 
            self._tree.heading(col, text=col.capitalize())
            self._tree.column(col, width=70 if col not in ["system", "body"] else 120)

        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=scrollbar.set)
        self._tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Button(btn_frame, text="Add", command=self._open_add_dialog).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Navigate", command=self._on_navigate).pack(side=tk.RIGHT, padx=2)

    def _load_data(self):
        for item in self._tree.get_children():
            self._tree.delete(item)
        for spot in self.db_manager.get_all_spots():
            self._tree.insert("", tk.END, values=(spot.star_system, spot.body_name, 
                                                 spot.mineral_type or "Unknown", spot.spot_number))

    def _on_navigate(self):
        selection = self._tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a spot.")
            return
        vals = self._tree.item(selection[0], 'values')
        # vals is (system, body, mineral, spot)
        self.overlay.send_text_message("nav_info", f"Nav to {vals[2]} in {vals[0]}", color="green")

    def _on_mining_record_found(self, data: dict):
        print(f"GUI Refresh triggered by mining record in {data['star_system']}")
        self._refresh()

    def _refresh(self):
        self._load_data()

    def _open_add_dialog(self):
        AddSpotDialog(self.winfo_toplevel(), self.db_manager, self._refresh)
