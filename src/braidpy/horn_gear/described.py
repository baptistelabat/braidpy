# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A horn gear machine written as its graph: which gears mesh with which.

A machine is gears that mesh, so it can be written as the pairs that do:
``A-B B-C C-D D-A`` is four gears in a ring, ``A-B`` two side by side.  A
gear may be given its own number of slots, ``A:6``, anywhere it is named;
the others have as many as the machine's default.

The rest follows from the graph:

- Two gears that mesh turn opposite ways, so each gear's direction is the
  graph's two colours, the first gear named turning anticlockwise.  A ring
  of an odd number of gears cannot turn at all, and is refused.
- Where two gears meet is where the layout puts them
  (:func:`~braidpy.horn_gear.layout.compute_layout`, from the graph and the
  gears' sizes alone), and the slot of each gear at a contact at the start
  is the one nearest it.

:func:`graph_of` writes a machine back as its graph.  A machine of the
catalogue written so and read again makes the same braid, though its
gears may start a slot round from where the catalogue starts them.
"""

from __future__ import annotations

import math
import re
from collections import Counter

import networkx as nx

from .model import BraidingMachine, Connection, HornGear

__all__ = ["graph_of", "machine_from_graph"]

# A gear's name, and its own number of slots if given: A, B2, left:6.
_GEAR = r"([A-Za-z0-9_]+)(?::(\d+))?"
_PAIR = re.compile(rf"{_GEAR}-{_GEAR}")


def _read(text: str) -> tuple[list[tuple[str, str]], dict[str, int]]:
    """The pairs of gears that mesh, in order, and the gears given their
    own number of slots."""
    pairs: list[tuple[str, str]] = []
    slots: dict[str, int] = {}
    for token in re.split(r"[\s,;]+", text.strip()):
        if not token:
            continue
        matched = _PAIR.fullmatch(token)
        if matched is None:
            raise ValueError(
                f"Cannot read {token!r}: give two gears that mesh as A-B, a gear "
                "with its own number of slots as A:6."
            )
        a, a_slots, b, b_slots = matched.groups()
        if a == b:
            raise ValueError(f"{token!r}: a gear cannot mesh with itself.")
        for gear, given in ((a, a_slots), (b, b_slots)):
            if given is None:
                continue
            if slots.get(gear, int(given)) != int(given):
                raise ValueError(
                    f"Gear {gear} is given {slots[gear]} slots and {given}: give one."
                )
            slots[gear] = int(given)
        pairs.append((a, b))
    if not pairs:
        raise ValueError("Give the gears that mesh, as A-B B-C C-D D-A.")
    return pairs, slots


def machine_from_graph(text: str, n_slots: int = 4) -> BraidingMachine:
    """The machine whose gears mesh as written.

    Args:
        text: The pairs of gears that mesh, as ``A-B B-C``, separated by
            spaces, commas or semicolons; a gear's own number of slots as
            ``A:6``.
        n_slots: How many slots a gear has when the text does not say.

    Returns:
        The machine, its gears' directions and contacts worked out.

    Raises:
        ValueError: If the text cannot be read, names a pair twice, falls
            into separate machines, or has a ring of an odd number of gears.
    """
    from .layout import compute_layout

    pairs, own = _read(text)
    graph = nx.Graph()
    for a, b in pairs:
        if graph.has_edge(a, b):
            raise ValueError(f"Gears {a} and {b} are named as meshing twice.")
        graph.add_edge(a, b)
    if not nx.is_connected(graph):
        parts = [" ".join(sorted(part)) for part in nx.connected_components(graph)]
        raise ValueError(
            "These gears make separate machines: " + "; ".join(parts) + "."
        )
    colours = nx.bipartite.color(graph) if nx.is_bipartite(graph) else None
    if colours is None:
        cycle = next(c for c in nx.cycle_basis(graph) if len(c) % 2)
        raise ValueError(
            f"Gears {'-'.join(cycle)} make a ring of {len(cycle)}: neighbours turn "
            "opposite ways, so a ring of an odd number cannot turn."
        )
    order = list(dict.fromkeys(gear for pair in pairs for gear in pair))
    first = colours[order[0]]
    gears = [
        HornGear(
            name,
            own.get(name, n_slots),
            direction=1 if colours[name] == first else -1,
        )
        for name in order
    ]
    # Laid out from the graph and the gears' sizes, which is all the layout
    # reads: the contacts' slots, not known yet, are left at 0.
    sketch = BraidingMachine(gears, [Connection(a, b, 0, 0) for a, b in pairs])
    at = compute_layout(sketch)
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
    return BraidingMachine(gears, connections)


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


def graph_of(machine: BraidingMachine) -> tuple[str, int]:
    """A machine written as its graph, for :func:`machine_from_graph`.

    Args:
        machine: The machine.

    Returns:
        The pairs of gears that mesh, and the number of slots most of its
        gears have: a gear with another number is written with its own.
    """
    common = Counter(g.n_slots for g in machine.gears.values()).most_common(1)[0][0]
    named: set[str] = set()

    def gear(name: str) -> str:
        n = machine.gears[name].n_slots
        written = name if n == common or name in named else f"{name}:{n}"
        named.add(name)
        return written

    pairs = [f"{gear(c.gear_a)}-{gear(c.gear_b)}" for c in machine.connections]
    return " ".join(pairs), common
