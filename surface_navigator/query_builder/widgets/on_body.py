"""On-body input with autocomplete.

Binds to :class:`OnBody.body_name`. Autocompletes against the bodies already
known to the DB.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import OnBody, Predicate
from ..base import DataContext
from ._common import BaseInputWidget


class OnBodyInputWidget(BaseInputWidget):
    """A combobox of known bodies bound to ``OnBody``."""

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        self._selected = tk.StringVar()
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Body:").pack(side=tk.LEFT)
        combobox = ttk.Combobox(row, textvariable=self._selected, width=28)
        combobox.pack(side=tk.LEFT, padx=(4, 0))
        combobox.bind("<<ComboboxSelected>>", lambda _e: self._refresh_label())
        self._combobox = combobox
        self._populate()

    def _populate(self) -> None:
        self._combobox.config(values=self.data.known_bodies())

    def _build_leaf(self) -> Predicate:
        name = self._selected.get().strip() or None
        return OnBody(name)

    def load_leaf(self, pred: Predicate) -> None:
        if not isinstance(pred, OnBody):
            raise TypeError("OnBodyInputWidget must be used with OnBody predicated.")
        self._selected.set(pred.body_name or "")
        self._refresh_label()
