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

from enum import Enum
from typing import List, Tuple

import matplotlib.pyplot as plt

from braidpy.parametric_strand import ParametricStrand
from braidpy.utils import StrictlyPositiveInt, PositiveFloat, terminal_colors

import plotly.graph_objects as go


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

    def plot(
        self, n_sample: StrictlyPositiveInt = 200, plotter: Plotter = Plotter.PLOTLY
    ) -> "ParametricBraid":
        """
        Plot the braid in 3D

        Args:
            n_sample:

        Returns:
            ParametricBraid: the braid itself
        """
        if plotter == Plotter.MATPLOTLIB:
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
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
            fig = go.Figure()

            # First pass to compute global z-range
            all_paths = []
            z_min, z_max = float("inf"), float("-inf")

            for strand in self.strands:
                path = strand.sample(n_sample)
                z_vals = [pt[2] for pt in path]
                z_min = min(z_min, min(z_vals))
                z_max = max(z_max, max(z_vals))
                all_paths.append(path)

            for i, path in enumerate(all_paths):
                x, y, z = zip(*path)

                color = terminal_colors[i % len(terminal_colors)]

                fig.add_trace(
                    go.Scatter3d(
                        x=x,
                        y=y,
                        z=z,
                        mode="lines",
                        line=dict(width=10, color=color),
                        name=f"Strand {i}",
                        hoverinfo="name",
                    )
                )

            fig.update_layout(
                scene=dict(
                    xaxis_title="X",
                    yaxis_title="Y",
                    zaxis_title="Z (time)",
                    zaxis=dict(range=[z_max, z_min]),  # Flip Z axis
                    aspectmode="data",
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                showlegend=True,
            )

            fig.show()

        # Return to avoid plotting and saving
        return self
