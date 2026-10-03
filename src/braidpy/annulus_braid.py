# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: annulus_braid.py
Description: Braids on a ring of slots, and the shape a laid rope takes
Authors: Baptiste Labat
Created: 2025-05-26
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

References on the annular braid group:

- https://people.math.wisc.edu/~aekent2/annular.pdf
- https://www.researchgate.net/publication/228456153_Cohomology_of_Artin_groups_of_type_zAn_Bn_and_applications
- https://math.stackexchange.com/questions/4504420/braid-groups-for-ropes

A flat braid lays its slots out on a line, so a strand that wants to get from
one end to the other has to climb over everyone in between.  An annulus lays
them round a circle, and that changes what a word can ask for:

**A crossing** puts two neighbouring strands past each other.  On a line one
of them goes over; on a ring the depth direction is radial, so one of them
goes *outside* — further from the axis — and the other inside.  A positive
move sends the strand in the lower-numbered slot of the pair outside, which
is the same rule as the flat braid's positive generator sending the lower
strand over.

Slot numbers run ``0`` to ``N-1``, so the pairs run ``(0,1)`` up to
``(N-2,N-1)`` — indices 1 to ``N-1`` — and then ``(N-1,0)``, index ``N``,
which is the pair a flat braid has no room for.  Nothing distinguishes that
pair on the ring: it is the pair whose slot numbers *wrap*, and the wrap
exists only because the numbering has to start somewhere.  Rotate the labels
and a different pair becomes index ``N``.  The annular braid literature
writes this generator as :math:`\\sigma_0` or :math:`\\sigma_N` and says the
indices are read modulo ``N``; :func:`wrap_crossing` is just a name for
``crossing(N)`` so a word reads without the reader counting slots.

**A turn** carries every strand round one slot together.  Nobody passes
anybody and nobody goes outside anybody; the cross-section simply rotates.
On a line there is no such move.  On a ring it is what a rope is.  Index
``N + 1`` names it.

Everything up to :func:`tubular_paths` is bookkeeping — which strand is
where, and which passed outside which — and is exact combinatorics,
checkable against a drawing of the braid.

:func:`rope_helices` is the one piece of *geometry* in braidpy that is both
closed-form and physical, and it is worth being clear about why it can be.
Laying up a rope asks nothing of the strands beyond winding on together, so
their shape is a one-parameter family — helices of radius R — and symmetry
says where they touch without anyone having to search for it.  Minimising
length then drives R down until they do, at :func:`lay_radius`.  Take
away either the symmetry or the absence of crossings and neither step
survives; see ``docs/source/why_no_closed_form.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


def crossing(index: int) -> int:
    """The move that puts slots ``index - 1`` and ``index`` past each other.

    Used positive, the strand in slot ``index - 1`` passes **outside** — at
    the greater radius — and ends up in slot ``index``; the other passes
    inside.  Negate the move to swap who goes outside.

    Args:
        index: Which neighbouring pair, from 1 to ``n_strands``.  The last
            value names the pair ``(n_strands - 1, 0)``, whose slot numbers
            wrap; :func:`wrap_crossing` names it without counting.

    Returns:
        The move, which is the index itself.
    """
    return index


def wrap_crossing(n_strands: int) -> int:
    """The move that crosses the pair whose slot numbers wrap round to zero.

    This is ``crossing(n_strands)``: the pair made of the last slot and slot
    zero.  It is a crossing like any other — the ring has no privileged
    place, and which pair wraps depends only on where the numbering starts.
    What makes it worth a name is that a *flat* braid has no such pair, so
    this is the one crossing that needs the ring.

    Used positive, the strand in the last slot passes outside, and carries on
    round rather than turning back: its winding goes up by one while the
    other strand's goes down.

    Args:
        n_strands: How many slots the ring has.

    Returns:
        The move, which is ``n_strands``.
    """
    return n_strands


def turn(n_strands: int) -> int:
    """The move that carries every strand round one slot, passing nobody.

    Nobody is outside or inside anybody — the whole cross-section rotates.
    Used positive it turns towards increasing slot numbers.

    Args:
        n_strands: How many slots the ring has.

    Returns:
        The move, which is ``n_strands + 1``.
    """
    return n_strands + 1


