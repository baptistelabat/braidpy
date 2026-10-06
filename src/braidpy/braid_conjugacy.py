"""
Filename: braid_conjugacy.py
Description: Comparing braids up to where you start reading them
Authors: Baptiste Labat
Created: 2026-10-06
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from __future__ import annotations

import itertools
from typing import Dict, FrozenSet, List, Sequence, Tuple

from braidpy.garside_canonical_form import (
    _delta,
    artin_left_normal_form,
    permutation_word,
)

#: A braid in Artin's left normal form: ``Δ^p A_1 ⋯ A_r``.
NormalForm = Tuple[int, Tuple[Tuple[int, ...], ...]]


class TooManyConjugates(RuntimeError):
    """The summit set grew past the limit it was asked to stay inside."""


def normal_form(word: Sequence[int], n_strands: int) -> NormalForm:
    """The braid a word spells, in left normal form.

    Args:
        word: Signed Artin generators, ``+i`` for σ_i and ``-i`` for its
            inverse.
        n_strands: Number of strands.

    Returns:
        ``(p, factors)`` for ``Δ^p A_1 ⋯ A_r``.
    """
    return artin_left_normal_form(list(word), n_strands)


def to_word(form: NormalForm, n_strands: int) -> List[int]:
    """A word spelling a braid given in normal form.

    Args:
        form: ``(p, factors)``.
        n_strands: Number of strands.

    Returns:
        Signed Artin generators.
    """
    p, factors = form
    half = permutation_word(_delta(n_strands))
    word: List[int] = []
    if p >= 0:
        for _ in range(p):
            word += half
    else:
        for _ in range(-p):
            word += [-g for g in reversed(half)]
    for factor in factors:
        word += permutation_word(factor)
    return word


def inverse_word(word: Sequence[int]) -> List[int]:
    """The word for the inverse braid.

    Args:
        word: Signed Artin generators.

    Returns:
        The generators reversed and negated.
    """
    return [-g for g in reversed(list(word))]


def invariants(form: NormalForm) -> Dict[str, int]:
    """The three numbers that conjugate braids must agree on.

    ``inf`` is the number of half twists in front, ``sup`` the same plus the
    canonical length.  All three are invariant under conjugacy, so braids
    whose invariants differ cannot be the same up to where you start reading
    them -- which makes them a cheap way to say *no* before any search.

    They do not make a complete invariant: braids can agree on all three and
    still not be conjugate.

    Args:
        form: ``(p, factors)``.

    Returns:
        ``inf``, ``sup`` and ``canonical_length``.
    """
    p, factors = form
    return {
        "inf": p,
        "sup": p + len(factors),
        "canonical_length": len(factors),
    }


def conjugate(word: Sequence[int], by: Sequence[int], n_strands: int) -> NormalForm:
    """``by⁻¹ · word · by``, in normal form.

    Args:
        word: The braid being conjugated.
        by: The braid to conjugate it by.
        n_strands: Number of strands.

    Returns:
        The conjugate, in left normal form.
    """
    return normal_form(list(inverse_word(by)) + list(word) + list(by), n_strands)


def cycling(form: NormalForm, n_strands: int) -> NormalForm:
    """Move the first canonical factor to the back.

    For ``x = Δ^p A_1 ⋯ A_r`` this is conjugation by ``Δ^p A_1 Δ^-p``, which
    leaves ``Δ^p A_2 ⋯ A_r`` followed by the factor that was in front.  Doing
    it repeatedly cannot lower ``inf`` and sooner or later raises it as far as
    it will go, which is how a braid is driven to its summit.

    Args:
        form: ``(p, factors)``.
        n_strands: Number of strands.

    Returns:
        The cycled braid, in left normal form.
    """
    p, factors = form
    if not factors:
        return form
    half = permutation_word(_delta(n_strands))
    shift: List[int] = []
    for _ in range(abs(p)):
        shift += half if p > 0 else [-g for g in reversed(half)]
    unshift = inverse_word(shift)
    by = shift + permutation_word(factors[0]) + unshift
    return conjugate(to_word(form, n_strands), by, n_strands)


def decycling(form: NormalForm, n_strands: int) -> NormalForm:
    """Move the last canonical factor to the front.

    Conjugation by the final factor.  Repeating it cannot raise ``sup`` and
    sooner or later lowers it as far as it will go.

    Args:
        form: ``(p, factors)``.
        n_strands: Number of strands.

    Returns:
        The decycled braid, in left normal form.
    """
    p, factors = form
    if not factors:
        return form
    by = inverse_word(permutation_word(factors[-1]))
    return conjugate(to_word(form, n_strands), by, n_strands)


def _orbit_best(form: NormalForm, n_strands: int, step, better, max_rounds: int):
    """Follow a repeated operation round its orbit, keeping the best element.

    Cycling and decycling both come back on themselves sooner or later, and
    neither necessarily improves on the very first go: ``inf`` can sit still
    for several cyclings before it rises.  Stopping at the first that does not
    help is what leaves a braid short of its summit, so follow the orbit until
    it repeats and keep the best seen.

    Args:
        form: Where to start.
        n_strands: Number of strands.
        step: The operation to repeat.
        better: Says whether the first argument beats the second.
        max_rounds: Safety limit on the orbit length.

    Returns:
        The best element of the orbit.
    """
    best = here = form
    seen = {form}
    for _ in range(max_rounds):
        here = step(here, n_strands)
        if better(invariants(here), invariants(best)):
            best = here
        if here in seen:
            break
        seen.add(here)
    return best


def summit(form: NormalForm, n_strands: int, max_rounds: int = 2000) -> NormalForm:
    """Drive a braid to a summit element of its conjugacy class.

    Cycling round its orbit for the largest ``inf``, then decycling round its
    own for the smallest ``sup``, and both again until neither moves.  What
    comes out has the largest ``inf`` and smallest ``sup`` of anything
    conjugate to it, which is what makes the super summit set finite.

    Args:
        form: ``(p, factors)``.
        n_strands: Number of strands.
        max_rounds: Safety limit on the number of operations.

    Returns:
        A summit element conjugate to the input.
    """
    here = form
    for _ in range(max_rounds):
        raised = _orbit_best(
            here, n_strands, cycling, lambda a, b: a["inf"] > b["inf"], max_rounds
        )
        lowered = _orbit_best(
            raised, n_strands, decycling, lambda a, b: a["sup"] < b["sup"], max_rounds
        )
        if lowered == here:
            return here
        here = lowered
    return here


def _simple_words(n_strands: int) -> List[List[int]]:
    """Every permutation braid of ``n`` strands, as a word."""
    return [permutation_word(perm) for perm in itertools.permutations(range(n_strands))]


def super_summit_set(
    word: Sequence[int], n_strands: int, limit: int = 20000
) -> FrozenSet[NormalForm]:
    """Every summit element conjugate to this braid.

    Two braids are conjugate exactly when their super summit sets are equal,
    and since conjugating a summit element by a permutation braid reaches the
    whole set, it can be closed under those alone (Elrifai and Morton).

    The set is finite but can be large; ``limit`` stops it running away.

    Args:
        word: Signed Artin generators.
        n_strands: Number of strands.
        limit: Largest set to build before giving up.

    Returns:
        The super summit set, as normal forms.

    Raises:
        TooManyConjugates: If the set outgrows ``limit``.
    """
    start = summit(normal_form(word, n_strands), n_strands)
    target = invariants(start)
    simples = _simple_words(n_strands)

    seen = {start}
    frontier = [start]
    while frontier:
        here = frontier.pop()
        here_word = to_word(here, n_strands)
        for simple in simples:
            if not simple:
                continue
            found = conjugate(here_word, simple, n_strands)
            if found in seen:
                continue
            got = invariants(found)
            if got["inf"] != target["inf"] or got["sup"] != target["sup"]:
                continue
            seen.add(found)
            frontier.append(found)
            if len(seen) > limit:
                raise TooManyConjugates(
                    f"the super summit set passed {limit} elements; "
                    f"raise the limit or compare the invariants instead"
                )
    return frozenset(seen)


def canonical(word: Sequence[int], n_strands: int, limit: int = 20000) -> NormalForm:
    """One name for a braid and every braid conjugate to it.

    The smallest element of the super summit set, ordered by the number of
    half twists first and then by the factors.  Two braids have the same
    canonical form exactly when one is the other read from a different
    starting point -- which is the comparison a braid off a machine needs,
    since where a repeating pattern is cut is arbitrary.

    Args:
        word: Signed Artin generators.
        n_strands: Number of strands.
        limit: Passed to :func:`super_summit_set`.

    Returns:
        The canonical normal form of the conjugacy class.
    """
    return min(super_summit_set(word, n_strands, limit))


def are_conjugate(
    left: Sequence[int],
    right: Sequence[int],
    n_strands: int,
    limit: int = 20000,
) -> bool:
    """Whether two braids are the same up to where you start reading them.

    The invariants are checked first, which settles most pairs without
    building anything.

    Args:
        left: First braid, as signed Artin generators.
        right: Second braid.
        n_strands: Number of strands, the same for both.
        limit: Passed to :func:`super_summit_set`.

    Returns:
        True if the braids are conjugate in the braid group.
    """
    a = summit(normal_form(left, n_strands), n_strands)
    b = summit(normal_form(right, n_strands), n_strands)
    if invariants(a) != invariants(b):
        return False
    return canonical(left, n_strands, limit) == canonical(right, n_strands, limit)


def least_rotation(word: Sequence[int]) -> List[int]:
    """The rotation of a cyclic word that reads smallest, by Booth's method.

    This is the canonical form of a *word* read round a circle: start where
    the smallest symbol is, and where several are smallest, prefer the one
    whose next symbol is smaller, and so on.

    It is not a canonical form for a *braid*.  The same braid has many words,
    because far generators commute and neighbouring ones satisfy the braid
    relation, so two words can spell one braid and have different least
    rotations.  Use :func:`canonical` to compare braids; this is here for
    comparing the words themselves, and because it is the cheap test to try
    first.

    Args:
        word: The cyclic word.

    Returns:
        The rotation that reads smallest.

    References:
        Booth, K. S. (1980). Lexicographically least circular substrings.
        *Information Processing Letters*, 10(4-5), 240-242.
    """
    letters = list(word)
    if not letters:
        return []
    doubled = letters + letters
    failure = [-1] * len(doubled)
    best = 0
    for j in range(1, len(doubled)):
        letter = doubled[j]
        i = failure[j - best - 1]
        while i != -1 and letter != doubled[best + i + 1]:
            if letter < doubled[best + i + 1]:
                best = j - i - 1
            i = failure[i]
        if letter != doubled[best + i + 1]:
            if letter < doubled[best]:
                best = j
            failure[j - best] = -1
        else:
            failure[j - best] = i + 1
    return doubled[best : best + len(letters)]
