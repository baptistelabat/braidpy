# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/simulation.py
========================

Simulation state and stepping for a horn gear braiding machine.

Each carrier occupies exactly one (gear, slot) position.  At each step
every *turning* gear advances by one slot-pitch, carrying its slots round
with it; a carrier keeps its own slot and rides with it, and crosses into a
neighbour's slot only when its own slot reaches a contact.  So the slot
index of a carrier riding its gear does not change from step to step — it
changes when the carrier transfers.

"Turning" matters: an ordinary machine turns every gear every step, but
:meth:`~braidpy.horn_gear.jacquard.JacquardLaceMachine.turning_gears` enables
only the gears of the current phase, and a gear that is not turning holds its
carriers where they are.

This module is intentionally pure / functional: MachineState is a frozen
dataclass and ``step()`` returns a new state rather than mutating in place,
making it easy to replay or branch the simulation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple


from .model import BraidingMachine
from .tracks import Position, _next_position


if TYPE_CHECKING:
    pass

# Carrier identifier — any hashable type, typically int or str.
CarrierId = int


class CollisionError(RuntimeError):
    """Raised when two or more carriers occupy the same (gear, slot) after a step.

    Attributes:
        step: The step at which the collision was detected.
        collisions: Mapping of {(gear, slot): [carrier_id, ...]} for every
            position with more than one carrier.
        history: Valid MachineState list up to (but not including) the
            colliding step — i.e. the last entry is the last safe state.
    """

    def __init__(
        self,
        step: int,
        collisions: Dict[Position, List[CarrierId]],
        history: "List[MachineState]",
    ) -> None:
        parts = [
            f"gear={g} slot={s} → carriers {ids}" for (g, s), ids in collisions.items()
        ]
        super().__init__(f"Collision at step {step}: {'; '.join(parts)}")
        self.step = step
        self.collisions = collisions
        self.history = history


@dataclass(frozen=True)
class CarrierState:
    """Position and identity of a single carrier.

    Args:
        carrier_id: Unique identifier for this carrier.
        gear: Gear the carrier is currently on.
        slot: Slot index within that gear.
    """

    carrier_id: CarrierId
    gear: str
    slot: int

    @property
    def position(self) -> Position:
        return self.gear, self.slot


@dataclass(frozen=True)
class MachineState:
    """Snapshot of the machine at a particular simulation step.

    Args:
        time: Current step index (0 = initial state).
        carriers: Tuple of CarrierState, one per carrier.
    """

    time: int
    carriers: Tuple[CarrierState, ...]

    def carrier_positions(self) -> Dict[CarrierId, Position]:
        """Return {carrier_id: (gear, slot)} for all carriers."""
        return {c.carrier_id: c.position for c in self.carriers}


def initial_state(
    machine: BraidingMachine,
    carrier_positions: Optional[Dict[CarrierId, Position]] = None,
) -> MachineState:
    """Create an initial MachineState.

    If ``carrier_positions`` is None, one carrier is placed in each slot
    across all gears in the order they were defined.

    Args:
        machine: The machine definition.
        carrier_positions: Optional mapping {carrier_id: (gear, slot)}.

    Returns:
        MachineState at time=0.

    Raises:
        ValueError: If two carriers share a position, or a position is invalid.
    """
    if carrier_positions is None:
        # Fill every slot with one carrier, numbered sequentially.
        positions: Dict[CarrierId, Position] = {}
        cid = 0
        for gear_name, gear in machine.gears.items():
            for slot in range(gear.n_slots):
                positions[cid] = (gear_name, slot)
                cid += 1
    else:
        positions = carrier_positions

    # Validate.
    seen: Dict[Position, CarrierId] = {}
    for cid, pos in positions.items():
        gear_name, slot = pos
        if gear_name not in machine.gears:
            raise ValueError(f"Carrier {cid}: unknown gear '{gear_name}'.")
        gear = machine.gears[gear_name]
        if not (0 <= slot < gear.n_slots):
            raise ValueError(
                f"Carrier {cid}: slot {slot} out of range for gear '{gear_name}'."
            )
        if pos in seen:
            raise ValueError(f"Carriers {seen[pos]} and {cid} share position {pos}.")
        seen[pos] = cid

    carriers = tuple(
        CarrierState(carrier_id=cid, gear=g, slot=s)
        for cid, (g, s) in positions.items()
    )
    return MachineState(time=0, carriers=carriers)


