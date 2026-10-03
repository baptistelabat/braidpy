# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids on a ring of slots, and the shape a laid rope takes."""

import math

import pytest

from braidpy.annulus_braid import (
    helix_clearance,
    lay_radius,
    minimum_lay,
    packing_radius,
    rope,
    rope_helices,
    wrap_crossing,
    tubular_paths,
    turn,
)
from braidpy.parametric_braid import closest_approach


# ── The word ──────────────────────────────────────────────────────────────────


def test_a_turn_is_not_a_crossing():
    """Nobody passes anybody when the whole ring goes round together.

    This is what separates a rope from a braid, and it is the reason a rope
    has a shape anyone can write down.
    """
    paths = tubular_paths(rope(3), 3)
    assert all(all(sign == 0 for sign in path.signs) for path in paths)
    assert all(path.turns == 1.0 for path in paths)
    # The unwrapped slot number counts on past the last slot, not resetting.
    assert paths[0].slots == (0, 1, 2, 3)


def test_a_crossing_sends_one_strand_outside_and_one_in():
    assert sorted(path.signs[0] for path in tubular_paths([1], 3)) == [-1, 0, 1]
    assert tubular_paths([-1], 3)[0].signs[0] == -tubular_paths([1], 3)[0].signs[0]


def test_the_wrapping_crossing_carries_a_strand_round():
    """Index N joins the last slot to slot zero, which a line cannot do."""
    paths = tubular_paths([wrap_crossing(3)], 3)
    assert paths[0].slots == (0, -1), "slot zero steps back a lap"
    assert paths[2].slots == (2, 3), "the last carries on round"


def test_a_tubular_braid_sends_its_strands_both_ways():
    paths = tubular_paths([1, 3, wrap_crossing(4), 2], 4)
    assert sorted(path.turns for path in paths) == [-0.5, -0.5, 0.5, 0.5]


def test_a_move_the_ring_does_not_have_is_refused():
    with pytest.raises(ValueError, match="not one of this ring"):
        tubular_paths([9], 3)


def test_turn_and_crossing_indices_do_not_collide():
    assert turn(3) != wrap_crossing(3)
    assert tubular_paths([turn(3)], 3)[0].signs == (0,)
    assert tubular_paths([wrap_crossing(3)], 3)[0].signs != (0,)


# ── The one shape that is closed-form and physical ────────────────────────────


@pytest.mark.parametrize("n_strands", [3, 4, 7])
def test_an_evenly_laid_rope_needs_a_diameter_of_lay_per_strand(n_strands):
    """Strand k is strand 0 slid along the axis by k n-ths of a lay.

    So a point on one and the matching point on another are at the same place
    across the rope and differ only by lay/n of height — and widening the
    rope cannot separate them, being the same point of the same curve.  Below
    n diameters of lay no radius keeps them apart.
    """
    diameter = 0.4
    assert minimum_lay(n_strands, diameter) == pytest.approx(n_strands * diameter)
    with pytest.raises(ValueError, match="too short"):
        lay_radius(n_strands, diameter, lay=minimum_lay(n_strands, diameter) * 0.9)


def test_the_bound_belongs_to_even_lay_and_not_to_braids_in_general():
    """A braid of three strands *can* have a period under three diameters.

    The bound follows from the strands being one curve repeated, so a braid
    whose strands differ from one another escapes it.  Two strands twisting
    around each other are one curve at two phases, and so need only two
    diameters of period; a third strand running alongside them is not a phase
    of that curve and adds no constraint on the period at all.
    """
    diameter, period = 0.4, 1.0
    assert period < 3 * diameter, "the claim under test is that this is possible"
    assert period > minimum_lay(2, diameter), "the twisting pair still binds"

    pair = rope_helices(
        2,
        diameter=diameter,
        length=period,
        turns=1.0,
        radius=lay_radius(2, diameter, lay=period),
    )

    class Straight:
        """A strand running straight up the braid, beside the twisting pair."""

        length = period

        def __init__(self, across: float) -> None:
            self.across = across

        def position(self, z):
            return (self.across, 0.0, z)

    beside = Straight(pair[0].radius + diameter + 0.05)
    assert closest_approach([*pair, beside], 600) >= diameter - 1e-6


@pytest.mark.parametrize("n_strands", [3, 4, 7])
def test_a_ropes_radius_is_set_by_contact_not_chosen(n_strands):
    """Nothing holds the strands out there: they are resting on one another.

    A helix of smaller radius is shorter, so tension pulls the strands in
    until they touch.  Where that is depends on the lay, and the answer is a
    search rather than a formula.
    """
    diameter = 0.4
    lay = minimum_lay(n_strands, diameter) * 2.0
    radius = lay_radius(n_strands, diameter, lay)
    helices = rope_helices(
        n_strands, diameter=diameter, length=lay, turns=1.0, radius=radius
    )
    assert closest_approach(helices, 600) == pytest.approx(diameter, abs=2e-3)


@pytest.mark.parametrize("n_strands", [3, 4, 7])
def test_squeezing_a_rope_tighter_makes_the_strands_overlap(n_strands):
    """Which is what makes that radius the smallest one, not merely one."""
    diameter = 0.4
    lay = minimum_lay(n_strands, diameter) * 2.0
    settled = lay_radius(n_strands, diameter, lay)
    for shrink in (0.95, 0.8, 0.5):
        assert helix_clearance(n_strands, settled * shrink, lay) < diameter


@pytest.mark.parametrize("n_strands", [3, 4, 7])
def test_the_packing_formula_is_the_limit_of_no_lay_at_all(n_strands):
    """d / (2 sin(pi/n)) is the cross-section answer, exact only for straight
    strands.

    Twist them and they come closer than it says, because a strand's
    neighbour is nearer at another height than alongside it — so the radius
    a real rope needs is always larger, tending to this as the lay grows.
    """
    diameter = 0.4
    packing = packing_radius(n_strands, diameter)
    assert helix_clearance(n_strands, packing, lay=1e5) == pytest.approx(
        diameter, abs=1e-3
    ), "with no twist, packing is right"

    radii = [
        lay_radius(n_strands, diameter, lay=minimum_lay(n_strands, diameter) * factor)
        for factor in (1.5, 3.0, 6.0)
    ]
    assert radii == sorted(radii, reverse=True), radii
    assert all(radius > packing for radius in radii)
    assert radii[-1] == pytest.approx(packing, rel=0.05)


def test_the_helix_clearance_formula_agrees_with_measuring_it():
    diameter, n_strands = 0.4, 3
    lay = 2.0
    for radius in (0.25, 0.4, 0.8):
        helices = rope_helices(
            n_strands, diameter=diameter, length=lay, turns=1.0, radius=radius
        )
        assert helix_clearance(n_strands, radius, lay) == pytest.approx(
            closest_approach(helices, 700), abs=2e-3
        )


def test_a_ropes_strands_are_evenly_spaced_helices():
    helices = rope_helices(3, diameter=0.4, length=3, turns=1.0)
    phases = sorted(math.degrees(helix.phase) % 360 for helix in helices)
    assert phases == pytest.approx([0.0, 120.0, 240.0])
    for helix in helices:
        radii = [math.hypot(*helix.position(3 * step / 50)[:2]) for step in range(50)]
        assert max(radii) - min(radii) < 1e-12, "a helix keeps its radius"


def test_a_rope_needs_two_strands_to_rest_on_each_other():
    with pytest.raises(ValueError, match="at least two strands"):
        packing_radius(1, 0.4)


# ── A braided tube, after the geometric model ─────────────────────────────────
