# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: braid.py
Description: Main braid class
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

import enum
from typing import List, Tuple, Optional, Union
import numpy as np

from sympy import Matrix, eye, symbols
from dataclasses import dataclass, field

from braidpy.garside_canonical_form import GarsideCanonicalFactors
from braidpy.parametric_strand import (
    ParametricStrand,
    make_idle_arc,
    make_arc,
    Arc,
    combine_arcs,
)
from braidpy.utils import (
    int_to_superscript,
    int_to_subscript,
    colorize,
    StrictlyPositiveInt,
)

import braidvisualiser as bv

import math_braid
from collections.abc import Iterable

t = symbols("t")

# Define a type alias for clarity
SignedCrossingIndex = int
BraidingStep = Union[SignedCrossingIndex, Tuple[SignedCrossingIndex, ...]]
BraidingProcess = Tuple[BraidingStep, ...]


class BraidWordNotation(str, enum.Enum):
    ARTIN = "ARTIN"
    ALPHA = "ALPHA"
    DEFAULT = "DEFAULT"


def single_crossing_braiding_process(
    process: BraidingProcess,
) -> List[SignedCrossingIndex]:
    """
    Flattens a tuple of braiding steps into a list of signed crossings.

    Each step may be a single crossing or multiple simultaneous crossings.
    To get Artin generators we need only consecutive single crossing, which is topologically equivalent
    """
    sequential_single_crossings_index: List[SignedCrossingIndex] = []
    for step in process:
        if isinstance(step, Iterable):
            sequential_single_crossings_index.extend(step)
        else:
            sequential_single_crossings_index.append(
                int(step)
            )  # Force int type to be able to use with math_braid
    return sequential_single_crossings_index


# Recursive type for nested tuples of integers
BraidProcess = Union[int, Tuple["BraidProcess", ...]]


