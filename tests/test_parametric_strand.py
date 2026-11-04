# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The curve braidpy draws through a braid word, written down rather than sampled."""

import math

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


def test_arc_length_is_right_where_it_can_be_checked():
    """A helix of radius R and one turn per unit is sqrt(1 + (2 pi R)^2) long."""
    from braidpy.annulus_braid import Helix

    helix = Helix(radius=0.3, turns=1.0, length=1)
    assert arc_length(helix, 20_000) == pytest.approx(
        math.hypot(1.0, 2 * math.pi * 0.3), rel=1e-6
    )


def test_a_strand_finds_its_arc_as_looking_through_them_all_would():
    """Arcs are found by halving, not one by one: the same arc, the first
    that holds t, at every time — on a boundary, in a gap, at the ends."""
    from braidpy.parametric_strand import combine_arcs

    def arc(k):
        return lambda t: (float(k), t, 0.0)

    # Touching arcs, a gap between the third and the fourth, and one instant.
    spans = [(0.0, 0.25), (0.25, 0.5), (0.5, 0.6), (0.7, 0.7), (0.7, 1.0)]
    arcs = [(t0, t1, arc(k)) for k, (t0, t1) in enumerate(spans)]
    strand = combine_arcs(arcs)

    def by_looking(t):
        for t0, t1, f in arcs:
            if t0 <= t <= t1:
                return f(t)
        raise ValueError

    for t in [0.0, 0.1, 0.25, 0.4, 0.5, 0.55, 0.6, 0.7, 0.8, 1.0]:
        assert strand(t) == by_looking(t)
    for t in [-0.1, 0.65, 1.1]:
        with pytest.raises(ValueError):
            strand(t)


def test_a_long_word_is_laid_in_a_moment():
    """A word of a thousand crossings: its strands are laid in well under a
    second (a fiftieth, here), where they took two — each was worked out from every
    crossing again, and its arcs looked through one by one."""
    import time

    word = [1, 2, -3, 4, -5, 6, 7] * 143
    braid = Braid(word, 8)
    start = time.perf_counter()
    strands = braid.to_parametric_strands()
    for strand in strands:
        for k in range(2001):
            strand.func(k / 2000)
    assert time.perf_counter() - start < 0.5
    assert len(strands) == 8
