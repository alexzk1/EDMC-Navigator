"""Versioned schema migrations for the surface navigator DB.

The on-disk schema is tracked by SQLite's ``PRAGMA user_version``. Each entry in
``MIGRATIONS`` targets exactly one version number and is applied, in order, the
first time the app opens a database whose stored version is lower. Future schema
changes are just more tuples appended to ``MIGRATIONS`` -- the runner chains
them from the stored version, so nothing here has to reason about where a given
user's database sits.

A migration is a pure function of a connection: it reads/writes rows and leaves
the tables in the *next* version's shape. ``run_migrations`` runs every pending
migration inside a single transaction and only advances ``user_version`` once
that migration has committed, so a half-run migration rolls back to the exact
state it started in rather than leaving a corrupt database.
"""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Callable, Sequence

logger = logging.getLogger("SurfaceNavigator")

Migration = Callable[[sqlite3.Connection], None]


# ---- schema definition (single source of truth) --------------------------
# The v1 column lists. ``COLLATE NOCASE`` is what makes ``=`` matching on these
# columns ignore case -- the fix for case-variant system/body names that used to
# slip duplicate rows through the online search. ``LIKE`` is already ASCII
# case-insensitive in a stock SQLite build, so the mineral searches need no
# extra work; the collation here only keeps the mineral columns consistent with
# the rest.
_STAR_SYSTEMS_COLS = """
    star_id INTEGER PRIMARY KEY AUTOINCREMENT,
    star_name TEXT NOT NULL UNIQUE COLLATE NOCASE,
    x REAL,
    y REAL,
    z REAL,
    systemid INTEGER
"""

_SURFACE_SPOTS_COLS = """
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    star_id INTEGER NOT NULL
        REFERENCES star_systems(star_id)
        ON DELETE CASCADE,
    body_name TEXT NOT NULL COLLATE NOCASE,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    spot_number INTEGER,
    mineral_type TEXT COLLATE NOCASE,
    mineral_original TEXT COLLATE NOCASE,
    amount REAL,
    density REAL,
    max_miners INTEGER DEFAULT 1,
    last_visit_time TIMESTAMP,
    notes TEXT COLLATE NOCASE,
    flags INTEGER NOT NULL DEFAULT 0
"""

_INDEXES: Sequence[str] = (
    (
        "CREATE INDEX IF NOT EXISTS idx_spots_location "
        "ON surface_spots (star_id, body_name)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_spots_coords "
        "ON surface_spots (latitude, longitude)"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_incomplete_mining_spots "
        "ON surface_spots (latitude, longitude) "
        "WHERE mineral_type IS NULL AND mineral_original IS NULL"
    ),
    (
        "CREATE INDEX IF NOT EXISTS idx_incomplete_mining_spots_system "
        "ON surface_spots (star_id, body_name, latitude, longitude) "
        "WHERE mineral_type IS NULL AND mineral_original IS NULL"
    ),
)


def _create_table(conn: sqlite3.Connection, cols: str, table: str) -> None:
    """Creates ``table`` from a column-list fragment (so DDL is not duplicated)."""
    conn.execute("CREATE TABLE " + table + " (" + cols + ")")


def _create_v1_schema(conn: sqlite3.Connection) -> None:
    """Creates a fresh v1 database (the path a brand-new install takes)."""
    _create_table(conn, _STAR_SYSTEMS_COLS, "star_systems")
    _create_table(conn, _SURFACE_SPOTS_COLS, "surface_spots")
    for ddl in _INDEXES:
        conn.execute(ddl)


def _merge_case_insensitive_star_dupes(conn: sqlite3.Connection) -> None:
    """Folds case-variant star names into one row before the table rebuild.

    A pre-v1 database can hold the same system twice, differing only in case --
    that drift is exactly what let the online search slip a duplicate through.
    The new ``UNIQUE COLLATE NOCASE`` constraint would reject the copy on
    rebuild, so collapse the losers into the lowest-id survivor first. Any spot
    that referenced a loser is repointed to the survivor, so no mark is orphaned
    (this is the "second table points at a failed star" case).
    """
    dupes = conn.execute(
        "SELECT min(star_id) survivor, group_concat(star_id) losers "
        "FROM star_systems GROUP BY lower(star_name) HAVING count(*) > 1"
    ).fetchall()
    for survivor, losers_csv in dupes:
        for loser in (
            int(raw) for raw in losers_csv.split(",") if int(raw) != survivor
        ):
            conn.execute(
                "UPDATE surface_spots SET star_id = ? WHERE star_id = ?",
                (survivor, loser),
            )
            conn.execute("DELETE FROM star_systems WHERE star_id = ?", (loser,))


