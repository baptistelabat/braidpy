# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/take_off.py
======================

The braid coming off a horn gear machine.

The machine says where each carrier is at every instant
(:func:`carrier_trajectories`); from there the braid is laid, drawn in to a
fell or braiding point and tightened exactly as any other source of strands
is — see :mod:`braidpy.take_off`, which holds the model.  This module only
adds what a machine knows: its gears to stand the braid on, the middle of
them for an axis, the axial cores the braid is laid round, and a take-off
rate in proportion to its gears.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import numpy as np
from braidpy.utils import lazy_module

if TYPE_CHECKING:
    import plotly.graph_objects as go
else:
    go = lazy_module("plotly.graph_objects")

from braidpy.take_off import (
    StrandTrajectories,
    YarnPaths,
    jammed_contraction,
    lay_yarns,
    tighten_yarns,
)
from braidpy.take_off import visualize_yarns as _visualize_yarns

from .layout import (
    axial_positions,
    carrier_radius,
    carrier_xy,
    compute_layout,
    gear_radii,
    slot_offsets,
)
from .model import BraidingMachine
from .simulation import CarrierId, Position, simulate, state_period

__all__ = [
    "CarrierTrajectories",
    "YarnPaths",
    "carrier_trajectories",
    "default_take_off",
    "jammed_contraction",
    "tighten_yarns",
    "visualize_yarns",
    "yarn_paths",
]


@dataclass(frozen=True)
class CarrierTrajectories(StrandTrajectories):
    """Where every carrier went, sampled through a run of the machine.

    :class:`~braidpy.take_off.StrandTrajectories` with times in steps, and the
    machine's layout kept alongside.

    Args:
        layout: Gear centres the positions are measured against.
        radii: Gear radii at the same scale.
    """

    layout: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    radii: Dict[str, float] = field(default_factory=dict)


def carrier_trajectories(
    machine: BraidingMachine,
    n_steps: int,
    carrier_positions: Optional[Dict[CarrierId, Position]] = None,
    n_substeps: int = 12,
    scale: float = 1.0,
) -> CarrierTrajectories:
    """Follow every carrier through ``n_steps`` steps of the machine.

    Each step is split into ``n_substeps`` samples, at the same positions the
    animation draws (:func:`~braidpy.horn_gear.layout.carrier_xy`), so what is
    laid here is exactly what is seen turning there.

    Args:
        machine: The machine definition.
        n_steps: How many steps to run.
        carrier_positions: The loading; the machine's own if None.
        n_substeps: Samples per step.
        scale: Layout scale.

    Returns:
        The sampled trajectories, ``n_steps * n_substeps + 1`` samples long.

    Raises:
        CollisionError: If the loading collides within the run — a braid that
            cannot be made has no shape to give.
    """
    if n_substeps < 1:
        raise ValueError("n_substeps must be at least 1.")
    if carrier_positions is None:
        carrier_positions = machine.default_carriers()

    layout = compute_layout(machine, scale=scale)
    offsets = slot_offsets(machine, layout)
    riding = {
        name: carrier_radius(machine, layout, name, scale) for name in machine.gears
    }
    history = simulate(machine, n_steps, carrier_positions)

    times: List[float] = []
    xy: Dict[CarrierId, List[Tuple[float, float]]] = {
        c.carrier_id: [] for c in history[0].carriers
    }
    for state in history:
        last = state.time == n_steps
        for k in range(1 if last else n_substeps):
            frac = k / n_substeps
            times.append(state.time + frac)
            for c in state.carriers:
                xy[c.carrier_id].append(
                    carrier_xy(
                        machine, layout, offsets, riding, c.position, state.time, frac
                    )
                )

    radii = gear_radii(machine, scale=scale)
    angles = np.linspace(0.0, 2 * np.pi, 73)
    gears = tuple(
        np.column_stack(
            [cx + radii[name] * np.cos(angles), cy + radii[name] * np.sin(angles)]
        )
        for name, (cx, cy) in layout.items()
    )
    centres = np.array(list(layout.values()))
    return CarrierTrajectories(
        times=np.asarray(times),
        xy={cid: np.asarray(points) for cid, points in xy.items()},
        outlines=gears,
        axis=(float(centres[:, 0].mean()), float(centres[:, 1].mean())),
        label="Yarn C",
        outline_name="Gears",
        layout=layout,
        radii=radii,
    )


def default_take_off(machine: BraidingMachine, scale: float = 1.0) -> float:
    """A take-off rate that draws a machine's braid in sensible proportions.

    Half the mean gear radius per step: a carrier then moves across the deck
    about as far as the braid moves up, so its yarn leaves at roughly 45°,
    near the angle a braid is usually made at.  It sets only how stretched the
    picture is — nothing about which yarn crosses which depends on it.
    """
    radii = gear_radii(machine, scale=scale)
    return 0.5 * sum(radii.values()) / len(radii)


