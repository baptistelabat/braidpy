# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid made over and over, compared as such: the same pattern however
often it is repeated and wherever it is read from.

``σ₁σ₂`` and ``σ₂σ₁`` are two braids and one pattern, the one read from the
other's second crossing; so are ``w`` and ``w w``.  A pattern and a closed
braid (:mod:`braidpy.closed_braid`) are both coarser than a braid, but
neither than the other: ``w`` and ``w w`` close into two links.

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
    from braidpy.similarity import Fingerprint

__all__ = ["BraidPattern"]


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
