import sqlite3
from typing import List, Optional
from .models import MiningSpot

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS mining_spots (
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
                    last_visit_time TIMESTAMP
                )
            """)

    def add_spot(self, spot: MiningSpot) -> Optional[int]:
        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    INSERT INTO mining_spots (
                        star_system, body_name, latitude, longitude, 
                        spot_number, mineral_type, amount, density, max_miners, last_visit_time
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    spot.star_system, spot.body_name, spot.latitude, spot.longitude,
                    spot.spot_number, spot.mineral_type, spot.amount, spot.density, 
                    spot.max_miners, spot.last_visit_time
                ))
                return cursor.lastrowid
        except sqlite3.Error as e:
            print(f"Database error during add_spot: {e}")
            return None

    def get_all_spots(self) -> List[MiningSpot]:
        spots = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM mining_spots")
            for row in cursor:
                data = dict(row)
                # SQLite might return timestamp as string or datetime depending on driver/version
                if data['last_visit_time'] and not isinstance(data['last_visit_time'], (type(None),)): # Simple check
                     import datetime
                     try:
                         # If it is a string, convert it. 
                         if isinstance(data['last_visit_time'], str):
                            data['last_visit_time'] = datetime.datetime.fromisoformat(data['last_visit_time'])
                     except (ValueError, TypeError):
                         pass
                spots.append(MiningSpot(**data))
        return spots

    def update_spot(self, spot_id: int, **kwargs) -> bool:
        if not kwargs:
            return False
        keys = [f"{k} = ?" for k in kwargs.keys()]
        values = list(kwargs.values())
        sql = f"UPDATE mining_spots SET {', '.join(keys)} WHERE id = ?"
        values.append(spot_id)

        try:
            with self._get_connection() as conn:
                conn.execute(sql, values)
                return True
        except sqlite3.Error as e:
            print(f"Database error during update_spot: {e}")
            return False

    def delete_spot(self, spot_id: int) -> bool:
        try:
            with self._get_connection() as conn:
                conn.execute("DELETE FROM mining_spots WHERE id = ?", (spot_id,))
                return True
        except sqlite3.Error as e:
            print(f"Database error during delete_spot: {e}")
            return False

    def find_closest_by_mineral(self, mineral_type: str) -> List[MiningSpot]:
        spots = []
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM mining_spots WHERE mineral_type LIKE ?", (f"%{mineral_type}%",))
            for row in cursor:
                data = dict(row)
                if data['last_visit_time']:
                     import datetime
                     try:
                         if isinstance(data['last_visit_time'], str):
                            data['last_visit_time'] = datetime.datetime.fromisoformat(data['last_visit_time'])
                     except (ValueError, TypeError):
                         pass
                spots.append(MiningSpot(**data))
        return spots

    def update_visit_time(self, star_system: str, body_name: str, lat: float, lon: float):
        import datetime
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE mining_spots 
                SET last_visit_time = ? 
                WHERE star_system = ? AND body_name = ? AND latitude BETWEEN ? - 0.01 AND ? + 0.01 
                  AND longitude BETWEEN ? - 0.01 AND ? + 0.01
            """, (datetime.datetime.now(), star_system, body_name, lat, lat, lon))

