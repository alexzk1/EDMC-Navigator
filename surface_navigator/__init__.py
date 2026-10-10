"""Re-export the plugin entry points and helpers defined in :mod:`load`.

The main EDMC application calls these names from ``load``; this package keeps
them reachable as ``surface_navigator.<name>`` so existing import paths are
preserved.
"""

from .load import (
    SurfaceNavigatorPlugin,
    dashboard_entry,
    journal_entry,
    logger,
    plugin_app,
    plugin_start3,
    shutdown,
)

__all__ = [
    "SurfaceNavigatorPlugin",
    "dashboard_entry",
    "journal_entry",
    "logger",
    "plugin_app",
    "plugin_start3",
    "shutdown",
]
