"""Tests for the surface_navigator DatabaseManager.

These verify the ``star_systems`` normalization: ``surface_spots`` references a
dedicated ``star_systems`` table via ``star_id``, and the historical
``SurfaceSpot.star_system`` string is transparently reconstructed on read.

Every test DB is created in ``/tmp`` so the repo stays clean (see the
``db_path`` fixture).
"""

import math
import os
import tempfile
import time
from collections.abc import Iterator

import pytest

from surface_navigator.database import DatabaseManager
from surface_navigator.models import StarSystem, SurfaceSpot
from surface_navigator.player_location import PlayerLocation, SurfacePoint


@pytest.fixture()
def db_path() -> Iterator[str]:
    """A fresh empty DB path in /tmp, removed after the test."""
    fd, path = tempfile.mkstemp(
        prefix="edmc_surface_navigator_", suffix=".db", dir="/tmp"
    )
    os.close(fd)
    yield path
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture()
def db(db_path: str) -> DatabaseManager:
    return DatabaseManager(db_path)


def _spot(
    system: str,
    body: str,
    lat: float,
    lon: float,
    mineral: str | None = None,
    num: int | None = None,
) -> SurfaceSpot:
    return SurfaceSpot(
        star_system=system,
        body_name=body,
        latitude=lat,
        longitude=lon,
        spot_number=num,
        mineral_type=mineral,
        mineral_original=mineral,
        max_miners=1,
    )


def _lat_deg_for_distance(distance_m: float, planet_radius_m: float) -> float:
    """Degrees of latitude covering ``distance_m`` along a meridian."""
    return distance_m * 180.0 / (math.pi * planet_radius_m)


def _lon_deg_for_distance(
    distance_m: float, planet_radius_m: float, lat_deg: float
) -> float:
    """Degrees of longitude covering ``distance_m`` at ``lat_deg``.

    Uses the standard small-angle relation (physical distance shrinks with
    ``cos(lat)`` for east-west travel). This is derived independently of the
    SQL so the test validates that the SQL applies the ``cos(lat)`` factor.
    """
    return (
        distance_m
        * 180.0
        / (math.pi * planet_radius_m * math.cos(math.radians(lat_deg)))
    )


def _columns(db: DatabaseManager, table: str) -> list[str]:
    conn = db._get_connection()  # type: ignore
    return [r[1] for r in conn.execute(f"PRAGMA table_info({table})")]


# ---- schema ----


def test_star_systems_table_created(db: DatabaseManager):
    conn = db._get_connection()  # type: ignore
    names = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert "star_systems" in names


def test_star_systems_columns_match_spec(db: DatabaseManager):
    assert _columns(db, "star_systems") == [
        "star_id",
        "star_name",
        "x",
        "y",
        "z",
        "systemid",
    ]


def test_surface_spots_uses_star_id_not_star_system(db: DatabaseManager):
    cols = _columns(db, "surface_spots")
    assert "star_id" in cols
    assert "star_system" not in cols


def test_incomplete_mining_indexes_are_distinct(db: DatabaseManager):
    """Both incomplete-mining-spot indexes must exist with their own name.

    They previously shared the name ``idx_incomplete_mining_spots``; SQLite
    silently ignores a second ``CREATE INDEX IF NOT EXISTS`` with a name that
    already exists, so the composite index was never created.
    """
    conn = db._get_connection()  # type: ignore
    index_names = {
        r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
    }
    assert "idx_incomplete_mining_spots" in index_names
    assert "idx_incomplete_mining_spots_system" in index_names
    lat_lon = {
        r[2] for r in conn.execute("PRAGMA index_info(idx_incomplete_mining_spots)")
    }
    assert lat_lon == {"latitude", "longitude"}
    system_cols = {
        r[2]
        for r in conn.execute("PRAGMA index_info(idx_incomplete_mining_spots_system)")
    }
    assert system_cols == {"star_id", "body_name", "latitude", "longitude"}


# ---- round trip ----


def test_add_and_read_all_reconstructs_star_system(db: DatabaseManager):
    for s in (
        _spot("Alpha", "b1", 10.0, 20.0, "iron"),
        _spot("Alpha", "b2", 11.0, 21.0, "iron"),
        _spot("Beta", "b3", 12.0, 22.0, "silver"),
    ):
        assert db.add_spot(s) is True

    spots = db.get_all_spots()
    assert len(spots) == 3
    assert {sp.star_system for sp in spots} == {"Alpha", "Beta"}


