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
from braidpy.horn_gear.jacquard import (
    JacquardLaceMachine,
    JacquardProgramError,
    jacquard_lace_ring,
    notch_positions,
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
    initial_state,
    load_carriers,
    simulate,
    step,
)
from braidpy.horn_gear.tracks import (
    NoFixedTracks,
    circulation,
    compute_tracks,
    ring_order,
    simulation_period,
    tracks_summary,
)
from braidpy.horn_gear.visualization import animate, visualize_machine

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


def test_tube_axials_handles_several_tubes():
    """A grid of gears has (rows-1)x(cols-1) holes, each getting its own core."""
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

    cores = tube_axials(m)
    assert len(cores) == 2, "a 2x3 grid encloses two holes"
    assert len({c.name for c in cores}) == 2, "cores must be uniquely named"


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


def test_axials_are_drawn_in_every_animation_frame():
    """The column is static, so it must appear in the static view and each frame."""
    m = princess_braid()

    static_names = [t.name for t in visualize_machine(m).data if t.name]
    assert "Axials" in static_names

    fig = animate(m, n_steps=6)
    for frame in fig.frames:
        assert "Axials" in [t.name for t in frame.data if t.name]


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


@pytest.mark.parametrize(
    "factory,n_steps",
    [
        (flat_braid_4, 8),
        (tubular_braid_8, 8),
        (tubular_braid_12, 8),
    ],
)
def test_animation_continuity(factory, n_steps):
    """Carrier (x,y) positions must not jump between consecutive animation frames.

    The maximum acceptable displacement per frame is 2×(arc of one full slot per
    sub-frame).  This is already generous; the original bug produced jumps of a
    full slot (9× larger than a sub-frame arc), which triggers this test easily.
    """
    from braidpy.horn_gear.layout import gear_radii
    from braidpy.horn_gear.visualization import animate

    n_substeps = 9
    machine = factory()
    fig = animate(machine, n_steps=n_steps, n_substeps=n_substeps)

    radii = gear_radii(machine)
    max_r = max(radii.values())
    n_slots_min = min(g.n_slots for g in machine.gears.values())

    # Per-sub-frame arc for one slot on the largest gear.
    # Allow 3× that to accommodate the transfer arc (carrier sweeping to contact).
    arc_per_substep = max_r * 2 * math.pi / n_slots_min / n_substeps
    threshold = arc_per_substep * 3

    frames = list(fig.frames)
    violations = []
    for i in range(len(frames) - 1):
        xs_a = frames[i].data[-1].x
        ys_a = frames[i].data[-1].y
        xs_b = frames[i + 1].data[-1].x
        ys_b = frames[i + 1].data[-1].y
        for j, (xa, ya, xb, yb) in enumerate(zip(xs_a, ys_a, xs_b, ys_b)):
            dist = math.hypot(xb - xa, yb - ya)
            if dist > threshold:
                violations.append((i, j, dist))

    assert not violations, (
        f"Continuity violations (threshold={threshold:.4f}):\n"
        + "\n".join(
            f"  frame {i}→{i + 1}, carrier {j}: jump={d:.4f}"
            for i, j, d in violations[:20]
        )
    )


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


def test_jacquard_has_no_tracks_to_compute():
    """A programmed machine has no closed tracks, and must say so.

    Where a bobbin goes is decided by the programme, not by the wiring, so its
    path need never come back on itself.  Inventing a track or a period here
    would be inventing a fact about the machine.
    """
    m = jacquard_lace_ring(6)
    assert m.has_fixed_tracks is False

    for call in (compute_tracks, simulation_period):
        with pytest.raises(NoFixedTracks, match="driven by a"):
            call(m)

    # An ordinary machine is unaffected.
    assert tubular_braid_8().has_fixed_tracks is True
    assert compute_tracks(tubular_braid_8())


def test_jacquard_is_threaded_one_bobbin_per_notch():
    """A notch is shared by two gears, so there is one bobbin position per contact."""
    m = jacquard_lace_ring(6)
    cp = notch_positions(m)

    assert len(cp) == len(m.connections) == 6
    assert cp == m.default_carriers()
    assert len(set(cp.values())) == len(cp), "two bobbins in one notch"

    simulate(m, 12, cp)  # raises on any collision


