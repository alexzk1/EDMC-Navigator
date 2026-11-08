"""Tests for :class:`surface_navigator.coordinate.CoordinateFormatter`.

The formatter is the single source of truth for lat/lon <-> ``{"lat": ...,
"lon": ...}`` conversion. These tests pin the three behaviours the rest of the
app relies on: the entry field / clipboard keep *all* digits, the DB-editor
columns stay narrow, and the parse round-trips exactly.
"""

from surface_navigator.coordinate import CoordinateFormatter
from surface_navigator.player_location import SurfacePoint

# ---- to_string ------------------------------------------------------------


def test_to_string_default_is_dict_literal():
    point = SurfacePoint(1.5, -2.5)
    assert CoordinateFormatter.to_string(point) == '{"lat": 1.5, "lon": -2.5}'


def test_to_string_default_keeps_all_digits():
    point = SurfacePoint(0.123456789012345, 12.9876543210987)
    text = CoordinateFormatter.to_string(point)
    # Full precision, not the 4-decimal DB rounding.
    assert text == (
        '{"lat": 0.123456789012345, "lon": 12.9876543210987}'
    )


def test_to_string_with_precision_rounds():
    point = SurfacePoint(1.23456789, -2.98765432)
    text = CoordinateFormatter.to_string(point, precision=CoordinateFormatter.DB_PRECISION)
    assert text == '{"lat": 1.2346, "lon": -2.9877}'


def test_to_string_json_and_python_literal():
    # The format is both valid JSON and a valid Python literal.
    import json

    point = SurfacePoint(3.14, 42.42)
    text = CoordinateFormatter.to_string(point)
    assert json.loads(text) == {"lat": 3.14, "lon": 42.42}


# ---- parse ----------------------------------------------------------------


def test_parse_dict_literal():
    point = CoordinateFormatter.parse('{"lat": 1.5, "lon": -2.5}')
    assert point == SurfacePoint(1.5, -2.5)


def test_parse_accepts_single_quotes_and_whitespace():
    point = CoordinateFormatter.parse("  {'lat': 1.5, 'lon': 2.5}  ")
    assert point == SurfacePoint(1.5, 2.5)


def test_parse_returns_none_on_empty():
    assert CoordinateFormatter.parse("") is None
    assert CoordinateFormatter.parse("   ") is None


def test_parse_returns_none_on_non_dict():
    # A bare number is a single float, not a coordinate (we need two).
    assert CoordinateFormatter.parse("1.5") is None
    assert CoordinateFormatter.parse("not a coordinate") is None


def test_parse_returns_none_on_missing_key():
    assert CoordinateFormatter.parse('{"lat": 1.5}') is None
    assert CoordinateFormatter.parse("{}") is None


def test_parse_returns_none_on_non_numeric():
    assert CoordinateFormatter.parse('{"lat": "x", "lon": 2.0}') is None


# ---- two-float formats ----------------------------------------------------
# Two bare ``<FLOAT>``s (``[+-]?\d+(?:\.\d+)?``) separated by *anything that is
# not part of a float* (a digit, ``+``, ``-`` or ``.``). First is lat, second is
# lon. The sign is always read as part of the number, so it can never double as
# a separator -- that is what makes ``6 -7`` unambiguous while rejecting the
# ambiguous ``6-7``.


def test_parse_two_floats_basic():
    point = CoordinateFormatter.parse("6 -7")
    assert point == SurfacePoint(6.0, -7.0)


def test_parse_two_floats_positive_signs():
    assert CoordinateFormatter.parse("+6,+7") == SurfacePoint(6.0, 7.0)


def test_parse_two_floats_with_decimals_and_comma():
    assert CoordinateFormatter.parse("1.5,2.5") == SurfacePoint(1.5, 2.5)


def test_parse_two_floats_semicolon():
    assert CoordinateFormatter.parse("3.0;4.0") == SurfacePoint(3.0, 4.0)


def test_parse_two_floats_rejects_brackets():
    # Brackets are extra text around the two floats, not a separator between
    # them -- the entry field wants pure "lat lon" input.
    assert CoordinateFormatter.parse("<3.0;4.0>") is None


def test_parse_two_floats_integer_only():
    assert CoordinateFormatter.parse("6,7") == SurfacePoint(6.0, 7.0)


def test_parse_two_floats_double_space():
    # Multiple separator characters in one run are still a single separator.
    assert CoordinateFormatter.parse("6  7") == SurfacePoint(6.0, 7.0)


def test_parse_two_floats_leading_trailing_whitespace():
    assert CoordinateFormatter.parse("  1.2 , 3.4  ") == SurfacePoint(1.2, 3.4)


def test_parse_two_floats_ambiguous_sign_fails():
    # ``6-7`` could mean 6/7 or 6/-7 -> reject (a sign is never a separator).
    assert CoordinateFormatter.parse("6-7") is None
    # ``6- 7`` is equally ambiguous.
    assert CoordinateFormatter.parse("6- 7") is None


def test_parse_two_floats_requires_a_separator():
    # ``6-7`` aside, two adjacent floats with no non-float separator cannot exist:
    # a single float is not a coordinate.
    assert CoordinateFormatter.parse("6") is None
    assert CoordinateFormatter.parse("1.5") is None


def test_parse_two_floats_rejects_three_numbers():
    # Exactly two floats are required; a third breaks the match.
    assert CoordinateFormatter.parse("6 7 8") is None


def test_parse_two_floats_rejects_trailing_junk():
    assert CoordinateFormatter.parse("6 7 x") is None
    assert CoordinateFormatter.parse("6 7.") is None


def test_parse_two_floats_rejects_dot_separator():
    # A dot is part of a float, so it can never be the separator.
    assert CoordinateFormatter.parse("6 . 7") is None


# ---- round trip -----------------------------------------------------------


def test_round_trip_is_exact():
    point = SurfacePoint(0.123456789012345, -12.9876543210987)
    parsed = CoordinateFormatter.parse(CoordinateFormatter.to_string(point))
    assert parsed == point


def test_field_then_parse_navigates_exactly():
    # What the table selection writes into the field, then what Navigate reads.
    field_value = CoordinateFormatter.to_string(SurfacePoint(1.23456789, 2.98765432))
    parsed = CoordinateFormatter.parse(field_value)
    assert parsed == SurfacePoint(1.23456789, 2.98765432)
