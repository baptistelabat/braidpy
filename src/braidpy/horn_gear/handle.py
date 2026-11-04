# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braiding machine worked by hand: carriers placed, the handle turned a
step at a time, forwards or back.

:func:`~braidpy.horn_gear.loading.load_carriers` loads a machine outright,
but when the loading wanted collides it says nothing of where or why.
Turning the handle and watching is often quicker.

What is turned is always the loading at step 0 — the carriers the machine
braids with — so there is one thing to keep: going back a step is running
one step fewer, and a carrier put on a slot at step ``t`` goes onto the slot
at step 0 that brings it there (:func:`origin`), changing the loading
itself.  Every step is the machine's own
(:func:`~braidpy.horn_gear.simulation.simulate`), and so is every
collision: two carriers in one slot, two crossing at a contact, or a carrier
either side of one.

:class:`Handle` keeps a loading and a step, for Python and plotly;
Braid Studio keeps them in the page and asks :func:`turn` for each step.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING

from .model import BraidingMachine
from .simulation import (
    CarrierId,
    CarrierState,
    CollisionError,
    MachineState,
    simulate,
)
from .tracks import Position, _next_position

if TYPE_CHECKING:
    import plotly.graph_objects as go

__all__ = ["Handle", "Turned", "drawing", "origin", "sweep", "turn"]


class Turned:
    """Where the handle got to: the machine at that step, and what stopped
    it, if anything did.

    Args:
        state: The carriers at the step reached.
        met: Where carriers met, by the carriers on each place; empty if
            none did.  The handle stops at the step they met.
    """

    def __init__(self, state: MachineState, met: dict[Position, list[CarrierId]]):
        self.state = state
        self.met = met

    @property
    def time(self) -> int:
        """The step reached."""
        return self.state.time

    @property
    def positions(self) -> list[Position]:
        """Where each carrier is, in the loading's order."""
        return [c.position for c in self.state.carriers]


def _numbered(loading: Sequence[Position]) -> dict[CarrierId, Position]:
    return {i: (str(g), int(s)) for i, (g, s) in enumerate(loading)}


def turn(machine: BraidingMachine, loading: Sequence[Position], time: int) -> Turned:
    """The handle turned ``time`` steps from a loading, as the machine turns
    it, stopping where carriers meet.

    Args:
        machine: The machine.
        loading: The carriers at step 0, as (gear, slot).
        time: How many steps to turn.

    Returns:
        Where the handle got to.
    """
    numbered = _numbered(loading)
    shared: dict[Position, list[CarrierId]] = {}
    for cid, place in numbered.items():
        shared.setdefault(place, []).append(cid)
    shared = {place: ids for place, ids in shared.items() if len(ids) > 1}
    if shared:
        # Two carriers put on one slot: met before anything moved.
        carriers = tuple(CarrierState(cid, g, s) for cid, (g, s) in numbered.items())
        return Turned(MachineState(time=0, carriers=carriers), shared)
    try:
        history = simulate(machine, max(0, time), numbered)
    except CollisionError as stopped:
        return Turned(stopped.history[-1], dict(stopped.collisions))
    return Turned(history[-1], {})


def origin(machine: BraidingMachine, position: Position, time: int) -> Position | None:
    """The slot at step 0 whose carrier is at ``position`` at step ``time``.

    Args:
        machine: The machine.
        position: A place at step ``time``, as (gear, slot).
        time: The step.

    Returns:
        That slot; None if no slot leads there.
    """
    wanted = (str(position[0]), int(position[1]))
    for gear_name, gear in machine.gears.items():
        for slot in range(gear.n_slots):
            place: Position = (gear_name, slot)
            for t in range(time):
                place = _next_position(machine, place, t)
            if place == wanted:
                return (gear_name, slot)
    return None


