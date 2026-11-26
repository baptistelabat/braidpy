# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What "the same braid" means: four kinds of braid, each with its own
``==`` and hash.

A braid is written as a word, and one braid has many words; a braid made
over and over is a pattern, and one pattern has many braids; a braid with
each strand's end tied back to its start is a closed braid, a knot or a
link, and one has many braids.  Each kind is told apart from its kin by
its own test, and is a key in a set or a dict by it:

- :class:`BraidWord`: the same crossings in the same order; told exactly,
  and cheaply.
- :class:`~braidpy.braid.Braid`: the same braid, its ends held where they
  are (:meth:`~braidpy.braid.Braid.__eq__`); told exactly.
- :class:`BraidPattern`: the same braid made over and over, read from
  another start (conjugate) or a power of it (``w`` and ``w w``); proven
  where it can be.
- :class:`ClosedBraid`: the same knot or link once each strand's end is
  tied back to its own start, however many strands; told by invariants.

From a word, its braid (:meth:`BraidWord.braid`); from a braid, its word
(:meth:`~braidpy.braid.Braid.word`), its pattern
(:meth:`~braidpy.braid.Braid.pattern`) and its closure
(:meth:`~braidpy.braid.Braid.closed`).  The pattern and the closure are
both coarser than the braid, but neither is coarser than the other: ``w``
and ``w w`` are one pattern and close into two links, and ``σ₁`` on two
strands and the braid of one strand close into one loop and are two
patterns.

A braid round a core — a tube, :meth:`~braidpy.horn_gear.word.RingWord.cored`
— is a braid with the core a strand of its own, and so has a pattern and a
closure like any other.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from braidpy.braid import Braid
    from braidpy.similarity import Fingerprint

__all__ = ["BraidPattern", "BraidWord", "ClosedBraid"]


@dataclass(frozen=True)
class BraidWord:
    """A braid word: its crossings in order, ``i`` for ``σᵢ`` and ``-i``
    for ``σᵢ⁻¹``, on so many strands.  Two words are equal when their
    crossings are, as tuples are.

    Args:
        generators: The crossings.
        n_strands: How many strands.
    """

    generators: tuple[int, ...]
    n_strands: int

    def braid(self) -> Braid:
        """The braid the word writes."""
        from braidpy.braid import Braid

        return Braid(self.generators, self.n_strands)


@dataclass(frozen=True, eq=False)
class BraidPattern:
    """A braid made over and over: what is the same however often it is
    repeated and wherever it is read from.

    Two patterns are equal when their braids, brought home
    (:func:`~braidpy.similarity.home`), are conjugate
    (:func:`~braidpy.conjugacy.same_pattern`): proven so, or proven not.
    Where the search would be too long
    (:class:`~braidpy.conjugacy.SuperSummitSetTooLarge`), as for long
    braids of many strands, they are equal when their fingerprints are
    (:func:`~braidpy.similarity.same_fingerprint`), which proves only that
    they differ; :meth:`proven` says which.  A pattern hashes by its
    fingerprint, which two equal patterns share.

    Args:
        braid: One braid of the pattern: one repeat, or several.
    """

    braid: Braid
    fingerprint: Fingerprint = field(init=False, repr=False, compare=False)
    _key: tuple[Any, ...] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        from braidpy.similarity import exact_part, fingerprint

        mark = fingerprint(self.braid)
        object.__setattr__(self, "fingerprint", mark)
        object.__setattr__(self, "_key", exact_part(mark))

    def key(self) -> tuple[Any, ...]:
        """What two equal patterns share, exactly: the fingerprint's exact
        parts (:func:`~braidpy.similarity.exact_part`)."""
        return self._key

    def proven(self, other: BraidPattern) -> bool | None:
        """Whether two patterns are the same, proven; None if the search
        for it would be too long."""
        from braidpy.conjugacy import SuperSummitSetTooLarge, same_pattern

        if self._key != other._key:
            return False
        try:
            return same_pattern(self.braid, other.braid)
        except SuperSummitSetTooLarge:
            return None

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, BraidPattern):
            return NotImplemented
        proven = self.proven(other)
        return self._key == other._key if proven is None else proven

    def __hash__(self) -> int:
        return hash(self._key)


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
