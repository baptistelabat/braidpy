from braidpy import Braid
from braidpy.parametric_braid import braid_to_parametric_strands, ParametricBraid

b = Braid((1, 0, 0, -2), n_strands=3)
strands = braid_to_parametric_strands(b)
p = ParametricBraid(strands)  # .plot()
assert p.get_positions_at(0.5) == [
    (0.2, 0.0, 0.5),
    (0.0, 0.0, 0.5),
    (0.4, 0.0, 0.5),
]

p.plot()
