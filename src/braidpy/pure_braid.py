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
bring it home.  :func:`closing_repeats` says how many.
"""

from typing import List, Optional

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


def closing_repeats(braid: Braid, limit: int = 1000) -> Optional[int]:
    """How many times a braid must be repeated before it is pure.

    Repeating a braid repeats its permutation, and a permutation has finite
    order, so a closing repeat always exists — the limit is there to stop a
    mistake running away rather than because one might not.

    Args:
        braid: The braid.
        limit: How many repeats to try.

    Returns:
        The smallest number of repeats that closes it — 1 if it is already
        pure — or None if the limit was reached first.
    """
    generators = list(braid.generators)
    n_strands = braid.n_strands or max(abs(g) for g in generators) + 1
    for repeats in range(1, limit + 1):
        if is_pure(Braid(tuple(generators * repeats), n_strands=n_strands)):
            return repeats
    return None
