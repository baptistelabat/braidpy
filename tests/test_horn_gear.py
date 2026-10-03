# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Basic tests for the horn gear simulator."""

import math

import pytest

from braidpy.horn_gear.examples import (
    diamond_braid,
    flat_braid_3,
    flat_braid_4,
    flat_braid_9,
    mixed_gear_machine,
    princess_braid,
    soutache_braid,
    tubular_braid_8,
    tubular_braid_12,
    tubular_braid_16,
)
from braidpy.horn_gear.layout import (
    axial_clearance,
    axial_position,
    carrier_radius,
    compute_layout,
    contact_point,
    gear_radii,
    offset_residuals,
    tube_axials,
    tube_rings,
)
from braidpy.horn_gear.model import Axial, BraidingMachine, Connection, HornGear

# ── Model ─────────────────────────────────────────────────────────────────────


def test_horn_gear_slot_count():
    with pytest.raises(ValueError):
        HornGear("bad", 1)


def test_horn_gear_direction_validation():
    with pytest.raises(ValueError):
        HornGear("bad", 4, direction=0)


def test_machine_invalid_gear_ref():
    gears = [HornGear("A", 4)]
    conns = [Connection("A", "X", 0, 0)]
    with pytest.raises(ValueError, match="unknown gear"):
        BraidingMachine(gears, conns)


def test_machine_invalid_slot_ref():
    gears = [HornGear("A", 4), HornGear("B", 4)]
    conns = [Connection("A", "B", 0, 10)]  # slot_b0=10 out of range
    with pytest.raises(ValueError, match="out of range"):
        BraidingMachine(gears, conns)


# ── Layout ────────────────────────────────────────────────────────────────────


def test_layout_single_gear():
    m = BraidingMachine([HornGear("A", 4)], [])
    layout = compute_layout(m)
    assert "A" in layout
    assert len(layout) == 1


def test_layout_two_gears():
    m = flat_braid_4()
    layout = compute_layout(m)
    assert set(layout.keys()) == {"A", "B"}
    ax, ay = layout["A"]
    bx, by = layout["B"]
    dist = ((ax - bx) ** 2 + (ay - by) ** 2) ** 0.5
    r = gear_radii(m)
    # Distance should be ~r_A + r_B (gears touching)
    expected = r["A"] + r["B"]
    assert abs(dist - expected) / expected < 0.05


# ── Tracks ────────────────────────────────────────────────────────────────────


# ── Simulation ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "factory",
    [
        flat_braid_3,
        flat_braid_4,
        flat_braid_9,
        tubular_braid_8,
        diamond_braid,
        mixed_gear_machine,
    ],
)
def test_slots_land_exactly_on_contacts(factory):
    """These machines' connection slots agree with their physical layout.

    Every contact of every gear must fall exactly on a slot.  When it does, a
    carrier arrives at the contact at the same instant as the neighbour's slot
    that receives it, so transfers are seamless.

    ``tubular_braid_12`` and ``tubular_braid_16`` are deliberately absent: a
    closed ring of N gears has its contacts ``180 - 360/N`` degrees apart, which
    for 4-slot gears (90° per slot) is only a whole number of slots at N=4.
    """
    m = factory()
    residuals = offset_residuals(m, compute_layout(m))
    worst_gear = max(residuals, key=residuals.get)
    assert math.degrees(residuals[worst_gear]) < 1.0, (
        f"{factory.__name__}: gear {worst_gear}'s contacts miss its slots by "
        f"{math.degrees(residuals[worst_gear]):.1f}°"
    )


@pytest.mark.parametrize(
    "factory,n_gears", [(tubular_braid_12, 6), (tubular_braid_16, 8)]
)
def test_rings_that_cannot_align_are_flagged(factory, n_gears):
    """A ring of N 4-slot gears only aligns at N=4 — record the shortfall.

    Closing a ring of N gears forces each gear's contacts to sit
    ``180 - 360/N`` degrees apart, and a 4-slot gear can only place slots every
    90°.  These two machines therefore cannot be made exact without changing
    their gear count or slot count, and their carriers jump when transferring.
    """
    m = factory()
    assert len(m.gears) == n_gears
    separation = 180 - 360 / n_gears
    assert separation % 90 != 0, "this ring would in fact align; update the test"

    worst = max(offset_residuals(m, compute_layout(m)).values())
    assert math.degrees(worst) > 1.0


