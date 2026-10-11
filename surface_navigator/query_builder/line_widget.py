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
from collections.abc import Callable
from tkinter import ttk

from ..predicates import KNOWN_PREDICATES, And, Not, Predicate
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
        on_remove: Callable[[LineWidget], None],
    ) -> None:
        super().__init__(parent)
        self.data = data
        self._widgets: list[tuple[ttk.Frame, PredicateEditor]] = []
        self._line_not = tk.BooleanVar(value=False)
        self._on_activate = on_activate
        self._on_remove = on_remove

        self._build_ui()
        # A freshly created line is the natural target for the palette.
        self._on_activate(self)

    # -- UI ---------------------------------------------------------------
    def _build_ui(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(2, 2))

        # Line-level NOT toggle (a Checkbutton to distinguish it from the
        # per-widget NOT buttons).
        self._line_not_btn = ttk.Checkbutton(
            header, text="Neg", variable=self._line_not, command=self._refresh_label
        )
        self._line_not_btn.pack(side=tk.LEFT)

        self._label = ttk.Label(header, text="")
        self._label.pack(side=tk.LEFT, padx=(6, 6))

        remove_btn = ttk.Button(header, text="✕", width=3, command=self.remove)
        remove_btn.pack(side=tk.RIGHT)

        # The widgets are packed here, left to right.
        self._widgets_row = ttk.Frame(self)
        self._widgets_row.pack(fill=tk.X)

        self._add_btn = ttk.Button(
            self._widgets_row, text="＋", width=3, command=self._open_add_menu
        )
        self._add_btn.pack(side=tk.RIGHT, pady=2)

        self._refresh_label()

    def _open_add_menu(self) -> None:
        menu = tk.Menu(self._add_btn, tearoff=0)
        for cls in KNOWN_PREDICATES:
            label = cls().describe()
            menu.add_command(label=label, command=lambda c=cls: self._add(c, False))
            menu.add_command(
                label=f"NOT {label}",
                command=lambda c=cls: self._add(c, True),
            )
        # Post just below the add button.
        x = self._add_btn.winfo_x()
        y = self._add_btn.winfo_y() + self._add_btn.winfo_height()
        menu.post(x, y)

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
        self._refresh_label()
        self._on_activate(self)

    def remove_widget(self, widget: PredicateEditor) -> None:
        for container, other in self._widgets:
            if other is widget:
                self._widgets.remove((container, widget))
                container.destroy()
                self._refresh_label()
                break

    def remove(self) -> None:
        for container, _ in self._widgets:
            container.destroy()
        self._widgets.clear()
        self._on_remove(self)

    # -- round-trip -------------------------------------------------------
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

    def _refresh_label(self) -> None:
        node = self.build()
        children = [Not(w.predicate) if w.not_ else w.predicate for w in node.widgets]
        text = And(*children).describe() if children else ""
        if node.not_:
            text = f"NOT {text}"
        self._label.config(text=f"| QUERY: {text}")
