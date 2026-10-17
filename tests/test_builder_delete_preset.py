"""Tests for the query-builder preset Delete button.

The listbox index maps directly to :class:`PresetManager` order -- which is the
persisted order -- so deleting shifts the rows up and the same index now points
at the next preset. This pins that behaviour (delete middle -> selection
follows; delete last user preset -> selection resets; built-ins cannot be
removed) and that the Delete button is disabled unless a deletable preset is
selected, without dragging a full window through the suite: the builder is
built via ``__new__`` and only the attributes the method touches are set by
hand.
"""

import os
import tempfile
from collections.abc import Iterator
from unittest.mock import MagicMock

import pytest
import tkinter as tk
from tkinter import ttk

# ``icons_cache`` builds ``PhotoImage``s at import time, which needs a default
# Tk root to exist first.
_root = tk.Tk()

from surface_navigator.presets import Preset, PresetManager
from surface_navigator.predicates import MineralIs
from surface_navigator.query_builder.builder_window import QueryBuilderWindow


@pytest.fixture()
def presets_path() -> Iterator[str]:
    fd, path = tempfile.mkstemp(
        prefix="edmc_surface_navigator_presets_", suffix=".json", dir="/tmp"
    )
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


def _builder(manager: PresetManager) -> QueryBuilderWindow:
    """A builder without the heavy ``__init__`` -- just the attributes touched by
    the delete flow: the listbox, the manager and the Delete button."""
    w = QueryBuilderWindow.__new__(QueryBuilderWindow)
    w._preset_list = tk.Listbox(_root, height=6)
    w._preset_list.pack()
    w._delete_btn = ttk.Button(_root, text="Delete")
    w._delete_btn.pack()
    w.preset_manager = manager
    return w


def _seed(manager: PresetManager, names: list[str]) -> None:
    # Two read-only built-ins always come first, mirroring the app, so the
    # listbox always has at least two rows.
    manager.builtins = [
        Preset(name="Builtin A", query=MineralIs("Water"), readonly=True),
        Preset(name="Builtin B", query=MineralIs("Water"), readonly=True),
    ]
    for name in names:
        manager.add(name, MineralIs(name))


def _select(builder: QueryBuilderWindow, idx: int) -> None:
    builder._preset_list.selection_clear(0, builder._preset_list.size())
    builder._preset_list.selection_set(idx)


# ---- Delete a middle user preset -------------------------------------------


def test_delete_middle_shifts_up_and_selection_follows(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2", "p3", "p4"])  # listbox: B0 B1 p2 p3 p4
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 2)  # select p2

    builder._delete_selected_preset()

    # p2 gone; p3 shifted up into index 2, and the selection is there.
    assert [p.name for p in manager.load()] == ["Builtin A", "Builtin B", "p3", "p4"]
    assert manager.user_presets == [Preset(name="p3", query=MineralIs("p3")),
                                    Preset(name="p4", query=MineralIs("p4"))]
    assert builder._preset_list.curselection() == (2,)


def test_order_in_memory_is_preserved(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["a", "b", "c"])  # listbox: B0 B1 a b c
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 3)  # select "b"

    builder._delete_selected_preset()

    # "b" removed; "a" and "c" keep their relative order.
    assert [p.name for p in manager.load()] == [
        "Builtin A",
        "Builtin B",
        "a",
        "c",
    ]


# ---- Read-only built-ins cannot be deleted ---------------------------------


def test_delete_builtin_is_noop(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2"])  # listbox: B0 B1 p2
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 0)  # select the first built-in

    builder._delete_selected_preset()

    assert [p.name for p in manager.load()] == ["Builtin A", "Builtin B", "p2"]
    assert builder._preset_list.curselection() == (0,)


# ---- Deleting down to the built-ins ----------------------------------------


def test_delete_last_user_preset_resets_selection(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2"])  # listbox: B0 B1 p2
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 2)  # select p2

    builder._delete_selected_preset()

    assert manager.user_presets == []
    assert [p.name for p in manager.load()] == ["Builtin A", "Builtin B"]
    # Index 2 is now out of range (only two built-ins) -> no selection.
    assert builder._preset_list.curselection() == ()


def test_repeated_delete_walks_down_the_list(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2", "p3", "p4", "p5"])
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 2)

    for _ in range(4):
        builder._delete_selected_preset()

    # All four user presets gone; only the two built-ins remain, unselected.
    assert manager.user_presets == []
    assert [p.name for p in manager.load()] == ["Builtin A", "Builtin B"]
    assert builder._preset_list.curselection() == ()


def test_delete_without_selection_is_noop(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2", "p3"])
    builder = _builder(manager)
    builder._reload_presets()  # nothing selected

    builder._delete_selected_preset()

    assert [p.name for p in manager.load()] == [
        "Builtin A",
        "Builtin B",
        "p2",
        "p3",
    ]


# ---- Delete button enable/disable state ------------------------------------


def _is_enabled(builder: QueryBuilderWindow) -> bool:
    """Whether the Delete button is currently enabled (``state()`` returns the
    live flag tuple for a ttk widget)."""
    return "disabled" not in builder._delete_btn.state()


def test_deletable_at_only_in_range_user_presets(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2", "p3"])
    builder = _builder(manager)
    # Built-ins (indices 0-1) and out-of-range indices are never deletable;
    # user presets are.
    assert builder._deletable_at(0) is False
    assert builder._deletable_at(2) is True
    assert builder._deletable_at(99) is False


def test_delete_button_disabled_without_selection(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2", "p3"])
    builder = _builder(manager)
    builder._reload_presets()
    builder._update_delete_button_state()
    assert not _is_enabled(builder)


def test_delete_button_disabled_on_readonly(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2"])
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 0)  # a read-only built-in
    builder._update_delete_button_state()
    assert not _is_enabled(builder)


def test_delete_button_enabled_on_user_preset(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2"])
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 2)  # a user preset
    builder._update_delete_button_state()
    assert _is_enabled(builder)


def test_delete_button_disabled_after_last_user_preset_gone(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2"])
    builder = _builder(manager)
    builder._reload_presets()
    _select(builder, 2)
    assert _is_enabled(builder)

    builder._delete_selected_preset()

    # Selection reset to empty -> button disabled again.
    assert not _is_enabled(builder)


# ---- Selection no longer auto-loads ----------------------------------------


def test_selection_change_does_not_auto_load(presets_path: str):
    manager = PresetManager(presets_path)
    _seed(manager, ["p2"])
    builder = _builder(manager)
    builder._reload_presets()
    builder._load_selected_preset = MagicMock()  # type: ignore[method-assign]
    _select(builder, 2)

    builder._on_preset_selected()

    # A selection change only refreshes the Delete button state; loading is an
    # explicit LOAD-button action, so it must not happen on selection.
    builder._load_selected_preset.assert_not_called()
