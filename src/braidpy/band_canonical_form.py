# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids in band generators (Birman, Ko and Lee, 1998): the strands round
a circle, any two crossing along the chord between them.

A **band generator** ``a_ts`` (``t > s``) crosses strands ``t`` and ``s``
directly, passing in front of every strand between them, as a band
stretched across: ``a_ts = σ_{t-1} ⋯ σ_{s+1} σ_s σ_{s+1}⁻¹ ⋯ σ_{t-1}⁻¹``,
and ``a_{s+1,s}`` is ``σ_s``.  Where Artin's generators cross neighbours on
a line, these treat every place round a circle alike, as a kumihimo disk
or a marudai does: a strand carried across the disk is one letter, a ring
word's crossing across the seam is ``a_{n,1}``, and ``δ = a_{n,n-1} ⋯
a_{2,1}``, every strand a place round, is the ring's turn.

Every braid is ``δ^p A_1 ⋯ A_r`` in one way (Birman, Ko and Lee's left
normal form, :func:`band_left_normal_form`): each factor ``A_i`` strands
in blocks round the circle, no two blocks crossing, each block's strands a
place round within it (a descending cycle), each pair of factors
left-weighted.  Worked out as Artin's form is
(:func:`~braidpy.garside_canonical_form.artin_left_normal_form`): the
turns kept at the word's end, each factor made left-weighted with those
before it in one pass back, a pair's meet the blocks the two share.

Disk braids spell far shorter so: Kongo gumi on 8 strands, 81 crossings
shortened, is 43 band letters (:func:`band_word`); machine braids of
neighbours crossing, longer.
"""

from __future__ import annotations

from collections.abc import Sequence
from itertools import pairwise

from braidpy.garside_canonical_form import Permutation, _compose, _inverse

__all__ = [
    "BandLetter",
    "artin_from_band",
    "band_left_normal_form",
    "band_word",
    "factor_blocks",
]

# A band generator a_ts as (t, s), strands counted from 1, t > s; its
# inverse as (s, t).
BandLetter = tuple[int, int]


def _transposition(n: int, i: int, j: int) -> Permutation:
    p = list(range(n))
    p[i], p[j] = p[j], p[i]
    return tuple(p)


def _from_blocks(n: int, blocks: Sequence[Sequence[int]]) -> Permutation:
    """The factor whose blocks these are, strands from 0: each strand a
    place up its block, the highest to the lowest."""
    p = list(range(n))
    for block in blocks:
        ordered = sorted(block)
        for low, high in zip(ordered, ordered[1:] + ordered[:1]):
            p[low] = high
    return tuple(p)


def _blocks(a: Permutation) -> list[list[int]]:
    """A factor's blocks: its cycles, strands from 0, in order."""
    seen: set[int] = set()
    out: list[list[int]] = []
    for start in range(len(a)):
        if start in seen:
            continue
        cycle = []
        strand = start
        while strand not in seen:
            seen.add(strand)
            cycle.append(strand)
            strand = a[strand]
        out.append(sorted(cycle))
    return out


def _meet(a: Permutation, b: Permutation) -> Permutation:
    """The greatest factor both begin with: the blocks they share."""
    n = len(a)
    block_of = [[0] * n, [0] * n]
    for which, factor in enumerate((a, b)):
        for number, block in enumerate(_blocks(factor)):
            for strand in block:
                block_of[which][strand] = number
    shared: dict[tuple[int, int], list[int]] = {}
    for strand in range(n):
        shared.setdefault((block_of[0][strand], block_of[1][strand]), []).append(strand)
    return _from_blocks(n, list(shared.values()))


def _delta(n: int) -> Permutation:
    """δ: every strand a place round, the highest to the lowest."""
    return _from_blocks(n, [range(n)])


def _turned(a: Permutation, k: int, powers: dict[int, Permutation]) -> Permutation:
    """``δ^k a δ^-k``: a factor turned k places round the circle."""
    n = len(a)
    k %= n
    if not k:
        return a
    if k not in powers:
        d = p = _delta(n)
        for _ in range(k - 1):
            p = _compose(p, d)
        powers[k] = p
    return _compose(_compose(powers[k], a), _inverse(powers[k]))