def step(machine: BraidingMachine, state: MachineState) -> MachineState:
    """Advance the machine by one step.

    Each carrier moves to its next position as determined by
    ``_next_position`` (gear rotation + optional transfer).

    Args:
        machine: The machine definition.
        state: Current machine state.

    Returns:
        New MachineState at state.time + 1.
    """
    new_carriers = tuple(
        CarrierState(
            carrier_id=c.carrier_id,
            gear=next_pos[0],
            slot=next_pos[1],
        )
        for c in state.carriers
        for next_pos in (_next_position(machine, c.position, state.time),)
    )
    return MachineState(time=state.time + 1, carriers=new_carriers)


def carrier_places(
    machine: BraidingMachine, state: MachineState
) -> Dict[CarrierId, Tuple[str, int]]:
    """Where each carrier actually *is*: its gear, and the angle it has reached.

    A slot index is a label painted on a turning gear, not a place.  Every step
    turns a gear by one slot, so its notches land back on notch angles and the
    gear is indistinguishable from the gear a step earlier — which means a
    carrier sitting in a different notch may be at exactly the point in space
    it started from, and one back in "its own" notch may be on the far side of
    the gear.  What the eye sees, and what the machine does next, follow from
    the angle.

    Angles are returned as whole millionths of a turn, so they compare exactly
    and 0 and a full turn are the same place.

    Args:
        machine: The machine definition.
        state: The snapshot to read.

    Returns:
        {carrier_id: (gear, angle in millionths of a turn)}.
    """
    turn = 2 * math.pi
    return {
        c.carrier_id: (
            c.gear,
            round(machine.slot_angle(c.gear, c.slot, state.time) % turn / turn * 1e6)
            % 1_000_000,
        )
        for c in state.carriers
    }


def state_period(
    machine: BraidingMachine,
    carrier_positions: Optional[Dict[CarrierId, Position]] = None,
    max_steps: int = 10_000,
) -> Optional[int]:
    """Steps after which the machine is exactly as it started, or None.

    "Exactly" means every carrier back at the point it set off from — see
    :func:`carrier_places` for why that is not the same as back in its own
    slot — and the drive back to its starting phase, so the step that follows
    is the step that followed then.  Run the machine for this many steps and
    the last frame hands straight back to the first.

    This is a property of the machine and of how it is loaded, and it varies a
    lot: eight steps for a square braid, eighteen for a flat braid on nine
    carriers.  It is *not* how long a carrier takes to walk its whole track —
    that flat braid's track is ninety steps round — because the machine is back
    where it started long before any one carrier has been everywhere.

    A machine driven by a programme need not ever come back — a carrier goes
    where the programme sends it — so this returns None rather than pretend.

    Args:
        machine: The machine definition.
        carrier_positions: The carriers to follow; the machine's own if None.
        max_steps: How far to look before giving up.

    Returns:
        The cycle length in steps, or None if there is none within reach.
    """
    state = initial_state(machine, carrier_positions)
    start = carrier_places(machine, state)
    # Whatever drives the machine has to come round too, or the next step would
    # not be the step that followed last time.  Geared together, nothing
    # depends on the clock once the angles match; driven by a programme, the
    # programme has to be back at its first row.
    rows = machine.program_rows()
    phase = len(rows) if rows else 1

    for t in range(1, max_steps + 1):
        state = step(machine, state)
        if t % phase == 0 and carrier_places(machine, state) == start:
            return t
    return None


