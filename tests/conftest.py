"""Shared test fixtures (tests/).

The ``db`` / ``db_path`` fixtures used across the DB test suite live here so
every test module can rely on them without each file re-declaring them. Each
test DB is created in ``/tmp`` and removed afterwards, so the repo stays clean.
"""

import os
import tempfile
from collections.abc import Iterator

import pytest

from surface_navigator.database import DatabaseManager


@pytest.fixture()
def db_path() -> Iterator[str]:
    """A fresh empty DB path in /tmp, removed after the test."""
    fd, path = tempfile.mkstemp(
        prefix="edmc_surface_navigator_", suffix=".db", dir="/tmp"
    )
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture()
def db(db_path: str) -> DatabaseManager:
    return DatabaseManager(db_path)
