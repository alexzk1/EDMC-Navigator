"""Tkinter glue for the query builder: the base editor widget and shared data.

This module is the only place that imports ``tkinter`` for the builder. It
stays thin on purpose -- every predicate stays pure and lives in
:mod:`surface_navigator.predicates`; the widgets only render a predicate's own
fields and read the data they need (system/commodity lists) from
:class:`DataContext`.

Two things live here:

* :class:`PredicateEditor` -- the base class every predicate's editor inherits.
  It owns the NOT toggle and the two directions of the round-trip:
  ``get_predicate`` (read fields -> leaf) and ``load_leaf`` (leaf -> fields).
  The NOT flag is *not* applied here -- the line owns all ``Not`` wrapping so
  it lives in exactly one place (:func:`query_builder.render.build`).
* :class:`DataContext` -- read-only data the widgets may need for autocomplete
  or sensible defaults (known systems, commodities, the current system).
"""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..predicates import Predicate


class PredicateEditor(ttk.Frame):
    """Base class for one predicate's editor widget.

    Subclasses render their own inputs and implement :meth:`_build_leaf` (read
    fields -> leaf predicate) and :meth:`load_leaf` (leaf -> fields). The base
    owns the NOT toggle and the constructor wires up the round-trip by loading
    ``owner``.

    The ``owner`` is the predicate this editor represents: a blank instance
    when the user adds the widget from the palette (empty fields), or the real
    predicate when loading a saved query (fields pre-filled). That single
    distinction is what makes both directions work through ``load_leaf(owner)``.
    """

    def __init__(self, owner: Predicate, parent: tk.Widget, data: DataContext) -> None:
        super().__init__(parent)
        self.pack(fill=tk.BOTH, expand=True)
        self.owner = owner
        self.data = data
        # NOT lives here but is applied by the line, not by ``get_predicate``.
        self._not = tk.BooleanVar(value=False)
        # Subclasses build their own UI here, then call ``self.load_leaf(owner)``
        # once the widgets exist (``load_leaf`` touches them).

    # -- UI -> predicate ---------------------------------------------------
    def _build_leaf(self) -> Predicate:
        """Build the leaf predicate from the current field values."""
        raise NotImplementedError

    def get_predicate(self) -> Predicate:
        """Return the leaf predicate for the current field values.

        Does **not** apply the NOT flag -- the line wraps this in ``Not`` when
        the widget is negated, so ``Not`` is produced in exactly one place.
        """
        return self._build_leaf()

    # -- predicate -> UI ---------------------------------------------------
    def load_leaf(self, pred: Predicate) -> None:
        """Populate the editor's fields from a leaf predicate.

        Called with ``owner`` at construction (blank -> empty fields, real ->
        pre-filled). ``Not`` has already been unwrapped by the caller, so this
        only deals with the leaf's own fields.
        """
        raise NotImplementedError

    # -- NOT toggle (owned by this widget, applied by the line) ------------
    def is_not(self) -> bool:
        return self._not.get()

    def set_not(self, value: bool) -> None:
        self._not.set(value)
        self._refresh_label()

    def get_not_button(self) -> tk.Widget | None:
        """Return the NOT toggle button, or ``None`` if this editor has none.

        The line attaches a hover tooltip to it (see
        :mod:`query_builder.line_widget`). Base editors have no toggle;
        ``BaseInputWidget`` exposes its ``_not_btn``.
        """
        return None

    def _refresh_label(self) -> None:
        pass


class DataContext:
    """Read-only data the widgets may need for autocomplete or defaults.

    Holds a handle to the database (for known systems / bodies) and the
    current system name, so predicate logic stays pure while the widgets can
    still offer autocomplete against real catalogue data.
    """

    def __init__(
        self,
        db_manager: Any,
        current_system_name: str | None,
    ) -> None:
        self.db_manager = db_manager
        self.current_system_name = current_system_name

    def known_systems(self) -> list[str]:
        """Distinct star/system names known to the DB, for autocomplete."""
        return self.db_manager.known_systems()

    def known_bodies(self) -> list[str]:
        """Distinct body names known to the DB, for the ``on body`` widget."""
        return self.db_manager.known_bodies()

    def commodities(self) -> list[str]:
        """Every known commodity label, for the mineral widget autocomplete."""
        from ..mined_names import Commodities

        return Commodities.all_names()

    def current_system(self) -> str | None:
        return self.current_system_name