def _v1_add_case_insensitive_collation(conn: sqlite3.Connection) -> None:
    """Adds ``COLLATE NOCASE`` to every searchable text column.

    Fresh installs get the schema straight. Existing installs are rebuilt: the
    tables are recreated with the collations and data copied row-for-row,
    preserving every primary key so the ``surface_spots`` foreign keys keep
    resolving. Case-variant star dupes are merged first so the new ``UNIQUE``
    constraint holds.
    """
    existing = {
        r[0]
        for r in conn.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type = 'table' "
            "AND name IN ('star_systems', 'surface_spots')"
        )
    }
    if not existing:
        _create_v1_schema(conn)
        return

    _merge_case_insensitive_star_dupes(conn)
    _create_table(conn, _STAR_SYSTEMS_COLS, "star_systems_new")
    _create_table(conn, _SURFACE_SPOTS_COLS, "surface_spots_new")
    conn.execute("INSERT INTO star_systems_new SELECT * FROM star_systems")
    conn.execute("INSERT INTO surface_spots_new SELECT * FROM surface_spots")
    conn.execute("DROP TABLE star_systems")
    conn.execute("DROP TABLE surface_spots")
    conn.execute("ALTER TABLE star_systems_new RENAME TO star_systems")
    conn.execute("ALTER TABLE surface_spots_new RENAME TO surface_spots")
    for ddl in _INDEXES:
        conn.execute(ddl)


# Append any future migrators to here.
MIGRATIONS: list[tuple[int, str, Migration]] = [
    (
        1,
        "Add COLLATE NOCASE to searchable text columns",
        _v1_add_case_insensitive_collation,
    ),
    # (2, "Short description of the next schema change", _migrate_v2),
]


def run_migrations(db_path: str) -> None:
    """Applies every pending schema migration to ``db_path``, in version order.

    Reads ``PRAGMA user_version``; each ``MIGRATIONS`` entry whose target is
    higher than the stored version runs in turn, and the version advances only
    after that migration commits. Everything shares one transaction, so a
    failing migration leaves the database exactly as it started. Foreign keys
    are disabled for the rebuild (tables are recreated and renamed), then
    re-enabled on the next connection.

    The connection runs in autocommit mode and the transaction is opened with an
    explicit ``BEGIN``: Python's default driver mode auto-commits DDL
    (CREATE/DROP/ALTER), which would let a half-run migration survive a
    ``ROLLBACK``. In autocommit mode the explicit transaction is the only thing
    in effect, so SQLite's own DDL transactionality applies and the whole
    migration -- schema and ``user_version`` together -- rolls back as one.
    """
    conn = sqlite3.connect(db_path, isolation_level=None)
    try:
        # Must run outside a transaction to take effect.
        conn.execute("PRAGMA foreign_keys = OFF")
        conn.execute("BEGIN")
        try:
            current = conn.execute("PRAGMA user_version").fetchone()[0] or 0
            for target, description, fn in MIGRATIONS:
                if target > current:
                    logger.info("Applying schema migration %d: %s", target, description)
                    fn(conn)
                    conn.execute("PRAGMA user_version = " + str(target))
            conn.execute("COMMIT")
        except sqlite3.Error:
            # A hard error (IO/busy) may have already ended the transaction;
            # ignore a failing ROLLBACK so it does not mask the original cause.
            try:
                conn.execute("ROLLBACK")
            except sqlite3.Error:
                pass
            raise
    except sqlite3.Error as e:
        logger.error("Schema migration failed: %s", e)
        raise
    finally:
        conn.close()
