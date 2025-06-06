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

from typing import Callable, List, Tuple
import math

import matplotlib.pyplot as plt

from braidpy import Braid
from braidpy.utils import StrictlyPositiveInt, PositiveFloat, terminal_colors


class ParametricStrand:
    def __init__(self, func: Callable[[float], tuple]) -> None:
        """

        Args:
            func(Callable[[float], tuple]): a function γ(t) : [0,1] → ℝ³
        """
        self.func = func

    def evaluate(self, t: float) -> tuple[float, float, float]:
        """
        Compute the strand position at time t (along z axis)
        Args:
            t: time or z coordinates

        Returns:
            tuple[float, float, float]: position of braid [x(t), y(t), t]
        """
        if t < 0 or t > 1:
            raise ValueError("t must be in [0, 1]")
        return self.func(t)

    def sample(self, n: StrictlyPositiveInt = 100) -> List[tuple]:
        """
        Return a list of sampled points for plotting

        Args:
            n(StrictlyPositiveInt): number of samples

        Returns:
            List[tuple]: list of 3D coordinates
        """
        return [self.evaluate(i / (n - 1)) for i in range(n)]


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

    def plot(self, n_sample: StrictlyPositiveInt = 200) -> "ParametricBraid":
        """
        Plot the braid in 3D

        Args:
            n_sample:

        Returns:
            ParametricBraid: the braid itself
        """
        plotter = "plotly"
        if plotter == "matplotlib":
            fig = plt.figure()
            ax = fig.add_subplot(111, projection="3d")
            for strand in self.strands:
                path = strand.sample(n_sample)
                x, y, z = zip(*path)
                ax.plot(x, y, z, linewidth=10)
            ax.set_xlabel("X")
            ax.set_ylabel("Y")
            ax.set_zlabel("Z (time)")
            ax.set_aspect("equal", "box")
            plt.tight_layout()
            plt.show()
        else:
            import plotly.graph_objects as go

            fig = go.Figure()

            for i, strand in enumerate(self.strands):
                path = strand.sample(n_sample)
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
                    aspectmode="data",
                ),
                margin=dict(l=0, r=0, b=0, t=0),
                showlegend=True,
            )

            fig.show()

        # Return to avoid plotting and saving
        return self


# Type alias for an arc of a strand: a time interval and a 3D path function over that interval
Arc = Tuple[float, float, Callable[[float], Tuple[float, float, float]]]


def make_arc(
    x_start: float, x_end: float, t_start: float, t_end: float, amplitude: float
) -> Callable[[float], Tuple[float, float, float]]:
    """
    Creates a sine-arc parametric function between two x-positions.

    Args:
        x_start(float): Starting x position.
        x_end(float): Ending x position.
        t_start(float): Start time.
        t_end(float): End time.
        amplitude(float): Amplitude of the sine wave in the y-direction.

    Returns:
        A function that maps time t to a 3D point (x, y, z).
    """

    def arc(t: float) -> Tuple[float, float, float]:
        progress = (t - t_start) / (t_end - t_start)
        x = x_start + (x_end - x_start) * progress
        y = amplitude * math.sin(math.pi * progress)
        return x, y, t

    return arc


def make_idle_arc(
    x: float, t_start: float, t_end: float
) -> Callable[[float], Tuple[float, float, float]]:
    """
    Creates a straight-line parametric function for idle strands.

    Args:
        x: Fixed x position.
        t_start: Start time.
        t_end: End time.

    Returns:
        A function that maps time t to a 3D point (x, 0.0, z).
    """

    def arc(t: float) -> Tuple[float, float, float]:
        return x, 0.0, t

    return arc


def combine_arcs(arcs: List[Arc]) -> Callable[[float], Tuple[float, float, float]]:
    """
    Combines a list of arcs into a single time-dependent function.

    Args:
        arcs: A list of arcs represented as (t_start, t_end, function).

    Returns:
        A function from t to (x, y, z), switching arcs over time.
    """

    def strand_func(t: float) -> Tuple[float, float, float]:
        for t0, t1, arc in arcs:
            if t0 <= t <= t1:
                return arc(t)
        raise ValueError(f"Time {t} is out of bounds for this strand.")

    return strand_func


def braid_to_parametric_strands(
    braid: Braid, amplitude: float = 0.2
) -> List[ParametricStrand]:
    """
    Converts a braid into a list of 3D parametric strand paths.

    Args:
        braid: The Braid object containing crossing generators.
        amplitude: Height of the sine wave for over/under crossings.

    Returns:
        A list of ParametricStrand objects representing the strands.
    """
    n_strands = braid.n_strands or max(abs(g) for g in braid.generators) + 1
    n_segments = len(braid.generators) + 1
    duration_per_gen = 1 / n_segments

    # Track strand positions across braid steps
    positions = list(range(n_strands))
    position_history = [positions.copy()]

    for gen in braid.generators:
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
            gen = braid.generators[k]
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

    return [ParametricStrand(combine_arcs(strand)) for strand in strand_arc_sequences]
