# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/take_off.py
======================

The braid coming off the machine, in the simplest model there is: no tension.

The simulation says where each carrier is at every instant; this turns that
history into the shape of the yarns it lays.  The braid is drawn off along the
gears' axis — the ``z`` axis, square to the machine's deck — at a steady rate,
and a yarn is taken to stay exactly where its carrier put it.  So the piece of
yarn laid at time ``t`` sits over the point the carrier occupied then, and has
since been carried up by however much braid has been taken off:

    yarn(t) = (x_carrier(t), y_carrier(t), take_off * (T - t))

for a braid observed at time ``T``.  The deck is at ``z = 0`` and the yarn
just leaving its bobbin is there; the oldest yarn is the highest.

That is a footprint of the machine extruded along its axis, not a braid as it
really comes off: real yarns are pulled taut toward a braiding point over the
middle of the machine, and a flat braid is pulled flat.  Nothing here moves a
yarn off the line its carrier drew.  What it does give is the *topology*
exactly — which yarn passes which, and on which side — and a check that the
machine's motion is what it should be, before tension is brought in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go

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


@dataclass(frozen=True)
class CarrierTrajectories:
    """Where every carrier went, sampled through a run of the machine.

    Args:
        times: Continuous time of each sample, in steps, from 0 to the run's
            length; shape ``(n,)``.
        xy: Per carrier, its position in the deck plane at each of those
            times; shape ``(n, 2)``.
        layout: Gear centres the positions are measured against.
        radii: Gear radii at the same scale.
    """

    times: np.ndarray
    xy: Dict[CarrierId, np.ndarray]
    layout: Dict[str, Tuple[float, float]]
    radii: Dict[str, float]


@dataclass(frozen=True)
class YarnPaths:
    """The yarns of a braid, as they hang off the machine at one instant.

    Args:
        times: When each point of a yarn was laid, in steps; shape ``(n,)``.
        points: Per carrier, its yarn's centreline; shape ``(n, 3)``, in the
            same order as ``times``, so the last point is the one at the deck.
        take_off: Length of braid drawn off per step.
        trajectories: The carrier motion the yarns were laid from.
    """

    times: np.ndarray
    points: Dict[CarrierId, np.ndarray]
    take_off: float
    trajectories: CarrierTrajectories

    @property
    def length(self) -> float:
        """How much braid has come off: the height of the oldest yarn."""
        return float(self.take_off * (self.times[-1] - self.times[0]))

    def to_parametric_braid(self):
        """The same yarns as a :class:`~braidpy.parametric_braid.ParametricBraid`.

        Each strand is parametrised from the deck (0) to the oldest yarn (1),
        and interpolated linearly between samples, so the drawing and the
        measuring done on parametric braids apply here too.

        Returns:
            ParametricBraid: One strand per carrier, in carrier order.
        """
        from braidpy.parametric_braid import ParametricBraid
        from braidpy.parametric_strand import ParametricStrand

        def strand(points: np.ndarray) -> ParametricStrand:
            path = points[::-1]
            s = np.linspace(0.0, 1.0, len(path))

            def func(u: float) -> Tuple[float, float, float]:
                return tuple(float(np.interp(u, s, path[:, i])) for i in range(3))

            return ParametricStrand(func)

        return ParametricBraid([strand(self.points[cid]) for cid in self.points])


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

    return CarrierTrajectories(
        times=np.asarray(times),
        xy={cid: np.asarray(points) for cid, points in xy.items()},
        layout=layout,
        radii=gear_radii(machine, scale=scale),
    )


def default_take_off(machine: BraidingMachine, scale: float = 1.0) -> float:
    """A take-off rate that draws a braid in sensible proportions.

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
) -> YarnPaths:
    """The braid as it stands after ``n_steps`` steps, with no tension.

    See the module docstring for the model: each yarn lies over the path its
    carrier traced, lifted along the machine's axis by the braid taken off
    since.

    Args:
        machine: The machine definition.
        n_steps: How long to braid for.  If None, ``n_cycles`` full cycles of
            the machine (:func:`~braidpy.horn_gear.simulation.state_period`),
            so the braid shows its repeat that many times over; a programmed
            machine with no cycle runs its drive round that many times.
        carrier_positions: The loading; the machine's own if None.
        take_off: Length of braid drawn off per step.  Defaults to
            :func:`default_take_off`.
        n_substeps: Samples per step.
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
    if take_off <= 0:
        raise ValueError("take_off must be positive.")

    traj = carrier_trajectories(
        machine, n_steps, carrier_positions, n_substeps=n_substeps, scale=scale
    )
    heights = take_off * (traj.times[-1] - traj.times)
    points = {cid: np.column_stack([xy, heights]) for cid, xy in traj.xy.items()}
    return YarnPaths(
        times=traj.times, points=points, take_off=take_off, trajectories=traj
    )


