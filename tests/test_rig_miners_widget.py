"""Tests for the rig miner count input widget (range 1-12).

The widget is the trust boundary for the ``max_miners`` input: it must reject
non-integers and clamp out-of-range values into 1-12. tkinter runs headless in
this env, so the widget can be exercised directly.
"""

import tkinter as tk

import pytest

from surface_navigator.predicates import HasMiners, MineralIs
from surface_navigator.query_builder.base import DataContext
from surface_navigator.query_builder.widgets.rig_miners import (
    MAX_MINERS,
    MIN_MINERS,
    HasMinersInputWidget,
)


@pytest.fixture(scope="module")
def root():
    r = tk.Tk()
    yield r
    r.destroy()


def _widget(root, owner, data=None):
    data = data or DataContext(db_manager=None, current_system_name=None)
    return HasMinersInputWidget(owner, tk.Frame(root), data)


def test_validate_rejects_non_digits():
    assert HasMinersInputWidget._validate("12") is True
    assert HasMinersInputWidget._validate("1a") is False
    assert HasMinersInputWidget._validate("") is True


def test_build_leaf_clamps_above_max(root):
    w = _widget(root, HasMiners())
    w._value.set("13")
    assert w._build_leaf().miners == MAX_MINERS


def test_build_leaf_clamps_below_min(root):
    w = _widget(root, HasMiners())
    w._value.set("0")
    assert w._build_leaf().miners == MIN_MINERS


def test_build_leaf_keeps_in_range(root):
    w = _widget(root, HasMiners())
    w._value.set("7")
    assert w._build_leaf().miners == 7


def test_build_leaf_empty_is_no_filter(root):
    w = _widget(root, HasMiners())
    w._value.set("")
    assert w._build_leaf().miners is None


def test_load_leaf_sets_value(root):
    w = _widget(root, HasMiners(5))
    assert w._value.get() == "5"


def test_load_leaf_rejects_wrong_predicate(root):
    # The base constructs the leaf on init, so a wrong predicate raises at
    # construction time -- the widget refuses to render a foreign predicate.
    with pytest.raises(TypeError):
        _widget(root, MineralIs("iridium"))
