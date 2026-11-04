# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Whether two braids are the same braid however written: a proof, not a
fingerprint.

Two words make the same braid, read from any starting point, when one is a
conjugate of the other: ``b = c⁻¹ a c`` for some braid ``c``.  Fingerprints
(:mod:`braidpy.similarity`) prove braids different but never the same.
This decides it, by Garside's method as Elrifai–Morton and Franco–González-
Meneses made it practical:

- every braid is written once in left normal form, ``Δ^p · A_1 ⋯ A_r``
  (:func:`braidpy.garside_canonical_form.artin_left_normal_form`);
- *cycling* and *decycling* — taking ``A_1`` round to the end, or ``A_r``
  round to the front — are conjugations, and repeated they raise ``p`` and
  lower ``p + r`` as far as any conjugate allows: to the braid's *super
  summit set*, the conjugates with ``p`` greatest and ``p + r`` least;
- that set is finite, and each of its braids leads to the others by
  conjugating with the least permutation braids that keep it there, one for
  each crossing ``σ_i`` (*minimal simple elements*); so it is found whole by
  following them;
- two braids are conjugate exactly when their super summit sets are the
  same, and so when one holds a braid of the other's.

:func:`same_braid` asks this of two braids' patterns, their
:func:`~braidpy.similarity.home` braids.  Strands numbered from the other
side, ``σ_i`` read as ``σ_{n-i}``, need no asking: that is conjugation by
``Δ``.
The set can be large — exponential in the number of strands at worst —
so the search stops at ``limit`` braids and says it could not tell.

