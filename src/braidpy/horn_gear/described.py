# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A horn gear machine written as its graph: which gears mesh with which.

A machine is gears that mesh, so it can be written as the pairs that do:
``A-B B-C C-D D-A`` is four gears in a ring, ``A-B`` two side by side.  A
gear may be given its own number of slots, ``A:6``, anywhere it is named;
the others have as many as the machine's default.

A **split gear** — gears on one axle, turning as one, their horns taking
turns round it, each meeting only its own neighbours, so that the bands
they serve never exchange a carrier
(:mod:`~braidpy.horn_gear.multiband`) — is written as its parts, each a
gear in the pairs, joined on their axle: ``A-B1 B2-C B1+B2`` is the twin
plait, its middle gear of six horns split in two.  A gear may be split in
more parts, ``H1+H2+H3``, its parts as many slots each; and split gears
may be anywhere in the graph.

The rest follows from the graph:

- Two gears that mesh turn opposite ways, so each gear's direction is the
  graph's two colours, the first gear named turning anticlockwise, a split
  gear's parts all one way.  A ring of an odd number of gears cannot turn
  at all, and is refused.
- Where the gears stand is where the layout puts them
  (:func:`~braidpy.horn_gear.layout.compute_layout`, from the graph and the
  gears' sizes alone, a split gear's parts at one centre, as large as the
  whole); in a tree of gears, each neighbour of a split gear's part where a
  horn of that part comes round.
- Each gear's contacts are spread round it as evenly as its slots allow, in
  the order the layout puts them, its first contact named at slot 0.

Where it feeds axial yarns is written as the places, ``B`` up a gear's
spindle or ``A-B-C-D`` down the hole of a ring of gears
(:func:`read_axials`); the carriers it starts with, where it does not load
itself, as ``A:0 B:2`` (:func:`read_loading`).  The catalogue's machines
are written so (:mod:`braidpy.machine_catalog`).

:func:`graph_of` writes a machine back as its graph, :func:`axials_of` and
:func:`loading_of` its axials and a loading.  A machine written so and read
again is the same machine, its slots perhaps numbered from another one
round.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import networkx as nx

from .model import Axial, BraidingMachine, Connection, HornGear

__all__ = [
    "axial_text",
    "axials_of",
    "graph_of",
    "loading_of",
    "machine_from_graph",
    "read_axials",
    "read_loading",
]

# A gear's name, and its own number of slots if given: A, B2, left:6.
_GEAR = r"([A-Za-z0-9_]+)(?::(\d+))?"
_PAIR = re.compile(rf"{_GEAR}-{_GEAR}")
# The parts of a split gear, on one axle: B1+B2, or more.
_AXLE = re.compile(rf"{_GEAR}(?:\+{_GEAR})+")


def _read(
    text: str,
) -> tuple[list[tuple[str, str]], list[tuple[str, ...]], dict[str, int]]:
    """The pairs of gears that mesh, in order; the gears split into parts on
    one axle, each as its parts; and the gears given their own number of
    slots."""
    pairs: list[tuple[str, str]] = []
    axles: list[tuple[str, ...]] = []
    slots: dict[str, int] = {}

    def given(gear: str, count: str | None) -> None:
        if count is None:
            return
        if slots.get(gear, int(count)) != int(count):
            raise ValueError(
                f"Gear {gear} is given {slots[gear]} slots and {count}: give one."
            )
        slots[gear] = int(count)

    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue
        pair = _PAIR.fullmatch(token)
        axle = _AXLE.fullmatch(token)
        if pair is not None:
            a, a_slots, b, b_slots = pair.groups()
            if a == b:
                raise ValueError(f"{token!r}: a gear cannot mesh with itself.")
            given(a, a_slots)
            given(b, b_slots)
            pairs.append((a, b))
        elif axle is not None:
            parts = []
            for part in token.split("+"):
                name, _, count = part.partition(":")
                given(name, count or None)
                parts.append(name)
            if len(set(parts)) != len(parts):
                raise ValueError(f"{token!r} names a part twice.")
            axles.append(tuple(parts))
        else:
            raise ValueError(
                f"Cannot read {token!r}: give two gears that mesh as A-B, a gear "
                "with its own number of slots as A:6, the parts of a split gear "
                "as B1+B2."
            )
    if not pairs:
        raise ValueError("Give the gears that mesh, as A-B B-C C-D D-A.")
    return pairs, axles, slots


