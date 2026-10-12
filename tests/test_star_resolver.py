"""Tests for the external-star resolver (``surface_navigator.star_resolver``).

The resolver's job is to turn a *system name* into DB rows: coordinates + world
key from EDSM and tritium rings from Spansh. These tests exercise that
resolver-DB wiring with **fake server responses** -- no real network, so we
neither depend on EDSM/Spansh being up nor risk getting rate-limited.

One test (``test_get_json_parses_remote_body``) spins up a local
``http.server`` to cover the raw parsing path against a real socket.
"""

import http.server
import json
import threading
from unittest.mock import patch
from typing import Any

from surface_navigator.database import DatabaseManager
from surface_navigator.models import SurfaceSpotFlags
from surface_navigator.star_resolver import StarApiClient, StarDataResolver


# ---- fakes -----------------------------------------------------------------


class FakeClient:
    """Drop-in for ``StarApiClient`` with canned responses.

    The resolver calls ``fetch_system(name, timeout)`` and
    ``fetch_dump(id64, timeout)``; instance methods match that signature while
    letting each test track how many times the resolver reached out.
    """

    def __init__(
        self, system: dict[str, Any] | None = None, dump: dict[str, Any] | None = None
    ) -> None:
        self._system = system if system is not None else {}
        self._dump = dump if dump is not None else {}
        self.system_calls = 0
        self.dump_calls = 0

    def fetch_system(self, system_name: str, timeout: int = 20) -> dict[str, Any]:
        self.system_calls += 1
        return self._system

    def fetch_dump(self, system_id64: int, timeout: int = 20) -> dict[str, Any]:
        self.dump_calls += 1
        return self._dump


def _system_response(
    id64: int = 999999999, x: float = 12.5, z: float = 88.25
) -> dict[str, Any]:
    return {
        "name": "Kepler-442",
        "id": 12345,
        "id64": id64,
        "coords": {"x": x, "y": -3.0, "z": z},
    }


def _dump_with_tritium() -> dict[str, Any]:
    """Two icy rings: one carries a Tritium signal, the other does not.

    Mirrors the real Spansh dump: everything is nested under a top-level
    ``system`` object (``{"system": {"bodies": [...]}}``), and ring names carry
    the parent system as a prefix.
    """
    return {
        "system": {
            "bodies": [
                {
                    "name": "Kepler-442 b",
                    "rings": [
                        {
                            "name": "Kepler-442 b A Ring",
                            "type": "Icy",
                            "signals": {"signals": {"Palladium": 1, "Tritium": 3}},
                        },
                        {
                            "name": "Kepler-442 b B Ring",
                            "type": "Icy",
                            "signals": {"signals": {"Iridium": 2}},
                        },
                    ],
                }
            ]
        }
    }


def _count_tritium_rings(db: DatabaseManager, system: str) -> int:
    conn = db._get_connection()  # type: ignore
    row = conn.execute(
        "SELECT COUNT(*) FROM surface_spots sp "
        "JOIN star_systems ss ON sp.star_id = ss.star_id "
        "WHERE ss.star_name = ? AND sp.flags = ?",
        (system, SurfaceSpotFlags.TRITIUM_RING_PRESENT.value),
    ).fetchone()
    return row[0]


def _has_tritium_ring_spot(db: DatabaseManager, ring_name: str) -> bool:
    conn = db._get_connection()  # type: ignore
    row = conn.execute(
        "SELECT COUNT(*) FROM surface_spots WHERE body_name = ? AND flags = ?",
        (ring_name, SurfaceSpotFlags.TRITIUM_RING_PRESENT.value),
    ).fetchone()
    return row[0] > 0


# ---- resolver behaviour ----------------------------------------------------


def test_resolver_persists_coords_and_systemid(db: DatabaseManager):
    """A resolve writes xyz + the Elite world key for an unknown system."""
    resolver = StarDataResolver(db, client=FakeClient(system=_system_response()))
    resolver("Kepler-442")

    conn = db._get_connection()  # type: ignore
    x, y, z = conn.execute(
        "SELECT x, y, z FROM star_systems WHERE star_name = ?", ("Kepler-442",)
    ).fetchone()
    assert (x, y, z) == (12.5, -3.0, 88.25)
    sid = conn.execute(
        "SELECT systemid FROM star_systems WHERE star_name = ?", ("Kepler-442",)
    ).fetchone()[0]
    assert sid == 999999999


def test_resolver_records_only_tritium_rings(db: DatabaseManager):
    """Only rings carrying a Tritium signal become spots; the other is skipped."""
    resolver = StarDataResolver(
        db, client=FakeClient(system=_system_response(), dump=_dump_with_tritium())
    )
    resolver("Kepler-442")

    # The Spansh dump prefixes ring names with the system ("Kepler-442 b A
    # Ring"); the resolver strips that prefix, so the stored name is just
    # "b A Ring".
    assert _has_tritium_ring_spot(db, "b A Ring")
    assert not _has_tritium_ring_spot(db, "b B Ring")
    assert _count_tritium_rings(db, "Kepler-442") == 1


