"""Display-only current-system widget.

``SearchInCurrentSystem`` takes no input -- it matches the player's current
system. The widget shows the predicate label and, when known, the current
system name, so the user sees what the condition targets.
"""

from __future__ import annotations

from ...predicates import Predicate, SearchInCurrentSystem
from ._common import BaseInputWidget


class CurrentSystemInfoWidget(BaseInputWidget):
    """Static label for the current-system predicate, annotated with the name."""

    def _build_input(self) -> None:
        pass  # nothing beyond the shared header label

    def _build_leaf(self) -> Predicate:
        return SearchInCurrentSystem()

    def load_leaf(self, pred: Predicate) -> None:
        self._refresh_label()