def test_jacquard_bobbins_travel_round_the_ring():
    """Fully enabled, every bobbin should work its way round every gear."""
    m = jacquard_lace_ring(6)
    cp = notch_positions(m)
    history = simulate(m, 12, cp)

    for cid in cp:
        visited = {history[t].carrier_positions()[cid][0] for t in range(13)}
        assert visited == set(m.gears), f"bobbin {cid} only reached {sorted(visited)}"


def test_mask_gates_which_gears_turn():
    """A gear left out of the mask must not turn, and one in it must."""
    # Punched step 0 turns everything; step 1 holds C and D.
    m = jacquard_lace_ring(6, [("101010", "010101"), ("100010", "010001")])

    assert m.steps_per_pass == 4, "two mask lines make two simulation steps"
    assert m.turning_gears(0) == frozenset({"A", "C", "E"})
    assert m.turning_gears(1) == frozenset({"B", "D", "F"})
    assert m.turning_gears(2) == frozenset({"A", "E"})
    assert m.turning_gears(3) == frozenset({"B", "F"})

    per_pass = {n: m.rotation(n, m.steps_per_pass) for n in m.gears}
    assert per_pass == {"A": 2, "B": -2, "C": 1, "D": -1, "E": 2, "F": -2}
    assert m.rotation("A", 2 * m.steps_per_pass) == 4
    assert m.rotation("C", 2 * m.steps_per_pass) == 2


def test_a_bobbin_stays_put_while_both_its_gears_are_idle():
    """Nothing moves a bobbin whose own gear and notch-neighbour are both held."""
    # Only A and B ever turn; C..F never do.
    m = jacquard_lace_ring(6, [("100000", "010000")])
    idle = {0: ("C", 0), 1: ("D", 0), 2: ("E", 0)}
    history = simulate(m, 8, idle)
    for state in history:
        assert state.carrier_positions() == idle, "an idle bobbin moved"


def test_a_turning_gear_takes_the_bobbin_from_its_idle_neighbour():
    """The point of interpenetrating gears: one turns while the other stands still.

    A bobbin in the notch shared by A and B is swept out by whichever of the
    two turns — so with A idle and B turning, it ends up on B.
    """
    m = jacquard_lace_ring(6, [("000000", "010000")])
    assert m.turning_gears(0) == frozenset()
    assert m.turning_gears(1) == frozenset({"B"})

    # Find the slot of A that faces B, and put a bobbin in that notch.
    conn = next(c for c in m.connections if {c.gear_a, c.gear_b} == {"A", "B"})
    notch = (conn.gear_a, conn.slot_a0)

    history = simulate(m, 2, {0: notch})
    assert history[1].carrier_positions()[0] == notch, "nothing turned yet"
    assert history[2].carrier_positions()[0][0] == "B", "B should have taken it"


@pytest.mark.parametrize(
    "program,message",
    [
        ([("111111", "000000")], "turns the other way"),
        ([("1010", "0101")], "has 4 bits"),
        ([], "needs a programme"),
        ([("10101x", "010101")], "may only contain 0 and 1"),
        ([("101010",)], "expected a"),
    ],
)
def test_invalid_programmes_are_rejected(program, message):
    with pytest.raises(JacquardProgramError, match=message):
        jacquard_lace_ring(6, program)


def test_touching_gears_may_not_turn_together():
    """Two neighbours turning at once would fight over the notch they share.

    A ring whose gears alternate direction can never express this, because the
    two mask lines already separate the neighbours — so this needs a machine
    built by hand with two touching gears turning the same way.
    """
    gears = [
        HornGear("A", 2, direction=+1),
        HornGear("B", 2, direction=+1),
        HornGear("C", 2, direction=-1),
        HornGear("D", 2, direction=-1),
    ]
    conns = [
        Connection("A", "B", 0, 1),
        Connection("B", "C", 0, 1),
        Connection("C", "D", 0, 1),
        Connection("D", "A", 0, 1),
    ]
    with pytest.raises(JacquardProgramError, match="share a notch"):
        JacquardLaceMachine(gears, conns, [("1100", "0000")])


