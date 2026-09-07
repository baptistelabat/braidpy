# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/simulation.py
========================

Simulation state and stepping for a horn gear braiding machine.

Each carrier occupies exactly one (gear, slot) position.  At each step
the machine advances by one slot, transfers happen at connection points,
and the new state is returned.

This module is intentionally pure / functional: MachineState is a frozen
dataclass and ``step()`` returns a new state rather than mutating in place,
making it easy to replay or branch the simulation.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING, Dict, Iterable, Iterator, List, Optional, Tuple

from .model import BraidingMachine
from .tracks import Position, _next_position

if TYPE_CHECKING:
    from .tracks import Track

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


def _number(positions: Iterable[Position]) -> Dict[CarrierId, Position]:
    """Assign sequential carrier ids to positions, skipping repeats."""
    numbered: Dict[CarrierId, Position] = {}
    seen: set = set()
    for pos in positions:
        if pos not in seen:
            seen.add(pos)
            numbered[len(numbered)] = pos
    return numbered


def _is_collision_free(
    machine: BraidingMachine,
    positions: Dict[CarrierId, Position],
    period: int,
) -> bool:
    """True if this placement runs a full period without any collision.

    A placement that puts two carriers in one slot is rejected as well, so
    callers may propose one without pre-checking.
    """
    try:
        simulate(machine, period, positions)
    except (CollisionError, ValueError):
        return False
    return True


def _alternating_loadings(
    tracks: List["Track"],
) -> Iterator[Dict[CarrierId, Position]]:
    """Every other slot along each track, for each choice of starting offset.

    Tracks may share a slot — carriers can cross it at different times without
    ever meeting — so repeats are dropped rather than doubly occupied.
    """
    for offsets in product((0, 1), repeat=len(tracks)):
        yield _number(
            track[i]
            for track, off in zip(tracks, offsets)
            for i in range(off, len(track), 2)
        )


def _greedy_loadings(
    machine: BraidingMachine,
) -> Iterator[List[Position]]:
    """Candidate slot orderings for greedy loading, one per starting slot.

    Greedy loading is very sensitive to where it starts, so every slot gets a
    turn at being first.
    """
    slots = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    for seed in range(len(slots)):
        yield slots[seed:] + slots[:seed]


def load_carriers(machine: BraidingMachine) -> Dict[CarrierId, Position]:
    """Fill the machine with as many carriers as it can hold without collisions.

    A real machine is loaded with a spool in every other slot along each track,
    which is what this tries first.  That has no meaning for a track whose path
    revisits slots — the interior gears of a flat braid are crossed once per
    traversal — so the fallback simply adds carriers one at a time, keeping
    each one that leaves the machine collision-free.

    Either way the candidate is validated by simulating a full period: checking
    occupancy at t=0 is not enough, because contact points move to a different
    slot every step and conflicts can surface later in the cycle.

    Half the slots is the most any machine can hold, since only one of the two
    slots meeting at a contact may be occupied, so the search stops there.

    Args:
        machine: The machine definition.

    Returns:
        Dict mapping carrier_id → (gear_name, slot).

    Raises:
        RuntimeError: If not even one carrier can be placed.
    """
    from .tracks import compute_tracks, simulation_period

    period = simulation_period(machine)
    target = machine.total_slots() // 2

    for positions in _alternating_loadings(compute_tracks(machine)):
        if _is_collision_free(machine, positions, period):
            return positions

    best: Dict[CarrierId, Position] = {}
    for order in _greedy_loadings(machine):
        chosen: Dict[CarrierId, Position] = {}
        for pos in order:
            trial = {**chosen, len(chosen): pos}
            if _is_collision_free(machine, trial, period):
                chosen = trial
        if len(chosen) > len(best):
            best = chosen
        if len(best) >= target:
            break

    if not best:
        raise RuntimeError(
            f"No collision-free carrier placement found for this machine "
            f"(period {period})."
        )
    return best


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
    """
    pos_map = {c.position: c.carrier_id for c in state.carriers}
    for conn in machine.connections:
        sa = machine.gears[conn.gear_a].slot_at_connection(conn.slot_a0, state.time)
        sb = machine.gears[conn.gear_b].slot_at_connection(conn.slot_b0, state.time)
        if (conn.gear_a, sa) in pos_map and (conn.gear_b, sb) in pos_map:
            cid_a = pos_map[(conn.gear_a, sa)]
            cid_b = pos_map[(conn.gear_b, sb)]
            col = {
                (conn.gear_a, sa): [cid_a],
                (conn.gear_b, sb): [cid_b],
            }
            raise CollisionError(state.time, col, history)
