"""
Operations on braids.

This module provides various operations that can be performed on braids.
"""

from .braid import Braid


def multiply(b1: Braid, b2: Braid) -> Braid:
    """
    Multiply two braids (concatenate them).

    Args:
        b1: First braid
        b2: Second braid

    Returns:
        The product of the two braids

    Raises:
        ValueError: If the braids have different number of strands
    """
    if b1.n_strands != b2.n_strands:
        raise ValueError("Braids must have the same number of strands")
    return Braid(b1.generators + b2.generators, b1.n_strands)


def conjugate(b: Braid, c: Braid) -> Braid:
    """
    Conjugate a braid by another braid.

    Args:
        b: The braid to conjugate
        c: The conjugating braid

    Returns:
        The conjugated braid c * b * c.inverse()
    """
    return multiply(multiply(c, b), c.inverse())


def power(b: Braid, n: int) -> Braid:
    """
    Raise a braid to a power.

    Args:
        b: The braid to raise to a power
        n: The power (can be negative)

    Returns:
        The powered braid
    """
    if n == 0:
        return Braid([], b.n_strands)
    elif n > 0:
        result = b
        for _ in range(n - 1):
            result = multiply(result, b)
        return result
    else:
        return power(b.inverse(), -n)
