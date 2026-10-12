"""HTTP clients for external star data (EDSM + Spansh) and the DB resolver.

Two concerns live here on purpose, so each can evolve independently:

* :class:`StarApiClient` is a **stateless** layer of raw requests. It knows
  nothing about the database or about tritium -- it just turns a name / id64
  into a parsed JSON dict (or ``{}`` on any failure). Callers reuse the methods
  directly, e.g. to build ring tooltips from :meth:`StarApiClient.fetch_bodies`.

* :class:`StarDataResolver` is the concrete implementation of the
  ``StarResolver`` contract (see :mod:`database`): given a *system name*, it
  fetches coordinates + world key from EDSM and tritium rings from Spansh, and
  persists both into the DB. It is a pure side effect with no return value --
  the engine never reads anything back from the call, it only re-queries the DB
  afterwards.

Only **two** network round-trips happen per resolve:

    EDSM ``/api-v1/system``  ->  ``id64`` + ``coords``  (world key + xyz)
    Spansh ``/api/dump/{id64}`` -> full dump (used to find tritium rings)

The EDSM ``/api-system-v1/bodies`` request is available through
:meth:`StarApiClient.fetch_bodies` but is **not** part of the resolve path --
Spansh is free, so we do not gate the tritium lookup behind an icy-ring check.
"""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Protocol, runtime_checkable

from .nav_config import STAR_API_TIMEOUT_SEC

logger = logging.getLogger("SurfaceNavigator")


@runtime_checkable
class StarClient(Protocol):
    """Structural type for the external-data dependency of :class:`StarDataResolver`.

    Satisfied by :class:`StarApiClient` and by any test double exposing the same
    two callables -- the resolver only ever calls
    ``fetch_system(name, timeout)`` and ``fetch_dump(id64, timeout)``.
    """

    def fetch_system(self, system_name: str, timeout: int = ...) -> dict[str, Any]: ...
    def fetch_dump(self, system_id64: int, timeout: int = ...) -> dict[str, Any]: ...

EDSM_SYSTEM_URL = "https://www.edsm.net/api-v1/system"
EDSM_BODIES_URL = "https://www.edsm.net/api-system-v1/bodies"
SPANSH_DUMP_URL = "https://www.spansh.co.uk/api/dump/{id64}"

# Signal key that marks a tritium (He3) ring in the Spansh dump.
_TRITIUM_SIGNAL = "Tritium"


