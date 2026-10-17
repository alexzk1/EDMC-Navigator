"""Visit-recency input: a validated number of days, with a label but no NOT.

``VisitedRecently`` and ``NotVisitedRecently`` are structurally identical -- a
single non-negative number -- so they share this one widget class (like
``NumericInputWidget`` for the radius predicates). The difference is that these
predicates carry their polarity in their own class, so the widget inherits from
:class:`NoNotInputWidget` and never shows a ``NOT`` toggle.
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from ...predicates import Predicate
from ..base import DataContext
from ._common import NoNotInputWidget


class NumericLabelWidget(NoNotInputWidget):
    """A validated non-negative float entry bound to one predicate field.

    No NOT toggle: the owning predicate expresses negation through its class.
    """

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
        # Stored under a name that does NOT collide with the header label
        # widget (``self._label``) set by NoNotInputWidget._build_header().
        self._caption = label
        super().__init__(owner, parent, data)

    def _build_input(self) -> None:
        row = ttk.Frame(self)
        row.pack(fill=tk.X)
        ttk.Label(row, text=f"{self._caption} ({self._unit}):").pack(side=tk.LEFT)

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
        if not isinstance(pred, self._leaf_cls):
            raise TypeError(
                f"{type(self).__name__} must be used with "
                f"{self._leaf_cls.__name__}."
            )
        value = getattr(pred, self._field)
        self._value.set("" if value is None else str(value))
        self._refresh_label()
