# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: symmetric_braid.py
Description: Closed-form shapes for braids symmetric enough to have one
Authors: Baptiste Labat
Created: 2026-09-20
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

No formula takes a braid word to the shape its strands settle into — see
``src/braidpy/analytic/WHY_NOT_ANALYTIC.md``.  But some braids are regular
enough that a *family* of shapes can be written down and the choosing left to
a handful of numbers, and then the question becomes a small search instead of
an open problem.

The classic three-strand flat braid is one.  Every strand does the same thing
a third of a period later, so one curve and three phases describe the whole
braid:

.. math::

    x_k(z) = A \\sin\\!\\left(\\frac{2\\pi z}{P} - \\frac{2\\pi k}{3}\\right),
    \\qquad
    y_k(z) = H \\sin\\!\\left(\\frac{4\\pi z}{P} - \\frac{4\\pi k}{3}\\right)

The over-and-under runs at exactly twice the frequency of the side-to-side,
which is what makes each strand a figure eight in cross-section, and what
makes the three of them braid rather than merely weave past one another.
:func:`braid_word` reads the braid straight off the curves and confirms it is
the flat braid, six crossings to the period.

Two amplitudes and a period are all that is left to choose, so the shape can
be *optimised* — shortest strands that still keep a diameter apart — which is
a search in two variables rather than over a space of curves.  That is the
honest sense in which a braid like this has an analytic geometry: the family
is closed-form, the choice within it is not.

Two facts about the family worth having, both exact:

- **The period cannot be shorter than ``n`` diameters.**  Strand ``k`` is
  strand 0 slid along the axis by ``k`` thirds of a period, so a point on one
  and the matching point on another are at the same place across the braid
  and differ only by ``P/3`` of height — which widening the braid does not
  change, since they are the same point of the same curve.  This follows from
  the strands being one curve repeated and says nothing about braids that
  are not.
- **Across the cross-section alone**, two strands pass closest at a crossing,
  where they sit at ±H√3/2, so they clear ``H√3`` there — provided
  ``A >= 2H``.  Below that the tightest spot moves off the crossing.
  Neither statement is the whole clearance, which also counts the axial
  offset: that is :func:`figure_eight_clearance`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import numpy as np


@dataclass(frozen=True)
class FigureEightStrand:
    """One strand of a symmetric flat braid, as the user's equations give it.

    Args:
        amplitude: ``A``, how far it swings to either side.
        height: ``H``, how far it rides over and under.
        period: ``P``, the axial distance in which the braid repeats.
        phase: Which strand it is, as a fraction of a period of delay.
    """

    amplitude: float
    height: float
    period: float
    phase: float = 0.0

    @property
    def length(self) -> float:
        """The period along the axis."""
        return self.period

    def position(self, z: float) -> Tuple[float, float, float]:
        """Where the strand is at ``z`` along the axis."""
        angle = 2.0 * math.pi * (z / self.period - self.phase)
        return (
            self.amplitude * math.sin(angle),
            self.height * math.sin(2.0 * angle),
            z,
        )


def figure_eight_strands(
    amplitude: float,
    height: float,
    period: float,
    n_strands: int = 3,
) -> List[FigureEightStrand]:
    """The strands of a symmetric flat braid, evenly spread in phase.

    Args:
        amplitude: ``A``.
        height: ``H``.
        period: ``P``.
        n_strands: How many strands; three is the classic braid.

    Returns:
        One strand per phase, in order.
    """
    return [
        FigureEightStrand(
            amplitude=amplitude,
            height=height,
            period=period,
            phase=strand / n_strands,
        )
        for strand in range(n_strands)
    ]


def minimum_period(n_strands: int, diameter: float) -> float:
    """The shortest period this family can have, ``n`` diameters.

    Strand ``k`` is strand 0 slid along the axis by ``k`` n-ths of a period,
    so a point on one and the matching point on another sit at the same place
    across the braid and differ only by ``P/n`` of height.  Widening the braid
    does not separate them — they are the same point of the same curve — so
    below ``n`` diameters no amplitudes will do.

    The bound belongs to braids whose strands are one curve repeated, which
    this family is by construction; it is not a fact about braids in general.

    In practice the family needs a good deal more than this — crowding across
    the cross-section bites first, and it runs out between six and seven
    diameters of period — but this bound is exact and costs nothing to
    check.

    Args:
        n_strands: How many strands.
        diameter: How thick they are.

    Returns:
        The shortest conceivable period.
    """
    return n_strands * diameter


