# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: parametric_braid.py
Description: A braid describes by a punctured disk
Authors: Baptiste Labat
Created: 2025-05-25
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0
"""

from __future__ import annotations

import math
from enum import Enum
from typing import TYPE_CHECKING, List, Optional, Sequence, Tuple, cast

import numpy as np

from braidpy.parametric_strand import ParametricStrand
from braidpy.utils import StrictlyPositiveInt, PositiveFloat, terminal_colors

from braidpy.utils import lazy_module

if TYPE_CHECKING:
    import matplotlib.pyplot as plt
    import plotly.graph_objects as go
    from mpl_toolkits.mplot3d import Axes3D
else:
    plt = lazy_module("matplotlib.pyplot")
    go = lazy_module("plotly.graph_objects")


class Plotter(str, Enum):
    PLOTLY = "PLOTLY"
    MATPLOTLIB = "MATPLOTLIB"


class ParametricBraid:
    def __init__(self, strands: list[ParametricStrand]) -> None:
        self.strands = strands
        self.n_strands = len(strands)

    def get_positions_at(self, t: PositiveFloat) -> List[Tuple[float, float, float]]:
        """
        Get position of different strands at a given time

        Args:
            t: time or z coordinates

        Returns:
            List[Tuple[float, float, float]]: list of 3D coordinates
        """
        return [strand.evaluate(t) for strand in self.strands]

    def _colour(self, index: int, colors: Optional[Sequence[str]]) -> str:
        palette = colors if colors else terminal_colors
        return palette[index % len(palette)]

    def _name(self, index: int, names: Optional[Sequence[str]]) -> str:
        return names[index] if names is not None else f"Strand {index}"

    def _tube_traces(
        self,
        diameter: float,
        n_sample: int,
        n_around: int,
        opacity: float,
        colors: Optional[Sequence[str]] = None,
        names: Optional[Sequence[str]] = None,
    ) -> List[go.Surface]:
        """One tube per strand, swept at the strands' real thickness.

        See :func:`~braidpy.parametric_strand.tube_mesh` for the sweep.
        """
        from braidpy.parametric_strand import tube_mesh

        traces = []
        for index, strand in enumerate(self.strands):
            colour = self._colour(index, colors)
            x, y, z = tube_mesh(
                strand.sample(n_sample), diameter / 2.0, n_around=n_around
            )
            traces.append(
                go.Surface(
                    x=x,
                    y=y,
                    z=z,
                    surfacecolor=np.zeros_like(x),
                    colorscale=[[0.0, colour], [1.0, colour]],
                    showscale=False,
                    opacity=opacity,
                    name=self._name(index, names),
                    legendgroup=self._name(index, names),
                    showlegend=True,
                    hoverinfo="name",
                )
            )
        return traces

    def _line_traces(
        self,
        n_sample: int,
        colors: Optional[Sequence[str]] = None,
        names: Optional[Sequence[str]] = None,
        line_width: float = 10,
    ) -> List[go.Scatter3d]:
        """One line per strand, along the centrelines."""
        traces = []
        for index, strand in enumerate(self.strands):
            x, y, z = zip(*strand.sample(n_sample))
            traces.append(
                go.Scatter3d(
                    x=x,
                    y=y,
                    z=z,
                    mode="lines",
                    line=dict(width=line_width, color=self._colour(index, colors)),
                    name=self._name(index, names),
                    legendgroup=self._name(index, names),
                    hoverinfo="name",
                )
            )
        return traces

    def figure(
        self,
        n_sample: StrictlyPositiveInt = 200,
        title: str = "",
        tube_diameter: Optional[float] = None,
        n_around: int = 16,
        opacity: float = 0.55,
        colors: Optional[Sequence[str]] = None,
        names: Optional[Sequence[str]] = None,
        line_width: float = 10,
        z_title: str = "Z (time)",
        flip_z: bool = True,
    ) -> go.Figure:
        """The braid as a Plotly figure, drawn but neither shown nor written.

        Given ``tube_diameter``, the strands are drawn at their real
        thickness instead of as lines.  That is worth the extra cost when the
        point is how the strands *fit*: a line drawing shows where the centres
        go and leaves whether the yarn touches or overlaps to be taken on
        trust.  The tubes are semi-transparent so the far side of a rope is
        not simply hidden behind the near one.

        Args:
            n_sample: Points sampled along each strand.
            title: Figure title.
            tube_diameter: Draw the strands this thick, rather than as lines.
            n_around: Points round each tube, when drawing them.
            opacity: How far through a tube the one behind shows.
            colors: One colour per strand, cycled; the terminal colours if None.
            names: One legend name per strand; "Strand i" if None.
            line_width: Width of the lines, when not drawing tubes.
            z_title: Title of the z axis.
            flip_z: Run z downward, as time does in a braid diagram.  A braid
                whose z is a height, such as one coming off a machine, wants
                it upright instead.

        Returns:
            The figure.
        """
        traces = (
            self._line_traces(n_sample, colors, names, line_width)
            if tube_diameter is None
            else self._tube_traces(
                tube_diameter, n_sample, n_around, opacity, colors, names
            )
        )
        heights = [
            point[2] for strand in self.strands for point in strand.sample(n_sample)
        ]

        figure = go.Figure(data=traces)
        figure.update_layout(
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title=z_title,
                zaxis=dict(range=[max(heights), min(heights)])  # Flip Z axis
                if flip_z
                else dict(),
                aspectmode="data",
            ),
            margin=dict(l=0, r=0, b=0, t=30 if title else 0),
            showlegend=True,
            title=title,
        )
        return figure

    def plot(
        self,
        n_sample: StrictlyPositiveInt = 200,
        plotter: Plotter = Plotter.PLOTLY,
        output_html: Optional[str] = None,
        title: str = "",
        tube_diameter: Optional[float] = None,
        n_around: int = 16,
        opacity: float = 0.55,
    ) -> "ParametricBraid":
        """
        Plot the braid in 3D

        Args:
            n_sample: Points sampled along each strand.
            plotter: Which backend to draw with.
            output_html: If given, write the figure to this path instead of
                showing it.  Plotly only.
            title: Figure title, for a written page that has to say what it is.
            tube_diameter: Draw the strands at this thickness rather than as
                lines — see :meth:`figure`.  Plotly only.
            n_around: Points round each tube, when drawing them.
            opacity: How far through a tube the one behind shows.

        Returns:
            ParametricBraid: the braid itself
        """
        if plotter == Plotter.MATPLOTLIB:
            fig = plt.figure()
            ax = cast("Axes3D", fig.add_subplot(111, projection="3d"))
            for i, strand in enumerate(self.strands):
                path = strand.sample(n_sample)
                x, y, z = zip(*path)
                color = terminal_colors[i % len(terminal_colors)]
                ax.plot(x, y, z, linewidth=10, color=color)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_zlabel("Z (time)")
            ax.set_aspect("equal", "box")
            plt.tight_layout()
            plt.show()
        elif plotter == Plotter.PLOTLY:
            fig = self.figure(
                n_sample=n_sample,
                title=title,
                tube_diameter=tube_diameter,
                n_around=n_around,
                opacity=opacity,
            )
            if output_html:
                fig.write_html(output_html)
            else:
                fig.show()

        # Return to avoid plotting and saving
        return self


def closest_approach(
    strands: Sequence,
    n_samples: int = 600,
    span: float = 1.0,
    against: Optional[Sequence[int]] = None,
) -> float:
    """The nearest the centres of two different strands come to each other.

    Strands of diameter ``d`` may not come closer than ``d``.  Nothing in a
    drawing enforces that, so it has to be measured — and a shape that fails
    here is not a braid however pretty.  Works on anything that answers
    ``position(z)`` over a known ``length``, whoever produced it.

    Every pair of *heights* is compared, not only equal ones.  Comparing
    strands at the same height is much cheaper and is wrong: two strands that
    wind round each other pass closest at *different* heights, and on a
    three-strand rope laid one turn per period the equal-height figure
    overstates the clearance by a third.  A strand is followed over
    ``span`` periods either side of the other's, which is ample — the
    distance between two points is at least their difference in height, so a
    neighbour further away than that in ``z`` cannot be the nearest.

    Args:
        strands: The strands to compare.
        n_samples: Points sampled along a period.  The measurement is a
            minimum over samples, so it converges from above.
        span: Periods to follow one strand either side of the other's.  The
            distance between two points is at least their difference in
            height, so a fraction of a period is enough whenever the strands
            are thin against the period — and much cheaper.
        against: Compare only these strands against all the others, rather
            than every pair.  For a braid with a symmetry that carries one
            strand onto another, most pairs are repeats of a few, and naming
            the few is the difference between a search that finishes and one
            that does not.  Comparing everything if left out.

    Returns:
        The smallest distance found; infinity if there are fewer than two
        strands.
    """
    if len(strands) < 2:
        return math.inf

    nearest = math.inf
    for first in range(len(strands)) if against is None else against:
        one = strands[first]
        here = np.array(
            [one.position(one.length * step / n_samples) for step in range(n_samples)]
        )
        for second in range(len(strands)):
            if second == first or (against is None and second < first):
                continue
            other = strands[second]
            reach = int(round((1 + 2 * span) * n_samples))
            there = np.array(
                [
                    other.position(
                        other.length * ((1 + 2 * span) * step / reach - span)
                    )
                    for step in range(reach)
                ]
            )
            gaps = np.linalg.norm(here[:, None, :] - there[None, :, :], axis=2)
            nearest = min(nearest, float(gaps.min()))
    return nearest
