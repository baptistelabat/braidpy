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

A word of moves round a ring (:mod:`braidpy.annulus_braid`) is shortened
the same way, its relations read round the ring (:func:`shortened_ring`):
crossing ``n``, of the pair whose slots wrap, is a crossing like any other,
neighbour of crossings ``n - 1`` and ``1``, and a turn passes a crossing
by renumbering it (:func:`~braidpy.annulus_braid.turns_last`).  The braid
kept is the braid round the core (:func:`~braidpy.annulus_braid.cored_word`),
so a tube stays a tube.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Iterator, Sequence
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from braidpy.braid import Braid

__all__ = [
    "SEARCH_BUDGET",
    "WINDOW",
    "free_reduced",
    "rewrites",
    "shortened",
    "shortened_ring",
]

# How many crossings of the word are rewritten at once: a crossing and its
# inverse further apart than this are not brought together.
WINDOW = 10
# How many rewritings of a piece of the word are tried before giving it up:
# a millisecond or two for a piece.  On the catalogue's words, four times
# as many find no more.
SEARCH_BUDGET = 500
# How long handle reduction is given, in seconds: its word is seldom the
# shorter, so not long.
HANDLES_SHORTENED_S = 1.0

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


def _apart(a: int, b: int, ring: Optional[int]) -> int:
    """How many places apart two crossings are: along the word's strands,
    or round a ring of ``ring`` slots."""
    gap = abs(abs(a) - abs(b))
    return gap if ring is None else min(gap, ring - gap)


def rewrites(word: Word, ring: Optional[int] = None) -> Iterator[Word]:
    """The words one braid relation away, as long as this one: two
    neighbouring crossings of strands far apart swapped, or three crossings
    of three strands made the other way round, signs mixed too.  Each is the
    same braid; read round a word, as a card runs it, they are what
    :func:`braidpy.making.lace.card_conjugate` searches.

    Args:
        word: The crossings, ``i`` for ``σᵢ`` and ``-i`` for ``σᵢ⁻¹``.
        ring: If given, the word is moves round a ring of so many slots
            (:mod:`braidpy.annulus_braid`): crossings are neighbours round
            the ring, crossing ``ring`` beside crossing 1, and a turn,
            ``±(ring + 1)``, passes a crossing by renumbering it.  On two
            slots the two crossings are not related at all.

    Yields:
        Each word one relation away.
    """
    turning = None if ring is None else ring + 1
    related = ring is None or ring > 2
    for k in range(len(word) - 1):
        a, b = word[k], word[k + 1]
        if ring is not None and ring + 1 in (abs(a), abs(b)):
            if abs(a) != abs(b):
                yield word[:k] + _passed(a, b, ring) + word[k + 2 :]
            continue
        if related and _apart(a, b, ring) >= 2:
            yield word[:k] + (b, a) + word[k + 2 :]
    if not related:
        return
    for k in range(len(word) - 2):
        a, b, c = word[k : k + 3]
        if turning in (abs(a), abs(b), abs(c)):
            continue
        if abs(a) != abs(c) or _apart(a, b, ring) != 1:
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


def _passed(a: int, b: int, ring: int) -> Word:
    """A turn and a crossing side by side, the other way round: a turn
    followed by crossing ``i`` is crossing ``i - 1`` followed by the turn
    (:func:`~braidpy.annulus_braid.turns_last`)."""
    turning = ring + 1
    if abs(a) == turning:
        # τ σᵢ = σᵢ₋ₜ τ, t the turn's sign.
        shift = 1 if a > 0 else -1
        return (_renumbered(b, -shift, ring), a)
    shift = 1 if b > 0 else -1
    return (b, _renumbered(a, shift, ring))


def _renumbered(crossing: int, by: int, ring: int) -> int:
    """A crossing ``by`` slots round the ring."""
    sign = 1 if crossing > 0 else -1
    return sign * ((abs(crossing) - 1 + by) % ring + 1)


def _shorter_piece(piece: Word, budget: int, ring: Optional[int] = None) -> Word | None:
    """A shorter word for the same braid as ``piece``, found by rewriting it
    every way the braid relations allow (round a ring of ``ring`` slots if
    given), nearest first, up to ``budget`` words; None if none is
    found."""
    seen = {piece}
    waiting = deque([piece])
    while waiting:
        word = waiting.popleft()
        reduced = free_reduced(word)
        if len(reduced) < len(piece):
            return reduced
        for other in rewrites(word, ring):
            if other not in seen:
                if len(seen) >= budget:
                    return None
                seen.add(other)
                waiting.append(other)
    return None


def _searched(word: Word, window: int, budget: int, ring: Optional[int] = None) -> Word:
    """A word shortened piece by piece (:func:`_shorter_piece`), each piece
    made shorter searched again from a little before it, until none is.  A
    piece of crossings all of one sign is not searched: the braid relations
    keep the sum of a word's signs, so no word for it is shorter; round a
    ring they keep the sum of its turns' signs too."""
    word = free_reduced(word)
    k = 0
    while k < max(1, len(word) - 1):
        piece = word[k : k + window]
        shorter = None if _one_way(piece, ring) else _shorter_piece(piece, budget, ring)
        if shorter is None:
            k += 1
            continue
        word = free_reduced(word[:k] + shorter + word[k + window :])
        k = max(0, k - window)
    return word


def _one_way(piece: Word, ring: Optional[int]) -> bool:
    """Whether every crossing of a piece is of one sign, and every turn
    too: nothing in it can ever cancel."""
    turning = None if ring is None else ring + 1
    signs = {(abs(g) == turning, g > 0) for g in piece}
    return len(signs) == len({kind for kind, _ in signs})


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
            list(word), HandleReductionMode.FULL, time_out_s=HANDLES_SHORTENED_S
        ).generators
    except FunctionalException:
        handled = None
    if handled is not None:
        handled_best = _searched(tuple(int(g) for g in handled), window, budget)
        if len(handled_best) < len(best):
            best = handled_best
    return Braid(best, braid.n_strands)


def shortened_ring(
    moves: Sequence[int],
    n_strands: int,
    window: int = WINDOW,
    budget: int = SEARCH_BUDGET,
) -> list[int]:
    """Moves round a ring in as few as are found: the turns moved to the
    end (:func:`~braidpy.annulus_braid.turns_last`), where those one way and
    the other cancel, then the crossings searched as :func:`shortened`
    searches a word, their relations read round the ring.

    Args:
        moves: Crossings ``±1`` to ``±n_strands``, turns
            ``±(n_strands + 1)`` (:mod:`braidpy.annulus_braid`).
        n_strands: How many slots the ring has.
        window: How many moves are rewritten at once.
        budget: How many rewritings of each piece are tried.

    Returns:
        The moves: the same braid round the core, exactly
        (:func:`~braidpy.annulus_braid.cored_word`), no more of them.
    """
    from braidpy.annulus_braid import turns_last

    normal = tuple(turns_last(moves, n_strands))
    best = _searched(normal, window, budget, n_strands)
    return list(best if len(best) < len(moves) else (int(g) for g in moves))
