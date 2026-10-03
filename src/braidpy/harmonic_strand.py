# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: harmonic_strand.py
Description: A braid's drawn strands as exact Fourier series
Authors: Baptiste Labat
Created: 2026-09-20
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

Where :class:`~braidpy.parametric_strand.ParametricStrand` is a curve you
sample, this is a curve you have the coefficients of.

A drawn strand is piecewise: over each generator it runs along a polynomial
profile sideways and a half sine off the axis
(:class:`~braidpy.parametric_strand.StrandPath`).  Both pieces integrate
against cos and sin in closed form, so the Fourier coefficients of the whole
path are a finite sum of exact terms — no quadrature, no sampling, and no
error beyond the arithmetic.

For a braid of ``M`` generators the path has period ``L = M`` and

.. math::

    f(z) = a_0 + \\sum_{n\\ge 1} a_n \\cos(\\omega_n z) + b_n \\sin(\\omega_n z),
    \\qquad \\omega_n = \\frac{2\\pi n}{L}

Everything reduces to two families of one-segment integrals.  For the
sideways motion, whose profile is a polynomial, integration by parts turns
:math:`\\int_0^1 \\tau^k \\cos(\\omega\\tau)` and its sine partner into a
two-line recurrence.  For the motion off the axis, product-to-sum settles
:math:`\\int_0^1 \\sin(\\pi\\tau)\\cos(\\omega\\tau)` at once.  Carrying each
segment to its place along the axis is then a rotation.

This describes the *drawn* curve, faithfully and exactly.  It is not the
shape a strand takes under tension, and no series of this kind is: see
``src/braidpy/analytic/WHY_NOT_ANALYTIC.md``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

import plotly.graph_objects as go

from braidpy.parametric_strand import (
    LINEAR,
    Profile,
    StrandPath,
    strand_paths,
)
from braidpy.pure_braid import closing_repeats, is_pure
from braidpy.utils import terminal_colors


class ImpureBraidError(ValueError):
    """Raised when an impure braid is asked for something only a pure one has.

    A Fourier series describes a periodic function, and a strand's path is
    only periodic if the braid brings every strand back to the slot it
    started in.  Repeat the braid until it does;
    :func:`~braidpy.pure_braid.closing_repeats` says how many times.
    """


def _polynomial_trig_integrals(
    omega: float, degree: int
) -> Tuple[List[float], List[float]]:
    """:math:`\\int_0^1 \\tau^k \\cos(\\omega\\tau)` and its sine partner, k up to degree.

    Integrating :math:`\\tau^k\\cos(\\omega\\tau)` by parts drops the power by
    one and swaps cosine for sine, which gives the pair of recurrences below.
    They are exact, and cost one multiplication each.

    Args:
        omega: Angular frequency; must not be zero.
        degree: Highest power needed.

    Returns:
        (cosine integrals, sine integrals), each indexed by power.
    """
    cosines = [math.sin(omega) / omega]
    sines = [(1.0 - math.cos(omega)) / omega]
    for power in range(1, degree + 1):
        cosines.append(math.sin(omega) / omega - power * sines[power - 1] / omega)
        sines.append(-math.cos(omega) / omega + power * cosines[power - 1] / omega)
    return cosines, sines


def _half_sine_trig_integrals(omega: float) -> Tuple[float, float]:
    """:math:`\\int_0^1 \\sin(\\pi\\tau)\\cos(\\omega\\tau)` and its sine partner.

    Product-to-sum turns each into a pair of elementary integrals.  One
    denominator vanishes when ``omega`` is exactly pi — which happens on the
    harmonic halfway up a braid of an even number of generators — and both
    expressions have finite limits there, taken directly.

    Args:
        omega: Angular frequency.

    Returns:
        (against cosine, against sine).
    """
    sum_frequency = math.pi + omega
    difference = math.pi - omega

    # sin A cos B = (sin(A+B) + sin(A-B)) / 2
    against_cosine = 0.5 * (1.0 - math.cos(sum_frequency)) / sum_frequency
    # sin A sin B = (cos(A-B) - cos(A+B)) / 2
    against_sine = -0.5 * math.sin(sum_frequency) / sum_frequency

    if abs(difference) < 1e-12:
        # The difference term becomes (1 - cos 0) / 0 -> 0 and sin 0 / 0 -> 1.
        against_sine += 0.5
    else:
        against_cosine += 0.5 * (1.0 - math.cos(difference)) / difference
        against_sine += 0.5 * math.sin(difference) / difference
    return against_cosine, against_sine


