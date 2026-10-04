import sqlite3

from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .models import SurfaceSpot
from .player_location import PlayerLocation


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS surface_spots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    star_system TEXT NOT NULL,
                    body_name TEXT NOT NULL,
                    latitude REAL NOT NULL,
                    longitude REAL NOT NULL,
                    spot_number INTEGER,
                    mineral_type TEXT,
                    amount REAL,
                    density REAL,
                    max_miners INTEGER DEFAULT 1,
                    last_visit_time TIMESTAMP,
                    notes TEXT
                )
            """)

    def add_spot(self, spot: SurfaceSpot) -> bool:
        try:
            success: bool = False
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO surface_spots (
                        star_system, body_name, latitude, longitude, 
                        spot_number, mineral_type, amount, density, max_miners, last_visit_time, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        spot.star_system,
                        spot.body_name,
                        spot.latitude,
                        spot.longitude,
                        spot.spot_number,
                        spot.mineral_type,
                        spot.amount,
                        spot.density,
                        spot.max_miners,
                        spot.last_visit_time,
                        spot.notes,
                    ),
                )
                success = cursor.lastrowid is not None

            # Let the transaction to finish!
            if success:
                dispatcher.dispatch(KnownEvents.DATA_BASE_MODIFIED, EventParams())
            return success
        except sqlite3.Error as e:
            print(f"Database error during add_spot: {e}")
        return False

    @staticmethod
    def _fetch_select_cursor(cursor: sqlite3.Cursor) -> list[SurfaceSpot]:
        """Does actual fetch from the cursor and validates datetime."""
        spots: list[SurfaceSpot] = []
        for row in cursor:
            data = dict(row)
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
                except (ValueError, TypeError):
                    pass
            spots.append(SurfaceSpot(**data))
        return spots

    def get_all_spots(self) -> list[SurfaceSpot]:
        """Fetches ALL records from DB. Warning! It can explode things."""
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            return DatabaseManager._fetch_select_cursor(
                conn.execute("SELECT * FROM surface_spots")
            )

    def get_planetary_spots(self, location: PlayerLocation | None) -> list[SurfaceSpot]:
        """Fetches records for the current planet if any."""
        if location is None or not location.body_name:
            return []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            return DatabaseManager._fetch_select_cursor(
                conn.execute(
                    "SELECT * FROM surface_spots WHERE star_system = ? AND body_name = ?",
                    (location.star_system, location.body_name),
                )
            )

    def update_spot(self, spot_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        keys = [f"{k} = ?" for k in kwargs.keys()]
        values = list(kwargs.values())
        sql = f"UPDATE surface_spots SET {', '.join(keys)} WHERE id = ?"
        values.append(spot_id)

        try:
            with self._get_connection() as conn:
                conn.execute(sql, values)

            # Let the transaction to finish!
            dispatcher.dispatch(KnownEvents.DATA_BASE_MODIFIED, EventParams())
            return True
        except sqlite3.Error as e:
            print(f"Database error during update_spot: {e}")
            return False

    def delete_spot(self, spot_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM surface_spots WHERE id = ?", (spot_id,))

            # Let the transaction to finish!
            dispatcher.dispatch(KnownEvents.DATA_BASE_MODIFIED, EventParams())
            return True
        except sqlite3.Error as e:
            print(f"Database error during delete_spot: {e}")
            return False

    def find_closest_by_mineral(self, mineral_type: str) -> list[SurfaceSpot]:
        spots = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM surface_spots WHERE mineral_type LIKE ?",
                (f"%{mineral_type}%",),
            )
            for row in cursor:
                data = dict(row)
                if data["last_visit_time"]:
                    import datetime

                    try:
                        if isinstance(data["last_visit_time"], str):
                            data["last_visit_time"] = datetime.datetime.fromisoformat(
                                data["last_visit_time"]
                            )
                    except (ValueError, TypeError):
                        pass
                spots.append(SurfaceSpot(**data))
        return spots

    def update_visit_time(
        self, star_system: str, body_name: str, lat: float, lon: float
    ):
        import datetime

        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE surface_spots 
                SET last_visit_time = ? 
                WHERE star_system = ? AND body_name = ? AND latitude BETWEEN ? - 0.01 AND ? + 0.01 
                  AND longitude BETWEEN ? - 0.01 AND ? + 0.01
            """,
                (datetime.datetime.now(), star_system, body_name, lat, lat, lon),
            )
        # Let the transaction to finish!
        dispatcher.dispatch(KnownEvents.DATA_BASE_MODIFIED, EventParams())
