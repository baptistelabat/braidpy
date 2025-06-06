# Visualizing braids

The followign code present the different visualizations
```python
from braidpy import Braid
from braidpy.parametric_braid import braid_to_parametric_strands, ParametricBraid
import matplotlib
matplotlib.use("QtAgg")
b = Braid((1, -2), n_strands=3)
b.draw()
b.plot()
strands = braid_to_parametric_strands(b**12)
p = ParametricBraid(strands)  # .plot()
p.plot()
```

The tirst basic visualization enables to draw a braid diagram directly in the console, with some colors !

[![colored ASCII braid example](draw_colored_ASCII_braid.png)]

The second type of visualization enables to plot a 2D braid diagram using matplotlib:

```python
b.plot()
```

The third level is 3D visualization. You first need to convert your braidword to a parametric braid.
Then you can plot the parametric braid using either matplotlib or plotly:

[![3D braid example](3D_braid_example.png)]
[![3D braid example plotly](3D_braid_example_plotly.png)]
