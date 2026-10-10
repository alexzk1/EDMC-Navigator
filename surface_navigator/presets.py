"""Presets and the saved query for the query builder.

Two things persist across sessions:

* **Presets** -- named, reusable query trees. Built-in presets live in code
  (read-only, shipped with the plugin); user presets live in a JSON file next
  to the DB. :class:`PresetManager` loads built-ins plus user presets and saves
  user presets atomically (temp file + rename) so a crash can never leave a
  half-written file.
* **The current query** -- the query the user is actively building. It is a
  single JSON string in EDMC config, so it survives a restart.

Serialization of the trees is handled by :mod:`surface_navigator.predicates`
(``to_dict`` / ``deserialize``) -- this module only decides *where* things live.
"""

from __future__ import annotations

import json
import logging
import os
import tempfile
from dataclasses import dataclass
from typing import Any

from .predicates import HasTritiumRing, MineralIs, Or, Predicate, deserialize

logger = logging.getLogger("SurfaceNavigator")

# Config key for the currently-built query (stored as a JSON string). Lowercase
# because ``config.set``/``get`` fold keys to lower case.
CURRENT_QUERY_KEY = "plugins.surface_navigator.query"

# File name for user presets -- kept next to the DB, so it rides the same
# fallback (app_dir -> plugin_dir) the DB uses.
PRESETS_FILENAME = "surface_navigator_presets.json"


@dataclass
class Preset:
    """A named, reusable query tree.

    ``readonly`` presets are built-ins: the user can read them but not edit or
    remove them. User presets (``readonly=False``) are fully editable.
    """

    name: str
    query: Predicate
    readonly: bool = False


# ---- Built-in query library ------------------------------------------------

# Read-only presets shipped with the plugin. The UI shows these first and lets
# the user edit/remove only their own presets. The combined "rings or spots"
# search is the default example -- the user can read it, not change it.
BUILTIN_PRESETS: list[Preset] = [
    Preset(
        name="Find Any Tritium",
        query=Or(HasTritiumRing(), MineralIs("tritium")),
        readonly=True,
    ),
]


# ---- Atomic file writes ----------------------------------------------------


def _atomic_write_json(path: str, data: object) -> None:
    """Write ``data`` as JSON to ``path`` atomically.

    The data is written to a sibling temp file, flushed, fsync'd, and
    ``os.replace``-ed into place. ``os.replace`` is atomic on POSIX, so a crash
    mid-write leaves either the previous file or the new one -- never a
    half-written one.
    """
    directory = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    os.replace(tmp_path, path)


# ---- Preset manager --------------------------------------------------------


class PresetManager:
    """Loads built-in + user presets and persists user presets atomically."""

    def __init__(self, presets_path: str, builtins: list[Preset] | None = None) -> None:
        self.presets_path = presets_path
        self.builtins = (
            list(builtins) if builtins is not None else list(BUILTIN_PRESETS)
        )

    def load(self) -> list[Preset]:
        """All presets: read-only built-ins followed by user presets."""
        return [*self.builtins, *self._read_user_presets()]

    @property
    def user_presets(self) -> list[Preset]:
        """User presets only -- the ones that can be edited or removed."""
        return [p for p in self.load() if not p.readonly]

    def _read_user_presets(self) -> list[Preset]:
        if not os.path.isfile(self.presets_path):
            return []
        try:
            with open(self.presets_path, encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning("Could not read presets %s: %s", self.presets_path, e)
            return []
        presets: list[Preset] = []
        for item in data:
            try:
                presets.append(
                    Preset(name=item["name"], query=deserialize(item["query"]))
                )
            except (KeyError, TypeError) as e:
                logger.warning(
                    "Skipping malformed preset in %s: %s", self.presets_path, e
                )
        return presets

    def save(self, user_presets: list[Preset]) -> None:
        """Persist user presets atomically (built-ins are never written)."""
        data: list[dict[str, Any]] = [
            {"name": p.name, "query": p.query.to_dict()} for p in user_presets
        ]
        _atomic_write_json(self.presets_path, data)

    def add(self, name: str, query: Predicate) -> None:
        """Create or replace a user preset."""
        user = [p for p in self.user_presets if p.name != name]
        user.append(Preset(name=name, query=query))
        self.save(user)

    def edit(self, name: str, query: Predicate) -> None:
        """Replace an existing user preset (no-op if it does not exist)."""
        if not any(p.name == name for p in self.user_presets):
            return
        user = [p for p in self.user_presets if p.name != name]
        user.append(Preset(name=name, query=query))
        self.save(user)

    def remove(self, name: str) -> None:
        """Remove a user preset (built-ins cannot be removed)."""
        user = [p for p in self.user_presets if p.name != name]
        self.save(user)


# ---- Current query (EDMC config) -------------------------------------------


def save_current_query(query: Predicate | None) -> None:
    """Persist the active builder query to EDMC config as a JSON string.

    ``None`` means an empty edit field: the key is removed entirely rather than
    stored, so a cleared query does not linger in config.
    """
    from config import config

    if query is None:
        config.delete(CURRENT_QUERY_KEY)
        return

    config.set(CURRENT_QUERY_KEY, json.dumps(query.to_dict(), ensure_ascii=False))


def load_current_query() -> Predicate | None:
    """Load the active builder query from config, or ``None`` if unset."""
    from config import config

    raw = config.get_str(CURRENT_QUERY_KEY)
    if not raw:
        return None
    try:
        return deserialize(json.loads(raw))
    except (json.JSONDecodeError, KeyError, TypeError) as e:
        logger.warning("Could not load current query: %s", e)
        return None
