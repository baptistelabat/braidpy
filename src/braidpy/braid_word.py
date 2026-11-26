# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid word: its crossings in order, compared as such.

One braid has many words: ``σ₁σ₂σ₁`` and ``σ₂σ₁σ₂`` are two words and one
braid.  A word is the same word only crossing for crossing; for the same
braid, compare braids (:meth:`BraidWord.braid`).

Braids are the same in four ways, each its own type with its own ``==``
and hash — a word (:class:`~braidpy.braid_word.BraidWord`), a braid
(:class:`~braidpy.braid.Braid`), a pattern
(:class:`~braidpy.braid_pattern.BraidPattern`) and a closed braid
(:class:`~braidpy.closed_braid.ClosedBraid`): see ``docs/source/comparing_braids.md``,
*Four kinds of "the same"*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from braidpy.braid import Braid

__all__ = ["BraidWord"]


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
