import tkinter as tk
from tkinter import ttk

from .vertical_wheel_scroll import CanvasVerticalMouseWheelScroller


class ScrollableArea(ttk.Frame):
    """
    Scrollable Frame + Canvas.
    Uses debounce to prevent X11 crash on heavy scenes.
    """

    def __init__(self, parent: tk.Widget, hscroll: bool = False, **kwargs) -> None:  # type: ignore
        super().__init__(parent, **kwargs)  # type: ignore

        self._debounce_id: str | None = None

        # Vertical scroll bar for the whole canvas
        canvas = tk.Canvas(parent, highlightthickness=0)
        self._canvas = canvas

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

        area = ttk.Frame(canvas)
        self.controls_area = area

        area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        area.pack_propagate(True)

        canvas.create_window((0, 0), window=area, anchor="nw")
        area.bind("<Configure>", self._on_configure)
        self._mousewheel_handler = CanvasVerticalMouseWheelScroller(canvas, attach=True)

    def _on_configure(self, event: tk.Event) -> None:
        """Debounced resize content handler"""
        if self._debounce_id:
            self.after_cancel(self._debounce_id)

        self._debounce_id = self.after(30, self._update_scroll_region)

    def _update_scroll_region(self) -> None:
        region = self._canvas.bbox("all")
        if region:
            self._canvas.config(scrollregion=region)
        self._debounce_id = None
