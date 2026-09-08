# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/model.py
==================

Data model for a horn gear braiding machine.

A machine is a graph of HornGear nodes connected by Connection edges.

A connection is a fixed point in space where two gears touch.  Every step
each gear turns by one slot, so a different slot index arrives at that point
each time; a carrier transfers when its slot is the one that has arrived.
``Connection.slot_a0``/``slot_b0`` record which slot of each gear sits there
at t=0, and for the animation to be seamless those slots must also point at
the neighbour in the computed layout.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import networkx as nx


@dataclass(frozen=True)
class HornGear:
    """A single horn gear with N evenly-spaced slots.

    Args:
        name: Unique identifier for this gear.
        n_slots: Number of carrier slots (≥ 2).
        direction: +1 for counter-clockwise, -1 for clockwise rotation.
    """

    name: str
    n_slots: int
    direction: int = 1  # +1 CCW, -1 CW

    def __post_init__(self) -> None:
        if self.n_slots < 2:
            raise ValueError(f"Gear '{self.name}' must have at least 2 slots.")
        if self.direction not in (1, -1):
            raise ValueError(f"direction must be +1 or -1, got {self.direction}.")

    def slot_angle(self, slot: int, time: int = 0) -> float:
        """Absolute angle (radians) of a slot at a given simulation step.

        Args:
            slot: Slot index (0-based).
            time: Current step count.

        Returns:
            Angle in radians, measured CCW from the positive x-axis.
        """
        base_angle = 2 * math.pi * slot / self.n_slots
        rotation = 2 * math.pi * self.direction * time / self.n_slots
        return base_angle + rotation

    def slot_at_connection(self, slot0_at_t0: int, time: int) -> int:
        """Which slot of this gear is currently at the connection point
        whose slot index at t=0 was slot0_at_t0?

        Equivalently: at time t, the gear has rotated so that the slot
        originally at slot0_at_t0 is now at a new angular position.
        We want to know *which slot index is currently at the original
        angular position* (i.e. the fixed connection point in space).

        Connection points are fixed in space.  At t=0 slot ``slot0_at_t0``
        is at the connection angle.  After t steps the gear has rotated by
        ``direction * t`` slots, so the slot currently at that angle is:

            (slot0_at_t0 - direction * time) mod n_slots

        Args:
            slot0_at_t0: Slot index that was at the connection at t=0.
            time: Current step.

        Returns:
            Slot index currently at the connection point.
        """
        return (slot0_at_t0 - self.direction * time) % self.n_slots


@dataclass(frozen=True)
class Connection:
    """A transfer point between two gears.

    At each simulation step the slot of gear_a that is currently at the
    connection angle and the slot of gear_b that is currently at the
    connection angle are computed.  A carrier sitting in the gear_a slot
    transfers to gear_b (and vice-versa).

    Args:
        gear_a: Name of the first gear.
        gear_b: Name of the second gear.
        slot_a0: Slot index of gear_a at the connection point at t=0.
        slot_b0: Slot index of gear_b at the connection point at t=0.
        name: Optional label for this connection.
    """

    gear_a: str
    gear_b: str
    slot_a0: int
    slot_b0: int
    name: Optional[str] = None

    def slots_at(self, machine: "BraidingMachine", time: int) -> Tuple[int, int]:
        """Return the (slot_of_a, slot_of_b) currently at this connection.

        Args:
            machine: The machine containing gear definitions.
            time: Current step.

        Returns:
            Tuple (slot_in_a, slot_in_b) currently at the connection point.
        """
        gear_a = machine.gears[self.gear_a]
        gear_b = machine.gears[self.gear_b]
        sa = gear_a.slot_at_connection(self.slot_a0, time)
        sb = gear_b.slot_at_connection(self.slot_b0, time)
        return sa, sb


@dataclass(frozen=True)
class Axial:
    """A yarn fed straight down a fixed column, never carried by a gear.

    Braiding carriers travel around an axial; the axial itself does not move,
    holds no slot, and has no track.  It is therefore *not* a carrier and takes
    no part in stepping, tracks or collision detection — it is a fixed point
    that the braid forms around.

    The column stands at the centroid of the gears it is anchored to, which
    covers both ways a machine carries one:

    - ``anchor=("B",)`` — one gear, so the column is that gear's own centre,
      as an axial yarn fed up through a hollow horn gear spindle.  This is the
      0° reinforcement of a triaxial braid, and the cord of a soutache.
    - ``anchor=("A", "B", "C", "D")`` — the ring of gears around a hole, so the
      column is the centre of the tube they braid, as a rope core or a mandrel.
      :func:`~braidpy.horn_gear.layout.tube_rings` finds these rings for you.

    Args:
        name: Unique identifier for this axial.
        anchor: Names of the gears whose centroid the column stands at.
    """

    name: str
    anchor: Tuple[str, ...]


