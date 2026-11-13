# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/examples.py
=====================

Classic braiding machine configurations as factory functions.

Each function returns a ready-to-use BraidingMachine, written as its graph
(:func:`~braidpy.horn_gear.described.machine_from_graph`): the gears that
mesh, where it feeds axial yarns, and the carriers it starts with where it
does not load itself so.  :mod:`braidpy.machine_catalog` lists the braids
they make.

References
----------
- Brunnschweiler, D. (1953). "Horn Gear Mechanism of Braiding Machines."
- Kyosev, Y. (2014). "Braiding Technology for Textiles."
"""

from __future__ import annotations

from .described import machine_from_graph
from .model import BraidingMachine

# Eight gears in a ring, and the loading of its tubular braid of 16
# carriers: two to a gear, on alternate slots, as the classic braid has them.
_RING_8 = "A-B B-C C-D D-E E-F F-G G-H H-A"
_RING_8_LOADING = "A:3 C:1 E:1 G:1 H:0 F:0 D:0 B:0 A:1 G:3 E:3 C:3 B:2 D:2 F:2 H:2"


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
    return machine_from_graph("A-B", n_slots)


def soutache_braid(n_slots: int = 5) -> BraidingMachine:
    """Soutache: the narrow flat braid used for trimming and in jewellery.

    Layout::

        [A(5)] -- [B(5)]

    Two gears carrying the same **odd** number of slots, loaded every other
    slot, which gives ``n_slots`` carriers.  The odd count is what makes the
    braid narrow and even: a carrier returning from one gear comes back on the
    opposite strand, so every slot lies on its own two-position track and the
    whole machine repeats in ``2 x n_slots`` steps.

    Both gears have a single connection, so their slots sit exactly on their
    one contact whatever the count — the layout is always exact.

    Soutache carries **two cords**, one fed up the spindle of each gear, and
    the carriers braid around both as they pass between them.  They are
    :class:`~braidpy.horn_gear.model.Axial` columns: they never ride a horn,
    and each stands clear of the carriers by its gear's radius.  The two cords
    are what make soutache soutache — the braid closes over them and is held
    flat, rather than rounding up as an uncored braid would.

    Args:
        n_slots: Slots per gear.  Odd values give the classic soutache.

    Returns:
        BraidingMachine for a 2-gear soutache braid with two cords.
    """
    return machine_from_graph("A-B", n_slots, axials="A B")


def princess_braid() -> BraidingMachine:
    """Princess braid: 3 gears, 5/6/5 slots, 8 carriers over a cord.

    Layout::

                   cord
                    ↓
        [A(5)] -- [B(6)] -- [C(5)]

    The classic princess arrangement: two 5-slot end gears either side of a
    6-slot centre gear, sixteen slots carrying eight carriers on a single
    track, so every carrier eventually occupies every slot and the braid is
    fully interlinked.

    Unlike :func:`soutache_braid`, this machine has a gear in the middle, so
    its cord can be fed up that gear's spindle and stands clear of the
    carriers by a full gear radius.  The cord is an
    :class:`~braidpy.horn_gear.model.Axial`: it never rides a horn, and the
    carriers braid around it as they pass between the end gears.

    The end gears have one connection each, so their 5 slots sit exactly on
    their contacts; the centre gear's two contacts are 180° apart, which is
    three of its six slots.  The layout is exact.

    Returns:
        BraidingMachine for a 3-gear princess braid with a cord core.
    """
    return machine_from_graph("A-B:6 B-C", 5, axials="B")


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
    and strands slots that cannot be filled.  These are true maxima, not the
    best a search happened to find: ``load_carriers`` solves loading exactly.

    Args:
        n_end: Slot count of the two end gears.  Odd gives one combined track,
            even gives several separate ones.

    Returns:
        BraidingMachine for a 4-gear flat braid.
    """
    return machine_from_graph("A-B:4 B-C:4 C-D", n_end)


