# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: artin_generators.py
Description: Artin's generators enables to describe a braid by successive crossing operations
Authors: Baptiste Labat
Created: 2025-05-30
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from braidpy import Braid


class a(Braid):
    """
    This class is a shortcut to be able to use a compact notation with Artin's generators
    """

    def __post_init__(self) -> None:
        """
        Ensures we have only one crossing
        """
        super().__post_init__()
        if len(self.process) > 1:  # Process is a Tuple
            raise ValueError(
                f"Artin generator is only a single crossing, but process is {self.process}"
            )

    def __mul__(self, other: Braid) -> Braid:
        """
        Compose two braids (concatenate operation of other after self)

        This corresponds to multiplication of two braids in braid theory.

        Resulting braid will have the minimum number of strands necessary

        Args:
            other(Braid): the other braid to add after

        Returns:
            Braid: the resulting braid
        """

        # Take max number of strands in this case
        n_strands = max(self.n_strands, other.n_strands)

        return Braid(self.generators + other.generators, n_strands)

    def __rmul__(self, other: Braid) -> Braid:
        """
        Compose two braids (concatenate operation of self after the other)

        This corresponds to multiplication of two braids in braid theory

        other*self (right multiplication)

        Resulting braid will have the minimum number of strands necessary

        Args:
            other(Braid): the other braid to be concatenated

        Returns:
            Braid: the resulting braid
        """

        # Take max number of strands in this case
        n_strands = max(self.n_strands, other.n_strands)

        return Braid(other.generators + self.generators, n_strands)

    def __repr__(self) -> str:
        """
        Adapt representation

        Returns:
            str: a string allowing to recreate this object
        """
        return f"a({self.generators[0]})"
