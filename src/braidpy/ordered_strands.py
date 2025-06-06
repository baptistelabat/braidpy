# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: ordered_strands.py
Description: todo
Authors: Baptiste Labat
Created: 2025-05-26
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Strand:
    color: str
    name: str
    diameter: float


@dataclass(frozen=True)
class OrderedBraid:
    strands: list[Strand]


class FlatBraid(OrderedBraid):
    pass


class AnnulusBraid(OrderedBraid):
    pass
