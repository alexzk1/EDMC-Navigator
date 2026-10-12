"""Tests for the builder's live "where the player is" tracking.

The query-builder window normalises its host input into two attributes:
``current_location`` (a ``PlayerLocation`` on a body, None in space) and
``current_system`` (the current star, always known while the game runs). The
old code only read ``current_location`` from the constructor and never updated
it, so two bugs followed:

  * When the player is *in space* there is no ``current_location`` at all, so
    ``In Current System`` degraded to ``1 = 1`` (matched the whole DB) even
    though the current system is known.
  * While the window stayed open the player kept moving, so a snapshot taken at
    open time went stale (fly for an hour, then RUN QUERY).

Both are fixed by seeding from the constructor and then subscribing to
``POSITION_UPDATED`` (which carries ``system`` -- always with ``.star_name``,
even in space -- plus ``location``). These tests guard that behaviour without
dragging a full Tk window through the test suite: the builder is built via
``__new__`` and the handful of attributes the methods touch are set by hand.
"""

import tkinter as tk

# ``icons_cache`` builds ``PhotoImage``s at import time, which needs a default
# Tk root to exist first. Create one here -- this mirrors the app, where the GUI
# root is created before any icon is loaded.
_root = tk.Tk()

from surface_navigator.events_dispatcher import EventParams, KnownEvents, dispatcher
from surface_navigator.models import StarSystem
from surface_navigator.player_location import PlayerLocation, SurfacePoint
from surface_navigator.predicates import Predicate, SearchInCurrentSystem
from surface_navigator.query_builder.base import DataContext
from surface_navigator.query_builder.builder_window import QueryBuilderWindow


def _builder() -> QueryBuilderWindow:
    """A builder without the heavy ``__init__`` -- just the attributes touched
    by the methods under test."""
    w = QueryBuilderWindow.__new__(QueryBuilderWindow)
    w.current_location = None
    w.current_system = None
    w._lines: list = []  # type: ignore
    w.data = DataContext(db_manager=None, current_system_name=None)
    return w


def _in_space_event(system_name: str) -> EventParams:
    """A POSITION_UPDATED for a player sitting in space (no body)."""
    return EventParams(system=StarSystem(star_name=system_name), location=None)


def test_in_space_system_sets_current_name():
    """The core regression: in space there is no location, but the system is
    known via ``data.system`` -- the builder must pick it up."""
    w = _builder()
    w._on_position_updated(_in_space_event("Sol"))  # type: ignore
    assert w.current_system is not None
    assert w.current_system.star_name == "Sol"


def test_build_ctx_scopes_current_system_predicate():
    """``_build_ctx`` must feed the live system name into the context so the
    predicate does not collapse to ``1 = 1``."""
    w = _builder()
    w._on_position_updated(_in_space_event("Sol"))  # type: ignore
    ctx = w._build_ctx()  # type: ignore
    assert ctx.current_system_name == "Sol"
    frag, params = SearchInCurrentSystem().sql(ctx)
    assert frag == "star_systems.star_name = ?"
    assert params == ["Sol"]


def test_build_ctx_still_scoped_before_first_event():
    """If the constructor already had the system (on-body seed), it is used
    directly, before any event arrives."""
    location = PlayerLocation(
        star_system=StarSystem(star_name="Kepler-442"),
        body_name="Aurelia",
        player_coord=SurfacePoint(1.0, 2.0),
        radius_meters=1234.0,
    )
    w = _builder()
    w.current_location = location
    w.current_system = location.star_system
    ctx = w._build_ctx()  # type: ignore
    assert ctx.current_system_name == "Kepler-442"
    frag, params = SearchInCurrentSystem().sql(ctx)
    assert frag == "star_systems.star_name = ?"
    assert params == ["Kepler-442"]


def test_location_star_system_used_when_present():
    """When the event carries an on-body location, its ``star_system`` wins
    (deterministic with ``data.system`` -- they are the same object)."""
    w = _builder()
    location = PlayerLocation(
        star_system=StarSystem(star_name="Wolf 359"),
        body_name="Aurelia",
        player_coord=SurfacePoint(1.0, 2.0),
    )
    w._on_position_updated(EventParams(location=location))  # type: ignore
    assert w.current_system is not None
    assert w.current_system.star_name == "Wolf 359"


# -- widget re-render --------------------------------------------------------


class _FakeWidget:
    """Stand-in for a predicate editor that records whether it was reloaded."""

    def __init__(self, predicate: Predicate) -> None:
        self._predicate = predicate
        self.loaded = 0

    def get_predicate(self):
        return self._predicate

    def load_leaf(self, pred: Predicate):
        self.loaded += 1


class _FakeLine:
    def __init__(self, widgets) -> None:  # type: ignore
        self._widgets = [(None, w) for w in widgets]  # type: ignore

    def iter_widgets(self):  # type: ignore
        for _container, widget in self._widgets:  # type: ignore
            yield widget


def test_current_system_widget_rerenders_on_name_change():
    w = _builder()
    widget = _FakeWidget(SearchInCurrentSystem())
    w._lines = [_FakeLine([widget])]  # type: ignore
    w._on_position_updated(_in_space_event("Sol"))  # type: ignore
    assert widget.loaded == 1


def test_current_system_widget_not_rerendered_when_unchanged():
    w = _builder()
    w.current_system = StarSystem(star_name="Sol")  # already known
    w.data.current_system_name = "Sol"
    widget = _FakeWidget(SearchInCurrentSystem())
    w._lines = [_FakeLine([widget])]  # type: ignore
    w._on_position_updated(_in_space_event("Sol"))  # type: ignore
    assert widget.loaded == 0


# -- dispatcher subscribe / unsubscribe --------------------------------------


def test_subscribe_then_unsubscribe_stops_receiving():
    calls: list = []  # type: ignore
    listener = lambda data: calls.append(data)  # type: ignore
    dispatcher.subscribe(KnownEvents.POSITION_UPDATED, listener)  # type: ignore
    dispatcher.dispatch(
        KnownEvents.POSITION_UPDATED, EventParams(system=StarSystem(star_name="Sol"))
    )
    assert len(calls) == 1  # type: ignore

    dispatcher.unsubscribe(KnownEvents.POSITION_UPDATED, listener)  # type: ignore
    dispatcher.dispatch(
        KnownEvents.POSITION_UPDATED,
        EventParams(system=StarSystem(star_name="Wolf 359")),
    )
    assert len(calls) == 1  # type: ignore


def test_unsubscribe_missing_is_noop():
    # Removing a callback that was never registered must not raise.
    dispatcher.unsubscribe(KnownEvents.POSITION_UPDATED, lambda data: None)