class StarApiClient:
    """Stateless HTTP layer over EDSM and Spansh star data.

    The fetch methods are ordinary instance methods so the class satisfies the
    ``StarClient`` protocol (see above) -- the resolver takes any matching
    double. ``_get_json`` stays a ``@staticmethod``: it is a low-level helper
    with no state to bind. Callers can still reuse the raw requests (for
    tooltips, previews, tests) via ``StarApiClient()``. A failed request --
    network error, HTTP error, or non-JSON body -- returns an empty dict rather
    than raising, so callers can treat "no data" and "unreachable" uniformly.
    """

    @staticmethod
    def _get_json(url: str, timeout: int = STAR_API_TIMEOUT_SEC) -> dict[str, Any]:
        """Performs a GET and returns parsed JSON, or ``{}`` on any failure."""
        req = urllib.request.Request(url, headers={"User-Agent": "EDMC-Navigator/1.0"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            logger.debug("StarApiClient GET %s failed: %s", url, e)
            return {}
        except UnicodeDecodeError as e:
            logger.debug("StarApiClient non-UTF8 response from %s: %s", url, e)
            return {}

        raw = raw.strip()
        if not raw:
            return {}
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            logger.debug("StarApiClient non-JSON response from %s", url)
            return {}

    def fetch_system(
        self, system_name: str, timeout: int = STAR_API_TIMEOUT_SEC
    ) -> dict[str, Any]:
        """``GET /api-v1/system`` -- EDSM internal ``id``, ``id64`` (Elite world
        key) and ``coords`` (``{x, y, z}``).

        ``id64`` is the value we feed to Spansh; ``coords`` are the xyz we
        persist into the DB.
        """
        params = urllib.parse.urlencode(
            {
                "systemName": system_name,
                "showId": 1,
                "showCoordinates": 1,
                "showInformation": 1,
                "showPrimaryStar": 1,
            }
        )
        return StarApiClient._get_json(f"{EDSM_SYSTEM_URL}?{params}", timeout)

    def fetch_bodies(
        self, system_name: str, timeout: int = STAR_API_TIMEOUT_SEC
    ) -> dict[str, Any]:
        """``GET /api-system-v1/bodies`` -- the system's bodies and their rings.

        Used for ring tooltips / previews, not for the resolve path.
        """
        params = urllib.parse.urlencode({"systemName": system_name})
        return StarApiClient._get_json(f"{EDSM_BODIES_URL}?{params}", timeout)

    def fetch_dump(
        self, system_id64: int, timeout: int = STAR_API_TIMEOUT_SEC
    ) -> dict[str, Any]:
        """``GET /api/dump/{id64}`` -- the full system dump (bodies, rings and
        their mining signals)."""
        return StarApiClient._get_json(
            SPANSH_DUMP_URL.format(id64=system_id64), timeout
        )


class StarDataResolver:
    """Concrete :data:`StarResolver` implementation.

    On ``resolver(system_name)`` it performs exactly two requests -- EDSM for
    the world key + coordinates, Spansh for the tritium rings -- and persists
    both into the DB. Anything that comes back empty (unknown system, missing
    ``id64``, unreachable Spansh) is logged and skipped, never raised: the
    engine only cares whether the DB holds the data afterwards.
    """

    def __init__(
        self,
        db_manager: Any,
        *,
        client: StarClient | None = None,
        timeout: int = STAR_API_TIMEOUT_SEC,
    ) -> None:
        self._db = db_manager
        self._client = client if client is not None else StarApiClient()
        self._timeout = timeout

    def __call__(self, system_name: str) -> None:
        """Resolve ``system_name`` and persist its data into the DB."""
        self._resolve(system_name)

    def _resolve(self, system_name: str) -> None:
        system_data = self._client.fetch_system(system_name, self._timeout)
        system_id64 = system_data.get("id64")
        coords = system_data.get("coords")

        if system_id64 is not None and coords is not None:
            self._persist_coords_and_key(system_name, system_id64, coords)

        if system_id64 is None:
            # EDSM knows nothing usable -- no world key, no Spansh to call.
            logger.debug("StarDataResolver: no id64 for %r", system_name)
            return

        self._record_tritium_rings(system_name, system_id64)

    def _persist_coords_and_key(
        self, system_name: str, system_id64: int, coords: dict[str, Any]
    ) -> None:
        from .models import StarSystem

        x = coords.get("x")
        y = coords.get("y")
        z = coords.get("z")
        # ``_get_or_create_star`` both creates a new row and backfills the
        # still-NULL columns of an existing one -- exactly what a resolve into
        # an unknown system needs. ``update_existing_star_coords`` would refuse
        # to touch a system that is not in the table yet.
        self._db._get_or_create_star(
            StarSystem(
                star_name=system_name,
                x=x,
                y=y,
                z=z,
                systemid=system_id64,
            )
        )

    def _record_tritium_rings(self, system_name: str, system_id64: int) -> None:
        """Records every ring that carries a tritium signal as a spot.

        Idempotent per ring (the DB dedupes by star + ring name), so a repeat
        resolve is a no-op once the rings are known.
        """
        from .models import RingScanStatus, StarSystem

        dump = self._client.fetch_dump(system_id64, self._timeout)
        if not dump:
            logger.debug("StarDataResolver: empty Spansh dump for %r", system_name)
            return

        system = StarSystem(star_name=system_name, systemid=system_id64)
        for body in dump.get("bodies", []) or []:  # type: ignore
            for ring in body.get("rings", []) or []:  # type: ignore
                signal = self._find_tritium_signal(ring)  # type: ignore
                if signal is None:
                    continue
                ring_name: str = ring.get("name") or ""  # type: ignore
                if not ring_name:
                    continue
                # ``name_from_log`` keeps the exact string from the dump;
                # ``fuzzy_matched_name`` is the canonical lowercased commodity
                # name (the DB compares against "tritium").
                self._db.ensure_tritium_recorded(
                    RingScanStatus(
                        system=system,
                        body=ring_name,  # type: ignore
                        name_from_log=signal,
                        fuzzy_matched_name=_TRITIUM_SIGNAL.lower(),
                    )
                )

    @staticmethod
    def _find_tritium_signal(ring: dict[str, Any]) -> str | None:
        """Returns the ring's tritium signal key (exact case) or ``None``."""
        signals = (ring.get("signals") or {}).get("signals") or {}  # type: ignore
        for key in signals:  # type: ignore
            if str(key).lower() == _TRITIUM_SIGNAL.lower():  # type: ignore
                return str(key)  # type: ignore
        return None
