"""Root conftest: make the repo importable and stub EDMC-only modules.

``surface_navigator``'s package ``__init__`` imports the GUI chain, which needs
``config`` (provided by EDMC at runtime, not present in a standalone test run).
This conftest runs before any test module is imported, so we (1) put the repo
root on ``sys.path`` and (2) install a minimal ``config`` stand-in.
"""

import pathlib
import sys
from types import ModuleType

REPO_ROOT = pathlib.Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


class _Config:
    app_dir_path = pathlib.Path("/tmp")

    def __getattr__(self, name):
        # Permissive fallback for anything the GUI may read at import time.
        return None


if "config" not in sys.modules:
    module = ModuleType("config")
    module.config = _Config()
    sys.modules["config"] = module
