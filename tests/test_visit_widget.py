"""Tests for the visit-recency input widget (number of days).

``NumericLabelWidget`` is the shared editor for the two visit predicates
(``VisitedRecently`` / ``NotVisitedRecently``). The widget is the trust boundary
for the ``days`` input and -- unlike ``BaseInputWidget`` -- carries no NOT
toggle: polarity is class-level, so negation can't be applied here. tkinter runs
headless in this env, so the widget can be exercised directly.
"""

import tkinter as tk

import pytest

from surface_navigator.predicates import IsTemporary, VisitedRecently
from surface_navigator.query_builder.base import DataContext
from surface_navigator.query_builder.widgets.visit import NumericLabelWidget


@pytest.fixture(scope="module")
def root():
    r = tk.Tk()
    yield r
    r.destroy()


def _widget(root, owner, data=None):
    data = data or DataContext(db_manager=None, current_system_name=None)
    return NumericLabelWidget(
        owner,
        tk.Frame(root),
        data,
        leaf_cls=VisitedRecently,
        field="days",
        label="Days",
        unit="d",
    )


def test_validate_rejects_non_digits():
    assert NumericLabelWidget._validate("7") is True
    assert NumericLabelWidget._validate("7d") is False
    assert NumericLabelWidget._validate("") is True


def test_build_leaf_parses_days(root):
    w = _widget(root, VisitedRecently())
    w._value.set("7")
    leaf = w._build_leaf()
    assert isinstance(leaf, VisitedRecently)
    assert leaf.days == 7.0


def test_build_leaf_empty_is_no_filter(root):
    w = _widget(root, VisitedRecently())
    w._value.set("   ")
    assert w._build_leaf().days is None


def test_build_leaf_unparseable_is_no_filter(root):
    w = _widget(root, VisitedRecently())
    w._value.set("abc")
    assert w._build_leaf().days is None


def test_load_leaf_sets_value(root):
    w = _widget(root, VisitedRecently(14))
    assert w._value.get() == "14"


def test_has_no_not_button(root):
    # The whole point of the dedicated widget: no negation toggle, and it can't
    # be negated even if asked (a hand-edited NOT in a saved query is dropped).
    w = _widget(root, VisitedRecently())
    assert w.get_not_button() is None
    assert w.is_not() is False
    w.set_not(True)  # must be a harmless no-op
    assert w.is_not() is False


def test_load_leaf_rejects_wrong_predicate(root):
    # The base constructs the leaf on init, so a wrong predicate raises at
    # construction time -- the widget refuses to render a foreign predicate.
    with pytest.raises(TypeError):
        _widget(root, IsTemporary())
