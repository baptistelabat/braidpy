# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braids compared by what does not depend on how they are written down.

The same braid can be written many ways: from another starting point, with
far crossings swapped, made of more or fewer repeats.  What does not change
is its *topology*, and a few numbers measure it.  A braid's
:func:`fingerprint` holds them; :func:`similar` ranks other braids by how
far their fingerprints are from it — to suggest, for a braid of your own,
the braids it is most like.

The fingerprint is of the braid's pattern, not of its length: the word's
:func:`~braidpy.pure_braid.repeating_unit`, and that unit repeated until
every strand is back where it started (:func:`home`), which closes each
strand into a loop of its own.  It holds:

- ``n_strands``;
- ``loops``: how the unit takes the strands round — the sizes of the loops
  its closure makes, largest first (:func:`braidpy.pure_braid.cycles`);
- ``writhe``: the unit's crossings counted with their signs.  It tells a
  braid from its mirror image, which the others do not;
- ``linking``: how many times each two strands wind round each other in a
  repeat, as linking numbers of the home braid's loops
  (:func:`braidpy.linking.linking_matrix`), sorted, so that it does not
  matter which strand is which;
- ``alexander``: the Alexander polynomial of the home braid's closure,
  sampled on the unit circle (:func:`braidpy.properties.alexander_on_circle`).
  It tells apart braids the linking numbers cannot: a plait from strands
  hanging straight, both with all their linking numbers 0.
- ``burau``: the characteristic polynomial of the home braid's Burau matrix,
  sampled on the unit circle
  (:func:`braidpy.properties.burau_polynomial_on_circle`).  It tells apart
  braids whose Alexander polynomial vanishes, as it does for many braids
  closing into several loops: a kumihimo disk's edo yatsu from Ashley's
  8-strand square sinnet, ABOK #3070, which agree on all the rest.
- ``burau_mod``: that characteristic polynomial again, exactly, modulo a
  prime at a few values of t
  (:func:`braidpy.properties.burau_polynomial_mod`).  The samples above are
  in floating point, which a long braid rounds differently for each way it
  is written; they say how *near* two braids are (:func:`distance`), this
  says whether they are the *same* (:func:`same_fingerprint`).  It holds the
  Alexander polynomial too, as its value at 1.

None of these changes when a braid is read from another starting point
(conjugation), and the loops, linking numbers and Alexander and Burau
polynomials do not change either when the strands are numbered otherwise.  Equal
fingerprints do not prove two braids the same — no handful of invariants
can — but different ones prove them different.
:func:`braidpy.conjugacy.same_pattern` proves either way, more slowly;
:class:`braidpy.braid_pattern.BraidPattern` is a braid compared so.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Optional

from braidpy.braid import Braid

__all__ = [
    "Fingerprint",
    "distance",
    "exact_part",
    "fingerprint",
    "home",
    "same_fingerprint",
    "similar",
]

# Where the Alexander polynomial is sampled: e^{iθ}, θ not a rational
# multiple of π.
ANGLES = (1.0, 2.0)

# Where the Burau polynomial is taken exactly, modulo
# :data:`braidpy.properties.PRIME`: the first primitive roots of that prime
# past a third and two thirds of it, so that no power of t short of the
# (PRIME − 1)-th is 1, as it would be at a root of unity, and not small
# numbers, at which polynomials with small coefficients agree more often
# (t − 2 vanishes at 2).
BURAU_T = (22369623, 44739239)


@dataclass(frozen=True)
class Fingerprint:
    """What a braid's topology is, in a few numbers; see the module."""

    n_strands: int
    loops: tuple[int, ...]
    writhe: int
    linking: tuple[int, ...]
    alexander: tuple[float | None, ...]
    burau: tuple[float, ...] = ()
    burau_mod: tuple[tuple[int, ...], ...] = ()


def home(braid: Braid) -> tuple[Braid, Braid]:
    """A braid's pattern: its repeating unit, and the unit repeated until
    every strand is back where it started.

    Args:
        braid: The braid.

    Returns:
        The unit, and the home braid.
    """
    unit, repeats = _unit_and_repeats(braid)
    return unit, Braid(tuple(unit.generators) * repeats, braid.n_strands)


def _unit_and_repeats(braid: Braid) -> tuple[Braid, int]:
    """The braid's repeating unit, and how many repeats bring every strand
    home: :func:`home` without writing the home braid out, which for a long
    unit is millions of crossings."""
    from braidpy.pure_braid import closing_repeats, repeating_unit

    unit = Braid(tuple(repeating_unit(braid.generators)), braid.n_strands)
    return unit, closing_repeats(unit, limit=None) or 1


