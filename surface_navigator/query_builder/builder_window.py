"""The query builder window -- a non-modal ``Toplevel`` for composing searches.

The window is the only place that ties the pure model
(:mod:`query_builder.render`) to the widgets (:mod:`query_builder.line_widget`)
and the database. It:

* shows a palette of predicates and a list of presets (left);
* shows the builder: lines OR'ed, each a group of widgets AND'ed, with ``Not``
  at the widget / line / whole-builder level (center);
* runs the built predicate against the DB and shows the matching spots (bottom);
* offers the two destructive delete-temporaries actions (bottom-right).

Destructive DB actions live on explicit buttons only -- never inline in the
builder -- so the builder stays a pure selection surface.
"""

from __future__ import annotations

import datetime
import logging
import threading
import tkinter as tk
import webbrowser
from tkinter import font as _tk_font
from tkinter import messagebox, ttk
from typing import Any

from ..database import DatabaseManager, StarNotFoundError
from ..events_dispatcher import EventParams, KnownEvents, dispatcher
from ..icons_cache import IconsCache
from ..models import StarSystem, SurfaceSpot
from ..player_location import (
    DEFAULT_PLANET_RADIUS,
    PlayerLocation,
    SurfacePoint,
    in_game_timestamp,
)
from ..predicates import (
    KNOWN_PREDICATES,
    InvalidContext,
    QueryContext,
    SearchInCurrentSystem,
)
from ..presets import PresetManager, load_current_query, save_current_query
from ..scrollable_area import ScrollableArea
from ..spot_flags import SurfaceSpotFlags
from ..star_resolver import StarApiClient
from ..ui_tooltip import Tooltip
from ..vertical_resize_handler import VerticalResizeHandler
from .base import DataContext
from .line_widget import LineWidget
from .render import BuilderState, build

# Seconds of age for the "clear temporaries older than an hour" action.
_GC_LAST_HOUR_SECS = 3600
_LEFT_LEFT_PAD_PX = 5

logger = logging.getLogger("SurfaceNavigator")


