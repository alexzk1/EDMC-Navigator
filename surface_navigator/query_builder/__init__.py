"""Query builder: the non-modal window for composing surface searches.

Layout of the package:

* :mod:`render` -- pure (UI-independent) model + conversions. ``build`` turns
  :class:`BuilderState` into a predicate tree; ``load`` splits a tree back into
  state, unwrapping ``Not`` at every level. This is the testable core.
* :mod:`base` -- the Tkinter glue: :class:`PredicateEditor` (base editor) and
  :class:`DataContext` (autocomplete data).
* :mod:`line_widget` -- a line: a group of widgets AND'ed, with a NOT toggle.
* :mod:`builder_window` -- the whole builder: lines OR'ed, palette, presets,
  results, and the delete-temporaries buttons.
* :mod:`widgets` -- one editor class per predicate (see
  :mod:`surface_navigator.predicates` ``make_widget``).
"""

from __future__ import annotations

__all__ = ["render", "base", "line_widget", "builder_window"]
