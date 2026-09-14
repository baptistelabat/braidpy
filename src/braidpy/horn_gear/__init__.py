# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/__init__.py
======================

Horn gear braiding machine simulator.

A braiding machine is described as a graph of connected horn gears.  Each
gear has N slots and the bobbins (carriers) travel between gears as the gears
turn.

:class:`BraidingMachine` covers machines whose gears are geared together, where
the carriers follow closed tracks fixed by the wiring.
:class:`JacquardLaceMachine` covers machines whose gears are driven one by one
from a punched programme, where they do not.  Both are laid out, simulated and
drawn by the same code.
"""

from .jacquard import (
    JacquardLaceMachine,
    JacquardProgramError,
    jacquard_lace_ring,
    notch_positions,
)
from .layout import (
    axial_clearance,
    axial_position,
    axial_positions,
    carrier_radius,
    compute_layout,
    contact_angle,
    contact_point,
    gear_radii,
    offset_residuals,
    slot_offsets,
    tube_axials,
    tube_rings,
)
from .model import Axial, BraidingMachine, Connection, HornGear
from .simulation import (
    CarrierState,
    CollisionError,
    MachineState,
    initial_state,
    load_carriers,
    simulate,
    step,
)
from .tracks import NoFixedTracks, compute_track, compute_tracks, simulation_period
from .visualization import animate, visualize_machine, visualize_tracks

__all__ = [
    # model
    "HornGear",
    "Connection",
    "Axial",
    "BraidingMachine",
    # jacquard lace machine
    "JacquardLaceMachine",
    "JacquardProgramError",
    "jacquard_lace_ring",
    "notch_positions",
    # layout
    "compute_layout",
    "gear_radii",
    # geometry derived from the layout
    "contact_point",
    "contact_angle",
    "carrier_radius",
    "slot_offsets",
    "offset_residuals",
    # axial columns and tube cores
    "axial_position",
    "axial_positions",
    "axial_clearance",
    "tube_rings",
    "tube_axials",
    # tracks
    "compute_track",
    "compute_tracks",
    "simulation_period",
    "NoFixedTracks",
    # simulation
    "CarrierState",
    "MachineState",
    "CollisionError",
    "initial_state",
    "load_carriers",
    "step",
    "simulate",
    # visualization
    "visualize_machine",
    "visualize_tracks",
    "animate",
]
