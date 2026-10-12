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
from dataclasses import dataclass, field
from typing import Any

from .mined_names import Commodities
from .player_location import DEFAULT_PLANET_RADIUS, SurfacePoint
from .spot_flags import SurfaceSpotFlags


class StarNotFoundError(LookupError):
    """A star-scoped search references a star with no coordinates.

    Raised when the engine cannot resolve a centre star (not in the local DB
    and the resolver callback did not supply coordinates). The callback is the
    hook for online lookup + insert-then-retry; with no callback (the default)
    this is a hard failure.
    """


class InvalidContext(ValueError):
    """A predicate can't be evaluated: required input or query context is
    missing.

    Raised by :meth:`Predicate.validate_context` before a query runs -- when a
    required field (a radius, a name) is left blank, or a location-dependent
    predicate's context (the player's current position or star) is absent. The
    builder reports this as a clear reason instead of letting the predicate
    silently degrade to a match-all ``1 = 1``.
    """


@dataclass
class QueryContext:
    """Query-level data the engine fills in before running a query.

    Predicates read only what they need from here, so evaluation stays a pure
    SQL render -- no Python-side filtering.
    """

    player_coord: SurfacePoint | None = None
    planet_radius: float = DEFAULT_PLANET_RADIUS
    current_system_coords: tuple[float, float, float] | None = None
    # The player's current system name (e.g. "Sol"). Filled from the FSDJump /
    # CarrierJump / Location event. ``SearchInCurrentSystem`` renders against
    # this; when unset it matches every system.
    current_system_name: str | None = None
    # Named star -> (x, y, z) for star-scoped searches. The engine populates
    # this by resolving ``referenced_stars()`` against the DB (and, via the
    # resolver callback, online sources) before running the query.
    star_coords: dict[str, tuple[float, float, float]] = field(
        default_factory=dict[str, tuple[float, float, float]]
    )


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

    def referenced_stars(self) -> set[str]:
        """Named stars this predicate centers a search on.

        Overridden by star-scoped predicates so the engine can resolve their
        coordinates up front. The default is empty: ordinary surface searches
        do not care which star a spot belongs to.
        """
        return set()

    def validate_context(self, ctx: QueryContext) -> None:
        """Raise :class:`InvalidContext` if this predicate can't be evaluated.

        The default is a no-op: a predicate with no input or context
        requirements is always evaluable. Predicates that *do* require input
        (a radius, a name) or query context (the player's current position or
        star) override this to check their preconditions.

        The engine calls this for the whole tree before running (each
        combinator recurses into its children), so a missing radius or an
        unknown current star fails fast with a clear message instead of
        silently rendering the match-all ``1 = 1`` fragment.
        """

    def make_widget(self, parent: Any, *, data: Any) -> Any:
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

    def referenced_stars(self) -> set[str]:
        stars: set[str] = set()
        for p in self.predicates:
            stars |= p.referenced_stars()
        return stars

    def validate_context(self, ctx: QueryContext) -> None:
        for p in self.predicates:
            p.validate_context(ctx)

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

    def referenced_stars(self) -> set[str]:
        stars: set[str] = set()
        for p in self.predicates:
            stars |= p.referenced_stars()
        return stars

    def validate_context(self, ctx: QueryContext) -> None:
        for p in self.predicates:
            p.validate_context(ctx)

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

    def referenced_stars(self) -> set[str]:
        return self.predicate.referenced_stars()

    def validate_context(self, ctx: QueryContext) -> None:
        self.predicate.validate_context(ctx)

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

    label = "Surface Distance"
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

    def make_widget(self, parent: Any, *, data: Any):
        # Lazy import avoids a circular import: query_builder imports
        # predicates, so predicates must not import the widgets at module load.
        from .query_builder.widgets.numeric import NumericInputWidget

        return NumericInputWidget(
            self,
            parent,
            data,
            leaf_cls=Within,
            field="distance_km",
            label="Search Radius",
            unit="km",
        )

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

    def validate_context(self, ctx: QueryContext) -> None:
        if self.distance_km is None:
            raise InvalidContext("Enter a surface radius before searching.")
        if ctx.player_coord is None:
            # ``player_coord`` (lat/lon) lives on the planet surface; it is
            # absent while the player flies in space, so a surface-distance
            # search can't be evaluated there.
            raise InvalidContext(
                "Surface distance needs your position on a planet surface -- "
                "you appear to be flying in space (no lat/lon)."
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

    label = "Surface Mineral"
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

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.mineral import MineralInputWidget

        return MineralInputWidget(self, parent, data)

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if not self.to_find:
            return "1 = 1", []
        return (
            "(surface_spots.mineral_type = ? OR surface_spots.mineral_original LIKE ?)",
            [self.to_find, f"%{self.to_find}%"],
        )

    def validate_context(self, ctx: QueryContext) -> None:
        if not self.to_find:
            raise InvalidContext("Enter a surface mineral before searching.")


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
    label = "Is Tritium Ring"
    serial_name = "has_tritium_ring"

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.flag import FlagStatusWidget

        return FlagStatusWidget(self, parent, data)


class IsTemporary(HasFlag):
    flag = SurfaceSpotFlags.IS_TEMPORARY_MARK
    label = "Is Temporary"
    serial_name = "is_temporary"

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.flag import FlagStatusWidget

        return FlagStatusWidget(self, parent, data)


class OnBody(Predicate):
    label = "Is on Body"
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

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.on_body import OnBodyInputWidget

        return OnBodyInputWidget(self, parent, data)

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

    def validate_context(self, ctx: QueryContext) -> None:
        if not self.body_name:
            raise InvalidContext("Enter a body before searching.")


# ---- System predicate (distance in space) ----------------------------------


def _light_years_fragment(
    x0: float, y0: float, z0: float, distance_ly: float
) -> tuple[str, list[Any]]:
    """Euclidean light-year radius centred on ``(x0, y0, z0)``.

    Shared by the current-star and named-star variants so the search is written
    once: the only thing that differs between them is *where* the centre comes
    from. A system with any missing coordinate cannot have a distance computed,
    so it fits *any* radius -- better to show it than to drop it.
    """
    dist_sq = distance_ly**2
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


class WithinLightYears(Predicate):
    """Within ``distance_ly`` light-years of the current system (Euclidean).

    Points at ``star_systems``; the centre comes from ``ctx.current_system_coords``
    (filled from FSDJump / CarrierJump / Location on arrival). This is the
    "search here" case -- the centre star is always the current one, so it
    references no named star.
    """

    label = "Near Current Star"
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

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.numeric import NumericInputWidget

        return NumericInputWidget(
            owner=self,
            parent=parent,
            data=data,
            leaf_cls=WithinLightYears,
            field="distance_ly",
            label="Search Radius",
            unit="ly",
        )

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if self.distance_ly is None or ctx.current_system_coords is None:
            return "1 = 1", []
        return _light_years_fragment(*ctx.current_system_coords, self.distance_ly)

    def validate_context(self, ctx: QueryContext) -> None:
        if self.distance_ly is None:
            raise InvalidContext("Enter a light-year radius before searching.")
        if ctx.current_system_coords is None:
            raise InvalidContext(
                "Searching near your current star needs the current system's "
                "coordinates -- start Elite (or load a location) first."
            )


class WithinLightYearsOfStar(Predicate):
    """Within ``distance_ly`` light-years of a *named* star (Euclidean).

    The centre is looked up in ``ctx.star_coords`` (the engine resolves it
    against the DB, and via the resolver callback -- online sources, inserting
    any newly found coordinates back into the DB). This is the general case;
    :class:`WithinLightYears` is the current star as a special case, so the
    search is written once in :func:`_light_years_fragment`.
    """

    label = "Near Any Star"
    serial_name = "within_light_years_of_star"

    def __init__(
        self, distance_ly: float | None = None, star_name: str | None = None
    ) -> None:
        self.distance_ly = distance_ly
        self.star_name = star_name

    def describe(self) -> str:
        if self.distance_ly is None:
            return self.label
        return f"within {self.distance_ly:.1f} ly of {self.star_name or '?'}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.serial_name,
            "distance_ly": self.distance_ly,
            "star_name": self.star_name,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(data.get("distance_ly"), data.get("star_name"))

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.star_distance import StarDistanceInputWidget

        return StarDistanceInputWidget(self, parent, data)

    def validate_context(self, ctx: QueryContext) -> None:
        if self.distance_ly is None or self.star_name is None:
            raise InvalidContext("Enter a radius and a star before searching.")

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if self.distance_ly is None or self.star_name is None:
            return "1 = 1", []
        coords = ctx.star_coords.get(self.star_name)
        if coords is None:
            # The engine is supposed to have resolved this star (and invoked the
            # resolver callback) before running. A missing centre here means the
            # lookup failed -- surface this loudly rather than silently match
            # nothing.
            raise StarNotFoundError(self.star_name)
        return _light_years_fragment(*coords, self.distance_ly)

    def referenced_stars(self) -> set[str]:
        return {self.star_name} if self.star_name else set()


# ---- System-scope predicates (exact name) ----------------------------------
# Exact-name analogues of the light-year radius search. ``WithinLightYears`` and
# ``WithinLightYearsOfStar`` scope by *distance* to a centre star; these scope by
# *name equality* instead, so a search can name a system as tightly as it wants.


class SearchInExactSystem(Predicate):
    """Match spots in exactly one named system (``star_name = ?``).

    The exact-name analogue of :class:`WithinLightYears`. Unlike the engine's
    ``system`` scope argument it is a first-class tree node, so it composes with
    ``And`` / ``Or`` / ``Not`` (e.g. "in Sol or Kepler-442"). When unset it
    matches every system.
    """

    label = "In System"
    serial_name = "search_in_exact_system"

    def __init__(self, system_name: str | None = None) -> None:
        self.system_name = system_name

    def describe(self) -> str:
        if self.system_name is None:
            return self.label
        return f"in {self.system_name}"

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name, "system_name": self.system_name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls(data.get("system_name"))

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if self.system_name is None:
            return "1 = 1", []
        return "star_systems.star_name = ?", [self.system_name]

    def validate_context(self, ctx: QueryContext) -> None:
        if self.system_name is None:
            raise InvalidContext("Enter a system name before searching.")

    def referenced_stars(self) -> set[str]:
        # Names the system so the engine resolves it up front: if it is not in
        # the local DB the resolver fetches it online (coordinates, tritium
        # rings, ...) and persists it, so this exact-name search succeeds
        # transparently instead of silently returning nothing.
        return {self.system_name} if self.system_name else set()

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.system import SystemInputWidget

        return SystemInputWidget(self, parent, data)


class SearchInCurrentSystem(Predicate):
    """Match spots in the player's current system.

    Renders ``star_systems.star_name = ?`` against ``ctx.current_system_name``.
    The exact-name analogue of :class:`WithinLightYears` (which searches a
    radius around the current star instead). When no current system is known it
    matches every system (there is no "current" to restrict to).
    """

    label = "In Current System"
    serial_name = "search_in_current_system"

    def describe(self) -> str:
        return self.label

    def to_dict(self) -> dict[str, Any]:
        return {"type": self.serial_name}

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Predicate:
        return cls()

    def sql(self, ctx: QueryContext) -> tuple[str, list[Any]]:
        if ctx.current_system_name is None:
            return "1 = 1", []
        return "star_systems.star_name = ?", [ctx.current_system_name]

    def validate_context(self, ctx: QueryContext) -> None:
        if ctx.current_system_name is None:
            raise InvalidContext(
                "Searching your current system needs the current system -- "
                "start Elite (or load a location) first."
            )

    def make_widget(self, parent: Any, *, data: Any):
        from .query_builder.widgets.current_system import CurrentSystemInfoWidget

        return CurrentSystemInfoWidget(self, parent, data)


# ---- Registry --------------------------------------------------------------

# Predicate classes available in the "add condition" menu, in display order.
# The UI builds a blank instance (``cls()``) to read ``describe()`` and pairs it
# with the class so a new one can be created on pick -- no UI-side text.
KNOWN_PREDICATES: list[type[Predicate]] = [
    Within,
    WithinLightYears,
    WithinLightYearsOfStar,
    SearchInExactSystem,
    SearchInCurrentSystem,
    MineralIs,
    OnBody,
    HasTritiumRing,
    IsTemporary,
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
    WithinLightYearsOfStar.serial_name: WithinLightYearsOfStar,
    SearchInExactSystem.serial_name: SearchInExactSystem,
    SearchInCurrentSystem.serial_name: SearchInCurrentSystem,
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
