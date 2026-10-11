"""Light-year radius around a *named* star.

Binds to :class:`WithinLightYearsOfStar` -- a distance plus a centre star. It
is the general case; :class:`WithinLightYears` is the current-star special case
handled by :class:`numeric.NumericInputWidget`. The centre star is resolved
online by the engine before the search runs.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import Predicate, WithinLightYearsOfStar
from ..base import DataContext
from ._common import BaseInputWidget


class StarDistanceInputWidget(BaseInputWidget):
    """A distance entry plus a star combobox, bound to ``WithinLightYearsOfStar``."""

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        self._distance = tk.StringVar()
        self._star = tk.StringVar()
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text="Distance (ly):").pack(side=tk.LEFT)

        vc = (self._register(self._validate), "%P")  # type: ignore
        self._entry = ttk.Entry(row, textvariable=self._distance, width=10)
        self._entry.configure(validate="key", validatecommand=vc)  # type: ignore
        self._entry.pack(side=tk.LEFT)
        self._entry.bind("<KeyRelease>", lambda _e: self._refresh_label())

        ttk.Label(row, text="of star:").pack(side=tk.LEFT, padx=(8, 0))
        self._combobox = ttk.Combobox(row, textvariable=self._star, width=16)
        self._combobox.pack(side=tk.LEFT, padx=(4, 0))
        self._combobox.bind("<<ComboboxSelected>>", lambda _e: self._refresh_label())
        self._populate()

    @staticmethod
    def _validate(p: str) -> bool:
        return p == "" or all(c in "0123456789.-" for c in p)

    def _populate(self) -> None:
        self._combobox.config(values=self.data.known_systems())

    def _build_leaf(self) -> Predicate:
        distance: float | None = None
        raw = self._distance.get().strip()
        if raw:
            try:
                distance = float(raw)
            except ValueError:
                distance = None
        star = self._star.get().strip() or None
        return WithinLightYearsOfStar(distance_ly=distance, star_name=star)

    def load_leaf(self, pred: Predicate) -> None:
        self._distance.set("" if pred.distance_ly is None else str(pred.distance_ly))  # type: ignore
        self._star.set(pred.star_name or "")  # type: ignore
        self._refresh_label()
