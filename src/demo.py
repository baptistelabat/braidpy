from braidpy import Braid
from braidpy.parametric_braid import (
    ParametricBraid,
)

b = Braid((1, -2), n_strands=3)
b.draw()
b.plot()
strands = (b**12).to_parametric_strands()
p = ParametricBraid(strands)  # .plot()
p.plot()