def rope(n_strands: int) -> List[int]:
    """The word for a rope: every strand round together, once round the tube.

    Laying up a rope is not a sequence of crossings — no strand climbs over
    another — it is the cross-section turning.

    Args:
        n_strands: How many strands are laid up.

    Returns:
        The word, one turn per slot, which brings every strand home.
    """
    return [turn(n_strands)] * n_strands


@dataclass(frozen=True)
class TubularStrandPath:
    """Where one strand goes round a tubular braid, and what it passed.

    This records the braid's *combinatorics*, not a shape: which slot the
    strand occupies at each step and which side of each crossing it took.
    Turning that into a curve is the part that has no general answer.

    Args:
        slots: Its unwrapped slot number at each of ``len(signs) + 1``
            instants — it counts on past the last slot rather than resetting
            to zero, so that going round reads as carrying on.
        signs: Per move, +1 if it passed outside — further from the axis —
            -1 if inside, 0 if it passed nobody.  The two strands of a
            crossing always get +1 and -1; a turn gives everyone 0.
        n_slots: How many slots the ring has.
    """

    slots: Tuple[int, ...]
    signs: Tuple[int, ...]
    n_slots: int

    @property
    def length(self) -> int:
        """The braid's period along its axis, one unit per move."""
        return len(self.signs)

    @property
    def turns(self) -> float:
        """How many times round the tube the strand goes in one period."""
        return (self.slots[-1] - self.slots[0]) / self.n_slots


def tubular_paths(moves: Sequence[int], n_strands: int) -> List[TubularStrandPath]:
    """Follow every strand round a tubular braid word.

    Args:
        moves: The word.  ``±i`` for ``i`` in 1..``n_strands - 1`` crosses
            slots ``i-1`` and ``i``; ``±n_strands`` crosses the wrapping pair
            ``(n_strands - 1, 0)``; ``±(n_strands + 1)`` turns the whole
            ring; ``0`` does nothing.  A positive crossing sends the strand
            in the lower-numbered slot outside, at the greater radius.
        n_strands: How many strands, which is how many slots the ring has.

    Returns:
        One path per strand, in strand order.

    Raises:
        ValueError: If a move names something the ring does not have.
    """
    n_slots = n_strands
    ring = list(range(n_strands))  # ring[slot] = strand standing there
    winding = [0] * n_strands  # how many times round each strand has gone
    slots: List[List[int]] = [[strand] for strand in range(n_strands)]
    signs: List[List[int]] = [[] for _ in range(n_strands)]

    def place(strand: int) -> int:
        return ring.index(strand) + n_slots * winding[strand]

    for move in moves:
        index = abs(move)
        step_signs = [0] * n_strands

        if index == 0:
            pass
        elif index == turn(n_strands):
            # Everyone round one slot together: nobody passes anybody, and
            # whoever leaves the last slot has been round once more.
            direction = 1 if move > 0 else -1
            for strand in range(n_strands):
                here = ring.index(strand)
                if direction > 0 and here == n_slots - 1:
                    winding[strand] += 1
                elif direction < 0 and here == 0:
                    winding[strand] -= 1
            ring = ring[-direction:] + ring[:-direction]
        elif 1 <= index <= n_strands:
            lower = index - 1
            upper = index % n_slots  # index == n_strands wraps round to zero
            low_strand, high_strand = ring[lower], ring[upper]
            if upper == 0:
                # The wrapping pair: the one in the last slot carries on
                # round, the one in slot zero steps back a lap.
                winding[low_strand] += 1
                winding[high_strand] -= 1
            ring[lower], ring[upper] = high_strand, low_strand
            outside, inside = (
                (low_strand, high_strand) if move > 0 else (high_strand, low_strand)
            )
            step_signs[outside] = 1
            step_signs[inside] = -1
        else:
            raise ValueError(
                f"Move {move} is not one of this ring's: crossings 1 to "
                f"{n_strands}, a turn at {turn(n_strands)}, or 0 for nothing."
            )

        for strand in range(n_strands):
            slots[strand].append(place(strand))
            signs[strand].append(step_signs[strand])

    return [
        TubularStrandPath(
            slots=tuple(slots[strand]),
            signs=tuple(signs[strand]),
            n_slots=n_slots,
        )
        for strand in range(n_strands)
    ]