def crossing_clearance(amplitude: float, height: float) -> float:
    """How far apart two strands pass, counting the cross-section only.

    At a crossing the two strands sit at angles of pi/6 and 5pi/6, so their
    heights are ±H√3/2 and they clear ``H√3``.  Writing the pair separation
    as ``(A√3 cos u, H√3 cos 2u)``, the squared distance
    ``3(A²c² + H²(2c² - 1)²)`` is smallest at ``c = 0`` — the crossing —
    exactly when ``A >= 2H``; below that the tightest spot slides off the
    crossing and the clearance is smaller.

    This ignores the axial offset between strands, so it is an upper bound on
    the real clearance, not the real clearance.  Use
    :func:`figure_eight_clearance` for that.

    Args:
        amplitude: ``A``.
        height: ``H``.

    Returns:
        The smallest separation within a cross-section.
    """
    if abs(amplitude) >= 2.0 * abs(height):
        return math.sqrt(3.0) * abs(height)
    return math.sqrt(3.0 * (amplitude**2 / 2.0 - amplitude**4 / (16.0 * height**2)))


def _pair_distance_squared(
    amplitude: float,
    height: float,
    period: float,
    slide: float,
    along: float,
    apart: float,
) -> float:
    """The squared distance between two strands, in closed form.

    Every strand is the same curve slid along the axis, so the distance
    between two of them depends only on how far along that curve each is.
    Writing ``w`` for their midpoint along it and ``r`` for their separation
    along it, the sines collapse by the sum-to-product identities into

    .. math::

        D^{2} = 4A^{2}\\cos^{2}(\\omega w)\\sin^{2}(\\omega r/2)
              + 4H^{2}\\cos^{2}(2\\omega w)\\sin^{2}(\\omega r)
              + (r + c)^{2}

    with :math:`\\omega = 2\\pi/P` and ``c`` the slide between the two
    strands.  Two variables and no curves left, which is the whole of what
    geometry can do here — where the minimum of it sits is another matter,
    and not one with a closed form: see :func:`figure_eight_clearance`.

    Args:
        amplitude: ``A``.
        height: ``H``.
        period: ``P``.
        slide: How far one strand is slid along the axis from the other.
        along: ``w``, their midpoint along the shared curve.
        apart: ``r``, their separation along it.

    Returns:
        The squared distance.
    """
    omega = 2.0 * math.pi / period
    return (
        4.0
        * amplitude**2
        * math.cos(omega * along) ** 2
        * math.sin(omega * apart / 2.0) ** 2
        + 4.0
        * height**2
        * math.cos(2.0 * omega * along) ** 2
        * math.sin(omega * apart) ** 2
        + (apart + slide) ** 2
    )


def symmetric_contact_needs(amplitude: float, height: float) -> bool:
    """Whether the strands pass closest where they cross, as the tube's do.

    A braided tube's tightest spot is its crossing, which is a point of
    symmetry for both strands and therefore a critical point of the
    distance whatever the parameters — which is what lets its radius be
    written down (:func:`~braidpy.annulus_braid.tubular_braid_radius`).

    This family has a candidate for the same role: ``w = P/4``, where the two
    strands sit either side of the widest part of the swing and so are at the
    same place across the braid.  There the sideways term drops out entirely
    and the distance depends on ``H`` alone.  But it is only a *minimum* in
    ``w`` while

    .. math:: A \\ge 4H

    and below that it is a saddle: the tightest spot slides off it, picks up
    a dependence on ``A``, and stops being anywhere symmetry can name.  The
    shapes worth having sit below it — the tightest three-strand plait comes
    out at ``A/H`` near 1.2 to 1.7 — so the flat braid does not close the way
    the tube does, and :func:`tightest_figure_eight` searches.

    Args:
        amplitude: ``A``.
        height: ``H``.

    Returns:
        True if the crossing is the tightest spot.
    """
    return abs(amplitude) >= 4.0 * abs(height)


def figure_eight_clearance(
    amplitude: float,
    height: float,
    period: float,
    n_strands: int = 3,
    n_samples: int = 200,
) -> float:
    """How close two strands of the braid really come, axial offset included.

    Minimises :func:`_pair_distance_squared` — two variables in closed form,
    rather than a grid over two sampled curves.  A coarse sweep then a local
    descent, because the minimum is not at any point symmetry can name (see
    :func:`symmetric_contact_needs`) and so there is nothing to solve for.

    Args:
        amplitude: ``A``.
        height: ``H``.
        period: ``P``.
        n_strands: How many strands.
        n_samples: Points per axis in the coarse sweep.

    Returns:
        The smallest distance between the centres of two strands.
    """
    omega = 2.0 * math.pi / period
    along = np.linspace(0.0, period, n_samples, endpoint=False)
    apart = np.linspace(-period, period, 2 * n_samples)

    # The two factors that depend on only one variable each, built once.
    wide = (2.0 * amplitude * np.cos(omega * along)) ** 2
    tall = (2.0 * height * np.cos(2.0 * omega * along)) ** 2
    swing = np.sin(omega * apart / 2.0) ** 2
    cross = np.sin(omega * apart) ** 2

    nearest = math.inf
    for step in range(1, n_strands):
        slide = step * period / n_strands
        grid = (
            wide[:, None] * swing[None, :]
            + tall[:, None] * cross[None, :]
            + (apart + slide)[None, :] ** 2
        )
        first, second = np.unravel_index(int(grid.argmin()), grid.shape)
        here, there = float(along[first]), float(apart[second])

        # Walk downhill from the best sample, so the answer does not depend
        # on the sweep having landed on the minimum.
        reach = period / n_samples
        for _ in range(60):
            reach *= 0.8
            best = _pair_distance_squared(amplitude, height, period, slide, here, there)
            for move_here, move_there in (
                (reach, 0.0),
                (-reach, 0.0),
                (0.0, reach),
                (0.0, -reach),
                (reach, reach),
                (-reach, -reach),
                (reach, -reach),
                (-reach, reach),
            ):
                if (
                    _pair_distance_squared(
                        amplitude,
                        height,
                        period,
                        slide,
                        here + move_here,
                        there + move_there,
                    )
                    < best
                ):
                    here, there = here + move_here, there + move_there
                    break
        nearest = min(
            nearest,
            math.sqrt(
                _pair_distance_squared(amplitude, height, period, slide, here, there)
            ),
        )
    return nearest


