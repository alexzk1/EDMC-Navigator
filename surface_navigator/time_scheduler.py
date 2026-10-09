"""Global scheduler for GUI-backed timers.

Plugins whose classes are not tkinter widgets (e.g. the overlay) still need
periodic callbacks that run on the main GUI thread. This scheduler bridges them
to ``tk.after`` / ``tk.after_cancel``.

It only works once a root is bound (by the GUI, first thing in ``create_gui``).
Before that ``has_gui()`` is False and callers must not start timers -- they
should fall back to working without them (see the overlay's ``navigate_to``).
"""

import logging
import tkinter as tk

logger = logging.getLogger("SurfaceNavigator")


class TimeScheduler:
    """Hands out ``after``-based timers, tied to the tkinter root."""

    def __init__(self) -> None:
        self._root = None

    def bind_root(self, root: tk.Tk) -> None:
        """Bind the tkinter root (called once by the GUI, before anything else)."""
        self._root = root

    def has_gui(self) -> bool:
        """Whether a tkinter root is available for scheduling."""
        return self._root is not None

    def schedule(self, delay_ms: int, callback) -> int | None:  # type: ignore
        """Schedule a one-shot ``after`` callback.

        Returns the cancel token, or ``None`` when there is no GUI root yet (the
        caller must then skip starting the timer).
        """
        if self._root is None:
            return None
        return self._root.after(delay_ms, callback)  # type: ignore

    def cancel(self, token: int | None) -> None:
        """Cancel a previously scheduled callback.

        ``token`` may be ``None`` (no GUI root was bound when the timer was
        started), so the guard is real, not dead code.
        """
        if self._root is not None and token is not None:
            self._root.after_cancel(token)  # type: ignore


# Global singleton, analogous to the event dispatcher.
scheduler: TimeScheduler = TimeScheduler()
