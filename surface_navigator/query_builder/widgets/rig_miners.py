"""Rig miner count input: a validated integer in 1-12.

``max_miners`` is an integer count, and no ship carries more than 12 miners, so
this widget rejects non-integers and clamps out-of-range values into 1-12
(backed by :class:`surface_navigator.predicates.HasMiners`).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import HasMiners, Predicate
from ..base import DataContext
from ._common import BaseInputWidget

MIN_MINERS = 1
MAX_MINERS = 12


class HasMinersInputWidget(BaseInputWidget):
    """An integer entry bound to :class:`HasMiners.miners`, clamped to 1-12."""

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        self._value = tk.StringVar()
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Rig Miners:").pack(side=tk.LEFT)

        # Digits only; an unparseable value yields a no-op predicate.
        vc = (self._register(self._validate), "%P")  # type: ignore
        self._entry = ttk.Entry(row, textvariable=self._value, width=12)
        self._entry.configure(validate="key", validatecommand=vc)  # type: ignore
        self._entry.pack(side=tk.LEFT, padx=(4, 0))
        self._entry.bind("<KeyRelease>", lambda _e: self._refresh_label())

    @staticmethod
    def _validate(p: str) -> bool:
        return p == "" or all(c in "0123456789" for c in p)

    def _build_leaf(self) -> Predicate:
        raw = self._value.get().strip()
        if not raw:
            return HasMiners(None)
        try:
            count = int(raw)
        except ValueError:
            # A lone "+" / "-" / "." slips past ``_validate`` only if typed in a
            # way that survives; treat anything unparseable as "no filter".
            return HasMiners(None)
        # Clamp to what a ship can actually carry: 1-12.
        return HasMiners(min(max(count, MIN_MINERS), MAX_MINERS))

    def load_leaf(self, pred: Predicate) -> None:
        if not isinstance(pred, HasMiners):
            raise TypeError(
                "HasMinersInputWidget must be used with HasMiners predicate."
            )
        self._value.set("" if pred.miners is None else str(pred.miners))
        self._refresh_label()
