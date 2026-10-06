import math
from dataclasses import dataclass

from .models import StarSystem


@dataclass(slots=True)
class SurfacePoint:
    """Represents planetary surface point."""

    latitude: float
    longitude: float


DEFAULT_PLANET_RADIUS = 6371000.0


@dataclass(slots=True)
class PlayerLocation:
    """Represent the player's transient spatial state."""

    star_system: StarSystem
    body_name: str = ""
    # Latest known player coordinate.
    player_coord: SurfacePoint | None = None
    # Latest known SRV coordinate.
    srv_coord: SurfacePoint | None = None
    # Radius of the planet.
    radius_meters: float | None = None
    heading_deg: float | None = None
    is_boarded_srv: bool = True


class NavigationUtils:
    """Mathematical utilities"""

    @staticmethod
    def haversine_distance(
        p1: SurfacePoint, p2: SurfacePoint, radius_meters: float
    ) -> float:
        """
        Computes great-circle distance between 2 points in meters.
        """
        lat1, lon1 = math.radians(p1.latitude), math.radians(p1.longitude)
        lat2, lon2 = math.radians(p2.latitude), math.radians(p2.longitude)

        dlat = lat2 - lat1
        dlon = lon2 - lon1

        a = (
            math.sin(dlat / 2) ** 2
            + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
        )

        c = 2 * math.asin(math.sqrt(a))

        return radius_meters * c

    @staticmethod
    def calculate_bearing(p1: SurfacePoint, p2: SurfacePoint) -> float:
        """
        Computes bearing from p1 to p2 in Degrees.
        """
        lat1, lon1 = math.radians(p1.latitude), math.radians(p1.longitude)
        lat2, lat2_lon = math.radians(p2.latitude), math.radians(p2.longitude)

        d_lon = lat2_lon - lon1

        x = math.sin(d_lon) * math.cos(lat2)
        y = (math.cos(lat1) * math.sin(lat2)) - (
            math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
        )

        initial_bearing = math.atan2(x, y)
        return (math.degrees(initial_bearing) + 360) % 360
