# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/model.py
==================

Data model for a horn gear braiding machine.

A machine is a graph of HornGear nodes connected by Connection edges.

A connection is a fixed point in space where two gears meet.  As a gear turns,
a different slot arrives there; ``Connection.slot_a0``/``slot_b0`` record which
slot of each gear sits there at t=0.

:class:`BraidingMachine` describes a machine whose gears are geared together:
every gear turns one slot every step, each slot belongs to one gear, and a
carrier crosses to its neighbour when its slot reaches a contact.  A machine
built differently says so by overriding a handful of methods —
:meth:`~BraidingMachine.turning_gears`, :meth:`~BraidingMachine.rotation`,
:meth:`~BraidingMachine.next_position` and their neighbours — and the rest of
the package needs no special case.  See
:class:`~braidpy.horn_gear.jacquard.JacquardLaceMachine`.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import reduce
from math import lcm
from typing import Dict, FrozenSet, Iterable, List, Optional, Tuple

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

    def angle_at_rotation(self, slot: int, rotation: float) -> float:
        """Angle (radians) of a slot after the gear has turned ``rotation`` slots.

        The gear knows only how far it has turned, never how that relates to
        simulation time — a gear that is driven individually turns at its own
        pace.  Ask the machine for the rotation; see
        :meth:`BraidingMachine.rotation`.

        Args:
            slot: Slot index (0-based).
            rotation: Signed slots turned through, fractional allowed.

        Returns:
            Angle in radians, measured CCW from the positive x-axis.
        """
        return 2 * math.pi * (slot + rotation) / self.n_slots


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
        sa = machine.slot_at_connection(self.gear_a, self.slot_a0, time)
        sb = machine.slot_at_connection(self.gear_b, self.slot_b0, time)
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

    #: Whether neighbouring gear circles overlap, cutting a notch that both
    #: gears share, rather than merely touching at a point.
    gears_interpenetrate: bool = False

    #: Whether carriers follow closed tracks fixed by the machine's wiring.
    #: False on a machine driven by a programme, where the path a carrier
    #: takes is whatever the programme dictates and need never come back.
    has_fixed_tracks: bool = True

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

    # ── How the gears are driven ──────────────────────────────────────────
    #
    # An ordinary braiding machine has its gears geared together: they all
    # turn, one slot at a time, for ever.  A machine that drives each gear
    # separately — a Jacquard lace machine reading a mask — overrides these
    # three methods, and nothing else in the package needs to know.

    def turning_gears(self, step: int) -> FrozenSet[str]:
        """Gears that turn during the transition from ``step`` to ``step + 1``.

        Args:
            step: The step being taken.

        Returns:
            Names of the gears that move.  Every gear, on an ordinary machine.
        """
        return frozenset(self.gears)

    def rotation(self, gear_name: str, time: int) -> int:
        """Signed number of slots a gear has turned through after ``time`` steps.

        Args:
            gear_name: Name of the gear.
            time: Current step.

        Returns:
            Slots turned; negative for a clockwise gear.
        """
        return self.gears[gear_name].direction * time

    def contact_period(self) -> int:
        """Steps after which every contact shows the same slots again.

        Each gear returns its slots to the contacts every ``n_slots`` steps,
        so the machine's contact pattern repeats with period ``lcm(n_slots)``.
        """
        return reduce(lcm, (g.n_slots for g in self.gears.values()), 1)

    # ── Derived from the above ────────────────────────────────────────────

    def program_rows(self) -> Optional[List[Tuple[str, Tuple[bool, ...]]]]:
        """The machine's programme as punchcard rows, or None if it has none.

        One row per phase, in the order they are driven, each a label and a
        flag per gear.  A machine whose gears are geared together has no
        programme to show.

        Returns:
            List of (label, flags) or None.
        """
        return None

    def preferred_layout(
        self, scale: float = 1.0
    ) -> Optional[Dict[str, Tuple[float, float]]]:
        """A layout the machine knows to be right for itself, or None.

        Returning None lets :func:`~braidpy.horn_gear.layout.compute_layout`
        work the positions out from the connection graph, which is what an
        ordinary machine of tangent gears wants.  A machine whose geometry is
        pinned by its own construction overrides this.

        Args:
            scale: Overall scale factor for gear radii.

        Returns:
            Gear name → (x, y), or None to let the layout be computed.
        """
        return None

    def riding_position(self, pos: Tuple[str, int], time: int) -> Tuple[str, int]:
        """Which (gear, slot) sweeps a carrier through the step at ``time``.

        This is what an animation must draw it on, and it is not always where
        the carrier is recorded.  On an ordinary machine the carrier's own gear
        carries it round to the contact and hands over only at the very end of
        the step, so it rides its own gear throughout — which is what this
        returns.

        A machine whose gears share their slots overrides this, because there
        the *receiving* gear does the sweeping: see
        :meth:`~braidpy.horn_gear.jacquard.JacquardLaceMachine.riding_position`.

        Args:
            pos: The carrier's (gear_name, slot_index) at ``time``.
            time: Step being taken.

        Returns:
            The (gear_name, slot_index) to draw the carrier on for this step.
        """
        return pos

    def default_carriers(self) -> Dict[int, Tuple[str, int]]:
        """How to thread this machine when the caller does not say.

        A wired machine is loaded along its tracks, as far as it will go.  A
        machine without tracks overrides this — see
        :func:`~braidpy.horn_gear.jacquard.notch_positions`.

        Returns:
            Dict mapping carrier_id → (gear_name, slot).
        """
        from .simulation import load_carriers

        return load_carriers(self)

    def next_position(self, pos: Tuple[str, int], time: int) -> Tuple[str, int]:
        """Where a carrier goes during the step from ``time`` to ``time + 1``.

        On an ordinary machine the gears are **tangent** and every slot belongs
        to one gear alone, so a carrier rides its own slot round until that
        slot arrives at a contact, and then crosses into the neighbour's slot
        waiting there.

        A machine built differently overrides this — see
        :meth:`~braidpy.horn_gear.jacquard.JacquardLaceMachine.next_position`,
        whose gears interpenetrate and share their slots.

        Args:
            pos: Current (gear_name, slot_index).
            time: Step being taken.

        Returns:
            The (gear_name, slot_index) the carrier occupies afterwards.
        """
        gear_name, slot = pos
        if gear_name not in self.turning_gears(time):
            return pos

        # time + 1 because the gear turns first, then the transfer happens.
        neighbor = self.neighbor_at_slot(gear_name, slot, time + 1)
        return neighbor if neighbor is not None else pos

    def slot_at_connection(self, gear_name: str, slot0_at_t0: int, time: int) -> int:
        """Which slot sits at the contact whose slot at t=0 was ``slot0_at_t0``.

        Contacts are fixed in space, so as the gear turns a different slot
        arrives at each one.

        Args:
            gear_name: Name of the gear.
            slot0_at_t0: Slot that was at the contact at t=0.
            time: Current step.

        Returns:
            Slot index currently at that contact.
        """
        gear = self.gears[gear_name]
        return (slot0_at_t0 - self.rotation(gear_name, time)) % gear.n_slots

    def slot_angle(
        self, gear_name: str, slot: int, time: int = 0, frac: float = 0.0
    ) -> float:
        """Angle (radians) of a slot at continuous time ``time + frac``.

        Args:
            gear_name: Name of the gear.
            slot: Slot index.
            time: Current step.
            frac: Fraction of the way into the step, for smooth animation.

        Returns:
            Angle in radians, measured CCW from the positive x-axis.
        """
        rotation = float(self.rotation(gear_name, time))
        if frac:
            step_arc = self.rotation(gear_name, time + 1) - rotation
            rotation += step_arc * frac
        return self.gears[gear_name].angle_at_rotation(slot, rotation)

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