@pytest.mark.parametrize("n_end", [4, 5, 6, 7])
def test_flat_braid_end_gear_slot_count_is_unconstrained(n_end):
    """End gears have one connection, so any slot count stays exact.

    Their single contact can always be put exactly on a slot, and the interior
    gears' two contacts are 180° apart — two slots of a 4-slot gear.
    """
    m = flat_braid_9(n_end=n_end)
    worst = max(offset_residuals(m, compute_layout(m)).values())
    assert math.degrees(worst) < 1.0


def test_contact_slots_match_ring_geometry():
    """tubular_braid_8's connection slots must match its physical layout.

    Four equal circles in a ring touch at points 90° apart on each gear — one
    slot pitch for a 4-slot gear — so each gear's two contact slots must be
    adjacent.  If they are not, carriers drift against the gear they ride on.
    """
    m = tubular_braid_8()
    layout = compute_layout(m)

    for name, gear in m.gears.items():
        conns = m.connections_of(name)
        assert len(conns) == 2
        seps = []
        for c in conns:
            other = c.gear_b if c.gear_a == name else c.gear_a
            slot = c.slot_a0 if c.gear_a == name else c.slot_b0
            cx, cy = layout[name]
            ox, oy = layout[other]
            seps.append((math.atan2(oy - cy, ox - cx), slot))

        (ang_a, slot_a), (ang_b, slot_b) = seps
        geometric = math.degrees((ang_b - ang_a) % (2 * math.pi))
        by_index = ((slot_b - slot_a) % gear.n_slots) * 360.0 / gear.n_slots
        assert abs((geometric - by_index + 180) % 360 - 180) < 1.0, (
            f"gear {name}: contacts are {geometric:.1f}° apart on the layout "
            f"but {by_index:.1f}° apart by slot index"
        )


# ── Axial columns and tube cores ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "factory,expected",
    [
        (flat_braid_3, 0),
        (flat_braid_9, 0),
        (soutache_braid, 0),
        (princess_braid, 0),
        (mixed_gear_machine, 0),
        (tubular_braid_8, 1),
        (tubular_braid_12, 1),
        (tubular_braid_16, 1),
        (diamond_braid, 1),
    ],
)
def test_tube_rings_finds_one_ring_per_hole(factory, expected):
    """Holes are the bounded faces of the planar machine graph.

    A flat braid has no cycle and so no tube; every ring braid encloses
    exactly one.  Each ring must be a real cycle of the graph.
    """
    m = factory()
    rings = tube_rings(m)
    assert len(rings) == expected

    for ring in rings:
        assert len(ring) >= 3
        for i, gear in enumerate(ring):
            neighbour = ring[(i + 1) % len(ring)]
            assert m.graph.has_edge(gear, neighbour), (
                f"{gear}-{neighbour} is not a connection, so this is no ring"
            )


def test_tube_ring_follows_the_hole_not_the_alphabet():
    """A ring is reported in the order it encloses the hole, not by gear name.

    W-Y-X-Z is the cycle here, so a routine that merely sorted the gears would
    report W-X-Y-Z and place the core using the wrong ring.
    """
    gears = [
        HornGear("W", 4, direction=+1),
        HornGear("Y", 4, direction=-1),
        HornGear("X", 4, direction=+1),
        HornGear("Z", 4, direction=-1),
    ]
    connections = [
        Connection("W", "Y", 0, 2),
        Connection("Y", "X", 0, 2),
        Connection("X", "Z", 0, 2),
        Connection("Z", "W", 0, 2),
    ]
    ring = tube_rings(BraidingMachine(gears, connections))[0]

    assert sorted(ring) == ["W", "X", "Y", "Z"]
    # Same cycle up to rotation and direction.
    doubled = ring + ring
    assert any(
        doubled[i : i + 4] in (["W", "Y", "X", "Z"], ["Z", "X", "Y", "W"])
        for i in range(4)
    )


