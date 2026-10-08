import logging
import math
import sqlite3
from typing import Any

from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .models import RingScanStatus, StarSystem, SurfaceSpot
from .player_location import PlayerLocation, SurfacePoint
from .spot_flags import SurfaceSpotFlags

logger = logging.getLogger("SurfaceNavigator")

# Surface spots live in their own table but reference a normalized
# ``star_systems`` table via ``star_id``. Every read reconstructs the
# (historically flat) ``star_system`` string through this JOIN so the rest of
# the app keeps working with ``SurfaceSpot.star_system`` unchanged.
_SPOTS_SELECT_LIST = "surface_spots.*, star_systems.star_name AS star_system"
_SPOTS_FROM = (
    "FROM surface_spots "
    "JOIN star_systems ON surface_spots.star_id = star_systems.star_id"
)


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
        conn.row_factory = sqlite3.Row

        return conn

    @staticmethod
    def _now_utc() -> str:
        """Returns the current UTC time as an ISO-8601 string, ready to store.

        Callers just use this value directly in an ``INSERT``/``UPDATE`` without
        any extra formatting. It is returned as a plain string (not a
        ``datetime``) so the write path never touches sqlite3's datetime
        adapters, which are deprecated in Python 3.12+. ``fromisoformat`` on the
        read path parses both this ``T``-separated format and the older
        space-separated one, so existing databases need no migration.
        """
        import datetime

        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def _init_db(self):
        with self._get_connection() as conn:
            # Normalized star systems. Names are unique in practice, but a few
            # systems share a name and are only distinguished by ``systemid``;
            # hence there is no UNIQUE constraint. ``systemid`` and x/y/z are
            # optional because they may arrive later via streaming updates.
            conn.execute("""
                CREATE TABLE IF NOT EXISTS star_systems (
                    star_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    star_name TEXT NOT NULL UNIQUE,
                    x REAL,
                    y REAL,
                    z REAL,
                    systemid INTEGER
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS surface_spots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    star_id INTEGER NOT NULL
                        REFERENCES star_systems(star_id)
                        ON DELETE CASCADE,
                    body_name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    spot_number INTEGER,
                    mineral_type TEXT,
                    mineral_original TEXT,
                    amount REAL,
                    density REAL,
                    max_miners INTEGER DEFAULT 1,
                    last_visit_time TIMESTAMP,
                    notes TEXT,
                    flags INTEGER NOT NULL DEFAULT 0
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spots_location ON surface_spots (star_id, body_name)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spots_coords ON surface_spots (latitude, longitude)"
            )
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_incomplete_mining_spots 
                ON surface_spots (latitude, longitude) 
                WHERE mineral_type IS NULL AND mineral_original IS NULL
            """)
            conn.execute("""
               CREATE INDEX IF NOT EXISTS idx_incomplete_mining_spots_system  
               ON surface_spots (star_id, body_name, latitude, longitude)  
               WHERE mineral_type IS NULL AND mineral_original IS NULL;
            """)

    def _get_or_create_star(
        self, star_name: str | StarSystem, systemid: int | None = None
    ) -> int:
        """Returns the star_id for ``star_name``, creating the row if needed.

        Star names are unique, so a single lookup by name is enough. When a
        ``StarSystem`` (or a plain ``systemid``) is known but the existing row
        still holds NULLs for ``systemid``/coordinates, those values are
        attached to that row instead of creating a duplicate.

        Fields are populated lazily: a value is only written into an existing
        row when that row's column is still NULL. Existing values are never
        overwritten, so partial updates that arrive at different times compose
        cleanly.
        """
        if isinstance(star_name, StarSystem):
            name = star_name.star_name
            systemid = systemid if systemid is not None else star_name.systemid
            x, y, z = star_name.x, star_name.y, star_name.z
        else:
            name = star_name
            x = y = z = None

        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT star_id, systemid, x, y, z FROM star_systems "
                "WHERE star_name = ?",
                (name,),
            )
            row = cur.fetchone()
            if row is not None:
                existing_id, existing_sid, ex_x, ex_y, ex_z = row
                updates: dict[str, object] = {}
                if systemid is not None and existing_sid is None:
                    updates["systemid"] = systemid
                if x is not None and ex_x is None:
                    updates["x"] = x
                if y is not None and ex_y is None:
                    updates["y"] = y
                if z is not None and ex_z is None:
                    updates["z"] = z
                if updates:
                    set_clause = ", ".join(f"{col} = ?" for col in updates)
                    conn.execute(
                        f"UPDATE star_systems SET {set_clause} WHERE star_id = ?",
                        (*updates.values(), existing_id),
                    )
                return existing_id

            cur = conn.execute(
                "INSERT INTO star_systems (star_name, systemid, x, y, z) "
                "VALUES (?, ?, ?, ?, ?)",
                (name, systemid, x, y, z),
            )
            star_id = cur.lastrowid
            assert star_id is not None  # a successful INSERT always sets lastrowid
            return star_id

    def ensure_star_exists(self, system: StarSystem) -> int:
        system.star_id = self._get_or_create_star(system)
        return system.star_id

    def update_existing_star_coords(self, system: StarSystem) -> int:
        """Updates x/y/z for an existing star row that still holds NULLs.

        Never creates a row - only fills in coordinates for a system already in
        the table (a repeat visit). Coordinates that are still ``None`` on
        ``system`` are skipped, so partial updates compose cleanly. Returns how
        many columns were updated (0-3); a system not in the table is left
        untouched.
        """
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT star_id, x, y, z FROM star_systems WHERE star_name = ?",
                (system.star_name,),
            )
            row = cur.fetchone()
            if row is None:
                return 0
            existing_id, ex_x, ex_y, ex_z = row
            updates: dict[str, float] = {}
            if system.x is not None and ex_x is None:
                updates["x"] = system.x
            if system.y is not None and ex_y is None:
                updates["y"] = system.y
            if system.z is not None and ex_z is None:
                updates["z"] = system.z
            if not updates:
                return 0
            set_clause = ", ".join(f"{col} = ?" for col in updates)
            conn.execute(
                f"UPDATE star_systems SET {set_clause} WHERE star_id = ?",
                (*updates.values(), existing_id),
            )
            return len(updates)

    def find_incomplete_surface_mining_spot(
        self,
        star: str | StarSystem,
        body: str,
        center: SurfacePoint,
        radius_meters: float,
        planet_radius_meters: float,
    ) -> SurfaceSpot | None:
        """
        Finds single mining spot around the center in radius which does not have mined mineral set in DB.
        Radius must be small enough to assume surface is flat.
        """
        if isinstance(star, StarSystem):
            star_name_to_use = star.star_name
        else:
            star_name_to_use = star
        if not star_name_to_use or not body:
            return None

        lat_rad = math.radians(center.latitude)
        cos_lat = math.cos(lat_rad)
        cos_lat_sq = cos_lat * cos_lat
        deg_ratio = (radius_meters / planet_radius_meters) * (180 / math.pi)
        deg_radius_sq = deg_ratio**2

        sql = f"""  
            SELECT {_SPOTS_SELECT_LIST} {_SPOTS_FROM}
            WHERE mineral_type IS NULL  
                AND mineral_original IS NULL  
                AND star_systems.star_name = ? AND body_name = ?
                AND (      
                    (latitude - ?) * (latitude - ?) +   
                    (longitude - ?) * (longitude - ?) * ?
                ) < ?      
                ORDER BY (      
                    (latitude - ?) * (latitude - ?) +    
                    (longitude - ?) * (longitude - ?) * ?    
                ) ASC  
            LIMIT 1
        """
        params = (
            star_name_to_use,
            body,
            center.latitude,  # WHERE lat1
            center.latitude,  # WHERE lat2
            center.longitude,  # WHERE lon1
            center.longitude,  # WHERE lon2
            cos_lat_sq,  # WHERE cos_sq
            deg_radius_sq,  # WHERE R^2
            center.latitude,  # ORDER BY lat1
            center.latitude,  # ORDER BY lat2
            center.longitude,  # ORDER BY lon1
            center.longitude,  # ORDER BY lon2
            cos_lat_sq,  # ORDER BY cos_sq
        )
        with self._get_connection() as conn:
            cursor = conn.execute(sql, params)
            spots = self._fetch_select_cursor(cursor)
            if len(spots) < 1:
                return None
            return spots[0]

    def update_visit_time(
        self,
        star: str | StarSystem,
        body: str,
        center: SurfacePoint,
        radius_meters: float,
        planet_radius_meters: float,
    ):
        if isinstance(star, StarSystem):
            star_name_to_use = star.star_name
        else:
            star_name_to_use = star
        if not star_name_to_use or not body:
            return

        lat_rad = math.radians(center.latitude)
        cos_lat = math.cos(lat_rad)
        cos_lat_sq = cos_lat * cos_lat

        deg_ratio = (radius_meters / planet_radius_meters) * (180 / math.pi)
        deg_radius_sq = deg_ratio**2

        sql = f"""    
            SELECT surface_spots.id 
            {_SPOTS_FROM}
            WHERE star_systems.star_name = ? AND body_name = ?      
                      AND (      
                          (latitude - ?) * (latitude - ?) +   
                          (longitude - ?) * (longitude - ?) * ?
                      ) < ?      
            ORDER BY (      
                (latitude - ?) * (latitude - ?) +    
                (longitude - ?) * (longitude - ?) * ?    
            ) ASC      
            LIMIT 1    
        """

        params = (
            star_name_to_use,  # WHERE star_systems.star_name
            body,  # WHERE body_name
            center.latitude,  # WHERE lat1
            center.latitude,  # WHERE lat2
            center.longitude,  # WHERE lon1
            center.longitude,  # WHERE lon2
            cos_lat_sq,  # WHERE cos_sq
            deg_radius_sq,  # WHERE R^2
            center.latitude,  # ORDER BY lat1
            center.latitude,  # ORDER BY lat2
            center.longitude,  # ORDER BY lon1
            center.longitude,  # ORDER BY lon2
            cos_lat_sq,  # ORDER BY cos_sq
        )

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(sql, params)
                row = cursor.fetchone()
                if row:
                    target_id = row[0]
                    # Step 2: Update that specific ID
                    conn.execute(
                        "UPDATE surface_spots SET last_visit_time = ? WHERE id = ?",
                        (DatabaseManager._now_utc(), target_id),
                    )

            # Let the transaction to finish!
            dispatcher.dispatch(KnownEvents.DATABASE_MODIFIED, EventParams())
        except sqlite3.Error as e:
            logger.error(f"Database error during update_visit_time: {e}")

    def add_spot(self, spot: SurfaceSpot) -> bool:
        try:
            success: bool = False
            with self._get_connection() as conn:
                star_id = self._get_or_create_star(spot.star_system)
                cursor = conn.execute(
                    """
                    INSERT INTO surface_spots (
                        star_id, body_name, latitude, longitude, 
                        spot_number, mineral_type, mineral_original, amount, density, max_miners, last_visit_time, notes, flags
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        star_id,
                        spot.body_name,
                        spot.latitude,
                        spot.longitude,
                        spot.spot_number,
                        spot.mineral_type,
                        spot.mineral_original,
                        spot.amount,
                        spot.density,
                        spot.max_miners,
                        DatabaseManager._now_utc(),
                        spot.notes,
                        spot.flags.value,
                    ),
                )
                success = cursor.lastrowid is not None

            # Let the transaction to finish!
            if success:
                dispatcher.dispatch(
                    KnownEvents.DATABASE_MODIFIED,
                    EventParams(
                        params={
                            "new_record": True,
                            "latitude": spot.latitude,
                            "longitude": spot.longitude,
                        }
                    ),
                )
            return success
        except sqlite3.Error as e:
            logger.error(f"Database error during add_spot: {e}")
        return False

    def ensure_tritium_recorded(self, status: RingScanStatus) -> bool:
        """Ensures the ring is recorded as a tritium (He3 fuel) ring.

        A signal counts as tritium when either its fuzzy-matched name or its
        lowercased original log name equals "tritium" (the fuzzy matcher is a
        convenience, so a raw log name still matches when the matcher did not
        resolve it). Rings are globally unique, so this is idempotent: a second
        scan of the same ring (same star + body) is a no-op and never
        overwrites the first record.

        Returns True when the ring is a tritium ring - whether it was just
        recorded or was already known - and False when the signal is not
        tritium. Callers can treat True as "this ring is fuel, stop looking".
        """
        if (
            status.fuzzy_matched_name or status.name_from_log.strip().lower()
        ) != "tritium":
            return False

        star_id = self._get_or_create_star(status.system)
        with self._get_connection() as conn:
            cur = conn.execute(
                "SELECT 1 FROM surface_spots WHERE star_id = ? AND body_name = ?",
                (star_id, status.body),
            )
            if cur.fetchone() is not None:
                # Already recorded this ring - leave the original untouched.
                return True

        spot = SurfaceSpot(
            star_system=status.system,
            body_name=status.body,
            latitude=0.0,
            longitude=0.0,
            mineral_type=status.fuzzy_matched_name,
            mineral_original=status.name_from_log,
            flags=SurfaceSpotFlags.TRITIUM_RING_PRESENT,
        )
        return self.add_spot(spot)

    @staticmethod
    def _fetch_select_cursor(cursor: sqlite3.Cursor) -> list[SurfaceSpot]:
        """Does actual fetch from the cursor and validates datetime."""
        spots: list[SurfaceSpot] = []
        for row in cursor:
            data = dict(row)
            # surface_spots.star_id is an internal FK; the star name is
            # reconstructed by the JOIN in every query. SurfaceSpot keeps its
            # historical star_system field.
            data.pop("star_id", None)
            # SQLite might return timestamp as string or datetime depending on driver/version
            if data["last_visit_time"] and not (
                data["last_visit_time"] is None
            ):  # Simple check
                import datetime

                try:
                    # If it is a string, convert it.
                    if isinstance(data["last_visit_time"], str):
                        data["last_visit_time"] = datetime.datetime.fromisoformat(
                            data["last_visit_time"]
                        )
                except (ValueError, TypeError) as e:
                    logger.error(f"Database error during _fetch_select_cursor: {e}")
            spots.append(SurfaceSpot(**data))
        return spots

    def get_all_spots(self) -> list[SurfaceSpot]:
        """Fetches ALL records from DB. Warning! It can explode things."""
        with self._get_connection() as conn:
            return DatabaseManager._fetch_select_cursor(
                conn.execute(f"SELECT {_SPOTS_SELECT_LIST} {_SPOTS_FROM}")
            )

    def get_planetary_spots(self, location: PlayerLocation | None) -> list[SurfaceSpot]:
        """Fetches records for the current planet if any."""
        if location is None or not location.body_name:
            return []
        with self._get_connection() as conn:
            return DatabaseManager._fetch_select_cursor(
                conn.execute(
                    f"SELECT {_SPOTS_SELECT_LIST} {_SPOTS_FROM} WHERE star_systems.star_name = ? AND body_name = ?",
                    (location.star_system.star_name, location.body_name),
                )
            )

    def get_system_spots(self, system: str | StarSystem | None) -> list[SurfaceSpot]:
        """Fetches records for the current planet if any."""
        if system is None:
            return []
        star = system if isinstance(system, str) else system.star_name
        if not star:
            return []
        with self._get_connection() as conn:
            return DatabaseManager._fetch_select_cursor(
                conn.execute(
                    f"SELECT {_SPOTS_SELECT_LIST} {_SPOTS_FROM} WHERE star_systems.star_name = ?",
                    (star,),
                )
            )

    def update_spot(self, spot_id: int, **kwargs: Any) -> bool:
        if not kwargs:
            return False
        keys = [f"{k} = ?" for k in kwargs]
        values = list(kwargs.values())
        sql = f"UPDATE surface_spots SET {', '.join(keys)} WHERE id = ?"
        values.append(spot_id)

        try:
            with self._get_connection() as conn:
                conn.execute(sql, values)

            # Let the transaction to finish!
            dispatcher.dispatch(KnownEvents.DATABASE_MODIFIED, EventParams())
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error during update_spot: {e}")
            return False

    def delete_spot(self, spot_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM surface_spots WHERE id = ?", (spot_id,))

            # Let the transaction to finish!
            dispatcher.dispatch(KnownEvents.DATABASE_MODIFIED, EventParams())
            return True
        except sqlite3.Error as e:
            logger.error(f"Database error during delete_spot: {e}")
            return False

    def gc_temporaries(self, age_secs: int) -> int:
        """Removes temporary marks older than ``age_secs`` seconds.

        A spot is "temporary" when the ``IS_TEMPORARY_MARK`` bit is set in its
        ``flags``. Age is measured from ``last_visit_time`` against now (UTC).
        Rows with a NULL ``last_visit_time`` are kept -- their age is unknown.

        Returns the number of deleted rows.
        """
        import datetime

        cutoff = (
            datetime.datetime.now(datetime.timezone.utc)
            - datetime.timedelta(seconds=age_secs)
        ).strftime("%Y-%m-%d %H:%M:%S")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    DELETE FROM surface_spots
                    WHERE (flags & ?) != 0
                      AND last_visit_time IS NOT NULL
                      AND datetime(last_visit_time) < ?
                    """,
                    (SurfaceSpotFlags.IS_TEMPORARY_MARK.value, cutoff),
                )
                deleted = cursor.rowcount

            # Let the transaction to finish!
            dispatcher.dispatch(
                KnownEvents.DATABASE_MODIFIED,
                EventParams(params={"deleted": deleted}),
            )
            return deleted
        except sqlite3.Error as e:
            logger.error(f"Database error during gc_temporaries: {e}")
            return 0

    def find_by_mineral(self, mineral_type: str) -> list[SurfaceSpot]:
        """Lists all spots by mineral. Warning! This can be a lot."""
        to_find = f"%{mineral_type}%"
        with self._get_connection() as conn:
            cursor = conn.execute(
                f"SELECT {_SPOTS_SELECT_LIST} {_SPOTS_FROM} WHERE mineral_type LIKE ? OR mineral_original LIKE ?",
                (
                    to_find,
                    to_find,
                ),
            )
            return self._fetch_select_cursor(cursor)
