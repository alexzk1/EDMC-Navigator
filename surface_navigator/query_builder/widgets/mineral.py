"""Mineral input with commodity autocomplete.

Picks a commodity from the catalogue (fuzzy-matched against the real list) so
the user does not have to type an exact name. Backed by
:meth:`surface_navigator.mined_names.Commodities.all_names`.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import MineralIs, Predicate
from ..base import DataContext
from ._common import BaseInputWidget


class MineralInputWidget(BaseInputWidget):
    """A combobox of commodities bound to :class:`MineralIs.user_input`."""

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        self._selected = tk.StringVar()
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Mineral:").pack(side=tk.LEFT)
        combobox = ttk.Combobox(row, textvariable=self._selected, width=28)
        combobox.pack(side=tk.LEFT, padx=(4, 0))
        # Refresh the describe label as the user picks / types a commodity.
        combobox.bind("<<ComboboxSelected>>", lambda _e: self._refresh_label())
        self._combobox = combobox
        self._populate()

    def _populate(self) -> None:
        names = self.data.commodities()
        self._combobox.config(values=names)

    def _build_leaf(self) -> Predicate:
        return MineralIs(self._selected.get())

    def load_leaf(self, pred: Predicate) -> None:
        if not isinstance(pred, MineralIs):
            raise TypeError(
                "MineralInputWidget must be used with MineralIs predicated."
            )

        self._selected.set(pred.user_input or "")
        self._refresh_label()
