"""
kumihimo.py
============

Kumihimo simulator and visualizer.

Features:
- Simulates formal S/R sequences (swap, rotate)
- Tracks Artin braid word (σ generators)
- Produces a vertical timeline with labeled steps
- Displays step labels, strand IDs, and pattern info
"""

from typing import List
import matplotlib.pyplot as plt
import numpy as np


class Kumihimo:
    """Simulate and visualize Kumihimo braiding sequences with annotations.

    Attributes:
        n_strands (int): Number of strands (divisible by 4).
        k (int): Number of positions per quarter turn.
        state (List[int]): Current strand order around the disk.
        braid_word (List[str]): Sequence of Artin generators.
        history (List[str]): Record of performed S/R moves.
        frames (List[List[int]]): Strand configurations per step.
        angles (np.ndarray): Angular positions of strand slots.
        colors (np.ndarray): Color assigned to each strand.
        pattern (str): Original S/R pattern executed.
    """

    def __init__(self, n_strands: int = 8) -> None:
        """Initialize a Kumihimo simulation.

        Args:
            n_strands (int, optional): Number of strands. Must be divisible by 4.
                Defaults to 8.

        Raises:
            ValueError: If n is not divisible by 4.
        """
        if n_strands % 4 != 0:
            raise ValueError("n must be divisible by 4 (e.g. 8, 12, 16).")

        self.n: int = n_strands
        self.k: int = n_strands // 4
        self.state: List[int] = list(range(n_strands))
        self.braid_word: List[str] = []
        self.history: List[str] = []
        self.frames: List[List[int]] = [self.state.copy()]
        self.angles: np.ndarray = np.linspace(0, 2 * np.pi, n_strands, endpoint=False)
        self.colors: np.ndarray = plt.cm.hsv(np.linspace(0, 1, n_strands))
        self.pattern: str = ""

    # ----------------------------------------------------------------------
    # Core Operations
    # ----------------------------------------------------------------------

    def _swap_path(self, i: int, j: int) -> List[str]:
        """Compute Artin word for swapping two distant strands.

        Args:
            i (int): Index of the first strand.
            j (int): Index of the second strand.

        Returns:
            List[str]: List of σ generators representing the swap.
        """
        if i > j:
            i, j = j, i
        path: List[str] = [k + 1 for k in range(i, j)]
        path.extend(-(k + 1) for k in reversed(range(i, j - 1)))
        return path

    def swap_top_bottom(self) -> None:
        """Swap top and bottom strands.

        Returns:
            None
        """
        top, bottom = 0, self.n // 2
        self.braid_word.extend(self._swap_path(top, bottom))
        self.state[top], self.state[bottom] = self.state[bottom], self.state[top]
        self.history.append("S")
        self.frames.append(self.state.copy())

    def rotate(self, turns: int = 1) -> None:
        """Rotate the disk clockwise by quarter turns.

        Args:
            turns (int, optional): Number of 90° clockwise turns. Defaults to 1.
        """
        shift = self.k * turns
        self.state = [self.state[(i + shift) % self.n] for i in range(self.n)]
        for _ in range(shift):
            self.braid_word.extend([k + 1 for k in range(self.n - 1)])
        self.history.append(f"R**{turns}")
        self.frames.append(self.state.copy())

    # ----------------------------------------------------------------------
    # Driver
    # ----------------------------------------------------------------------

    def move(self, pattern: str) -> "Kumihimo":
        """Execute a sequence of S/R operations.

        Args:
            pattern (str): String of moves, e.g. "SRSRSR".

        Returns:
            Kumihimo: Self (for chaining).
        """
        self.pattern = pattern
        for step in pattern:
            if step == "S":
                self.swap_top_bottom()
            elif step == "R":
                self.rotate()
            else:
                raise ValueError(f"Invalid step: {step}")
        return self

    # ----------------------------------------------------------------------
    # Visualization
    # ----------------------------------------------------------------------

    def plot_timeline(
        self,
        step_width: float = 2.5,  # Use width instead of height
        show_ids: bool = True,
    ) -> None:
        """Plot the braid evolution as horizontally arranged disks.

        Args:
            step_width (float, optional): Horizontal spacing between steps.
                Defaults to 2.5
            show_ids (bool, optional): Whether to display strand indices.
                Defaults to True.
        """
        n_steps = len(self.frames)
        # Swap figsize dimensions for horizontal plot
        fig, ax = plt.subplots(figsize=(n_steps * step_width, 5))
        ax.set_aspect("equal")
        ax.axis("off")

        # draw each step
        for t, frame in enumerate(self.frames):
            # Calculate horizontal offset instead of vertical
            x_offset: float = t * step_width
            radius = 0.8 * step_width / 2

            # draw each strand as a radial line
            for i, strand in enumerate(frame):
                angle = self.angles[i]
                # x and y calculations remain relative to the disk center
                x, y = -np.sin(angle), np.cos(angle)
                color = self.colors[strand]
                ax.plot(
                    [x_offset, x_offset + radius * x],  # Add x_offset to x-coordinates
                    [0, radius * y],
                    color=color,
                    lw=2.3,
                    alpha=0.85,
                )

                # label strand IDs
                if show_ids:
                    ax.text(
                        x_offset + 1.15 * radius * x,
                        1.15 * radius * y,
                        f"{strand}",
                        color=color,
                        ha="center",
                        va="center",
                        fontsize=8,
                        alpha=0.9,
                    )

            # outer ring
            circle = plt.Circle((x_offset, 0), radius, color="gray", fill=False, lw=1)
            ax.add_artist(circle)

            # annotate the step type (Move to bottom for horizontal)
            if t < len(self.history):
                op = self.history[t]
                ax.text(
                    x_offset, -1.7, f"{op}", fontsize=9, fontweight="bold", ha="center"
                )

            # step index (Move to top for horizontal)
            ax.text(
                x_offset, 1.5, f"Step {t}", ha="center", fontsize=8, color="dimgray"
            )

        # title / legend
        ax.set_title(
            f"Kumihimo braid evolution\nPattern: {self.pattern}",
            fontsize=10,
            pad=20,
        )

        # Adjust limits to fit all elements
        x_min = -1
        x_max = n_steps * step_width
        y_min = -3
        y_max = 3
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)

        plt.tight_layout()
        plt.show()

    # ----------------------------------------------------------------------
    # Utilities
    # ----------------------------------------------------------------------

    def __repr__(self) -> str:
        """Return concise summary of current braid state."""
        return (
            f"<Kumihimo n={self.n}, steps={len(self.history)}, "
            f"pattern='{self.pattern}', braid='{self.braid_word}'>"
        )


if __name__ == "__main__":
    K = Kumihimo(n_strands=8)
    K.move("SRSRSRSR")
    print(K)
    print("Artin word:", K.braid_word)
    K.plot_timeline()
