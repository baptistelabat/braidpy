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

from dataclasses import dataclass
from typing import List, Sequence, Tuple


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
