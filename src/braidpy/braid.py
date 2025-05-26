from typing import List, Tuple, Optional
import numpy as np

from sympy import Matrix, eye, symbols
from dataclasses import dataclass, field

from braidpy.utils import int_to_superscript, int_to_subscript, colorize

import braidvisualiser as bv
import matplotlib

matplotlib.use("qtagg")

t = symbols("t")


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
            object.__setattr__(self, "n_strands", actual_n)

    def __repr__(self) -> str:
        return f"Braid({self.generators}, n_strands={self.n_strands})"

    def format(
        self,
        generator_symbols: list[str] = None,
        inverse_generator_symbols: list[str] = None,
        zero_symbol: str = "0",
        separator: str = "",
    ) -> str:
        """
        Allow to format the braid word following different format.
        Note that the power are limited to -1/1 (not possible to display σ₁² for example)

        Args:
            generator_symbols:
            inverse_generator_symbols:
            zero_symbol:
            separator:

        Returns:

        """
        if generator_symbols is None:
            generator_symbols = [
                "σ" + int_to_subscript(i + 1) for i in range(self.n_strands)
            ]
        if inverse_generator_symbols is None:
            inverse_generator_symbols = [
                "σ" + int_to_subscript(i + 1) + int_to_superscript(-1)
                for i in range(self.n_strands)
            ]

        word = ""
        for i, gen in enumerate(self.generators):
            if gen > 0:
                word = word + generator_symbols[gen - 1]
            elif gen < 0:
                word = word + inverse_generator_symbols[-gen - 1]
            else:
                word = word + zero_symbol
            if i < len(self.generators) - 1:
                word += separator
        return f"{word}"

    def __len__(self):
        return len(self.generators)

    def __mul__(self, other: "Braid") -> "Braid":
        """Multiply two braids (concatenate them)"""
        if self.n_strands != other.n_strands:
            raise ValueError("Braids must have the same number of strands")
        return Braid(self.generators + other.generators, self.n_strands)

    def __pow__(self, n) -> "Braid":
        """Raise bread to power two braids (concatenate them)"""
        if n == 0:
            return Braid([], self.n_strands)
        elif n > 0:
            result = self
            for _ in range(n - 1):
                result = result * self
            return result
        else:
            return (self ** (-n)).inverse()

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

    def inverse(self) -> "Braid":
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
                B[i + 1, i] = t**-1
                B[i + 1, i + 1] = 1 - t**-1
            matrix = matrix * B  # Correct order: left-to-right
        return matrix

    def to_reduced_matrix(self):
        return self.to_matrix()[:-1, :-1]

    def is_trivial(self) -> bool:
        """Check if the braid is trivial (identity braid)"""
        return not self.generators or all(g == 0 for g in self.generators)

    def permutations(self, plot=False) -> List[int]:
        """Return the permutations induced by the braid"""
        perms = []
        strands = list(range(1, self.n_strands + 1))
        perms.append(strands.copy())
        if plot:
            print(" ".join(colorize(item) for item in strands))
        for gen in self.generators:
            i = abs(gen) - 1
            if gen > 0:  # Positive crossing (σ_i)
                if plot:
                    print(
                        " ".join(colorize(item) for item in strands[: i + 1])
                        + colorize(">", strands[i] - 1)
                        + " ".join(colorize(item) for item in strands[i + 1 :])
                    )
                strands[i], strands[i + 1] = strands[i + 1], strands[i]
            elif gen < 0:  # Negative crossing (σ_i⁻¹)
                if plot:
                    print(
                        " ".join(colorize(item) for item in strands[: i + 1])
                        + colorize("<", strands[i + 1] - 1)
                        + " ".join(colorize(item) for item in strands[i + 1 :])
                    )
                strands[i + 1], strands[i] = strands[i], strands[i + 1]

            else:
                if plot:
                    print(" ".join(colorize(item) for item in strands))
                # No crossing
                strands = strands

            perms.append(strands.copy())
        if plot:
            print(" ".join(colorize(item) for item in strands))
        return perms

    def perm(self):
        """

        Returns:
            list: return the final permutation due to braid
        """
        return self.permutations()[-1]

    def is_pure(self) -> bool:
        """Check if a braid is pure (permutation is identity)"""
        return self.perm() == list(range(1, self.n_strands + 1))

    def is_palindromic(self):
        return self.generators == self.generators[::-1]

    def is_involutive(self):
        return self.inverse().generators == self.generators

    def cyclic_conjugates(self):
        return [
            self.generators[i:] + self.generators[:i]
            for i in range(len(self.generators))
        ]

    def is_equivalent_to(self, other):
        if self.n != other.n:
            return False
        return any(conj == other.word for conj in self.cyclic_conjugates())

    def draw(self):
        self.permutations(plot=True)

        #Return self to enable to chain the different steps
        return self

    def plot(self, style="ext", line_width=3, gap_size=3, color="rainbow", save=False):
        """
        style : "comp" or "ext"
            "comp" renders the image of the braid in a compact style with
            crossings parallel to one another if possible. "ext", for extended,
            shows the crossings in series.
        line_width : int (Default = 3)
            Thickness of the strands in the figure.
        gap_size : int (Default = 3)
            Amount of space shown at crossings for undercrossing strands.
        color : str
            Multicolor strands defined by "rainbow". Single fixed colour for
            all strands can be chosen from:
                {'b': blue,
                'g': green,
                'r': red,
                'c': cyan,
                'm': magenta,
                'y': yellow,
                'k': black,
                'w': white}
        Args:
            save:

        Returns:

        """
        b = bv.Braid(self.n_strands, *self.generators)

        b.draw(
            save=save,
            style=style,
            line_width=line_width,
            gap_size=gap_size,
            color=color,
        )