@pytest.mark.parametrize("n_gears", [3, 5, 2, 0])
def test_jacquard_ring_needs_an_even_number_of_gears(n_gears):
    """Meshing gears turn opposite ways, so a ring cannot have an odd count."""
    with pytest.raises(ValueError, match="even number"):
        jacquard_lace_ring(n_gears)


def test_jacquard_machine_draws():
    """The drawing code is machine-driven, so it must handle a programme."""
    m = jacquard_lace_ring(6, [("101010", "010101"), ("100010", "010001")])
    assert len(visualize_machine(m).data) > 0

    fig = animate(m, n_steps=6)
    assert fig.frames
    for frame in fig.frames:
        assert "Carriers" in [t.name for t in frame.data if t.name]


@pytest.mark.parametrize("n_gears", [4, 6, 8, 12])
def test_lace_bobbin_sits_in_the_notch(n_gears):
    """A bobbin rides inside the notch, not out on the rim.

    Overlapping circles cut a chord between their two crossings; the bobbin
    sits at the middle of it, which lies on the line between the two centres
    and is closer in than either rim.
    """
    m = jacquard_lace_ring(n_gears)
    layout, radii = compute_layout(m), gear_radii(m)
    assert m.gears_interpenetrate is True

    for conn in m.connections:
        a, b = conn.gear_a, conn.gear_b
        centres = math.dist(layout[a], layout[b])
        assert centres < radii[a] + radii[b], "the circles only touch"

        notch = contact_point(m, layout, a, b)
        # On the line of centres, and the same point seen from either gear.
        assert contact_point(m, layout, b, a) == pytest.approx(notch)
        assert math.dist(layout[a], notch) + math.dist(notch, layout[b]) == (
            pytest.approx(centres)
        )
        # Cut back inside both rims.
        assert math.dist(layout[a], notch) < radii[a]

    for gear in m.gears:
        assert carrier_radius(m, layout, gear) < radii[gear]


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


def test_programme_is_drawn_as_a_punchcard():
    """The mask is shown as the punchcard it is, one row per phase.

    The clockwise row of each step is offset half a punch from its
    trigonometric partner, because the two are driven one after the other.
    """
    from braidpy.horn_gear.visualization import _punchcard_traces

    m = jacquard_lace_ring(6, [("101010", "010101"), ("100010", "010001")])
    rows = m.program_rows()
    assert [label for label, _ in rows] == [
        "trigonometric",
        "clockwise",
        "trigonometric",
        "clockwise",
    ]
    assert rows[0][1] == (True, False, True, False, True, False)

    traces = _punchcard_traces(m, compute_layout(m), gear_radii(m), current_phase=0)
    card = next(t for t in traces if t.name == "Programme")

    # Every punch has a place on the card, whether or not it is punched.
    n = len(m.gears)
    assert len(card.x) == len(rows) * n

    # The row being driven is lit, and only the gears turning in it.
    lit = [x for x, size in zip(card.x, card.marker.size) if size == 12]
    assert len(lit) == len(m.turning_gears(0)) == 3

    # A clockwise row sits half a punch right of its trigonometric partner.
    trig_xs = sorted(card.x[:n])
    cw_xs = sorted(card.x[n : 2 * n])
    pitch = trig_xs[1] - trig_xs[0]
    assert cw_xs[0] - trig_xs[0] == pytest.approx(pitch / 2)


GREEN, RED, GREY = "60,170,90", "205,60,55", "140,140,140"


def _disc_colours(figure_or_frame):
    """The fill of every gear disc, in gear order."""
    return [t.fillcolor for t in figure_or_frame.data if t.fill == "toself"]


@pytest.mark.parametrize(
    "factory", [tubular_braid_8, flat_braid_9, princess_braid, diamond_braid]
)
def test_wired_machine_gears_are_coloured_by_direction(factory):
    """Green turns clockwise, red the other way — and a wired machine never stops.

    Every gear of a geared-together machine turns on every step, so none of
    them may be grey, and the colours show the alternation the braid needs.
    """
    m = factory()
    colours = _disc_colours(visualize_machine(m))
    assert len(colours) == len(m.gears)

    for colour, gear in zip(colours, m.gears.values()):
        wanted = GREEN if gear.direction == -1 else RED
        assert wanted in colour, f"gear {gear.name} turns {gear.direction:+d}"
        assert GREY not in colour, "a geared-together machine never holds a gear"


