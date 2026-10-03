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
survives; see ``src/braidpy/analytic/WHY_NOT_ANALYTIC.md``.
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
    at a different height than alongside it: laid one turn per period, three
    strands at this radius clear only 0.68 of a diameter.  For a rope with
    an actual lay use :func:`lay_radius`, which solves for it.

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
    ``src/braidpy/analytic/WHY_NOT_ANALYTIC.md``.

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