class BraidingMachine:
    """A complete horn-gear braiding machine described as a connection graph.

    Args:
        gears: List of HornGear instances.
        connections: List of Connection edges between gears.
        axials: Optional Axial columns the braid forms around.

    Attributes:
        gears: Dict mapping gear name → HornGear.
        connections: List of Connection instances.
        axials: List of Axial instances (empty for a machine without cores).
        graph: NetworkX graph of gear connections (for layout / analysis).
    """

    def __init__(
        self,
        gears: List[HornGear],
        connections: List[Connection],
        axials: Iterable[Axial] = (),
    ) -> None:
        self.gears: Dict[str, HornGear] = {g.name: g for g in gears}
        self.connections: List[Connection] = connections
        self.axials: List[Axial] = list(axials)
        self.graph: nx.Graph = self._build_graph()
        self._validate()

    def _build_graph(self) -> nx.Graph:
        g = nx.Graph()
        for gear in self.gears.values():
            g.add_node(gear.name, n_slots=gear.n_slots, direction=gear.direction)
        for conn in self.connections:
            label = conn.name or f"{conn.gear_a}-{conn.gear_b}"
            g.add_edge(
                conn.gear_a,
                conn.gear_b,
                slot_a0=conn.slot_a0,
                slot_b0=conn.slot_b0,
                label=label,
            )
        return g

    def _validate(self) -> None:
        for conn in self.connections:
            for name in (conn.gear_a, conn.gear_b):
                if name not in self.gears:
                    raise ValueError(f"Connection references unknown gear '{name}'.")
            ga = self.gears[conn.gear_a]
            gb = self.gears[conn.gear_b]
            if not (0 <= conn.slot_a0 < ga.n_slots):
                raise ValueError(
                    f"slot_a0={conn.slot_a0} out of range for gear '{conn.gear_a}' "
                    f"(n_slots={ga.n_slots})."
                )
            if not (0 <= conn.slot_b0 < gb.n_slots):
                raise ValueError(
                    f"slot_b0={conn.slot_b0} out of range for gear '{conn.gear_b}' "
                    f"(n_slots={gb.n_slots})."
                )

        seen_axials: set = set()
        for axial in self.axials:
            if not axial.anchor:
                raise ValueError(f"Axial '{axial.name}' has an empty anchor.")
            for name in axial.anchor:
                if name not in self.gears:
                    raise ValueError(
                        f"Axial '{axial.name}' anchors to unknown gear '{name}'."
                    )
            if axial.name in seen_axials:
                raise ValueError(f"Duplicate axial name '{axial.name}'.")
            seen_axials.add(axial.name)

    def total_slots(self) -> int:
        """Total number of carrier slots across all gears."""
        return sum(g.n_slots for g in self.gears.values())

    def connections_of(self, gear_name: str) -> List[Connection]:
        """Return all connections involving a given gear.

        Args:
            gear_name: Name of the gear.

        Returns:
            List of Connection objects.
        """
        return [
            c
            for c in self.connections
            if c.gear_a == gear_name or c.gear_b == gear_name
        ]

    def neighbor_at_slot(
        self, gear_name: str, slot: int, time: int
    ) -> Optional[Tuple[str, int]]:
        """If slot ``slot`` of gear ``gear_name`` is at a connection at step
        ``time``, return (neighbor_gear_name, neighbor_slot).  Otherwise None.

        Args:
            gear_name: Name of the gear.
            slot: Current slot index.
            time: Current step.

        Returns:
            (neighbor_name, neighbor_slot) or None.
        """
        for conn in self.connections_of(gear_name):
            sa, sb = conn.slots_at(self, time)
            if conn.gear_a == gear_name and sa == slot:
                return conn.gear_b, sb
            if conn.gear_b == gear_name and sb == slot:
                return conn.gear_a, sa
        return None