def test_held_gears_are_grey():
    """A gear its programme is not turning goes grey, whichever way it turns."""
    m = jacquard_lace_ring(6, [("101010", "010101"), ("100010", "010001")])
    fig = animate(m, n_steps=4)

    for frame in fig.frames:
        turning = m.turning_gears(frame.name and int(frame.name.split("_")[0]) or 0)
        for colour, (name, gear) in zip(_disc_colours(frame), m.gears.items()):
            if name not in turning:
                assert GREY in colour, f"{name} is held but not grey"
            else:
                wanted = GREEN if gear.direction == -1 else RED
                assert wanted in colour, f"{name} turns {gear.direction:+d}"


@pytest.mark.parametrize("factory", [tubular_braid_8, flat_braid_9, princess_braid])
def test_wired_machines_get_no_punchcard(factory):
    """A machine with no programme has no punchcard to show."""
    from braidpy.horn_gear.visualization import _punchcard_traces

    m = factory()
    assert m.program_rows() is None
    assert _punchcard_traces(m, compute_layout(m), gear_radii(m)) == []


def test_animation_traces_keep_their_identity_between_frames():
    """Only what actually moves may move.

    Plotly pairs traces between frames by position, so a trace has to mean the
    same thing in every frame.  Batching the gear discs by colour broke this:
    one slot held the turning gears in one frame and the held ones in the next,
    and the circles appeared to fly around the machine instead of just
    changing colour.  The same trap catches the punchcard if its lit and unlit
    punches are split into separate traces.
    """
    m = jacquard_lace_ring(6, [("101010", "010101"), ("100010", "010001")])
    frames = list(animate(m, n_steps=6).frames)
    assert len({len(f.data) for f in frames}) == 1, "trace count changes"

    base = frames[0].data
    for index, trace in enumerate(base):
        moved = any(list(f.data[index].x) != list(trace.x) for f in frames[1:])

        if trace.fill == "toself":  # a gear disc
            assert not moved, f"gear disc {index} moved between frames"
            assert any(
                f.data[index].fillcolor != trace.fillcolor for f in frames[1:]
            ), "a gear disc never changes colour, so nothing shows it turning"

        if trace.name == "Programme":  # the punchcard
            assert not moved, "a punch moved between frames"
            assert any(
                str(f.data[index].marker.color) != str(trace.marker.color)
                for f in frames[1:]
            ), "the punchcard never lights the row being driven"

    # Exactly two things are entitled to move: the tick marks turning with
    # their gears, and the carriers.
    movers = sum(
        any(list(f.data[i].x) != list(tr.x) for f in frames[1:])
        for i, tr in enumerate(base)
    )
    assert movers == 2, f"{movers} traces move, expected the ticks and the carriers"


@pytest.mark.parametrize("n_gears", [6, 12, 24])
def test_lace_carriers_never_jump_across_a_gear(n_gears):
    """A bobbin must be drawn on whatever is actually sweeping it.

    On this machine the gear that moves a bobbin is often *not* the one it is
    recorded on: an idle gear's neighbour reaches into the shared notch and
    takes it.  Drawing it on its own gear leaves it still for the whole step
    and then flings it across to the neighbour — which measured 6.4x a normal
    sub-frame step before this was fixed.
    """
    n_substeps = 9
    m = jacquard_lace_ring(n_gears)
    fig = animate(m, n_steps=4, n_substeps=n_substeps)

    layout = compute_layout(m)
    radius = max(carrier_radius(m, layout, g) for g in m.gears)
    pitch = min(2 * math.pi / g.n_slots for g in m.gears.values())
    smooth = radius * pitch / n_substeps

    carriers = [f.data[-1] for f in fig.frames]
    worst = max(
        math.hypot(xb - xa, yb - ya)
        for a, b in zip(carriers, carriers[1:])
        for xa, ya, xb, yb in zip(a.x, a.y, b.x, b.y)
    )
    assert worst < 3 * smooth, (
        f"a bobbin moved {worst / smooth:.1f}x a normal sub-frame step, so it is "
        f"being drawn on a gear that is not carrying it"
    )


