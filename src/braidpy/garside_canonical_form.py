# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The Garside canonical form: a braid as a power of the half twist and
permutation braids, the same however the braid was written.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # math_braid imports sympy, slow to import: only named here for types.
    from math_braid.canonical_factor import CanonicalFactor

from braidpy.utils import PositiveInt, StrictlyPositiveInt


@dataclass(frozen=True)
class GarsideCanonicalFactors:
    """
    Represents the Garside asymmetric canonical form of a braid. Also called greedy normal form.

    Also known as Garside canonical form:
    https://webhomes.maths.ed.ac.uk/~v1ranick/papers/garside.pdf

    Attributes:
        n_half_twist (int): The exponent of the Garside element Δ (number of half-twists).
            From :meth:`~braidpy.braid.Braid.get_band_canonical_factors` it
            is instead the band generators' δ, a ``1/n_strands`` turn.
        n_strands (int): The number of strands in the braid.
        Ai (Tuple[int]): The sequence of simple elements (as indices or identifiers). Also known as Garside generators.
            From :func:`artin_left_normal_form`, each is a permutation: ``A[j]`` is where strand j ends.
    """

    n_half_twist: int
    n_strands: StrictlyPositiveInt
    Ai: tuple[CanonicalFactor | tuple[int, ...], ...]

    @property
    def dehornoy_floor(self) -> int:
        """
        Computes the Dehornoy floor of the braid.

        It is the unique integer m such that:

            Δ^{2m} < β < Δ^{2m+2}

        An estimate is floor(n_half_twist / 2) or floor(n_half_twist / 2) + 1
        depending on the position of the braid in Dehornoy order.

        For now, we return the conservative lower bound:
            floor(n_half_twist / 2)

        Returns:
            int: the Dehornoy floor
        """
        return self.n_half_twist // 2

    @property
    def garside_length(self) -> PositiveInt:
        """
        Returns the Garside (canonical) length of the braid,
        defined as the number of simple elements A_i in the positive part.

        Returns:
            int: the Garside length
        """
        return len(self.Ai)


# ── Artin's left normal form ──────────────────────────────────────────────────
#
# Every braid on n strands is uniquely Δ^k · A_1 ⋯ A_r: Δ the half twist, and
# each A_i a positive braid in which any two strands cross at most once — a
# permutation braid, given by where it sends each strand — none of them Δ or
# the identity, and each pair (A_i, A_{i+1}) left-weighted: every crossing
# A_{i+1} could start with is one A_i already ends with.
#
# A permutation is kept as a tuple ``p`` with ``p[j]`` the position strand j,
# starting at position j, ends at; σ_i swaps positions i-1 and i (0-based).

Permutation = tuple[int, ...]


def _compose(a: Permutation, b: Permutation) -> Permutation:
    """``a`` then ``b``: strand j goes to ``b[a[j]]``."""
    return tuple(b[a[j]] for j in range(len(a)))


def _inverse(a: Permutation) -> Permutation:
    inv = [0] * len(a)
    for j, image in enumerate(a):
        inv[image] = j
    return tuple(inv)


def _swap(n: int, i: int) -> Permutation:
    """σ_i, as a permutation: positions i-1 and i exchanged."""
    p = list(range(n))
    p[i - 1], p[i] = p[i], p[i - 1]
    return tuple(p)


def _delta(n: int) -> Permutation:
    """The half twist: every strand to the opposite side."""
    return tuple(n - 1 - j for j in range(n))


def _flip(a: Permutation) -> Permutation:
    """Conjugation by Δ, which sends σ_i to σ_{n-i}."""
    n = len(a)
    return tuple(n - 1 - a[n - 1 - j] for j in range(n))


def _starts_with(a: Permutation) -> set:
    """The σ_i a permutation braid can begin with: strands at i-1, i cross."""
    return {i for i in range(1, len(a)) if a[i - 1] > a[i]}


def _ends_with(a: Permutation) -> set:
    """The σ_i it can end with: the strands ending at i-1, i crossed."""
    return _starts_with(_inverse(a))


