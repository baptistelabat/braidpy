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
    # Optional: Force a direction if you want a "long way round" move
    # 1 = CW, -1 = CCW, 0 = Auto (Shortest Path)
    force_direction: int = 0


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

    def __init__(self, strands: List[Strand], n_slots: int, is_disk_clockwise: bool):
        """Initializes the BraidTracker.

        Args:
            strands (List[Strand]): The list of strands involved in the braid.
            n_slots (int): Total slots on the disk (used for sorting).
        """
        self.strand_map = {s.id: s for s in strands}
        self.n_slots = n_slots
        self.is_disk_clockwise = is_disk_clockwise

        # Initialize linear order based on current positions
        # We sort by position to get the 1..N topological order
        self.linear_order = sorted(
            [s.id for s in strands], key=lambda sid: self.strand_map[sid].position
        )

    def get_generators_for_move(self, move: Move) -> str:
        moving_strand = None
        for s in self.strand_map.values():
            if s.position == move.from_slot:
                moving_strand = s
                break

        if not moving_strand:
            return ""

        # 1. Determine Direction (CW or CCW)
        diff = (move.to_slot - move.from_slot) % self.n_slots

        # Determine if path is Clockwise (CW)
        if move.force_direction == 1:
            is_move_cw = True
        elif move.force_direction == -1:
            is_move_cw = False
        else:
            # Default: Shortest path
            is_move_cw = diff <= (self.n_slots // 2)

        # 2. Identify Strands in the Path
        # We iterate slot-by-slot from 'from' to 'to'
        steps = diff if is_move_cw else (self.n_slots - diff)
        direction_step = 1 if is_move_cw else -1

        crossed_strand_ids = []
        current_slot = move.from_slot

        for _ in range(steps):
            # Update slot check (Simulate walking along the rim)
            # Math: (current - 1 + direction) % n + 1 gives 1-based index wrap
            current_slot = ((current_slot + direction_step - 1) % self.n_slots) + 1

            # Ignore the target slot (it's where we place the strand, not cross it)
            # But strict checking: if strands are packed, we might cross a strand
            # just before placing it? Usually target is empty.
            if current_slot == move.to_slot:
                continue

            # Check for strands at this position
            for s in self.strand_map.values():
                if s.position == current_slot and s.id != moving_strand.id:
                    crossed_strand_ids.append(s.id)

        if not crossed_strand_ids:
            return ""

        # 3. Generate Artin Words
        generators = []

        for crossed_id in crossed_strand_ids:
            # Find current topological ranks (0-indexed index in linear_order list)
            idx_moving = self.linear_order.index(moving_strand.id)
            idx_stationary = self.linear_order.index(crossed_id)

            # Artin Index k is the minimum rank (Leftmost strand in the pair)
            k = min(idx_moving, idx_stationary) + 1

            # SIGN LOGIC:
            # If Disk is CW (1..N go Right):
            #    CW Move (Right) = Positive (s)
            #    CCW Move (Left) = Negative (s^-1)
            # If Disk is CCW (1..N go Left):
            #    CW Move (Right) = Moves AGAINST index = Negative (s^-1)
            #    CCW Move (Left) = Moves WITH index = Positive (s)

            if self.is_disk_clockwise:
                sign = "" if is_move_cw else "^-1"
            else:
                sign = "^-1" if is_move_cw else ""

            generators.append(f"s{k}{sign}")

            # Update Topology (Swap ranks)
            self.linear_order[idx_moving], self.linear_order[idx_stationary] = (
                self.linear_order[idx_stationary],
                self.linear_order[idx_moving],
            )

        return " ".join(generators)


# ---------------------------------------------------------------------------
# Mobidai Class Updates
# ---------------------------------------------------------------------------


class Mobidai:
    def __init__(self, config: MobidaiConfig):
        self.n_total_shift = 0
        self.config = config
        self.slots: Dict[int, Strand | None] = {
            i: None for i in range(1, config.n_slots + 1)
        }

        new_strands = []
        for i, s in enumerate(config.strands):
            new_s = Strand(s.color, s.position, id=i)
            new_strands.append(new_s)
            if new_s.position in self.slots:
                self.slots[new_s.position] = new_s
            else:
                raise ValueError(f"Invalid slot {new_s.position}")

        self.config.strands = new_strands

        # Pass 'is_clockwise' from config to Tracker to fix sign logic
        self.braid_tracker = BraidTracker(
            self.config.strands, self.config.n_slots, self.config.is_clockwise
        )
        self.braid_word: List[str] = []

    def single_step(
        self, move: Move, slots: Dict[int, Optional[Strand]]
    ) -> Dict[int, Optional[Strand]]:
        strand = slots.get(move.from_slot)
        if strand:
            if slots.get(move.to_slot) is not None:
                raise SlotAlreadyInUseError(f"Slot {move.to_slot} occupied.")

            # Extract Generators
            gens = self.braid_tracker.get_generators_for_move(move)
            if gens:
                self.braid_word.append(gens)

            # Physical Move
            slots[move.from_slot] = None
            strand.position = move.to_slot
            slots[move.to_slot] = strand

        return slots

    # ... rotate, all_steps, visualize, simulate remain the same ...
    def rotate(self, steps: int):
        n = self.config.n_slots
        new_slots = {i: None for i in range(1, n + 1)}
        for slot, strand in self.slots.items():
            if strand:
                new_pos = ((slot - 1 + steps) % n) + 1
                strand.position = new_pos
                new_slots[new_pos] = strand
        self.slots = new_slots
        self.n_total_shift += steps

    def all_steps(self):
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
            # Calculate angle
            shift = self.n_total_shift * int(not (shift_back_to_initial_position))
            direction = 1 if self.config.is_clockwise else -1
            # Angle starts at 0 (top usually) and rotates based on slot index
            angle = (2 * np.pi * (slot - 1 - shift) / n) * direction

            x = r_outer * np.sin(angle)
            y = r_outer * np.cos(angle)
            strand = self.slots.get(slot)
            color = strand.color if strand else "white"
            ax.plot(x, y, "o", color=color, markersize=12, markeredgecolor="black")
            ax.text(x * 1.15, y * 1.15, str(slot), ha="center", va="center", fontsize=8)
        plt.show()


# ---------------------------------------------------------------------------
# Example to Verify CCW/Backward Crossing
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
