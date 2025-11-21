"""
mobidai.py

A simulator for the traditional Japanese braiding stand (Marudai / Mobidai).
Sometimes known as friendship disk and used for kumihimo braiding.

This module provides classes to model, simulate, and visualize the braiding
process, based on configurations of slots, strands, and moves. It also
includes topological tracking to extract the Artin Braid Group word
associated with the braiding moves.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
import matplotlib.pyplot as plt
import numpy as np


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------


class SlotAlreadyInUseError(Exception):
    """Exception raised when attempting to move a strand to an occupied slot."""

    ...


@dataclass
class Strand:
    """Represents a strand placed on a mobidai slot.

    Attributes:
        color (str): The color of the strand (format as supported by matplotlib).
        position (int): The slot number (1-indexed) where the strand currently sits.
        id (int): A unique identifier for the strand to track it topologically.
                  Defaults to -1 (assigned during initialization).
    """

    color: str
    position: int
    id: int = -1


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
        n_shift_after_cycle (int): Number of slots to rotate between cycles to
            come back to strands positions similar to initial positions.
        n_slots (int): Total number of slots on the mobidai disk. Defaults to 32.
        is_clockwise (bool): Direction of rotation for numbering (True = clockwise).
            Defaults to True.
    """

    strands: List[Strand]
    moves: List[Move]
    n_shift_after_cycle: int
    n_slots: int = 32
    is_clockwise: bool = True


# ---------------------------------------------------------------------------
# Braid Topology Logic
# ---------------------------------------------------------------------------


