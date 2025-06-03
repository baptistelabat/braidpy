from enum import Enum
from typing import List, Literal, Optional

import numpy as np

from braidpy import Braid

class FunctionalException(Exception):
    pass

class HandleReducedButUnexpectedResult(FunctionalException):
    pass

class HandleReductionMode(str, Enum):
    FULL="FULL"
    COMPARE="COMPARE"

def dehornoy_handle_indices(gens):
    """
    Detect the first Dehornoy handle in gens.
    A handle is of the form g ... g^-1, with all intermediates having strictly larger absolute values.
    Returns (i, j) — the indices of g and g^-1 — for the first such valid handle.
    """
    n = len(gens)

    for j in range(1, n):
        g = -gens[j]  # we're looking for a gens[i] == -gens[j]
        for i in range(j):
            if gens[i] == g:
                # Check all between gens[i+1 : j] are strictly larger in absolute value
                if all(abs(h) > abs(g) for h in gens[i + 1 : j]):
                    return i, j  # first such handle found
    return None


def reduce_handle(segment):
    """
    Reduces a Dehornoy handle of the form [sigma_m, u..., sigma_m^{-1}]
    by keeping u and replacing each sigma_{m+1} with sigma_{m+1}^{-1} * sigma_m * sigma_{m+1}.
    """

    m = abs(segment[0])
    e = np.sign(segment[0])
    if segment[-1] != -segment[0]:
        return segment  # not a valid Dehornoy handle

    u = segment[1:-1]
    result = []

    for g in u:
        abs_g = abs(g)
        d = np.sign(g)

        if abs_g == m + 1:
            # Replace σ_{m+1} with σ_{m+1}^{-1} * σ_m * σ_{m+1}
            replacement = [-e * (m + 1), d * m, e * (m + 1)]
            result.extend(replacement)
        else:
            result.append(g)

    return result

def dehornoy_sign(gens: List[int]):
    """

    """
    if gens:
        mg = min(abs(g) for g in gens)
        signs = [np.sign(g) for g in gens if abs(g) == mg]
        if all([s>=0 for s in signs]):
            return 1
        elif all([s<=0 for s in signs]):  # all negative
            return -1
        elif all([s==0 for s in signs]):
            return 0
        else:
            return None
    else:
        return 0

def dehornoy_reduce_core(
    gens: List[int], mode: HandleReductionMode = HandleReductionMode.FULL
) -> tuple[List[int], Optional[int]]:
    """
    Unified Dehornoy reduction engine.
    - `mode="full"`: returns the fully reduced word.
    - `mode="compare"`: returns early if positive/neutral/negative.

    Returns: (reduced_gens, sign) where sign is:
        - 1 if Dehornoy positive
        - -1 if Dehornoy negative
        - 0 if neutral element
        - None in case it can not be said without reducing handles further
    """
    gens = list(gens)

    # Suppress potential zero
    gens = [g for g in gens if g != 0]

    if not isinstance(mode, HandleReductionMode):
        mode=HandleReductionMode(mode.upper())

    while True:
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
        raise HandleReducedButUnexpectedResult(f"Braid word reduced to {gens}, but sign can not be determined which is unexpected")
    return gens, sign
