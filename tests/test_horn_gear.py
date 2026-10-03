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
from braidpy.horn_gear.simulation import (
    carrier_places,
    initial_state,
    load_carriers,
    simulate,
    state_period,
    step,
)
from braidpy.horn_gear.tracks import (
    circulation,
    compute_tracks,
    ring_order,
    simulation_period,
    tracks_summary,
    walk,
)

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


def test_tracks_cover_all_slots():
    m = tubular_braid_8()
    tracks = compute_tracks(m)
    summary = tracks_summary(tracks)
    assert summary["total_positions"] == m.total_slots()


def test_tracks_flat_braid_4():
    m = flat_braid_4(n_slots=4)
    tracks = compute_tracks(m)
    # Each track must be non-empty and closed (we check closure via compute_track)
    for t in tracks:
        assert len(t) > 0
    assert sum(len(t) for t in tracks) == m.total_slots()


def test_tracks_tubular_16():
    m = tubular_braid_16()
    tracks = compute_tracks(m)
    summary = tracks_summary(tracks)
    assert summary["total_positions"] == m.total_slots()


def test_tracks_diamond():
    m = diamond_braid()
    tracks = compute_tracks(m)
    assert sum(len(t) for t in tracks) == m.total_slots()


def test_tracks_mixed_gear():
    m = mixed_gear_machine()
    tracks = compute_tracks(m)
    assert sum(len(t) for t in tracks) == m.total_slots()


# ── Simulation ────────────────────────────────────────────────────────────────


def test_initial_state_fills_all_slots():
    m = tubular_braid_8()
    state = initial_state(m)
    assert len(state.carriers) == m.total_slots()


def test_step_returns_new_state():
    m = flat_braid_4()
    s0 = initial_state(m)
    s1 = step(m, s0)
    assert s1.time == 1
    assert s1 is not s0


def test_simulate_length():
    m = tubular_braid_8()
    cp = load_carriers(m)
    history = simulate(m, n_steps=10, carrier_positions=cp)
    assert len(history) == 11  # t=0 ... t=10


def test_simplest_machine():
    """The 2-gear, 3-slot machine: 3 carriers shuttling through one contact.

    Six slots, three two-position tracks, and a 6-step period — each carrier
    rides one gear for three steps, hands over, and rides the other back.
    """
    m = flat_braid_3()
    assert m.total_slots() == 6
    assert len(m.gears) == 2
    assert len(m.connections) == 1

    tracks = compute_tracks(m)
    assert len(tracks) == 3
    assert all(len(t) == 2 for t in tracks)

    cp = load_carriers(m)
    assert len(cp) == 3
    assert simulation_period(m) == 6

    history = simulate(m, simulation_period(m), cp)
    for cid in cp:
        visited = {history[t].carrier_positions()[cid][0] for t in range(7)}
        assert visited == {"A", "B"}, f"carrier {cid} only saw {visited}"


def test_carriers_periodic():
    """After a full simulation period, all carriers must be back to start."""
    m = tubular_braid_8()
    period = simulation_period(m)
    cp = load_carriers(m)
    history = simulate(m, n_steps=period, carrier_positions=cp)
    s0 = history[0].carrier_positions()
    s_end = history[period].carrier_positions()
    assert s0 == s_end


def test_carriers_follow_tracks():
    """load_carriers produces a valid collision-free simulation.

    For each machine:
    - All initial carrier positions come from the theoretical tracks.
    - The simulation runs collision-free for one full period.
    - Every carrier returns to its starting position after one period.

    The simulation period comes from ``simulation_period``: a carrier holds
    each slot for several steps and must travel its whole track, so the period
    is generally longer than the track length or the gear slot count.
    """
    for factory in [flat_braid_4, flat_braid_9, tubular_braid_8, tubular_braid_12]:
        m = factory()
        tracks = compute_tracks(m)
        track_positions = {pos for track in tracks for pos in track}

        cp = load_carriers(m)

        # Every selected position must come from a theoretical track.
        for cid, pos in cp.items():
            assert pos in track_positions, (
                f"{factory.__name__}: carrier {cid} at {pos} is not on any track"
            )

        period = simulation_period(m)
        # simulate raises CollisionError on any collision — no explicit check needed.
        history = simulate(m, n_steps=period, carrier_positions=cp)

        # After one full period every carrier must be back where it started.
        s0 = history[0].carrier_positions()
        s_end = history[period].carrier_positions()
        assert s0 == s_end, (
            f"{factory.__name__}: carriers did not return to start after period={period}"
        )