def artin_left_normal_form(
    generators, n_strands: int
) -> tuple[int, tuple[Permutation, ...]]:
    """A braid word in Artin's left normal form, Δ^k · A_1 ⋯ A_r.

    The half twists are kept at the word's end as it is read: there a
    crossing passes them by turning over (``Δ σᵢ = σₙ₋ᵢ Δ``), and an inverse
    crossing is a half twist less and a permutation braid more
    (``σᵢ⁻¹ = (σᵢ⁻¹Δ) Δ⁻¹``), so no factor read before is touched.  Each
    factor is then made left-weighted with those before it
    (:func:`left_weighted`), and the half twists brought to the front,
    turning the factors over once.

    Args:
        generators: Signed Artin generators, ``+i`` for σ_i and ``-i`` for its
            inverse; 0 is ignored.
        n_strands: Number of strands.

    Returns:
        ``k``, the number of half twists in front — negative for half twists
        the other way — and the factors A_i as permutations.
    """
    n = n_strands
    delta = _delta(n)
    k = 0
    factors: list[Permutation] = []
    for g in generators:
        if g == 0:
            continue
        # Past the k half twists behind it, σ_i is σ_{n-i} if k is odd.
        i = abs(g) if k % 2 == 0 else n - abs(g)
        if g > 0:
            factors.append(_swap(n, i))
        else:
            factors.append(_compose(_swap(n, i), delta))
            k -= 1
    # F_1 ⋯ F_m · Δ^k = Δ^k · τ^k(F_1) ⋯ τ^k(F_m), τ turning a factor over.
    lead, form = left_weighted(0, factors)
    if k % 2:
        form = tuple(_flip(f) for f in form)
    return k + lead, form


def left_weighted(
    k: int, factors: Sequence[Permutation]
) -> tuple[int, tuple[Permutation, ...]]:
    """Δ^k · F_1 ⋯ F_m, for any permutation braids F_i, in left normal form.

    The factors are taken one at a time, each made left-weighted with the
    one before it, and that one with the one before it, back until a pair
    is left as it was: one pass back is enough for a left normal form
    followed by one permutation braid (Thurston; Epstein et al., *Word
    Processing in Groups*, chapter 9).  Half twists the form begins with go
    into ``k``, and factors left empty go.

    Args:
        k: Half twists in front.
        factors: Permutation braids, Δ and the identity among them if need be.

    Returns:
        ``k`` and the factors, as :func:`artin_left_normal_form` gives them.
    """
    if not factors:
        return k, ()
    n = len(factors[0])
    identity = tuple(range(n))
    delta = _delta(n)
    form: list[Permutation] = []
    for factor in factors:
        form.append(factor)
        at = len(form) - 2
        while at >= 0:
            moved = _weighted(form[at], form[at + 1])
            if moved is None:
                break
            form[at], form[at + 1] = moved
            at -= 1
        while form and form[-1] == identity:
            form.pop()
    lead = 0
    while lead < len(form) and form[lead] == delta:
        lead += 1
    return k + lead, tuple(f for f in form[lead:] if f != identity)


def _weighted(a: Permutation, b: Permutation) -> tuple[Permutation, Permutation] | None:
    """The pair ``a · b`` made left-weighted: every crossing ``b`` can begin
    with that ``a`` can end with, and stay a permutation braid, moved from
    ``b`` to ``a``; None if there is none.

    A crossing moved changes which crossings each can begin or end with
    only beside it, so those are kept, and changed there.
    """
    n = len(a)
    ends = list(a)
    strand_at = [0] * n  # the strand ending in each place, in a
    for strand, place in enumerate(ends):
        strand_at[place] = strand
    starts = list(b)
    # σ_i: a ends with it if the strands ending at i-1, i crossed, b
    # begins with it if those starting at i-1, i cross.
    a_ends = {i for i in range(1, n) if strand_at[i - 1] > strand_at[i]}
    b_starts = {i for i in range(1, n) if starts[i - 1] > starts[i]}
    free = b_starts - a_ends
    if not free:
        return None
    while free:
        i = min(free)
        # a · σ_i: the strands ending at i-1 and i swap ends; σ_i · b: the
        # strands starting at i-1 and i swap starts.
        x, y = strand_at[i - 1], strand_at[i]
        strand_at[i - 1], strand_at[i] = y, x
        ends[x], ends[y] = i, i - 1
        starts[i - 1], starts[i] = starts[i], starts[i - 1]
        for p in (i - 1, i, i + 1):
            if not 1 <= p < n:
                continue
            ended = strand_at[p - 1] > strand_at[p]
            begun = starts[p - 1] > starts[p]
            (a_ends.add if ended else a_ends.discard)(p)
            (b_starts.add if begun else b_starts.discard)(p)
            (free.add if begun and not ended else free.discard)(p)
    return tuple(ends), tuple(starts)


def permutation_word(a: Permutation) -> list:
    """A positive word for a permutation braid: each pair crosses once at most."""
    order = list(range(len(a)))  # strands, by the position they stand at
    word = []
    swapped = True
    while swapped:
        swapped = False
        for i in range(1, len(order)):
            if a[order[i - 1]] > a[order[i]]:
                order[i - 1], order[i] = order[i], order[i - 1]
                word.append(i)
                swapped = True
    return word
