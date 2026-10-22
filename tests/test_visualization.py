import matplotlib

matplotlib.use("Agg")

from braidpy import Braid  # noqa: E402

# Run tests with: uv run pytest /tests


class TestVisualization:
    def test_plot_braid(self, simple_braid, tmp_path):
        """The diagram draws, for a braid with gaps and for a long one.

        Written to tmp_path rather than the working directory: this test used
        to leave a test.svg in whatever directory it ran from.
        """
        import matplotlib.pyplot as plt

        complex_braid = Braid([1, 5, 10, -1, 0, 0, 7, -6])
        complex_braid.plot(save=str(tmp_path / "complex.png"))
        (Braid([1, -2]) ** 20).plot(save=str(tmp_path / "long.png"))
        assert (tmp_path / "complex.png").is_file()
        assert (tmp_path / "long.png").is_file()
        plt.close("all")
