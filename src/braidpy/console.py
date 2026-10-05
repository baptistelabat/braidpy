# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
console.py
==========

Working a braiding machine by hand, a step at a time.

A braid comes out of a machine whose carriers must be placed so that no two
ever meet.  :func:`~braidpy.horn_gear.loading.load_carriers` solves that
outright, but on a machine of any size it is slow, and when it cannot reach
the loading a real machine runs it says nothing about why.  Turning the
handle and watching is often quicker — which is what this module is for.

It holds no state.  The page keeps the carriers and the step number and hands
them back, so going backwards is just restoring what was there before, and
editing the carriers mid-run needs no special case.

The geometry is sent once: where the gears are, how big, how fast and which
way they turn.  Where a slot *is* at a given step follows from that by
arithmetic the page can do itself, so stepping does not redraw from Python.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Sequence, Tuple

from braidpy.horn_gear.layout import (
    carrier_radius,
    compute_layout,
    contact_point,
    gear_radii,
    slot_offsets,
)
from braidpy.horn_gear.model import BraidingMachine

Position = Tuple[str, int]


def machines() -> Dict[str, Callable[[], BraidingMachine]]:
    """Every machine the console can work, by id.

    Returns:
        Machine id → a function building it.
    """
    from braidpy.horn_gear import examples
    from braidpy.horn_gear.switch import multiband_10_15_10

    return {
        "flat_9": examples.flat_braid_9,
        "princess": examples.princess_braid,
        "tubular_8": examples.tubular_braid_8,
        "tubular_16": examples.tubular_braid_16,
        "multiband_10_15_10": multiband_10_15_10,
    }


TITLES = {
    "flat_9": "Flat braid, 9 carriers",
    "princess": "Princess braid, 5/6/5",
    "tubular_8": "Tubular braid, 8 carriers",
    "tubular_16": "Tubular braid, 16 carriers",
    "multiband_10_15_10": "Three bands, 10-15-10",
}


def _machine(name: str) -> BraidingMachine:
    builders = machines()
    if name not in builders:
        raise KeyError(f"no machine called {name!r}; have {sorted(builders)}")
    return builders[name]()


def geometry(name: str, scale: float = 1.0) -> Dict[str, Any]:
    """Everything needed to draw the machine, sent once.

    A slot's angle at step ``t`` is ``offset + 2*pi*(slot + direction*t)/n``
    -- the gear turns ``direction`` slots a step, and the slot index itself is
    not mirrored.  The page works that out for itself, so only what does not
    change is sent here.

    Args:
        name: Machine id, from :func:`machines`.
        scale: Layout scale.

    Returns:
        A dict of gears, contacts and the suggested loading, ready for JSON.
    """
    machine = _machine(name)
    layout = compute_layout(machine, scale=scale)
    radii = gear_radii(machine, scale=scale)
    offsets = slot_offsets(machine, layout)

    gears = []
    for gear_name, gear in machine.gears.items():
        x, y = layout[gear_name]
        gears.append(
            {
                "name": gear_name,
                "x": x,
                "y": y,
                "radius": radii[gear_name],
                "ride": carrier_radius(machine, layout, gear_name, scale),
                "slots": gear.n_slots,
                "direction": gear.direction,
                "offset": offsets[gear_name],
            }
        )

    switched = set()
    for switch in getattr(machine, "switches", ()):
        switched.add(switch.connection)

    contacts = []
    for conn in machine.connections:
        x, y = contact_point(machine, layout, conn.gear_a, conn.gear_b, scale)
        contacts.append(
            {
                "name": conn.name or f"{conn.gear_a}-{conn.gear_b}",
                "a": conn.gear_a,
                "b": conn.gear_b,
                "x": x,
                "y": y,
                "switched": (conn.name or "") in switched,
            }
        )

    return {
        "name": name,
        "title": TITLES.get(name, name),
        "gears": gears,
        "contacts": contacts,
        "loading": [list(p) for p in suggested_loading(name)],
    }


def suggested_loading(name: str) -> List[Position]:
    """A loading to start from, rather than an empty machine.

    The machine's own loader is used where it is quick enough, and a greedy
    search where it is not — on 86 slots the exact one does not return.

    Args:
        name: Machine id.

    Returns:
        Carrier positions.
    """
    machine = _machine(name)
    if machine.total_slots() <= 32:
        from braidpy.horn_gear.loading import load_carriers

        return [tuple(p) for p in load_carriers(machine).values()]
    return greedy_loading(name)