def machine_from_graph(
    text: str, n_slots: int = 4, axials: str = "", loading: str = ""
) -> BraidingMachine:
    """The machine whose gears mesh as written.

    Args:
        text: The pairs of gears that mesh, as ``A-B B-C``, separated by
            spaces, commas or semicolons; a gear's own number of slots as
            ``A:6``; a gear split into parts on one axle as ``B1+B2`` (or
            more parts), each part a gear of its own in the pairs.
        n_slots: How many slots a gear, or a part, has when the text does
            not say.
        axials: Where it feeds axial yarns (:func:`read_axials`): none if
            empty.
        loading: The carriers it starts with when not told otherwise
            (:func:`read_loading`); if empty, as it loads itself
            (:meth:`~braidpy.horn_gear.model.BraidingMachine.default_carriers`).

    Returns:
        The machine, its gears' directions and contacts worked out.

    Raises:
        ValueError: If the text cannot be read, names a pair twice, falls
            into separate machines, has a ring of an odd number of gears, or
            a split gear whose parts mesh with one another, with the same
            gear, or with none; or if an axial or a carrier cannot be where
            it is given.
    """
    machine = _meshed(text, n_slots)
    if axials.strip():
        machine = machine.with_axials(read_axials(machine, axials))
    if loading.strip():
        machine = machine.with_loading(read_loading(loading, machine))
    return machine


def _meshed(text: str, n_slots: int) -> BraidingMachine:
    """The machine whose gears mesh as written, without axials, loaded as
    it loads itself (:func:`machine_from_graph`)."""
    from .layout import _layout_bfs, compute_layout

    pairs, axles, own = _read(text)
    named = list(dict.fromkeys(gear for pair in pairs for gear in pair))
    # Each gear's axle: its own, or the split gear it is a part of.
    axle_of = {gear: gear for gear in named}
    for parts in axles:
        whole = "+".join(parts)
        for part in parts:
            if part not in axle_of:
                raise ValueError(f"Part {part} of {whole} meshes with no gear.")
            if axle_of[part] != part:
                raise ValueError(f"Gear {part} is on two axles: give it one.")
            axle_of[part] = whole
    # The machine as its axles: what meshes, which way each turns, where.
    graph = nx.Graph()
    graph.add_nodes_from(dict.fromkeys(axle_of[g] for g in named))
    for a, b in pairs:
        u, v = axle_of[a], axle_of[b]
        if u == v:
            raise ValueError(f"Parts {a} and {b} of {u} cannot mesh: they turn as one.")
        if graph.has_edge(u, v):
            raise ValueError(f"Gears {u} and {v} are named as meshing twice.")
        graph.add_edge(u, v)
    if not nx.is_connected(graph):
        groups = [" ".join(sorted(part)) for part in nx.connected_components(graph)]
        raise ValueError(
            "These gears make separate machines: " + "; ".join(groups) + "."
        )
    colours = nx.bipartite.color(graph) if nx.is_bipartite(graph) else None
    if colours is None:
        cycle = next(c for c in nx.cycle_basis(graph) if len(c) % 2)
        raise ValueError(
            f"Gears {'-'.join(cycle)} make a ring of {len(cycle)}: neighbours turn "
            "opposite ways, so a ring of an odd number cannot turn."
        )
    first = colours[axle_of[named[0]]]
    slots = {gear: own.get(gear, n_slots) for gear in named}
    # A split gear is as large as all its parts' slots together.
    size = {axle: 0 for axle in graph}
    for gear in named:
        size[axle_of[gear]] += slots[gear]
    gears = [
        HornGear(
            name,
            slots[name],
            direction=1 if colours[axle_of[name]] == first else -1,
            size=None if axle_of[name] == name else size[axle_of[name]],
        )
        for name in named
    ]
    for parts in axles:
        if len({slots[part] for part in parts}) > 1:
            counts = ", ".join(f"{part}:{slots[part]}" for part in parts)
            raise ValueError(
                f"The parts of {'+'.join(parts)} have {counts} slots: a split "
                "gear's parts take turns round it, so give them as many each."
            )
    # Laid out from the axles and their sizes, which is all the layout reads:
    # the contacts' slots, not known yet, are left at 0.
    sketch = BraidingMachine(
        [HornGear(axle, size[axle]) for axle in graph],
        [Connection(axle_of[a], axle_of[b], 0, 0) for a, b in pairs],
    )
    # Which part of a split gear meets each of its neighbours.
    meets = {}
    for a, b in pairs:
        meets[(axle_of[a], axle_of[b])] = a
        meets[(axle_of[b], axle_of[a])] = b
    if axles and nx.is_forest(graph):
        centres = _layout_bfs(
            sketch, directions=_interleaved(axles, meets, slots, axle_of)
        )
    else:
        centres = compute_layout(sketch)
    at = {gear: centres[axle_of[gear]] for gear in named}
    slot = {
        gear.name: _contact_slots(
            gear,
            [b if a == gear.name else a for a, b in pairs if gear.name in (a, b)],
            at,
        )
        for gear in gears
    }
    connections = [
        Connection(a, b, slot[a][b], slot[b][a], name=f"{a}-{b}") for a, b in pairs
    ]
    if not axles:
        return BraidingMachine(gears, connections)
    return DescribedMachine(gears, connections, at)


