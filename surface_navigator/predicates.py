"""Predicate tree for the query builder.

Every predicate is pure data: it renders itself as a *parameterized* SQL
fragment (so all filtering happens inside SQLite, where it is fast) and
describes itself in plain text (so the UI never hard-codes strings that must
stay in sync with the code).

A query is a tree of predicates combined with AND / OR / NOT. The engine walks
the tree, collects the fragments and their params, and runs one query:

    SELECT surface_spots.*, star_systems.star_name AS star_system
    FROM surface_spots
    JOIN star_systems ON surface_spots.star_id = star_systems.star_id
    WHERE <combined fragment>

The INNER JOIN drops any star with no spots, so every result row is a
``SurfaceSpot`` -- even a tritium ring, which is stored as a spot carrying the
TRITIUM_RING_PRESENT flag. That is why there is a *single* query shape: every
predicate just points at ``table.column`` and the two tables are always joined.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from typing import Any

from .mined_names import Commodities
from .player_location import DEFAULT_PLANET_RADIUS, SurfacePoint
from .spot_flags import SurfaceSpotFlags


@dataclass
class QueryContext:
    """Query-level data the engine fills in before running a query.

    Predicates read only what they need from here, so evaluation stays a pure
    SQL render -- no Python-side filtering.
    """

    player_coord: SurfacePoint | None = None
    planet_radius: float = DEFAULT_PLANET_RADIUS
    current_system_coords: tuple[float, float, float] | None = None


class Predicate:
    """Base class.

    ``sql`` returns ``(WHERE fragment, params)``; ``describe`` renders the
    human-readable text the UI shows. ``label`` is the category name used both
    in the "add condition" menu and as the blank placeholder.

    ``serial_name`` is the stable string used to (de)serialize the tree to/from
    JSON for presets and the saved query. ``to_dict``/``from_dict`` implement
    the round-trip; the top-level :func:`deserialize` looks the class up by
    ``serial_name`` so the file format never has to import the classes itself.
    """

    label: str = "condition"
    serial_name: str = "predicate"

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        raise NotImplementedError

    def describe(self) -> str:
        return self.label

    def to_dict(self) -> dict[str, Any]:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        raise NotImplementedError

    def __eq__(self, other: object) -> bool:
        # Structural equality: two predicates are equal when their serialized
        # trees match. This is what lets Preset/dataclass comparisons and set
        # membership work without each class re-implementing field checks.
        if not isinstance(other, Predicate):
            return NotImplemented
        return self.to_dict() == other.to_dict()

    def __hash__(self) -> int:
        # Equal predicates must hash equal. Serializing the tree (keys sorted so
        # dict ordering never matters) gives one implementation for the whole
        # class hierarchy -- no per-class weak hashes to keep in sync.
        return hash(json.dumps(self.to_dict(), sort_keys=True))


# ---- Combinators -----------------------------------------------------------


class And(Predicate):
    serial_name = "and"

    def __init__(self, *predicates: Predicate) -> None:
        self.predicates = list(predicates)

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        frags: list[str] = []
        params: list[object] = []
        for p in self.predicates:
            frag, ps = p.sql(ctx)
            frags.append(f"({frag})")
            params.extend(ps)
        return " AND ".join(frags), params

    def describe(self) -> str:
        return "(" + " AND ".join(p.describe() for p in self.predicates) + ")"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.serial_name,
            "children": [p.to_dict() for p in self.predicates],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(*[deserialize(c) for c in data["children"]])


class Or(Predicate):
    serial_name = "or"

    def __init__(self, *predicates: Predicate) -> None:
        self.predicates = list(predicates)

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        frags: list[str] = []
        params: list[object] = []
        for p in self.predicates:
            frag, ps = p.sql(ctx)
            frags.append(f"({frag})")
            params.extend(ps)
        return " OR ".join(frags), params

    def describe(self) -> str:
        return "(" + " OR ".join(p.describe() for p in self.predicates) + ")"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.serial_name,
            "children": [p.to_dict() for p in self.predicates],
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(*[deserialize(c) for c in data["children"]])


class Not(Predicate):
    serial_name = "not"

    def __init__(self, predicate: Predicate) -> None:
        self.predicate = predicate

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        frag, params = self.predicate.sql(ctx)
        return f"NOT ({frag})", params

    def describe(self) -> str:
        return f"(NOT {self.predicate.describe()})"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name, "child": self.predicate.to_dict()}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(deserialize(data["child"]))


# ---- Surface predicates ----------------------------------------------------


class Within(Predicate):
    """Within ``distance_km`` of the player's position (flat-earth approximation).

    Uses the same planar approximation as the existing radius search: degrees on
    both axes, longitude scaled by ``cos(latitude)``, compared against the
    radius squared in degrees. Points at ``surface_spots``; the player's
    position comes from ``ctx.player_coord``.
    """

    label = "distance (km)"
    serial_name = "within_km"

    def __init__(self, distance_km: float | None = None) -> None:
        self.distance_km = distance_km

    def describe(self) -> str:
        if self.distance_km is None:
            return self.label
        return f"within {self.distance_km:.1f} km"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name, "distance_km": self.distance_km}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(data.get("distance_km"))

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if self.distance_km is None or ctx.player_coord is None:
            return "1 = 1", []
        center = ctx.player_coord
        lat_rad = math.radians(center.latitude)
        cos_lat_sq = math.cos(lat_rad) ** 2
        deg_ratio = (self.distance_km * 1000.0 / ctx.planet_radius) * (180 / math.pi)
        deg_radius_sq = deg_ratio**2
        return (
            (
                "(surface_spots.latitude - ?) * (surface_spots.latitude - ?) + "
                "(surface_spots.longitude - ?) * (surface_spots.longitude - ?) * ? < ?"
            ),
            [
                center.latitude,
                center.latitude,
                center.longitude,
                center.longitude,
                cos_lat_sq,
                deg_radius_sq,
            ],
        )


class MineralIs(Predicate):
    """Matches a spot by commodity (any commodity, not just tritium).

    The user's input is normalized through :class:`Commodities` (so "Iridium"
    resolves to its canonical symbol). A spot matches when the canonical type
    equals the resolved value *or* the resolved value is a substring of the
    original the user typed when recording the spot.

    Tritium is *not* special here: a surface spot with tritium ore is just like
    any other mineral spot. A tritium *ring* is matched by :class:`HasTritiumRing`
    instead. The "rings or spots" combination lives in the UI query library.
    """

    label = "mineral"
    serial_name = "mineral_is"

    def __init__(self, user_input: str | None = None) -> None:
        self.user_input = (user_input or "").strip()
        # Prefer the commodity-catalogue value, fall back to the raw input.
        self.to_find = (
            Commodities.resolve_db_value(self.user_input) or self.user_input.lower()
        )

    def describe(self) -> str:
        if not self.to_find:
            return self.label
        return f"mineral: {self.to_find}"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name, "user_input": self.user_input}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(data.get("user_input"))

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if not self.to_find:
            return "1 = 1", []
        return (
            "(surface_spots.mineral_type = ? OR surface_spots.mineral_original LIKE ?)",
            [self.to_find, f"%{self.to_find}%"],
        )


class HasFlag(Predicate):
    """Base for flag-based predicates.

    Subclasses declare the flag they watch and its ``serial_name``, so the UI
    only needs ``describe()`` and serialization needs no per-flag logic.
    """

    flag: SurfaceSpotFlags = ...  # type: ignore[assignment]  # set by subclasses
    label: str = "flag"  # set by subclasses
    serial_name: str = "has_flag"  # set by subclasses

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        return "(surface_spots.flags & ?) != 0", [self.flag.value]

    def describe(self) -> str:
        return self.label

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        # Look the exact class up by serial_name so the flag bit stays in sync
        # with the class that owns it -- no per-flag text to keep in sync.
        return _SERIALIZERS[data["type"]]()


class HasTritiumRing(HasFlag):
    """A tritium *ring* -- a spot carrying the TRITIUM_RING_PRESENT flag.

    Rings are stored like any other spot, but the flag marks them as being in
    space (a ring around the star/body), not on a surface.
    """

    flag = SurfaceSpotFlags.TRITIUM_RING_PRESENT
    label = "has tritium ring"
    serial_name = "has_tritium_ring"


class IsTemporary(HasFlag):
    flag = SurfaceSpotFlags.IS_TEMPORARY_MARK
    label = "is temporary"
    serial_name = "is_temporary"


class OnBody(Predicate):
    label = "on body"
    serial_name = "on_body"

    def __init__(self, body_name: str | None = None) -> None:
        self.body_name = body_name

    def describe(self) -> str:
        if not self.body_name:
            return self.label
        return f"on {self.body_name}"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name, "body_name": self.body_name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(data.get("body_name"))

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        # A landing spot sits on a real body: skip empty-body_name rows (bad
        # data -- the schema is NOT NULL, but "" can be written) and tritium
        # rings (they live in space, flag set, coords 0/0). The ring exclusion
        # is what makes "OnBody" mean "where you can land", not "any record".
        frags: list[str] = [
            "surface_spots.body_name != ''",
            "(surface_spots.flags & ?) = 0",
        ]
        params: list[object] = [SurfaceSpotFlags.TRITIUM_RING_PRESENT.value]
        if self.body_name:
            frags.append("surface_spots.body_name = ?")
            params.append(self.body_name)
        return " AND ".join(frags), params


# ---- System predicate (distance in space) ----------------------------------


class WithinLightYears(Predicate):
    """Within ``distance_ly`` light-years of the current system (Euclidean).

    Points at ``star_systems``; the current system's coordinates come from
    ``ctx.current_system_coords`` (filled from FSDJump / CarrierJump / Location
    on arrival). Systems without their own coordinates are never matched.
    """

    label = "light-year radius"
    serial_name = "within_light_years"

    def __init__(self, distance_ly: float | None = None) -> None:
        self.distance_ly = distance_ly

    def describe(self) -> str:
        if self.distance_ly is None:
            return self.label
        return f"within {self.distance_ly:.1f} light-years"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name, "distance_ly": self.distance_ly}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(data.get("distance_ly"))

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if self.distance_ly is None or ctx.current_system_coords is None:
            return "1 = 1", []
        x0, y0, z0 = ctx.current_system_coords
        dist_sq = self.distance_ly**2
        # A system with any missing coordinate cannot have a distance computed,
        # so it fits *any* radius -- better to show it than to drop it.
        return (
            (
                "(star_systems.x IS NULL OR star_systems.y IS NULL OR "
                "star_systems.z IS NULL OR "
                "((star_systems.x - ?) * (star_systems.x - ?) + "
                "(star_systems.y - ?) * (star_systems.y - ?) + "
                "(star_systems.z - ?) * (star_systems.z - ?)) <= ?)"
            ),
            [x0, x0, y0, y0, z0, z0, dist_sq],
        )


# ---- Registry --------------------------------------------------------------

# Predicate classes available in the "add condition" menu, in display order.
# The UI builds a blank instance (``cls()``) to read ``describe()`` and pairs it
# with the class so a new one can be created on pick -- no UI-side text.
KNOWN_PREDICATES: list[type[Predicate]] = [
    Within,
    MineralIs,
    HasTritiumRing,
    IsTemporary,
    OnBody,
    WithinLightYears,
]


# ---- Serialization ---------------------------------------------------------

# Stable name -> class, keyed by ``serial_name``. This is what lets a saved
# query file reconstruct the tree without importing the classes by name, and
# keeps the flag bit owned by the class that declares it.
_SERIALIZERS: dict[str, type[Predicate]] = {
    Within.serial_name: Within,
    MineralIs.serial_name: MineralIs,
    HasTritiumRing.serial_name: HasTritiumRing,
    IsTemporary.serial_name: IsTemporary,
    OnBody.serial_name: OnBody,
    WithinLightYears.serial_name: WithinLightYears,
    And.serial_name: And,
    Or.serial_name: Or,
    Not.serial_name: Not,
}


def deserialize(data: dict[str, Any]) -> Predicate:
    """Reconstruct a predicate tree from its :meth:`Predicate.to_dict` form.

    This is the one-directional half of the (de)serialization pair. The other
    half is :meth:`Predicate.to_dict` -- every predicate serializes itself, so
    there is no top-level ``serialize`` to call sites (and no extra call on the
    hot path): ``query.to_dict()`` serializes, ``deserialize(...)`` restores.

    Raises ``KeyError`` for an unknown ``type`` so a corrupt/foreign file fails
    loudly on load rather than silently producing an empty query.
    """
    cls = _SERIALIZERS[data["type"]]
    return cls.from_dict(data)