def packing_radius(n_strands: int, diameter: float) -> float:
    """The radius ``n`` *parallel* strands sit at when they touch their neighbours.

    Evenly spaced round a circle, strands touch when the chord between two
    neighbours is one diameter:

    .. math:: R = \\frac{d}{2 \\sin(\\pi / n)}

    This is the cross-section packing answer, and it is exact only for
    strands that run straight — a rope with no lay at all.  Twist them and
    they come closer than this says, because a strand's neighbour is nearer
    at a different height than alongside it: at the tightest lay they can be
    made at, three strands at this radius clear 0.76 of a diameter, and the
    shortfall barely eases with more strands — 0.71 at twelve.  For a rope
    with an actual lay use :func:`lay_radius`, which solves for it.

    Args:
        n_strands: How many strands are laid up.
        diameter: How thick they are.

    Returns:
        The radius at which parallel neighbours just touch.

    Raises:
        ValueError: If there are fewer than two strands to touch.
    """
    if n_strands < 2:
        raise ValueError("A rope needs at least two strands to rest on each other.")
    return diameter / (2.0 * math.sin(math.pi / n_strands))


def minimum_lay(n_strands: int, diameter: float) -> float:
    """The shortest lay an *evenly laid* rope of this thickness can have.

    Strand ``k`` of an evenly laid rope is strand 0 slid along the axis by
    ``k`` n-ths of a lay — the strands are one helix, repeated at ``n``
    phases.  So take a point on one and the matching point on another: they
    are at the same place across the rope and differ only by ``lay / n`` of
    height.  Widening the rope does not separate them, because they are the
    same point of the same curve.  Hence

    .. math:: \\lambda \\ge n \\, d

    Below that no radius keeps the strands apart and the rope cannot be made.

    What this needs is the evenness, not ropes in general: it follows from
    the strands being one curve repeated, which is what "evenly laid" means
    here.  A rope whose strands differ from one another is outside it.

    The bound is not attained — clearing a diameter *at* it would take an
    infinite radius — and it is rarely what bites first; crowding round the
    circle usually does.  It is cheap to check and exact, which is its use.

    Args:
        n_strands: How many strands are laid up.
        diameter: How thick they are.

    Returns:
        The shortest workable lay length.
    """
    return n_strands * diameter


def helix_clearance(
    n_strands: int, radius: float, lay: float, n_samples: int = 2000
) -> float:
    """How close two strands of a laid rope come, exactly.

    Because the strands are one helix repeated — strand ``k`` slid along by
    ``k`` n-ths of a lay — the distance between two of them depends only on
    how far along one is slid relative to the other:

    .. math::

        D(w)^2 = 4R^2\\sin^2\\!\\left(\\frac{\\pi w}{\\lambda}\\right)
                 + \\left(\\frac{k\\lambda}{n} - w\\right)^2

    so the clearance is that minimised over ``w`` — one variable, no surface
    to search.  At ``w = k\\lambda/n`` it is the chord between neighbours,
    which is the packing answer; at ``w = 0`` it is ``k\\lambda/n``, which is
    why :func:`minimum_lay` exists.  The true minimum is generally at
    neither.

    Args:
        n_strands: How many strands are laid up.
        radius: The radius they sit at.
        lay: The lay length — the axial distance for one full turn.
        n_samples: Points in the coarse scan, before it is refined.

    Returns:
        The smallest distance between the centres of two strands.
    """

    def gap(step: int, w: float) -> float:
        slide = step * lay / n_strands
        return math.hypot(2.0 * radius * math.sin(math.pi * w / lay), slide - w)

    # The minimum lies in [0, lay].  Negative w only widens the axial term
    # while repeating the sine, and past one lay the sine repeats while the
    # axial term keeps growing — so neither can beat the first period.
    nearest = math.inf
    for step in range(1, n_strands):
        coarse = [lay * sample / n_samples for sample in range(n_samples + 1)]
        best = min(range(len(coarse)), key=lambda i: gap(step, coarse[i]))
        low = coarse[max(best - 1, 0)]
        high = coarse[min(best + 1, len(coarse) - 1)]
        # Golden section on the bracket, so a long lay is resolved as well as
        # a short one without sampling it to death.
        ratio = (math.sqrt(5.0) - 1.0) / 2.0
        for _ in range(80):
            left = high - ratio * (high - low)
            right = low + ratio * (high - low)
            if gap(step, left) < gap(step, right):
                high = right
            else:
                low = left
        nearest = min(nearest, gap(step, (low + high) / 2.0))
    return nearest


