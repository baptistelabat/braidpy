"""
mobidai.py

A simulator for the traditional Japanese braiding stand (Marudai / Mobidai).
Sometimes known as friendship disk and used for kumihimo braiding.

This module provides classes to model, simulate, and visualize the braiding
process, based on configurations of slots, strands, and moves.

"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


class SlotAlreadyInUseError(Exception): ...


@dataclass
class Strand:
    """Represents a strand placed on a mobidai slot.

    Attributes:
        color (str): The color of the strand (format as supported by matplotlib)
        position (int): The slot number (1-indexed) where the strand currently sits.
    """

    color: str
    position: int


@dataclass
class Move:
    """Represents one strand move from one slot to another.

    Attributes:
        from_slot (int): The slot number where the strand starts.
        to_slot (int): The slot number where the strand will be placed.
    """

    from_slot: int
    to_slot: int


@dataclass
class MobidaiConfig:
    """Configuration of a mobidai setup.

    Attributes:
        strands (List[Strand]): Initial list of strands on slots.
        moves (List[Move]): Sequence of moves performed in one braiding cycle.
        n_shift_after_cycle (int): Number of slots to rotate between cycles to come back to strands positions similar to initial positions (permutation only)
        n_slots (int): Total number of slots on the mobidai disk. Default to 32
        is_clockwise (bool): Direction of rotation for numbering (True = clockwise).

    """

    strands: List[Strand]
    moves: List[Move]
    n_shift_after_cycle: int
    n_slots: int = 32
    is_clockwise: bool = True


# ---------------------------------------------------------------------------
# Mobidai Simulation
# ---------------------------------------------------------------------------


class Mobidai:
    """Simulates a mobidai braiding process.

    Attributes:
        config (MobidaiConfig): Configuration object for this mobidai.
        slots (Dict[int, Optional[Strand]]): Dictionary mapping slot number to strand.
    """

    def __init__(self, config: MobidaiConfig):
        """Initializes the mobidai simulation.

        Args:
            config (MobidaiConfig): The mobidai configuration.
        """
        self.n_total_shift = 0
        self.config = config
        self.slots: Dict[int, Strand | None] = {
            i: None for i in range(1, config.n_slots + 1)
        }
        for strand in config.strands:
            if strand.position in self.slots:
                self.slots[strand.position] = strand
            else:
                raise ValueError(
                    f"Invalid slot {strand.position} for strand {strand.color}"
                )

    # ---------------------------------------------------------------------

    def rotate(self, steps: int):
        """Rotates all strands by a given number of slots.

        Args:
            steps (int): Number of slots to rotate. Positive for clockwise.
        """
        n = self.config.n_slots
        new_slots: Dict[int, Optional[Strand]] = {i: None for i in range(1, n + 1)}

        for slot, strand in self.slots.items():
            if strand:
                new_absolute_position = ((slot - 1 + steps) % n) + 1
                strand.position = new_absolute_position
                new_slots[new_absolute_position] = strand

        self.slots = new_slots
        self.n_total_shift += steps

    # ---------------------------------------------------------------------

    @staticmethod
    def single_step(move: Move, slots):
        """Performs one step of the braiding moves."""
        strand = slots.get(move.from_slot)
        if strand:
            if slots.get(move.to_slot) is not None:
                raise SlotAlreadyInUseError(
                    f"Slot {move.to_slot} already occupied during move."
                )
            # Move the strand
            slots[move.from_slot] = None
            strand.position = move.to_slot
            slots[move.to_slot] = strand
        return slots

    def all_steps(self):
        """Performs one round of the braiding moves."""
        new_slots: Dict[int, Optional[Strand]] = self.slots.copy()

        for move in self.config.moves:
            new_slots = self.single_step(move, new_slots)

        self.slots = new_slots

        self.rotate(self.config.n_shift_after_cycle)

    # ---------------------------------------------------------------------

    def visualize(self, ax=None, shift_back_to_initial_position: bool = False):
        """Visualizes the current state of the mobidai.

        Args:
            ax (matplotlib.axes.Axes, optional): Axis to draw on. Creates one if None.
        """
        n = self.config.n_slots
        if ax is None:
            fig, ax = plt.subplots(figsize=(6, 6))
        ax.set_aspect("equal")
        ax.axis("off")

        r_outer = 1.0
        theta = np.linspace(0, 2 * np.pi, n + 1)
        ax.plot(r_outer * np.cos(theta), r_outer * np.sin(theta), "k-", lw=1)

        for slot in range(1, n + 1):
            angle = (
                2
                * np.pi
                * (
                    slot
                    - 1
                    - self.n_total_shift * int(not (shift_back_to_initial_position))
                )
                / n
                * (int(self.config.is_clockwise) * 2 - 1)
            )
            x = r_outer * np.sin(angle)
            y = r_outer * np.cos(angle)
            strand = self.slots.get(slot)
            color = strand.color if strand else "white"
            ax.plot(x, y, "o", color=color, markersize=12, markeredgecolor="black")
            ax.text(x * 1.15, y * 1.15, str(slot), ha="center", va="center", fontsize=8)

        plt.show()

    # ---------------------------------------------------------------------

    def simulate(self, steps: int, visualize_each: bool = False):
        """Runs multiple braiding steps.

        Args:
            steps (int): Number of steps to simulate.
            visualize_each (bool, optional): Whether to show each step. Defaults to False.
        """
        for _ in range(steps):
            self.all_steps()
            if visualize_each:
                self.visualize()
                plt.show()


# ---------------------------------------------------------------------------
# Example usage
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Typical moves described in books
    config = MobidaiConfig(
        n_slots=32,
        is_clockwise=True,
        strands=[
            Strand("red", 32),
            Strand("red", 1),
            Strand("red", 17),
            Strand("red", 16),
            Strand("green", 25),
            Strand("green", 24),
            Strand("green", 8),
            Strand("green", 9),
        ],
        moves=[
            Move(a, b)
            for a, b in [
                (1, 15),
                (17, 31),
                (25, 7),
                (9, 23),
                (16, 30),
                (32, 14),
                (8, 22),
                (24, 6),
            ]
        ],
        n_shift_after_cycle=2,
    )

    mobidai = Mobidai(config)
    mobidai.visualize(shift_back_to_initial_position=False)
    mobidai.all_steps()
    mobidai.visualize(shift_back_to_initial_position=False)
    mobidai.all_steps()
    mobidai.visualize(shift_back_to_initial_position=False)
    mobidai.all_steps()
    mobidai.visualize(shift_back_to_initial_position=False)

    # We can get the same braid using only half of the moves, then repeating them !
    config = MobidaiConfig(
        n_slots=32,
        is_clockwise=True,
        strands=[
            Strand("red", 32),
            Strand("red", 1),
            Strand("red", 17),
            Strand("red", 16),
            Strand("green", 25),
            Strand("green", 24),
            Strand("green", 8),
            Strand("green", 9),
        ],
        moves=[Move(a, b) for a, b in [(1, 15), (17, 31), (25, 7), (9, 23)]],
        n_shift_after_cycle=1,
    )

    mobidai = Mobidai(config)
    mobidai.visualize(shift_back_to_initial_position=False)
    mobidai.all_steps()
    mobidai.visualize(shift_back_to_initial_position=False)
    mobidai.all_steps()
    mobidai.visualize(shift_back_to_initial_position=False)
    mobidai.all_steps()
    mobidai.visualize(shift_back_to_initial_position=False)
