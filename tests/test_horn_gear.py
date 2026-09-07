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
    tubular_braid_8,
    tubular_braid_12,
    tubular_braid_16,
)
from braidpy.horn_gear.layout import compute_layout, gear_radii
from braidpy.horn_gear.model import BraidingMachine, Connection, HornGear
from braidpy.horn_gear.simulation import (
    initial_state,
    load_carriers,
    simulate,
    step,
)
from braidpy.horn_gear.tracks import (
    compute_tracks,
    simulation_period,
    tracks_summary,
)
from braidpy.horn_gear.visualization import _offset_residuals

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
    residuals = _offset_residuals(m, compute_layout(m))
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

    worst = max(_offset_residuals(m, compute_layout(m)).values())
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
    worst = max(_offset_residuals(m, compute_layout(m)).values())
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
