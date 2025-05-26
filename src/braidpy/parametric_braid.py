from typing import Callable, List, Tuple
import math

import matplotlib.pyplot as plt

from braidpy import Braid
from braidpy.utils import StrictlyPositiveInt, PositiveFloat


class ParametricStrand:
    def __init__(self, func: Callable[[float], tuple]):
        """
        func: a function γ(t) : [0,1] → ℝ³
        """
        self.func = func

    def evaluate(self, t: float) -> tuple:
        """Returns the position γ(t)"""
        if t < 0 or t > 1:
            raise ValueError("t must be in [0, 1]")
        return self.func(t)

    def sample(self, n: StrictlyPositiveInt = 100) -> List[tuple]:
        """Return a list of sampled points for plotting"""
        return [self.evaluate(i / (n - 1)) for i in range(n)]


class ParametricBraid:
    def __init__(self, strands: list[ParametricStrand]):
        self.strands = strands
        self.n_strands = len(strands)

    def get_positions_at(self, t: PositiveFloat):
        return [strand.evaluate(t) for strand in self.strands]

    def plot(self, n_sample: StrictlyPositiveInt = 200):
        fig = plt.figure()
        ax = fig.add_subplot(111, projection="3d")
        for strand in self.strands:
            path = strand.sample(n_sample)
            x, y, z = zip(*path)
            ax.plot(x, y, z)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z (time)")
        plt.tight_layout()
        plt.show()

        # Return to avoid plotting and saving
        return self


# Type alias for an arc of a strand: a time interval and a 3D path function over that interval
Arc = Tuple[float, float, Callable[[float], Tuple[float, float, float]]]


def braid_to_parametric_strands(
    braid: Braid, amplitude: float = 0.2, duration_per_gen: float = 1.0
) -> List[ParametricStrand]:
    """
    Converts a braid into a list of 3D parametric strand paths.

    Each strand is returned as a function of time `t`, describing its (x, y, z)
    position over time as it weaves through crossings defined in the braid.

    Args:
        braid: The Braid object containing crossing generators.
        amplitude: Height of the sine wave used to visualize over/under crossings.
        duration_per_gen: The duration each generator (crossing) spans in time.

    Returns:
        A list of ParametricStrand instances, each representing a strand's 3D path.
    """
    # Determine number of strands
    n_strands: int = braid.n_strands or max(abs(g) for g in braid.generators) + 1
    x_positions: List[float] = list(range(n_strands))

    # Prepare arcs (segments) for each strand
    strand_arcs: List[List[Arc]] = [[] for _ in range(n_strands)]
    current_time: float = 0.0

    def make_crossing_arc(
        strand_idx: int, crossing_idx: int, over: bool, t_start: float, t_end: float
    ) -> Callable[[float], Tuple[float, float, float]]:
        """
        Generates the arc function for a strand involved in a crossing.
        """
        x0 = x_positions[strand_idx]
        delta_t = t_end - t_start

        if strand_idx == crossing_idx:
            # First strand in the crossing
            def arc(t: float) -> Tuple[float, float, float]:
                progress = (t - t_start) / delta_t
                x = x0 + (x_positions[crossing_idx + 1] - x0) * progress
                y = (amplitude if over else -amplitude) * math.sin(math.pi * progress)
                return (x, y, t)
        elif strand_idx == crossing_idx + 1:
            # Second strand in the crossing
            def arc(t: float) -> Tuple[float, float, float]:
                progress = (t - t_start) / delta_t
                x = x0 + (x_positions[crossing_idx] - x0) * progress
                y = (-amplitude if over else amplitude) * math.sin(math.pi * progress)
                return (x, y, t)
        else:
            # Strand not involved in crossing
            def arc(t: float) -> Tuple[float, float, float]:
                return (x0, 0.0, t)

        return arc

    # Generate arcs for each generator (crossing)
    for generator in braid.generators:
        crossing_idx = abs(generator) - 1
        over = generator > 0
        t_start = current_time
        t_end = t_start + duration_per_gen

        for strand_idx in range(n_strands):
            arc_func = make_crossing_arc(strand_idx, crossing_idx, over, t_start, t_end)
            strand_arcs[strand_idx].append((t_start, t_end, arc_func))

        current_time = t_end

    # Append final vertical arc (no crossing)
    final_time = current_time + duration_per_gen
    for strand_idx in range(n_strands):
        x = x_positions[strand_idx]

        def final_arc(t: float, x=x) -> Tuple[float, float, float]:
            return (x, 0.0, t)

        strand_arcs[strand_idx].append((current_time, final_time, final_arc))

    # Combine arcs into a complete strand function
    def combine_arcs(arcs: List[Arc]) -> Callable[[float], Tuple[float, float, float]]:
        def strand_function(t: float) -> Tuple[float, float, float]:
            for t_start, t_end, arc_func in arcs:
                if t_start <= t <= t_end:
                    return arc_func(t)
            raise ValueError("Time t is out of bounds for this strand.")

        return strand_function

    # Build final parametric strands
    return [ParametricStrand(combine_arcs(arcs)) for arcs in strand_arcs]
