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
        n_strands (int): The number of strands in the braid.
        Ai (Tuple[int]): The sequence of simple elements (as indices or identifiers). Also known as Garside generators
    """

    n_half_twist: int
    n_strands: StrictlyPositiveInt
    Ai: Tuple[CanonicalFactor | None]

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
