"""Pure (UI-independent) model + conversion for the query builder.

The builder window and its widgets translate to/from :class:`BuilderState`;
this module owns the one-way conversions so they stay testable with no
display. ``build`` turns state into a predicate tree; ``load`` splits a tree
back into state, unwrapping ``Not`` at every level.

The builder expression shape is::

    top_not? Or(
        line_not? And(widget, widget, ...),
        line_not? And(widget, ...),
        ...
    )

Lines are OR'ed, widgets within a line are AND'ed, and ``Not`` may wrap a
widget, a whole line, or the entire builder.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from ..predicates import And, Not, Or, Predicate

__all__ = [
    "BuilderState",
    "LineNode",
    "WidgetNode",
    "build",
    "load",
]


@dataclass
class WidgetNode:
    """A single predicate inside a line, plus whether it is negated."""

    predicate: Predicate
    not_: bool = False


@dataclass
class LineNode:
    """A group of widgets AND'ed together, plus whether the group is negated."""

    widgets: list[WidgetNode] = field(default_factory=list[WidgetNode])
    not_: bool = False


@dataclass
class BuilderState:
    """The whole builder: lines OR'ed, plus whether the whole thing is negated."""

    lines: list[LineNode] = field(default_factory=list[LineNode])
    top_not: bool = False


def _unwrap_not(node: Predicate) -> tuple[bool, Predicate]:
    """Return ``(was_not, inner)`` -- one leading ``Not`` unwrapped, if present."""
    if isinstance(node, Not):
        return True, node.predicate
    return False, node


def build(state: BuilderState) -> Predicate | None:
    """Assemble a predicate tree from builder state.

    Empty lines contribute nothing. Returns ``None`` when there is nothing to
    search (no non-empty line), so the UI can keep Run inert rather than run a
    match-all query.
    """
    or_children: list[Predicate] = []
    for line in state.lines:
        if not line.widgets:
            continue
        and_children = [
            Not(w.predicate) if w.not_ else w.predicate for w in line.widgets
        ]
        and_pred: Predicate = And(*and_children)
        if line.not_:
            and_pred = Not(and_pred)
        or_children.append(and_pred)
    if not or_children:
        return None
    result: Predicate = Or(*or_children)
    if state.top_not:
        result = Not(result)
    return result


def load(tree: Predicate) -> BuilderState:
    """Split a predicate tree into builder state, unwrapping ``Not`` per level.

    A bare predicate (not wrapped in ``Or``) becomes a single one-widget line,
    so ``build(load(build(s)))`` reproduces any builder-produced tree.

    The outer ``Not`` is only a *top-level* negation when it wraps an ``Or``; a
    ``Not`` around a lone ``And`` (a single, un-OR'd line) is that line's own
    negation, so it is reported as ``line.not_`` rather than ``top_not``. This
    keeps a loaded tree's negations where the UI shows them.
    """
    root = tree
    top_not = False
    if isinstance(root, Not) and isinstance(root.predicate, Or):
        top_not = True
        root = root.predicate

    or_children: list[Predicate] = root.predicates if isinstance(root, Or) else [root]

    lines: list[LineNode] = []
    for or_child in or_children:
        line_not, child = _unwrap_not(or_child)
        widgets: list[WidgetNode] = []
        if isinstance(child, And):
            for w_pred in child.predicates:
                w_not, inner = _unwrap_not(w_pred)
                widgets.append(WidgetNode(predicate=inner, not_=w_not))
        else:
            # A bare predicate in the Or (or a single-predicate query): one
            # widget, carrying the line's negation if any.
            widgets.append(WidgetNode(predicate=child, not_=line_not))
        lines.append(LineNode(widgets=widgets, not_=line_not))

    return BuilderState(lines=lines, top_not=top_not)
