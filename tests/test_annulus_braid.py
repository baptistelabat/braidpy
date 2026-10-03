# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids on a ring of slots, and the shape a laid rope takes."""

import math

import pytest

from braidpy.annulus_braid import (
    TubularBraidStrand,
    helix_clearance,
    lay_radius,
    minimum_lay,
    packing_radius,
    rope,
    rope_helices,
    wrap_crossing,
    cover_factor,
    crossing_binds_above,
    radius_for_cover,
    tubular_braid,
    tubular_braid_clearance,
    tubular_braid_radius,
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


def test_the_strands_alternate_direction_round_the_tube():
    """Which is what makes it braid rather than merely wind.

    Spaced evenly and alternating, two strands that cross meet where the
    radial swing is at its extreme — one fully out, the other fully in.
    """
    strands = tubular_braid(6, radius=1.0, braid_angle=math.radians(45))

    assert [strand.direction for strand in strands] == [1, -1, 1, -1, 1, -1]
    phases = [math.degrees(strand.phase) for strand in strands]
    assert phases == pytest.approx([0.0, 60.0, 120.0, 180.0, 240.0, 300.0])
    assert all(isinstance(strand, TubularBraidStrand) for strand in strands)


def test_a_tube_needs_an_even_number_of_strands_and_a_real_braid_angle():
    with pytest.raises(ValueError, match="even number of strands"):
        tubular_braid(5)
    with pytest.raises(ValueError, match="does not wind round"):
        tubular_braid(6, braid_angle=0.0)
    with pytest.raises(ValueError, match="does not wind round"):
        tubular_braid(6, braid_angle=math.pi / 2)


def test_two_crossing_strands_are_twice_the_bulge_apart():
    """The model's one promise, and it is about the crossings only.

    Where a strand going one way meets one going the other, the swing has
    carried one fully out and the other fully in, so their radii differ by
    twice the bulge — half a diameter each way, by default.
    """
    diameter, bulge = 0.4, 0.2
    strands = tubular_braid(6, 1.0, math.radians(45), diameter, bulge=bulge)

    out, back = strands[0], strands[1]
    period = out.length
    gaps = []
    for step in range(2000):
        z = period * step / 2000
        here, there = out.position(z), back.position(z)
        angle = abs(
            (math.atan2(here[1], here[0]) - math.atan2(there[1], there[0]))
            % (2 * math.pi)
        )
        if min(angle, 2 * math.pi - angle) < 1e-2:  # they are at the same angle
            gaps.append(abs(math.hypot(*here[:2]) - math.hypot(*there[:2])))
    assert gaps, "the two strands should cross within a period"
    assert max(gaps) == pytest.approx(2 * bulge, abs=1e-2)


def test_the_braid_angle_belongs_to_the_mean_helix_not_to_every_point():
    """Once round the tube takes 2 pi R cot(q), and the *mean* helix runs at q.

    The swing makes the local angle wander either side of the nominal one,
    and biases it upward: swinging out and in adds path across the tube but
    none along it.  So the nominal angle is recovered exactly with no swing
    and only approximately with one — worth knowing before anyone measures a
    braid angle off a picture.
    """
    import numpy as np

    radius, angle = 1.0, math.radians(50)

    def local_angles(bulge):
        strand = tubular_braid(8, radius, angle, bulge=bulge)[0]
        points = np.array(
            [strand.position(strand.length * step / 400) for step in range(401)]
        )
        steps = np.diff(points, axis=0)
        return np.degrees(np.arctan2(np.linalg.norm(steps[:, :2], axis=1), steps[:, 2]))

    strand = tubular_braid(8, radius, angle)[0]
    assert strand.length == pytest.approx(2 * math.pi * radius / math.tan(angle))

    plain = local_angles(0.0)
    assert plain.max() - plain.min() < 1e-9, "no swing, no wander"
    # Chords understate an arc, so the sampled angle sits a whisker low.
    assert plain.mean() == pytest.approx(math.degrees(angle), abs=1e-2)

    swung = local_angles(0.2)
    assert swung.max() - swung.min() > 5.0, "the swing should show"
    assert swung.mean() > math.degrees(angle), "and should bias it upward"
    assert swung.mean() == pytest.approx(math.degrees(angle), abs=6.0)


def test_the_symmetry_shortcut_gets_the_same_clearance():
    """Turning the tube two places carries the braid onto itself, so most
    pairs are repeats — and the search would not finish without using that."""
    strands = tubular_braid(8, 1.0, math.radians(45), 0.4)
    assert tubular_braid_clearance(strands, 400) == pytest.approx(
        closest_approach(strands, 400), abs=1e-6
    )


@pytest.mark.parametrize(
    "n_strands,degrees",
    [(4, 45), (6, 45), (8, 45), (16, 45), (8, 30), (8, 70), (4, 75)],
)
def test_the_radius_formula_is_the_radius(n_strands, degrees):
    """Derived, not searched — and the geometry has to bear it out.

    At the radius the formula gives, the strands are exactly twice the bulge
    apart, which is the most the model allows; a whisker narrower and they
    are closer than that.
    """
    diameter, angle = 0.4, math.radians(degrees)
    radius = tubular_braid_radius(n_strands, diameter, angle)

    at_it = tubular_braid_clearance(
        tubular_braid(n_strands, radius, angle, diameter), 700
    )
    assert at_it == pytest.approx(diameter, abs=1e-3)

    inside = tubular_braid_clearance(
        tubular_braid(n_strands, radius * 0.97, angle, diameter), 700
    )
    assert inside < at_it, "narrower should be tighter"


def test_which_condition_binds_says_what_holds_the_tube_open():
    """Two conditions, and they change places near 45 degrees.

    Below the crossover the tube is held open by the strands' own swing —
    so the radius does not depend on the braid angle at all.  Above it, by
    how fast they climb past one another, and the angle is everything.
    """
    diameter, n_strands = 0.4, 8
    shallow = math.radians(30)
    steep = math.radians(70)

    assert not crossing_binds_above(n_strands, shallow)
    assert crossing_binds_above(n_strands, steep)

    # Below the crossover, the angle makes no difference.
    assert tubular_braid_radius(n_strands, diameter, math.radians(20)) == pytest.approx(
        tubular_braid_radius(n_strands, diameter, shallow)
    )

    # Above it, the radius follows tan q.
    ratio = tubular_braid_radius(
        n_strands, diameter, math.radians(75)
    ) / tubular_braid_radius(n_strands, diameter, steep)
    assert ratio == pytest.approx(
        math.tan(math.radians(75)) / math.tan(steep), rel=1e-9
    )

    # The crossover tends to 45 degrees as strands are added.
    crossovers = [
        math.degrees(math.atan(math.sqrt(1 + 4 / n**2))) for n in (4, 8, 16, 48)
    ]
    assert crossovers == sorted(crossovers, reverse=True)
    assert crossovers[-1] == pytest.approx(45.0, abs=0.1)


def test_a_tube_too_narrow_crowds_its_strands_between_the_crossings():
    """The model's promise is about crossings; the rest has to be measured."""
    diameter = 0.4
    settled = tubular_braid_radius(6, diameter, math.radians(45))

    assert settled > packing_radius(6, diameter), "wider than merely seated"
    for shrink in (0.9, 0.7, 0.5):
        assert (
            tubular_braid_clearance(
                tubular_braid(6, settled * shrink, math.radians(45), diameter), 400
            )
            < diameter * 0.99
        )


def test_more_strands_and_a_steeper_braid_both_want_a_fatter_tube():
    diameter = 0.4
    by_count = [tubular_braid_radius(n, diameter, math.radians(45)) for n in (4, 6, 8)]
    assert by_count == sorted(by_count), by_count

    by_angle = [
        tubular_braid_radius(6, diameter, math.radians(degrees))
        for degrees in (50, 60, 70)
    ]
    assert by_angle == sorted(by_angle), by_angle


def test_cover_says_how_tight_the_braid_is():
    """The measure a braider cares about: how much surface the strands hide."""
    diameter, n_strands, angle = 0.4, 8, math.radians(45)

    full = radius_for_cover(n_strands, diameter, angle, cover=1.0)
    assert cover_factor(n_strands, full, angle, diameter) == pytest.approx(1.0)

    half = radius_for_cover(n_strands, diameter, angle, cover=0.5)
    assert half == pytest.approx(2 * full), "half the cover, twice the radius"

    # A steeper braid hides more at a given radius: each strand cuts a
    # circumferential line in a longer segment.
    steep = cover_factor(n_strands, full, math.radians(65), diameter)
    assert steep > cover_factor(n_strands, full, angle, diameter)

    with pytest.raises(ValueError, match="not a fraction"):
        radius_for_cover(n_strands, diameter, angle, cover=0.0)


def test_the_round_strand_model_cannot_make_a_tight_tube():
    """A finding about the model, kept where it will be noticed.

    At the tightest radius that does not crowd, it covers about 0.4 of the
    tube whatever the strand count or the braid angle — so a braid drawn
    from it looks open, and tightening it makes the strands overlap.  Two
    strands are nearest not at their crossing, where the swing holds them a
    full 2b apart, but just beside it where the swing has decayed; a real
    braid escapes this because yarn flattens and stays proud for longer,
    which is a squarer swing than a sine.
    """
    diameter = 0.4
    covers = []
    for n_strands, degrees in ((4, 45), (8, 45), (16, 45), (8, 65)):
        angle = math.radians(degrees)
        radius = tubular_braid_radius(n_strands, diameter, angle)
        covers.append(cover_factor(n_strands, radius, angle, diameter))
    assert all(0.3 < cover < 0.5 for cover in covers), covers

    # And tightening past it overlaps the strands, by a lot.
    angle = math.radians(45)
    tight = radius_for_cover(8, diameter, angle, cover=0.9)
    assert (
        tubular_braid_clearance(tubular_braid(8, tight, angle, diameter), 400)
        < diameter * 0.7
    )