def band_left_normal_form(
    generators: Sequence[int], n_strands: int
) -> tuple[int, tuple[Permutation, ...]]:
    """A braid word, of Artin generators, in Birman, Ko and Lee's left
    normal form, ``δ^p · A_1 ⋯ A_r``.

    Args:
        generators: Signed Artin generators, ``+i`` for ``σᵢ`` and ``-i``
            for its inverse; 0 is ignored.
        n_strands: Number of strands.

    Returns:
        ``p``, the turns in front (negative the other way), and the
        factors as permutations, strands from 0: ``A[j]`` is where strand
        j ends, each block's strands a place up it (:func:`factor_blocks`).
    """
    n = n_strands
    delta = _delta(n)
    identity = tuple(range(n))
    powers: dict[int, Permutation] = {}
    k = 0
    form: list[Permutation] = []
    for g in generators:
        if g == 0:
            continue
        # σᵢ = a_{i+1,i}, past the k turns behind it: δ^k x = τ^k(x) δ^k.
        crossing = _turned(_transposition(n, abs(g) - 1, abs(g)), k, powers)
        if g > 0:
            form.append(crossing)
        else:
            # x⁻¹ = (x⁻¹ δ) δ⁻¹: a factor more, a turn less.
            form.append(_compose(_inverse(crossing), delta))
            k -= 1
        at = len(form) - 2
        while at >= 0:
            a, b = form[at], form[at + 1]
            # What b begins with that a can take and stay a factor.
            moved = _meet(_compose(_inverse(a), delta), b)
            if moved == identity:
                break
            form[at], form[at + 1] = _compose(a, moved), _compose(_inverse(moved), b)
            at -= 1
        while form and form[-1] == identity:
            form.pop()
    lead = 0
    while lead < len(form) and form[lead] == delta:
        lead += 1
    # form · δ^k = δ^k · τ^-k(form)
    rest = tuple(_turned(f, -k, powers) for f in form[lead:])
    return k + lead, tuple(f for f in rest if f != identity)


def factor_blocks(a: Permutation) -> list[tuple[int, ...]]:
    """A factor's blocks of more than one strand, strands from 1: each is
    its strands carried a place round within it, ``a_{b_k b_{k-1}} ⋯
    a_{b_2 b_1}``.

    Args:
        a: A factor of :func:`band_left_normal_form`.

    Returns:
        The blocks, each its strands in increasing order.
    """
    return [tuple(s + 1 for s in block) for block in _blocks(a) if len(block) > 1]


def _letters(a: Permutation) -> list[BandLetter]:
    """A factor as band letters: each block's, highest strand first."""
    letters: list[BandLetter] = []
    for block in factor_blocks(a):
        ordered = sorted(block, reverse=True)
        letters.extend(pairwise(ordered))
    return letters


def band_word(generators: Sequence[int], n_strands: int) -> list[BandLetter]:
    """A braid word written in band generators, as its band normal form
    spells it: ``δ^p``, each δ ``a_{n,n-1} ⋯ a_{2,1}``, then the factors'
    letters.

    Args:
        generators: Signed Artin generators.
        n_strands: Number of strands.

    Returns:
        The letters: ``(t, s)``, ``t > s``, for ``a_ts``, and ``(s, t)``
        for its inverse.
    """
    p, factors = band_left_normal_form(generators, n_strands)
    turn = _letters(_delta(n_strands))
    if p >= 0:
        word = turn * p
    else:
        word = [(s, t) for t, s in reversed(turn)] * -p
    for factor in factors:
        word += _letters(factor)
    return word


def artin_from_band(letters: Sequence[BandLetter]) -> list[int]:
    """Band letters as Artin generators:
    ``a_ts = σ_{t-1} ⋯ σ_{s+1} σ_s σ_{s+1}⁻¹ ⋯ σ_{t-1}⁻¹``.

    Args:
        letters: ``(t, s)`` for ``a_ts``, ``(s, t)`` for its inverse,
            strands from 1.

    Returns:
        The signed Artin generators.
    """
    word: list[int] = []
    for first, second in letters:
        t, s = max(first, second), min(first, second)
        if t == s:
            raise ValueError(
                f"A band letter crosses two strands, not ({first}, {second})."
            )
        up = list(range(t - 1, s, -1))
        if first > second:
            word += up + [s] + [-g for g in reversed(up)]
        else:
            word += up + [-s] + [-g for g in reversed(up)]
    return word
