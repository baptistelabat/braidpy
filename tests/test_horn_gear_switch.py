# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Switches, and the three-band machine they make possible."""

import pytest

from braidpy.horn_gear.model import BraidingMachine, Connection, HornGear
from braidpy.horn_gear.switch import (
    MULTIBAND_10_15_10_BANDS,
    MULTIBAND_10_15_10_CARRIERS,
    MULTIBAND_10_15_10_SLOTS,
    Switch,
    SwitchedMachine,
    SwitchError,
    band_of,
    multiband_10_15_10,
)
from braidpy.horn_gear.tracks import _follow

SLOTS = MULTIBAND_10_15_10_SLOTS


def positions():
    return [(f"G{i}", s) for i, n in enumerate(SLOTS) for s in range(n)]


def tracks_of(machine, cap=40000):
    """Every closed track of the machine, by following each slot in turn."""
    left, out = set(positions()), []
    while left:
        start = next(iter(left))
        track, _ = _follow(machine, start, cap)
        out.append(track)
        before = len(left)
        left -= set(track)
        if len(left) == before:
            left.discard(start)
    return out


def band_span(track):
    return {int(p[0][1:]) for p in track}


# ── The switch itself ─────────────────────────────────────────────────────────


def test_a_switch_must_name_a_real_connection_gear_and_slot():
    gears = [HornGear("A", 4, direction=+1), HornGear("B", 4, direction=-1)]
    conns = [Connection("A", "B", 0, 0, name="A-B")]

    with pytest.raises(SwitchError, match="does not have"):
        SwitchedMachine(gears, conns, [Switch("nope", "A", {0})])
    with pytest.raises(SwitchError, match="not one of its gears"):
        SwitchedMachine(gears, conns, [Switch("A-B", "C", {0})])
    with pytest.raises(SwitchError, match="only 4"):
        SwitchedMachine(gears, conns, [Switch("A-B", "A", {9})])


def test_a_machine_with_no_switches_behaves_like_an_ordinary_one():
    """The switch is an addition, not a change of rules."""
    gears = [HornGear("A", 4, direction=+1), HornGear("B", 4, direction=-1)]
    conns = [Connection("A", "B", 0, 0, name="A-B")]
    plain = BraidingMachine(gears, conns)
    switched = SwitchedMachine(gears, conns, [])
    for slot in range(4):
        for time in range(8):
            assert switched.next_position(("A", slot), time) == plain.next_position(
                ("A", slot), time
            )


def test_a_switch_keeps_a_carrier_on_its_gear():
    """Declined at the contact, it holds its slot and rides round."""
    gears = [HornGear("A", 4, direction=+1), HornGear("B", 4, direction=-1)]
    conns = [Connection("A", "B", 0, 0, name="A-B")]
    plain = BraidingMachine(gears, conns)
    shut = SwitchedMachine(gears, conns, [Switch("A-B", "A", set())])

    crossed = [
        (slot, t)
        for slot in range(4)
        for t in range(8)
        if plain.next_position(("A", slot), t)[0] == "B"
    ]
    assert crossed, "the plain machine should hand carriers over"
    for slot, t in crossed:
        assert shut.next_position(("A", slot), t) == ("A", slot)


# ── The three-band machine ────────────────────────────────────────────────────


def test_the_line_is_a_palindrome_of_eighty_six_slots():
    """Five-slot gears at the ends, six-slot gears where the bands divide."""
    assert SLOTS == SLOTS[::-1]
    assert len(SLOTS) == 16
    assert sum(SLOTS) == 86
    assert SLOTS[0] == SLOTS[-1] == 5
    assert SLOTS[4] == SLOTS[11] == 6


def test_without_switches_the_same_line_braids_a_single_band():
    """Which is the point of the switches: one line, one circuit, otherwise."""
    machine = multiband_10_15_10()
    plain = BraidingMachine(list(machine.gears.values()), list(machine.connections))
    tracks = tracks_of(plain)
    assert len(tracks) == 1
    assert len(tracks[0]) == sum(SLOTS)


