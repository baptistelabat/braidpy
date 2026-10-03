# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/loading.py
====================

Deciding where the carriers start.

Threading a machine is a search, not a convention.  A placement has to
survive being run: :func:`_is_collision_free` simulates a candidate and
rejects it if two carriers ever share a slot or meet at a connection point.
Among the placements that survive, :func:`_fullest_loading` takes the one
that carries most, breaking ties on circulation balance (equal numbers going
each way), crowding, and how evenly the carriers spread over the gears.

Separate from :mod:`~braidpy.horn_gear.simulation` because the two are
different jobs and the dependency runs one way: loading calls ``simulate`` to
try a candidate, while stepping never calls loading.

:func:`load_carriers` needs the machine to have fixed tracks, so it is not
the whole story — a machine reaches its own threading through
:meth:`~braidpy.horn_gear.model.BraidingMachine.default_carriers`, which is a
hook rather than a shortcut.  A Jacquard lace machine overrides it to thread
one bobbin into every notch, and must: its carriers go where the programme
sends them, there are no fixed tracks, and :func:`load_carriers` raises
:class:`~braidpy.horn_gear.tracks.NoFixedTracks` on it.
"""

from __future__ import annotations

from itertools import product
from typing import TYPE_CHECKING, Dict, Iterable, Iterator, List, Tuple

import networkx as nx

from .model import BraidingMachine
from .simulation import CarrierId, CollisionError, simulate
from .tracks import Position, circulation

if TYPE_CHECKING:
    from .tracks import Track


# Above this slot count, maximum-clique enumeration is no longer safe to run
# unbounded and loading falls back to a greedy search.
_EXACT_LOADING_LIMIT = 48


# Beyond this many tracks, enumerating every per-track offset is not worth
# it and the first candidate is used as-is.
_MAX_TRACK_OFFSETS = 16


def _number(positions: Iterable[Position]) -> Dict[CarrierId, Position]:
    """Assign sequential carrier ids to positions, skipping repeats."""
    numbered: Dict[CarrierId, Position] = {}
    seen: set = set()
    for pos in positions:
        if pos not in seen:
            seen.add(pos)
            numbered[len(numbered)] = pos
    return numbered


def _is_collision_free(
    machine: BraidingMachine,
    positions: Dict[CarrierId, Position],
    period: int,
) -> bool:
    """True if this placement runs a full period without any collision.

    A placement that puts two carriers in one slot is rejected as well, so
    callers may propose one without pre-checking.
    """
    try:
        simulate(machine, period, positions)
    except (CollisionError, ValueError):
        return False
    return True


def _circulation_imbalance(
    machine: BraidingMachine,
    positions: Dict[CarrierId, Position],
    period: int,
) -> int:
    """How lopsided a loading is between the two ways round; lower is better.

    A tubular braid is made of two counter-rotating sets of carriers, and it
    wants as many going one way as the other.  Which way a carrier travels
    depends on the slot it starts in — two carriers on the same track can
    circulate opposite ways, since one placed there at t=0 sits at a different
    phase from one that arrived — so the loading decides the balance, and
    several equally full loadings can differ in it.

    Zero for a machine with no ring, which has no circulation to balance.
    """
    senses = [
        (1 if circulation(machine, pos, period) > 0 else -1)
        for pos in positions.values()
        if circulation(machine, pos, period) != 0
    ]
    return abs(sum(senses))


def _crowding(
    machine: BraidingMachine,
    positions: Dict[CarrierId, Position],
) -> int:
    """How many carriers sit in neighbouring slots; lower is better.

    A machine is threaded with its spools spread out, not bunched together —
    every other horn where the count allows it.  Nothing about a bunched
    loading collides, so the simulation will not rule it out, and two loadings
    can hold the same number of carriers and spread them quite differently:
    soutache came out with three consecutive slots filled on one gear when a
    placement with only one such pair was available.
    """
    chosen = set(positions.values())
    return sum(
        1
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
        if (name, slot) in chosen and (name, (slot + 1) % gear.n_slots) in chosen
    )


def _gear_balance(
    machine: BraidingMachine,
    positions: Dict[CarrierId, Position],
    period: int,
) -> float:
    """How evenly a loading spreads over the gears, over the whole run.

    Scoring the starting arrangement alone is not enough: carriers drift from
    gear to gear as the machine turns, so a loading that looks well spread at
    the outset can pile every carrier onto one gear a step later — which is
    what a three-carrier flat braid did, leaving one gear bare and the braid
    momentarily undone.  This walks a full period and charges for the spread at
    every step.

    Nothing about a bunched loading collides, so the simulation will not rule
    it out; this is what chooses between placements it accepts.  Candidates are
    ranked before being checked, so one that does collide is simply sorted
    last rather than raising here.
    """
    try:
        history = simulate(machine, period, positions)
    except (CollisionError, ValueError):
        return float("inf")
    total = 0.0
    for state in history[:-1]:
        counts: Dict[str, int] = {name: 0 for name in machine.gears}
        for carrier in state.carriers:
            counts[carrier.gear] += 1
        filled = [counts[name] / machine.gears[name].n_slots for name in machine.gears]
        mean = sum(filled) / len(filled)
        total += sum((f - mean) ** 2 for f in filled)
    return total / max(len(history) - 1, 1)


def _alternating_loadings(
    machine: BraidingMachine,
    tracks: List["Track"],
    period: int,
) -> Iterator[Dict[CarrierId, Position]]:
    """Every other slot along each track, for each choice of starting offset.

    Tracks may share a slot — carriers can cross it at different times without
    ever meeting — so repeats are dropped rather than doubly occupied.

    Candidates come out fullest first and, among equally full ones, most evenly
    spread first.  Choosing an offset per track decides which *gear* each
    carrier starts on, so without that ordering a two-gear machine happily
    loads every carrier onto one gear and leaves the other bare.
    """
    if len(tracks) > _MAX_TRACK_OFFSETS:
        offsets_to_try: Iterable[Tuple[int, ...]] = [(0,) * len(tracks)]
    else:
        offsets_to_try = product((0, 1), repeat=len(tracks))

    candidates = [
        _number(
            track[i]
            for track, off in zip(tracks, offsets)
            for i in range(off, len(track), 2)
        )
        for offsets in offsets_to_try
    ]
    candidates.sort(
        key=lambda p: (
            -len(p),
            _circulation_imbalance(machine, p, period),
            _crowding(machine, p),
            _gear_balance(machine, p, period),
        )
    )
    yield from candidates


def _greedy_loadings(
    machine: BraidingMachine,
) -> Iterator[List[Position]]:
    """Candidate slot orderings for greedy loading, one per starting slot.

    Greedy loading is very sensitive to where it starts, so every slot gets a
    turn at being first.
    """
    slots = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    for seed in range(len(slots)):
        yield slots[seed:] + slots[:seed]


def _fullest_loading(
    machine: BraidingMachine,
    period: int,
) -> Dict[CarrierId, Position]:
    """The largest collision-free set of slots, computed exactly.

    Every collision this model detects involves exactly two carriers — two in
    one slot, two on the two sides of one contact, or two swapping through one
    contact — so a set of carriers is collision-free precisely when every
    *pair* in it is.  That makes the fullest loading a maximum clique of the
    "these two can coexist" graph, which is worth solving exactly: greedy
    loading leaves real machines short of what they can hold.
    """
    slots = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]

    graph = nx.Graph()
    graph.add_nodes_from(
        i
        for i, pos in enumerate(slots)
        if _is_collision_free(machine, {0: pos}, period)
    )
    viable = list(graph.nodes)
    for a in range(len(viable)):
        for b in range(a + 1, len(viable)):
            i, j = viable[a], viable[b]
            if _is_collision_free(machine, {0: slots[i], 1: slots[j]}, period):
                graph.add_edge(i, j)

    if graph.number_of_nodes() == 0:
        return {}

    cliques = list(nx.find_cliques(graph))
    fullest = max(len(c) for c in cliques)
    return min(
        (_number(slots[i] for i in sorted(c)) for c in cliques if len(c) == fullest),
        key=lambda positions: (
            _circulation_imbalance(machine, positions, period),
            _crowding(machine, positions),
            _gear_balance(machine, positions, period),
        ),
    )


def load_carriers(machine: BraidingMachine) -> Dict[CarrierId, Position]:
    """Fill the machine with as many carriers as it can hold without collisions.

    A real machine is loaded with a spool in every other slot along each track,
    which is what this tries first, since it reproduces how a machine is
    threaded in practice.  That has no meaning for a track whose path revisits
    slots — the interior gears of a flat braid are crossed once per traversal —
    so the machine is then filled as far as it will go instead.

    Either way the candidate is validated by simulating a full period: checking
    occupancy at t=0 is not enough, because contact points move to a different
    slot every step and conflicts can surface later in the cycle.

    Args:
        machine: The machine definition.

    Returns:
        Dict mapping carrier_id → (gear_name, slot).

    Raises:
        RuntimeError: If not even one carrier can be placed.
    """
    from .tracks import compute_tracks, simulation_period

    period = simulation_period(machine)

    # A gear with no carrier does no braiding, so a loading that leaves one
    # bare is rejected here even though it collides with nothing — the exact
    # search below spreads the same number of carriers over every gear.
    for positions in _alternating_loadings(machine, compute_tracks(machine), period):
        occupied = {gear for gear, _ in positions.values()}
        if len(occupied) == len(machine.gears) and _is_collision_free(
            machine, positions, period
        ):
            return positions

    # Exact for any machine of a sane size; clique enumeration is exponential
    # in the worst case, so very large machines fall back to greedy.
    if machine.total_slots() <= _EXACT_LOADING_LIMIT:
        best = _fullest_loading(machine, period)
    else:
        best = {}
        for order in _greedy_loadings(machine):
            chosen: Dict[CarrierId, Position] = {}
            for pos in order:
                trial = {**chosen, len(chosen): pos}
                if _is_collision_free(machine, trial, period):
                    chosen = trial
            if len(chosen) > len(best):
                best = chosen
            if len(best) >= machine.total_slots() // 2:
                break

    if not best:
        raise RuntimeError(
            f"No collision-free carrier placement found for this machine "
            f"(period {period})."
        )
    return best
