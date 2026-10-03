# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The curve braidpy draws through a braid word, written down rather than sampled."""

import pytest

from braidpy.braid import Braid
from braidpy.parametric_strand import (
    LINEAR,
    SMOOTHSTEP,
    ParametricStrand,
    arc_length,
    evaluate_profile,
    strand_paths,
)

FLAT_BRAID = Braid((1, -2) * 3, n_strands=3)


# ── Which strand goes over ────────────────────────────────────────────────────


def test_the_generator_sign_decides_which_strand_goes_over():
    """The whole content of the sign, and the thing a slot-watcher loses.

    Both a generator and its inverse exchange the same two strands, so the
    slots alone cannot tell them apart — only the crossing does.
    """
    forward = strand_paths(Braid((1,), n_strands=2))
    inverse = strand_paths(Braid((-1,), n_strands=2))

    assert [p.slots for p in forward] == [p.slots for p in inverse]
    assert forward[0].signs == (1,) and forward[1].signs == (-1,)
    assert inverse[0].signs == (-1,) and inverse[1].signs == (1,)


def test_a_strand_that_holds_its_slot_stays_on_the_axis():
    path = strand_paths(Braid((1,), n_strands=3))[2]
    assert path.signs == (0,)
    assert path.position(0.5)[1] == 0.0


def test_the_paths_are_the_ones_braidpy_already_drew():
    """Not a second geometry beside `to_parametric_strands`, but the same one."""
    amplitude = 0.2
    mine = strand_paths(FLAT_BRAID, spacing=amplitude, amplitude=amplitude)
    theirs = FLAT_BRAID.to_parametric_strands(amplitude=amplitude)

    n_segments = len(FLAT_BRAID.generators) + 1  # braidpy adds a trailing idle one
    worst = 0.0
    for segment in range(len(FLAT_BRAID.generators)):
        for fraction in (0.0, 0.25, 0.5, 0.75):
            z = segment + fraction
            for strand in range(3):
                here = mine[strand].position(z)
                there = theirs[strand].evaluate(z / n_segments)
                worst = max(worst, abs(here[0] - there[0]), abs(here[1] - there[1]))
    assert worst < 1e-12, f"the two geometries differ by {worst}"


# ── The profiles ──────────────────────────────────────────────────────────────


@pytest.mark.parametrize("profile", [LINEAR, SMOOTHSTEP])
def test_a_profile_runs_from_one_slot_to_the_next(profile):
    assert evaluate_profile(profile, 0.0) == pytest.approx(0.0)
    assert evaluate_profile(profile, 1.0) == pytest.approx(1.0)


def test_the_smoothstep_arrives_parallel_to_the_axis():
    """Which is what makes it the minimum-bending-energy transition."""
    step = 1e-6
    for end in (0.0, 1.0):
        near = evaluate_profile(SMOOTHSTEP, end + (step if end == 0.0 else -step))
        slope = abs(near - evaluate_profile(SMOOTHSTEP, end)) / step
        assert slope < 1e-3, "the cubic should leave and arrive flat"
    assert evaluate_profile(LINEAR, 0.5) == pytest.approx(0.5)


# ── Fitting in with the rest of braidpy ───────────────────────────────────────


def test_a_path_can_be_handed_on_as_a_parametric_strand():
    path = strand_paths(FLAT_BRAID)[0]
    wrapped = path.to_parametric()
    assert isinstance(wrapped, ParametricStrand)
    x, y, z = wrapped.evaluate(0.5)
    assert z == pytest.approx(path.length * 0.5)
    assert (x, y) == pytest.approx(path.position(path.length * 0.5)[:2])


# ── Measuring ─────────────────────────────────────────────────────────────────


def test_a_braided_strand_is_longer_than_the_axis_it_covers():
    path = strand_paths(FLAT_BRAID)[0]
    assert arc_length(path) > path.length