@dataclass(frozen=True)
class Braid:
    """
    Sometimes referred as algebraic braids
    Args:
        process (BraidProcess): list of Artin's generator, which may group or not by parenthesis (tuples)
        n_strands (Optional[int]): number of strands. Default to the minimum number needed for process
    """

    process: BraidProcess
    n_strands: Optional[int] = field(default=None)

    def __post_init__(self):
        # Hack to allow to code single generator without parenthesis
        if isinstance(self.process, Iterable):
            process = self.process
        else:
            process = (self.process,)
            object.__setattr__(self, "process", (self.process,))

        sequential_generators = single_crossing_braiding_process(process)
        # Infer number of strands if not provided
        inferred_n = (
            abs(max(sequential_generators, key=abs)) + 1 if sequential_generators else 1
        )
        actual_n = self.n_strands if self.n_strands is not None else inferred_n

        # Validate generators
        if any(abs(g) >= actual_n for g in sequential_generators):
            raise ValueError(f"Generator index out of bounds for {actual_n} strands")

        # Set the inferred value if needed (bypass frozen with object.__setattr__)
        if self.n_strands is None:
            object.__setattr__(self, "n_strands", actual_n)

    @property
    def generators(self):
        return single_crossing_braiding_process(self.process)

    @property
    def main_generator(self):
        """A main generator of a braid word w is the generator with the lowest index
        https://pure.tue.nl/ws/portalfiles/portal/67742824/630595-1.pdf page 33

        """
        if not self.no_zero().generators:
            return None
        return min([abs(gen) for gen in self.generators if abs(gen) > 0])

    def __repr__(self) -> str:
        return f"Braid({self.generators}, n_strands={self.n_strands})"

    def format_to_notation(self, target: str = ""):
        """
        Inspired from https://github.com/abhikpal/dehornoy/blob/master/braid.py

        Allow for targets:


        The Artin representation can also be used in a latex file.

        The neutral element is 'e' for the Artin representation and '#' for alpha.

        Args:
            target(str): Among
                'alpha': for example 'aBa'
                'artin'  for example 's_{1}^{1.0} s_{2}^{1.0} s_{1}^{-1.0} s_{2}^{-1.0}'
                'default'

        Returns:
            str: the formated braid word
        """
        match target.upper():
            case BraidWordNotation.ARTIN.value:
                if len(self.generators) == 0:
                    return "e"
                return " ".join(
                    "s_{" + str(abs(g)) + "}^{" + str(abs(g) / g) + "}"
                    if g != 0
                    else "e"
                    for g in self.generators
                )
            case BraidWordNotation.ALPHA.value:
                if len(self.generators) == 0:
                    return "#"

                def alp(g):
                    return chr(ord("Q") + int(abs(g) / g) * 16 + abs(g) - 1)

                return "".join(alp(g) if g != 0 else "#" for g in self.generators)
            case BraidWordNotation.DEFAULT.value | "":
                """
                This is the syntax used by math-braid and braidlab
                """
                return "<" + " : ".join(str(g) for g in self.generators) + ">"
            case _:
                raise NotImplementedError(
                    f"target notation should be among {[notation.value for notation in BraidWordNotation]}"
                )

    def format(
        self,
        generator_symbols: list[str] = None,
        inverse_generator_symbols: list[str] = None,
        zero_symbol: str = "e",
        separator: str = "",
    ) -> str:
        """
        Allow to format the braid word following different formats.

        Note that the power are limited to -1/1 due to the actual braid word definition (not possible to display σ₁² for example)

        See also format_to_notation for simpler predefined format

        Args:
            generator_symbols (Optional(list[str])): Default to ["σ₁", "σ₂", ...]
            inverse_generator_symbols(Optional(list[str])): Default to ["σ₁⁻¹", ...]
            zero_symbol (Optional(str)): Default to "e
            separator(Optional(str)): Default to ""

        Returns:
            str: the formated braid word
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

    def no_zero(self):
        """
        Suppress all the zero steps (multiplication by neutral element)

        Returns:
            Braid
        """
        return Braid([g for g in self.generators if g != 0], self.n_strands)

    def word_length(self):
        """
        Length of the word including neutral element

        Returns:
            int: the length of the braid word
        """

        return len(self.generators)

    def __len__(self):
        """
        Define the length of the braid as the length of its word

        Returns:
            int: the length of the braid word
        """
        return self.word_length()

    def __mul__(self, other: "Braid") -> "Braid":
        """Compose two braids (concatenate operation of other after self

        This corresponds to multiplication of two braids in braid theory"""
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
        """
        Enables to get a key on the braid (used by hash function)

        Returns:
            Tuple: key constructed with the Artin's generators and the number of strands
        """
        return tuple(self.generators + [self.n_strands])

    def word_eq(self, other):
        return self.__key() == other.__key()

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        """
        Check if two braids are equivalent
        We ask to get the same number of strands

        Relies on math_braid implementation from J. Cha et al, "An Efficient Implementation of Braid Groups",
        Advances in Cryptology: Proceedings of ASIACRYPT 2001,
        Lecture Notes in Computer Science (2001), 144--156.
        https://www.iacr.org/archive/asiacrypt2001/22480144.pdf

        Complexity is in O(l²n.log n) where n is the word size and l correspond roughly to the number of strands.

        Might not be the best algorithm compared to handle reduction which is efficient in practice and
        whose complexity is assumed to be linear in O(n), but without proof and an exponential majorant.
        ON WORD REVERSING IN BRAID GROUPS PATRICK DEHORNOY AND BERT WIEST
        https://dehornoy.lmno.cnrs.fr/Papers/Dhg.pdf

        Args:
            other(Braid): the braid to compare with

        Returns:
            bool: True if the braid are topologically equivalent
        """
        if self.n_strands != other.n_strands:
            return False
        if not self.no_zero().generators and not other.no_zero().generators:
            return True
        return math_braid.Braid(
            list(self.generators), self.n_strands
        ) == math_braid.Braid(list(other.generators), other.n_strands)

    def inverse(self) -> "Braid":
        """
        Return the inverse of the braid
        This corresponds to the image of the braid in a mirror.
        Both order and signs are reversed

        Returns:
            Braid: the inverse braid
        """
        return Braid([-g for g in reversed(self.generators)], self.n_strands)

    def __invert__(self):
        """
        Inverse of the braid with symbole ~
        This corresponds to the image of the braid in a mirror orthogonal to the braid direction
        The last operation becomes the firt one
        Both order of operation and signs are reversed, but not order of strands

        >>> x = Braid([1, -2], 3)
        >>> ~x

        Returns:
            Braid
        """
        return self.inverse()

    def n(self, n_strands):
        """
        Compact notation to allow to change the number of strands

        Args:
            n_strands:

        Returns:

        """
        return Braid(self.process, n_strands)

    def flip(self):
        """
        Flip the braid
        This corresponds to the image of the braid in a mirror on the side of the braid reordered from left to right
        The strands are reversed, not the order of operations
        Sign is also changed.
        This step is often used when braiding

        >>> b = Braid([1], 3)
        >>> basic_3_braid = (b*(b.flip()))**3

        Returns:
            Braid: the reversed braid
        """
        gen = [-np.sign(g) * (self.n_strands - abs(g)) for g in self.generators]
        return Braid(gen, self.n_strands)

    def half_twist(self, sign: int = +1):
        """
        Twist the braid with half a turn

        https://en.wikipedia.org/wiki/Twist_(differential_geometry)


        Args:
            sign(Optional[int]): sign of the twist. IF positive the first strand is going over. Default to +1

        Returns:
            Braid: the twisted braid
        """
        b = self
        for i in range(abs(self.n_strands)):
            b = b * (
                slide_strand(
                    start_index=1, n_slide=self.n_strands - i - 1, sign=np.sign(sign)
                ).n(self.n_strands)
            )

        return b

    def full_twist(self, sign: int = +1):
        """
        Twist the braid with a complete turn

        https://en.wikipedia.org/wiki/Twist_(differential_geometry)

        Args:
            sign(Optional[int]): sign of the twist. IF positive the first strand is going over. Default to +1

        Returns:
            Braid: the twisted braid
        """
        return self.half_twist(sign=sign).half_twist(sign=sign)

    def up_side_down(self):
        """
        Invert up and down crossing operations

        For hair braiding this is called "inversé"

        Returns:
            Braid: the mirrored braid
        """
        gen = [-g for g in self.generators]
        return Braid(gen, self.n_strands)

    def __neg__(self):
        """
        Invert up and down crossing operations

        Returns:
            Braid: the mirrored braid
        """
        return self.up_side_down()

    def is_reduced(self) -> bool:
        """A braid word w is reduced either if it is the null string, or the empty braid, or if the main
        generator of w occurs only positively or only negatively.
        https://pure.tue.nl/ws/portalfiles/portal/67742824/630595-1.pdf page 33
        """
        if not self.generators:
            return True
        mg = self.main_generator

        signs = [g > 0 for g in self.generators if abs(g) == mg]
        return all(signs) or not any(signs)

    def writhe(self) -> int:
        """Calculate the writhe of the braid (sum of generator powers)"""
        return sum(np.sign(self.generators))

    def get_canonical_factors(self):
        """
        Get decomposition in left normal form

        Relies on math_braid implementation from J. Cha et al, "An Efficient Implementation of Braid Groups",
        Advances in Cryptology: Proceedings of ASIACRYPT 2001,
        Lecture Notes in Computer Science (2001), 144--156.
        https://www.iacr.org/archive/asiacrypt2001/22480144.pdf

        Returns:
            GarsideCanonicalFactors: the unique decomposition of the braid according to left convention
        """
        br = self.no_zero()
        if br.generators:
            b = math_braid.Braid(list(self.generators), self.n_strands)
            b.cleanUpFactors()
            return GarsideCanonicalFactors(n_half_twist=b.p, n_strands=b.n, Ai=b.a)
        else:
            return GarsideCanonicalFactors(
                n_half_twist=0, n_strands=StrictlyPositiveInt(br.n_strands), Ai=()
            )

    def to_matrix(self) -> Matrix:
        """Convert braid to its (unreduced) Burau matrix representation."""
        matrix = eye(self.n_strands)

        for gen in self.generators:
            i = abs(gen) - 1
            mat = eye(self.n_strands)
            if gen > 0:
                # σ_i
                mat[i, i] = 1 - t
                mat[i, i + 1] = t
                mat[i + 1, i] = 1
                mat[i + 1, i + 1] = 0
            if gen < 0:
                # σ_i⁻¹
                mat[i, i] = 0
                mat[i, i + 1] = 1
                mat[i + 1, i] = t**-1
                mat[i + 1, i + 1] = 1 - t**-1
            matrix = matrix * mat  # Correct order: left-to-right
        return matrix

    def to_reduced_matrix(self):
        """
        Return the reduced Burau representation

        \todo Implementation not finished
        """

        raise NotImplementedError(
            "Implementation in progress, several definitions make validation difficult"
        )
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
        Compute the permutation corresponding to the braid

        This is a braid invariant.

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
        """
        Returns true if inverse of braid word ie the same as braid word
        This probably works only for the neutral element

        Returns:
            bool: True if braid word is involutive
        """
        return self.inverse().generators == self.generators

    def is_periodic(self):
        """
        braid x is periodic if and only if its nth power or its (n − 1)st power is a power of the half-twist ∆

        https://hal.science/hal-00647035v2/file/B_nNTHClassificationv5.pdf

        Periodic braid are roots of ∆**m
        https://homepages.math.uic.edu/~jaca2009/notes/Meneses.pdf
        """

        return (self ** (2 * self.n_strands)).perm() == list(
            range(1, self.n_strands + 1)
        ) or (self ** (2 * (self.n_strands - 1))).perm() == list(
            range(1, self.n_strands + 1)
        )

    def is_brunnian(self):
        """
        A Brunnian braid is a braid that becomes trivial upon removal of any one of its strings.
        Brunnian braids form a subgroup of the braid group

        https://en.wikipedia.org/wiki/Brunnian_link#Brunnian_braids

        Returns:
            bool: True if Brunnian
        """
        raise NotImplementedError()

    def to_parametric_strands(self, amplitude: float = 0.2) -> List[ParametricStrand]:
        """
        Converts a braid into a list of 3D parametric strand paths.

        Args:
            braid: The Braid object containing crossing generators.
            amplitude: Height of the sine wave for over/under crossings.

        Returns:
            A list of ParametricStrand objects representing the strands.
        """
        n_strands = self.n_strands or max(abs(g) for g in self.generators) + 1
        n_segments = len(self.generators) + 1
        duration_per_gen = 1 / n_segments

        # Track strand positions across braid steps
        positions = list(range(n_strands))
        position_history = [positions.copy()]

        for gen in self.generators:
            i = abs(gen) - 1
            positions = positions.copy()
            if gen != 0:
                positions[i], positions[i + 1] = positions[i + 1], positions[i]
            position_history.append(positions.copy())

        # Transpose history to get each strand's path
        strand_paths = [[] for _ in range(n_strands)]
        for step in position_history:
            for x_pos, strand_id in enumerate(step):
                strand_paths[strand_id].append(x_pos)

        # Generate arc sequences for each strand
        strand_arc_sequences: List[List[Arc]] = []
        for strand_id in range(n_strands):
            arcs: List[Arc] = []
            path = strand_paths[strand_id]

            for k in range(n_segments - 1):
                i0 = path[k]
                i1 = path[k + 1]
                x0 = i0 * amplitude
                x1 = i1 * amplitude
                t_start = k * duration_per_gen
                t_end = (k + 1) * duration_per_gen
                gen = self.generators[k]
                if i0 == i1 or gen == 0:
                    arc_func = make_idle_arc(x0, t_start, t_end)
                else:
                    i = abs(gen) - 1
                    over = (i0 == i and gen > 0) or (i0 == i + 1 and gen < 0)
                    arc_func = make_arc(
                        x0, x1, t_start, t_end, amplitude if over else -amplitude
                    )

                arcs.append((t_start, t_end, arc_func))

            # Final segment (idle)
            t_final_start = (n_segments - 1) * duration_per_gen
            t_final_end = t_final_start + duration_per_gen
            x_final = path[-1] * amplitude
            arcs.append(
                (
                    t_final_start,
                    t_final_end,
                    make_idle_arc(x_final, t_final_start, t_final_end),
                )
            )
            strand_arc_sequences.append(arcs)

        return [
            ParametricStrand(combine_arcs(strand)) for strand in strand_arc_sequences
        ]

    def draw(self):
        """
        Draw the braid in the terminal with arrows allowing
        to better check the differnet operations (with colors !)

        Returns:
            Braid: return the braid itself to allow to debug in a chain
        """
        self.permutations(plot=True)

        # Return self to enable to chain the different steps
        return self

    def plot(self, style="ext", line_width=3, gap_size=3, color="rainbow", save=False):
        """
        Plot the braid using library braid-visualiser
        https://github.com/rexgreenway/braid-visualiser

        Args:
            style(Optional(str)): "comp" or "ext"(default)
                "comp" renders the image of the braid in a compact style with
                crossings parallel to one another if possible. "ext", for extended,
                shows the crossings in series.
            line_width(Optional(int)): Default to 3
                Thickness of the strands in the figure.
            gap_size(Optional(int)): Default to 3
                Amount of space shown at crossings for undercrossing strands.
            color(str): Multicolor strands defined by "rainbow". Single fixed colour for
                all strands can be chosen from:
                {'b': blue,
                'g': green,
                'r': red,
                'c': cyan,
                'm': magenta,
                'y': yellow,
                'k': black,
                'w': white}
            save(bool): if True save to file "test.svg"

        Returns:
            Braid: return the slightly modified braid to allow to debug in a chain
        """
        # Neutral elements are not supported by library used
        compact = self.no_zero()
        b = bv.Braid(compact.n_strands, *compact.generators)

        b.draw(
            save=save,
            style=style,
            line_width=line_width,
            gap_size=gap_size,
            color=color,
        )
        return b


def slide_strand(n_slide, start_index=1, sign: int = +1):
    """
    Combine Artin Generator to move one braid over or under several braids

    This is noted as (ai...as) by Garside where i=start_index and s= i+n_slide

    Πs corresponds to start_index=1 (default) and n_slide=s-1


    Args:
        n_slide (int): number of crossings
        start_index(Optional(int)): index of the strand to move. Default to 1
        sign(Optional[int]): positive if the start strand is going over. Default to +1

    Returns:
        Braid: the corresponding braid
    """

    b = Braid(0, n_strands=n_slide + start_index)
    for i in range(0, n_slide):
        b = b * Braid(sign * (start_index + i), n_strands=n_slide + start_index)
    return b.no_zero()


def weave_strand(n_slide, start_index=1, sign: int = +1):
    """
    Combine Artin Generator to move one braid over/under/over... or under/over/under... several braids

    Args:
        n_slide (int): number of crossings
        start_index(Optional(int)): index of the strand to move. Default to 1
        sign(Optional[int]): positive if the start strand is first going over. Default to +1

    Returns:
        Braid: the corresponding braid
    """

    b = Braid(0, n_strands=n_slide + start_index)
    for i in range(0, n_slide):
        b = b * Braid(
            sign * (start_index + i) * (-1) ** i, n_strands=n_slide + start_index
        )
    return b.no_zero()