def yarn_paths(
    machine: BraidingMachine,
    n_steps: Optional[int] = None,
    carrier_positions: Optional[Dict[CarrierId, Position]] = None,
    take_off: Optional[float] = None,
    n_substeps: int = 12,
    scale: float = 1.0,
    n_cycles: int = 3,
    **lay,
) -> YarnPaths:
    """The braid a machine has made after ``n_steps`` steps.

    Follows the carriers (:func:`carrier_trajectories`) and lays their yarns
    with :func:`~braidpy.take_off.lay_yarns`, which ``lay`` is passed to:
    ``fell_radius``, ``yarn_diameter``, ``fell_height``, ``axis``,
    ``n_converge`` and ``settle_length``.  The axis defaults to the middle of
    the gears.

    Args:
        machine: The machine definition.
        n_steps: How long to braid for.  If None, ``n_cycles`` full cycles of
            the machine (:func:`~braidpy.horn_gear.simulation.state_period`),
            so the braid shows its repeat that many times over; a programmed
            machine with no cycle runs its drive round that many times.
        carrier_positions: The loading; the machine's own if None.
        take_off: Length of braid drawn off per step.  Defaults to
            :func:`default_take_off`.
        n_substeps: Samples per step.  With a ``yarn_diameter``, keep
            ``take_off / n_substeps`` below it, or contacts go unseen.
        scale: Layout scale.
        n_cycles: Cycles to braid for when ``n_steps`` is None.

    Returns:
        The yarns, one per carrier.
    """
    if carrier_positions is None:
        carrier_positions = machine.default_carriers()
    if n_steps is None:
        cycle = state_period(machine, carrier_positions)
        if cycle is None:
            cycle = machine.contact_period()
        n_steps = n_cycles * cycle
    if take_off is None:
        take_off = default_take_off(machine, scale)
    traj = carrier_trajectories(
        machine, n_steps, carrier_positions, n_substeps=n_substeps, scale=scale
    )
    return lay_yarns(traj, take_off=take_off, **lay)


def visualize_yarns(
    machine: BraidingMachine,
    paths: Optional[YarnPaths] = None,
    output_html: Optional[str] = None,
    title: Optional[str] = None,
    tube_diameter: Optional[float] = None,
    n_around: int = 12,
    show_deck: bool = True,
    **kwargs,
) -> go.Figure:
    """The yarns in 3D, standing on the machine that laid them.

    :func:`~braidpy.take_off.visualize_yarns`, with the gears outlined on the
    deck and any axial core standing as a column through the braid.  Each
    yarn is drawn in its carrier's colour — the same colours as
    :func:`~braidpy.horn_gear.visualization.animate`.

    Args:
        machine: The machine definition.
        paths: Yarns to draw; computed by :func:`yarn_paths` if None, which
            ``kwargs`` are then passed to.
        output_html: If given, write the figure to this HTML file.
        title: Figure title; says which model the yarns follow if None.
        tube_diameter: Draw the yarns as tubes this thick.  Defaults to the
            yarn diameter the braid was made for, if any; 0 draws lines.
        n_around: Points round each tube, when drawing them.
        show_deck: Outline the gears at z = 0.

    Returns:
        The figure.
    """
    if paths is None:
        paths = yarn_paths(machine, **kwargs)
    elif kwargs:
        raise TypeError("kwargs are only used when paths is computed here.")

    layout = getattr(paths.trajectories, "layout", None) or compute_layout(machine)
    cores: List[go.BaseTraceType] = [
        go.Scatter3d(
            x=[ax, ax],
            y=[ay, ay],
            z=[0.0, paths.top],
            mode="lines",
            line=dict(color="rgba(60,60,60,0.8)", width=10),
            name=f"Core {axial_name}",
            hoverinfo="name",
        )
        for axial_name, (ax, ay) in axial_positions(machine, layout).items()
    ]
    if title is None:
        if paths.fell_radius is None:
            title = "Braid coming off the machine (no tension)"
        elif paths.fell_radius == 0:
            title = "Braid coming off the machine, at a braiding point"
        else:
            title = (
                "Braid coming off the machine, formed on a fell of radius "
                f"{paths.fell_radius:.3g}"
            )
    return _visualize_yarns(
        paths,
        output_html=output_html,
        title=title,
        tube_diameter=tube_diameter,
        n_around=n_around,
        show_deck=show_deck,
        extra_traces=cores,
    )
