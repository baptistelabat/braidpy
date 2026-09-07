# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/examples.py
=====================

Classic braiding machine configurations as factory functions.

Each function returns a ready-to-use BraidingMachine.

References
----------
- Brunnschweiler, D. (1953). "Horn Gear Mechanism of Braiding Machines."
- Kyosev, Y. (2014). "Braiding Technology for Textiles."
"""

from __future__ import annotations

from .model import BraidingMachine, Connection, HornGear


def flat_braid_3() -> BraidingMachine:
    """The simplest machine there is: 2 gears of 3 slots, 3 carriers.

    Layout::

        [A(3)] -- [B(3)]

    This is the smallest configuration that still braids, and the easiest one
    to read in the animation.  Six slots hold three carriers; each rides its
    gear for three steps, hands over at the single contact, rides the other
    gear for three steps and comes back, so the whole machine repeats every 6
    steps.  Three strands shuttling between two points is the ordinary
    three-strand plait.

    Both gears have a single connection, so their one contact can always be
    placed exactly on a slot — the layout is exact.

    Returns:
        BraidingMachine for a 2-gear, 3-carrier flat braid.
    """
    return flat_braid_4(n_slots=3)


def flat_braid_4(n_slots: int = 4) -> BraidingMachine:
    """Flat braid: 2 gears in a row, turning in opposite directions.

    Layout::

        [A] -- [B]

    Carriers shuttle between the two gears through the single contact.  Half
    the slots can be loaded, so the machine carries ``n_slots`` carriers.
    See :func:`flat_braid_3` for the smallest useful case.

    Args:
        n_slots: Number of slots per gear (= number of carriers).

    Returns:
        BraidingMachine for a 2-gear flat braid.
    """
    gears = [
        HornGear("A", n_slots, direction=+1),
        HornGear("B", n_slots, direction=-1),
    ]
    connections = [
        Connection("A", "B", slot_a0=0, slot_b0=0, name="A-B"),
    ]
    return BraidingMachine(gears, connections)


def flat_braid_9(n_end: int = 5) -> BraidingMachine:
    """9-carrier flat braid: 4 gears in a row, turnaround gears at each end.

    Layout::

        [A(5)] -- [B(4)] -- [C(4)] -- [D(5)]

    The end gears have only one connection each, so their slot count is free:
    that single contact can always be put exactly on a slot whatever it is.
    The interior gears sit between two neighbours on a straight line, 180°
    apart, which is a whole number of slots for a 4-slot gear.  Every variant
    is therefore geometrically exact.

    What ``n_end`` changes is how the carrier paths join up.  A carrier
    entering an end gear rides round it and leaves by the same contact it
    arrived through, so an **odd** ``n_end`` brings it back on the opposite
    strand and fuses the machine into one closed track over every slot, while
    an **even** ``n_end`` returns it to its own strand and leaves separate
    tracks that never exchange carriers:

    ====== ======= ======== ======== ====== ========
    n_end  slots   tracks   carriers load   period
    ====== ======= ======== ======== ====== ========
    3      14      1         7       50%      84
    4      16      4         4       25%      16
    5      18      1         9       50%     180
    6      20      2        10       50%      60
    7      22      1        11       50%     308
    8      24      8         8       33%      24
    9      26      1        13       50%     468
    ====== ======= ======== ======== ====== ========

    Odd values always reach 50% loading — the ceiling, since only one of the
    two slots meeting at a contact may be occupied — at the cost of a much
    longer period.  Even values can fall short: 4 and 8 share a factor with the
    4-slot interior gears, which fragments the machine into many short tracks
    and strands slots that cannot be filled.

    Args:
        n_end: Slot count of the two end gears.  Odd gives one combined track,
            even gives several separate ones.

    Returns:
        BraidingMachine for a 4-gear flat braid.
    """
    gears = [
        HornGear("A", n_end, direction=+1),
        HornGear("B", 4, direction=-1),
        HornGear("C", 4, direction=+1),
        HornGear("D", n_end, direction=-1),
    ]
    connections = [
        Connection("A", "B", slot_a0=0, slot_b0=2, name="A-B"),
        Connection("B", "C", slot_a0=0, slot_b0=2, name="B-C"),
        Connection("C", "D", slot_a0=0, slot_b0=0, name="C-D"),
    ]
    return BraidingMachine(gears, connections)


def tubular_braid_8() -> BraidingMachine:
    """Classic 8-carrier tubular braid: 4 gears in a ring.

    Layout::

           [A]
          /   \\
        [D]   [B]
          \\   /
           [C]

    All gears have 4 slots; rotations alternate around the ring.

    Four equal circles in a ring meet at contacts 90° apart on each gear, which
    is exactly one 4-slot pitch.  The connection slots below are chosen so each
    gear's two contact slots are adjacent (differ by 1), matching that geometry:
    carriers then sweep in step with the gear instead of drifting against it.

    Returns:
        BraidingMachine for a 4-gear ring braid.
    """
    gears = [
        HornGear("A", 4, direction=+1),
        HornGear("B", 4, direction=-1),
        HornGear("C", 4, direction=+1),
        HornGear("D", 4, direction=-1),
    ]
    connections = [
        Connection("A", "B", slot_a0=1, slot_b0=3, name="A-B"),
        Connection("B", "C", slot_a0=0, slot_b0=3, name="B-C"),
        Connection("C", "D", slot_a0=0, slot_b0=3, name="C-D"),
        Connection("D", "A", slot_a0=0, slot_b0=0, name="D-A"),
    ]
    return BraidingMachine(gears, connections)


def tubular_braid_12() -> BraidingMachine:
    """12-carrier tubular braid: 6 gears in a hexagonal ring.

    Each gear has 4 slots; gears alternate direction around the ring.
    Produces the classic 12-carrier tubular braid.

    Returns:
        BraidingMachine for a 6-gear hexagonal ring braid.
    """
    n = 6
    names = [chr(ord("A") + i) for i in range(n)]
    gears = [
        HornGear(name, 4, direction=+1 if i % 2 == 0 else -1)
        for i, name in enumerate(names)
    ]
    connections = [
        Connection(
            names[i],
            names[(i + 1) % n],
            slot_a0=1,
            slot_b0=3,
            name=f"{names[i]}-{names[(i + 1) % n]}",
        )
        for i in range(n)
    ]
    return BraidingMachine(gears, connections)


def tubular_braid_16() -> BraidingMachine:
    """16-carrier tubular braid: 8 gears in a ring.

    Each gear has 4 slots; gears alternate direction around the ring.
    This produces the classic tubular braid with 16 carriers.

    Returns:
        BraidingMachine for an 8-gear ring braid.
    """
    n = 8
    names = [chr(ord("A") + i) for i in range(n)]
    gears = [
        HornGear(name, 4, direction=+1 if i % 2 == 0 else -1)
        for i, name in enumerate(names)
    ]
    connections = [
        Connection(
            names[i],
            names[(i + 1) % n],
            slot_a0=1,
            slot_b0=3,
            name=f"{names[i]}-{names[(i + 1) % n]}",
        )
        for i in range(n)
    ]
    return BraidingMachine(gears, connections)


def diamond_braid() -> BraidingMachine:
    """Diamond / square braid: 2×2 grid of gears.

    Layout::

        [A] -- [B]
         |      |
        [C] -- [D]

    Each gear has 4 slots.  Produces 2 interlocked braid tracks.

    The four gears form a 4-cycle (A-B-D-C-A), so as in :func:`tubular_braid_8`
    each gear's two contacts are 90° apart — one slot pitch.  The connection
    slots below keep those two slots adjacent, matching the layout.

    Returns:
        BraidingMachine for a 2×2 grid.
    """
    gears = [
        HornGear("A", 4, direction=+1),
        HornGear("B", 4, direction=-1),
        HornGear("C", 4, direction=-1),
        HornGear("D", 4, direction=+1),
    ]
    connections = [
        Connection("A", "B", slot_a0=0, slot_b0=0, name="A-B"),
        Connection("C", "D", slot_a0=1, slot_b0=0, name="C-D"),
        Connection("A", "C", slot_a0=1, slot_b0=0, name="A-C"),
        Connection("B", "D", slot_a0=3, slot_b0=1, name="B-D"),
    ]
    return BraidingMachine(gears, connections)


def mixed_gear_machine() -> BraidingMachine:
    """Example machine mixing 4-slot and 6-slot gears.

    Layout::

        [A(6)] -- [B(4)] -- [C(6)]

    Demonstrates heterogeneous gear support.

    Returns:
        BraidingMachine with mixed slot counts.
    """
    gears = [
        HornGear("A", 6, direction=+1),
        HornGear("B", 4, direction=-1),
        HornGear("C", 6, direction=+1),
    ]
    connections = [
        Connection("A", "B", slot_a0=0, slot_b0=2, name="A-B"),
        Connection("B", "C", slot_a0=0, slot_b0=3, name="B-C"),
    ]
    return BraidingMachine(gears, connections)
