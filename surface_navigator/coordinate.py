"""Lat/lon <-> string conversion -- the single source of truth.

Coordinates travel between three representations in this plugin:

  * a :class:`SurfacePoint` (the in-memory object every module speaks),
  * the ``{"lat": ..., "lon": ...}`` dict literal used by the main GUI's entry
    field and copied to the clipboard,
  * the rounded numbers shown in the DB-editor tables.

All three conversions funnel through :class:`CoordinateFormatter` so there is
exactly one place that decides what a coordinate string looks like and how it is
parsed. That is what makes the entry field, the table selection and the
clipboard agree with each other.

The parser is a short ordered list of *strategies* (see :meth:`parse`). Each
strategy either returns a :class:`SurfacePoint` or ``None``. Adding a new
supported input format is therefore a matter of appending one strategy - see
the notes on :meth:`parse` for the planned ordering ("most complex" first).
"""

from __future__ import annotations

import ast
from collections.abc import Callable

from .player_location import SurfacePoint


class CoordinateFormatter:
    """Converts between :class:`SurfacePoint` and coordinate strings."""

    # Decimals shown in the DB-editor tables. Kept small so the columns stay
    # narrow; the entry field and the clipboard use *all* digits
    # (``precision=None``) so a coordinate pasted from the internet navigates
    # exactly instead of drifting by a few metres.
    DB_PRECISION = 4

    # The dict literal is both a valid Python literal and valid JSON, so it
    # pastes cleanly into scripts (``ast.literal_eval`` / ``json.loads``) and
    # web tools alike. The outer braces are doubled so ``str.format`` treats
    # them as literal characters, not field delimiters.
    FORMAT_TEMPLATE = '{{"lat": {lat}, "lon": {lon}}}'

    @classmethod
    def to_string(cls, point: SurfacePoint, precision: int | None = None) -> str:
        """Render ``point`` as a ``{"lat": ..., "lon": ...}`` string.

        ``precision=None`` (the default) keeps *every* digit of the float, which
        is what the entry field and the clipboard need so a pasted coordinate
        navigates exactly. ``precision=N`` rounds to ``N`` decimals for the
        narrow DB-editor columns.
        """
        if precision is None:
            lat = repr(point.latitude)
            lon = repr(point.longitude)
        else:
            lat = f"{point.latitude:.{precision}f}"
            lon = f"{point.longitude:.{precision}f}"
        return cls.FORMAT_TEMPLATE.format(lat=lat, lon=lon)

    @classmethod
    def parse(cls, text: str) -> SurfacePoint | None:
        """Parse a coordinate string into a :class:`SurfacePoint`.

        Returns ``None`` when the text is empty or matches no known format, so
        callers can treat "no parse" as "do nothing" (the entry field drops
        navigation on a failed parse).

        Strategies run in the order below, first match wins. The dict literal is
        the only one implemented now; Stage 3 appends the compact numeric
        formats ("most complex" first).
        """
        if not text:
            return None
        stripped = text.strip()
        for strategy in _STRATEGIES:
            point = strategy(stripped)
            if point is not None:
                return point
        return None


def _parse_dict_literal(text: str) -> SurfacePoint | None:
    """``{"lat": 1.5, "lon": 2.5}`` (also accepts single quotes / whitespace)."""
    try:
        value = ast.literal_eval(text)
    except (ValueError, SyntaxError):
        return None
    if not isinstance(value, dict):
        return None
    try:
        return SurfacePoint(float(value["lat"]), float(value["lon"]))  # pyright: ignore[reportUnknownArgumentType]
    except (KeyError, TypeError, ValueError):
        return None


# Ordered list of parse strategies. New formats are appended here (most complex
# first) - see :meth:`CoordinateFormatter.parse`.
_STRATEGIES: list[Callable[[str], SurfacePoint | None]] = [_parse_dict_literal]
