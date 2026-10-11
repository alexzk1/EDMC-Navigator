"""Tests for the pure query-builder model (:mod:`query_builder.render`).

These pin the one-way conversions that turn builder state into a predicate tree
(``build``) and split a tree back into builder state (`load`). The builder
expression shape is::

    top_not? Or(
        line_not? And(widget, widget, ...),
        line_not? And(widget, ...),
        ...
    )

Lines are OR'ed, widgets within a line are AND'ed, and ``Not`` may wrap a
widget, a whole line, or the entire builder. Everything here is pure data -- no
tkinter, no display -- so it is testable headlessly.
"""

from surface_navigator.predicates import (
    And,
    MineralIs,
    Not,
    Or,
    OnBody,
    Predicate,
    WithinLightYears,
)
from surface_navigator.query_builder.render import (
    BuilderState,
    LineNode,
    WidgetNode,
    build,
    load,
)


# ---- build: assembling a tree from state ----------------------------------


def test_build_empty_state_returns_none():
    """No non-empty line means nothing to search for -> None (keeps Run inert)."""
    assert build(BuilderState(lines=[])) is None
    assert build(BuilderState(lines=[LineNode(widgets=[])])) is None


def test_build_single_widget_wraps_in_or_and_and():
    """A lone widget becomes ``Or(And(widget))`` -- the canonical one-line form."""
    state = BuilderState(lines=[LineNode(widgets=[WidgetNode(MineralIs("iridium"))])])
    result = build(state)
    assert isinstance(result, Or)
    inner = result.predicates[0]
    assert isinstance(inner, And)
    assert inner.predicates == [MineralIs("iridium")]


def test_build_multiple_widgets_in_a_line_are_anded():
    state = BuilderState(
        lines=[
            LineNode(
                widgets=[
                    WidgetNode(MineralIs("iridium")),
                    WidgetNode(OnBody("Earth")),
                ]
            )
        ]
    )
    result = build(state)
    assert isinstance(result, Or)
    assert isinstance(result.predicates[0], And)
    assert result.predicates[0].predicates == [MineralIs("iridium"), OnBody("Earth")]


def test_build_multiple_lines_are_ored():
    state = BuilderState(
        lines=[
            LineNode(widgets=[WidgetNode(MineralIs("iridium"))]),
            LineNode(widgets=[WidgetNode(OnBody("Earth"))]),
        ]
    )
    result = build(state)
    assert isinstance(result, Or)
    assert len(result.predicates) == 2
    assert result.predicates[0] == And(MineralIs("iridium"))
    assert result.predicates[1] == And(OnBody("Earth"))


def test_build_skips_empty_lines_between_filled_ones():
    state = BuilderState(
        lines=[
            LineNode(widgets=[]),
            LineNode(widgets=[WidgetNode(MineralIs("iridium"))]),
            LineNode(widgets=[]),
        ]
    )
    result = build(state)
    assert isinstance(result, Or)
    assert len(result.predicates) == 1


def test_build_widget_not_wraps_the_widget():
    state = BuilderState(
        lines=[LineNode(widgets=[WidgetNode(MineralIs("iridium"), not_=True)])]
    )
    result = build(state)
    assert isinstance(result, Or)
    assert isinstance(result.predicates[0], And)
    assert isinstance(result.predicates[0].predicates[0], Not)


def test_build_line_not_wraps_the_whole_and():
    state = BuilderState(
        lines=[
            LineNode(
                widgets=[WidgetNode(MineralIs("iridium"))],
                not_=True,
            )
        ]
    )
    result = build(state)
    assert isinstance(result, Or)
    assert isinstance(result.predicates[0], Not)


def test_build_top_not_wraps_the_whole_or():
    state = BuilderState(
        lines=[LineNode(widgets=[WidgetNode(MineralIs("iridium"))])],
        top_not=True,
    )
    result = build(state)
    assert isinstance(result, Not)
    assert isinstance(result.predicate, Or)


# ---- load: splitting a tree back into state -------------------------------


