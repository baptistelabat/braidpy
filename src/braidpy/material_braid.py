import numpy as np
from braidpy.parametric_braid import ParametricStrand


class MaterialStrand(ParametricStrand):
    def __init__(self, path_points, radius=0.05):
        """
        radius: physical thickness of the strand
        """
        super().__init__(path_points)
        self.radius = radius


class MaterialBraid:
    def __init__(self, strands):
        """
        strands: list of MaterialStrand objects
        """
        self.strands = strands
        self.n = len(strands)
        self._check_nonintersecting()

    def _check_nonintersecting(self, min_clearance=1e-3):
        """
        Checks that strands do not intersect or overlap.
        """
        for i in range(self.n):
            for j in range(i + 1, self.n):
                if self._are_too_close(self.strands[i], self.strands[j], min_clearance):
                    raise ValueError(f"Strands {i} and {j} intersect or are too close.")

    @staticmethod
    def are_too_close(s1, s2, clearance=1e-3, samples=100):
        """
        Checks if two ParametricStrand objects are too close at any point in time.

        Args:
            s1, s2: ParametricStrand objects with .evaluate(t) and .radius
            clearance: minimum allowed distance between surfaces
            samples: number of time steps to check (default: 100)

        Returns:
            True if strands are too close; False otherwise.
        """
        ts = np.linspace(0, 1, samples)

        for t in ts:
            p1 = np.array(s1.evaluate(t))
            p2 = np.array(s2.evaluate(t))
            dist = np.linalg.norm(p1 - p2)
            if dist < s1.radius + s2.radius + clearance:
                return True
        return False
