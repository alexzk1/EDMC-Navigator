import tkinter as tk


class CanvasVerticalMouseWheelScroller:
    """
    Handles vertical mouse wheel scrolling for a Tkinter Canvas,
    correctly supporting Windows, macOS, and Linux.

    Details:
    - Windows/macOS: uses <MouseWheel> events with event.delta divided by 120.
    - Linux (X11): uses mouse buttons Button-4 (scroll up) and Button-5 (scroll down).

    Attach this handler to a canvas to enable smooth vertical scrolling.
    """

    def __init__(self, target_canvas: tk.Canvas, *, attach: bool = False):
        """
        Initialize the scroller.

        :param target_canvas: Tkinter Canvas widget to scroll.
        :param attach if True, calls self.attach() too.
        """
        self._canvas = target_canvas
        if attach:
            self.attach()

    def attach(self) -> None:
        """
        Attach scroll event handlers to the canvas.
        """
        self._canvas.bind("<MouseWheel>", self._on_mousewheel)  # Windows/macOS
        self._canvas.bind("<Button-4>", self._on_mousewheel_linux)  # Linux scroll up
        self._canvas.bind("<Button-5>", self._on_mousewheel_linux)  # Linux scroll down

    def detach(self) -> None:
        """
        Detach scroll event handlers from the canvas.
        """
        self._canvas.unbind("<MouseWheel>")
        self._canvas.unbind("<Button-4>")
        self._canvas.unbind("<Button-5>")

    def _on_mousewheel(self, event: tk.Event) -> None:
        """
        Mouse wheel event handler for Windows and macOS.

        :param event: Tkinter event object.
        """
        if self._canvas:
            # event.delta / 120 represents one scroll step
            self._canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def _on_mousewheel_linux(self, event: tk.Event) -> None:
        """
        Mouse wheel event handler for Linux.

        :param event: Tkinter event object.
        """
        if not self._canvas:
            return

        if event.num == 4:
            self._canvas.yview_scroll(-1, "units")  # scroll up
        elif event.num == 5:
            self._canvas.yview_scroll(1, "units")  # scroll down