def test_star_names_deduped_by_name(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b1", 10.0, 20.0, "iron"))
    db.add_spot(_spot("Alpha", "b2", 11.0, 21.0, "iron"))
    count = (
        db._get_connection()  # type: ignore
        .execute("SELECT COUNT(*) FROM star_systems WHERE star_name='Alpha'")
        .fetchone()[0]
    )
    assert count == 1


def test_get_system_spots(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b1", 10.0, 20.0, "iron"))
    db.add_spot(_spot("Alpha", "b2", 11.0, 21.0, "iron"))
    db.add_spot(_spot("Beta", "b3", 12.0, 22.0, "silver"))
    assert len(db.get_system_spots("Alpha")) == 2
    assert len(db.get_system_spots("Beta")) == 1


def test_get_planetary_spots(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b1", 10.0, 20.0, "iron"))
    db.add_spot(_spot("Alpha", "b2", 11.0, 21.0, "iron"))
    loc = PlayerLocation(star_system=StarSystem(star_name="Alpha"), body_name="b1")
    assert len(db.get_planetary_spots(loc)) == 1


def test_find_by_mineral(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b1", 10.0, 20.0, "iron"))
    db.add_spot(_spot("Alpha", "b2", 11.0, 21.0, "iron"))
    db.add_spot(_spot("Beta", "b3", 12.0, 22.0, "silver"))
    iron = db.find_by_mineral("iron")
    assert len(iron) == 2
    assert all(sp.star_system == "Alpha" for sp in iron)


def test_find_incomplete_surface_mining_spot(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b4", 10.0, 20.0))  # no mineral set
    result = db.find_incomplete_surface_mining_spot(
        star="Alpha",
        body="b4",
        center=SurfacePoint(10.0, 20.0),
        radius_meters=5000.0,
        planet_radius_meters=1000000.0,
    )
    assert result is not None
    assert result.star_system == "Alpha"
    assert result.mineral_type is None


def test_closeness_radius_boundary_in_every_direction(db: DatabaseManager):
    """A spot is found by physical distance in any direction, and excluded
    beyond the radius. High latitude makes the ``cos(lat)`` longitude scaling
    sensitive: a naive SQL that ignores it would mis-classify the eastward spot."""
    planet_radius = 1_000_000.0
    center_lat, center_lon = 70.0, 30.0
    radius_m = 5_000.0

    north = _spot(
        "Closeness",
        "north",
        center_lat + _lat_deg_for_distance(0.5 * radius_m, planet_radius),
        center_lon,
    )
    east = _spot(
        "Closeness",
        "east",
        center_lat,
        center_lon + _lon_deg_for_distance(0.5 * radius_m, planet_radius, center_lat),
    )
    far = _spot(
        "Closeness",
        "far",
        center_lat + _lat_deg_for_distance(3.0 * radius_m, planet_radius),
        center_lon,
    )
    for s in (north, east, far):
        db.add_spot(s)

    # Within radius, one purely north and one purely east.
    assert (
        db.find_incomplete_surface_mining_spot(
            "Closeness",
            "north",
            SurfacePoint(center_lat, center_lon),
            radius_m,
            planet_radius,
        )
        is not None
    )
    assert (
        db.find_incomplete_surface_mining_spot(
            "Closeness",
            "east",
            SurfacePoint(center_lat, center_lon),
            radius_m,
            planet_radius,
        )
        is not None
    )
    # Beyond radius -> not found.
    assert (
        db.find_incomplete_surface_mining_spot(
            "Closeness",
            "far",
            SurfacePoint(center_lat, center_lon),
            radius_m,
            planet_radius,
        )
        is None
    )


def test_closeness_selects_nearest_of_candidates(db: DatabaseManager):
    """When several incomplete spots in the same body are inside the radius,
    the one with the smallest (formula) distance to the center is returned."""
    planet_radius = 1_000_000.0
    center_lat, center_lon = 10.0, 10.0
    radius_m = 10_000.0

    near = _spot(
        "NearFar",
        "body",
        center_lat + _lat_deg_for_distance(0.2 * radius_m, planet_radius),
        center_lon,
    )
    farther = _spot(
        "NearFar",
        "body",
        center_lat + _lat_deg_for_distance(0.8 * radius_m, planet_radius),
        center_lon,
    )
    db.add_spot(near)
    db.add_spot(farther)

    result = db.find_incomplete_surface_mining_spot(
        "NearFar", "body", SurfacePoint(center_lat, center_lon), radius_m, planet_radius
    )
    assert result is not None
    assert result.latitude == near.latitude


def test_update_spot(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b4", 10.0, 20.0))
    spot = db.get_system_spots("Alpha")[0]
    assert spot.id is not None
    assert db.update_spot(spot.id, mineral_type="gold") is True


def test_delete_spot(db: DatabaseManager):
    db.add_spot(_spot("Beta", "b3", 12.0, 22.0, "silver"))
    spot = db.get_system_spots("Beta")[0]
    assert spot.id is not None
    assert db.delete_spot(spot.id) is True
    assert db.get_system_spots("Beta") == []


def test_update_visit_time_advances(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b1", 10.0, 20.0, "iron"))

    # Stored value comes back parsed from the ISO string we write.
    before = db.get_system_spots("Alpha")[0].last_visit_time
    assert before is not None

    # Ensure real time has passed so the new timestamp actually differs.
    time.sleep(2)

    db.update_visit_time(
        star="Alpha",
        body="b1",
        center=SurfacePoint(10.0, 20.0),
        radius_meters=5000.0,
        planet_radius_meters=1000000.0,
    )

    after = db.get_system_spots("Alpha")[0].last_visit_time
    assert after is not None
    assert after > before  # the value was genuinely updated, not just written


# ---- star name uniqueness ----


def test_name_only_dedup_returns_same_id(db: DatabaseManager):
    assert db._get_or_create_star("Gamma") == db._get_or_create_star("Gamma")  # type: ignore


def test_same_name_same_id_regardless_of_systemid(db: DatabaseManager):
    # Names are unique: the systemid no longer splits same-named systems.
    a = db._get_or_create_star("Delta", systemid=111)  # type: ignore
    b = db._get_or_create_star("Delta", systemid=222)  # type: ignore
    assert a == b


def test_systemid_arriving_late_attaches_to_name_row(db: DatabaseManager):
    by_name = db._get_or_create_star("Delta")  # type: ignore # systemid unknown for now
    with_systemid = db._get_or_create_star("Delta", systemid=999)  # type: ignore
    assert by_name == with_systemid
    # No NULL-systemid row is left behind.
    leftover = (
        db._get_connection()  # type: ignore
        .execute(
            "SELECT COUNT(*) FROM star_systems WHERE star_name='Delta' AND systemid IS NULL"
        )
        .fetchone()[0]
    )
    assert leftover == 0


# ---- StarSystem partial updates (fill NULLs only) ----


def test_starsystem_creates_with_all_fields(db: DatabaseManager):
    sid = db._get_or_create_star(  # type: ignore
        StarSystem(
            star_name="Omega",
            x=1.0,
            y=2.0,
            z=3.0,
            systemid=42,
        )
    )
    row = tuple(
        db._get_connection()  # type: ignore
        .execute(
            "SELECT star_id, star_name, x, y, z, systemid FROM star_systems "
            "WHERE star_name='Omega'"
        )
        .fetchone()
    )
    assert row == (sid, "Omega", 1.0, 2.0, 3.0, 42)


def test_starsystem_fields_fill_nulls_later(db: DatabaseManager):
    # First arrival: only the name is known.
    first = db._get_or_create_star(StarSystem(star_name="Omega"))  # type: ignore
    # Second arrival: coordinates arrive late, systemid still unknown.
    second = db._get_or_create_star(StarSystem(star_name="Omega", x=1.0, y=2.0, z=3.0))  # type: ignore
    assert first == second
    row = tuple(
        db._get_connection()  # type: ignore
        .execute("SELECT x, y, z, systemid FROM star_systems WHERE star_name='Omega'")
        .fetchone()
    )
    assert row == (1.0, 2.0, 3.0, None)


def test_starsystem_does_not_overwrite_existing_values(db: DatabaseManager):
    # A complete row arrives first.
    first = db._get_or_create_star(  # type: ignore
        StarSystem(star_name="Omega", x=1.0, y=2.0, z=3.0, systemid=42)
    )
    # A partial update arrives later with conflicting values.
    db._get_or_create_star(StarSystem(star_name="Omega", x=99.0, y=99.0, z=99.0))  # type: ignore
    assert first == db._get_or_create_star(StarSystem(star_name="Omega"))  # type: ignore
    row = tuple(
        db._get_connection()  # type: ignore
        .execute("SELECT x, y, z, systemid FROM star_systems WHERE star_name='Omega'")
        .fetchone()
    )
    # Original values are preserved; the partial update is ignored.
    assert row == (1.0, 2.0, 3.0, 42)


def test_cascade_delete_star(db: DatabaseManager):
    db.add_spot(_spot("Alpha", "b1", 10.0, 20.0, "iron"))
    assert (
        db._get_connection().execute("SELECT COUNT(*) FROM surface_spots").fetchone()[0]  # type: ignore
        == 1
    )

    with db._get_connection() as conn:  # type: ignore
        conn.execute("DELETE FROM star_systems WHERE star_name='Alpha'")

    assert (
        db._get_connection().execute("SELECT COUNT(*) FROM surface_spots").fetchone()[0]  # type: ignore
        == 0
    )