def lay_radius(
    n_strands: int,
    diameter: float = 0.4,
    lay: Optional[float] = None,
    tolerance: float = 1e-9,
) -> float:
    """The radius a rope of a given lay settles at, found by squeezing it.

    Nothing holds strands out at a radius: a helix of smaller radius is
    shorter, so tension pulls them in and what stops them is each other.
    Where they stop depends on the lay, and not in a way
    :func:`packing_radius` can express — the tighter the lay, the further
    out they must sit for the same clearance, because winding brings a
    strand nearer to its neighbour's *other* turns.

    There is no closed form, only a well-posed search: :func:`helix_clearance`
    rises with the radius, so bisection finds where it equals a diameter.
    That it is a search rather than a formula is the point — see
    ``docs/source/why_no_closed_form.md``.

    Args:
        n_strands: How many strands are laid up.
        diameter: How thick they are.
        lay: The lay length.  Defaults to the shortest that can be made,
            :func:`minimum_lay`, which needs an infinite radius — so give a
            longer one for a rope that exists.
        tolerance: How closely to pin the radius down, relative to the
            diameter.

    Returns:
        The radius at which the strands just touch.

    Raises:
        ValueError: If the lay is too short for the strands to fit past one
            another at any radius at all.
    """
    if lay is None:
        lay = minimum_lay(n_strands, diameter)
    shortest = minimum_lay(n_strands, diameter)
    if lay <= shortest:
        raise ValueError(
            f"A lay of {lay:g} is too short for {n_strands} strands "
            f"{diameter:g} thick: two of them are only {lay / n_strands:g} "
            f"apart along the axis whatever the radius, and they need "
            f"{diameter:g}.  The lay must exceed {shortest:g}."
        )

    low = packing_radius(n_strands, diameter)
    high = low
    while helix_clearance(n_strands, high, lay) < diameter:
        high *= 1.4
        if high > 1e6 * diameter:  # pragma: no cover - guarded by the check above
            raise ValueError("No radius keeps these strands apart at this lay.")
    while high - low > tolerance * diameter:
        middle = (low + high) / 2.0
        if helix_clearance(n_strands, middle, lay) < diameter:
            low = middle
        else:
            high = middle
    return high


@dataclass(frozen=True)
class Helix:
    """A strand winding uniformly at a constant radius.

    Args:
        radius: Distance from the axis.
        turns: Laps round the axis per period.
        length: The period along the axis.
        phase: Where on the circle it starts, in radians.
    """

    radius: float
    turns: float
    length: int
    phase: float = 0.0

    def position(self, z: float) -> Tuple[float, float, float]:
        """Where the strand is at ``z`` along the axis."""
        angle = self.phase + 2.0 * math.pi * self.turns * z / self.length
        return self.radius * math.cos(angle), self.radius * math.sin(angle), z