def test_load_splits_or_of_two_lines():
    tree = Or(And(MineralIs("iridium")), And(OnBody("Earth")))
    state = load(tree)
    assert len(state.lines) == 2
    assert state.lines[0].widgets == [WidgetNode(MineralIs("iridium"))]
    assert state.lines[1].widgets == [WidgetNode(OnBody("Earth"))]
    assert state.top_not is False


def test_load_single_widget_without_or_becomes_one_line():
    """A bare leaf (no Or) is a single one-widget line so it round-trips."""
    state = load(MineralIs("iridium"))
    assert len(state.lines) == 1
    assert state.lines[0].widgets == [WidgetNode(MineralIs("iridium"))]


def test_load_unwraps_widget_not():
    state = load(And(Not(MineralIs("iridium"))))
    assert state.lines[0].widgets == [WidgetNode(MineralIs("iridium"), not_=True)]


def test_load_unwraps_line_not():
    state = load(Not(And(MineralIs("iridium"))))
    assert state.lines[0].not_ is True
    assert state.lines[0].widgets == [WidgetNode(MineralIs("iridium"))]


def test_load_unwraps_top_not():
    state = load(Not(Or(And(MineralIs("iridium")))))
    assert state.top_not is True
    assert len(state.lines) == 1
    assert state.lines[0].widgets == [WidgetNode(MineralIs("iridium"))]


def test_load_top_not_requires_enclosing_or():
    """A ``Not`` over an ``Or`` is top-level; a ``Not`` over a lone ``And`` is a
    line-level negation -- the two are not interchangeable on load."""
    top = load(Not(Or(And(MineralIs("iridium")))))
    assert top.top_not is True
    assert top.lines[0].not_ is False

    line = load(Not(And(MineralIs("iridium"))))
    assert line.top_not is False
    assert line.lines[0].not_ is True


def test_load_nested_not_matches_builder_shape():
    """``NOT (NOT A AND B)`` -> one NOT'd line with a NOT'd widget and a plain one.

    The outer ``Not`` wraps a lone ``And`` (no enclosing ``Or``), so it is the
    line's own negation, not a top-level one.
    """
    tree = Not(And(Not(MineralIs("iridium")), OnBody("Earth")))
    state = load(tree)
    assert state.top_not is False
    line = state.lines[0]
    assert line.not_ is True
    assert line.widgets == [
        WidgetNode(MineralIs("iridium"), not_=True),
        WidgetNode(OnBody("Earth")),
    ]


# ---- round-trip: build(load(build(s))) is stable --------------------------


def _roundtrip(state: BuilderState) -> Predicate:
    return build(load(build(state)))


def test_roundtrip_preserves_simple_line():
    state = BuilderState(
        lines=[LineNode(widgets=[WidgetNode(MineralIs("iridium"))])]
    )
    assert _roundtrip(state) == build(state)


def test_roundtrip_preserves_multiple_lines():
    state = BuilderState(
        lines=[
            LineNode(widgets=[WidgetNode(MineralIs("iridium"))]),
            LineNode(
                widgets=[
                    WidgetNode(OnBody("Earth")),
                    WidgetNode(WithinLightYears(10.0), not_=True),
                ]
            ),
        ]
    )
    assert _roundtrip(state) == build(state)


def test_roundtrip_preserves_line_and_top_not():
    state = BuilderState(
        lines=[
            LineNode(widgets=[WidgetNode(MineralIs("iridium"), not_=True)]),
            LineNode(widgets=[WidgetNode(OnBody("Earth"))], not_=True),
        ],
        top_not=True,
    )
    assert _roundtrip(state) == build(state)


def test_roundtrip_drops_previously_empty_lines():
    """An empty line contributes nothing, so it is not resurrected on load."""
    original = BuilderState(
        lines=[
            LineNode(widgets=[]),
            LineNode(widgets=[WidgetNode(MineralIs("iridium"))]),
        ]
    )
    assert _roundtrip(original) == build(original)
