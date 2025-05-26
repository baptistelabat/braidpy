from braidpy import Braid

# Run tests with: uv run pytest /tests

PLOT = False


class TestVisualization:
    def test_plot_braid(self, simple_braid):
        save = not (PLOT)
        complex_braid = Braid([1, 5, 10, -1, 0, 0, 7, -6])
        complex_braid.plot(save=save)
        (Braid([1, -2]) ** 20).plot(save=save)
