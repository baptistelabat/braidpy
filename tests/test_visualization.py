from braidpy import Braid
from braidpy.visualization import plot_braid


# Run tests with: uv run pytest /tests

PLOT = False


class TestVisualization:
    def test_plot_braid(self, simple_braid):
        save = not (PLOT)
        complex_braid = Braid([1, 5, 10, -1, 0, 0, 7, -6])
        plot_braid(complex_braid, save=save)
        plot_braid(simple_braid, save=save)

        plot_braid(Braid([1, -2]) ** 20, save=save)