def tightest_figure_eight(
    diameter: float,
    period: float,
    n_strands: int = 3,
    n_samples: int = 260,
    refinements: int = 4,
) -> Optional[Tuple[float, float]]:
    """The shortest strands of this family that still clear a diameter.

    Length falls as the amplitudes shrink and clearance falls with them, so
    the answer sits on the boundary where the strands just touch.  Finding it
    is a search in two variables — coarse grid, then refined about the best —
    which is cheap and reliable, and is the sense in which this shape is
    "solved".

    Args:
        diameter: How thick the strands are.
        period: The axial period to fit the braid into.
        n_strands: How many strands.
        n_samples: Points per period in the clearance measurement.
        refinements: How many times to narrow the search about the best.

    Returns:
        (amplitude, height), or None if no shape of this family fits that
        period — which happens long before :func:`minimum_period`.
    """
    low_a, high_a = 0.05 * diameter, 6.0 * diameter
    low_h, high_h = 0.05 * diameter, 4.0 * diameter
    best: Optional[Tuple[float, float, float]] = None

    for _ in range(refinements):
        found = None
        for amplitude in np.linspace(low_a, high_a, 26):
            for height in np.linspace(low_h, high_h, 26):
                if (
                    figure_eight_clearance(
                        amplitude, height, period, n_strands, n_samples
                    )
                    < diameter
                ):
                    continue
                strand = FigureEightStrand(amplitude, height, period)
                span = _strand_length(strand)
                if found is None or span < found[0]:
                    found = (span, float(amplitude), float(height))
        if found is None:
            return None
        best = found
        reach_a = (high_a - low_a) / 6.0
        reach_h = (high_h - low_h) / 6.0
        low_a, high_a = max(1e-6, best[1] - reach_a), best[1] + reach_a
        low_h, high_h = max(1e-6, best[2] - reach_h), best[2] + reach_h

    return (best[1], best[2]) if best else None


def _strand_length(strand: FigureEightStrand, n_samples: int = 4000) -> float:
    """Arc length of one period, for ranking candidates inside the search."""
    along = np.linspace(0.0, strand.period, n_samples + 1)
    angle = 2.0 * np.pi * along / strand.period
    points = np.stack(
        [
            strand.amplitude * np.sin(angle),
            strand.height * np.sin(2.0 * angle),
            along,
        ],
        axis=1,
    )
    return float(np.linalg.norm(np.diff(points, axis=0), axis=1).sum())


def braid_word(
    strands: Sequence,
    n_samples: int = 200000,
) -> List[int]:
    """Read the braid word off a set of curves.

    Which slots a crossing exchanges is read from the order of the strands
    across the braid, and its sign from which of the two was higher as they
    passed — the same convention
    :meth:`~braidpy.braid.Braid.to_parametric_strands` draws with.

    This is how a shape is checked against the braid it claims to be, rather
    than taken on trust.  It needs the strands to be ordered across the braid
    at every height, so it suits a flat braid and not a tubular one.

    Args:
        strands: Anything answering ``position(z)`` over a common ``length``.
        n_samples: Heights to look at.  A crossing narrower than the spacing
            between samples is missed, so this wants to be generous.

    Returns:
        The word, as signed generator indices.
    """
    count = len(strands)
    period = strands[0].length
    order = sorted(range(count), key=lambda k: strands[k].position(0.0)[0])
    previous = [strand.position(0.0)[0] for strand in strands]

    word: List[int] = []
    for step in range(1, n_samples + 1):
        z = period * step / n_samples
        across = [strand.position(z)[0] for strand in strands]
        for slot in range(count - 1):
            first, second = order[slot], order[slot + 1]
            if previous[first] - previous[second] < 0 <= across[first] - across[second]:
                heights = (
                    strands[first].position(z)[1],
                    strands[second].position(z)[1],
                )
                word.append(slot + 1 if heights[0] > heights[1] else -(slot + 1))
                order[slot], order[slot + 1] = second, first
        previous = across
    return word
