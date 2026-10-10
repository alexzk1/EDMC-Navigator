"""Root conftest: make the repo importable and stub EDMC-only modules.

``surface_navigator``'s package ``__init__`` imports the GUI chain, which needs
``config`` (provided by EDMC at runtime, not present in a standalone test run).
This conftest runs before any test module is imported, so we (1) put the repo
root on ``sys.path``, (2) install a minimal ``config`` stand-in, and (3) give it
a real (if tiny) app-data dir with a ``commodity.csv`` so ``Commodities`` can
resolve names through its real path -- no need to stub ``resolve_db_value``.
"""

import atexit
import pathlib
import shutil
import sys
import tempfile
from types import ModuleType
from typing import Any

REPO_ROOT = pathlib.Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


def _make_app_dir() -> pathlib.Path:
    """A temp app-data dir containing a minimal ``FDevIDs/commodity.csv``.

    ``Commodities.load_commodity_map`` requires that file to exist (and hold at
    least five rows) before it will resolve anything. A handful of common
    metals plus tritium is enough for the tests to exercise the real resolution
    path. The dir is removed on interpreter exit.
    """
    app_dir = pathlib.Path(
        tempfile.mkdtemp(prefix="edmc_surface_navigator_test_")
    )
    fdevids = app_dir / "FDevIDs"
    fdevids.mkdir(parents=True, exist_ok=True)
    (fdevids / "commodity.csv").write_text(
        "id,symbol,category,name\n"
        "128049152,Platinum,Metals,Platinum\n"
        "128049153,Palladium,Metals,Palladium\n"
        "128049154,Gold,Metals,Gold\n"
        "128049155,Silver,Metals,Silver\n"
        "128049156,Tritium,Resources,Tritium\n",
        encoding="utf-8",
    )
    atexit.register(lambda: shutil.rmtree(app_dir, ignore_errors=True))
    return app_dir


_APP_DIR_PATH = _make_app_dir()


class _Config:
    app_dir_path = _APP_DIR_PATH
    # In-memory settings so ``set``/``get_str`` work for real (no EDMC config).
    settings: dict[str, str] = {}

    def get_str(self, key: str, default: str = "") -> str:
        return self.settings.get(key.lower(), default)

    def set(self, key: str, value: Any) -> None:
        self.settings[key.lower()] = str(value)

    def delete(self, key: str, *, suppress: bool = False) -> None:
        self.settings.pop(key.lower(), None)

    def __getattr__(self, name):
        # Permissive fallback for anything the GUI may read at import time.
        return None


if "config" not in sys.modules:
    module = ModuleType("config")
    module.config = _Config()
    sys.modules["config"] = module
