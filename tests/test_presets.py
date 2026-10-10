"""Tests for the query-builder presets and saved query (surface_navigator.presets).

These pin the two persistence paths:

* **Presets** -- built-ins (read-only) plus user presets stored in a JSON file,
  loaded and saved through :class:`PresetManager`. Saves are atomic (temp file +
  rename), so a crash mid-write can never leave a half-written file.
* **The current query** -- a single JSON string in EDMC config, round-tripped
  through :func:`save_current_query` / :func:`load_current_query`.
"""

import json
import os
import tempfile
from collections.abc import Iterator

import pytest

from surface_navigator.predicates import (
    And,
    HasTritiumRing,
    MineralIs,
    OnBody,
    Predicate,
)
from surface_navigator.presets import (
    BUILTIN_PRESETS,
    Preset,
    PresetManager,
    load_current_query,
    save_current_query,
)


def _config():
    from config import config

    return config


@pytest.fixture()
def presets_path() -> Iterator[str]:
    """A fresh empty user-presets file path in /tmp, removed after the test."""
    fd, path = tempfile.mkstemp(
        prefix="edmc_surface_navigator_presets_", suffix=".json", dir="/tmp"
    )
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture(autouse=True)
def _reset_config_settings():
    """Reset the in-memory config stub between tests."""
    from config import config

    config.settings.clear()
    yield
    config.settings.clear()


@pytest.fixture()
def manager(presets_path: str) -> PresetManager:
    return PresetManager(presets_path)


def _query() -> Predicate:
    return And(HasTritiumRing(), MineralIs("tritium"), OnBody("Kepler-442 b"))


def test_builtin_presets_are_readonly():
    assert BUILTIN_PRESETS, "there should be at least one built-in preset"
    assert all(p.readonly for p in BUILTIN_PRESETS)
    assert BUILTIN_PRESETS[0].name == "Find Any Tritium"


def test_load_returns_builtins_plus_user(manager: PresetManager):
    manager.add("My Search", _query())
    all_presets = manager.load()
    user_presets = manager.user_presets

    # Built-ins come first, then the one user preset.
    assert all(p.readonly for p in all_presets[: len(BUILTIN_PRESETS)])
    assert user_presets == [p for p in all_presets if not p.readonly]
    assert user_presets[0].name == "My Search"


def test_add_writes_file_and_roundtrips(manager: PresetManager):
    manager.add("My Search", _query())
    # A fresh manager reading the same file sees the preset.
    reloaded = PresetManager(manager.presets_path)
    assert reloaded.user_presets == [Preset(name="My Search", query=_query())]


def test_add_replaces_same_name(manager: PresetManager):
    manager.add("Search", MineralIs("Water"))
    manager.add("Search", MineralIs("Helium"))
    user = manager.user_presets
    assert len(user) == 1
    assert user[0].query == MineralIs("Helium")


def test_edit_updates_existing(manager: PresetManager):
    manager.add("Search", MineralIs("Water"))
    manager.edit("Search", MineralIs("Helium"))
    user = manager.user_presets
    assert len(user) == 1
    assert user[0].query == MineralIs("Helium")


def test_edit_missing_is_noop(manager: PresetManager):
    manager.add("Search", MineralIs("Water"))
    manager.edit("Does Not Exist", MineralIs("Helium"))
    assert len(manager.user_presets) == 1


def test_remove_excludes_builtins(manager: PresetManager):
    manager.remove(BUILTIN_PRESETS[0].name)  # cannot remove a built-in
    assert manager.load()[0].readonly
    assert manager.load()[0].name == BUILTIN_PRESETS[0].name


def test_save_is_atomic_no_temp_left_behind(manager: PresetManager):
    manager.add("Search", _query())
    directory = os.path.dirname(manager.presets_path)
    leftovers = [
        name
        for name in os.listdir(directory)
        if name.startswith("surface_navigator_presets")
        and name != os.path.basename(manager.presets_path)
    ]
    assert leftovers == []


def test_malformed_presets_are_skipped(presets_path: str):
    with open(presets_path, "w", encoding="utf-8") as f:
        json.dump(
            [
                {"name": "Good", "query": MineralIs("Water").to_dict()},
                {"nope": "missing name"},  # malformed: skipped
                {"name": "Bad", "query": {"type": "not_a_real_predicate"}},
            ],
            f,
        )
    manager = PresetManager(presets_path)
    names = [p.name for p in manager.user_presets]
    assert names == ["Good"]


def test_missing_file_yields_only_builtins(presets_path: str):
    os.remove(presets_path)
    manager = PresetManager(presets_path)
    assert manager.user_presets == []
    assert [p.name for p in manager.load()] == [p.name for p in BUILTIN_PRESETS]


def test_save_and_load_current_query():
    query = _query()

    save_current_query(query)
    assert "plugins.surface_navigator.query" in _config().settings
    assert load_current_query() == query


def test_save_current_query_none_erases_from_config():
    """An empty edit field (None) removes the key rather than storing junk."""
    save_current_query(_query())
    assert "plugins.surface_navigator.query" in _config().settings

    save_current_query(None)
    assert "plugins.surface_navigator.query" not in _config().settings
    assert load_current_query() is None


def test_load_current_query_none_when_unset():
    assert load_current_query() is None