@pytest.mark.parametrize(
    "factory",
    [
        flat_braid_3,
        flat_braid_4,
        flat_braid_9,
        tubular_braid_8,
        tubular_braid_12,
        tubular_braid_16,
        diamond_braid,
        mixed_gear_machine,
    ],
)
def test_every_carrier_changes_gear(factory):
    """Every carrier must transfer between gears — that is what braids.

    Regression guard: a carrier sits in a physical slot and keeps its slot
    index while the gear turns, and contact points are fixed in space.  If the
    carrier's index is instead advanced each step it chases the contact point
    and never reaches it, so every carrier spins on its own gear forever and
    no braid is produced.
    """
    m = factory()
    period = simulation_period(m)
    cp = load_carriers(m)
    history = simulate(m, n_steps=period, carrier_positions=cp)

    for cid in cp:
        gears_visited = {
            history[t].carrier_positions()[cid][0] for t in range(period + 1)
        }
        assert len(gears_visited) > 1, (
            f"{factory.__name__}: carrier {cid} never left gear "
            f"{gears_visited.pop()} in {period} steps"
        )


@pytest.mark.parametrize(
    "factory",
    [
        flat_braid_3,
        flat_braid_4,
        flat_braid_9,
        tubular_braid_8,
        tubular_braid_12,
        tubular_braid_16,
        diamond_braid,
        mixed_gear_machine,
    ],
)
def test_carrier_keeps_its_slot_until_it_transfers(factory):
    """A carrier rides in a physical horn and cannot change slot in place.

    Its slot index may only change at the instant it moves to another gear.
    Advancing the index every step instead makes the carrier chase the contact
    point, which is fixed in space, so it can never reach it — the bug that
    left every carrier spinning on its own gear.
    """
    m = factory()
    period = simulation_period(m)
    cp = load_carriers(m)
    history = simulate(m, n_steps=period, carrier_positions=cp)

    for t in range(period):
        now = history[t].carrier_positions()
        nxt = history[t + 1].carrier_positions()
        for cid in cp:
            (g0, s0), (g1, s1) = now[cid], nxt[cid]
            if g0 == g1:
                assert s0 == s1, (
                    f"{factory.__name__}: carrier {cid} jumped {g0}[{s0}]->{g1}[{s1}] "
                    f"at step {t} without leaving the gear"
                )


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


@pytest.mark.parametrize("n_end,expected_slots", [(3, 14), (5, 18), (7, 22)])
def test_odd_end_gears_fuse_the_flat_braid_into_one_track(n_end, expected_slots):
    """An odd end gear returns the carrier on the opposite strand.

    A carrier entering an end gear leaves by the same contact it came in by.
    With an odd slot count it comes back onto the other strand, joining both
    halves into a single closed track that covers every slot.  Even counts
    leave the machine split (see the companion test).
    """
    m = flat_braid_9(n_end=n_end)
    assert m.total_slots() == expected_slots

    tracks = compute_tracks(m)
    assert len(tracks) == 1
    assert len(tracks[0]) == expected_slots


@pytest.mark.parametrize("n_end,expected_tracks", [(4, 4), (6, 2), (8, 8)])
def test_even_end_gears_leave_the_flat_braid_split(n_end, expected_tracks):
    """Even end gears return the carrier to its own strand, so tracks stay separate."""
    m = flat_braid_9(n_end=n_end)
    assert len(compute_tracks(m)) == expected_tracks


def test_tracks_may_overlap_when_carriers_pass_at_different_times():
    """Tracks need not partition the slots.

    Two carriers can cross the same slot at different times without ever
    meeting, so their tracks share it.  ``flat_braid_9(n_end=8)`` does this on
    both interior gears, and placement must cope rather than put two carriers
    in one slot.
    """
    m = flat_braid_9(n_end=8)
    tracks = compute_tracks(m)
    assert sum(len(t) for t in tracks) > m.total_slots()

    cp = load_carriers(m)
    assert len(set(cp.values())) == len(cp), "a slot was given two carriers"
    simulate(m, simulation_period(m), cp)  # raises on any collision


@pytest.mark.parametrize("n_end", [4, 5, 6, 7])
def test_flat_braid_end_gear_slot_count_is_unconstrained(n_end):
    """End gears have one connection, so any slot count stays exact.

    Their single contact can always be put exactly on a slot, and the interior
    gears' two contacts are 180° apart — two slots of a 4-slot gear.
    """
    m = flat_braid_9(n_end=n_end)
    worst = max(offset_residuals(m, compute_layout(m)).values())
    assert math.degrees(worst) < 1.0


