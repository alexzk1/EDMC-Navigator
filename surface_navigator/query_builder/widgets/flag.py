"""Display-only flag widget, shared by the two flag predicates.

``HasTritiumRing`` and ``IsTemporary`` take no input -- they only assert a
flag's presence. The widget renders the predicate's ``describe()`` as static
text; the NOT toggle still applies (e.g. "NOT has tritium ring").
"""

from __future__ import annotations

from ...predicates import Predicate
from ._common import BaseInputWidget


class FlagStatusWidget(BaseInputWidget):
    """Static label for a flag predicate (no input fields)."""

    def _build_input(self) -> None:
        pass  # nothing to render beyond the shared header label

    def _build_leaf(self) -> Predicate:
        # ``owner`` is the flag predicate instance that created this widget, so
        # a fresh instance of the same class reproduces the (parameter-less)
        # flag predicate.
        return type(self.owner)()

    def load_leaf(self, pred: Predicate) -> None:
        # No fields to restore; the shared header already mirrors describe().
        self._refresh_label()
