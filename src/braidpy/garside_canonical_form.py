from dataclasses import dataclass
from typing import Tuple


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
    n_strands: int
    Ai: Tuple[int]

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
        """
        return self.n_half_twist // 2

    @property
    def garside_length(self) -> int:
        """
        Returns the Garside (canonical) length of the braid,
        defined as the number of simple elements A_i in the positive part.
        """
        return len(self.Ai)
