# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: __init__.py
Description: BraidPy - A Python library for working with braids
This library provides tools for representing, manipulating, and analyzing braids.
It includes support for braid operations, visualization, and mathematical properties.
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from .braid import Braid as Braid
from .properties import (
    alexander_polynomial as alexander_polynomial,
    conjugacy_class as conjugacy_class,
)