def _interleaved(axles, meets, slots, axle_of):
    """How a tree of gears with split gears is laid out: each gear placed
    from a split gear where a horn of the part it meets stands.

    A split gear's ``k`` parts of ``s`` slots take turns round it, part
    ``j``'s horns ``j`` of the whole gear's ``k s`` pitches on from part 0's,
    each part meeting its own neighbours.  So a neighbour of part ``j`` can
    only be where one of part ``j``'s horns comes round: of those, the one
    nearest where the tree would spread it (:func:`~braidpy.horn_gear.layout
    ._spread`), and not one taken.  Other gears are spread as the tree
    spreads them.

    Returns:
        The ``directions`` for :func:`~braidpy.horn_gear.layout._layout_bfs`.
    """
    from .layout import _spread

    split = {"+".join(parts): parts for parts in axles}

    def directions(gear, back, onward):
        wanted = _spread(back, len(onward))
        if gear not in split:
            return wanted
        parts = split[gear]
        k, s = len(parts), slots[parts[0]]
        pitch = 2 * math.pi / (k * s)
        # The whole gear's horns turned so that the part meeting the gear it
        # was placed from faces it.
        base = 0.0
        taken = set()
        if back is not None:
            via = parts.index(meets[(gear, _placed_from[gear])])
            base = back - via * pitch
            taken.add(via)
        chosen = []
        for next_gear, target in zip(onward, wanted):
            j = parts.index(meets[(gear, next_gear)])
            horns = [
                base + (j + k * m) * pitch
                for m in range(s)
                if (j + k * m) % (k * s) not in taken
            ]
            angle = min(
                horns, key=lambda h: abs(math.remainder(h - target, 2 * math.pi))
            )
            taken.add(round((angle - base) / pitch) % (k * s))
            chosen.append(angle)
        return chosen

    # The gear each gear is placed from, which the layout does not say:
    # noted as it places them.
    _placed_from: dict[str, str] = {}

    def recording(gear, back, onward):
        for next_gear in onward:
            _placed_from[next_gear] = gear
        return directions(gear, back, onward)

    return recording


