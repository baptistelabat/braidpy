from typing import List, Tuple, Optional
import numpy as np

from sympy import Matrix, eye, symbols
from dataclasses import dataclass, field

t = symbols('t')

@dataclass(frozen=True)
class Braid:
    generators: Tuple[int, ...]
    n_strands: Optional[int] = field(default=None)

    def __post_init__(self):
        # Infer number of strands if not provided
        inferred_n = abs(max(self.generators, key=abs)) + 1 if self.generators else 1
        actual_n = self.n_strands if self.n_strands is not None else inferred_n

        # Validate generators
        if any(abs(g) >= actual_n for g in self.generators):
            raise ValueError(f"Generator index out of bounds for {actual_n} strands")

        # Set the inferred value if needed (bypass frozen with object.__setattr__)
        if self.n_strands is None:
            object.__setattr__(self, 'n_strands', actual_n)

    def __repr__(self) -> str:
        return f"Braid({self.generators}, n_strands={self.n_strands})"

    def __len__(self):
        return len(self.generators)
    
    def __mul__(self, other: 'Braid') -> 'Braid':
        """Multiply two braids (concatenate them)"""
        if self.n_strands != other.n_strands:
            raise ValueError("Braids must have the same number of strands")
        return Braid(self.generators + other.generators, self.n_strands)

    def __pow__(self, n) -> 'Braid':
        """Raise bread to power two braids (concatenate them)"""
        if n == 0:
            return Braid([], self.n_strands)
        elif n > 0:
            result = self
            for _ in range(n - 1):
                result = result*self
            return result
        else:
            return (self**n).inverse()
    def __key(self):
        return tuple(self.generators + [self.n_strands])

    def word_eq(self, other):
        return self.__key() == other.__key()


    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        """
        For now we check equality of words

        Args:
            other:

        Returns:

        """
        return self.word_eq(other)
    
    def inverse(self) -> 'Braid':
        """Return the inverse of the braid"""
        return Braid([-g for g in reversed(self.generators)], self.n_strands)
    
    def writhe(self) -> int:
        """Calculate the writhe of the braid (sum of generator powers)"""
        return sum(np.sign(self.generators))

    def to_matrix(self) -> Matrix:
        """Convert braid to its (unreduced) Burau matrix representation."""
        matrix = eye(self.n_strands)

        for gen in self.generators:
            i = abs(gen) - 1
            B = eye(self.n_strands)
            if gen > 0:
                # σ_i
                B[i, i] = 1 - t
                B[i, i + 1] = t
                B[i + 1, i] = 1
                B[i + 1, i + 1] = 0
            if gen < 0:
                # σ_i⁻¹
                B[i, i] = 0
                B[i, i + 1] = 1
                B[i + 1, i] = t ** -1
                B[i + 1, i + 1] = 1 - t ** -1
            matrix = matrix * B  # Correct order: left-to-right
        return matrix

    def to_reduced_matrix(self):
        return self.to_matrix()[:-1, :-1]

    def is_trivial(self) -> bool:
        """Check if the braid is trivial (identity braid)"""
        return not self.generators or all(g == 0 for g in self.generators)
    
    def perm(self) -> List[int]:
        """Return the permutation induced by the braid"""
        strands = list(range(1, self.n_strands + 1))
        for gen in self.generators:
            i = abs(gen) - 1
            if gen > 0:  # Positive crossing (σ_i)
                strands[i], strands[i+1] = strands[i+1], strands[i]
            else:        # Negative crossing (σ_i⁻¹)
                strands[i+1], strands[i] = strands[i], strands[i+1]
        return strands

    def is_pure(self) -> bool:
        """Check if a braid is pure (permutation is identity)"""
        return self.perm() == list(range(1, self.n_strands + 1))


    def is_palindromic(self):
        return self.generators == self.generators[::-1]

    def is_involutive(self):
        return self.inverse().generators == self.generators

    def cyclic_conjugates(self):
        return [self.generators[i:] + self.generators[:i] for i in range(len(self.generators))]

    def is_equivalent_to(self, other):
        if self.n != other.n:
            return False
        return any(conj == other.word for conj in self.cyclic_conjugates())
