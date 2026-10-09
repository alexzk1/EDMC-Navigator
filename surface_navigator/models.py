from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any

from .spot_flags import SurfaceSpotFlags


@dataclass
class SurfaceSpot:
    """Represents surface spot into DB. It can be just nice views location and/or Rhino mining spot."""

    id: int | None = None
    star_system: str = ""
    body_name: str = ""
    latitude: float = 0.0
    longitude: float = 0.0
    spot_number: int | None = None
    mineral_type: str | None = None  # Fuzzy matched value against dictionary.
    mineral_original: str | None = None  # Original provided value.
    amount: float | None = None
    density: float | None = None
    max_miners: int = 1
    last_visit_time: datetime.datetime | None = None
    notes: str | None = None
    # Bit-field of SurfaceSpotFlags. Stored as INTEGER in the DB; defaults to 0
    # (no flags). ``__post_init__`` normalises the plain int the DB returns into
    # a SurfaceSpotFlags so callers can test membership directly.
    flags: SurfaceSpotFlags = SurfaceSpotFlags(0)  # noqa: RUF009

    def __post_init__(self) -> None:
        # The DB stores flags as a plain INTEGER; coerce so callers always get a
        # SurfaceSpotFlags they can query with ``IS_TEMPORARY_MARK in self.flags``.
        if not isinstance(self.flags, SurfaceSpotFlags):  # type: ignore
            self.flags = SurfaceSpotFlags(int(self.flags))

    def to_dict(self) -> dict[str, Any]:
        return {
            "star_system": self.star_system,
            "body_name": self.body_name,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "spot_number": self.spot_number,
            "mineral_type": self.mineral_type,
            "mineral_original": self.mineral_original,
            "amount": self.amount,
            "density": self.density,
            "max_miners": self.max_miners,
            "last_visit_time": self.last_visit_time.isoformat()
            if self.last_visit_time
            else None,
            "notes": self.notes,
            "flags": self.flags.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SurfaceSpot:
        dt = data.get("last_visit_time")
        if dt and isinstance(dt, str):
            data["last_visit_time"] = datetime.datetime.fromisoformat(dt)
        return cls(**data)


@dataclass
class RingScanStatus:
    """A single ring signal extracted from a ``SAASignalsFound`` journal entry.

    ``system`` is the current ``StarSystem`` (name + coordinates + systemid) so
    the DB can record x/y/z immediately. ``body`` is the ring body name (already
    stripped of its system prefix). ``name_from_log`` is the raw signal ``Type``
    as it arrived in the log; ``fuzzy_matched_name`` is the canonical
    (lowercased) commodity name produced by the fuzzy matcher. The matcher runs
    in the plugin layer (it pulls in EDMC's ``config``), so the DB layer only
    ever sees the already-resolved ``fuzzy_matched_name`` and can stay free of
    heavy imports.
    """

    system: StarSystem
    body: str
    name_from_log: str
    fuzzy_matched_name: str | None = None


@dataclass
class StarSystem:
    """Represents a row in the dedicated ``star_systems`` table.

    Star names are unique in practice, but a handful of systems share a name and
    are only distinguished by ``systemid``. ``systemid`` (and the x/y/z
    coordinates) may be unknown at first and arrive later via streaming
    updates, so they are optional.
    """

    # Database id (key)
    star_id: int | None = None
    # In-Game name
    star_name: str = ""
    # Galaxy coordinates, probed from the servers, probably, could be computed from the systemid.
    x: float | None = None
    y: float | None = None
    z: float | None = None
    # In-game id (world key)
    systemid: int | None = None
