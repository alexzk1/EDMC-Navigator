"""Numeric distance input, shared by the two light/km radius predicates.

``Within`` (km) and ``WithinLightYears`` (ly) are structurally identical -- a
single non-negative float -- so they share this one widget class. The leaf
class, the attribute it reads/writes, and the display label/unit are passed in
at construction, so the widget stays generic and the two predicates stay
distinct.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import Predicate
from ..base import DataContext
from ._common import BaseInputWidget


class NumericInputWidget(BaseInputWidget):
    """A validated non-negative float entry bound to one predicate field."""

    def __init__(
        self,
        owner: Predicate,
        parent: tk.Widget,
        data: DataContext,
        *,
        leaf_cls: type[Predicate],
        field: str,
        label: str,
        unit: str,
    ) -> None:
        self._leaf_cls = leaf_cls
        self._field = field
        self._unit = unit
        self._value = tk.StringVar()
        self._label = label
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text=f"{self._label} ({self._unit}):").pack(side=tk.LEFT)

        # Only allow digits, a single dot, and a leading minus (kept permissive;
        # an unparseable value simply yields a no-op predicate).
        vc = (self._register(self._validate), "%P")  # type: ignore
        self._entry = ttk.Entry(row, textvariable=self._value, width=12)
        self._entry.configure(validate="key", validatecommand=vc)  # type: ignore
        self._entry.pack(side=tk.LEFT, padx=(4, 0))
        self._entry.bind("<KeyRelease>", lambda _e: self._refresh_label())

    @staticmethod
    def _validate(p: str) -> bool:
        return p == "" or all(c in "0123456789.-" for c in p)

    def _build_leaf(self) -> Predicate:
        raw = self._value.get().strip()
        number: float | None = None
        if raw:
            try:
                number = float(raw)
            except ValueError:
                number = None
        return self._leaf_cls(**{self._field: number})

    def load_leaf(self, pred: Predicate) -> None:
        value = getattr(pred, self._field)
        self._value.set("" if value is None else str(value))
        self._refresh_label()