@pytest.mark.parametrize("n_end", [5, 6])
def test_flat_braid_loads_half_its_slots(n_end):
    """Half the slots is the most any machine can carry, and both variants reach it.

    At each contact only one of the two meeting slots may hold a carrier, so
    half is the ceiling.
    """
    m = flat_braid_9(n_end=n_end)
    cp = load_carriers(m)
    assert len(cp) == m.total_slots() // 2
    simulate(m, simulation_period(m), cp)  # raises on any collision


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


def test_duplicate_carrier_position_rejected():
    m = flat_braid_4()
    with pytest.raises(ValueError, match="share position"):
        initial_state(m, carrier_positions={0: ("A", 0), 1: ("A", 0)})


# ── Axial columns and tube cores ──────────────────────────────────────────────


@pytest.mark.parametrize(
    "factory", [princess_braid, tubular_braid_8, diamond_braid, flat_braid_3]
)
def test_axials_do_not_disturb_the_simulation(factory):
    """An axial is geometry, not a carrier — it must change nothing dynamic.

    This is the invariant the whole design rests on: an axial holds no slot,
    never moves and cannot collide, so loading, tracks and the period must come
    out identical whether or not the machine carries one.
    """
    m = factory()
    cored = BraidingMachine(
        list(m.gears.values()),
        m.connections,
        axials=[Axial("probe", ("A",))],
    )
    assert load_carriers(cored) == load_carriers(m)
    assert compute_tracks(cored) == compute_tracks(m)
    assert simulation_period(cored) == simulation_period(m)


@pytest.mark.parametrize("n_slots", [3, 5, 7, 9])
def test_soutache_is_two_odd_gears_loaded_every_other_slot(n_slots):
    """Soutache: two gears of the same odd slot count, half of them loaded.

    Every slot sits on its own two-position track, so the machine repeats in
    2 x n_slots steps, and both gears have a single connection so the layout is
    exact whatever the slot count.
    """
    m = soutache_braid(n_slots=n_slots)
    assert len(m.gears) == 2
    assert {g.n_slots for g in m.gears.values()} == {n_slots}
    assert m.total_slots() == 2 * n_slots

    cp = load_carriers(m)
    assert len(cp) == n_slots, "every other slot carries a spool"
    assert simulation_period(m) == 2 * n_slots
    simulate(m, simulation_period(m), cp)  # raises on any collision

    worst = max(offset_residuals(m, compute_layout(m)).values())
    assert math.degrees(worst) < 1.0


def test_princess_carries_eight_carriers_around_a_cord():
    """Princess: 5/6/5 gears, 8 carriers, cord up the centre gear's spindle.

    The carrier count is the regression guard that matters here — a greedy
    loader finds only 7, and the machine genuinely holds 8.
    """
    m = princess_braid()
    assert [g.n_slots for g in m.gears.values()] == [5, 6, 5]
    assert m.total_slots() == 16

    cp = load_carriers(m)
    assert len(cp) == 8, "princess 5/6/5 carries eight"
    assert len(compute_tracks(m)) == 1, "princess should be one interlinked track"
    simulate(m, simulation_period(m), cp)  # raises on any collision

    cord = m.axials[0]
    assert cord.name == "cord"
    assert cord.anchor == ("B",)

    # The cord stands at the centre gear, so it clears that gear's radius.
    layout = compute_layout(m)
    position = axial_position(m, layout, cord)
    assert position == pytest.approx(layout["B"])
    assert axial_clearance(m, layout, position) == pytest.approx(
        gear_radii(m)["B"], abs=1e-9
    )


@pytest.mark.parametrize(
    "factory",
    [princess_braid, flat_braid_9, tubular_braid_8, diamond_braid, mixed_gear_machine],
)
def test_loading_reaches_half_the_slots(factory):
    """Half the slots is the ceiling, and these machines all reach it.

    Only one of the two slots meeting at a contact may be occupied, so half is
    the most any machine can hold.  Loading is solved exactly rather than
    greedily, so falling short here means a real regression.
    """
    m = factory()
    assert len(load_carriers(m)) == m.total_slots() // 2


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


@pytest.mark.parametrize(
    "factory",
    [
        flat_braid_3,
        flat_braid_4,
        flat_braid_9,
        tubular_braid_8,
        tubular_braid_12,
        tubular_braid_16,
        diamond_braid,
        mixed_gear_machine,
    ],
)
def test_example_machines_valid(factory):
    m = factory()
    assert m.total_slots() > 0
    tracks = compute_tracks(m)
    assert sum(len(t) for t in tracks) == m.total_slots()