@dataclass(frozen=True)
class HarmonicStrand:
    """One strand's path as a truncated Fourier series.

    Args:
        length: The period along the braid axis, one unit per generator.
        mean: The (x, y) average over one period — the series' constant term.
        cosines: Per harmonic, the (x, y) cosine coefficients, from n = 1.
        sines: Per harmonic, the (x, y) sine coefficients, from n = 1.
    """

    length: int
    mean: Tuple[float, float]
    cosines: Tuple[Tuple[float, float], ...]
    sines: Tuple[Tuple[float, float], ...]

    @property
    def n_harmonics(self) -> int:
        """How many harmonics were kept."""
        return len(self.cosines)

    def position(self, z: float) -> Tuple[float, float, float]:
        """Where the series puts the strand at ``z`` along the axis.

        Args:
            z: Distance along the braid axis; the series is periodic in it.

        Returns:
            (x, y, z).
        """
        x, y = self.mean
        for index, ((cos_x, cos_y), (sin_x, sin_y)) in enumerate(
            zip(self.cosines, self.sines), start=1
        ):
            omega = 2.0 * math.pi * index / self.length
            cosine = math.cos(omega * z)
            sine = math.sin(omega * z)
            x += cos_x * cosine + sin_x * sine
            y += cos_y * cosine + sin_y * sine
        return x, y, z

    def amplitude(self, harmonic: int) -> Tuple[float, float]:
        """The (x, y) size of one harmonic, regardless of its phase.

        Args:
            harmonic: Which harmonic, counting from 1.

        Returns:
            (x, y) amplitudes, each the hypotenuse of that harmonic's cosine
            and sine coefficients.
        """
        cos_x, cos_y = self.cosines[harmonic - 1]
        sin_x, sin_y = self.sines[harmonic - 1]
        return math.hypot(cos_x, sin_x), math.hypot(cos_y, sin_y)


def strand_harmonics(path: StrandPath, n_harmonics: int = 8) -> HarmonicStrand:
    """The exact Fourier coefficients of one strand's path.

    Args:
        path: The strand to transform.
        n_harmonics: How many harmonics to compute, from the first.

    Returns:
        The series, truncated at ``n_harmonics``.

    Raises:
        ValueError: If fewer than one harmonic is asked for.
    """
    if n_harmonics < 1:
        raise ValueError(f"A series needs at least one harmonic, not {n_harmonics}.")

    length = float(path.length)
    degree = len(path.profile) - 1
    profile_mean = sum(
        coefficient / (power + 1) for power, coefficient in enumerate(path.profile)
    )

    # The constant term is the average over the period.  Sideways, each segment
    # contributes its starting slot plus the profile's own average times the
    # step it makes; off the axis, a half sine averages 2/pi of its amplitude,
    # so segments that cross one way cancel those that cross the other.
    mean_x = 0.0
    mean_y = 0.0
    for segment in range(path.length):
        start = path.slots[segment] * path.spacing
        step = path.slots[segment + 1] * path.spacing - start
        mean_x += start + step * profile_mean
        mean_y += path.signs[segment] * path.amplitude * 2.0 / math.pi
    mean_x /= length
    mean_y /= length

    cosines: List[Tuple[float, float]] = []
    sines: List[Tuple[float, float]] = []

    for harmonic in range(1, n_harmonics + 1):
        omega = 2.0 * math.pi * harmonic / length
        power_cosines, power_sines = _polynomial_trig_integrals(omega, degree)
        sine_cosine, sine_sine = _half_sine_trig_integrals(omega)

        # The profile's own projections, shared by every segment: only the
        # step it is multiplied by changes from one segment to the next.
        profile_against_cosine = sum(
            coefficient * power_cosines[power]
            for power, coefficient in enumerate(path.profile)
        )
        profile_against_sine = sum(
            coefficient * power_sines[power]
            for power, coefficient in enumerate(path.profile)
        )

        cos_x = cos_y = sin_x = sin_y = 0.0
        for segment in range(path.length):
            shift_cos = math.cos(omega * segment)
            shift_sin = math.sin(omega * segment)

            start = path.slots[segment] * path.spacing
            step = path.slots[segment + 1] * path.spacing - start
            height = path.signs[segment] * path.amplitude

            # Each segment's integral against cos(omega tau) and sin(omega tau),
            # before it is carried to its place along the axis.
            local_x_cos = start * power_cosines[0] + step * profile_against_cosine
            local_x_sin = start * power_sines[0] + step * profile_against_sine
            local_y_cos = height * sine_cosine
            local_y_sin = height * sine_sine

            # cos(omega (m + tau)) = cos wm cos wt - sin wm sin wt
            # sin(omega (m + tau)) = sin wm cos wt + cos wm sin wt
            cos_x += shift_cos * local_x_cos - shift_sin * local_x_sin
            sin_x += shift_sin * local_x_cos + shift_cos * local_x_sin
            cos_y += shift_cos * local_y_cos - shift_sin * local_y_sin
            sin_y += shift_sin * local_y_cos + shift_cos * local_y_sin

        scale = 2.0 / length
        cosines.append((scale * cos_x, scale * cos_y))
        sines.append((scale * sin_x, scale * sin_y))

    return HarmonicStrand(
        length=path.length,
        mean=(mean_x, mean_y),
        cosines=tuple(cosines),
        sines=tuple(sines),
    )


