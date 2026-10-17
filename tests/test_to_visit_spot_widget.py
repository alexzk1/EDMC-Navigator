"""Tests for the ToVisitSpot predicate's widget wiring.

``ToVisitSpot`` takes no input -- it is a boolean "not a mining spot" flag -- so
it renders through the shared display-only :class:`FlagStatusWidget`. This pins
the one integration detail that is not covered elsewhere: the predicate's
``make_widget`` produces a flag widget whose leaf is a ``ToVisitSpot``.
"""

import tkinter as tk

import pytest

from surface_navigator.predicates import ToVisitSpot
from surface_navigator.query_builder.base import DataContext
from surface_navigator.query_builder.widgets.flag import FlagStatusWidget


@pytest.fixture(scope="module")
def root():
    r = tk.Tk()
    yield r
    r.destroy()


def test_make_widget_is_flag_widget(root):
    data = DataContext(db_manager=None, current_system_name=None)
    w = ToVisitSpot().make_widget(parent=tk.Frame(root), data=data)
    assert isinstance(w, FlagStatusWidget)


def test_flag_widget_builds_to_visit_leaf(root):
    # FlagStatusWidget rebuilds the leaf from its owner class, so a ToVisitSpot
    # owner must yield a ToVisitSpot leaf.
    data = DataContext(db_manager=None, current_system_name=None)
    w = ToVisitSpot().make_widget(parent=tk.Frame(root), data=data)
    assert isinstance(w._build_leaf(), ToVisitSpot)