def tubular_braid_8() -> BraidingMachine:
    """Classic 8-carrier tubular braid: 4 gears in a ring.

    Layout::

           [A]
          /   \\
        [D]   [B]
          \\   /
           [C]

    All gears have 4 slots; rotations alternate around the ring.

    Four equal circles in a ring meet at contacts 90° apart on each gear,
    which is exactly one 4-slot pitch, so each gear's two contact slots are
    side by side: carriers then sweep in step with the gear instead of
    drifting against it.

    Returns:
        BraidingMachine for a 4-gear ring braid.
    """
    return machine_from_graph("A-B B-C C-D D-A")


def tubular_braid_12() -> BraidingMachine:
    """12-carrier tubular braid: 6 gears in a hexagonal ring.

    Each gear has 4 slots; gears alternate direction around the ring.
    Produces the classic 12-carrier tubular braid.

    Returns:
        BraidingMachine for a 6-gear hexagonal ring braid.
    """
    return machine_from_graph(
        "A-B B-C C-D D-E E-F F-A",
        loading="A:3 C:1 E:1 F:0 D:0 B:0 A:1 E:3 C:3 B:2 D:2 F:2",
    )


def tubular_braid_16() -> BraidingMachine:
    """16-carrier tubular braid: 8 gears in a ring.

    Each gear has 4 slots; gears alternate direction around the ring.
    This produces the classic tubular braid with 16 carriers.

    Returns:
        BraidingMachine for an 8-gear ring braid.
    """
    return machine_from_graph(_RING_8, loading=_RING_8_LOADING)


def triaxial_braid_16() -> BraidingMachine:
    """16-carrier triaxial braid: the tubular braid of 16, round 8 axial yarns.

    A triaxial braid lays a third set of yarns along the braid, at 0°,
    between the two sets braided at ±θ: they stiffen it along its length and
    hold its diameter, which is why braided composites are made so.  On a
    maypole braider each axial yarn is fed up through a hollow horn gear
    spindle (van Ravenhorst's thesis, see the references page): it stands
    still at that gear's centre while the gear's carriers go round it, those
    of one set passing it on the inside of the braid and those of the other on
    the outside, so that it lies between them.

    So this is :func:`tubular_braid_16`, unchanged, with an
    :class:`~braidpy.horn_gear.model.Axial` up each of its eight gears.

    Returns:
        BraidingMachine for an 8-gear ring braid with an axial yarn up each
        gear.
    """
    return machine_from_graph(
        _RING_8, axials="A B C D E F G H", loading=_RING_8_LOADING
    )


def diamond_braid() -> BraidingMachine:
    """Diamond / square braid — the same machine as :func:`tubular_braid_8`.

    Drawing the four gears as a 2×2 grid rather than a ring suggests a
    different machine, but it is not one.  Both are a 4-cycle of 4-slot gears
    with alternating rotations, and they are isomorphic with slot counts and
    directions respected (A→A, C→B, D→C, B→D): 16 slots, 8 carriers, four
    4-position tracks, period 8.  So this delegates rather than restating the
    same gears and connections in a different order.

    The braiding terms *diamond* (1/1 intersection) and *square* or *regular*
    (2/2) name different **interlacings** of this one machine, not different
    machines.  Telling them apart needs which yarn crosses over which, which
    the simulator does not compute yet — see the axial/interlacing note in
    :class:`~braidpy.horn_gear.model.Axial`.

    Returns:
        BraidingMachine for a 4-gear ring braid.
    """
    return tubular_braid_8()


def mixed_gear_machine() -> BraidingMachine:
    """Example machine mixing 4-slot and 6-slot gears.

    Layout::

        [A(6)] -- [B(4)] -- [C(6)]

    Demonstrates heterogeneous gear support.

    Returns:
        BraidingMachine with mixed slot counts.
    """
    return machine_from_graph("A:6-B B-C:6")
