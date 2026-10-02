# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The exact Fourier series of a drawn braid."""

import math

import numpy as np
import pytest

from braidpy.braid import Braid
from braidpy.harmonic_strand import (
    ImpureBraidError,
    braid_harmonics,
    plot_convergence,
    plot_spectrum,
    reconstruction_error,
    strand_harmonics,
)
from braidpy.parametric_strand import LINEAR, SMOOTHSTEP, strand_paths

FLAT_BRAID = Braid((1, -2) * 3, n_strands=3)
WIDER_BRAID = Braid((1, -2, 3, -2) * 3, n_strands=4)


def numerical_coefficients(path, harmonic, n_samples=200_001):
    """The coefficients by quadrature, which knows nothing of the closed form."""
    length = float(path.length)
    zs = np.linspace(0.0, length, n_samples)[:-1]
    xs = np.array([path.position(z)[0] for z in zs])
    ys = np.array([path.position(z)[1] for z in zs])
    omega = 2.0 * math.pi * harmonic / length
    cosine, sine = np.cos(omega * zs), np.sin(omega * zs)
    return (
        (
            2 / length * np.trapz(xs * cosine, zs),
            2 / length * np.trapz(ys * cosine, zs),
        ),
        (2 / length * np.trapz(xs * sine, zs), 2 / length * np.trapz(ys * sine, zs)),
    )


# ── The coefficients are exact ────────────────────────────────────────────────


@pytest.mark.parametrize("profile", [LINEAR, SMOOTHSTEP])
@pytest.mark.parametrize("harmonic", [1, 2, 3, 5])
def test_the_coefficients_match_quadrature(profile, harmonic):
    """The point of the closed form: no sampling, and nothing lost to it."""
    path = strand_paths(FLAT_BRAID, profile=profile)[0]
    series = strand_harmonics(path, harmonic)

    wanted_cosines, wanted_sines = numerical_coefficients(path, harmonic)
    for axis in (0, 1):
        assert series.cosines[harmonic - 1][axis] == pytest.approx(
            wanted_cosines[axis], abs=1e-8
        )
        assert series.sines[harmonic - 1][axis] == pytest.approx(
            wanted_sines[axis], abs=1e-8
        )


@pytest.mark.parametrize("profile", [LINEAR, SMOOTHSTEP])
def test_the_constant_term_is_the_average_position(profile):
    path = strand_paths(FLAT_BRAID, profile=profile)[0]
    series = strand_harmonics(path, 1)

    zs = np.linspace(0.0, float(path.length), 100_001)[:-1]
    xs = np.array([path.position(z)[0] for z in zs])
    ys = np.array([path.position(z)[1] for z in zs])
    assert series.mean[0] == pytest.approx(np.trapz(xs, zs) / path.length, abs=1e-8)
    assert series.mean[1] == pytest.approx(np.trapz(ys, zs) / path.length, abs=1e-8)


def test_the_resonant_harmonic_is_finite():
    """Halfway up a braid of even length the sine integrals go to 0/0.

    The limit is finite and is taken directly; without it the coefficient
    would come back as a nan and quietly poison the series.
    """
    path = strand_paths(FLAT_BRAID)[0]  # six generators, so harmonic 3 resonates
    series = strand_harmonics(path, 4)
    assert all(
        math.isfinite(value) for pair in series.cosines + series.sines for value in pair
    )
    wanted_cosines, wanted_sines = numerical_coefficients(path, 3)
    assert series.cosines[2][1] == pytest.approx(wanted_cosines[1], abs=1e-8)
    assert series.sines[2][1] == pytest.approx(wanted_sines[1], abs=1e-8)


def test_a_series_needs_a_harmonic():
    path = strand_paths(FLAT_BRAID)[0]
    with pytest.raises(ValueError, match="at least one harmonic"):
        strand_harmonics(path, 0)


# ── The series describes the braid ────────────────────────────────────────────


@pytest.mark.parametrize("braid", [FLAT_BRAID, WIDER_BRAID])
def test_more_harmonics_means_a_closer_braid(braid):
    paths = strand_paths(braid)
    errors = [
        max(
            reconstruction_error(path, series)
            for path, series in zip(paths, braid_harmonics(braid, kept))
        )
        for kept in (2, 8, 32, 128)
    ]
    assert errors == sorted(errors, reverse=True), f"not converging: {errors}"
    assert errors[-1] < 0.01, f"128 harmonics still {errors[-1]} out"


def test_the_series_closes_on_itself():
    """A period later the series is where it began, which is what makes it one."""
    series = braid_harmonics(FLAT_BRAID)[0]
    start = series.position(0.0)
    around = series.position(float(series.length))
    assert start[0] == pytest.approx(around[0])
    assert start[1] == pytest.approx(around[1])


def test_an_impure_braid_has_no_series_and_says_how_to_close_it():
    with pytest.raises(ImpureBraidError, match="repeating it 3 times"):
        braid_harmonics(Braid((1, -2), n_strands=3))


def test_the_flat_braid_keeps_its_strands_in_a_few_harmonics():
    """The closed form's dividend: a regular braid is a sparse spectrum.

    Every strand of the flat braid does the same thing a third of a period
    apart, so they share one set of amplitudes and differ only in phase — and
    across and over/under land on separate harmonics.
    """
    strands = braid_harmonics(FLAT_BRAID, n_harmonics=6)
    amplitudes = [
        [strand.amplitude(order) for order in range(1, 7)] for strand in strands
    ]
    for other in amplitudes[1:]:
        for (x_a, y_a), (x_b, y_b) in zip(amplitudes[0], other):
            assert x_a == pytest.approx(x_b, abs=1e-12)
            assert y_a == pytest.approx(y_b, abs=1e-12)

    across = [pair[0] for pair in amplitudes[0]]
    over_under = [pair[1] for pair in amplitudes[0]]
    assert across[0] > 1.0 and max(across[1:]) < 0.1, "sideways is one harmonic"
    assert over_under[1] > 0.1 and over_under[0] < 1e-12, "crossings are not the first"


# ── Pictures ──────────────────────────────────────────────────────────────────


def test_the_figures_draw_every_strand():
    paths = strand_paths(FLAT_BRAID)
    series = braid_harmonics(FLAT_BRAID, n_harmonics=8)

    assert len(plot_spectrum(series).data) == 6, "across and over/under, per strand"
    convergence = plot_convergence(paths, orders=(1, 4, 16))
    assert len(convergence.data[0].x) == 3
    assert list(convergence.data[0].y) == sorted(convergence.data[0].y, reverse=True)
