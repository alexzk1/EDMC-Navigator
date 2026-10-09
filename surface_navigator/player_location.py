import datetime
import math
from dataclasses import dataclass

from .models import StarSystem


@dataclass(slots=True)
class SurfacePoint:
    """Represents planetary surface point."""

    latitude: float
    longitude: float


DEFAULT_PLANET_RADIUS = 6371000.0

# Elite's in-game calendar starts 1286 years ahead of the real one (real 2026
# -> in-game 3312). In-game time tracks real UTC for month, day and time of day;
# only the year is shifted. This is a fixed era offset, not a multiple of the
# 400-year Gregorian leap cycle, so an impossible in-game date (e.g. 29 Feb in a
# non-leap in-game year) still has to be rendered - never constructed.
IN_GAME_YEAR_OFFSET = 1286


def in_game_timestamp(
    fmt: str = "%Y-%m-%d %H:%M:%S", now: datetime.datetime | None = None
) -> str:
    """Current UTC time rendered in the in-game calendar.

    ``now`` defaults to the real current UTC, which is why it is a parameter.
    The year is rewritten in the formatted string rather than via
    ``datetime.replace(year=...)``. That keeps an impossible in-game date -
    e.g. 29 Feb in a non-leap in-game year - rendered verbatim, exactly like the
    game does, and never raises ``ValueError``.
    """
    if now is None:
        now = datetime.datetime.now(datetime.timezone.utc)
    real_year = f"{now.year:04d}"
    in_game_year = f"{now.year + IN_GAME_YEAR_OFFSET:04d}"
    return now.strftime(fmt).replace(real_year, in_game_year, 1)


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
        p1: SurfacePoint, p2: SurfacePoint, planet_radius_meters: float
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

        return planet_radius_meters * c

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

    @staticmethod
    def format_distance(dist: float) -> str:
        """Format a distance for display (shared by the overlay and the GUI).

        ``inf`` means there is no valid coordinate yet, so we render a dash.
        Below 1 km we show whole meters; above that kilometres to 2 decimals --
        tens of metres is the precision actually visible in-game, so that is the
        floor we keep.
        """
        if dist == float("inf"):
            return "—"
        if dist < 1000:
            return f"{dist:.0f} m"
        return f"{dist / 1000:.2f} km"