def rope_helices(
    n_strands: int,
    diameter: float = 0.4,
    length: int = 1,
    turns: float = 1.0,
    radius: Optional[float] = None,
) -> List[Helix]:
    """The shape a laid rope takes: helices, touching, evenly spaced.

    The only braid shape in this package that is both closed-form and
    physical.  It is available because a rope asks nothing of its strands
    beyond winding on together, which leaves a one-parameter family; because
    symmetry says which strands touch, so the contact set needs no searching;
    and because minimising length within that family is then a single
    inequality.  Where that inequality bites has no closed form once the rope
    has any lay to it, so :func:`lay_radius` searches for it.

    Args:
        n_strands: How many strands are laid up.
        diameter: How thick they are.
        length: The period along the axis.
        turns: Laps per period.
        radius: Override the radius.  Left out, it is the one the lay
            settles at — see :func:`lay_radius` — since nothing holds the
            strands out at any other.  Anything smaller makes them overlap,
            which :func:`~braidpy.parametric_braid.closest_approach` reports.

    Returns:
        One helix per strand, evenly spaced in phase.
    """
    if radius is None:
        radius = lay_radius(n_strands, diameter=diameter, lay=length / turns)
    return [
        Helix(
            radius=radius,
            turns=turns,
            length=length,
            phase=2.0 * math.pi * strand / n_strands,
        )
        for strand in range(n_strands)
    ]


@dataclass(frozen=True)
class TubularBraidStrand:
    """A strand of a braided tube, after Brunnschweiler's geometric model.

    The strand winds round the tube at a constant angle to the axis while its
    distance from the axis swings in and out — out where it passes over a
    strand coming the other way, in where it passes under.  That swing is the
    whole of the braid: take it away and the strands are helices that would
    have to pass through one another.

    From "The geometry of tubular braided structures", page 19:
    https://scispace.com/pdf/the-geometry-of-tubular-braided-structures-32b4yiwio2.pdf

    Args:
        n_strands: How many strands the tube has, half going each way.
        radius: The mean distance from the axis.
        braid_angle: The angle the *mean* helix makes with the axis, in
            radians — zero is straight up the tube, a right angle is round
            it.  The swing makes the local angle wander either side of it,
            and biases it upward, since swinging out and in adds path across
            the tube but none along it.
        bulge: How far the strand swings out and in.  Two strands crossing
            are ``2 * bulge`` apart radially, so half a diameter makes them
            touch there.
        direction: +1 or -1, which way round the tube it goes.
        phase: Where on the circle it starts, in radians.
    """

    n_strands: int
    radius: float
    braid_angle: float
    bulge: float
    direction: int
    phase: float

    @property
    def length(self) -> float:
        """The axial distance in which the strand goes once round the tube."""
        return 2.0 * math.pi * self.radius / math.tan(self.braid_angle)

    def position(self, z: float) -> Tuple[float, float, float]:
        """Where the strand is at ``z`` along the axis."""
        # z = R * u * cot(q), so the angle travelled follows from the height.
        travelled = z * math.tan(self.braid_angle) / self.radius
        angle = self.direction * travelled + self.phase
        swing = self.radius + self.direction * self.bulge * math.sin(
            self.n_strands * angle / 2.0
        )
        return swing * math.cos(angle), swing * math.sin(angle), z


def tubular_braid(
    n_strands: int,
    radius: float = 1.0,
    braid_angle: float = math.pi / 4.0,
    diameter: float = 0.4,
    bulge: Optional[float] = None,
) -> List[TubularBraidStrand]:
    """A braided tube: half the strands each way, interlacing.

    Two things the bare formula does not say, and without which it does not
    braid:

    **The strands alternate direction round the tube.**  Spaced evenly and
    alternating, two that cross meet where the radial swing is at its
    extreme, so one is fully out and the other fully in.  Space them any
    other way and they meet mid-swing, or — in the worst case — where the
    swing is zero and they are in the same place.

    **The swing follows the direction.**  A strand going one way bulges out
    where one going the other way tucks in; give them a common sign and both
    strands of a crossing take the same radius, which is a collision rather
    than a braid.

    Args:
        n_strands: How many strands, which must be even — half go each way.
        radius: The mean distance from the axis.
        braid_angle: The angle the strands make with the axis, in radians.
        diameter: How thick the strands are.  Only used to pick a default
            bulge; the geometry itself does not depend on it.
        bulge: How far the strands swing.  Half a diameter if left out, which
            sets two crossing strands exactly a diameter apart *at the
            crossing* — the clearance everywhere only while the crossings are
            the tightest spot, which
            :func:`~braidpy.parametric_braid.closest_approach` will tell you.

    Returns:
        One strand per place round the tube, alternating direction.

    Raises:
        ValueError: If the strand count is odd, or the braid angle leaves the
            strands running straight up the tube without braiding.
    """
    if n_strands < 2 or n_strands % 2:
        raise ValueError(
            f"A braided tube needs an even number of strands, half going each "
            f"way, not {n_strands}."
        )
    if not 0.0 < braid_angle < math.pi / 2.0:
        raise ValueError(
            f"A braid angle of {braid_angle:g} radians does not wind round the "
            f"tube: it must lie strictly between 0 and pi/2."
        )
    if bulge is None:
        bulge = diameter / 2.0

    return [
        TubularBraidStrand(
            n_strands=n_strands,
            radius=radius,
            braid_angle=braid_angle,
            bulge=bulge,
            direction=1 if place % 2 == 0 else -1,
            phase=2.0 * math.pi * place / n_strands,
        )
        for place in range(n_strands)
    ]


