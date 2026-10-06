#!/usr/bin/env python3
"""One-time migrator: old single-table schema -> new two-table schema.

Converts surface_navigator.db from:
    surface_spots ( ..., star_system TEXT, ... )
to:
    star_systems ( star_id, star_name, x, y, z, systemid )
    surface_spots ( ..., star_id INTEGER REFERENCES star_systems(star_id), ... )

Run ONCE against the production DB. It:
  * backs up the DB to /tmp before touching anything,
  * aborts if the table already has a star_id column (already migrated),
  * preserves original row ids,
  * resolves each star_system name to a star_id,
  * verifies the result through DatabaseManager.get_all_spots().

This is a throwaway script (kept in /tmp); it is not part of the project.
"""

import datetime
import os
import shutil
import sqlite3
import sys
import pathlib
import types

REPO = "/home/alex/Games/EliteTools/EDMC-Navigator"
DEFAULT_DB = os.path.join(
    REPO, "surface_navigator", "surface_navigator.db"
)


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
    backup = f"/tmp/surface_navigator.db.migrate-backup-{ts}.db"
    shutil.copy(db_path, backup)
    print(f"Backup written to {backup}")

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    cols = [r[1] for r in conn.execute("PRAGMA table_info(surface_spots)")]
    if "star_id" in cols:
        conn.close()
        abort("surface_spots already has star_id -> already migrated. Aborting.")
    if "star_system" not in cols:
        conn.close()
        abort("Unexpected schema (no star_system column). Aborting.")

    legacy_rows = conn.execute(
        "SELECT id, star_system, body_name, latitude, longitude, spot_number, "
        "mineral_type, mineral_original, amount, density, max_miners, "
        "last_visit_time, notes FROM surface_spots ORDER BY id"
    ).fetchall()
    print(f"Found {len(legacy_rows)} legacy row(s) to migrate.")

    # 2) Rename the old table so the new one can take the surface_spots name.
    conn.execute("ALTER TABLE surface_spots RENAME TO surface_spots_legacy")
    conn.commit()

    # 3) Create the new schema exactly as the app expects it.
    db = DatabaseManager(db_path)

    # 4) Migrate rows: resolve star names -> star_id, preserve ids.
    by_name: dict[str, int] = {}
    for row in legacy_rows:
        name = row["star_system"]
        if name not in by_name:
            star_id = conn.execute(
                "INSERT INTO star_systems (star_name) VALUES (?)", (name,)
            ).lastrowid
            by_name[name] = star_id

        conn.execute(
            """
            INSERT INTO surface_spots (
                id, star_id, body_name, latitude, longitude, spot_number,
                mineral_type, mineral_original, amount, density, max_miners,
                last_visit_time, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["id"],
                by_name[name],
                row["body_name"],
                row["latitude"],
                row["longitude"],
                row["spot_number"],
                row["mineral_type"],
                row["mineral_original"],
                row["amount"],
                row["density"],
                row["max_miners"],
                row["last_visit_time"],
                row["notes"],
            ),
        )
    conn.commit()
    print(f"Migrated {len(legacy_rows)} row(s) into new surface_spots.")

    # 5) Drop the legacy table and clean any orphaned sequence entry.
    conn.execute("DROP TABLE surface_spots_legacy")
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'surface_spots_legacy'")
    max_id = conn.execute("SELECT MAX(id) FROM surface_spots").fetchone()[0]
    # Keep autoincrement consistent with the preserved ids.
    conn.execute("DELETE FROM sqlite_sequence WHERE name = 'surface_spots'")
    conn.execute(
        "INSERT INTO sqlite_sequence (name, seq) VALUES ('surface_spots', ?)",
        (max_id,),
    )
    conn.commit()
    conn.close()

    # 6) Verify through the app's own reader.
    check = DatabaseManager(db_path)
    spots = check.get_all_spots()
    print(f"Verified: {len(spots)} spot(s) readable via get_all_spots().")
    for s in spots:
        print(f"  id={s.id} star_id=<resolved> star_system={s.star_system!r} "
              f"body={s.body_name!r}")

    star_count = sqlite3.connect(db_path).execute(
        "SELECT COUNT(*) FROM star_systems"
    ).fetchone()[0]
    print(f"star_systems table: {star_count} row(s).")
    print("MIGRATION COMPLETE")


if __name__ == "__main__":
    main()