# ── Drawing ───────────────────────────────────────────────────────────────────


def _deck_traces(
    trajectories: CarrierTrajectories, n_points: int = 72
) -> List[go.Scatter3d]:
    """The gears' outlines, on the deck at z = 0, so the yarns have a footing."""
    angles = np.linspace(0.0, 2 * np.pi, n_points)
    xs: List[Optional[float]] = []
    ys: List[Optional[float]] = []
    for name, (cx, cy) in trajectories.layout.items():
        r = trajectories.radii[name]
        xs.extend((cx + r * np.cos(angles)).tolist() + [None])
        ys.extend((cy + r * np.sin(angles)).tolist() + [None])
    return [
        go.Scatter3d(
            x=xs,
            y=ys,
            z=[0.0 if x is not None else None for x in xs],
            mode="lines",
            line=dict(color="rgba(110,110,110,0.7)", width=3),
            name="Gears",
            hoverinfo="skip",
        )
    ]


def visualize_yarns(
    machine: BraidingMachine,
    paths: Optional[YarnPaths] = None,
    output_html: Optional[str] = None,
    title: str = "Braid coming off the machine (no tension)",
    tube_diameter: Optional[float] = None,
    n_around: int = 12,
    show_deck: bool = True,
    **kwargs,
) -> go.Figure:
    """The yarns in 3D, standing on the machine that laid them.

    Each yarn is drawn in its carrier's colour — the same colours as
    :func:`~braidpy.horn_gear.visualization.animate`, so a yarn here can be
    matched to the bobbin there — and ends in a marker at the deck where its
    carrier is now.  The gears are outlined on the deck underneath, and any
    axial core stands as a column through the braid.

    Args:
        machine: The machine definition.
        paths: Yarns to draw; computed by :func:`yarn_paths` if None, which
            ``kwargs`` are then passed to.
        output_html: If given, write the figure to this HTML file.
        title: Figure title.
        tube_diameter: Draw the yarns this thick, rather than as lines.
        n_around: Points round each tube, when drawing them.
        show_deck: Outline the gears at z = 0.

    Returns:
        The figure.
    """
    from .visualization import _PALETTE

    if paths is None:
        paths = yarn_paths(machine, **kwargs)
    elif kwargs:
        raise TypeError("kwargs are only used when paths is computed here.")

    # The yarns themselves are drawn as any parametric braid is, upright,
    # sampled as finely as they were laid, in their carriers' colours.
    names = [f"Yarn C{cid}" for cid in paths.points]
    fig = paths.to_parametric_braid().figure(
        n_sample=len(paths.times),
        title=title,
        tube_diameter=tube_diameter,
        n_around=n_around,
        opacity=1.0,
        colors=_PALETTE,
        names=names,
        line_width=6,
        z_title="z (take-off)",
        flip_z=False,
    )

    traces: List[go.BaseTraceType] = []
    if show_deck:
        traces.extend(_deck_traces(paths.trajectories))

    for index, (cid, points) in enumerate(paths.points.items()):
        colour = _PALETTE[index % len(_PALETTE)]
        name = names[index]
        x0, y0, z0 = points[-1]
        traces.append(
            go.Scatter3d(
                x=[x0],
                y=[y0],
                z=[z0],
                mode="markers",
                marker=dict(size=6, color=colour, line=dict(color="white", width=1)),
                name=f"C{cid}",
                legendgroup=name,
                showlegend=False,
                hoverinfo="name",
            )
        )

    # A core runs straight up the middle of the braid laid round it.
    for axial_name, (ax, ay) in axial_positions(
        machine, paths.trajectories.layout
    ).items():
        traces.append(
            go.Scatter3d(
                x=[ax, ax],
                y=[ay, ay],
                z=[0.0, paths.length],
                mode="lines",
                line=dict(color="rgba(60,60,60,0.8)", width=10),
                name=f"Core {axial_name}",
                hoverinfo="name",
            )
        )

    fig.add_traces(traces)
    fig.update_layout(
        scene=dict(xaxis_title="x", yaxis_title="y"),
        margin=dict(l=0, r=0, b=0, t=40),
    )
    if output_html:
        fig.write_html(output_html)
    return fig
