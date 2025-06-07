from braidpy import Braid
from braidpy.handles_reduction import dehornoy_reduce_core
from braidpy.parametric_braid import (
    ParametricBraid,
)

b = Braid((1, 2, 3, 1, 2, 4, -4, -2, -1, -3, -2, -1), n_strands=5)
b.draw()
gen, sign = dehornoy_reduce_core(b.generators)
print()
Braid(gen).draw()
(b**10).draw()
b.plot()
strands = (b**12).to_parametric_strands()
p = ParametricBraid(strands)  # .plot()
# p.plot()
