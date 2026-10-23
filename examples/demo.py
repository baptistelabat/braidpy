from braidpy import Braid
from braidpy.parametric_braid import (
    ParametricBraid,
)

# Create a braid using list of Artin's generator
b = Braid([1, 2, -1])

# Display the corresponding braid word. You should get the notation as used by Artin 'σ₁σ₂σ₁⁻¹'.
b.format()

# Display using other common notation. You should get 'abA'.
b.format_to_notation(target="alpha")

# Draw the braid in console. Alternatively use result.plot() for more advanced 2D plot.
b.draw()

# Perform operations. See documentation for much more features !
result = b * b.inverse()

# Draw the resulting braid in console.
result.draw()

# Plot the resulting braid.
result.plot()

# Convert to parametric braid before ploting in 3D.
strands = result.to_parametric_strands()


p = ParametricBraid(strands)  # .plot()
p.plot()
