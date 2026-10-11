"""Exact-system-name input with autocomplete.

Binds to :class:`SearchInExactSystem.system_name`. Autocompletes against the
systems already known to the DB so the user can name a system without
remembering the spelling.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import Predicate, SearchInExactSystem
from ..base import DataContext
from ._common import BaseInputWidget


class SystemInputWidget(BaseInputWidget):
    """A combobox of known systems bound to ``SearchInExactSystem``."""

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        self._selected = tk.StringVar()
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text="System:").pack(side=tk.LEFT)
        combobox = ttk.Combobox(row, textvariable=self._selected, width=28)
        combobox.pack(side=tk.LEFT, padx=(4, 0))
        combobox.bind("<<ComboboxSelected>>", lambda _e: self._refresh_label())
        self._combobox = combobox
        self._populate()

    def _populate(self) -> None:
        self._combobox.config(values=self.data.known_systems())

    def _build_leaf(self) -> Predicate:
        name = self._selected.get().strip() or None
        return SearchInExactSystem(name)

    def load_leaf(self, pred: Predicate) -> None:
        self._selected.set(pred.system_name or "")  # type: ignore
        self._refresh_label()