class Handle:
    """A machine, its loading, and how far its handle has been turned.

    >>> from braidpy.horn_gear.examples import flat_braid_9
    >>> handle = Handle(flat_braid_9())
    >>> handle.turn(3).time
    3
    >>> handle.back().time
    2

    Args:
        machine: The machine.
        loading: The carriers at step 0; the machine's own if None.
    """

    def __init__(
        self, machine: BraidingMachine, loading: Sequence[Position] | None = None
    ):
        self.machine = machine
        if loading is None:
            own = machine.default_carriers()
            loading = [own[k] for k in sorted(own)]
        self.loading: list[Position] = [(str(g), int(s)) for g, s in loading]
        self.time = 0

    def turned(self) -> Turned:
        """The machine as the handle has turned it."""
        return turn(self.machine, self.loading, self.time)

    @property
    def met(self) -> dict[Position, list[CarrierId]]:
        """Where carriers met, if they did, on the way to this step."""
        return self.turned().met

    def turn(self, steps: int = 1) -> Handle:
        """Turn the handle on, stopping where carriers meet.

        Args:
            steps: How many steps.

        Returns:
            The handle, at the step reached.
        """
        self.time = turn(self.machine, self.loading, self.time + steps).time
        return self

    def back(self, steps: int = 1) -> Handle:
        """Turn the handle back, no further than step 0.

        Args:
            steps: How many steps.

        Returns:
            The handle.
        """
        self.time = max(0, self.time - steps)
        return self

    def toggle(self, position: Position) -> Handle:
        """Put a carrier on a place, as it is at this step, or take off the
        one there: the loading changes, at the slot that leads there.

        Args:
            position: The place, as (gear, slot), at this step.

        Returns:
            The handle.

        Raises:
            ValueError: If no slot leads there.
        """
        start = origin(self.machine, position, self.time)
        if start is None:
            raise ValueError(f"No slot leads to {position} at step {self.time}.")
        if start in self.loading:
            self.loading.remove(start)
        else:
            self.loading.append(start)
        return self

    def figure(self, **options) -> go.Figure:
        """The machine turned from step 0 to this one, as a plotly
        animation; where carriers met, ringed.

        Args:
            **options: For :func:`~braidpy.horn_gear.visualization.animate`.

        Returns:
            The figure.
        """
        from .visualization import animate

        return animate(
            self.machine,
            n_steps=self.time,
            carrier_positions=_numbered(self.loading),
            **options,
        )


Drawing = tuple[dict[str, tuple[float, float]], dict[str, float], dict[str, float]]


def drawing(machine: BraidingMachine) -> Drawing:
    """Where a machine's gears are, how they are turned and the circle their
    carriers ride: worked out once, for :func:`sweep` to draw every step."""
    from .layout import carrier_radius, compute_layout, slot_offsets

    layout = compute_layout(machine)
    offsets = slot_offsets(machine, layout)
    riding = {name: carrier_radius(machine, layout, name) for name in machine.gears}
    return layout, offsets, riding


def sweep(
    machine: BraidingMachine,
    state: MachineState,
    frames: int,
    drawn: Drawing | None = None,
) -> tuple[list[Position], list[list[list[float]]], list[list[list[float]]]]:
    """Where every slot and carrier is through one step, from ``state``:
    ``frames`` pictures, the first the step itself.  The same places as the
    plotly animation draws (:func:`~braidpy.horn_gear.visualization.animate`).

    Args:
        machine: The machine.
        state: The carriers at the step.
        frames: How many pictures.
        drawn: The machine's :func:`drawing`, if already worked out.

    Returns:
        The slots, gear by gear; and per picture, each slot's and each
        carrier's (x, y).
    """
    from .layout import carrier_xy
    from .visualization import _slot_angle

    layout, offsets, riding = drawn or drawing(machine)
    slots = [
        (name, slot)
        for name, gear in machine.gears.items()
        for slot in range(gear.n_slots)
    ]
    slot_xy: list[list[list[float]]] = []
    carrier_places: list[list[list[float]]] = []
    for k in range(frames):
        frac = k / frames
        here = []
        for name, slot in slots:
            angle = _slot_angle(machine, name, slot, offsets[name], state.time, frac)
            cx, cy = layout[name]
            here.append(
                [
                    cx + riding[name] * math.cos(angle),
                    cy + riding[name] * math.sin(angle),
                ]
            )
        slot_xy.append(here)
        carrier_places.append(
            [
                list(
                    carrier_xy(
                        machine, layout, offsets, riding, c.position, state.time, frac
                    )
                )
                for c in state.carriers
            ]
        )
    return slots, slot_xy, carrier_places
