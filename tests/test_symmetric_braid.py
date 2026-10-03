# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Closed-form shape families for braids regular enough to have one."""

import math

import pytest

from braidpy.parametric_braid import closest_approach
from braidpy.symmetric_braid import (
    FigureEightStrand,
    _pair_distance_squared,
    braid_word,
    crossing_clearance,
    figure_eight_clearance,
    figure_eight_strands,
    minimum_period,
    symmetric_contact_needs,
    tightest_figure_eight,
)


# ── It really is the braid it claims to be ────────────────────────────────────


def test_the_figure_eight_family_is_the_classic_flat_braid():
    """Read the word off the curves rather than taking the shape on trust.

    Six crossings to the period, alternating generators of opposite sign:
    (sigma_1 sigma_2^-1)^3, the braid everyone plaits.
    """
    assert braid_word(figure_eight_strands(-1.0, -0.3, 1.0)) == [1, -2] * 3


def test_the_signs_pick_which_of_the_four_equivalent_forms_you_get():
    """Sideways sign relabels the slots; height sign swaps over for under."""
    assert braid_word(figure_eight_strands(1.0, 0.3, 1.0)) == [2, -1] * 3
    assert braid_word(figure_eight_strands(-1.0, 0.3, 1.0)) == [-1, 2] * 3
    assert braid_word(figure_eight_strands(1.0, -0.3, 1.0)) == [-2, 1] * 3


# ── The clearance ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "amplitude,height,period", [(0.4, 0.3, 3.0), (1.0, 0.5, 4.0), (0.35, 0.38, 2.8)]
)
def test_the_clearance_formula_agrees_with_measuring_it(amplitude, height, period):
    """The family's own formula against the general measurement, which knows
    nothing of the family."""
    strands = figure_eight_strands(amplitude, height, period)
    assert figure_eight_clearance(
        amplitude, height, period, n_samples=900
    ) == pytest.approx(closest_approach(strands, 500), abs=2e-3)


def test_a_braid_is_never_wider_apart_than_a_third_of_its_period():
    """Strand k is strand 0 slid along the axis by k thirds of a period.

    So two strands are never further apart than that slide, whatever the
    amplitudes — which is why a period shorter than n diameters cannot be
    braided at all.
    """
    period = 3.0
    for amplitude in (0.2, 1.0, 5.0):
        for height in (0.1, 0.5, 2.0):
            assert (
                figure_eight_clearance(amplitude, height, period, n_samples=300)
                <= period / 3.0 + 1e-9
            )
    assert minimum_period(3, 0.4) == pytest.approx(1.2)


def test_the_cross_section_clearance_is_h_root_three_when_a_is_wide_enough():
    """At a crossing the two strands sit at pi/6 and 5pi/6, so ±H√3/2 apart.

    That is the tightest spot in the cross-section only while A >= 2H; below
    that it slides off the crossing and the clearance is less.
    """
    for height in (0.1, 0.3, 0.7):
        assert crossing_clearance(2 * height, height) == pytest.approx(
            math.sqrt(3) * height
        )
        assert crossing_clearance(10 * height, height) == pytest.approx(
            math.sqrt(3) * height
        )
        assert crossing_clearance(height, height) < math.sqrt(3) * height


def test_the_cross_section_figure_is_only_an_upper_bound():
    """It ignores the axial offset, which is most of what keeps strands apart."""
    amplitude, height, period = 0.4, 0.3, 3.0
    assert figure_eight_clearance(amplitude, height, period) < crossing_clearance(
        amplitude, height
    )


# ── Choosing within the family ────────────────────────────────────────────────


def test_the_tightest_shape_just_touches():
    diameter, period = 0.4, 3.6
    found = tightest_figure_eight(diameter, period)
    assert found is not None
    amplitude, height = found
    clearance = figure_eight_clearance(amplitude, height, period, n_samples=900)
    assert clearance >= diameter - 1e-3
    assert clearance < diameter * 1.05, "it should be resting on its neighbours"


def test_a_period_too_short_for_the_family_gets_no_shape():
    """And well before the n-diameters bound: crowding bites first."""
    diameter = 0.4
    assert minimum_period(3, diameter) == pytest.approx(1.2)
    assert tightest_figure_eight(diameter, 1.5) is None
    assert tightest_figure_eight(diameter, 2.4) is None
    assert tightest_figure_eight(diameter, 3.2) is not None


def test_stretching_the_braid_out_buys_shorter_strands():
    """The longer the period, the less yarn a unit of braid costs."""
    diameter = 0.4
    costs = []
    for period in (3.2, 5.0, 8.0):
        amplitude, height = tightest_figure_eight(diameter, period)
        strand = FigureEightStrand(amplitude, height, period)
        span = sum(
            math.dist(
                strand.position(period * step / 4000),
                strand.position(period * (step + 1) / 4000),
            )
            for step in range(4000)
        )
        costs.append(span / period)
    assert costs == sorted(costs, reverse=True), costs
    assert costs[-1] > 1.0, "a braided strand is longer than the braid"


