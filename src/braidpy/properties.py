# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: properties.py
Description: Properties and invariants of braids
Authors: Baptiste Labat
Created: 2025-05-24
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from collections.abc import Sequence
from typing import TYPE_CHECKING

from .braid import Braid, reduced_burau_generator

if TYPE_CHECKING:
    from sympy import Poly


def _burau_product(braid: Braid, t, one, zero, product, identity):
    """The braid's reduced Burau matrix, a generator at a time, in whatever
    ring ``t``, ``one`` and ``zero`` are of: ``product(a, rows)`` multiplies
    a matrix by a generator's rows, ``identity`` is where it starts."""
    matrix = identity
    for generator in braid.generators:
        matrix = product(
            matrix,
            reduced_burau_generator(generator, braid.n_strands, t, one, zero),
        )
    return matrix


def alexander_polynomial(braid: Braid) -> "Poly":
    """The Alexander polynomial of the braid's closure, in ``t``.

    From the reduced Burau matrix B of an n-strand braid (Burau, 1935):

        Δ(t) ≐ det(I − B) (1 − t) / (1 − tⁿ),

    up to a unit ±tᵏ, which is fixed here as most tables fix it: no
    negative powers, a nonzero constant term, a positive leading
    coefficient.  A split link — loops that could be pulled apart — has
    Δ = 0, as can some links that are not.

    It is a link invariant: it is the same for a braid read from any
    starting point (conjugation), and for braids on different numbers of
    strands that close up the same way (Markov's theorem).  It does not
    tell a braid from its mirror image, nor every link from every other.

    Computed exactly, over the field of rational functions of t: a few
    hundred crossings on eight strands take a fraction of a second.  For
    longer braids, :func:`alexander_on_circle` samples it.

    Args:
        braid: The braid.

    Returns:
        Δ(t), as a polynomial with integer coefficients.

    References:
        W. Burau, "Über Zopfgruppen und gleichsinnig verdrillte
        Verkettungen", Abh. Math. Sem. Hamburg 11, 179 (1935).
        D. Rolfsen, *Knots and Links* (1976), chapter 8.
    """
    from sympy import QQ, Integer, Poly, fraction, symbols
    from sympy.polys.matrices import DomainMatrix

    t = symbols("t")
    n = braid.n_strands
    if n == 1:
        return Poly(Integer(1), t)
    field = QQ.frac_field(t)
    m = n - 1
    burau = _burau_product(
        braid,
        field.convert(t),
        field.one,
        field.zero,
        lambda a, rows: a * DomainMatrix(rows, (m, m), field),
        DomainMatrix.eye(m, field),
    )
    determinant = field.to_sympy((DomainMatrix.eye(m, field) - burau).det())
    numerator, _ = fraction((determinant * (1 - t) / (1 - t**n)).cancel())
    poly = Poly(numerator, t)
    if poly.is_zero:
        return poly
    # Up to ±tᵏ: no factor of t, a positive leading coefficient.
    coefficients = poly.all_coeffs()
    while coefficients[-1] == 0:
        coefficients.pop()
    poly = Poly(coefficients, t)
    return -poly if poly.LC() < 0 else poly


# |Δ| below this, on the circle, is zero but for rounding.
_ZERO = 1e-8


def alexander_on_circle(
    braid: Braid, angles: Sequence[float], repeats: int = 1
) -> tuple[float | None, ...]:
    """``log₁₀ |Δ(e^{iθ})|``: the Alexander polynomial of the closure of the
    braid repeated ``repeats`` times, sampled on the unit circle.

    On the unit circle ``|±tᵏ| = 1``, so the modulus is exactly an invariant of
    the closure, with nothing to normalise; it is computed numerically, from
    the braid's Burau matrix at t = e^{iθ} raised to the power ``repeats`` —
    milliseconds where the polynomial of a long braid takes minutes.  The
    angles should not be rational multiples of π: at an n-th root of unity
    the formula divides by zero.

    Args:
        braid: The braid.
        angles: The angles θ, in radians.
        repeats: How many times the braid is repeated before it is closed.

    Returns:
        Per angle, ``log₁₀ |Δ|``; None where Δ vanishes there.
    """
    import numpy as np

    n = braid.n_strands
    if n == 1:
        return tuple(0.0 for _ in angles)
    values: list[float | None] = []
    for theta in angles:
        t = complex(np.exp(1j * theta))
        burau = _burau_product(
            braid,
            t,
            1.0 + 0j,
            0j,
            lambda a, rows: a @ np.array(rows, dtype=complex),
            np.eye(n - 1, dtype=complex),
        )
        power = np.linalg.matrix_power(burau, repeats)
        _, log_det = np.linalg.slogdet(np.eye(n - 1) - power)
        value = (log_det + np.log(abs(1 - t)) - np.log(abs(1 - t**n))) / np.log(10)
        values.append(
            None if not np.isfinite(value) or value < np.log10(_ZERO) else float(value)
        )
    return tuple(values)


def conjugacy_class(
    braid: Braid, conjugators: list[Braid] | None = None
) -> list[Braid]:
    """Generate conjugates of a braid by a list of other braids.

    Args:
        braid: The Braid object to conjugate.
        conjugators: A list of Braid objects to use as conjugators.
            Defaults to generators and their inverses.

    Returns:
        List[Braid]: List of unique conjugates a * braid * a⁻¹.
    """
    conjugates = set()
    if conjugators is None:
        conjugators = [
            Braid([i], braid.n_strands) for i in range(1, braid.n_strands)
        ] + [Braid([-i], braid.n_strands) for i in range(1, braid.n_strands)]

    for a in conjugators:
        inv_a = a.inverse()  # You need to implement or have this method
        conj = a * braid * inv_a  # Assume Braid class supports multiplication
        conjugates.add(conj)

    return list(conjugates)
