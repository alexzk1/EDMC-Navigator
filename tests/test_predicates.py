"""Tests for the query-builder predicate tree.

These pin the two things that matter: each predicate renders a correct
parameterized SQL fragment, and describes itself in text (so the UI never
hard-codes strings that must stay in sync with the code).
"""

from unittest.mock import patch

import pytest

from surface_navigator.models import SurfaceSpot
from surface_navigator.player_location import DEFAULT_PLANET_RADIUS, SurfacePoint
from surface_navigator.predicates import (
    KNOWN_PREDICATES,
    And,
    HasTritiumRing,
    IsTemporary,
    MineralIs,
    Not,
    OnBody,
    Or,
    Predicate,
    QueryContext,
    Within,
    WithinLightYears,
)
from surface_navigator.spot_flags import SurfaceSpotFlags


def _ctx(**kwargs):  # type: ignore
    return QueryContext(**kwargs)  # type: ignore


def _spot(**kwargs):  # type: ignore
    base = {  # type: ignore
        "star_system": "Sol",
        "body_name": "Earth",
        "latitude": 0.0,
        "longitude": 0.0,
        "mineral_type": "Water",
        "mineral_original": "Water",
        **kwargs,
    }
    return SurfaceSpot(**base)  # type: ignore


@pytest.fixture(autouse=True)
def _stub_commodities():
    """The commodity CSV is not present in the test env, so ``resolve_db_value``
    cannot load. Stub it to a safe default (fuzzy fails -> raw input); tests
    that need a specific value patch it again inside their own context."""
    with patch(
        "surface_navigator.predicates.Commodities.resolve_db_value",
        return_value=None,
    ):
        yield


# ---- Within (surface distance SQL) -----------------------------------------


def test_within_sql_matches_flat_earth_pattern():
    ctx = _ctx(
        player_coord=SurfacePoint(10.0, 20.0), planet_radius=DEFAULT_PLANET_RADIUS
    )
    frag, params = Within(5.0).sql(ctx)
    assert "surface_spots.latitude" in frag
    assert "surface_spots.longitude" in frag
    assert "cos" not in frag  # cos is precomputed into params
    # lat, lat, lon, lon, cos_sq, radius_sq
    assert len(params) == 6
    assert params[0] == params[1] == 10.0
    assert params[2] == params[3] == 20.0


def test_within_unset_matches_all():
    frag, params = Within(None).sql(_ctx())
    assert frag == "1 = 1"
    assert params == []


def test_within_no_player_matches_all():
    frag, params = Within(5.0).sql(_ctx(player_coord=None))
    assert frag == "1 = 1"
    assert params == []


def test_within_describes_value():
    assert Within(10.0).describe() == "within 10.0 km"
    assert Within(None).describe() == "distance (km)"


# ---- MineralIs (fuzzy + original SQL) --------------------------------------


def test_mineral_is_normalizes_and_matches_canonical():
    with patch(
        "surface_navigator.predicates.Commodities.resolve_db_value",
        return_value="iridium",
    ):
        pred = MineralIs("Iridium")
        assert pred.to_find == "iridium"
        frag, params = pred.sql(_ctx())
        assert "surface_spots.mineral_type = ?" in frag
        assert params[0] == "iridium"


def test_mineral_is_substring_in_original():
    with patch(
        "surface_navigator.predicates.Commodities.resolve_db_value", return_value=None
    ):
        pred = MineralIs("iridium ore")
        # Fuzzy failed -> fall back to the raw input.
        assert pred.to_find == "iridium ore"
        frag, params = pred.sql(_ctx())
        assert "surface_spots.mineral_original LIKE ?" in frag
        assert params[1] == "%iridium ore%"


def test_mineral_unset_matches_all():
    frag, params = MineralIs(None).sql(_ctx())
    assert frag == "1 = 1"
    assert params == []


# ---- HasFlag derived predicates --------------------------------------------


def test_has_tritium_ring_sql():
    frag, params = HasTritiumRing().sql(_ctx())
    assert "surface_spots.flags" in frag
    assert params == [SurfaceSpotFlags.TRITIUM_RING_PRESENT.value]


def test_is_temporary_sql():
    _, params = IsTemporary().sql(_ctx())
    assert params == [SurfaceSpotFlags.IS_TEMPORARY_MARK.value]


# ---- OnBody ----------------------------------------------------------------


def test_on_body_sql():
    frag, params = OnBody("Earth").sql(_ctx())
    assert frag == "(surface_spots.body_name = ?)"
    assert params == ["Earth"]


def test_on_body_unset_matches_all():
    frag, _ = OnBody(None).sql(_ctx())
    assert frag == "1 = 1"


# ---- WithinLightYears (euclidean SQL) --------------------------------------


def test_within_light_years_sql():
    ctx = _ctx(current_system_coords=(0.0, 0.0, 0.0))
    frag, params = WithinLightYears(100.0).sql(ctx)
    assert "star_systems.x" in frag
    assert "star_systems.y" in frag
    assert "star_systems.z" in frag
    # x0, x0, y0, y0, z0, z0, dist_sq
    assert len(params) == 7
    assert params[6] == 100.0**2


def test_within_light_years_no_current_matches_all():
    frag, _ = WithinLightYears(100.0).sql(_ctx(current_system_coords=None))
    assert frag == "1 = 1"


def test_within_light_years_describes():
    assert WithinLightYears(50.0).describe() == "within 50.0 light-years"
    assert WithinLightYears(None).describe() == "light-year radius"


# ---- Combinators -----------------------------------------------------------


def test_and_combines_and_collects_params():
    ctx = _ctx(player_coord=SurfacePoint(10.0, 20.0))
    frag, params = And(OnBody("Earth"), Within(10.0)).sql(ctx)
    assert frag.startswith("(")
    assert " AND " in frag
    # OnBody: 1 param, Within: 6 params
    assert len(params) == 7


def test_or_combines_with_or():
    ctx = _ctx()
    frag, _ = Or(MineralIs("Water"), MineralIs("Helium")).sql(ctx)
    assert " OR " in frag


def test_not_negates():
    ctx = _ctx()
    frag, _ = Not(IsTemporary()).sql(ctx)
    assert frag.startswith("NOT (")


def test_combinator_describe():
    q = And(MineralIs("Water"), Not(IsTemporary()))
    text = q.describe()
    assert "AND" in text
    assert "NOT" in text


# ---- Registry --------------------------------------------------------------


def test_known_predicates_are_classes_with_describe():
    for cls in KNOWN_PREDICATES:
        assert issubclass(cls, Predicate)
        blank = cls()
        assert isinstance(blank.describe(), str)
        assert blank.describe()  # non-empty