class BraidTracker:
    """Tracks the topological state of the strands to generate Artin words.

    This class maintains the 'linear order' of strands. When a strand moves physically
    on the disk, this tracker determines which strands it crosses over and generates
    the corresponding Artin generators (σ_i or σ_i^-1).

    Attributes:
        linear_order (List[int]): A list of Strand IDs representing their current
            order from 'left' to 'right' (or counter-clockwise to clockwise).
        strand_map (Dict[int, Strand]): Reference to the actual strand objects.
    """

    def __init__(self, strands: List[Strand], n_slots: int):
        """Initializes the BraidTracker.

        Args:
            strands (List[Strand]): The list of strands involved in the braid.
            n_slots (int): Total slots on the disk (used for sorting).
        """
        self.strand_map = {s.id: s for s in strands}
        # Sort strands by their initial position to establish the baseline linear order (1..N)
        self.linear_order = sorted(
            [s.id for s in strands], key=lambda sid: self.strand_map[sid].position
        )

    def get_generators_for_move(self, move: Move, n_slots: int) -> str:
        """Calculates the Artin generators for a specific move.

        Assumes the standard Marudai physics where the moving strand is lifted
        UP and passes OVER any intervening strands.

        Args:
            move (Move): The move being performed.
            n_slots (int): Total number of slots (to calculate direction).

        Returns:
            str: A space-separated string of generators (e.g., "s1 s2" or "s3^-1").
                 Returns an empty string if no crossings occur.
        """
        # 1. Identify the moving strand
        moving_strand = None
        for s in self.strand_map.values():
            if s.position == move.from_slot:
                moving_strand = s
                break

        if not moving_strand:
            return ""

        # 2. Determine Direction and Path
        # Calculate distance Clockwise
        diff = (move.to_slot - move.from_slot) % n_slots
        is_clockwise = diff <= (n_slots // 2)

        steps = diff if is_clockwise else (n_slots - diff)
        direction = 1 if is_clockwise else -1

        # 3. Find all strands physically located in the path
        crossed_strand_ids = []
        current_check = move.from_slot

        for _ in range(steps):
            # Move one slot in the direction
            current_check = ((current_check + direction - 1) % n_slots) + 1

            # Check if a strand exists at this slot
            for s in self.strand_map.values():
                if s.position == current_check and s.id != moving_strand.id:
                    crossed_strand_ids.append(s.id)

        if not crossed_strand_ids:
            return ""

        # 4. Generate Words and Update Linear Order
        generators = []

        for crossed_id in crossed_strand_ids:
            # Find current topological ranks (0-indexed index in linear_order list)
            idx_moving = self.linear_order.index(moving_strand.id)
            idx_stationary = self.linear_order.index(crossed_id)

            # The Artin generator index 'k' is 1-indexed, based on the leftmost strand involved
            k = min(idx_moving, idx_stationary) + 1

            if is_clockwise:
                # Moving Left -> Right (Rank i -> i+1). Crossing OVER.
                # This is the positive generator σ_k
                gen = f"s{k}"
            else:
                # Moving Right -> Left (Rank i+1 -> i). Crossing OVER.
                # A right-strand crossing over a left-strand is the inverse σ_k^-1
                gen = f"s{k}^-1"

            generators.append(gen)

            # CRITICAL: Update the linear order to reflect the swap
            # The strands have topologically exchanged places.
            self.linear_order[idx_moving], self.linear_order[idx_stationary] = (
                self.linear_order[idx_stationary],
                self.linear_order[idx_moving],
            )

        return " ".join(generators)


# ---------------------------------------------------------------------------
# Mobidai Simulation
# ---------------------------------------------------------------------------


class Mobidai:
    """Simulates a mobidai braiding process and tracks braid words.

    Attributes:
        config (MobidaiConfig): Configuration object for this mobidai.
        slots (Dict[int, Optional[Strand]]): Dictionary mapping slot number to strand.
        braid_word (List[str]): The accumulated sequence of Artin generators.
    """

    def __init__(self, config: MobidaiConfig):
        """Initializes the mobidai simulation.

        Assigns unique IDs to strands if they don't have them, sets up slots,
        and initializes the topological BraidTracker.

        Args:
            config (MobidaiConfig): The mobidai configuration.

        Raises:
            ValueError: If a slot is double-booked in the initial config.
        """
        self.n_total_shift = 0
        self.config = config
        self.slots: Dict[int, Strand | None] = {
            i: None for i in range(1, config.n_slots + 1)
        }

        # Re-initialize strands with unique IDs for tracking
        new_strands = []
        for i, s in enumerate(config.strands):
            # Create new instance to avoid mutating the passed config directly
            # Assign ID 'i'
            new_s = Strand(s.color, s.position, id=i)
            new_strands.append(new_s)

            if new_s.position in self.slots:
                self.slots[new_s.position] = new_s
            else:
                raise ValueError(
                    f"Invalid slot {new_s.position} for strand {new_s.color}"
                )

        # Update config to use the ID-aware strands
        self.config.strands = new_strands

        # Initialize Braid Word logic
        self.braid_tracker = BraidTracker(self.config.strands, self.config.n_slots)
        self.braid_word: List[str] = []

    # ---------------------------------------------------------------------

    def rotate(self, steps: int):
        """Rotates all strands by a given number of slots.

        Does not generate braid words as rotation is a change of reference frame,
        not a crossing of strands.

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

    def single_step(
        self, move: Move, slots: Dict[int, Optional[Strand]]
    ) -> Dict[int, Optional[Strand]]:
        """Performs one step of the braiding moves and extracts generators.

        Args:
            move (Move): The move to perform.
            slots (Dict): Current snapshot of the slots.

        Returns:
            Dict: Updated snapshot of the slots.

        Raises:
            SlotAlreadyInUseError: If the target slot is occupied.
        """
        strand = slots.get(move.from_slot)
        if strand:
            if slots.get(move.to_slot) is not None:
                raise SlotAlreadyInUseError(
                    f"Slot {move.to_slot} already occupied during move."
                )

            # --- Braid Extraction Start ---
            # Calculate generators before physical update, but knowing the path
            generators = self.braid_tracker.get_generators_for_move(
                move, self.config.n_slots
            )
            if generators:
                self.braid_word.append(generators)
            # --- Braid Extraction End ---

            # Move the strand physically
            slots[move.from_slot] = None
            strand.position = move.to_slot
            slots[move.to_slot] = strand

        return slots

    def all_steps(self):
        """Performs one round of the braiding moves.

        Iterates through all configured moves, updates the braid word,
        and finally performs the rotation step.
        """
        # Use self.slots directly to maintain state
        for move in self.config.moves:
            self.slots = self.single_step(move, self.slots)

        self.rotate(self.config.n_shift_after_cycle)

    # ---------------------------------------------------------------------

    def visualize(self, ax=None, shift_back_to_initial_position: bool = False):
        """Visualizes the current state of the mobidai.

        Args:
            ax (matplotlib.axes.Axes, optional): Axis to draw on. Creates one if None.
            shift_back_to_initial_position (bool, optional): If True, rotates the
                visualization counter to the total shift, making the strands appear
                stationary relative to the viewer. Defaults to False.
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
    # Using the simpler example to easily verify braid words
    print("--- Simulating Braiding and Extracting Artin Words ---")

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

    print("Initial State:")
    mobidai.visualize(shift_back_to_initial_position=False)

    # Run cycles
    for i in range(3):
        mobidai.all_steps()
        print(f"\nCycle {i + 1} complete.")
        mobidai.visualize(shift_back_to_initial_position=False)

    print("\n" + "=" * 50)
    print("EXTRACTED ARTIN BRAID WORD:")
    print("=" * 50)
    # Join the list of strings into one long formula
    full_word = " ".join(mobidai.braid_word)
    print(full_word)
    print("=" * 50)
