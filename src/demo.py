from braidpy import Braid
from braidpy.parametric_braid import braid_to_parametric_strands, ParametricBraid

b = Braid((1, -2), n_strands=3)
strands = braid_to_parametric_strands(b**12)
p = ParametricBraid(strands)  # .plot()
p.plot()
