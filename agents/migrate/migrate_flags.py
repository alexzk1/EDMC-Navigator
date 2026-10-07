#!/usr/bin/env python3
"""One-time migrator: add the per-spot ``flags`` bit-field column.

Adds ``surface_spots.flags`` (INTEGER, NOT NULL DEFAULT 0) to an existing
surface_navigator.db.

New databases already ship with this column through
``DatabaseManager._init_db``; this script only upgrades a DB that was created
before the flag feature shipped (i.e. the one existing DB).

Run ONCE against the production DB. It:
  * backs up the DB to /tmp before touching anything,
  * aborts if the column already exists (already migrated),
  * gives every existing row the default 0 (no flags),
  * verifies the result through DatabaseManager.get_all_spots().

This is a throwaway script (kept under agents/migrate/); it is not part of the
project runtime.
"""

import datetime
import os
import shutil
import sqlite3
import sys
import pathlib
import types

REPO = "/home/alex/Games/EliteTools/EDMC-Navigator"
DEFAULT_DB = os.path.join(REPO, "surface_navigator", "surface_navigator.db")


def _install_config_stub() -> None:
    """The package __init__ pulls in the GUI chain, which needs EDMC's config."""
    if "config" in sys.modules:
        return

    class _Config:
        app_dir_path = pathlib.Path("/tmp")

        def __getattr__(self, name):
            return None

    module = types.ModuleType("config")
    module.config = _Config()
    sys.modules["config"] = module


def abort(msg: str) -> None:
    print("ABORT:", msg)
    sys.exit(1)


def main() -> None:
    _install_config_stub()
    sys.path.insert(0, REPO)

    from surface_navigator.database import DatabaseManager

    db_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_DB
    if not os.path.exists(db_path):
        abort(f"DB not found: {db_path}")

    # 1) Backup before anything changes.
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    backup = f"/tmp/surface_navigator.db.flags-backup-{ts}.db"
    shutil.copy(db_path, backup)
    print(f"Backup written to {backup}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cols = [r[1] for r in conn.execute("PRAGMA table_info(surface_spots)")]
    if "flags" in cols:
        conn.close()
        abort("surface_spots already has flags -> already migrated. Aborting.")
    if "id" not in cols:
        conn.close()
        abort("Unexpected schema (no id column). Aborting.")

    # 2) Add the column. NOT NULL DEFAULT 0 fills every existing row with
    #    "no flags" in one shot -- no per-row update needed.
    conn.execute(
        "ALTER TABLE surface_spots ADD COLUMN flags INTEGER NOT NULL DEFAULT 0"
    )
    conn.commit()
    print("Added column: surface_spots.flags INTEGER NOT NULL DEFAULT 0")

    # 3) Verify every existing row defaulted to 0 and the app reader still works.
    total = conn.execute("SELECT COUNT(*) FROM surface_spots").fetchone()[0]
    zero = conn.execute("SELECT COUNT(*) FROM surface_spots WHERE flags = 0").fetchone()[0]
    print(f"Verified: {zero}/{total} existing row(s) default to no flags (0).")

    check = DatabaseManager(db_path)
    spots = check.get_all_spots()
    print(f"Verified: {len(spots)} spot(s) readable via get_all_spots().")
    for s in spots:
        print(f"  id={s.id} star_system={s.star_system!r} body={s.body_name!r} flags={s.flags.value}")

    print("MIGRATION COMPLETE")


if __name__ == "__main__":
    main()
