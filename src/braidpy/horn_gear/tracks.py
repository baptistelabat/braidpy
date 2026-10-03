# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/tracks.py
===================

Precompute the closed carrier tracks of a braiding machine.

A *track* is the closed path a carrier follows when started at a given
(gear, slot) position at t=0.  A carrier rides in a physical horn of its
gear, so at each step it either:

1. Stays where it is — keeping its slot index while the gear turns it to a
   new angle.
2. Transfers to an adjacent gear, which happens on exactly the step where
   its slot is the one sitting at a contact point.

Contact points are fixed in space, so a different slot index reaches them
every step.  The dynamics are therefore time-dependent, and a track only
closes once the carrier is back at its starting slot *and* the contact
pattern is back to its t=0 phase — usually well after one gear revolution.

Tracks normally partition the slots, but not always: two carriers may cross
the same slot at different times without ever meeting, in which case their
tracks overlap.
"""

from __future__ import annotations

from functools import reduce
from math import lcm
from typing import Dict, List, Optional, Tuple

from .model import BraidingMachine


class NoFixedTracks(RuntimeError):
    """Raised when a fixed-track calculation is asked of a programmed machine."""


def _require_fixed_tracks(machine: BraidingMachine, what: str) -> None:
    """Guard the calculations that only mean something for a wired machine."""
    if not machine.has_fixed_tracks:
        raise NoFixedTracks(
            f"{what} is a property of a machine whose gears are geared "
            f"together, and {type(machine).__name__} is driven by a "
            f"programme: a carrier goes where the programme sends it, so its "
            f"path need not close and there is no period to find.  Simulate "
            f"the programme instead, with carriers you place yourself."
        )


# A position is (gear_name, slot_index)
Position = Tuple[str, int]

# A track is an ordered list of positions visited, ending just before
# returning to the start (i.e. the start is NOT repeated at the end).
Track = List[Position]


def _next_position(machine: BraidingMachine, pos: Position, time: int) -> Position:
    """Compute the position of a carrier after one step.

    How a carrier moves depends on how the machine is built — tangent gears
    with their own slots, or interpenetrating gears sharing them — so the rule
    lives on the machine, in
    :meth:`~braidpy.horn_gear.model.BraidingMachine.next_position`.

    Args:
        machine: The machine definition.
        pos: Current (gear_name, slot_index).
        time: Current step (before the step is applied).

    Returns:
        Next (gear_name, slot_index) after one step.
    """
    return machine.next_position(pos, time)


def ring_order(machine: BraidingMachine) -> Optional[List[str]]:
    """The gears in the order they circle the machine, or None if it has no ring.

    A flat braid is a chain with no way round, so there is no circulation to
    speak of and this returns None.
    """
    import networkx as nx

    if any(degree != 2 for _, degree in machine.graph.degree()):
        return None
    cycles = nx.cycle_basis(machine.graph)
    if len(cycles) != 1 or len(cycles[0]) != len(machine.gears):
        return None
    return list(cycles[0])


def circulation(
    machine: BraidingMachine,
    start: Position,
    period: Optional[int] = None,
) -> int:
    """Which way round the machine a carrier started at ``start`` travels.

    Returns the net number of gear-to-gear steps it makes around the ring over
    one period: positive one way, negative the other, zero for a machine with
    no ring or a carrier that ends up where it began.

    This counts steps around the connection graph, so it needs no layout — and
    it is a property of the *starting position*, not of the track.  Two
    carriers on the same track can circulate opposite ways, because one placed
    in a slot at t=0 sits at a different phase from one that arrived there.

    Args:
        machine: The machine definition.
        start: The (gear_name, slot_index) a carrier is placed in.
        period: Steps to follow it for; the simulation period if None.

    Returns:
        Signed number of places moved around the ring.
    """
    order = ring_order(machine)
    if order is None:
        return 0
    index = {name: i for i, name in enumerate(order)}
    size = len(order)
    if period is None:
        period = simulation_period(machine)

    net = 0
    pos = start
    for t in range(period):
        nxt = _next_position(machine, pos, t)
        if nxt[0] != pos[0]:
            step = (index[nxt[0]] - index[pos[0]]) % size
            net += step if step * 2 <= size else step - size
        pos = nxt
    return net


def walk(
    machine: BraidingMachine,
    start: Position,
    period: Optional[int] = None,
) -> List[Position]:
    """Every position a carrier passes through, in order, repeats included.

    A :data:`Track` lists the *distinct* positions on a loop, which is what you
    want for counting slots but not for following one: a carrier that comes
    back to a slot it has already used is not recorded again, so two entries
    that sit side by side in a track need not be a step apart in time.  On a
    flat braid that leaves the track reading as though a carrier hopped
    straight from one end gear to the other, which are not even connected.

    Args:
        machine: The machine definition.
        start: Where the carrier begins.
        period: Steps to follow it for; the simulation period if None.

    Returns:
        The positions visited, one per step, starting at ``start``.
    """
    if period is None:
        period = simulation_period(machine)

    path = [start]
    pos = start
    for t in range(period):
        pos = _next_position(machine, pos, t)
        path.append(pos)
    return path


def contact_period(machine: BraidingMachine) -> int:
    """Number of steps after which every contact point shows the same slots again.

    Delegates to the machine, because how fast the contacts cycle depends on
    how the gears are driven — see :meth:`BraidingMachine.contact_period`.
    """
    return machine.contact_period()


def _follow(
    machine: BraidingMachine,
    start: Position,
    max_steps: int = 100_000,
) -> Tuple[Track, int]:
    """Follow one carrier from ``start`` until its path closes.

    Returns:
        (track, n_steps) — the distinct positions visited in order, and the
        number of steps after which the carrier is back at ``start`` with the
        contact pattern in its t=0 phase.
    """
    _require_fixed_tracks(machine, "Following a track")
    period = contact_period(machine)
    track: Track = [start]
    seen = {start}
    pos = start
    for t in range(max_steps):
        pos = _next_position(machine, pos, t)
        if pos == start and (t + 1) % period == 0:
            return track, t + 1
        if pos not in seen:
            track.append(pos)
            seen.add(pos)
    raise RuntimeError(
        f"Track starting at {start} did not close within {max_steps} steps. "
        "Check gear directions and connection slot indices."
    )


def compute_track(
    machine: BraidingMachine,
    start: Position,
    max_steps: int = 100_000,
) -> Track:
    """Follow a single carrier from ``start`` until it returns.

    Time advances for real: the contact pattern shifts every step, exactly as
    in :func:`~braidpy.horn_gear.simulation.simulate`.  A carrier holds its
    slot for several steps, then transfers when that slot reaches a contact,
    so the track records the **distinct positions** visited, in order.

    The track is closed only when the carrier is back at ``start`` *and* the
    machine's contact pattern is back to its t=0 phase — otherwise the path
    from there onward would not repeat.

    Args:
        machine: The machine definition.
        start: Starting (gear_name, slot_index).
        max_steps: Safety limit to prevent infinite loops in broken configs.

    Returns:
        The closed track as a list of positions (start not repeated at end).

    Raises:
        RuntimeError: If the track does not close within ``max_steps``.
    """
    return _follow(machine, start, max_steps)[0]


def simulation_period(machine: BraidingMachine, max_steps: int = 100_000) -> int:
    """Number of steps after which *every* carrier is back where it started.

    A carrier holds each slot for several steps and must go all the way round
    its track, so this is generally larger than ``len(track)`` and larger than
    :func:`contact_period`.

    Args:
        machine: The machine definition.
        max_steps: Safety limit passed to the track follower.

    Returns:
        The machine's full simulation period in steps.
    """
    _require_fixed_tracks(machine, "A simulation period")
    positions = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    return reduce(lcm, (_follow(machine, p, max_steps)[1] for p in positions), 1)


def compute_tracks(machine: BraidingMachine) -> List[Track]:
    """Compute all distinct closed tracks for the machine.

    A slot belongs to one gear and one track, so the tracks partition the
    slots.  Following a track out of *every* slot instead would not improve on
    this: at a contact the carrier is in two slots at once, so entering the
    loop by the other one hands back the same track reversed, and on a flat
    braid entering at a different phase hands back an ordering that is neither
    a rotation nor a reversal of the first.  Starting from the slots not yet
    accounted for is what keeps the result a partition.

    Every (gear, slot) appears on at least one track.  For most machines the
    tracks also partition the slots, but that is not guaranteed: two carriers
    may pass through the same slot at *different* times without ever meeting,
    in which case their tracks overlap and the lengths sum to more than
    ``machine.total_slots()``.  Callers placing carriers from tracks should
    therefore drop repeated positions.

    Args:
        machine: The machine definition.

    Returns:
        List of tracks.  Each track is a list of (gear_name, slot_index)
        visited in order.
    """
    _require_fixed_tracks(machine, "Computing tracks")
    all_positions: List[Position] = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]

    seen = set()
    tracks: List[Track] = []

    for pos in all_positions:
        if pos in seen:
            continue
        track = compute_track(machine, pos)
        tracks.append(track)
        seen.update(track)

    return tracks


def tracks_summary(tracks: List[Track]) -> Dict[str, int]:
    """Return summary statistics for a list of tracks.

    Args:
        tracks: Output of compute_tracks.

    Returns:
        Dict with keys 'n_tracks', 'min_length', 'max_length', 'total_positions'.
    """
    if not tracks:
        return {"n_tracks": 0, "min_length": 0, "max_length": 0, "total_positions": 0}
    lengths = [len(t) for t in tracks]
    return {
        "n_tracks": len(tracks),
        "min_length": min(lengths),
        "max_length": max(lengths),
        "total_positions": sum(lengths),
    }
