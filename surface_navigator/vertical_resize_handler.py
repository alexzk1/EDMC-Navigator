import tkinter as tk
from typing import Any, Protocol


class RequiredMethodsOfTarget(Protocol):
    """
    "Compile time" check we use type with proper methods as target widget.
    """

    def config(self, *, height: int) -> None: ...
    def winfo_height(self) -> int: ...


class VerticalResizeHandler:
    def __init__(self, target: Any, min_height: int = 100, max_height: int = 500):
        """
        target: is a widget which will be resized by this controller and must support 'height' option.
        """

        # runtime check, just in case...
        keys_method = getattr(target, "keys", None)
        if keys_method is None or "height" not in keys_method():
            raise TypeError(
                f"{target.__class__.__name__} does not support 'height' configuration option, "
                "cannot be used with VerticalResizer"
            )
        self._widget = target
        self._target: RequiredMethodsOfTarget = target
        self._min_height = min_height
        self._max_height = max_height

        self._resizing = False
        self._start_y = 0
        self._start_height = 0
        self._source = None

        # Debounce / throttling to avoid XServer crash if too many / too fast complex resizes.
        self._after_id: int | None = None
        self._current_mouse_y = 0

    def set_source_of_events(self, source_of_events_widget: tk.Widget) -> None:
        """
        Sets the source of the resize events for this resizer.
        source_of_events_widget: will provide events which will resize target widget set on construction.
        """
        if self._source is not None:
            self._source.unbind("<ButtonPress-1>")
            self._source.unbind("<ButtonRelease-1>")
            self._source.unbind("<Motion>")

        self._source = source_of_events_widget
        self._source.bind("<ButtonPress-1>", self._start_resize)
        self._source.bind("<ButtonRelease-1>", self._stop_resize)
        self._source.bind("<Motion>", self._resize_frame)

    def get_min_max_height(self):
        return self._min_height, self._max_height

    def set_max_height(self, max_height: int) -> None:
        """Update the upper height bound at runtime (e.g. to track the parent
        window size). The lower bound set at construction is left untouched."""
        self._max_height = max_height

    def _start_resize(self, event: tk.Event):
        self._start_y = event.y_root
        self._start_height = self._target.winfo_height()
        self._resizing = True
        self._current_mouse_y = event.y_root

    def _stop_resize(self, event: tk.Event):
        self._resizing = False
        self._start_y = 0
        self._start_height = 0
        self._after_id = None

    def _resize_frame(self, event: tk.Event):
        if not self._resizing:
            return

        self._current_mouse_y = event.y_root
        if self._after_id is None:
            self._after_id = self._widget.after(16, self._apply_resize)

    def _apply_resize(self):
        if not self._resizing:
            self._after_id = None
            return

        delta = self._start_y - self._current_mouse_y
        new_height = self._start_height - delta
        new_height = min(max(new_height, self._min_height), self._max_height)
        self._target.config(height=new_height)
        self._after_id = None