class DescribedMachine(BraidingMachine):
    """A machine read from its graph with split gears: its gears placed as
    the graph lays them out, each part of a split gear on its axle, at the
    split gear's centre, where the layout of the parts alone would not put
    them.

    Args:
        gears: The gears, parts of split gears among them.
        connections: The contacts.
        centres: Each gear's centre, at scale 1.
    """

    def __init__(
        self,
        gears: list[HornGear],
        connections: list[Connection],
        centres: dict[str, tuple[float, float]],
    ) -> None:
        self.centres = dict(centres)
        super().__init__(gears, connections)

    def preferred_layout(
        self, scale: float = 1.0
    ) -> dict[str, tuple[float, float]] | None:
        """The centres the graph laid out, at this scale."""
        return {g: (x * scale, y * scale) for g, (x, y) in self.centres.items()}


# Angles closer than this, in slots, are taken as equal: a ring of eight
# gears puts a gear's two contacts one and a half slots apart, which is a
# tie to be broken the same way on every gear, not by rounding error.
_SAME = 1e-6


def _contact_slots(
    gear: HornGear, neighbours: list[str], at: dict[str, tuple[float, float]]
) -> dict[str, int]:
    """The slot of a gear at each of its contacts at the start.

    Its first contact named is its slot 0; the others follow anticlockwise,
    each a whole number of slots on from the one before, those numbers
    together the gear's slots, as close as they can be to where the layout
    puts the contacts, and as even as they can be where that does not
    decide.

    Raises:
        ValueError: If the gear has more contacts than slots.
    """
    n, k = gear.n_slots, len(neighbours)
    if k > n:
        raise ValueError(
            f"Gear {gear.name} meshes with {k} gears but has {n} slots: give it "
            f"at least {k}, as {gear.name}:{k}."
        )
    if k == 1:
        return {neighbours[0]: 0}
    x, y = at[gear.name]

    def turn(name: str) -> float:
        u, v = at[name]
        return math.atan2(v - y, u - x)

    first = turn(neighbours[0])
    # Anticlockwise from the first contact, in slots.
    ahead = sorted(
        (((turn(name) - first) % (2 * math.pi)) / (2 * math.pi) * n, name)
        for name in neighbours
    )
    wanted = [
        round(((ahead[(i + 1) % k][0] - ahead[i][0]) % n) / _SAME) * _SAME
        for i in range(k)
    ]
    best = min(
        _gaps(n, k),
        key=lambda gaps: (
            sum((g - n / k) ** 2 for g in gaps),
            sum(abs(g - w) for g, w in zip(gaps, wanted)),
        ),
    )
    slots, at_slot = {}, 0
    for (_, name), gap in zip(ahead, best):
        slots[name] = at_slot
        at_slot += gap
    return slots


def _gaps(n: int, k: int):
    """Every way of cutting ``n`` slots into ``k`` gaps of one or more, in
    order."""
    if k == 1:
        yield (n,)
        return
    for first in range(1, n - k + 2):
        for rest in _gaps(n - first, k - 1):
            yield (first, *rest)


def axial_text(axial: Axial) -> str:
    """Where an axial is fed, as written: its gear, ``B``, or the ring of
    gears round its hole, ``A-B-C-D``."""
    return "-".join(axial.anchor)


def read_axials(machine: BraidingMachine, text: str) -> list[Axial]:
    """The axials fed where written, each one of the machine's
    :func:`~braidpy.horn_gear.layout.axial_spots`.

    Args:
        machine: The machine.
        text: The places, separated by spaces, commas or semicolons: a gear,
            ``B``, up its spindle (a split gear by any of its parts); or the
            ring of gears round a hole, ``A-B-C-D``, in any order, down it.

    Returns:
        The axials, in the order written.

    Raises:
        ValueError: For a place the machine has no room for an axial at, or
            one given twice.
    """
    from .layout import _axle, axial_spots, compute_layout

    layout = compute_layout(machine)
    spots = axial_spots(machine, layout)
    by_gears = {frozenset(spot.anchor): spot for spot in spots}
    # A part of a split gear is fed through its axle's spot.
    up_axle = {_axle(layout, s.anchor[0]): s for s in spots if len(s.anchor) == 1}
    for name in machine.gears:
        by_gears.setdefault(frozenset((name,)), up_axle[_axle(layout, name)])
    chosen: list[Axial] = []
    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue
        spot = by_gears.get(frozenset(token.split("-")))
        if spot is None:
            places = ", ".join(axial_text(s) for s in spots) or "none"
            raise ValueError(
                f"No place for an axial at {token}: up a gear, or down a ring of "
                f"gears that leaves room for it ({places})."
            )
        if spot in chosen:
            raise ValueError(f"An axial is given twice at {token}.")
        chosen.append(spot)
    return chosen


