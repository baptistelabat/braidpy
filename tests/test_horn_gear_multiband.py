# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Split gears, and the three-band machine they make: braidpy.horn_gear.multiband."""

import itertools
import math

import pytest

from braidpy.horn_gear.layout import compute_layout, gear_radii, slot_offsets
from braidpy.horn_gear.loading import _fullest_loading
from braidpy.horn_gear.multiband import (
    MULTIBAND_10_15_10_CARRIERS,
    MULTIBAND_10_15_10_LOADING,
    MULTIBAND_10_15_10_SLOTS,
    MULTIBAND_10_15_10_SPLIT,
    MultibandLine,
    band_of,
    multiband_10_15_10,
    multiband_band,
    twin_plait,
)
from braidpy.horn_gear.simulation import simulate
from braidpy.horn_gear.tracks import compute_tracks, simulation_period


def test_a_split_gear_is_two_halves_one_for_each_band():
    """G4 and G11, six horns each, are three for the band on either side."""
    machine = multiband_10_15_10()
    for k in MULTIBAND_10_15_10_SPLIT:
        assert f"G{k}" not in machine.gears
        for half in (f"G{k}a", f"G{k}b"):
            assert machine.gears[half].n_slots == 3
    assert machine.total_slots() == sum(MULTIBAND_10_15_10_SLOTS)


def test_only_an_even_gear_can_be_split():
    with pytest.raises(ValueError, match="not even"):
        MultibandLine((5, 4, 5, 4, 5), (2,))


def test_no_track_leaves_its_band():
    """A half meets only its own band's neighbour, so the three bands never
    exchange a carrier."""
    machine = multiband_10_15_10()
    tracks = compute_tracks(machine)
    for track in tracks:
        assert len({band_of(gear) for gear, _ in track}) == 1
    assert {band_of(gear) for track in tracks for gear, _ in track} == {0, 1, 2}


def test_a_band_alone_braids_as_it_does_in_the_whole_machine():
    """Same gear names, slots and contacts: every slot goes where it goes on
    the whole line."""
    whole = multiband_10_15_10()
    for band in range(3):
        alone = multiband_band(band)
        for gear, spec in alone.gears.items():
            for slot in range(spec.n_slots):
                for time in range(12):
                    assert alone.next_position((gear, slot), time) == (
                        whole.next_position((gear, slot), time)
                    )


@pytest.mark.slow
@pytest.mark.parametrize("band, most", [(0, 12), (1, 19), (2, 12)])
def test_each_band_holds_half_its_slots(band, most):
    """24, 38 and 24 slots: at most half of them carry, as on a flat braid,
    and the exact loading search reaches it."""
    machine = multiband_band(band)
    assert machine.total_slots() == 2 * most
    assert len(_fullest_loading(machine, simulation_period(machine))) == most


def test_the_reference_loading_is_ten_fifteen_and_ten():
    machine = multiband_10_15_10()
    per_band = [0, 0, 0]
    for gear, _ in machine.default_carriers().values():
        per_band[band_of(gear)] += 1
    assert tuple(per_band) == MULTIBAND_10_15_10_CARRIERS
    assert [len(b) for b in MULTIBAND_10_15_10_LOADING] == list(per_band)


def test_the_reference_loading_runs_the_whole_machine_without_a_collision():
    """35 carriers, over the 2280 steps after which every one is back where
    it started."""
    machine = multiband_10_15_10()
    period = simulation_period(machine)
    assert period == 2280
    simulate(machine, period, machine.default_carriers())


@pytest.mark.parametrize("band", [0, 1, 2])
def test_a_band_runs_its_own_loading(band):
    machine = multiband_band(band)
    loading = machine.default_carriers()
    assert len(loading) == MULTIBAND_10_15_10_CARRIERS[band]
    simulate(machine, simulation_period(machine), loading)


def test_a_split_gear_is_drawn_as_one_gear_whole():
    """Both halves on one centre, as large as a six-slot gear, and every
    other pair of neighbours touching rim to rim."""
    machine = multiband_10_15_10()
    layout = compute_layout(machine)
    radii = gear_radii(machine)
    six = gear_radii(MultibandLine((5, 6, 5), ()))["G1"]
    for k in MULTIBAND_10_15_10_SPLIT:
        assert layout[f"G{k}a"] == layout[f"G{k}b"]
        assert radii[f"G{k}a"] == radii[f"G{k}b"] == pytest.approx(six)
    for conn in machine.connections:
        (xa, ya), (xb, yb) = layout[conn.gear_a], layout[conn.gear_b]
        assert math.hypot(xa - xb, ya - yb) == pytest.approx(
            radii[conn.gear_a] + radii[conn.gear_b]
        )


def test_the_six_horns_of_a_split_gear_make_a_regular_hexagon():
    """The line runs straight through a split gear, so each half's three
    horns stand exactly between the other's, 60 degrees apart, at every step
    and every moment of one."""
    machine = multiband_10_15_10()
    offsets = slot_offsets(machine, compute_layout(machine))
    for k in MULTIBAND_10_15_10_SPLIT:
        for time in range(6):
            for frac in (0.0, 0.25, 0.5):
                angles = sorted(
                    (machine.slot_angle(half, slot, time, frac) + offsets[half])
                    % (2 * math.pi)
                    for half in (f"G{k}a", f"G{k}b")
                    for slot in range(3)
                )
                gaps = [b - a for a, b in itertools.pairwise(angles)]
                gaps.append(angles[0] + 2 * math.pi - angles[-1])
                assert gaps == pytest.approx([math.pi / 3] * 6)


def test_the_fold_leaves_the_ends_apart():
    """Folded round, the line's ends come near but do not touch, and no two
    gears but neighbours do."""
    machine = multiband_10_15_10()
    layout, radii = compute_layout(machine), gear_radii(machine)

    def index(name):
        return int(name[1:].rstrip("ab"))

    for a, b in itertools.combinations(layout, 2):
        if abs(index(a) - index(b)) > 1:
            gap = math.dist(layout[a], layout[b]) - radii[a] - radii[b]
            assert gap > 1


def test_band_of_names_each_half_by_the_band_it_serves():
    assert band_of("G4a") == 0
    assert band_of("G4b") == 1
    assert band_of("G11a") == 1
    assert band_of("G11b") == 2
    assert band_of("G0") == 0
    assert band_of("G15") == 2
    assert band_of("nope") is None


def test_the_smallest_multiband_braids_two_plaits():
    """Three gears, 3 6 3, the middle one split: each band is the smallest
    flat braid, three carriers, and the two run together without meeting,
    every carrier back where it started after six steps."""
    machine = twin_plait()
    assert list(machine.gears) == ["G0", "G1a", "G1b", "G2"]
    loading = machine.default_carriers()
    assert len(loading) == 6
    first_band = [gear in ("G0", "G1a") for gear, _ in loading.values()]
    assert first_band.count(True) == first_band.count(False) == 3
    assert simulation_period(machine) == 6
    simulate(machine, 6, loading)
    for track in compute_tracks(machine):
        assert {gear in ("G0", "G1a") for gear, _ in track} in ({True}, {False})


def test_the_whole_machine_and_the_smallest_are_in_braid_studio():
    from braidpy.machine_catalog import CATALOGUE

    for name in ("twin_plait", "multiband_10_15_10"):
        assert CATALOGUE[name].make().total_slots() in (12, 86)