# ── Animation continuity ───────────────────────────────────────────────────────


# ── One cycle, and round again ────────────────────────────────────────────────


@pytest.mark.parametrize(
    "factory",
    [
        flat_braid_3,
        flat_braid_4,
        flat_braid_9,
        soutache_braid,
        princess_braid,
        tubular_braid_8,
        tubular_braid_12,
    ],
)
def test_a_cycle_puts_every_carrier_back_where_it_started(factory):
    """Each bobbin at its own place again — and nothing shorter does it."""
    m = factory()
    period = state_period(m)
    assert period is not None

    history = simulate(m, period, m.default_carriers())
    start = carrier_places(m, history[0])
    assert carrier_places(m, history[period]) == start
    assert all(carrier_places(m, history[t]) != start for t in range(1, period))


def test_diamond_braid_is_tubular_braid_8_relabelled():
    """The 2x2 grid and the 4-gear ring are one machine, so one must delegate.

    Both are a 4-cycle of 4-slot gears with alternating rotations.  If they
    ever diverge, one of them has been edited without the other.
    """
    from networkx.algorithms.isomorphism import (
        GraphMatcher,
        categorical_node_match,
    )

    d, t = diamond_braid(), tubular_braid_8()

    def annotated(m):
        g = m.graph.copy()
        for name, gear in m.gears.items():
            g.nodes[name]["spec"] = (gear.n_slots, gear.direction)
        return g

    matcher = GraphMatcher(
        annotated(d), annotated(t), node_match=categorical_node_match("spec", None)
    )
    assert matcher.is_isomorphic(), "diamond and tubular_8 have diverged"

    assert d.total_slots() == t.total_slots()
    assert len(load_carriers(d)) == len(load_carriers(t))
    assert simulation_period(d) == simulation_period(t)
    assert sorted(len(x) for x in compute_tracks(d)) == sorted(
        len(x) for x in compute_tracks(t)
    )


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


def test_flat_braids_have_no_circulation():
    """There is no way round a chain, so nothing circulates."""
    for factory in (flat_braid_3, flat_braid_9, soutache_braid, princess_braid):
        m = factory()
        assert ring_order(m) is None
        for pos in load_carriers(m).values():
            assert circulation(m, pos) == 0


@pytest.mark.parametrize(
    "factory", [flat_braid_3, flat_braid_4, soutache_braid, princess_braid]
)
def test_a_gear_is_never_left_bare_while_the_machine_runs(factory):
    """Carriers must stay spread over the gears for the whole run, not just at t=0.

    Carriers drift from gear to gear as the machine turns, so a loading that
    looks well spread at the start can pile every one of them onto a single
    gear a step later.  A three-carrier flat braid did exactly that, leaving
    the other gear empty and the braid momentarily undone, and nothing
    collided so the simulation never objected.
    """
    m = factory()
    period = simulation_period(m)
    history = simulate(m, period, load_carriers(m))

    for state in history[:-1]:
        busy = {c.gear for c in state.carriers}
        assert busy == set(m.gears), (
            f"at step {state.time} gear(s) {sorted(set(m.gears) - busy)} carry nothing"
        )


def test_soutache_is_threaded_every_other_slot():
    """Soutache wants its spools spread, not bunched up on one side of a gear."""
    m = soutache_braid()
    placed = set(load_carriers(m).values())

    crowded = sum(
        1
        for name, gear in m.gears.items()
        for slot in range(gear.n_slots)
        if (name, slot) in placed and (name, (slot + 1) % gear.n_slots) in placed
    )
    # Three carriers on a five-slot gear must crowd once; more means bunching.
    assert crowded <= 1, f"{sorted(placed)} bunches carriers together"


def test_the_stored_track_is_not_a_path():
    """Guard the distinction the drawing bug turned on.

    flat_braid_9's track genuinely contains slots that sit next to each other
    in the list while being far apart in time, so anything that needs the real
    path must walk it rather than read the track.
    """
    m = flat_braid_9()
    track = compute_tracks(m)[0]

    jumps = [
        (track[i], track[(i + 1) % len(track)])
        for i in range(len(track))
        if track[i][0] != track[(i + 1) % len(track)][0]
        and not m.graph.has_edge(track[i][0], track[(i + 1) % len(track)][0])
    ]
    assert jumps, "if this track became a path, the walk above can be simplified"

    # Walking it never does that.
    path = walk(m, track[0], simulation_period(m))
    for here, nxt in zip(path, path[1:]):
        assert here[0] == nxt[0] or m.graph.has_edge(here[0], nxt[0])
