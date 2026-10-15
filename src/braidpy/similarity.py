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

None of these changes when a braid is read from another starting point
(conjugation), and the loops, linking numbers and Alexander polynomial do
not change either when the strands are numbered otherwise.  Equal
fingerprints do not prove two braids the same — no handful of invariants
can — but different ones prove them different.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

from braidpy.braid import Braid

__all__ = ["Fingerprint", "distance", "fingerprint", "home", "similar"]

# Where the Alexander polynomial is sampled: e^{iθ}, θ not a rational
# multiple of π.
ANGLES = (1.0, 2.0)


@dataclass(frozen=True)
class Fingerprint:
    """What a braid's topology is, in a few numbers; see the module."""

    n_strands: int
    loops: Tuple[int, ...]
    writhe: int
    linking: Tuple[int, ...]
    alexander: Tuple[Optional[float], ...]


def home(braid: Braid) -> Tuple[Braid, Braid]:
    """A braid's pattern: its repeating unit, and the unit repeated until
    every strand is back where it started.

    Args:
        braid: The braid.

    Returns:
        The unit, and the home braid.
    """
    from braidpy.pure_braid import closing_repeats, repeating_unit

    unit = Braid(tuple(repeating_unit(braid.generators)), braid.n_strands)
    repeats = closing_repeats(unit, limit=None) or 1
    return unit, Braid(tuple(unit.generators) * repeats, braid.n_strands)


def fingerprint(braid: Braid) -> Fingerprint:
    """A braid's fingerprint; see the module.

    Args:
        braid: The braid.

    Returns:
        Its fingerprint.
    """
    from braidpy.linking import linking_matrix
    from braidpy.properties import alexander_on_circle
    from braidpy.pure_braid import cycles

    unit, whole = home(braid)
    repeats = len(whole.generators) // max(1, len(unit.generators))
    links = linking_matrix(whole)
    upper = [
        int(links[i, j]) for i in range(len(links)) for j in range(i + 1, len(links))
    ]
    return Fingerprint(
        n_strands=braid.n_strands,
        loops=tuple(sorted((len(c) for c in cycles(unit)), reverse=True)),
        writhe=int(sum(1 if g > 0 else -1 for g in unit.generators)),
        linking=tuple(sorted(upper)),
        alexander=alexander_on_circle(unit, ANGLES, repeats),
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
    fingerprint, up to 5 for braids alike in nothing.

    Each of the five parts adds a share from 0 to 1: the numbers of
    strands, the loops, the writhe, the linking numbers, and the Alexander
    polynomial on the circle (log₁₀ of it, so that a braid twice as long
    is not twice as far away).

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
    return strands + loops + writhe + linking + alexander


@dataclass(frozen=True)
class Match:
    """A braid found like another."""

    name: str
    distance: float
    same_fingerprint: bool


def _close(a: Fingerprint, b: Fingerprint) -> bool:
    """The same fingerprint, the Alexander samples but for rounding."""
    if (a.n_strands, a.loops, a.writhe, a.linking) != (
        b.n_strands,
        b.loops,
        b.writhe,
        b.linking,
    ):
        return False
    return all(
        (x is None and y is None)
        or (x is not None and y is not None and math.isclose(x, y, abs_tol=1e-6))
        for x, y in zip(a.alexander, b.alexander)
    )


def catalogue_braids() -> Dict[str, Braid]:
    """The braids of :mod:`braidpy.braid_catalog`, by name."""
    from braidpy.braid_catalog import CATALOGUE

    return {name: entry.make() for name, entry in CATALOGUE.items()}


def similar(
    braid: Braid,
    candidates: Optional[Mapping[str, Braid]] = None,
    count: int = 5,
) -> List[Match]:
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
    mine = fingerprint(braid)
    found = []
    for name, other in candidates.items():
        theirs = fingerprint(other)
        found.append(Match(name, distance(mine, theirs), _close(mine, theirs)))
    found.sort(key=lambda m: (not m.same_fingerprint, m.distance, m.name))
    return found[:count]
