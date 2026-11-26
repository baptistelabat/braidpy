# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid word made shorter: the same braid, in fewer crossings.

Fewer crossings are fewer moves to make, by hand or on a machine.  Three
ways are tried, and the shortest word kept:

- **free cancellation**: a crossing followed at once by its inverse,
  ``σᵢ σᵢ⁻¹``, is no crossing at all (:func:`free_reduced`);
- **braid relations**: a crossing and its inverse kept apart by crossings
  that can be moved out of the way.  Crossings of strands far apart
  commute, ``σᵢ σⱼ = σⱼ σᵢ`` when ``|i - j| ≥ 2``, and three crossings of
  three strands can be made the other way round, ``σᵢ σᵢ₊₁ σᵢ =
  σᵢ₊₁ σᵢ σᵢ₊₁``, signs mixed too (``σᵢ σⱼ σᵢ⁻¹ = σⱼ⁻¹ σᵢ σⱼ``).  None of
  these changes the word's length; each piece of the word, ``WINDOW``
  crossings long, is rewritten every way they allow, up to
  ``SEARCH_BUDGET`` words, for one where two crossings cancel
  (:func:`shortened`);
- **handle reduction** (:mod:`braidpy.handles_reduction`): Dehornoy's,
  which leaves no handle, ``σᵢ … σᵢ⁻¹`` with only higher crossings between.
  Its word is often *longer* (the book's #3072 goes from 114 crossings to
  150), so it is kept only when it is shorter, after the search above.

A shortest word is not promised: finding one is hard in general.  The word
found is the same braid exactly (:meth:`braidpy.braid.Braid.__eq__`), not
merely one alike when repeated.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from braidpy.braid import Braid

__all__ = ["SEARCH_BUDGET", "WINDOW", "free_reduced", "shortened"]

# How many crossings of the word are rewritten at once: a crossing and its
# inverse further apart than this are not brought together.
WINDOW = 10
# How many rewritings of a piece of the word are tried before giving it up:
# a millisecond or two for a piece.  On the catalogue's words, four times
# as many find no more.
SEARCH_BUDGET = 500
# How long handle reduction is given, in seconds: its word is seldom the
# shorter, so not long.
HANDLE_REDUCTION_S = 1.0

Word = tuple[int, ...]


def free_reduced(word: Sequence[int]) -> Word:
    """A word with every crossing followed at once by its inverse taken out,
    and again, until none is.

    Args:
        word: The crossings, ``i`` for ``σᵢ`` and ``-i`` for ``σᵢ⁻¹``.

    Returns:
        The word, freely reduced.
    """
    out: list[int] = []
    for g in word:
        if out and out[-1] == -g:
            out.pop()
        else:
            out.append(int(g))
    return tuple(out)


def _rewrites(word: Word) -> Iterator[Word]:
    """The words one braid relation away, as long as this one: two
    neighbouring crossings of strands far apart swapped, or three crossings
    of three strands made the other way round."""
    for k in range(len(word) - 1):
        a, b = word[k], word[k + 1]
        if abs(abs(a) - abs(b)) >= 2:
            yield word[:k] + (b, a) + word[k + 2 :]
    for k in range(len(word) - 2):
        a, b, c = word[k : k + 3]
        if abs(a) != abs(c) or abs(abs(a) - abs(b)) != 1:
            continue
        if a == c and (a > 0) == (b > 0):
            # σᵢ σⱼ σᵢ = σⱼ σᵢ σⱼ, and the same all inverse.
            yield word[:k] + (b, a, b) + word[k + 3 :]
        elif a == -c and (b > 0) == (a > 0):
            # σᵢ σⱼ σᵢ⁻¹ = σⱼ⁻¹ σᵢ σⱼ, and the same all inverse.
            yield word[:k] + (-b, a, b) + word[k + 3 :]
        elif a == -c:
            # σᵢ⁻¹ σⱼ σᵢ = σⱼ σᵢ σⱼ⁻¹, and the same all inverse.
            yield word[:k] + (b, c, -b) + word[k + 3 :]


def _shorter_piece(piece: Word, budget: int) -> Word | None:
    """A shorter word for the same braid as ``piece``, found by rewriting it
    every way the braid relations allow, nearest first, up to ``budget``
    words; None if none is found."""
    seen = {piece}
    waiting = deque([piece])
    while waiting:
        word = waiting.popleft()
        reduced = free_reduced(word)
        if len(reduced) < len(piece):
            return reduced
        for other in _rewrites(word):
            if other not in seen:
                if len(seen) >= budget:
                    return None
                seen.add(other)
                waiting.append(other)
    return None


def _searched(word: Word, window: int, budget: int) -> Word:
    """A word shortened piece by piece (:func:`_shorter_piece`), each piece
    made shorter searched again from a little before it, until none is.  A
    piece of crossings all of one sign is not searched: the braid relations
    keep the sum of a word's signs, so no word for it is shorter."""
    word = free_reduced(word)
    k = 0
    while k < max(1, len(word) - 1):
        piece = word[k : k + window]
        shorter = (
            None
            if abs(sum(1 if g > 0 else -1 for g in piece)) == len(piece)
            else _shorter_piece(piece, budget)
        )
        if shorter is None:
            k += 1
            continue
        word = free_reduced(word[:k] + shorter + word[k + window :])
        k = max(0, k - window)
    return word


def shortened(braid: Braid, window: int = WINDOW, budget: int = SEARCH_BUDGET) -> Braid:
    """The braid in as few crossings as are found; see the module.

    Args:
        braid: The braid.
        window: How many crossings are rewritten at once.
        budget: How many rewritings of each piece are tried.

    Returns:
        The same braid, exactly, its word no longer than the braid's, on as
        many strands.
    """
    from braidpy.braid import Braid
    from braidpy.handles_reduction import HandleReductionMode, dehornoy_reduce_core
    from braidpy.utils import FunctionalException

    word = tuple(int(g) for g in braid.generators)
    best = _searched(word, window, budget)
    try:
        handled = dehornoy_reduce_core(
            list(word), HandleReductionMode.FULL, time_out_s=HANDLE_REDUCTION_S
        ).generators
    except FunctionalException:
        handled = None
    if handled is not None:
        handled_best = _searched(tuple(int(g) for g in handled), window, budget)
        if len(handled_best) < len(best):
            best = handled_best
    return Braid(best, braid.n_strands)