# ── More strands ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("n_strands", [3, 5, 7])
def test_the_family_braids_at_any_odd_strand_count(n_strands):
    """Every pair crosses twice a period, so there are n(n-1) crossings.

    Each strand sweeps the full width and back once per period, meeting
    every other strand once each way.
    """
    word = braid_word(
        figure_eight_strands(-1.0, -0.3, 1.0, n_strands=n_strands),
        n_samples=60000,
    )
    assert len(word) == n_strands * (n_strands - 1)
    assert all(1 <= abs(generator) < n_strands for generator in word)
    # Both handednesses appear: it braids rather than merely winding.
    assert any(g > 0 for g in word) and any(g < 0 for g in word)


def test_a_five_strand_plait_can_be_drawn_tight():
    diameter = 0.4
    period = 12 * diameter
    found = tightest_figure_eight(diameter, period, n_strands=5)
    assert found is not None
    amplitude, height = found
    assert figure_eight_clearance(amplitude, height, period, 5, 300) == pytest.approx(
        diameter, abs=5e-3
    )


# ── The closed form behind the clearance ──────────────────────────────────────


@pytest.mark.parametrize(
    "amplitude,height,period,n_strands",
    [(0.41, 0.24, 8.0, 3), (0.36, 0.30, 3.2, 3), (0.53, 0.58, 4.8, 5)],
)
def test_the_distance_formula_agrees_with_measuring_it(
    amplitude, height, period, n_strands
):
    """Two variables in closed form, against a grid over two sampled curves."""
    from braidpy.parametric_braid import closest_approach

    strands = figure_eight_strands(amplitude, height, period, n_strands)
    assert figure_eight_clearance(
        amplitude, height, period, n_strands, 300
    ) == pytest.approx(closest_approach(strands, 500), abs=2e-3)


def test_the_clearance_does_not_depend_on_how_finely_it_is_swept():
    """The sweep only picks a starting point; the descent finds the minimum."""
    values = [
        figure_eight_clearance(0.53, 0.58, 4.8, 5, n_samples)
        for n_samples in (60, 120, 300, 700)
    ]
    assert max(values) - min(values) < 1e-6, values


def test_the_crossing_is_the_tightest_spot_only_when_the_swing_is_wide():
    """Why the flat braid has no formula and the braided tube does.

    At w = P/4 the two strands sit either side of the widest part of the
    swing, at the same place across the braid, and the sideways term drops
    out — a point symmetry could name.  But it is a minimum only while
    A >= 4H, and the shapes worth having are well below that, so the
    tightest spot slides off it and has to be searched for.
    """
    assert symmetric_contact_needs(2.0, 0.4)
    assert not symmetric_contact_needs(0.41, 0.24)

    tight = tightest_figure_eight(0.4, 8.0, n_strands=3)
    assert not symmetric_contact_needs(*tight), "the useful shapes are below it"

    # Where the sideways term drops out, the distance is H's alone.
    period, slide = 8.0, 8.0 / 3
    quarter = period / 4
    for amplitude in (0.5, 5.0):
        assert _pair_distance_squared(
            amplitude, 0.3, period, slide, quarter, 1.1
        ) == pytest.approx(
            _pair_distance_squared(0.0, 0.3, period, slide, quarter, 1.1)
        )


def test_the_family_is_not_the_classical_flat_sinnet_of_five():
    """It reproduces the everyday three-strand plait, and then diverges.

    ABOK 2967 moves the outer strands alternately, each travelling right
    across the braid; the family has every strand swinging at once.  The two
    agree at three strands — there is only one way to plait three — and at
    five they are different elements of the braid group, despite having the
    same number of crossings and the same exponent sum.

    Dehornoy reduction decides it: a word equals another exactly when the one
    times the other's inverse reduces to nothing.
    """
    import contextlib
    import io

    from braidpy.braid_catalog import flat_sinnet5
    from braidpy.handles_reduction import dehornoy_reduce_core

    with contextlib.redirect_stdout(io.StringIO()):
        catalogue, _ = flat_sinnet5()
        theirs = list(catalogue.generators)
        mine = braid_word(
            figure_eight_strands(-1.0, -0.3, 1.0, n_strands=5), n_samples=60000
        )

        def same(first, second):
            return not dehornoy_reduce_core(
                list(first) + [-letter for letter in reversed(second)]
            )

        identical = same(theirs, mine)
        shifted = any(
            same(theirs[at:] + theirs[:at], mine) for at in range(len(theirs))
        )
        mirrored = same([-letter for letter in theirs], mine)

    assert len(theirs) == len(mine) == 20, "the same number of crossings"
    assert sum(1 if g > 0 else -1 for g in theirs) == sum(
        1 if g > 0 else -1 for g in mine
    ), "and the same exponent sum"

    assert not identical, "if this fails, the family has been made to match"
    assert not shifted, "nor at any starting height"
    assert not mirrored, "nor as its mirror image"