def axials_of(machine: BraidingMachine) -> str:
    """Where a machine feeds its axials, as :func:`read_axials` reads it."""
    return " ".join(axial_text(axial) for axial in machine.axials)


def read_loading(
    text: str,
    machine: BraidingMachine,
    named: dict[str, tuple[str, int]] | None = None,
) -> list[tuple[str, int]]:
    """Carriers as written, ``A:0 B:2``: each its gear and slot, once.

    Args:
        text: The carriers, separated by spaces, commas or semicolons.
        machine: The machine they are on.
        named: Other names a carrier's place may go by, with its gear and
            slot: a lace machine's notches.

    Returns:
        Each carrier's (gear, slot), in the order written.

    Raises:
        ValueError: For a carrier that cannot be read or is not on the
            machine, two on one slot, or none at all.
    """
    named = named or {}
    loading: list[tuple[str, int]] = []
    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue
        if token in named:
            place = named[token]
        else:
            matched = re.fullmatch(r"([^:\s]+):(\d+)", token)
            if not matched:
                raise ValueError(
                    f"Cannot read {token!r}: give each carrier as gear:slot."
                )
            place = (matched.group(1), int(matched.group(2)))
            gear, slot = place
            if gear not in machine.gears:
                raise ValueError(f"No gear {gear!r}: one of {sorted(machine.gears)}.")
            n = machine.gears[gear].n_slots
            if slot >= n:
                raise ValueError(f"Gear {gear} has slots 0 to {n - 1}.")
        if place in loading:
            if token in named:
                raise ValueError(f"Two bobbins in the same notch, {token}.")
            raise ValueError(f"Two carriers on the same slot, {token}.")
        loading.append(place)
    if not loading:
        raise ValueError("Give at least one carrier.")
    return loading


def loading_of(loading: dict[int, tuple[str, int]]) -> str:
    """A loading as :func:`read_loading` reads it, carrier after carrier."""
    return " ".join(f"{gear}:{slot}" for _, (gear, slot) in sorted(loading.items()))


def graph_of(machine: BraidingMachine) -> tuple[str, int]:
    """A machine written as its graph, for :func:`machine_from_graph`.

    Gears on one axle — the parts of a split gear, drawn as large as the
    whole (:attr:`HornGear.size`) and at one centre — are written as one,
    ``B1+B2``.

    Args:
        machine: The machine.

    Returns:
        The pairs of gears that mesh, and the number of slots most of its
        gears have: a gear with another number is written with its own.
    """
    from .layout import compute_layout

    common = Counter(g.n_slots for g in machine.gears.values()).most_common(1)[0][0]
    named: set[str] = set()

    def gear(name: str) -> str:
        n = machine.gears[name].n_slots
        written = name if n == common or name in named else f"{name}:{n}"
        named.add(name)
        return written

    # The first gear named turns anticlockwise when read back: named first,
    # of the first pair, the one of the two that does.
    meshing = [(c.gear_a, c.gear_b) for c in machine.connections]
    a, b = meshing[0]
    if machine.gears[a].direction < 0:
        meshing[0] = (b, a)
    pairs = [f"{gear(a)}-{gear(b)}" for a, b in meshing]
    split = [g for g in machine.gears.values() if g.size not in (None, g.n_slots)]
    axles: dict[tuple[float, float], list[str]] = {}
    if split:
        centres = compute_layout(machine)
        for g in split:
            x, y = centres[g.name]
            axles.setdefault((round(x, 6), round(y, 6)), []).append(g.name)
    together = ["+".join(parts) for parts in axles.values() if len(parts) > 1]
    return " ".join(pairs + together), common
