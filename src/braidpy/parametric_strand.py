import math
from typing import Callable, List, Tuple

from braidpy.utils import StrictlyPositiveInt


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
