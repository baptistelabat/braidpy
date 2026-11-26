# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid closed, each strand's end tied back to its own start: a knot or
a link, compared as such.

It does not matter where the braid is read from, nor how many strands it
is on (Markov's theorem): ``σ₁`` on two strands and a single strand close
into one loop, two patterns (:mod:`braidpy.braid_pattern`) but one closed
braid.  Grommets and Turk's heads are closed braids.

Braids are the same in four ways, each its own type with its own ``==``
and hash — a word (:class:`~braidpy.braid_word.BraidWord`), a braid
(:class:`~braidpy.braid.Braid`), a pattern
(:class:`~braidpy.braid_pattern.BraidPattern`) and a closed braid
(:class:`~braidpy.closed_braid.ClosedBraid`): see ``docs/source/comparing_braids.md``,
*Four kinds of "the same"*.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from braidpy.braid import Braid

__all__ = ["ClosedBraid"]


@dataclass(frozen=True, eq=False)
class ClosedBraid:
    """A braid closed: each strand's end tied back to its own start, a
    knot or a link of several loops — a grommet, a Turk's head.

    It does not matter where the braid is read from, nor how many strands
    it is on (Markov's theorem): ``σ₁`` on two strands closes into one
    loop, as one strand does.  Telling two knots apart is hard in general,
    and here two closed braids are equal when nothing measured tells them
    apart: the number of loops, the linking numbers of every two
    (:func:`~braidpy.linking.linking_matrix`), sorted, and the Alexander
    polynomial (:func:`~braidpy.properties.alexander_polynomial`).  Equal
    so is not proven the same — a knot and its mirror image are equal so
    — but different is proven different.

    Args:
        braid: The braid closed.
    """

    braid: Braid
    _key: tuple[Any, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        from braidpy.linking import linking_matrix
        from braidpy.properties import alexander_polynomial

        links = linking_matrix(self.braid)
        loops = len(links)
        pairs = tuple(
            sorted(int(links[i, j]) for i in range(loops) for j in range(i + 1, loops))
        )
        alexander = tuple(int(c) for c in alexander_polynomial(self.braid).all_coeffs())
        object.__setattr__(self, "_key", (loops, pairs, alexander))

    @property
    def loops(self) -> int:
        """How many loops it closes into: one for a knot."""
        return int(self._key[0])

    def key(self) -> tuple[Any, ...]:
        """What it is measured by: its loops, their linking numbers sorted,
        and the coefficients of its Alexander polynomial."""
        return self._key

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ClosedBraid):
            return NotImplemented
        return self._key == other._key

    def __hash__(self) -> int:
        return hash(self._key)
