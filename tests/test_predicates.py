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
    InvalidContext,
    IsTemporary,
    MineralIs,
    Not,
    OnBody,
    Or,
    Predicate,
    QueryContext,
    SearchInCurrentSystem,
    SearchInExactSystem,
    StarNotFoundError,
    Within,
    WithinLightYears,
    WithinLightYearsOfStar,
    deserialize,
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
    assert Within(None).describe() == "Surface Distance"


# ---- validate_context (missing input / context) ----------------------------


def test_validate_context_default_is_noop():
    # A self-sufficient predicate never needs context.
    MineralIs("iridium").validate_context(_ctx())


def test_within_validate_context_needs_radius():
    ctx = _ctx(player_coord=SurfacePoint(10.0, 20.0))
    with pytest.raises(InvalidContext, match="radius"):
        Within(None).validate_context(ctx)


def test_within_validate_context_needs_surface_position():
    # A radius set but the player flying in space (no lat/lon) -> can't evaluate.
    with pytest.raises(InvalidContext, match="space"):
        Within(5.0).validate_context(_ctx(player_coord=None))


def test_within_validate_context_ok_on_surface():
    ctx = _ctx(player_coord=SurfacePoint(10.0, 20.0))
    Within(5.0).validate_context(ctx)  # no raise


def test_within_light_years_validate_context_needs_radius():
    ctx = _ctx(current_system_coords=(0.0, 0.0, 0.0))
    with pytest.raises(InvalidContext, match="radius"):
        WithinLightYears(None).validate_context(ctx)


def test_within_light_years_validate_context_needs_current_star():
    # Radius set but no current-system coordinates (game not running).
    with pytest.raises(InvalidContext, match="current star"):
        WithinLightYears(5.0).validate_context(_ctx())


def test_validate_context_combinators_recurse():
    # A Not(And(...)) wrapping a radius-less Within still fails.
    tree = Not(And(Within(None), MineralIs("iridium")))
    with pytest.raises(InvalidContext):
        tree.validate_context(_ctx(player_coord=SurfacePoint(1.0, 2.0)))


def test_validate_context_or_reports_first_bad_child():
    with pytest.raises(InvalidContext):
        Or(MineralIs("iridium"), WithinLightYears(None)).validate_context(
            _ctx(current_system_coords=(0.0, 0.0, 0.0))
        )


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
    # body filter plus the two standing exclusions (empty body, tritium ring).
    assert frag == (
        "surface_spots.body_name != '' "
        "AND (surface_spots.flags & ?) = 0 "
        "AND surface_spots.body_name = ?"
    )
    assert params == [SurfaceSpotFlags.TRITIUM_RING_PRESENT.value, "Earth"]


def test_on_body_unset_matches_landing_spots():
    # Even unfilled, OnBody means "landing spot" -- rings and empty-body rows
    # are excluded, so it is not a bare "match everything".
    frag, params = OnBody(None).sql(_ctx())
    assert frag == (
        "surface_spots.body_name != '' AND (surface_spots.flags & ?) = 0"
    )
    assert params == [SurfaceSpotFlags.TRITIUM_RING_PRESENT.value]


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
    assert WithinLightYears(None).describe() == "Near Current Star"


def test_within_light_years_references_no_star():
    # The current star is always known, so the predicate names no centre.
    assert WithinLightYears(100.0).referenced_stars() == set()


# ---- WithinLightYearsOfStar (named-star variant) ---------------------------


def test_within_light_years_of_star_sql():
    ctx = _ctx(current_system_coords=(0.0, 0.0, 0.0), star_coords={"Sol": (1.0, 2.0, 3.0)})
    frag, params = WithinLightYearsOfStar(50.0, "Sol").sql(ctx)
    assert "star_systems.x" in frag
    # x0, x0, y0, y0, z0, z0, dist_sq
    assert len(params) == 7
    assert params[:6] == [1.0, 1.0, 2.0, 2.0, 3.0, 3.0]
    assert params[6] == 50.0**2


def test_within_light_years_of_star_missing_star_raises():
    # The engine is supposed to resolve the star first; a missing centre here
    # is a loud failure, not a silent no-match.
    with pytest.raises(StarNotFoundError):
        WithinLightYearsOfStar(50.0, "Kepler-442").sql(_ctx())


def test_within_light_years_of_star_unset_matches_all():
    assert WithinLightYearsOfStar(None, "Sol").sql(_ctx()) == ("1 = 1", [])
    assert WithinLightYearsOfStar(50.0, None).sql(_ctx()) == ("1 = 1", [])