A permutation braid is kept as in
:mod:`braidpy.garside_canonical_form`: a tuple ``p``, ``p[j]`` the place
strand ``j`` ends at; a product is read left to right.
"""

from __future__ import annotations

from collections import deque

from braidpy.braid import Braid
from braidpy.garside_canonical_form import (
    Permutation,
    _compose,
    _delta,
    _flip,
    _inverse,
    _swap,
    artin_left_normal_form,
    left_weighted,
    permutation_word,
)

__all__ = [
    "NormalForm",
    "SuperSummitSetTooLarge",
    "are_conjugate",
    "same_braid",
    "super_summit_set",
]

# A braid in left normal form: half twists in front, then the factors.
NormalForm = tuple[int, tuple[Permutation, ...]]


class SuperSummitSetTooLarge(Exception):
    """The super summit set has more braids than the search was let find."""


def _normal_form(braid: Braid) -> NormalForm:
    return artin_left_normal_form(braid.generators, braid.n_strands)


def _turned(a: Permutation, p: int) -> Permutation:
    """Conjugated by Δ^p: Δ^p a = τ^p(a) Δ^p."""
    return _flip(a) if p % 2 else a


def _word(x: NormalForm, n: int) -> list[int]:
    p, factors = x
    delta = permutation_word(_delta(n))
    word = delta * p if p >= 0 else [-g for g in reversed(delta)] * -p
    for f in factors:
        word += permutation_word(f)
    return word


def _inverse_form(x: NormalForm, n: int) -> NormalForm:
    return artin_left_normal_form([-g for g in reversed(_word(x, n))], n)


def _conjugated(x: NormalForm, u: Permutation) -> NormalForm:
    """``u⁻¹ x u`` for a permutation braid ``u``.

    ``u⁻¹ = Δ⁻¹ (Δ u⁻¹)``, and the Δ⁻¹ goes to the front through Δ^p.
    """
    p, factors = x
    first = _turned(_compose(_delta(len(u)), _inverse(u)), p)
    return left_weighted(p - 1, (first, *factors, u))


def _cycled(x: NormalForm) -> NormalForm:
    p, factors = x
    if not factors:
        return x
    return left_weighted(p, (*factors[1:], _turned(factors[0], p)))


def _decycled(x: NormalForm) -> NormalForm:
    p, factors = x
    if not factors:
        return x
    return left_weighted(p, (_turned(factors[-1], p), *factors[:-1]))


def _summit(x: NormalForm, step, better) -> NormalForm:
    """Step on until no step makes it better: once a step has come back to a
    braid already seen, none will (Elrifai–Morton)."""
    seen = {x}
    while True:
        y = step(x)
        if better(y, x):
            seen = {y}
        elif y in seen:
            return x
        seen.add(y)
        x = y


def _inf(x: NormalForm) -> int:
    return x[0]


def _sup(x: NormalForm) -> int:
    return x[0] + len(x[1])


def _in_summit(x: NormalForm) -> NormalForm:
    """A conjugate in the super summit set."""
    x = _summit(x, _cycled, lambda y, z: _inf(y) > _inf(z))
    return _summit(x, _decycled, lambda y, z: _sup(y) < _sup(z))


def _inversions(a: Permutation) -> set[tuple[int, int]]:
    """The strands, by where they start, that a permutation braid crosses."""
    n = len(a)
    return {(i, j) for i in range(n) for j in range(i + 1, n) if a[i] > a[j]}


def _from_inversions(n: int, crossed: set[tuple[int, int]]) -> Permutation:
    return tuple(
        i
        - sum((j, i) in crossed for j in range(i))
        + sum((i, j) in crossed for j in range(i + 1, n))
        for i in range(n)
    )


def _join(a: Permutation, b: Permutation) -> Permutation:
    """The least permutation braid starting with both ``a`` and ``b``: its
    crossings are theirs, and whatever crossings those force."""
    n = len(a)
    crossed = _inversions(a) | _inversions(b)
    # Strands i < j < k with i crossing j and j crossing k: i crosses k.
    for j in range(n):
        for i in range(j):
            if (i, j) in crossed:
                crossed |= {(i, k) for k in range(j + 1, n) if (j, k) in crossed}
    return _from_inversions(n, crossed)


def _after(a: Permutation, b: Permutation) -> Permutation:
    """``a⁻¹ b``, for ``a`` a start of ``b``."""
    return _compose(_inverse(a), b)


def _forced(x: NormalForm, c: Permutation) -> Permutation:
    """What ``u`` starting with ``c`` must also start with for ``u⁻¹ x u``
    to keep ``x``'s half twists in front.

    That is ``τ^p(u) ≼ A_1 ⋯ A_r u``; so ``u`` starts with
    ``(A_1⋯A_r)⁻¹ (A_1⋯A_r ∨ τ^p(c))``, worked out a factor at a time.
    """
    p, factors = x
    forced = _turned(c, p)
    for f in factors:
        forced = _after(f, _join(f, forced))
    return forced


def _minimal(x: NormalForm, inverse: NormalForm, atom: Permutation) -> Permutation:
    """The least permutation braid ``u`` starting with ``atom`` with
    ``u⁻¹ x u`` in the super summit set (Franco–González-Meneses): keeping
    the half twists of ``x`` in front, and those of ``x⁻¹``."""
    u = atom
    while True:
        grown = _join(_join(u, _forced(x, u)), _forced(inverse, u))
        if grown == u:
            return u
        u = grown


def super_summit_set(braid: Braid, limit: int | None = 10000) -> set[NormalForm]:
    """Every conjugate of a braid in its super summit set; see the module.

    Args:
        braid: The braid.
        limit: The most braids to find; None for no limit.

    Returns:
        The super summit set, each braid in left normal form.

    Raises:
        SuperSummitSetTooLarge: if it has more than ``limit`` braids.
    """
    return _search(_in_summit(_normal_form(braid)), braid.n_strands, limit)


def _search(start: NormalForm, n: int, limit: int | None) -> set[NormalForm]:
    atoms = [_swap(n, i) for i in range(1, n)]
    found = {start}
    queue = deque([start])
    while queue:
        x = queue.popleft()
        inverse = _inverse_form(x, n)
        for u in {_minimal(x, inverse, a) for a in atoms}:
            y = _conjugated(x, u)
            if y not in found:
                found.add(y)
                if limit is not None and len(found) > limit:
                    raise SuperSummitSetTooLarge(
                        f"more than {limit} braids in the super summit set"
                    )
                queue.append(y)
    return found


def are_conjugate(a: Braid, b: Braid, limit: int | None = 10000) -> bool:
    """Whether ``b = c⁻¹ a c`` for some braid ``c``: the same braid read from
    another starting point.

    Args:
        a: A braid.
        b: Another, on as many strands.
        limit: The most braids of a super summit set to find.

    Returns:
        True if they are conjugate, False if not.

    Raises:
        SuperSummitSetTooLarge: if it cannot tell within ``limit`` braids.
    """
    if a.n_strands != b.n_strands:
        return False
    n = a.n_strands
    x, y = _in_summit(_normal_form(a)), _in_summit(_normal_form(b))
    if (_inf(x), _sup(x)) != (_inf(y), _sup(y)):
        return False
    return y in _search(x, n, limit)


def same_braid(a: Braid, b: Braid, limit: int | None = 10000) -> bool:
    """Whether two braids are the same braid however written: their
    patterns (:func:`~braidpy.similarity.home`) conjugate.

    Home braids repeated as often are conjugate exactly when their units
    are, a braid's roots being unique up to conjugacy (González-Meneses):
    so then the units are compared, far shorter.  And braids whose
    fingerprints differ (:func:`~braidpy.similarity.same_fingerprint`) are
    different already: no search is made.

    Args:
        a: A braid.
        b: Another.
        limit: The most braids of a super summit set to find.

    Returns:
        True if they are proven the same, False if proven not.

    Raises:
        SuperSummitSetTooLarge: if it cannot tell within ``limit`` braids.
    """
    from braidpy.similarity import fingerprint, home, same_fingerprint

    if a.n_strands != b.n_strands:
        return False
    if not same_fingerprint(fingerprint(a), fingerprint(b)):
        return False
    (unit, whole), (other_unit, other) = home(a), home(b)
    if len(whole.generators) * len(other_unit.generators) == len(
        other.generators
    ) * len(unit.generators):
        return are_conjugate(unit, other_unit, limit)
    return are_conjugate(whole, other, limit)
