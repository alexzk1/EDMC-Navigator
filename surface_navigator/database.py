import logging
import math
import sqlite3
from typing import Any

from .events_dispatcher import EventParams, KnownEvents, dispatcher
from .models import SurfaceSpot
from .player_location import PlayerLocation, SurfacePoint

logger = logging.getLogger("SurfaceNavigator")


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    @staticmethod
    def now_utc():
        import datetime

        return datetime.datetime.now(datetime.timezone.utc)

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
                    mineral_original TEXT,
                    amount REAL,
                    density REAL,
                    max_miners INTEGER DEFAULT 1,
                    last_visit_time TIMESTAMP,
                    notes TEXT
                )
            """)
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_spots_location ON surface_spots (star_system, body_name)"
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
               CREATE INDEX IF NOT EXISTS idx_incomplete_mining_spots  
               ON surface_spots (star_system, body_name, latitude, longitude)  
               WHERE mineral_type IS NULL AND mineral_original IS NULL;
            """)

    def find_incomplete_surface_mining_spot(
        self,
        star: str,
        body: str,
        center: SurfacePoint,
        radius_meters: float,
        planet_radius_meters: float,
    ) -> SurfaceSpot | None:
        """
        Finds single mining spot around the center in radius which does not have mined mineral set in DB.
        Radius must be small enough to assume surface is flat.
        """

        if not star or not body:
            return None

        lat_rad = math.radians(center.latitude)
        cos_lat = math.cos(lat_rad)
        cos_lat_sq = cos_lat * cos_lat
        deg_ratio = (radius_meters / planet_radius_meters) * (180 / math.pi)
        deg_radius_sq = deg_ratio**2

        sql = """  
            SELECT *  
            FROM surface_spots  
            WHERE mineral_type IS NULL  
                AND mineral_original IS NULL  
                AND star_system = ? AND body_name = ?
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
            star,
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
        star: str,
        body: str,
        center: SurfacePoint,
        radius_meters: float,
        planet_radius_meters: float,
    ):
        if not star or not body:
            return

        lat_rad = math.radians(center.latitude)
        cos_lat = math.cos(lat_rad)
        cos_lat_sq = cos_lat * cos_lat

        deg_ratio = (radius_meters / planet_radius_meters) * (180 / math.pi)
        deg_radius_sq = deg_ratio**2

        sql = """    
            SELECT id FROM surface_spots                        
            WHERE star_system = ? AND body_name = ?      
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
            star,  # WHERE star_system
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
                        (DatabaseManager.now_utc(), target_id),
                    )

            # Let the transaction to finish!
            dispatcher.dispatch(KnownEvents.DATABASE_MODIFIED, EventParams())
        except sqlite3.Error as e:
            logger.error(f"Database error during update_visit_time: {e}")

    def add_spot(self, spot: SurfaceSpot) -> bool:
        try:
            success: bool = False
            with self._get_connection() as conn:
                cursor = conn.execute(
                    """
                    INSERT INTO surface_spots (
                        star_system, body_name, latitude, longitude, 
                        spot_number, mineral_type, mineral_original, amount, density, max_miners, last_visit_time, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        spot.star_system,
                        spot.body_name,
                        spot.latitude,
                        spot.longitude,
                        spot.spot_number,
                        spot.mineral_type,
                        spot.mineral_original,
                        spot.amount,
                        spot.density,
                        spot.max_miners,
                        DatabaseManager.now_utc(),
                        spot.notes,
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
                except (ValueError, TypeError) as e:
                    logger.error(f"Database error during _fetch_select_cursor: {e}")
            spots.append(SurfaceSpot(**data))
        return spots

    def get_all_spots(self) -> list[SurfaceSpot]:
        """Fetches ALL records from DB. Warning! It can explode things."""
        with self._get_connection() as conn:
            return DatabaseManager._fetch_select_cursor(
                conn.execute("SELECT * FROM surface_spots")
            )

    def get_planetary_spots(self, location: PlayerLocation | None) -> list[SurfaceSpot]:
        """Fetches records for the current planet if any."""
        if location is None or not location.body_name:
            return []
        with self._get_connection() as conn:
            return DatabaseManager._fetch_select_cursor(
                conn.execute(
                    "SELECT * FROM surface_spots WHERE star_system = ? AND body_name = ?",
                    (location.star_system, location.body_name),
                )
            )

    def get_system_spots(self, system: str) -> list[SurfaceSpot]:
        """Fetches records for the current planet if any."""
        if not system:
            return []
        with self._get_connection() as conn:
            return DatabaseManager._fetch_select_cursor(
                conn.execute(
                    "SELECT * FROM surface_spots WHERE star_system = ?",
                    (system,),
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

    def find_by_mineral(self, mineral_type: str) -> list[SurfaceSpot]:
        """Lists all spots by mineral. Warning! This can be a lot."""
        to_find = f"%{mineral_type}%"
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM surface_spots WHERE mineral_type LIKE ? OR mineral_original LIKE ?",
                (
                    to_find,
                    to_find,
                ),
            )
            return self._fetch_select_cursor(cursor)