@pytest.mark.parametrize(
    "factory", [tubular_braid_8, tubular_braid_12, tubular_braid_16, diamond_braid]
)
def test_tube_axials_place_a_core_with_room_for_it(factory):
    """Each tube gets one core, centred, with positive clearance."""
    m = factory()
    cores = tube_axials(m)
    assert len(cores) == 1

    cored = BraidingMachine(list(m.gears.values()), m.connections, cores)
    layout = compute_layout(cored)
    position = axial_position(cored, layout, cores[0])
    assert position == pytest.approx((0.0, 0.0), abs=0.05), "ring braids centre on 0,0"
    assert axial_clearance(cored, layout, position) > 0


@pytest.mark.parametrize(
    "factory", [flat_braid_3, flat_braid_9, soutache_braid, princess_braid]
)
def test_flat_braids_get_no_tube_core(factory):
    """A flat braid has no hole, so nothing to feed a core through."""
    assert tube_axials(factory()) == []


def test_tube_rings_handles_several_tubes():
    """A grid of gears encloses one hole per opening, and all are found.

    Only the *detection* is asserted here.  Whether a core will fit is a
    separate question, and depends on the drawing: the layout solver is free to
    draw this ladder as a hexagon, which squashes both openings onto the same
    point and leaves no room for anything — in which case tube_axials rightly
    offers no cores at all.
    """
    gears, connections = [], []
    for row in range(2):
        for col in range(3):
            gears.append(
                HornGear(f"{row}{col}", 4, direction=+1 if (row + col) % 2 == 0 else -1)
            )
    for row in range(2):
        for col in range(3):
            if col + 1 < 3:
                connections.append(Connection(f"{row}{col}", f"{row}{col + 1}", 0, 2))
            if row + 1 < 2:
                connections.append(Connection(f"{row}{col}", f"{row + 1}{col}", 1, 3))
    m = BraidingMachine(gears, connections)

    rings = tube_rings(m)
    assert len(rings) == 2, "a 2x3 grid encloses two holes"
    for ring in rings:
        assert len(ring) == 4
        for i, gear in enumerate(ring):
            assert m.graph.has_edge(gear, ring[(i + 1) % len(ring)])

    # Any cores offered must have somewhere to go.
    layout = compute_layout(m)
    for core in tube_axials(m, layout):
        assert axial_clearance(m, layout, axial_position(m, layout, core)) > 0


@pytest.mark.parametrize(
    "axials,message",
    [
        ([Axial("x", ("NOPE",))], "unknown gear"),
        ([Axial("x", ())], "empty anchor"),
        ([Axial("x", ("A",)), Axial("x", ("B",))], "Duplicate axial"),
    ],
)
def test_invalid_axials_are_rejected(axials, message):
    m = tubular_braid_8()
    with pytest.raises(ValueError, match=message):
        BraidingMachine(list(m.gears.values()), m.connections, axials)


# ── Examples sanity ───────────────────────────────────────────────────────────


# ── Animation continuity ───────────────────────────────────────────────────────


# ── One cycle, and round again ────────────────────────────────────────────────


# ── Jacquard lace machine ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "factory", [tubular_braid_8, flat_braid_9, princess_braid, diamond_braid]
)
def test_tangent_machines_carry_bobbins_on_the_rim(factory):
    """Gears that merely touch hold their bobbins out on the rim, as before."""
    m = factory()
    assert m.gears_interpenetrate is False

    layout, radii = compute_layout(m), gear_radii(m)
    for gear in m.gears:
        assert carrier_radius(m, layout, gear) == pytest.approx(radii[gear])


def test_tangent_machines_keep_contacts_on_the_line_of_centres():
    """Ordinary gears touch, so their contact must stay where it always was."""
    m = tubular_braid_8()
    layout, radii = compute_layout(m), gear_radii(m)
    for conn in m.connections:
        ax, ay = layout[conn.gear_a]
        bx, by = layout[conn.gear_b]
        dist = math.hypot(bx - ax, by - ay)
        expected = (
            ax + radii[conn.gear_a] * (bx - ax) / dist,
            ay + radii[conn.gear_a] * (by - ay) / dist,
        )
        assert contact_point(m, layout, conn.gear_a, conn.gear_b) == pytest.approx(
            expected, abs=0.01
        )


GREEN, RED, GREY = "60,170,90", "205,60,55", "140,140,140"


def _disc_colours(figure_or_frame):
    """The fill of every gear disc, in gear order."""
    return [t.fillcolor for t in figure_or_frame.data if t.fill == "toself"]