def test_a_bobbin_is_drawn_on_the_gear_that_sweeps_it():
    """The receiving gear carries the bobbin through the step, not the idle one."""
    m = jacquard_lace_ring(6)

    # Find a bobbin whose own gear is idle while a neighbour takes it.
    cp = notch_positions(m)
    history = simulate(m, 2, cp)
    moved = [
        c
        for c in history[0].carriers
        if history[1].carrier_positions()[c.carrier_id][0] != c.gear
    ]
    assert moved, "this programme should hand bobbins over on its first step"

    for c in moved:
        assert c.gear not in m.turning_gears(0), "its own gear should be idle"
        riding = m.riding_position(c.position, 0)
        assert riding == history[1].carrier_positions()[c.carrier_id]
        assert riding[0] in m.turning_gears(0), "drawn on the gear that turns"

    # A wired machine keeps its carriers on their own gear all step.
    wired = tubular_braid_8()
    for gear, slot in load_carriers(wired).values():
        assert wired.riding_position((gear, slot), 0) == (gear, slot)


@pytest.mark.parametrize(
    "factory,expected_paths",
    [
        (tubular_braid_8, 2),
        (tubular_braid_12, 2),
        (tubular_braid_16, 2),
        (diamond_braid, 2),
        (flat_braid_3, 1),
        (flat_braid_9, 1),
        (soutache_braid, 1),
        (princess_braid, 1),
    ],
)
def test_a_track_is_drawn_once_however_many_cycles_share_it(factory, expected_paths):
    """Several carrier cycles can run round the same loop of gears.

    The drawn arc depends only on which gears a carrier crosses, never on the
    slot, so cycles offset from one another by a slot come out as the very same
    closed curve.  Drawing one trace per cycle stacked them invisibly and
    claimed more paths than the machine has: a square braid drew four for the
    two — one each way round the ring — that its braid is actually made of.
    """
    from braidpy.horn_gear.visualization import _track_traces

    m = factory()
    traces = _track_traces(m, compute_layout(m))
    assert len(traces) == expected_paths

    # What is drawn must really be that many distinct curves.
    shapes = {
        (tuple(round(x, 6) for x in t.x), tuple(round(y, 6) for y in t.y))
        for t in traces
    }
    assert len(shapes) == expected_paths, "two traces drew the same curve"

    # Every slot of the machine is accounted for by some drawn path.
    assert sum(len(t) for t in compute_tracks(m)) >= m.total_slots()


def test_ring_braids_run_two_ways_round():
    """A tubular braid is two paths, one clockwise and one anticlockwise."""
    from braidpy.horn_gear.visualization import _track_runs

    for factory in (tubular_braid_8, tubular_braid_12, tubular_braid_16):
        m = factory()
        paths = set()
        for track in compute_tracks(m):
            runs = tuple(g for g, _, _ in _track_runs(track))
            paths.add(min(runs[i:] + runs[:i] for i in range(len(runs))))
        assert len(paths) == 2, f"{factory.__name__} should run two ways round"

        # The two are the same loop of gears walked in opposite directions.
        one, other = (list(p) for p in paths)
        assert sorted(one) == sorted(other)
        assert one != other


def _laps_per_carrier(m):
    """Signed laps each carrier makes round the machine over one period.

    Measured from where the carriers actually are, rather than inferred from
    the tracks, so it is independent of how tracks are computed or drawn.
    """
    from braidpy.horn_gear.layout import carrier_radius
    from braidpy.horn_gear.visualization import slot_offsets

    layout = compute_layout(m)
    offsets = slot_offsets(m, layout)
    radii = {n: carrier_radius(m, layout, n) for n in m.gears}
    hub_x = sum(p[0] for p in layout.values()) / len(layout)
    hub_y = sum(p[1] for p in layout.values()) / len(layout)

    def angle(carrier, time):
        a = offsets[carrier.gear] + m.slot_angle(carrier.gear, carrier.slot, time)
        x = layout[carrier.gear][0] + radii[carrier.gear] * math.cos(a)
        y = layout[carrier.gear][1] + radii[carrier.gear] * math.sin(a)
        return math.atan2(y - hub_y, x - hub_x)

    period = simulation_period(m)
    history = simulate(m, period, load_carriers(m))
    swept = {}
    for t in range(period):
        now = {c.carrier_id: c for c in history[t].carriers}
        nxt = {c.carrier_id: c for c in history[t + 1].carriers}
        for cid, carrier in now.items():
            step_angle = angle(nxt[cid], t + 1) - angle(carrier, t)
            step_angle = (step_angle + math.pi) % (2 * math.pi) - math.pi
            swept[cid] = swept.get(cid, 0.0) + step_angle
    return {cid: total / (2 * math.pi) for cid, total in swept.items()}