def tubular_braid_clearance(strands: Sequence, n_samples: int = 500) -> float:
    """How close two strands of a braided tube come, using its symmetry.

    Turning the tube by two places and relabelling the strands to match
    carries the braid onto itself, so the pair (0, j) is the same distance
    apart as the pair (2, j + 2).  Every pair is therefore a repeat of one
    involving strand 0 or strand 1, and comparing those two against the rest
    answers the question at a fraction of the cost — which matters, because
    finding a tube's radius asks it a few dozen times.

    The strands are also thin against the length in which they go once round,
    so only a fraction of a period either side need be searched.

    Args:
        strands: The strands of one braided tube, as :func:`tubular_braid`
            returns them.
        n_samples: Points per period.

    Returns:
        The smallest distance between the centres of two strands.
    """
    from braidpy.parametric_braid import closest_approach

    return closest_approach(strands, n_samples=n_samples, span=0.15, against=(0, 1))


def crossing_binds_above(n_strands: int, braid_angle: float) -> bool:
    """Which of the two conditions on the radius is the binding one.

    See :func:`tubular_braid_radius`.  Below the crossover angle the tube's
    width is set by the strands' own swing; above it, by how fast they climb.
    The crossover is at

    .. math:: \\tan q^{*} = \\sqrt{1 + 4/n^{2}}

    which tends to 45 degrees as the strands are added, so any braid of more
    than a few strands changes character near 45.

    Args:
        n_strands: How many strands, half each way.
        braid_angle: The angle they make with the axis, in radians.

    Returns:
        True if the climbing condition binds, False if the swing does.
    """
    return math.tan(braid_angle) > math.sqrt(1.0 + 4.0 / (n_strands**2))


def tubular_braid_radius(
    n_strands: int,
    diameter: float = 0.4,
    braid_angle: float = math.pi / 4.0,
    bulge: Optional[float] = None,
) -> float:
    """The narrowest tube on which these strands braid without crowding.

    In closed form, from the geometry, rather than by squeezing and
    measuring.

    Take the two strands of a crossing and let ``s`` and ``t`` measure how
    far each has gone past it.  At the crossing itself the swing holds them
    ``2b`` apart.  Just beside it the swing has decayed — as
    :math:`\\cos(ns/2)`, so by :math:`b n^{2} s^{2}/8` to second order — while
    the angle between them has opened by ``s + t`` and their heights have
    parted by :math:`R\\cot q\\,(s - t)`.  Writing ``p = s + t`` and
    ``m = s - t``, the squared distance comes out as

    .. math::

        D^{2} \\simeq 4b^{2}
            + p^{2}\\left[(R^{2} - b^{2}) - \\tfrac{1}{4}b^{2}n^{2}\\right]
            + m^{2}\\left[R^{2}\\cot^{2}q - \\tfrac{1}{4}b^{2}n^{2}\\right]

    — no cross term, the two motions being independent.  So the crossing is
    the tightest spot exactly when both brackets are non-negative, and the
    narrowest tube is where the first of them reaches zero:

    .. math::

        R = b \\max\\!\\left(\\sqrt{1 + \\tfrac{n^{2}}{4}},\\;
            \\tfrac{n}{2}\\tan q\\right)

    Two conditions, and which one binds says what is holding the tube open:
    the strands' own swing, or the rate at which they climb past one
    another.  :func:`crossing_binds_above` says which.

    The rope has no such formula (:func:`lay_radius` searches), and the
    reason is visible here: this works because a crossing is a point of
    symmetry for *both* strands, so it is automatically a critical point of
    the distance and only the second-order terms matter.  Two helices of a
    rope have no such point — their nearest approach is not where the chord
    between them is.

    Args:
        n_strands: How many strands, half each way.
        diameter: How thick they are.
        braid_angle: The angle they make with the axis, in radians.
        bulge: The radial swing; half a diameter if left out.

    Returns:
        The smallest mean radius at which the strands are no closer together
        than they are at their crossings.
    """
    if bulge is None:
        bulge = diameter / 2.0
    swing = math.sqrt(1.0 + n_strands**2 / 4.0)
    climb = (n_strands / 2.0) * math.tan(braid_angle)
    return bulge * max(swing, climb)