def test_within_light_years_of_star_describes():
    assert WithinLightYearsOfStar(50.0, "Sol").describe() == "within 50.0 ly of Sol"
    assert WithinLightYearsOfStar(None, "Sol").describe() == "Near Any Star"


def test_within_light_years_of_star_references_name():
    assert WithinLightYearsOfStar(50.0, "Sol").referenced_stars() == {"Sol"}
    assert WithinLightYearsOfStar(50.0, None).referenced_stars() == set()


def test_within_light_years_of_star_roundtrip():
    q = WithinLightYearsOfStar(100.0, "Sol")
    assert deserialize(q.to_dict()) == q


# ---- System-scope predicates (exact name) ----------------------------------


def test_search_in_exact_system_sql():
    frag, params = SearchInExactSystem("Sol").sql(_ctx())
    assert frag == "star_systems.star_name = ?"
    assert params == ["Sol"]


def test_search_in_exact_system_unset_matches_all():
    assert SearchInExactSystem(None).sql(_ctx()) == ("1 = 1", [])


def test_search_in_exact_system_describes():
    assert SearchInExactSystem("Sol").describe() == "in Sol"
    assert SearchInExactSystem(None).describe() == "In System"


def test_search_in_exact_system_roundtrip():
    q = SearchInExactSystem("Sol")
    assert deserialize(q.to_dict()) == q


def test_search_in_current_system_uses_current_name():
    frag, params = SearchInCurrentSystem().sql(_ctx(current_system_name="Sol"))
    assert frag == "star_systems.star_name = ?"
    assert params == ["Sol"]


def test_search_in_current_system_unset_matches_all():
    assert SearchInCurrentSystem().sql(_ctx(current_system_name=None)) == ("1 = 1", [])


def test_search_in_current_system_describes():
    assert SearchInCurrentSystem().describe() == "In Current System"


def test_search_in_current_system_roundtrip():
    assert deserialize(SearchInCurrentSystem().to_dict()) == SearchInCurrentSystem()


# ---- Combinators -----------------------------------------------------------


def test_and_combines_and_collects_params():
    ctx = _ctx(player_coord=SurfacePoint(10.0, 20.0))
    frag, params = And(OnBody("Earth"), Within(10.0)).sql(ctx)
    assert frag.startswith("(")
    assert " AND " in frag
    # OnBody: 2 params (ring flag + body), Within: 6 params
    assert len(params) == 8


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


def test_referenced_stars_aggregates_across_tree():
    # A named-star search nested in an AND/OR/Not exposes its star so the
    # engine can resolve it; ordinary predicates contribute nothing.
    star = WithinLightYearsOfStar(50.0, "Sol")
    assert star.referenced_stars() == {"Sol"}
    q = And(
        Or(WithinLightYearsOfStar(50.0, "Sol"), OnBody("Kepler-442 b")),
        Not(WithinLightYears(100.0)),
    )
    assert q.referenced_stars() == {"Sol"}


# ---- Registry --------------------------------------------------------------


def test_known_predicates_are_classes_with_describe():
    for cls in KNOWN_PREDICATES:
        assert issubclass(cls, Predicate)
        blank = cls()
        assert isinstance(blank.describe(), str)
        assert blank.describe()  # non-empty


# ---- Serialization round-trip ----------------------------------------------
# ``Predicate.__eq__`` compares by serialized structure, so a faithful
# round-trip reproduces an equal predicate -- we assert that directly.


def test_leaf_within_roundtrip():
    q = Within(12.5)
    assert deserialize(q.to_dict()) == q


def test_leaf_mineral_roundtrip():
    q = MineralIs("Iridium")
    assert deserialize(q.to_dict()) == q


def test_leaf_on_body_roundtrip():
    q = OnBody("Earth")
    assert deserialize(q.to_dict()) == q


def test_leaf_flags_roundtrip():
    assert deserialize(HasTritiumRing().to_dict()) == HasTritiumRing()
    assert deserialize(IsTemporary().to_dict()) == IsTemporary()


def test_leaf_within_light_years_roundtrip():
    q = WithinLightYears(100.0)
    assert deserialize(q.to_dict()) == q


def test_combinators_roundtrip():
    q = And(
        Or(HasTritiumRing(), MineralIs("tritium")),
        Not(WithinLightYears(50.0)),
        OnBody("Kepler-442 b"),
    )
    assert deserialize(q.to_dict()) == q


def test_unknown_type_raises_keyerror():
    with pytest.raises(KeyError):
        deserialize({"type": "not_a_real_predicate"})