@pytest.mark.parametrize(
    "factory", [tubular_braid_8, tubular_braid_12, tubular_braid_16, diamond_braid]
)
def test_ring_braids_are_loaded_with_equal_carriers_each_way(factory):
    """A tubular braid needs as many carriers going one way as the other.

    Which way a carrier travels is decided by the slot it is put in, not by the
    track it lands on: two carriers on the same track circulate opposite ways,
    because one placed there at t=0 sits at a different phase from one that
    arrived.  So a machine can be threaded balanced or lopsided, and the
    loading has to choose — tubular_braid_8 ran six one way against two before
    the loader weighed this, while still being a perfectly good machine.
    """
    m = factory()
    laps = _laps_per_carrier(m)

    assert all(abs(abs(v) - 1.0) < 0.01 for v in laps.values()), (
        "every carrier should make exactly one lap per period"
    )

    clockwise = sum(1 for v in laps.values() if v < 0)
    anticlockwise = sum(1 for v in laps.values() if v > 0)
    assert clockwise == anticlockwise, (
        f"{factory.__name__} is threaded {clockwise} one way against "
        f"{anticlockwise} the other"
    )


@pytest.mark.parametrize(
    "factory", [tubular_braid_8, tubular_braid_12, tubular_braid_16]
)
def test_circulation_agrees_with_the_angle_actually_swept(factory):
    """The combinatorial sense must match the geometric one.

    ``circulation`` counts steps around the connection graph and never looks at
    a layout, so it is worth checking against the angle a carrier really sweeps
    about the machine's centre.
    """
    m = factory()
    period = simulation_period(m)
    laps = _laps_per_carrier(m)

    for cid, pos in load_carriers(m).items():
        steps = circulation(m, pos, period)
        assert steps != 0, "a ring braid's carriers must go somewhere"
        assert (steps > 0) == (laps[cid] > 0), (
            f"carrier {cid} counts {steps} steps round but sweeps {laps[cid]:+.2f} laps"
        )


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


@pytest.mark.parametrize(
    "factory", [tubular_braid_8, soutache_braid, princess_braid, flat_braid_3]
)
def test_a_bobbin_fits_inside_its_notch(factory):
    """A bobbin is drawn to sit in its seat, a little smaller than the notch.

    Plotly sizes markers in pixels while the notches are in layout units, so a
    fixed marker size looks right on one machine and wrong on the next.  The
    size is worked out from the machine's own extent instead, and must come
    out under the notch it sits in but not vanishingly small.
    """
    from braidpy.horn_gear.visualization import (
        _BOBBIN_FILL,
        _carrier_marker_sizes,
    )

    m = factory()
    sizes = _carrier_marker_sizes(m, compute_layout(m), gear_radii(m))
    assert set(sizes) == set(m.gears)

    for gear, size in sizes.items():
        notch = size / _BOBBIN_FILL
        assert size < notch, f"bobbin on {gear} is not smaller than its notch"
        assert size > 8, f"bobbin on {gear} would be too small to see"


def test_bobbins_and_notches_scale_together():
    """Halving the slot spacing must shrink bobbin and notch alike."""
    from braidpy.horn_gear.visualization import _carrier_marker_sizes

    roomy = _carrier_marker_sizes(
        soutache_braid(n_slots=5),
        *(lambda m: (compute_layout(m), gear_radii(m)))(soutache_braid(n_slots=5)),
    )
    crowded = _carrier_marker_sizes(
        soutache_braid(n_slots=9),
        *(lambda m: (compute_layout(m), gear_radii(m)))(soutache_braid(n_slots=9)),
    )
    # More slots on the same gear means a tighter seat for each.
    assert crowded["A"] <= roomy["A"]