def fingerprint(braid: Braid) -> Fingerprint:
    """A braid's fingerprint; see the module.

    Args:
        braid: The braid.

    Returns:
        Its fingerprint.
    """
    from braidpy.linking import linking_matrix
    from braidpy.properties import (
        PRIME,
        alexander_on_circle,
        burau_polynomial_mod,
        burau_polynomial_on_circle,
    )
    from braidpy.pure_braid import cycles

    unit, repeats = _unit_and_repeats(braid)
    links = linking_matrix(unit, repeats)
    upper = [
        int(links[i, j]) for i in range(len(links)) for j in range(i + 1, len(links))
    ]
    exact = tuple(burau_polynomial_mod(unit, t, repeats) for t in BURAU_T)
    alexander = alexander_on_circle(unit, ANGLES, repeats)
    # Where det(1 − Bᵏ), the polynomial at x = 1, is exactly 0, the Alexander
    # polynomial vanishes, however far from 0 rounding left its samples.
    if all(sum(coefficients) % PRIME == 0 for coefficients in exact):
        alexander = tuple(None for _ in ANGLES)
    return Fingerprint(
        n_strands=braid.n_strands,
        loops=tuple(sorted((len(c) for c in cycles(unit)), reverse=True)),
        writhe=int(sum(1 if g > 0 else -1 for g in unit.generators)),
        linking=tuple(sorted(upper)),
        alexander=alexander,
        burau=burau_polynomial_on_circle(unit, ANGLES, repeats),
        burau_mod=exact,
    )


def _apart(a: Sequence[float], b: Sequence[float]) -> float:
    """How far apart two lists of numbers are, from 0 (the same) towards 1:
    padded with zeros to one length, their difference over their size."""
    size = max(len(a), len(b))
    a = list(a) + [0] * (size - len(a))
    b = list(b) + [0] * (size - len(b))
    total = sum(abs(x) + abs(y) for x, y in zip(a, b))
    return sum(abs(x - y) for x, y in zip(a, b)) / total if total else 0.0


def distance(a: Fingerprint, b: Fingerprint) -> float:
    """How unlike two braids are, from their fingerprints: 0 for the same
    fingerprint, up to 6 for braids alike in nothing.

    Each of the six parts adds a share from 0 to 1: the numbers of
    strands, the loops, the writhe, the linking numbers, and the Alexander
    and Burau polynomials on the circle (log₁₀ of them, so that a braid
    twice as long is not twice as far away).

    Args:
        a: A fingerprint.
        b: Another.

    Returns:
        The distance.
    """
    strands = abs(a.n_strands - b.n_strands) / max(a.n_strands, b.n_strands)
    loops = _apart(a.loops, b.loops)
    writhe = _apart([a.writhe], [b.writhe])
    linking = _apart(a.linking, b.linking)
    alexander = 0.0
    for x, y in zip(a.alexander, b.alexander):
        if x is None or y is None:
            alexander += 0.0 if x is y else 1.0
        else:
            alexander += abs(x - y) / (1 + abs(x) + abs(y))
    alexander /= max(1, len(ANGLES))
    burau = sum(
        abs(x - y) / (1 + abs(x) + abs(y)) for x, y in zip(a.burau, b.burau)
    ) / max(1, len(ANGLES))
    return strands + loops + writhe + linking + alexander + burau


@dataclass(frozen=True)
class Match:
    """A braid found like another."""

    name: str
    distance: float
    same_fingerprint: bool


def same_fingerprint(a: Fingerprint, b: Fingerprint) -> bool:
    """Whether two fingerprints are the same: nothing measured tells the
    braids apart.

    The polynomials are compared by ``burau_mod``, exactly, not by their
    samples in floating point: those differ in the third digit for two long
    words of one braid, and ``burau_mod`` holds what they measure.

    Args:
        a: A fingerprint.
        b: Another.

    Returns:
        True if they are the same.
    """
    return exact_part(a) == exact_part(b)


def exact_part(mark: Fingerprint) -> tuple:
    """What :func:`same_fingerprint` compares: the parts of a fingerprint
    taken exactly, not sampled in floating point.  Hashable: a key for
    braids by their pattern (:class:`braidpy.braid_pattern.BraidPattern`).

    Args:
        mark: A fingerprint.

    Returns:
        Its strands, loops, writhe, linking numbers and Burau polynomials
        modulo a prime.
    """
    return (mark.n_strands, mark.loops, mark.writhe, mark.linking, mark.burau_mod)


def catalogue_braids() -> dict[str, Braid]:
    """The braids of :mod:`braidpy.braid_catalog`, by name."""
    from braidpy.braid_catalog import CATALOGUE

    return {name: entry.make() for name, entry in CATALOGUE.items()}


def similar(
    braid: Braid,
    candidates: Optional[Mapping[str, Braid]] = None,
    count: int = 5,
) -> list[Match]:
    """The braids most like this one, nearest first.

    Args:
        braid: The braid — your own, say.
        candidates: The braids to look among, by name; by default those of
            :mod:`braidpy.braid_catalog`.
        count: How many to give.

    Returns:
        Up to ``count`` matches, by :func:`distance`; ``same_fingerprint``
        where nothing measured tells the two apart.
    """
    if candidates is None:
        candidates = catalogue_braids()
    mine = braid.pattern()
    found = []
    for name, other in candidates.items():
        theirs = other.pattern()
        found.append(
            Match(
                name,
                distance(mine.fingerprint, theirs.fingerprint),
                mine.alike(theirs),
            )
        )
    found.sort(key=lambda m: (not m.same_fingerprint, m.distance, m.name))
    return found[:count]
