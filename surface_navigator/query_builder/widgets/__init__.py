"""Package of per-predicate editor widgets.

Each predicate owns exactly one editor widget class here (see
:meth:`surface_navigator.predicates.Predicate.make_widget`). The predicate
forwards ``make_widget(parent, *, data)`` to ``XWidget(self, parent, data)``;
the widget reads/writes the predicate's own fields so predicate logic stays
pure and testable.
"""

from __future__ import annotations

from ..base import DataContext, PredicateEditor

__all__ = ["PredicateEditor", "DataContext"]
