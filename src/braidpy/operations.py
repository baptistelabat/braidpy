"""
Operations on braids.

This module provides various operations that can be performed on braids.
"""

from .braid import Braid


def conjugate(b: Braid, c: Braid) -> Braid:
    """
    Conjugate a braid by another braid.

    Args:
        b: The braid to conjugate
        c: The conjugating braid

    Returns:
        The conjugated braid c * b * c.inverse()
    """
    return c * b * c.inverse()