def braid_harmonics(
    braid,
    n_harmonics: int = 8,
    spacing: float = 1.0,
    amplitude: float = 0.2,
    profile: Profile = LINEAR,
) -> List[HarmonicStrand]:
    """The Fourier series of every drawn strand of a braid.

    Args:
        braid: A :class:`~braidpy.braid.Braid`.
        n_harmonics: How many harmonics to compute, from the first.
        spacing: Distance between neighbouring slots.
        amplitude: How far off the axis a crossing strand rides.
        profile: How a strand travels sideways within a segment.

    Returns:
        One :class:`HarmonicStrand` per strand, in strand order.

    Raises:
        ImpureBraidError: If the braid leaves the strands permuted, so that
            no strand's path joins up and there is no series to speak of.
    """
    if not is_pure(braid):
        repeats = closing_repeats(braid)
        advice = (
            f"repeating it {repeats} times closes it"
            if repeats
            else "no repeat within the search limit closes it"
        )
        raise ImpureBraidError(
            f"This braid leaves the strands permuted, so a strand's path does "
            f"not join up and is not periodic: {advice}."
        )

    return [
        strand_harmonics(path, n_harmonics)
        for path in strand_paths(
            braid, spacing=spacing, amplitude=amplitude, profile=profile
        )
    ]


def reconstruction_error(
    path: StrandPath, harmonics: HarmonicStrand, n_samples: int = 400
) -> float:
    """How far the truncated series strays from the path it came from.

    A useful thing to watch: the sideways motion of a braid is nearly a single
    harmonic and converges at once, while the crossings, which are where the
    braid actually happens, need a few more.

    Args:
        path: The exact path.
        harmonics: Its series.
        n_samples: How many points along the period to compare at.

    Returns:
        The largest distance between the two, over the sampled points.
    """
    worst = 0.0
    for index in range(n_samples):
        z = path.length * index / n_samples
        exact = path.position(z)
        approximate = harmonics.position(z)
        worst = max(
            worst, math.hypot(exact[0] - approximate[0], exact[1] - approximate[1])
        )
    return worst


def plot_spectrum(
    harmonics: Sequence[HarmonicStrand],
    title: str = "Harmonic content",
    output_html: Optional[str] = None,
) -> go.Figure:
    """How much of each strand lives in each harmonic, across and over/under.

    Amplitudes rather than coefficients, so a harmonic's size does not depend
    on where along the braid the reader happens to start counting.  On a
    regular braid it is strikingly sparse — which is what having the
    coefficients buys you over having the samples.

    Args:
        harmonics: One series per strand.
        title: Figure title.
        output_html: If given, write the figure to this path.

    Returns:
        A Plotly figure.
    """
    figure = go.Figure()
    orders = list(range(1, harmonics[0].n_harmonics + 1))

    for index, series in enumerate(harmonics):
        colour = terminal_colors[index % len(terminal_colors)]
        across, over_under = [], []
        for order in orders:
            x_amplitude, y_amplitude = series.amplitude(order)
            across.append(x_amplitude)
            over_under.append(y_amplitude)
        figure.add_trace(
            go.Bar(
                x=orders, y=across, name=f"strand {index} across", marker_color=colour
            )
        )
        figure.add_trace(
            go.Bar(
                x=orders,
                y=over_under,
                name=f"strand {index} over/under",
                marker_color=colour,
                marker_pattern_shape="/",
                opacity=0.65,
            )
        )

    figure.update_layout(
        title=title,
        barmode="group",
        xaxis_title="harmonic",
        yaxis_title="amplitude",
        xaxis=dict(dtick=1),
        margin=dict(l=40, r=20, t=60, b=40),
    )
    if output_html:
        figure.write_html(output_html)
    return figure


def plot_convergence(
    paths: Sequence[StrandPath],
    orders: Sequence[int] = (1, 2, 4, 8, 16, 32, 64),
    title: str = "How fast the series catches the braid",
    output_html: Optional[str] = None,
) -> go.Figure:
    """Worst distance between the drawn braid and its series, against harmonics.

    Args:
        paths: The drawn strand paths.
        orders: How many harmonics to try.
        title: Figure title.
        output_html: If given, write the figure to this path.

    Returns:
        A Plotly figure, both axes logarithmic.
    """
    errors = [
        max(reconstruction_error(path, strand_harmonics(path, order)) for path in paths)
        for order in orders
    ]
    figure = go.Figure(
        go.Scatter(
            x=list(orders),
            y=errors,
            mode="lines+markers",
            line=dict(width=3),
            marker=dict(size=9),
            name="worst error",
        )
    )
    figure.update_layout(
        title=title,
        xaxis=dict(title="harmonics kept", type="log"),
        yaxis=dict(title="worst distance from the drawn braid", type="log"),
        margin=dict(l=60, r=20, t=60, b=50),
    )
    if output_html:
        figure.write_html(output_html)
    return figure
