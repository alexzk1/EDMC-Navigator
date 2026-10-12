"""A single builder line: widgets AND'ed together, optionally negated.

A line is the OR operand of the builder. Its widgets are AND'ed (via
:func:`query_builder.render.build`), and a NOT toggle wraps the whole AND in
``Not``. Each widget carries its own NOT too (the per-widget negation), so the
builder can express ``NOT (A AND B)`` as well as ``NOT A AND B``.

The line owns the round-trip for its own level: :meth:`build` produces a
:class:`LineNode`; :meth:`load` recreates the widgets from one.
"""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable, Iterator
from tkinter import ttk

from ..predicates import KNOWN_PREDICATES, And, Not, Predicate
from ..ui_tooltip import Tooltip
from .base import DataContext, PredicateEditor
from .render import LineNode, WidgetNode


class LineWidget(ttk.Frame):
    """One OR operand: an AND-group of widget editors with a NOT toggle."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        data: DataContext,
        on_activate: Callable[[LineWidget], None],
        on_remove: Callable[[LineWidget], bool],
    ) -> None:
        super().__init__(parent)
        self.data = data
        self._widgets: list[tuple[ttk.Frame, PredicateEditor]] = []
        self._line_not = tk.BooleanVar(value=False)
        self._on_activate = on_activate
        self._on_remove = on_remove
        # Hover tooltips. ``_tooltips`` holds the line-level ones (detached when
        # the line is removed); ``_widget_tooltips`` maps a widget to its own
        # NOT-toggle tooltip so ``remove_widget`` can detach just that one.
        self._tooltips: list[Tooltip] = []
        self._widget_tooltips: dict[PredicateEditor, Tooltip] = {}

        self._build_ui()
        # A freshly created line is the natural target for the palette.
        self._on_activate(self)

    # -- UI ---------------------------------------------------------------
    def _build_ui(self) -> None:
        # OR separator: the topmost element of the line, so everything else
        # (header + widgets) sits under it. The first line keeps an empty
        # marker here (set by the host) so every line has the same top offset.
        self._or_label = ttk.Label(self, text="")
        self._or_label.pack(fill=tk.X)

        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(2, 2))

        # Line-level NOT toggle (a Checkbutton to distinguish it from the
        # per-widget NOT buttons).
        self._line_not_btn = ttk.Checkbutton(
            header, text="🔁 Neg", variable=self._line_not, command=self._refresh_label
        )
        self._line_not_btn.pack(side=tk.LEFT)

        self._label = ttk.Label(header, text="")
        self._label.pack(side=tk.LEFT, padx=(6, 6))

        self._remove_btn = ttk.Button(header, text="✕", width=3, command=self.remove)
        self._remove_btn.pack(side=tk.RIGHT)

        # The widgets are packed here, left to right.
        self._widgets_row = ttk.Frame(self)
        self._widgets_row.pack(fill=tk.X)

        self._add_btn = ttk.Button(
            self._widgets_row, text="＋", width=3, command=self._open_add_menu
        )
        self._add_btn.pack(side=tk.RIGHT, pady=2)

        self._refresh_label()
        # Line-level tooltips. These controls live for the line's whole life,
        # so they are torn down together with the line in ``remove``.
        self._add_tooltip(
            self._line_not_btn, "Negate this whole line -- inverts the whole AND-group."
        )
        self._add_tooltip(self._remove_btn, "Remove this whole line from the query.")
        self._add_tooltip(
            self._add_btn,
            "Add a condition to this line via AND. Press to see the list.",
        )

    def set_or_separator(self, text: str) -> None:
        """Show/hide the ``-- OR --`` marker above this line.

        The host calls this whenever the line list changes: a freshly added
        line gets the marker (it ORs with the lines above it), while the first
        line always gets a blank marker so the stack stays aligned.
        """
        self._or_label.config(text=text)

    def _open_add_menu(self) -> None:
        menu = tk.Menu(self._add_btn, tearoff=0)
        for cls in KNOWN_PREDICATES:
            label = cls().describe()
            menu.add_command(label=label, command=lambda c=cls: self._add(c, False))
            menu.add_command(
                label=f"NOT {label}",
                command=lambda c=cls: self._add(c, True),
            )
        # A way to dismiss the menu without picking a predicate. ``lambda: None``
        # (rather than ``menu.destroy``) lets ``tk_popup`` withdraw the menu
        # itself, so the ``grab_release`` in ``finally`` stays happy.
        menu.add_separator()
        menu.add_command(label="Cancel", command=lambda: None)
        # ``tk_popup`` takes *absolute* screen coords, so the menu appears
        # straight under the add button no matter where the line sits in the
        # window. ``winfo_rootx``/``winfo_rooty`` are the button's position
        # relative to the screen root; adding the button height drops the menu
        # just below it. (The old ``winfo_x``/``winfo_y`` were relative to the
        # button's parent *frame*, which offset the menu sideways.)
        try:
            menu.tk_popup(
                self._add_btn.winfo_rootx(),
                self._add_btn.winfo_rooty() + self._add_btn.winfo_height(),
            )
        finally:
            menu.grab_release()

    # -- adding / removing widgets ----------------------------------------
    def add_widget(self, pred: Predicate, not_: bool) -> None:
        """Create an editor for ``pred`` and append it to this line.

        ``pred`` is a blank instance (palette add) or a real predicate (load);
        ``make_widget`` handles both. If ``not_`` the widget is negated.
        """
        container = ttk.Frame(self._widgets_row)
        container.pack(side=tk.LEFT, padx=2)
        self._widgets_row.pack(fill=tk.X)
        widget: PredicateEditor = pred.make_widget(parent=container, data=self.data)
        if not_:
            widget.set_not(True)
        self._widgets.append((container, widget))
        # The NOT toggle lives in the container (destroyed on removal), so the
        # tooltip is tracked per-widget and detached in ``remove_widget``.
        not_btn = widget.get_not_button()
        if not_btn is not None:
            self._widget_tooltips[widget] = Tooltip(
                not_btn, "Toggle the negation of this condition."
            )
        self._refresh_label()
        self._on_activate(self)

    def remove_widget(self, widget: PredicateEditor) -> None:
        for container, other in self._widgets:
            if other is widget:
                self._widgets.remove((container, widget))
                # Detach before the container (and its NOT button) is gone.
                tip = self._widget_tooltips.pop(widget, None)
                if tip is not None:
                    tip.detach()
                container.destroy()
                self._refresh_label()
                break

    def destroy_internal(self) -> None:
        """Detach tooltips and tear down internal widgets without notifying the host.

        Every removal path must run this so internal state (``_widgets``,
        ``_tooltips``, ``_widget_tooltips``) never leaks and orphaned tip
        windows can't outlive their widgets. ``remove`` calls it before
        notifying the host; the builder's reload path calls it directly before
        destroying the frame.
        """
        # Detach per-widget tooltips first: their buttons live inside the
        # containers we are about to destroy.
        for tip in self._widget_tooltips.values():
            tip.detach()
        self._widget_tooltips.clear()
        for container, _ in self._widgets:
            container.destroy()
        self._widgets.clear()
        # Then the line-level tooltips (line NOT, remove, add).
        for tip in self._tooltips:
            tip.detach()
        self._tooltips.clear()

    def remove(self) -> bool:
        self.destroy_internal()
        return self._on_remove(self)

    # -- round-trip -------------------------------------------------------
    def iter_widgets(self) -> Iterator[PredicateEditor]:
        """Yield the live editors in order (used by the host to refresh them)."""
        for _container, widget in self._widgets:
            yield widget

    def build(self) -> LineNode:
        widgets = [
            WidgetNode(predicate=w.get_predicate(), not_=w.is_not())
            for _, w in self._widgets
        ]
        return LineNode(widgets=widgets, not_=self._line_not.get())

    def load(self, node: LineNode) -> None:
        self._line_not.set(node.not_)
        for wn in node.widgets:
            self.add_widget(wn.predicate, wn.not_)
        self._refresh_label()

    # -- helpers ----------------------------------------------------------
    def _add(self, cls: type[Predicate], not_: bool) -> None:
        self.add_widget(cls(), not_)

    def _add_tooltip(self, widget: tk.Widget, text: str) -> None:
        """Attach a static hover tooltip and remember it for cleanup."""
        tip = Tooltip(widget, text)
        self._tooltips.append(tip)

    def _refresh_label(self) -> None:
        node = self.build()
        children = [Not(w.predicate) if w.not_ else w.predicate for w in node.widgets]
        text = And(*children).describe() if children else ""
        if node.not_:
            text = f"NOT {text}"
        self._label.config(text=f"| QUERY: {text}")
