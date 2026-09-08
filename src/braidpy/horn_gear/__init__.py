# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/__init__.py
======================

Horn gear braiding machine simulator.

A braiding machine is described as a graph of connected horn gears.
Each gear has N slots; bobbins (carriers) travel between gears along
closed tracks determined by the connection topology and gear rotations.
"""

from .layout import (
    axial_clearance,
    axial_position,
    axial_positions,
    compute_layout,
    gear_radii,
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
from .tracks import compute_track, compute_tracks, simulation_period
from .visualization import animate, visualize_machine, visualize_tracks

__all__ = [
    # model
    "HornGear",
    "Connection",
    "Axial",
    "BraidingMachine",
    # layout
    "compute_layout",
    "gear_radii",
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
