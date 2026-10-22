# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: pure_braid.py
Description: Pure braids: the ones that leave every strand where it started
Authors: Baptiste Labat
Created: 2025-05-30
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

A braid is *pure* when its word returns every strand to the slot it set out
from — when the permutation it performs is the identity.  The pure braids
form a subgroup, the kernel of the map from the braid group to the symmetric
group, and are sometimes called the coloured braid group, since each strand
can then be given a colour that survives composition.

Purity is also what decides whether a braid has a shape that repeats.  A
strand of a pure braid comes back to where it began, so its path closes and
can be described periodically; a strand of an impure one ends somewhere else
and has no period of its own until the word is repeated enough times to
bring it home.  :func:`closing_repeats` says how many, from the strands'
:func:`cycles`.
"""

from functools import reduce
from math import lcm
from typing import List, Optional, Sequence

from braidpy.braid import Braid


def permutation(braid: Braid) -> List[int]:
    """Where each strand ends up, as a slot per strand.

    Args:
        braid: The braid.

    Returns:
        ``slot[s]`` — the slot strand ``s`` finishes in, having started in
        slot ``s``.
    """
    return braid.slot_history()[-1]


def is_pure(braid: Braid) -> bool:
    """Whether the braid returns every strand to the slot it started in.

    Args:
        braid: The braid.

    Returns:
        True if its permutation is the identity.
    """
    n_strands = braid.n_strands or max(abs(g) for g in braid.generators) + 1
    return permutation(braid) == list(range(n_strands))


def cycles(braid: Braid) -> List[List[int]]:
    """The strands' cycles: the slots a strand passes through, braid after
    braid, until it is back where it started.

    Args:
        braid: The braid.

    Returns:
        Each cycle, as the slots in the order the strand visits them.  The
        braid's closure makes one separate piece per cycle.
    """
    slot = permutation(braid)
    seen: set = set()
    found: List[List[int]] = []
    for start in range(len(slot)):
        if start in seen:
            continue
        cycle: List[int] = []
        here = start
        while here not in seen:
            seen.add(here)
            cycle.append(here)
            here = slot[here]
        found.append(cycle)
    return found


def components(braid: Braid) -> int:
    """How many separate pieces the braid's closure makes: its cycles.

    Args:
        braid: The braid.

    Returns:
        1 if every strand passes through every slot before coming home.
    """
    return len(cycles(braid))


def closing_repeats(braid: Braid, limit: Optional[int] = 1000) -> Optional[int]:
    """How many times a braid must be repeated before it is pure.

    Repeating a braid repeats its permutation, so a strand is home after a
    whole number of turns of its cycle: every strand, after the least common
    multiple of the cycles' lengths.  That is the permutation's order, so a
    closing repeat always exists; the limit is there for a caller who would
    not repeat the braid that often.

    Args:
        braid: The braid.
        limit: The most repeats worth having, or None for no limit.

    Returns:
        The smallest number of repeats that closes it — 1 if it is already
        pure — or None if that is over the limit.
    """
    repeats = reduce(lcm, (len(cycle) for cycle in cycles(braid)), 1)
    return repeats if limit is None or repeats <= limit else None


def repeating_unit(word: Sequence[int]) -> List[int]:
    """The shortest word that, repeated, makes ``word``.

    Args:
        word: Signed Artin generators.

    Returns:
        The unit: ``word`` itself if it repeats nothing shorter.
    """
    word = list(word)
    for length in range(1, len(word) + 1):
        if len(word) % length == 0 and word[:length] * (len(word) // length) == word:
            return word[:length]
    return word
