import pytest
import matplotlib.pyplot as plt
from braidpy import Braid
from braidpy.visualization import plot_braid
import matplotlib

# Run tests with: uv run pytest /tests


class TestVisualization:
    def test_plot_braid(self, simple_braid):
        plot_braid(simple_braid)

