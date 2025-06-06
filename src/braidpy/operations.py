# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: operations.py
Description: This module provides various operations that can be performed on braids.
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
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