def test_the_switches_divide_the_line_into_three_bands():
    machine = multiband_10_15_10()
    assert len(machine.switches) == 4
    bands = [set(range(first, last + 1)) for first, last in MULTIBAND_10_15_10_BANDS]
    for track in tracks_of(machine):
        assert any(band_span(track) <= band for band in bands), (
            f"a track runs over gears {sorted(band_span(track))}, crossing a band"
        )


def test_every_band_is_actually_used():
    """All three bands carry tracks; none of them is a dead stretch of line."""
    machine = multiband_10_15_10()
    tracks = tracks_of(machine)
    for first, last in MULTIBAND_10_15_10_BANDS:
        band = set(range(first, last + 1))
        assert any(band_span(t) <= band for t in tracks), (
            f"band G{first}..G{last} empty"
        )


def test_the_six_slot_gears_are_shared_between_two_bands():
    """They are what each band turns its carriers back on."""
    shared = [4, 11]
    for gear in shared:
        owning = [
            band
            for band, (first, last) in enumerate(MULTIBAND_10_15_10_BANDS)
            if first <= gear <= last
        ]
        assert len(owning) == 2, f"G{gear} should belong to two bands"
        assert SLOTS[gear] == 6


def test_carriers_never_leave_their_band():
    """Followed from every slot, a carrier stays among its own gears."""
    machine = multiband_10_15_10()
    bands = [set(range(first, last + 1)) for first, last in MULTIBAND_10_15_10_BANDS]
    for start in positions():
        here = {int(start[0][1:])}
        pos = start
        for t in range(400):
            pos = machine.next_position(pos, t)
            here.add(int(pos[0][1:]))
        assert any(here <= band for band in bands), (
            f"a carrier from {start} reached gears {sorted(here)}"
        )


def test_band_of_names_the_band_each_gear_works_for():
    assert band_of("G0") == 0
    assert band_of("G4") == 0  # shared: the first band it belongs to
    assert band_of("G7") == 1
    assert band_of("G15") == 2
    assert band_of("nonsense") is None


def test_the_reference_runs_ten_fifteen_and_ten_carriers():
    """The 10-15-10 of the machine's name, which is not yet reachable.

    Measured band by band the machine holds 7, 21 and 7 -- the right total of
    35, but the wrong split: the middle band has capacity to spare while the
    two outer ones fall three short of the ten the reference runs.  No
    geometrically valid wiring of an outer band does better than 7, and no
    choice of switched slots changes it, so the shortfall is in how braidpy
    loads a 27-slot band of 5-4-4-8-6, not in the switch.

    Relaxing the collision rule at a switched contact
    (:meth:`~braidpy.horn_gear.model.BraidingMachine.contact_exchanges`)
    lifted the whole machine from 19 carriers to 22; the rest of the gap is
    elsewhere.  This records that rather than asserting something weaker.
    """
    import random

    from braidpy.horn_gear.simulation import CollisionError, simulate

    assert MULTIBAND_10_15_10_CARRIERS == (10, 15, 10)
    assert sum(MULTIBAND_10_15_10_CARRIERS) == 35

    machine = multiband_10_15_10()

    def capacity(places, trials=6, steps=120):
        best = 0
        for seed in range(trials):
            rng = random.Random(seed)
            order = list(places)
            rng.shuffle(order)
            placed = []
            for p in order:
                try:
                    simulate(machine, steps, {i: q for i, q in enumerate(placed + [p])})
                except CollisionError:
                    continue
                placed.append(p)
            best = max(best, len(placed))
        return best

    per_band = []
    for first, last in MULTIBAND_10_15_10_BANDS:
        band = [(f"G{i}", s) for i in range(first, last + 1) for s in range(SLOTS[i])]
        per_band.append(capacity(band))

    assert sum(per_band) <= sum(MULTIBAND_10_15_10_CARRIERS), (
        f"the bands now hold {per_band}, totalling more than the reference's "
        f"35 -- the docstring above is out of date"
    )
    assert per_band[1] >= MULTIBAND_10_15_10_CARRIERS[1], (
        "the middle band should have room for its fifteen"
    )
    assert any(
        got < want for got, want in zip(per_band, MULTIBAND_10_15_10_CARRIERS)
    ), "every band now reaches the reference -- update the docstring and switch.py"
