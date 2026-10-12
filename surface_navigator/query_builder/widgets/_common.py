"""Shared base for input widgets: header (NOT toggle + describe label) + input.

Every leaf editor shares the same chrome: a ``NOT`` button on the left that
flips the widget's negation, and a live label that mirrors
``predicate.describe()`` (prefixed with ``NOT `` when negated). Subclasses
pack their input below the header and implement :meth:`_build_input` and
:meth:`load_leaf`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import Predicate
from ..base import DataContext, PredicateEditor


class BaseInputWidget(PredicateEditor):
    """Base for widgets that render a single-field input plus a NOT toggle."""

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        super().__init__(owner, parent, data)
        self._build_header()
        self._build_input()
        self.load_leaf(owner)

    # -- chrome ------------------------------------------------------------
    def _build_header(self) -> None:
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 4))
        self._not_btn = ttk.Button(
            header, text="🔁Neg", width=5, command=self._toggle_not
        )
        self._not_btn.pack(side=tk.LEFT)
        self._label = ttk.Label(header, text="")
        self._label.pack(side=tk.LEFT, padx=(4, 0))

    def get_not_button(self) -> tk.Widget | None:
        return self._not_btn

    def _toggle_not(self) -> None:
        self.set_not(not self._not.get())

    def _refresh_label(self) -> None:
        text = self.get_predicate().describe()
        if self.is_not():
            text = f"NOT {text}"
        self._label.config(text=text)

    # -- subclasses implement ---------------------------------------------
    def _build_input(self) -> None:  # pragma: no cover - overridden
        raise NotImplementedError
