from typing import List, Tuple
import numpy as np
from sympy import Matrix, Poly, symbols, simplify
from .braid import Braid

t = symbols('t')

def alexander_polynomial(braid: Braid) -> Poly:
    """Compute the Alexander polynomial of a braid."""
    matrix = braid.to_matrix()

    # Reduced Burau: delete last row and column
    reduced_matrix = matrix[:-1, :-1]

    # Compute determinant
    det = reduced_matrix.det()

    # Normalize: remove t shift and make monic
    poly = Poly(simplify(det / t**Poly(det, t).degree()), t).monic()
    return poly


def conjugacy_class(braid: Braid, conjugators: List[Braid]=None) -> List[Braid]:
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
        conjugators = ([Braid([i], braid.n_strands) for i in range(1, (braid.n_strands))]
                       +[Braid([-i], braid.n_strands) for i in range(1, (braid.n_strands))])

    for a in conjugators:
        inv_a = a.inverse()  # You need to implement or have this method
        conj = a * braid * inv_a  # Assume Braid class supports multiplication
        conjugates.add(conj)

    return list(conjugates)

def garside_normal_form(braid: Braid) -> Tuple[List[int], List[int]]:
    """
    Compute the Garside normal form of a braid.
    
    Args:
        braid: The Braid object
    
    Returns:
        Tuple of (positive part, negative part) in the normal form
    """
    # This is a simplified version - full implementation would be more complex
    positive_part = [g for g in braid.generators if g > 0]
    negative_part = [g for g in braid.generators if g < 0]
    return (positive_part, negative_part)
