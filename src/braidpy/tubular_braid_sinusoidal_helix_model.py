# See page 19 in https://scispace.com/pdf/the-geometry-of-tubular-braided-structures-32b4yiwio2.pdf
import numpy as np


def tubular_braid(
    theta: float, r1: float = 1, q1: float = 1, r: float = 0, n_strands: int = 4
):
    """
    According to reference page 20

    Args:
        theta(float): angle (rad)
        r1:
        q1:
        r:
        n_strands:

    Returns:

    """
    r0 = 1 + r * np.sin(n_strands * theta / 2)
    x = r0 * np.cos(theta)
    y = r0 * np.sin(theta)
    z = r1 * theta * np.cotan(q1)
    return (x, y, z)
