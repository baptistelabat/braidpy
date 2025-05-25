from typing import Callable, List
import math

import matplotlib.pyplot as plt

from braidpy import Braid


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

    def sample(self, n: int = 100) -> List[tuple]:
        """Return a list of sampled points for plotting"""
        return [self.evaluate(i / (n - 1)) for i in range(n)]

class ParametricBraid:
    def __init__(self, strands: list[ParametricStrand]):
        self.strands = strands
        self.n = len(strands)

    def get_positions_at(self, t: float):
        return [strand.evaluate(t) for strand in self.strands]

    def plot(self):

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        for strand in self.strands:
            path = strand.sample(200)
            x, y, z = zip(*path)
            ax.plot(x, y, z)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_zlabel("Z (time)")
        plt.tight_layout()
        plt.show()

def braid_to_parametric_strands(braid: Braid, amplitude=0.2, duration_per_gen=1.0):
    n = braid.n_strands or max(abs(g) for g in braid.generators) + 1
    x_positions = [i for i in range(n)]

    # For each strand, build a list of segment functions and their time ranges
    strand_segments = [[] for _ in range(n)]
    t0 = 0.0

    for g in braid.generators:
        i = abs(g) - 1
        over = g > 0
        t1 = t0 + duration_per_gen

        def make_segment(j, i=i, over=over, t0=t0, t1=t1):
            x0 = x_positions[j]
            if j == i:
                # First strand in crossing
                return lambda t: (
                    x0 + (x_positions[i+1] - x0) * ((t - t0) / (t1 - t0)),
                    (amplitude if over else -amplitude) * math.sin(math.pi * (t - t0) / (t1 - t0)),
                    t
                )
            elif j == i + 1:
                # Second strand in crossing
                return lambda t: (
                    x0 + (x_positions[i] - x0) * ((t - t0) / (t1 - t0)),
                    (-amplitude if over else amplitude) * math.sin(math.pi * (t - t0) / (t1 - t0)),
                    t
                )
            else:
                # Idle strand
                return lambda t: (x0, 0.0, t)

        for j in range(n):
            strand_segments[j].append((t0, t1, make_segment(j)))

        t0 = t1

    # Add final straight segment to z = t1 + 1
    t_final = t0 + duration_per_gen
    for j in range(n):
        xj = x_positions[j]
        strand_segments[j].append((t0, t_final, lambda t, xj=xj: (xj, 0.0, t)))

    # Compose each strand's segments into a single function
    def combine_segments(segments):
        def strand_func(t):
            for t_start, t_end, seg_func in segments:
                if t_start <= t <= t_end:
                    return seg_func(t)
            raise ValueError("t out of bounds")
        return strand_func

    return [ParametricStrand(combine_segments(segments)) for segments in strand_segments]