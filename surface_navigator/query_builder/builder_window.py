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
from ..icons_cache import IconsCache
from ..models import SurfaceSpot
from ..player_location import DEFAULT_PLANET_RADIUS, SurfacePoint
from ..predicates import KNOWN_PREDICATES, InvalidContext, QueryContext
from ..presets import PresetManager, load_current_query, save_current_query
from ..vertical_resize_handler import VerticalResizeHandler
from ..vertical_wheel_scroll import CanvasVerticalMouseWheelScroller
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
        # Left: palette + presets.
        left = ttk.Frame(self, width=self._compute_palette_width())
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        # Section for palette with fixed initial height (controlled by resizer later)
        self._palette_section = ttk.Frame(left)
        self._palette_section.pack(side=tk.TOP, fill=tk.X)
        self._palette_section.pack_propagate(False)
        self._palette_section.config(height=380)
        self._build_palette(self._palette_section)

        # Setup resizer handler and widget
        sizegrip = tk.Label(left, image=IconsCache.icons["resize"], cursor="sizing")
        sizegrip.pack(side=tk.TOP, fill=tk.X)
        self._left_panel_vertical_resizer = VerticalResizeHandler(
            target=self._palette_section, min_height=50, max_height=800
        )
        self._left_panel_vertical_resizer.set_source_of_events(sizegrip)

        # Bottom section - presets
        self._presets_section = ttk.Frame(left)
        self._presets_section.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
        self._presets_section.pack_propagate(False)
        self._build_presets(self._presets_section)

        # Right: builder + results.
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

    def _create_scrollable_container(self, parent: tk.Widget, hscroll: bool = False):
        # Vertical scroll bar for the whole canvas
        canvas = tk.Canvas(parent, highlightthickness=0)
        canvas.pack_propagate(True)
        vscrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)  # type: ignore

        # Pack scrollbar(s), than canvas - order is important here, otherwise canvas will eat all space.
        vscrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        if hscroll:
            hscrollbar = ttk.Scrollbar(
                parent,
                orient="horizontal",
                command=canvas.xview,  # type: ignore
            )
            canvas.configure(xscrollcommand=hscrollbar.set)
            hscrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        canvas.configure(yscrollcommand=vscrollbar.set)
        self._palette_canvas_scroll = CanvasVerticalMouseWheelScroller(
            canvas, attach=True
        )

        palette = ttk.Frame(canvas)
        palette.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        palette.pack_propagate(True)

        canvas.create_window((0, 0), window=palette, anchor="nw")

        # Keep the scroll region in sync as palette entries are added.
        def _debounced_configure(event: Any):
            self.after_idle(lambda: canvas.config(scrollregion=canvas.bbox("all")))

        palette.bind("<Configure>", _debounced_configure)
        return palette

    def _build_palette(self, parent: tk.Widget) -> None:
        ttk.Label(parent, text="Conditions Palette").pack(anchor=tk.W)
        palette = self._create_scrollable_container(parent)
        for cls in KNOWN_PREDICATES:
            label = cls().describe()
            row = ttk.Frame(palette)
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
        ttk.Label(parent, text="User Presets").pack(anchor=tk.W, pady=(10, 0))
        palette = self._create_scrollable_container(parent)
        self._preset_list = tk.Listbox(palette, height=6)
        self._preset_list.pack(fill=tk.Y, expand=True)
        self._preset_list.bind("<<ListboxSelected>>", self._on_preset_selected)
        ttk.Button(palette, text="Load", command=self._load_selected_preset).pack(
            fill=tk.X, pady=(2, 0)
        )

        ttk.Label(palette, text="Save current as:").pack(anchor=tk.W, pady=(10, 0))
        self._save_entry = ttk.Entry(palette)
        self._save_entry.pack(fill=tk.X)
        ttk.Button(palette, text="Save preset", command=self._save_current).pack(
            fill=tk.X, pady=(2, 0)
        )
        self._reload_presets()

    def _add_line_controls(self, parent: tk.Widget) -> None:
        controls = ttk.Frame(parent)
        controls.pack(fill=tk.X)
        ttk.Button(controls, text="＋ Add Line", command=self._add_line).pack(
            side=tk.LEFT
        )
        ttk.Button(controls, text="− Remove Line", command=self._remove_last_line).pack(
            side=tk.LEFT, padx=(6, 0)
        )
        ttk.Button(controls, text="🗑️ Reset Builder", command=self._reset_builder).pack(
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
        self._lines_container = self._create_scrollable_container(outer, True)

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

    def _remove_line_callback(self, line: LineWidget) -> bool:
        """
        This is 2nd part of line deletion, called as callback from the object which is being destroyed.
        Do not call it directly as self._remove_line_callback(line) because internal data of the line will leak.
        Returns False when last line was deleted and new empty was created instead.
        """
        self._clean_results()
        self._lines.remove(line)
        line.destroy()
        if self._active_line is line:
            self._active_line = self._lines[0] if self._lines else None
        if not self._lines:
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
                on_remove=self._remove_line_callback,
            )
            self._lines.append(line)
            line.pack(fill=tk.X)
            line.load(node)
        self._active_line = self._lines[-1]