class QueryBuilderWindow(tk.Toplevel):
    """Floating window that composes and runs a surface search."""

    # Lower bound for the left column so it never gets uncomfortably narrow.
    _PALETTE_MIN_WIDTH = 220

    def __init__(
        self,
        parent: tk.Tk,
        *,
        db_manager: DatabaseManager,
        preset_manager: PresetManager,
        loc: PlayerLocation | StarSystem | None = None,
        star_resolver: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Surface Navigator Managing")
        self.minsize(1024, 768)

        self.db_manager = db_manager
        self.preset_manager = preset_manager
        # The host always has *something* while the game runs: a
        # ``PlayerLocation`` on a body, or just a ``StarSystem`` in space (no
        # body). When the game is not running it is ``None``. Normalize all
        # three into the same two attributes so the rest of the builder only
        # ever deals with ``current_location`` (surface position, None in
        # space) and ``current_system`` (the current star, or None). This is
        # what fixes the "In Current System" predicate: a bare system in space
        # still scopes the search instead of degrading to ``1 = 1``.
        self.current_location: PlayerLocation | None
        self.current_system: StarSystem | None
        if isinstance(loc, PlayerLocation):
            self.current_location = loc
            self.current_system = loc.star_system
        elif loc is not None:
            self.current_location = None
            self.current_system = loc
        else:
            self.current_location = None
            self.current_system = None
        self._star_resolver = star_resolver
        self.data = DataContext(
            db_manager, self.current_system.star_name if self.current_system else None
        )

        # Keep "where the player is" fresh while the window is open. We do not
        # rely on the constructor snapshot alone: the player keeps moving and a
        # stale ``current_location`` would make ``In Current System`` match the
        # whole DB. The event carries ``system`` (always with ``.star_name``,
        # even in space where ``location`` is None), so it is the source of
        # truth once subscribed.
        dispatcher.subscribe(KnownEvents.POSITION_UPDATED, self._on_position_updated)

        self._lines: list[LineWidget] = []
        self._active_line: LineWidget | None = None

        # Widget references for tooltips (see ``_bind_tooltips``).
        self._run_btn: ttk.Button
        self._top_not_btn: ttk.Checkbutton
        self._add_line_btn: ttk.Button
        self._remove_line_btn: ttk.Button
        self._reset_builder_btn: ttk.Button
        self._load_btn: ttk.Button
        self._save_preset_btn: ttk.Button
        self._gc_all_btn: ttk.Button
        self._gc_recent_btn: ttk.Button
        self._palette_header: ttk.Label

        self._build_ui()
        self._add_line()
        self._restore_current_query()

        # Persist whatever the user has built when the window is closed.
        self._is_closing: bool = False
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        # Sync resizers!
        self.after(50, self._fix_layout)

    def _fix_layout(self):
        """
        Hack to make splitter between builder lines and results table to work.
        Without this splitted will resize window instead results tree.
        """
        w = self.winfo_width()
        h = self.winfo_height()
        self.geometry(f"{w + 1}x{h + 1}")
        self.geometry(f"{w}x{h}")

    # -- UI construction --------------------------------------------------
    def _compute_palette_width(self) -> int:
        """Width of the left column: widest condition label plus the +/- buttons,
        row padding and the vertical scrollbar.

        Measured with the default font so it works before the widget is
        realized; the margin covers the two ``width=3`` buttons, row padding
        and the scrollbar, so no label gets truncated.
        """
        measure = _tk_font.Font().measure
        widest = max((cls().describe() for cls in KNOWN_PREDICATES), key=measure)
        return max(self._PALETTE_MIN_WIDTH, int(measure(widest) + 96))

    def _build_ui(self) -> None:
        # Left: palette + presets.
        left = ttk.Frame(self, width=self._compute_palette_width())
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        # Section for palette with fixed initial height (controlled by resizer later)
        palette_section = ttk.Frame(left)
        palette_section.pack(side=tk.TOP, fill=tk.X)
        palette_section.pack_propagate(False)
        palette_section.config(height=380)
        self._build_palette(palette_section)

        # Setup resizer handler and widget
        sizegrip = tk.Label(left, image=IconsCache.icons["resize"], cursor="sizing")
        sizegrip.pack(side=tk.TOP, fill=tk.X)
        self._left_panel_vertical_resizer = VerticalResizeHandler(
            target=palette_section, min_height=50, max_height=800
        )
        self._left_panel_vertical_resizer.set_source_of_events(sizegrip)

        # Bottom section - presets
        presets_section = ttk.Frame(left)
        presets_section.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        presets_section.pack_propagate(False)
        self._build_presets(presets_section)

        # Right: builder + results.
        right = ttk.Frame(self)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top Level Header + Generic buttons for all lines.
        right_header = ttk.Frame(right)
        right_header.pack(fill=tk.X)
        self._top_not = tk.BooleanVar(value=False)
        self._top_not_btn = ttk.Checkbutton(
            right_header, text="🔁 Neg the whole query.", variable=self._top_not
        )
        self._top_not_btn.pack(side=tk.RIGHT)
        self._run_btn = ttk.Button(right_header, text="🔎 Run", command=self._run)
        self._run_btn.pack(side=tk.RIGHT)
        self._add_line_controls(right)

        # Lines area
        lines_area = ttk.Frame(right)
        lines_area.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        lines_area.config(height=250)
        lines_area.pack_propagate(False)
        self._lines_container = self._create_scrollable_container(lines_area, True)

        # Resizer lines/table
        sizegrip = tk.Label(right, image=IconsCache.icons["resize"], cursor="sizing")
        sizegrip.pack(side=tk.TOP, fill=tk.X)
        self._right_panel_vertical_resizer = VerticalResizeHandler(
            target=lines_area, min_height=50, max_height=800
        )
        self._right_panel_vertical_resizer.set_source_of_events(sizegrip)

        # Table area
        table_area = ttk.Frame(right)
        table_area.pack(side=tk.TOP, fill=tk.BOTH)
        table_area.config(height=450)
        table_area.pack_propagate(False)
        self._build_status(table_area)
        self._build_results(table_area)

        # Attach hover tooltips to the main controls once every widget exists.
        self._bind_tooltips()

    def _bind_tooltips(self) -> None:
        """Attach a short, static hover tooltip to each main control.

        One :class:`Tooltip` per widget -- a one or two sentence description of
        what the control does. Kept in a single method so the set is easy to
        review and extend as more controls are added.
        """
        Tooltip(
            self._result_tree,
            "Search results. Right-click a row to copy the name or coordinates, "
            "or open the system on EDSM.",
        )
        Tooltip(
            self._run_btn,
            "Run the built query against the database and show matching spots.",
        )
        Tooltip(
            self._top_not_btn,
            "Negate the entire query -- every result is inverted.",
        )
        Tooltip(
            self._add_line_btn,
            "Add a new condition line. Multiple lines are combined with OR.",
        )
        Tooltip(
            self._remove_line_btn,
            "Remove the last condition line.",
        )
        Tooltip(
            self._reset_builder_btn,
            "Clear all lines and start the builder over.",
        )
        Tooltip(
            self._palette_header,
            "Conditions. Use + to add a condition, ¬ to negate it.",
        )
        Tooltip(
            self._load_btn,
            "Load the selected preset into the builder.",
        )
        Tooltip(
            self._save_preset_btn,
            "Save the current query as a named preset.",
        )
        Tooltip(
            self._preset_list,
            "Saved presets. Select one, then click Load.",
        )
        Tooltip(
            self._gc_all_btn,
            "Delete every temporary mark right away. Temporary marks are short-lived (often automatic) bookmarks.",
        )
        Tooltip(
            self._gc_recent_btn,
            "Delete temporary marks older than the shown age. Temporary marks are short-lived (often automatic) bookmarks.",
        )

    def _create_scrollable_container(self, parent: tk.Widget, hscroll: bool = False):
        area = ScrollableArea(parent=parent, hscroll=hscroll)
        return area.controls_area

    def _build_palette(self, parent: tk.Widget) -> None:
        self._palette_header = ttk.Label(parent, text="🔣 Conditions Palette")
        self._palette_header.pack(anchor=tk.W)
        palette = self._create_scrollable_container(parent)
        for cls in KNOWN_PREDICATES:
            label = cls().describe()
            row = ttk.Frame(palette)
            row.pack(fill=tk.X, pady=1, padx=(_LEFT_LEFT_PAD_PX, 0))
            ttk.Button(
                row,
                text="+",
                width=3,
                command=lambda c=cls: self._add_to_active(c, False),
            ).pack(side=tk.LEFT)
            ttk.Button(
                row,
                text="¬",
                width=3,
                command=lambda c=cls: self._add_to_active(c, True),
            ).pack(side=tk.LEFT)
            ttk.Label(row, text=label, anchor="w").pack(side=tk.LEFT, padx=(2, 0))

    def _build_presets(self, parent: tk.Widget) -> None:
        ttk.Label(parent, text="🗂️ User Presets").pack(
            anchor=tk.W, pady=(10, 0), padx=(_LEFT_LEFT_PAD_PX, 0)
        )
        palette = self._create_scrollable_container(parent)
        self._preset_list = tk.Listbox(palette, height=6)
        self._preset_list.pack(fill=tk.Y, expand=True, padx=(_LEFT_LEFT_PAD_PX, 0))
        self._preset_list.bind("<<ListboxSelected>>", self._on_preset_selected)
        self._load_btn = ttk.Button(
            palette, text="📂 Load", command=self._load_selected_preset
        )
        self._load_btn.pack(fill=tk.X, pady=(2, 0), padx=(_LEFT_LEFT_PAD_PX, 0))

        ttk.Label(palette, text="⌨️ Save current as:").pack(anchor=tk.W, pady=(10, 0))
        self._save_entry = ttk.Entry(palette)
        self._save_entry.pack(fill=tk.X, padx=(_LEFT_LEFT_PAD_PX, 0))
        self._save_preset_btn = ttk.Button(
            palette, text="💾 Save preset", command=self._save_current
        )
        self._save_preset_btn.pack(fill=tk.X, pady=(2, 0), padx=(_LEFT_LEFT_PAD_PX, 0))
        self._reload_presets()

    def _add_line_controls(self, parent: tk.Widget) -> None:
        controls = ttk.Frame(parent)
        controls.pack(fill=tk.X)
        self._add_line_btn = ttk.Button(
            controls, text="＋ Add Line", command=self._add_line
        )
        self._add_line_btn.pack(side=tk.LEFT)
        self._remove_line_btn = ttk.Button(
            controls, text="− Remove Line", command=self._remove_last_line
        )
        self._remove_line_btn.pack(side=tk.LEFT, padx=(6, 0))
        self._reset_builder_btn = ttk.Button(
            controls, text="🗑️ Reset Builder", command=self._reset_builder
        )
        self._reset_builder_btn.pack(side=tk.LEFT, padx=(6, 0))

    def _build_results(self, parent: tk.Widget) -> None:
        ttk.Label(parent, text="👉 Results").pack(
            anchor=tk.W, pady=(10, 0), side=tk.TOP
        )
        # ``full_name`` is what the player reads (``system body``). ``system``
        # and ``body`` stay as *hidden* columns: the context menu still needs
        # them separately to copy the full name and to build the EDSM link.
        columns = (
            "full_name",
            "mineral",
            "note",
            "visit",
            "lat",
            "lon",
            "system",
            "body",
            "rigs",
            "spot_number",
        )
        self._result_tree = ttk.Treeview(
            parent, columns=columns, show="headings", height=8
        )
        column_headers = {
            "full_name": "System/Body",
            "mineral": "Mineral",
            "note": "Note",
            "visit": "Visited",
            "lat": "Lat",
            "lon": "Lon",
        }
        column_widths = {
            "full_name": 180,
            "mineral": 90,
            "note": 200,
            "visit": 110,
            "lat": 70,
            "lon": 70,
        }
        for col in columns:
            if col in ("system", "body", "rigs", "spot_number"):
                # Hidden, but kept: the context menu reads these by name.
                self._result_tree.column(col, width=0, stretch=False)
                self._result_tree.heading(col, text="")
                continue
            self._result_tree.column(col, width=column_widths[col])
            self._result_tree.heading(col, text=column_headers[col])
        scrollbar = ttk.Scrollbar(
            parent,
            orient="vertical",
            command=self._result_tree.yview,  # type: ignore
        )
        self._result_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._result_tree.pack(side=tk.TOP, fill=tk.BOTH, expand=True, anchor=tk.SW)
        # Right-click on a result row opens a small action menu (see
        # ``_on_context_menu``). Bound here rather than in ``__init__`` so the
        # widget definitely exists.
        self._result_tree.bind("<Button-3>", self._on_context_menu)

    def _build_status(self, parent: tk.Widget) -> None:
        status = ttk.Frame(parent)
        status.pack(fill=tk.X, pady=(6, 0))
        self._status = ttk.Label(status, text="")
        self._status.pack(side=tk.LEFT)
        self._gc_all_btn = ttk.Button(
            status, text="🧹 Clear all temporaries", command=lambda: self._gc(0)
        )
        self._gc_all_btn.pack(side=tk.RIGHT, padx=(5, 20), pady=5)
        self._gc_recent_btn = ttk.Button(
            status,
            text=f"🧹 Clear temporaries > {_GC_LAST_HOUR_SECS // 60} min",
            command=lambda: self._gc(_GC_LAST_HOUR_SECS),
        )
        self._gc_recent_btn.pack(side=tk.RIGHT)

    def _gc(self, age_secs: int):
        self.db_manager.gc_temporaries(age_secs)

    # -- lines ------------------------------------------------------------
    def _activate_line(self, line: LineWidget) -> None:
        self._active_line = line

    def _remove_line_callback(self, line: LineWidget) -> bool:
        """
        This is 2nd part of line deletion, called as callback from the object which is being destroyed.
        Do not call it directly as self._remove_line_callback(line) because internal data of the line will leak.
        Returns False when last line was deleted and new empty was created instead.
        """
        self._clean_results()
        self._lines.remove(line)
        line.destroy()
        # The list shrank: the new first line must stop showing the marker.
        # Harmless no-op when a non-first line was removed (the first line was
        # already blank); essential when the first line itself was removed.
        if self._lines:
            self._lines[0].set_or_separator("")
        if self._active_line is line:
            self._active_line = self._lines[0] if self._lines else None
        if not self._lines:
            if not self._is_closing:
                self._add_line()
            return False
        return True

    def _add_line(self) -> None:
        self._clean_results()
        line = LineWidget(
            self._lines_container,
            data=self.data,
            on_activate=self._activate_line,
            on_remove=self._remove_line_callback,
        )
        self._lines.append(line)
        # Any line but the first ORs with the ones above it, so show the marker.
        if len(self._lines) > 1:
            line.set_or_separator("— OR —")
        line.pack(fill=tk.X)
        self._active_line = line

    def _remove_last_line(self) -> bool:
        """
        Removes last line in the list. Properly calls internal line clean-up.
        Returns True if more lines remain, returns False when last line was deleted and empty line was created instead.
        """
        # Do not call self._remove_line_callback(line) direct, instead ask object to self destroy.
        # Object must cleanup internal stuff.
        assert len(self._lines) > 0
        return self._lines[-1].remove()

    def _add_to_active(self, cls: Any, not_: bool) -> None:
        if self._active_line is None:
            self._add_line()
        assert self._active_line is not None
        self._active_line.add_widget(cls(), not_)

    def _reset_builder(self):
        while self._remove_last_line():
            pass

    # -- building / running ----------------------------------------------
    def _current_state(self) -> BuilderState:
        return BuilderState(
            lines=[line.build() for line in self._lines],
            top_not=self._top_not.get(),
        )

    def _build_ctx(self) -> QueryContext:
        coord: SurfacePoint | None = None
        radius = DEFAULT_PLANET_RADIUS
        # ``current_system`` is the source of truth for the name (and, when
        # known, the star coords). It is present even in space, so both the
        # name and the coords come from it; the DB resolves the name to
        # coordinates itself, these coords just let "near current star"
        # searches run without an extra lookup.
        current_name = self.current_system.star_name if self.current_system else None
        current_coords: tuple[float, float, float] | None = None
        if self.current_system is not None:
            x = self.current_system.x
            y = self.current_system.y
            z = self.current_system.z
            if x is not None and y is not None and z is not None:
                current_coords = (x, y, z)
        # The surface position only exists on a body; in space it is None, so
        # surface-distance predicates fail validation instead of searching a
        # phantom planet.
        if self.current_location is not None:
            pc = self.current_location.player_coord
            if pc is not None:
                coord = SurfacePoint(pc.latitude, pc.longitude)
            radius = self.current_location.radius_meters or DEFAULT_PLANET_RADIUS
        return QueryContext(
            player_coord=coord,
            planet_radius=radius,
            current_system_coords=current_coords,
            current_system_name=current_name,
        )

    def _on_position_updated(self, data: EventParams) -> None:
        """Refresh the builder's view of where the player is.

        Follows the same normalization as the constructor: ``current_location``
        is a ``PlayerLocation`` on a body (None in space) and ``current_system``
        is the current star (always present while the game runs). When both are
        available ``location`` wins for ``system`` -- they are the same object,
        but the ordering is deterministic. Only re-renders the ``In Current
        System`` widget when the name actually changes, so a high-frequency
        position stream does not thrash the UI.
        """
        if isinstance(data.location, PlayerLocation):
            self.current_location = data.location
            self.current_system = data.location.star_system
        else:
            # In space: ``location`` is None, but ``data.system`` still names
            # the star. Treat it as a bare system so the "In Current System"
            # predicate keeps scoping instead of degrading to ``1 = 1``.
            self.current_location = None
            self.current_system = data.system
        new_name = self.current_system.star_name if self.current_system else None
        if new_name != self.data.current_system_name:
            self.data.current_system_name = new_name
            self._refresh_current_system_widgets()

    def _refresh_current_system_widgets(self) -> None:
        """Re-render any ``In Current System`` widget after a system change.

        The widget reads the system name from ``DataContext`` at render time, so
        a plain data update is not enough -- the label has to be rebuilt.
        """
        for line in self._lines:
            for widget in line.iter_widgets():
                if isinstance(widget.get_predicate(), SearchInCurrentSystem):
                    widget.load_leaf(widget.get_predicate())

    def _run(self) -> None:
        predicate = build(self._current_state())
        if predicate is None:
            messagebox.showwarning(
                "Empty search", "Add at least one condition before running."
            )
            return
        try:
            spots = self.db_manager.query_spots(
                predicate,
                self._build_ctx(),
                allow_unbounded=True,
                star_resolver=self._star_resolver,
            )
        except InvalidContext as e:
            messagebox.showerror("Can't search", str(e))
            return
        except StarNotFoundError as e:
            messagebox.showerror("Star not found", f"Could not resolve star: {e}")
            return
        except ValueError as e:
            messagebox.showerror("Invalid search", str(e))
            return
        self._show_results(spots)

    def _clean_results(self):
        for item in self._result_tree.get_children():
            self._result_tree.delete(item)
        self._status.config(text="0 result(s)")

    def _show_results(self, spots: list[SurfaceSpot]) -> None:
        self._clean_results()
        for spot in spots:
            parts = [p for p in (spot.star_system, spot.body_name) if p]
            notes = spot.notes or "-"
            extra_segments: list[str] = []
            if not (spot.flags & SurfaceSpotFlags.TRITIUM_RING_PRESENT):
                if spot.spot_number is not None:
                    extra_segments.append(f"nav_id: {spot.spot_number}")
                if spot.mineral_type is not None:
                    extra_segments.append(f"rigs: {spot.max_miners}")

            display_notes = notes
            if extra_segments:
                meta = ", ".join(extra_segments)
                display_notes = f"{meta} • {notes}" if notes != "-" else meta

            self._result_tree.insert(
                "",
                tk.END,
                values=(
                    " ".join(parts) if parts else "—",  # full_name (visible)
                    spot.mineral_type or "—",  # mineral
                    display_notes,
                    self._format_visit_time(spot.last_visit_time),  # visit
                    round(spot.latitude, 4),  # lat
                    round(spot.longitude, 4),  # lon
                    spot.star_system or "",  # system (hidden)
                    spot.body_name or "",  # body (hidden)
                ),
            )
        self._status.config(text=f"{len(spots)} result(s)")

    @staticmethod
    def _format_visit_time(dt: datetime.datetime | None) -> str:
        """Formats a visit time in the in-game calendar (``3312-10-12 14:30``).

        ``None`` (never visited) renders as ``—`` so the column stays uniform.
        """
        if dt is None:
            return "—"
        return in_game_timestamp(now=dt)

    # -- results context menu ---------------------------------------------
    def _on_context_menu(self, event: Any) -> None:
        """Show the results-table context menu at the cursor.

        The menu acts on the row under the cursor: **Copy Name** puts the full
        (``system body``) name on the clipboard, **Copy Location** puts the
        coordinates as a ``{"lat": ..., "lon": ...}`` dict literal, **Visit on
        EDSM** fetches the EDSM page (one ``/api-v1/system`` call for the system
        ``id``) and opens it in the default browser, and **Cancel** just
        dismisses the menu. A right-click outside a row (or on a row with no
        system) does nothing.
        """
        # ``identify_row`` returns ``None`` when the click lands on empty space,
        # not a row -- the stubs only say ``str``, so annotate explicitly.
        item: str | None = self._result_tree.identify_row(event.y)
        if item is None:  # type: ignore
            return
        # ``system`` lives in a hidden column -- the menu needs it separately
        # from the displayed ``full_name``: copy the name, link the system.
        system = self._result_tree.set(item, "system")
        if not system or system in ("", "—"):
            return
        full_name = self._result_tree.set(item, "full_name")
        location = self._format_location(
            self._result_tree.set(item, "lat"),
            self._result_tree.set(item, "lon"),
        )
        menu = self._build_context_menu(full_name, location, system)
        # ``tk_popup`` takes *absolute* screen coords (``x_root``/``y_root``), so
        # the menu lands exactly under the cursor regardless of where the tree
        # sits inside the window. ``grab_release`` undoes the grab ``tk_popup``
        # takes, so the window becomes clickable again after the menu closes.
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _build_context_menu(
        self, full_name: str, location: str, system: str
    ) -> tk.Menu:
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="Copy Name", command=lambda: self._copy(full_name))
        menu.add_command(label="Copy Location", command=lambda: self._copy(location))
        menu.add_command(
            label="Visit on EDSM", command=lambda: self._visit_edsm(system)
        )
        menu.add_separator()
        menu.add_command(label="Cancel", command=menu.destroy)
        return menu

    @staticmethod
    def _format_location(lat: str, lon: str) -> str:
        """Coordinates as a dict literal: ``{"lat": 0.5, "lon": 1.2}``.

        The same text is both a valid Python dict literal and valid JSON, so it
        pastes cleanly into scripts (``ast.literal_eval`` / ``json.loads``) and
        web tools alike. ``lat``/``lon`` are the rounded values shown in the
        table, so the copy always matches what the player sees.
        """
        return f'{{"lat": {lat}, "lon": {lon}}}'

    def _copy(self, text: str) -> None:
        """Copy ``text`` to the clipboard."""
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update_idletasks()

    def _visit_edsm(self, system: str) -> None:
        """Open the system on EDSM in the default browser.

        The EDSM ``id`` is fetched over the network, so this runs in a worker
        thread; the browser launch (an external call, never a tkinter call) is
        still marshalled back to the main thread via ``after``.
        """

        def worker() -> None:
            try:
                url = StarApiClient().edsm_system_url(system)
            except Exception:
                logger.exception("Failed to build EDSM URL for %r", system)
                self.after(0, lambda: self._show_edsm_warning(system, "open"))
                return
            if url is None:
                self.after(0, lambda: self._show_edsm_warning(system, "unknown"))
                return
            self.after(0, lambda: webbrowser.open(url))

        threading.Thread(target=worker, name="edsm-url", daemon=True).start()

    def _show_edsm_warning(self, system: str, reason: str) -> None:
        if reason == "unknown":
            message = (
                f"EDSM knows nothing about '{system}' -- there is no page to open."
            )
        else:
            message = (
                f"Couldn't reach EDSM to find '{system}'. "
                "Check your network connection and try again."
            )
        messagebox.showwarning("EDSM", message)

    # -- presets ----------------------------------------------------------
    def _reload_presets(self) -> None:
        self._preset_list.delete(0, self._preset_list.size())
        # Insert in order (``tk.END``), not at index 0 -- ``insert(0, ...)``
        # reverses the list, which then mismatches the index used by
        # ``_load_selected_preset`` (that one reads ``preset_manager.load()``
        # in the correct order). That mismatch is what loaded the wrong query.
        for preset in self.preset_manager.load():
            self._preset_list.insert(tk.END, preset.name)

    def _on_preset_selected(self, _event: Any = None) -> None:
        self._load_selected_preset()

    def _load_selected_preset(self) -> None:
        selection = self._preset_list.curselection()  # type: ignore
        if not selection:
            return
        presets = self.preset_manager.load()
        index: int = selection[0]  # type: ignore
        if index >= len(presets):
            return
        self._load_query(presets[index].query)

    def _save_current(self) -> None:
        name = self._save_entry.get().strip()
        if not name:
            messagebox.showwarning("Save preset", "Enter a name for the preset.")
            return
        predicate = build(self._current_state())
        if predicate is None:
            messagebox.showwarning("Save preset", "Nothing to save -- add a condition.")
            return
        self.preset_manager.add(name, predicate)
        self._reload_presets()
        self._status.config(text=f"Saved preset '{name}'.")

    # -- current query (config) ------------------------------------------
    def _restore_current_query(self) -> None:
        predicate = load_current_query()
        if predicate is not None:
            self._load_query(predicate)

    def _on_close(self) -> None:
        """Window is closed."""
        self._is_closing = True
        save_current_query(build(self._current_state()))
        # Drop the live position subscription so the dispatcher stops holding a
        # reference to this (about-to-be-destroyed) window's callback.
        dispatcher.unsubscribe(KnownEvents.POSITION_UPDATED, self._on_position_updated)
        # Act consistent as user pressed "Clear" UI button.
        self._reset_builder()
        self.destroy()

    def _load_query(self, predicate: Any) -> None:
        """Populate the builder from a predicate (reverse of :meth:`_run`)."""
        from .render import load as load_state

        state: BuilderState = load_state(predicate)
        for line in self._lines:
            # Clean up internal state (widgets + tooltips) before destroying;
            # ``remove`` would do this but also notifies the host, which the
            # reload does not want.
            line.destroy_internal()
            line.destroy()
        self._lines.clear()
        self._top_not.set(state.top_not)
        if not state.lines:
            self._add_line()
            return
        for i, node in enumerate(state.lines):
            line = LineWidget(
                self._lines_container,
                data=self.data,
                on_activate=self._activate_line,
                on_remove=self._remove_line_callback,
            )
            self._lines.append(line)
            # Restore the OR markers: blank on the first line, shown after.
            if i > 0:
                line.set_or_separator("— OR —")
            line.pack(fill=tk.X)
            line.load(node)
        self._active_line = self._lines[-1]