def cover_factor(
    n_strands: int, radius: float, braid_angle: float, diameter: float
) -> float:
    """How much of the tube's surface the strands hide, as a fraction.

    The measure of a braid's tightness, and the one a braider cares about:
    a sleeve at 0.4 is visibly open, one at 1 is closed.  Half the strands
    run each way, so one direction covers the surface when its ``n/2``
    strands, each crossing a circumferential cut in a segment of
    ``d / cos(q)``, together span the circumference:

    .. math:: \\text{cover} = \\frac{n}{2}\\,
              \\frac{d / \\cos q}{2 \\pi R}

    Above 1 the strands of one direction would have to overlap each other,
    which round ones cannot.

    Args:
        n_strands: How many strands, half each way.
        radius: The mean distance from the axis.
        braid_angle: The angle the strands make with the axis, in radians.
        diameter: How thick they are.

    Returns:
        The covered fraction, counting one direction.
    """
    circumferential = diameter / math.cos(braid_angle)
    return (n_strands / 2.0) * circumferential / (2.0 * math.pi * radius)


def radius_for_cover(
    n_strands: int, diameter: float, braid_angle: float, cover: float = 1.0
) -> float:
    """The radius at which the strands cover that fraction of the tube.

    :func:`cover_factor` rearranged, which is worth having because the
    radius that avoids crowding and the radius that looks like a braid are
    not the same number, and the gap between them is the model's main
    limitation — see below.

    .. math:: R = \\frac{n \\, d}{4 \\pi \\, \\text{cover} \\, \\cos q}

    **This will not clear.**  At its own non-crowding radius
    (:func:`tubular_braid_radius`) the model covers about 0.4 whatever the
    strand count, the braid angle or the swing depth — measured across 4 to
    16 strands and 45 to 80 degrees.  Tightening past that makes the strands
    overlap: at a cover of 0.9 they are a third of a diameter into one
    another.

    The reason is the sinusoidal swing.  Two strands are nearest not at
    their crossing, where the swing holds them a full ``2b`` apart, but just
    beside it, where the swing has decayed while the angle between them is
    still small — and at a smaller radius a given angle buys less arc to
    separate them with.  A real braid escapes this because its strands are
    not round: yarn flattens where it crosses and stays proud for longer,
    which is a squarer swing than a sine.

    So use this to draw a braid that looks like one, and
    :func:`tubular_braid_radius` for the tightest the round-strand model
    honestly allows.

    Args:
        n_strands: How many strands, half each way.
        diameter: How thick they are.
        braid_angle: The angle they make with the axis, in radians.
        cover: The fraction of the surface to hide.

    Returns:
        The mean radius giving that cover.
    """
    if cover <= 0.0:
        raise ValueError(f"A cover of {cover:g} is not a fraction of anything.")
    return (n_strands * diameter) / (4.0 * math.pi * cover * math.cos(braid_angle))