def test_resolver_reads_bodies_under_system(db: DatabaseManager):
    """Regression: the Spansh dump nests bodies under ``system``, not at the
    top level. A resolver that reads ``dump["bodies"]`` silently records zero
    rings for every system.

    Also checks the ring-name prefix is stripped: the dump carries
    "Kepler-442 b A Ring" but the stored name is just "b A Ring".
    """
    resolver = StarDataResolver(
        db, client=FakeClient(system=_system_response(), dump=_dump_with_tritium())
    )
    resolver("Kepler-442")

    assert _count_tritium_rings(db, "Kepler-442") == 1
    assert _has_tritium_ring_spot(db, "b A Ring")


def test_resolver_reads_bodies_at_top_level_fallback(db: DatabaseManager):
    """Older Spansh mirrors put ``bodies`` at the top level; the resolver must
    still find them (fall back to ``dump["bodies"]``)."""
    legacy_dump = {
        "bodies": [
            {
                "name": "Kepler-442 b",
                "rings": [
                    {
                        "name": "Kepler-442 b A Ring",
                        "type": "Icy",
                        "signals": {"signals": {"Tritium": 1}},
                    }
                ],
            }
        ]
    }
    resolver = StarDataResolver(
        db, client=FakeClient(system=_system_response(), dump=legacy_dump)
    )
    resolver("Kepler-442")

    assert _count_tritium_rings(db, "Kepler-442") == 1
    assert _has_tritium_ring_spot(db, "b A Ring")


def test_resolver_no_id64_is_a_no_op(db: DatabaseManager):
    """Without a world key we cannot reach Spansh, so nothing is persisted."""
    client = FakeClient(system={})  # no id64, no coords
    resolver = StarDataResolver(db, client=client)
    resolver("Kepler-442")

    assert client.system_calls == 1
    assert client.dump_calls == 0
    conn = db._get_connection()  # type: ignore
    assert (
        conn.execute(
            "SELECT COUNT(*) FROM star_systems WHERE star_name = ?", ("Kepler-442",)
        ).fetchone()[0]
        == 0
    )


def test_resolver_empty_dump_does_not_crash(db: DatabaseManager):
    """A missing/empty Spansh dump still leaves the coords we already fetched."""
    client = FakeClient(system=_system_response(), dump={})
    resolver = StarDataResolver(db, client=client)
    resolver("Kepler-442")

    assert client.dump_calls == 1
    assert _count_tritium_rings(db, "Kepler-442") == 0


def test_resolver_is_idempotent(db: DatabaseManager):
    """Resolving the same system twice does not duplicate tritium rings."""
    client = FakeClient(system=_system_response(), dump=_dump_with_tritium())
    resolver = StarDataResolver(db, client=client)

    resolver("Kepler-442")
    resolver("Kepler-442")

    assert _count_tritium_rings(db, "Kepler-442") == 1
    assert client.system_calls == 2
    assert client.dump_calls == 2


# ---- edsm_system_url (results-table "Visit on EDSM") -----------------------


def test_edsm_system_url_builds_url_from_edsm_id() -> None:
    """The link uses EDSM's *internal* ``id`` (not the world key ``id64``)."""
    with patch.object(StarApiClient, "fetch_system", return_value={"id": 12345}):
        url = StarApiClient().edsm_system_url("Sol", timeout=1)
    assert url == "https://www.edsm.net/en/system/id/12345/name/Sol"


def test_edsm_system_url_percent_encodes_system_name() -> None:
    """Spaces and punctuation in the system name are percent-encoded."""
    with patch.object(StarApiClient, "fetch_system", return_value={"id": 7}):
        url = StarApiClient().edsm_system_url("LHS 1434 (G 108-71)", timeout=1)
    assert url == "https://www.edsm.net/en/system/id/7/name/LHS%201434%20%28G%20108-71%29"


def test_edsm_system_url_returns_none_when_system_unknown() -> None:
    """Without an ``id`` EDSM knows nothing -- no link to build."""
    with patch.object(StarApiClient, "fetch_system", return_value={}):
        url = StarApiClient().edsm_system_url("Nowhere", timeout=1)
    assert url is None


# ---- raw HTTP parsing (local mock server) ----------------------------------


def test_get_json_parses_remote_body() -> None:
    """``StarApiClient._get_json`` parses a real HTTP JSON body from a socket."""
    payload = json.dumps({"hello": "world"}).encode("utf-8")

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802 (http.server API)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)

        def log_message(self, *args) -> None:  # type: ignore # silence test output
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/?systemName=Sol"
        result = StarApiClient._get_json(url)  # type: ignore[method-access]
    finally:
        server.shutdown()
        thread.join()

    assert result == {"hello": "world"}


def test_get_json_returns_empty_on_non_json_body() -> None:
    """A non-JSON body (e.g. an EDSM error page) yields ``{}``, never raises."""

    class _Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:  # noqa: N802
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"<html>not json</html>")

        def log_message(self, *args) -> None:  # type: ignore
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_address[1]}/"
        result = StarApiClient._get_json(url)  # type: ignore[method-access]
    finally:
        server.shutdown()
        thread.join()

    assert result == {}
