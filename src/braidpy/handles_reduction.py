from typing import List, Literal, Optional

import numpy as np

from braidpy import Braid

ReductionOutcome = Literal["continue", "less", "greater", "equal", "incomparable"]


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


def dehornoy_reduce_core(
    gens: List[int], mode: Literal["full", "compare"] = "full"
) -> tuple[List[int], Optional[str]]:
    """
    Unified Dehornoy reduction engine.
    - `mode="full"`: returns the fully reduced word.
    - `mode="compare"`: returns early if positive/negative.

    Returns: (reduced_gens, status) where status is:
        - 'less' or 'greater' if early comparison detected
        - 'equal' if reduced to empty word
        - 'incomparable' if reduction halts with no decision
        - None if in full reduction mode
    """
    gens = list(gens)

    while True:
        if mode == "compare" and gens:
            mg = min(abs(g) for g in gens)
            signs = [g > 0 for g in gens if abs(g) == mg]
            if all(signs):
                return gens, "less"
            elif not any(signs):  # all negative
                return gens, "greater"

        handle = dehornoy_handle_indices(gens)
        if not handle:
            break
        i, j = handle

        # Apply Dehornoy handle reduction (this part was wrong before)
        reduced_segment = reduce_handle(gens[i : j + 1])
        gens = gens[:i] + reduced_segment + gens[j + 1 :]
        print(Braid(gens).format_to_notation(target="alpha"))

    if mode == "compare":
        return gens, "equal" if not gens else "incomparable"
    return gens, None
