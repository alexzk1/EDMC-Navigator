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

import tkinter as tk
from tkinter import font as _tk_font
from tkinter import messagebox, ttk
from typing import Any

from ..database import DatabaseManager, StarNotFoundError
from ..models import SurfaceSpot
from ..player_location import DEFAULT_PLANET_RADIUS, SurfacePoint
from ..predicates import KNOWN_PREDICATES, QueryContext
from ..presets import PresetManager, load_current_query, save_current_query
from .base import DataContext
from .line_widget import LineWidget
from .render import BuilderState, build

# Seconds of age for the "clear temporaries older than an hour" action.
_GC_LAST_HOUR_SECS = 3600


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
        current_location: Any | None = None,
        star_resolver: Any | None = None,
    ) -> None:
        super().__init__(parent)
        self.title("Surface Search Builder")
        self.db_manager = db_manager
        self.preset_manager = preset_manager
        self.current_location = current_location
        self._star_resolver = star_resolver
        self.data = DataContext(
            db_manager,
            current_location.star_system.star_name
            if current_location is not None and current_location.star_system
            else None,
        )

        self._lines: list[LineWidget] = []
        self._active_line: LineWidget | None = None

        self._build_ui()
        self._add_line()
        self._restore_current_query()

        # Persist whatever the user has built when the window is closed.
        self.protocol("WM_DELETE_WINDOW", self._on_close)

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
        # Left: palette + presets. Right: builder + results.
        left = ttk.Frame(self, width=self._compute_palette_width())
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)
        self._build_palette(left)
        self._build_presets(left)

        right = ttk.Frame(self)
        right.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Top-level NOT toggle + Run button, in the title-bar area.
        header = ttk.Frame(right)
        header.pack(fill=tk.X)
        self._top_not = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            header, text="Neg the whole query.", variable=self._top_not
        ).pack(side=tk.RIGHT)
        ttk.Button(header, text="Run", command=self._run).pack(side=tk.RIGHT)

        self._add_line_controls(right)
        self._build_builder(right)

        # Bottom strip: results + status. Kept out of the builder's pack tree so
        # it never steals width from the canvas; the builder expands to fill the
        # space above it.
        bottom = ttk.Frame(right)
        bottom.pack(side=tk.BOTTOM, fill=tk.X)
        self._build_results(bottom)
        self._build_status(bottom)

    def _build_palette(self, parent: tk.Widget) -> None:
        ttk.Label(parent, text="Add condition").pack(anchor=tk.W)
        canvas = tk.Canvas(parent, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)  # type: ignore
        palette = ttk.Frame(canvas)
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.Y, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.create_window((0, 0), window=palette, anchor="nw")
        # Keep the scroll region in sync as palette entries are added.
        palette.bind(
            "<Configure>",
            lambda e: canvas.config(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<MouseWheel>", lambda e: canvas.yview_scroll(-1 * e.delta, "units")
        )
        for cls in KNOWN_PREDICATES:
            self._add_palette_entry(palette, cls)

    def _add_palette_entry(self, parent: tk.Widget, cls: Any) -> None:
        label = cls().describe()
        row = ttk.Frame(parent)
        row.pack(fill=tk.X, pady=1)
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
        ttk.Label(parent, text="Presets").pack(anchor=tk.W, pady=(10, 0))
        self._preset_list = tk.Listbox(parent, height=6)
        self._preset_list.pack(fill=tk.Y, expand=True)
        self._preset_list.bind("<<ListboxSelected>>", self._on_preset_selected)
        ttk.Button(parent, text="Load", command=self._load_selected_preset).pack(
            fill=tk.X, pady=(2, 0)
        )

        ttk.Label(parent, text="Save current as:").pack(anchor=tk.W, pady=(10, 0))
        self._save_entry = ttk.Entry(parent)
        self._save_entry.pack(fill=tk.X)
        ttk.Button(parent, text="Save preset", command=self._save_current).pack(
            fill=tk.X, pady=(2, 0)
        )
        self._reload_presets()

    def _add_line_controls(self, parent: tk.Widget) -> None:
        controls = ttk.Frame(parent)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="＋ Add line", command=self._add_line).pack(
            side=tk.LEFT
        )
        ttk.Button(controls, text="− Remove line", command=self._remove_last_line).pack(
            side=tk.LEFT, padx=(6, 0)
        )

    def _build_builder(self, parent: tk.Widget) -> None:
        """Builder area: lines inside a two-direction scrollable canvas.

        Lines are packed into ``self._lines_container`` -- the inner frame that
        lives inside the canvas. The canvas owns the scrollbars and keeps the
        scroll region in sync as lines and their widgets are added, so a line
        full of widgets (or many lines) scrolls instead of running off-screen.
        """
        # Outer wrapper owns the vertical layout: [canvas row] over [hscroll].
        # Keeping the hscroll inside this block means it never fights the
        # status/results strip that is packed later into ``parent``.
        outer = ttk.Frame(parent)
        outer.pack(fill=tk.BOTH, expand=True)

        canvas_row = ttk.Frame(outer)
        canvas_row.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._builder_canvas = tk.Canvas(canvas_row, highlightthickness=0)
        self._vscrollbar = ttk.Scrollbar(
            canvas_row, orient="vertical", command=self._builder_canvas.yview
        )
        self._builder_canvas.configure(yscrollcommand=self._vscrollbar.set)
        self._builder_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._hscrollbar = ttk.Scrollbar(
            outer, orient="horizontal", command=self._builder_canvas.xview
        )
        self._builder_canvas.configure(xscrollcommand=self._hscrollbar.set)
        self._hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # The inner frame holds the lines; it is stretched to the canvas width
        # so widgets that overflow a line push the horizontal scrollbar out.
        self._lines_container = ttk.Frame(self._builder_canvas)
        self._builder_canvas.create_window(
            (0, 0), window=self._lines_container, anchor="nw", tags="builder_inner"
        )

        def _on_inner_configure(event: tk.Event) -> None:
            # Keep the scroll region covering everything currently drawn. The
            # inner frame sizes itself to its content (we deliberately do NOT
            # force it to the canvas width), so when widgets overflow a line the
            # bounding box grows past the canvas and the horizontal scrollbar
            # gets a real scrollable range instead of being pinned at 100%.
            region = self._builder_canvas.bbox("all")
            if region is not None:
                self._builder_canvas.configure(scrollregion=region)

        self._lines_container.bind("<Configure>", _on_inner_configure)

        # Wheel (Windows/macOS) and X11 scroll buttons (Linux).
        def _wheel(event: tk.Event) -> None:
            self._builder_canvas.yview_scroll(-1 * event.delta, "units")

        self._builder_canvas.bind("<MouseWheel>", _wheel)
        self._builder_canvas.bind(
            "<Button-4>", lambda e: self._builder_canvas.yview_scroll(1, "units")
        )
        self._builder_canvas.bind(
            "<Button-5>", lambda e: self._builder_canvas.yview_scroll(-1, "units")
        )

    def _build_results(self, parent: tk.Widget) -> None:
        ttk.Label(parent, text="Results").pack(anchor=tk.W, pady=(10, 0))
        container = ttk.Frame(parent)
        container.pack(fill=tk.X)
        columns = ("system", "body", "mineral", "note", "lat", "lon")
        self._result_tree = ttk.Treeview(
            container, columns=columns, show="headings", height=8
        )
        for col in columns:
            self._result_tree.column(col, width=90 if col != "note" else 200)
            self._result_tree.heading(col, text=col.capitalize())
        scrollbar = ttk.Scrollbar(
            container,
            orient="vertical",
            command=self._result_tree.yview,  # type: ignore
        )
        self._result_tree.configure(yscrollcommand=scrollbar.set)
        self._result_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _build_status(self, parent: tk.Widget) -> None:
        status = ttk.Frame(parent)
        status.pack(fill=tk.X, pady=(6, 0))
        self._status = ttk.Label(status, text="")
        self._status.pack(side=tk.LEFT)
        ttk.Button(
            status, text="Clear all temporaries", command=lambda: self._gc(0)
        ).pack(side=tk.RIGHT, padx=2)
        ttk.Button(
            status,
            text=f"Clear temporaries > {_GC_LAST_HOUR_SECS // 60} min",
            command=lambda: self._gc(_GC_LAST_HOUR_SECS),
        ).pack(side=tk.RIGHT)

    def _gc(self, age_secs: int):
        self.db_manager.gc_temporaries(age_secs)

    # -- lines ------------------------------------------------------------
    def _activate_line(self, line: LineWidget) -> None:
        self._active_line = line

    def _remove_line(self, line: LineWidget) -> None:
        self._lines.remove(line)
        line.destroy()
        if self._active_line is line:
            self._active_line = self._lines[0] if self._lines else None
        if not self._lines:
            self._add_line()

    def _add_line(self) -> None:
        line = LineWidget(
            self._lines_container,
            data=self.data,
            on_activate=self._activate_line,
            on_remove=self._remove_line,
        )
        self._lines.append(line)
        line.pack(fill=tk.X)
        self._active_line = line

    def _remove_last_line(self) -> None:
        if len(self._lines) <= 1:
            return
        self._lines[-1].remove()

    def _add_to_active(self, cls: Any, not_: bool) -> None:
        if self._active_line is None:
            self._add_line()
        assert self._active_line is not None
        self._active_line.add_widget(cls(), not_)

    # -- building / running ----------------------------------------------
    def _current_state(self) -> BuilderState:
        return BuilderState(
            lines=[line.build() for line in self._lines],
            top_not=self._top_not.get(),
        )

    def _build_ctx(self) -> QueryContext:
        coord: SurfacePoint | None = None
        radius = DEFAULT_PLANET_RADIUS
        current_coords: tuple[float, float, float] | None = None
        current_name = self.data.current_system_name
        if self.current_location is not None:
            pc = self.current_location.player_coord
            if pc is not None:
                coord = SurfacePoint(pc.latitude, pc.longitude)
            radius = self.current_location.radius_meters or DEFAULT_PLANET_RADIUS
            star = self.current_location.star_system
            if star is not None and None not in (star.x, star.y, star.z):
                current_coords = (star.x, star.y, star.z)
                if current_name is None:
                    current_name = star.star_name
        return QueryContext(
            player_coord=coord,
            planet_radius=radius,
            current_system_coords=current_coords,
            current_system_name=current_name,
        )

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
        except StarNotFoundError as e:
            messagebox.showerror("Star not found", f"Could not resolve star: {e}")
            return
        except ValueError as e:
            messagebox.showerror("Invalid search", str(e))
            return
        self._show_results(spots)

    def _show_results(self, spots: list[SurfaceSpot]) -> None:
        for item in self._result_tree.get_children():
            self._result_tree.delete(item)
        for spot in spots:
            self._result_tree.insert(
                "",
                tk.END,
                values=(
                    spot.star_system or "—",
                    spot.body_name or "—",
                    spot.mineral_type or "—",
                    spot.notes or "",
                    round(spot.latitude, 4),
                    round(spot.longitude, 4),
                ),
            )
        self._status.config(text=f"{len(spots)} result(s)")

    # -- presets ----------------------------------------------------------
    def _reload_presets(self) -> None:
        self._preset_list.delete(0, self._preset_list.size())
        for preset in self.preset_manager.load():
            self._preset_list.insert(0, preset.name)

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
        save_current_query(build(self._current_state()))
        self.destroy()

    def _load_query(self, predicate: Any) -> None:
        """Populate the builder from a predicate (reverse of :meth:`_run`)."""
        from .render import load as load_state

        state: BuilderState = load_state(predicate)
        for line in self._lines:
            line.destroy()
        self._lines.clear()
        self._top_not.set(state.top_not)
        if not state.lines:
            self._add_line()
            return
        for node in state.lines:
            line = LineWidget(
                self._lines_container,
                data=self.data,
                on_activate=self._activate_line,
                on_remove=self._remove_line,
            )
            self._lines.append(line)
            line.pack(fill=tk.X)
            line.load(node)
        self._active_line = self._lines[-1]
