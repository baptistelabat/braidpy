# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: garside_canonical_form.py
Description: Another way to describe braid as twist and permutations
Authors: Baptiste Labat
Created: 2025-06-04
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from dataclasses import dataclass
from typing import Tuple

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
    Ai: Tuple[CanonicalFactor | Tuple[int, ...], ...]

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

Permutation = Tuple[int, ...]


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
) -> Tuple[int, Tuple[Permutation, ...]]:
    """A braid word in Artin's left normal form, Δ^k · A_1 ⋯ A_r.

    Args:
        generators: Signed Artin generators, ``+i`` for σ_i and ``-i`` for its
            inverse; 0 is ignored.
        n_strands: Number of strands.

    Returns:
        ``k``, the number of half twists in front — negative for half twists
        the other way — and the factors A_i as permutations.
    """
    n = n_strands
    identity = tuple(range(n))
    delta = _delta(n)
    k = 0
    factors: list = []
    for g in generators:
        if g == 0:
            continue
        i = abs(g)
        if g > 0:
            factors.append(_swap(n, i))
        else:
            # σ_i⁻¹ = Δ⁻¹ · (Δ σ_i⁻¹), and the Δ⁻¹ moves to the front through
            # what came before, turning each factor over as it goes.
            factors = [_flip(f) for f in factors]
            factors.append(_compose(delta, _swap(n, i)))
            k -= 1

    # Make every neighbouring pair left-weighted, until nothing moves.
    changed = True
    while changed:
        changed = False
        for j in range(len(factors) - 1):
            a, b = factors[j], factors[j + 1]
            while True:
                free = _starts_with(b) - _ends_with(a)
                if not free:
                    break
                i = min(free)
                s = _swap(n, i)
                a, b = _compose(a, s), _compose(s, b)
                changed = True
            factors[j], factors[j + 1] = a, b
        # Whole half twists at the front go into k; empty factors go.
        while factors and factors[0] == delta:
            factors.pop(0)
            k += 1
        factors = [f for f in factors if f != identity]
    return k, tuple(factors)


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
