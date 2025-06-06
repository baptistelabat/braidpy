# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: properties.py
Description: Properties of braid
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from typing import List
from sympy import Poly, symbols, simplify
from .braid import Braid

t = symbols("t")


def alexander_polynomial(braid: Braid) -> Poly:
    """Compute the Alexander polynomial of a braid."""
    matrix = braid.to_matrix()

    # Reduced Burau: delete last row and column
    reduced_matrix = matrix[:-1, :-1]

    # Compute determinant
    det = reduced_matrix.det()

    # Normalize: remove t shift and make monic
    poly = Poly(simplify(det / t ** Poly(det, t).degree()), t).monic()
    return poly


def conjugacy_class(braid: Braid, conjugators: List[Braid] = None) -> List[Braid]:
    """
    Generate conjugates of a braid by a list of other braids.

    Args:
        braid: The Braid object to conjugate
        conjugators: A list of Braid objects to use as conjugators

    Returns:
        List of unique conjugates a * braid * a⁻¹
    """
    conjugates = set()
    if conjugators is None:
        conjugators = [
            Braid([i], braid.n_strands) for i in range(1, braid.n_strands)
        ] + [Braid([-i], braid.n_strands) for i in range(1, braid.n_strands)]

    for a in conjugators:
        inv_a = a.inverse()  # You need to implement or have this method
        conj = a * braid * inv_a  # Assume Braid class supports multiplication
        conjugates.add(conj)

    return list(conjugates)