def greedy_loading(name: str, trials: int = 8, steps: int = 120) -> List[Position]:
    """The fullest loading a greedy search finds.

    Args:
        name: Machine id.
        trials: Random orders to try.
        steps: Steps each candidate must survive.

    Returns:
        Carrier positions.
    """
    import random

    machine = _machine(name)
    places = [
        (gear_name, slot)
        for gear_name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    best: List[Position] = []
    for seed in range(trials):
        rng = random.Random(seed)
        order = list(places)
        rng.shuffle(order)
        kept: List[Position] = []
        for place in order:
            if not collisions(name, kept + [place], steps=steps):
                kept.append(place)
        if len(kept) > len(best):
            best = kept
    return best


def advance(
    name: str,
    carriers: Sequence[Sequence[Any]],
    time: int = 0,
) -> Dict[str, Any]:
    """Turn the handle one step.

    Args:
        name: Machine id.
        carriers: Where the carriers are now, as (gear, slot).
        time: The step being taken.

    Returns:
        ``carriers`` after the step, the new ``time``, and ``collisions`` --
        the positions two or more carriers have landed on, empty if none.
    """
    machine = _machine(name)
    moved = [machine.next_position((str(g), int(s)), time) for g, s in carriers]
    return {
        "carriers": [list(p) for p in moved],
        "time": time + 1,
        "collisions": trouble(name, moved, time + 1),
    }


def trouble(
    name: str,
    carriers: Sequence[Sequence[Any]],
    time: int = 0,
) -> List[Dict[str, Any]]:
    """What is wrong with the carriers as they stand, now, without moving.

    Two carriers in one slot is the obvious trouble.  The other is two either
    side of a contact that is exchanging: the slots meeting there are the same
    point in space, so only one of them may be occupied -- the rule
    :func:`~braidpy.horn_gear.simulation.simulate` enforces before it takes a
    single step, and the one a carrier dropped onto a slot by hand most often
    breaks.

    Args:
        name: Machine id.
        carriers: Where the carriers are.
        time: The step they are standing at.

    Returns:
        One entry per position in trouble, naming the carriers on it.
    """
    machine = _machine(name)
    places = [(str(g), int(s)) for g, s in carriers]

    seen: Dict[Position, List[int]] = {}
    for index, place in enumerate(places):
        seen.setdefault(place, []).append(index)
    met = {place: who for place, who in seen.items() if len(who) > 1}

    for conn in machine.connections:
        if not machine.contact_exchanges(conn, time):
            continue
        here = (
            conn.gear_a,
            machine.slot_at_connection(conn.gear_a, conn.slot_a0, time),
        )
        there = (
            conn.gear_b,
            machine.slot_at_connection(conn.gear_b, conn.slot_b0, time),
        )
        at_a = [i for i, p in enumerate(places) if p == here]
        at_b = [i for i, p in enumerate(places) if p == there]
        if at_a and at_b:
            met.setdefault(here, []).extend(at_a)
            met.setdefault(there, []).extend(at_b)

    return [
        {"gear": g, "slot": s, "carriers": sorted(set(who))}
        for (g, s), who in met.items()
    ]


def collisions(
    name: str,
    carriers: Sequence[Sequence[Any]],
    steps: int = 120,
    time: int = 0,
) -> List[Dict[str, Any]]:
    """Run ahead and report the first trouble, if any.

    Args:
        name: Machine id.
        carriers: Where the carriers start.
        steps: How far to look.
        time: The step to start from.

    Returns:
        The collisions at the first step that has any, with ``step`` added;
        empty if the machine runs cleanly that far.
    """
    here = trouble(name, carriers, time)
    if here:
        for item in here:
            item["step"] = time
        return here

    places: List[Sequence[Any]] = [tuple(p) for p in carriers]
    for offset in range(steps):
        out = advance(name, places, time + offset)
        if out["collisions"]:
            for item in out["collisions"]:
                item["step"] = time + offset + 1
            return out["collisions"]
        places = out["carriers"]
    return []
