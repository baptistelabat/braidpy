# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: handles_reduction.py
Description: Simplification of braid word to get unique braid representation
Authors: Baptiste Labat
Created: 2025-06-03
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

import time
from enum import Enum
from typing import List

import numpy as np

from braidpy import Braid
from braidpy.braid import SignedCrossingIndex
from braidpy.utils import FunctionalException, PositiveInt


class HandleReducedButUnexpectedResult(FunctionalException):
    """
    Exception to be raised if handle reduction is not finishing as expected
    """

    pass


class HandleReductionMode(str, Enum):
    """
    Define the possible options for handle reduction
        -full: reduce all handles
        -compare: partical short circuit reductio which is exiting as long as we can determine if braid is positive, or negative
    """

    FULL = "FULL"
    COMPARE = "COMPARE"


def dehornoy_handle_indices(
    gens: list[SignedCrossingIndex],
) -> tuple[PositiveInt, PositiveInt] | None:
    """
    Detect the first Dehornoy handle in gens.
    A handle is of the form g ... g^-1, with all intermediates having strictly larger absolute values.

    Args:
        gens(list[SignedCrossingIndex]): list of Artin's generator

    Returns:
        Tuple[int, int] | None : (i, j) — the indices of g and g^-1 — for the first such valid handle or None if no more handles
    """
    n = len(gens)

    for j in range(1, n):
        g = -gens[j]  # we're looking for a gens[i] == -gens[j]
        for i in range(j):
            if gens[i] == g:
                # Check all between gens[i+1 : j] are strictly larger in absolute value
                if all(abs(h) > abs(g) for h in gens[i + 1 : j]):
                    return i, j  # first such closing handle found
    return None


def reduce_handle(segment: list[SignedCrossingIndex]) -> list[SignedCrossingIndex]:
    """
    Reduces a Dehornoy handle of the form [sigma_m, u..., sigma_m^{-1}]
    by keeping u and replacing each sigma_{m+1} with sigma_{m+1}^{-1} * sigma_m * sigma_{m+1}.

    Args:
        segment(list[SignedCrossingIndex]): segment corresponding to handle

    Returns:
        list[SignedCrossingIndex]: the segment with handle reduced (and no more complete handle, but it may create the start of new one)

    Raises:
        ValueError: if segment is not a handle
    """

    # Index of first crossing of handle
    m = abs(segment[0])

    # Sign of crossing
    e = np.sign(segment[0])

    if segment[-1] != -segment[0]:
        raise ValueError(f"Segment {segment} is not a valid Dehornoy handle")
    else:
        # Suppress the handle
        u = segment[1:-1]

        # But take into account the effect it can have on next strand
        result = []
        for g in u:
            d = np.sign(g)
            if abs(g) == m + 1:
                # Replace σ_{m+1} with σ_{m+1}^{-1} * σ_m * σ_{m+1}
                replacement = [-e * (m + 1), d * m, e * (m + 1)]
                result.extend(replacement)
            else:
                result.append(g)

    return result


def dehornoy_sign(gens: List[SignedCrossingIndex]) -> int | None:
    """
    Check  if braid is Dehornoy positive, negative, neutral or if this can not be directly said from braid word

    Args:
        gens(SignedCrossingIndex: list of Artin's generator

    Returns:
        int|None: 1 if Dehornoy positive, -1 if Dehornoy negative, 0 if neutral element and None if it can not be said
    """
    if gens:
        mg = min(abs(g) for g in gens)
        signs = [np.sign(g) for g in gens if abs(g) == mg]
        if all([s >= 0 for s in signs]):
            return 1
        elif all([s <= 0 for s in signs]):  # all negative
            return -1
        elif all([s == 0 for s in signs]):
            return 0
        else:
            return None
    else:
        return 0


def dehornoy_reduce_core(
    gens: List[SignedCrossingIndex],
    mode: HandleReductionMode | str = HandleReductionMode.FULL,
    time_out_s: float = 1,
) -> tuple[List[SignedCrossingIndex], int | None]:
    """
    Unified Dehornoy reduction engine.

    Args:
        -gens(List[SignedCrossingIndex]): list of Artin's generators
        -mode(HandleReductionMode | str):
            "FULL": returns the fully reduced word.
            "COMPARE`: returns early if positive/neutral/negative.
        -time_out_s(Optional(float)): safety timeout. Default to 1


    Returns:
         tuple[List[SignedCrossingIndex], int|None]: (reduced_gens, sign) where sign is:
        - 1 if Dehornoy positive
        - -1 if Dehornoy negative
        - 0 if neutral element
        - None in case it can not be said without reducing handles further

    Raises:
        HandleReducedButUnexpectedResult
    """
    gens = list(gens)
    non_integers = [x for x in gens if not isinstance(x, (int, np.integer))]
    if non_integers:
        raise ValueError(f"All generators should be integers but got {non_integers}")

    # Suppress potential zero
    gens = [g for g in gens if g != 0]

    if not isinstance(mode, HandleReductionMode):
        mode = HandleReductionMode(mode.upper())
    t0 = time.time()
    while abs(time.time() - t0) < time_out_s:
        if mode == HandleReductionMode.COMPARE:
            sign = dehornoy_sign(gens)
            if sign in [-1, 0, +1]:
                return gens, sign

        handle = dehornoy_handle_indices(gens)
        if not handle:
            break
        i, j = handle

        # Apply Dehornoy handle reduction (this part was wrong before)
        reduced_segment = reduce_handle(gens[i : j + 1])
        gens = gens[:i] + reduced_segment + gens[j + 1 :]
        print(Braid(gens).format_to_notation(target="alpha"))

    sign = dehornoy_sign(gens)
    if sign is None:
        raise HandleReducedButUnexpectedResult(
            f"Braid word reduced to {gens}, but sign can not be determined which is unexpected. Consider increasing timeout if necessary"
        )
    return gens, sign
