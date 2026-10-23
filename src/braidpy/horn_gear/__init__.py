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

:func:`yarn_paths` follows the carriers through a run and lays their yarns
off along the machine's axis, with no tension yet, and :func:`visualize_yarns`
draws the result in 3D standing on the machine.
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
    carrier_xy,
    compute_layout,
    contact_angle,
    contact_point,
    gear_radii,
    offset_residuals,
    slot_offsets,
    tube_axials,
    tube_rings,
)
from .loading import load_carriers
from .model import Axial, BraidingMachine, Connection, HornGear
from .simulation import (
    CarrierState,
    CollisionError,
    MachineState,
    carrier_places,
    initial_state,
    simulate,
    state_period,
    step,
)
from .take_off import (
    CarrierTrajectories,
    YarnPaths,
    carrier_trajectories,
    default_take_off,
    jammed_contraction,
    tighten_yarns,
    visualize_yarns,
    yarn_paths,
)
from .tracks import (
    NoFixedTracks,
    circulation,
    compute_track,
    compute_tracks,
    ring_order,
    simulation_period,
    walk,
)
from .visualization import animate, visualize_machine, visualize_tracks

__all__ = [
    "Axial",
    "BraidingMachine",
    # simulation
    "CarrierState",
    # the braid coming off the machine
    "CarrierTrajectories",
    "CollisionError",
    "Connection",
    # model
    "HornGear",
    # jacquard lace machine
    "JacquardLaceMachine",
    "JacquardProgramError",
    "MachineState",
    "NoFixedTracks",
    "YarnPaths",
    "animate",
    "axial_clearance",
    # axial columns and tube cores
    "axial_position",
    "axial_positions",
    "carrier_places",
    "carrier_radius",
    "carrier_trajectories",
    "carrier_xy",
    "circulation",
    # layout
    "compute_layout",
    # tracks
    "compute_track",
    "compute_tracks",
    "contact_angle",
    # geometry derived from the layout
    "contact_point",
    "default_take_off",
    "gear_radii",
    "initial_state",
    "jacquard_lace_ring",
    "jammed_contraction",
    "load_carriers",
    "notch_positions",
    "offset_residuals",
    "ring_order",
    "simulate",
    "simulation_period",
    "slot_offsets",
    "state_period",
    "step",
    "tighten_yarns",
    "tube_axials",
    "tube_rings",
    # visualization
    "visualize_machine",
    "visualize_tracks",
    "visualize_yarns",
    "walk",
    "yarn_paths",
]
