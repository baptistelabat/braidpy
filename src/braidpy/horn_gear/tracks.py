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
