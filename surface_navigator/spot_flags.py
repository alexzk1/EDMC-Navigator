"""Bit flags stored per surface spot (the ``surface_spots.flags`` column).

A single ``INTEGER`` column holds an arbitrary set of independent on/off
markers, one bit each. A bit-field scales far better than a lone boolean: new
markers can be added later without any schema change -- each new marker only
consumes one more bit, and existing rows simply read as ``0`` (no flags).

The default value is ``0`` -- no flags set.
"""

from enum import Flag, auto


class SurfaceSpotFlags(Flag):
    """Independent on/off markers for a single surface spot (one bit each).

    Add a new marker by appending another ``= auto()`` line; it takes the next
    free bit and nothing else changes.
    """

    # First concrete marker. Setting this bit only reserves one bit here; the
    # "temporary bookmark" behaviour (auto-removal once its TTL expires) is the
    # next task -- for now the flag can already be set/cleared through the DB.
    IS_TEMPORARY_MARK = auto()