def simulate(
    machine: BraidingMachine,
    n_steps: int,
    carrier_positions: Optional[Dict[CarrierId, Position]] = None,
) -> List[MachineState]:
    """Run the simulation for ``n_steps`` steps.

    Args:
        machine: The machine definition.
        n_steps: Number of steps to simulate.
        carrier_positions: Optional initial placement of carriers.

    Returns:
        List of MachineState objects, length n_steps + 1 (includes t=0).
    """
    state = initial_state(machine, carrier_positions)
    history: List[MachineState] = [state]

    # Check the initial state: if both sides of a connection are already occupied,
    # carriers are at the same physical point at frac=0 of step 0.
    _check_connection_point_collision(machine, state, history)

    for _ in range(n_steps):
        prev_state = state
        state = step(machine, state)

        # 1. Same-gear same-slot collision.
        occupied: Dict[Position, List[CarrierId]] = {}
        for c in state.carriers:
            occupied.setdefault(c.position, []).append(c.carrier_id)
        same_slot = {pos: ids for pos, ids in occupied.items() if len(ids) > 1}
        if same_slot:
            history.append(state)
            raise CollisionError(state.time, same_slot, history)

        # 2. Crossing-transfer collision: two carriers swapping through the same
        #    connection in opposite directions.  Both end up at the contact point
        #    at frac=0 of the next step, which is the same physical (x, y).
        prev_gear = {c.carrier_id: c.gear for c in prev_state.carriers}
        curr_gear = {c.carrier_id: c.gear for c in state.carriers}
        for conn in machine.connections:
            a_to_b = [
                cid
                for cid in prev_gear
                if prev_gear[cid] == conn.gear_a and curr_gear[cid] == conn.gear_b
            ]
            b_to_a = [
                cid
                for cid in prev_gear
                if prev_gear[cid] == conn.gear_b and curr_gear[cid] == conn.gear_a
            ]
            if a_to_b and b_to_a:
                new_map = {c.carrier_id: c for c in state.carriers}
                col: Dict[Position, List[CarrierId]] = {}
                for cid in a_to_b:
                    col.setdefault(new_map[cid].position, []).append(cid)
                for cid in b_to_a:
                    col.setdefault(new_map[cid].position, []).append(cid)
                history.append(state)
                raise CollisionError(state.time, col, history)

        history.append(state)

        # Check whether the new state already has both sides of a connection
        # occupied (would cause a visual collision at frac=0 of the next step).
        _check_connection_point_collision(machine, state, history)

    return history


def _check_connection_point_collision(
    machine: BraidingMachine,
    state: MachineState,
    history: "List[MachineState]",
) -> None:
    """Raise CollisionError if both sides of any connection are occupied.

    When both gear_a[sa(t)] and gear_b[sb(t)] hold carriers they are at the
    same physical tangent point, causing a visual collision at frac=0 of the
    next animation step.

    Contacts the machine says are not exchanging this step are skipped: see
    :meth:`~braidpy.horn_gear.model.BraidingMachine.contact_exchanges`.
    """
    pos_map = {c.position: c.carrier_id for c in state.carriers}
    for conn in machine.connections:
        # A contact that is not exchanging this step holds the two gears'
        # paths apart, so both of its slots may be occupied at once.
        if not machine.contact_exchanges(conn, state.time):
            continue
        sa = machine.slot_at_connection(conn.gear_a, conn.slot_a0, state.time)
        sb = machine.slot_at_connection(conn.gear_b, conn.slot_b0, state.time)
        if (conn.gear_a, sa) in pos_map and (conn.gear_b, sb) in pos_map:
            cid_a = pos_map[(conn.gear_a, sa)]
            cid_b = pos_map[(conn.gear_b, sb)]
            col = {
                (conn.gear_a, sa): [cid_a],
                (conn.gear_b, sb): [cid_b],
            }
            raise CollisionError(state.time, col, history)
