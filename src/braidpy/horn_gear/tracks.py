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
from typing import Dict, List, Tuple

from .model import BraidingMachine

# A position is (gear_name, slot_index)
Position = Tuple[str, int]

# A track is an ordered list of positions visited, ending just before
# returning to the start (i.e. the start is NOT repeated at the end).
Track = List[Position]


def _next_position(machine: BraidingMachine, pos: Position, time: int) -> Position:
    """Compute the position of a carrier after one step.

    A carrier sits in a physical slot (a horn of the gear) and turns with it,
    so **its slot index never changes while it stays on a gear** — only the
    slot's angular position changes, via ``HornGear.slot_angle``.

    Contact points, by contrast, are fixed in space: as the gear turns, a
    different slot index arrives at each contact every step
    (``HornGear.slot_at_connection``).  A transfer happens exactly when the
    carrier's slot is the one sitting at a contact.

    Args:
        machine: The machine definition.
        pos: Current (gear_name, slot_index).
        time: Current step (before the step is applied).

    Returns:
        Next (gear_name, slot_index) after one step.
    """
    gear_name, slot = pos

    # Has this slot arrived at a contact point at time+1?  The check uses
    # time+1 because the gear turns first, then the transfer happens.
    neighbor = machine.neighbor_at_slot(gear_name, slot, time + 1)
    if neighbor is not None:
        return neighbor  # transfer to neighbouring gear

    return gear_name, slot


def contact_period(machine: BraidingMachine) -> int:
    """Number of steps after which every contact point shows the same slots again.

    Each gear returns its slot indices to the contact points every
    ``n_slots`` steps, so the whole machine's contact pattern repeats with
    period ``lcm(n_slots)``.
    """
    return reduce(lcm, (g.n_slots for g in machine.gears.values()), 1)


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
    positions = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    return reduce(lcm, (_follow(machine, p, max_steps)[1] for p in positions), 1)


def compute_tracks(machine: BraidingMachine) -> List[Track]:
    """Compute all distinct closed tracks for the machine.

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
