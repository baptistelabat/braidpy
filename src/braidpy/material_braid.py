# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: material_braid.py
Description: Material braids describe real world braid
Authors: Baptiste Labat
Created: 2025-05-25
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from typing import Callable

import numpy as np
from braidpy.parametric_strand import ParametricStrand
from braidpy.utils import PositiveFloat, StrictlyPositiveFloat, StrictlyPositiveInt


class MaterialStrand(ParametricStrand):
    def __init__(
        self, func: Callable[[float], tuple], radius: PositiveFloat = 0.005
    ) -> None:
        """

        Args:
            func(Callable): function describing the strand x,y = f(z)
            radius(Optional[PositiveFloat]): physical thickness of the strand [m]. Default to 0.005
        """
        super().__init__(func)
        self.radius = radius


class MaterialBraid:
    def __init__(self, strands: tuple[ParametricStrand]) -> None:
        """

        Args:
            strands(tuple[ParametricStrand]): list of MaterialStrand objects
        """
        self.strands = strands
        self.n_strands = len(strands)
        self._check_nonintersecting()

    def _check_nonintersecting(
        self, min_clearance: StrictlyPositiveFloat = 1e-3
    ) -> None:
        """
        Checks that strands do not intersect or overlap.

        Args:
            min_clearance:

        Returns:
            None
        Raises:
            ValueError if strands are too close
        """
        for i in range(self.n_strands):
            for j in range(i + 1, self.n_strands):
                if self._are_too_close(self.strands[i], self.strands[j], min_clearance):
                    raise ValueError(f"Strands {i} and {j} intersect or are too close.")

    @staticmethod
    def _are_too_close(
        s1: ParametricStrand,
        s2: ParametricStrand,
        clearance: StrictlyPositiveFloat = 1e-3,
        samples: StrictlyPositiveInt = 100,
    ) -> bool:
        """
        Checks if two ParametricStrand objects are too close at any point in time.

        Args:
            s1, s2: ParametricStrand objects with .evaluate(t) and .radius
            clearance: minimum allowed distance between surfaces
            samples: number of time steps to check (default: 100)

        Returns:
            True if strands are too close; False otherwise.
        """
        ts = np.linspace(0, 1, samples)

        for t in ts:
            p1 = np.array(s1.evaluate(t))
            p2 = np.array(s2.evaluate(t))
            dist = np.linalg.norm(p1 - p2)
            if dist < s1.radius + s2.radius + clearance:
                return True
        return False
