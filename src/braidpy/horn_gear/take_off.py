# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/take_off.py
======================

The braid coming off the machine: first with no tension at all, then pulled
together at a braiding point, then tightened.

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
really comes off, but it gives the *topology* exactly — which yarn passes
which, and on which side — and a check that the machine's motion is what it
should be.

The braiding point
------------------
Real yarns run in straight lines from their carriers up to the *fell*, where
the braid is formed, at a height ``fell_height`` over the middle of the
machine.  Above the fell the braid is the machine's footprint drawn in toward
the braid's axis:

    yarn(t) = axis + k * (carrier(t) - axis),   z = fell_height + take_off * (T - t)

with ``k = fell_radius / deck_radius``.  ``k = 1`` is the extruded footprint;
``k = 0`` pulls every yarn onto the axis, a braiding point; in between the
fell is a circle of ``fell_radius``.

Scaling the plane uniformly never changes which yarn passes over which: two
yarns at the same height keep the direction between them and only come
closer, and yarns at different heights cannot meet.  So any ``k > 0`` keeps
the braid the machine made, and the question is only how far it may be drawn
in — which the yarn's thickness answers.  Given ``yarn_diameter``,
:func:`jammed_contraction` finds the smallest ``k`` at which no two yarns come
closer than a diameter: the braid as tight as uniform drawing-in can make it.

Tightening
----------
Uniform drawing-in stops at the first contact; a real braid goes on to
straighten its yarns between crossings.  :func:`tighten_yarns` does that, as
posed in *Solving a braid's shape numerically*: each yarn shortened under
tension, with every point held at its height, while no two yarns are allowed
closer than a diameter.  Steps are kept below a fraction of the diameter, so
no yarn can pass through another and the topology survives.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
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
    fell_height: float = 0.0
    fell_radius: Optional[float] = None
    axis: Tuple[float, float] = (0.0, 0.0)
    contraction: float = 1.0
    n_formed: Optional[int] = None

    @property
    def length(self) -> float:
        """How much braid has come off, measured above the fell."""
        n = self.formed_count
        return float(self.take_off * (self.times[n - 1] - self.times[0]))

    @property
    def top(self) -> float:
        """Height of the oldest yarn."""
        return self.fell_height + self.length

    @property
    def formed_count(self) -> int:
        """Points per yarn in the braid itself, above the fell.

        They come first; any after them run down from the fell to the carrier.
        """
        return len(self.times) if self.n_formed is None else self.n_formed

    def formed(self) -> np.ndarray:
        """The braid above the fell, one row per yarn; shape ``(yarns, n, 3)``.

        Every yarn is sampled at the same heights, so ``[:, i]`` is one level.
        """
        n = self.formed_count
        return np.stack([pts[:n] for pts in self.points.values()])

    def closest_approach(self) -> float:
        """The nearest two different yarns come in the braid, over its samples."""
        return _closest_approach(self.formed(), self._level_spacing())

    def _level_spacing(self) -> float:
        n = self.formed_count
        return self.take_off * float(self.times[1] - self.times[0]) if n > 1 else 0.0

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
    fell_radius: Optional[float] = None,
    yarn_diameter: Optional[float] = None,
    fell_height: Optional[float] = None,
    axis: Optional[Tuple[float, float]] = None,
    n_converge: int = 16,
) -> YarnPaths:
    """The braid as it stands after ``n_steps`` steps.

    See the module docstring for the model.  With neither ``fell_radius`` nor
    ``yarn_diameter`` each yarn lies over the path its carrier traced, lifted
    along the machine's axis by the braid taken off since.  With either, the
    yarns converge on a fell and the braid above it is drawn in toward the
    axis.

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
        fell_radius: Radius of the fell circle the braid is formed on; 0 for
            a braiding point.
        yarn_diameter: If ``fell_radius`` is not given, draw the braid in as
            far as yarns this thick allow — see :func:`jammed_contraction`.
            The samples should then be closer than a diameter apart along
            the axis (``take_off / n_substeps < yarn_diameter``), or contacts
            between them go unseen.
        fell_height: Height of the fell over the deck.  Defaults to as far
            above it as the braid is drawn in, so the yarns converge at about
            45°.
        axis: The braid's axis, in the deck plane.  Defaults to the middle of
            the gears.
        n_converge: Points along each yarn from the fell down to its carrier.

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
    if axis is None:
        centres = np.array(list(traj.layout.values()))
        axis = (float(centres[:, 0].mean()), float(centres[:, 1].mean()))
    centre = np.asarray(axis)
    rel = np.stack([xy - centre for xy in traj.xy.values()])
    deck_radius = float(np.max(np.linalg.norm(rel, axis=2)))

    if fell_radius is not None:
        if fell_radius < 0:
            raise ValueError("fell_radius must not be negative.")
        k = fell_radius / deck_radius if deck_radius > 0 else 0.0
    elif yarn_diameter is not None:
        spacing = take_off * float(traj.times[1] - traj.times[0])
        k = jammed_contraction(rel, spacing, yarn_diameter)
    else:
        k = 1.0
    converging = fell_radius is not None or yarn_diameter is not None
    if fell_height is None:
        fell_height = abs(1.0 - k) * deck_radius if converging else 0.0

    heights = fell_height + take_off * (traj.times[-1] - traj.times)
    points: Dict[CarrierId, np.ndarray] = {}
    for cid, r in zip(traj.xy, rel):
        formed = np.column_stack([centre + k * r, heights])
        if fell_height > 0:
            # Straight from the fell down to the carrier, which sits on the
            # deck where the yarn's last sample was taken.
            u = np.linspace(0.0, 1.0, n_converge + 1)[1:, None]
            deck = np.array([*traj.xy[cid][-1], 0.0])
            formed = np.vstack([formed, formed[-1] + u * (deck - formed[-1])])
        points[cid] = formed

    n_formed = len(traj.times)
    times = np.concatenate(
        [
            traj.times,
            np.full(len(points[next(iter(points))]) - n_formed, traj.times[-1]),
        ]
    )
    return YarnPaths(
        times=times,
        points=points,
        take_off=take_off,
        trajectories=traj,
        fell_height=fell_height,
        fell_radius=k * deck_radius if converging else None,
        axis=(float(centre[0]), float(centre[1])),
        contraction=k,
        n_formed=n_formed,
    )


# ── Contact between yarns ─────────────────────────────────────────────────────
#
# Every yarn is sampled at the same heights, so two samples can be closer than
# a diameter only if they are fewer than ``diameter / spacing`` levels apart.
# Comparing every yarn against every other at each such offset finds every
# close pair without a spatial index.


def _level_pairs(n_yarns: int, offset: int) -> Tuple[np.ndarray, np.ndarray]:
    """Yarn index pairs to compare at a level offset, each unordered pair once."""
    a, b = np.meshgrid(np.arange(n_yarns), np.arange(n_yarns), indexing="ij")
    keep = a < b if offset == 0 else a != b
    return a[keep], b[keep]


def _offsets(spacing: float, diameter: float, n: int) -> range:
    """Level offsets at which two samples can still be within a diameter."""
    if spacing <= 0:
        return range(1)
    return range(min(n, int(math.ceil(diameter / spacing))))


def _closest_approach(formed: np.ndarray, spacing: float) -> float:
    """Smallest distance between samples of two different yarns."""
    n_yarns, n, _ = formed.shape
    if n_yarns < 2:
        return math.inf
    best = math.inf
    offset = 0
    while offset < n and offset * spacing < best:
        a, b = _level_pairs(n_yarns, offset)
        diff = formed[a, : n - offset] - formed[b, offset:]
        best = min(best, float(np.sqrt(np.min(np.sum(diff**2, axis=-1)))))
        offset += 1
    return best


def jammed_contraction(rel: np.ndarray, spacing: float, diameter: float) -> float:
    """How far a braid can be drawn in before two yarns touch.

    Drawing the plane in by ``k`` shrinks the sideways part of every distance
    by ``k`` and leaves the height part alone, so a pair of samples a height
    ``dz`` apart and ``s`` apart sideways touches when
    ``k = sqrt(d² - dz²) / s``.  The braid jams at the largest of these — an
    exact answer over the samples, with no search.

    Args:
        rel: Per yarn, its samples relative to the axis; shape ``(yarns, n, 2)``,
            every yarn at the same heights.
        spacing: Height between successive samples.
        diameter: Yarn diameter.

    Returns:
        The contraction ``k``; above 1 if the yarns do not fit even undrawn.

    Raises:
        ValueError: If two yarns pass through the same place too close in
            height for any drawing-in to separate them — the take-off is too
            slow for yarns this thick.
    """
    if diameter <= 0:
        raise ValueError("yarn_diameter must be positive.")
    n_yarns, n, _ = rel.shape
    k = 0.0
    for offset in _offsets(spacing, diameter, n):
        a, b = _level_pairs(n_yarns, offset)
        if len(a) == 0:
            break
        sideways = np.linalg.norm(rel[a, : n - offset] - rel[b, offset:], axis=-1)
        room = diameter**2 - (offset * spacing) ** 2
        if np.any(sideways == 0):
            raise ValueError(
                "Two yarns pass the same point too close together in height to "
                "be separated: increase take_off or reduce yarn_diameter."
            )
        k = max(k, float(np.sqrt(room) / np.min(sideways)))
    return k


def tighten_yarns(
    paths: YarnPaths,
    yarn_diameter: float,
    iterations: int = 400,
    stiffness: float = 0.5,
    core_radius: Optional[float] = None,
    tolerance: float = 1e-3,
) -> Tuple[YarnPaths, Dict[str, List[float]]]:
    """Pull the yarns taut above the fell, without letting them overlap.

    Each iteration shortens every yarn — each sample moves toward the middle of
    its two neighbours, sideways only, so it keeps its height — then pushes
    apart any two samples of different yarns closer than a diameter, until
    none are.  The ends stay where they are: the oldest yarn, and the fell
    where the yarn arrives from its carrier.

    Shortening at fixed height is the length objective of *Solving a braid's
    shape numerically* in its small-slope form, and the push is its
    non-interpenetration constraint.  No sample moves more than a fifth of a
    diameter in one go, so a yarn cannot jump through another and the braid
    the machine made is the braid that comes out.

    Start it from a braid already drawn in (``yarn_diameter`` given to
    :func:`yarn_paths`): tension alone draws a braid in only very slowly.

    Args:
        paths: The braid to tighten.
        yarn_diameter: Yarn diameter.
        iterations: Shortening steps.
        stiffness: Fraction of the way to its neighbours' middle a sample moves
            per step, 0 to 1.
        core_radius: Keep the yarns outside a core of this radius round the
            axis, for a braid laid over one.
        tolerance: Overlap, as a fraction of the diameter, that the contact
            push accepts.

    Returns:
        The tightened braid, and its history: ``"length"``, the total yarn
        length above the fell, and ``"closest"``, the closest approach, after
        each iteration.
    """
    if yarn_diameter <= 0:
        raise ValueError("yarn_diameter must be positive.")
    if not 0 < stiffness <= 1:
        raise ValueError("stiffness must be in (0, 1].")

    formed = paths.formed().copy()
    n_yarns, n, _ = formed.shape
    spacing = paths._level_spacing()
    offsets = list(_offsets(spacing, yarn_diameter, n))
    max_move = yarn_diameter / 5
    slack = tolerance * yarn_diameter
    centre = np.asarray(paths.axis)
    # One row per sample, yarn after yarn: sample i of yarn a is row a * n + i.
    xy = formed[:, :, :2].reshape(-1, 2)
    level = np.tile(np.arange(n), n_yarns)
    held = (level == 0) | (level == n - 1)

    def clamp(move: np.ndarray) -> np.ndarray:
        size = np.linalg.norm(move, axis=-1, keepdims=True)
        return move * np.minimum(1.0, max_move / np.maximum(size, 1e-300))

    def neighbours() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """Pairs of samples that could touch before the list is rebuilt.

        Every pair within a diameter of touching.  The list is rebuilt once
        any sample has moved half a diameter since it was built, so no pair
        left off it can have come into contact in between.
        """
        first, second, needs, rises = [], [], [], []
        grid = np.arange(n * n_yarns).reshape(n_yarns, n)
        for o in offsets:
            a, b = _level_pairs(n_yarns, o)
            if len(a) == 0:
                continue
            need = math.sqrt(max(yarn_diameter**2 - (o * spacing) ** 2, 0.0))
            p, q = grid[a, : n - o].ravel(), grid[b, o:].ravel()
            close = np.linalg.norm(xy[p] - xy[q], axis=-1) < need + yarn_diameter
            first.append(p[close])
            second.append(q[close])
            needs.append(np.full(int(close.sum()), need))
            rises.append(np.full(int(close.sum()), o * spacing))
        if not first:
            empty = np.zeros(0)
            return empty.astype(int), empty.astype(int), empty, empty
        return (
            np.concatenate(first),
            np.concatenate(second),
            np.concatenate(needs),
            np.concatenate(rises),
        )

    def separate(p: np.ndarray, q: np.ndarray, need: np.ndarray) -> None:
        for _ in range(50):
            push = np.zeros_like(xy)
            worst = 0.0
            if len(p):
                diff = xy[p] - xy[q]
                dist = np.linalg.norm(diff, axis=-1)
                short = need - dist
                hit = short > slack
                if np.any(hit):
                    worst = float(np.max(short[hit]))
                    unit = diff[hit] / np.maximum(dist[hit], 1e-300)[:, None]
                    half = 0.5 * short[hit, None] * unit
                    np.add.at(push, p[hit], half)
                    np.add.at(push, q[hit], -half)
            if core_radius is not None:
                rel = xy - centre
                r = np.linalg.norm(rel, axis=-1)
                inner = core_radius + yarn_diameter / 2
                low = r < inner
                if np.any(low):
                    worst = max(worst, float(np.max(inner - r[low])))
                    unit = rel[low] / np.maximum(r[low], 1e-300)[:, None]
                    push[low] += unit * (inner - r[low])[:, None]
            if worst <= slack:
                return
            push[held] = 0.0
            xy[:] += clamp(push)

    def closest(p: np.ndarray, q: np.ndarray, rise: np.ndarray) -> float:
        if not len(p):
            return math.inf
        sideways = np.sum((xy[p] - xy[q]) ** 2, axis=-1)
        return float(np.sqrt(np.min(sideways + rise**2)))

    def total_length() -> float:
        return float(np.sum(np.linalg.norm(np.diff(formed, axis=1), axis=-1)))

    history: Dict[str, List[float]] = {"length": [], "closest": []}
    p, q, need, rise = neighbours()
    built = xy.copy()
    separate(p, q, need)
    inner = ~held
    for _ in range(iterations):
        middle = 0.5 * (np.roll(xy, 1, axis=0) + np.roll(xy, -1, axis=0))
        xy[inner] += clamp(stiffness * (middle[inner] - xy[inner]))
        separate(p, q, need)
        # The push itself can carry a sample out of the list's reach, so the
        # check comes after it, and a rebuilt list is pushed against again.
        while np.max(np.linalg.norm(xy - built, axis=-1)) > yarn_diameter / 4:
            p, q, need, rise = neighbours()
            built = xy.copy()
            separate(p, q, need)
        history["length"].append(total_length())
        history["closest"].append(closest(p, q, rise))

    points = {}
    for row, (cid, pts) in zip(formed, paths.points.items()):
        points[cid] = np.vstack([row, pts[n:]])
    return replace(paths, points=points), history


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
    title: Optional[str] = None,
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
        title: Figure title; says which model the yarns follow if None.
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
                z=[0.0, paths.top],
                mode="lines",
                line=dict(color="rgba(60,60,60,0.8)", width=10),
                name=f"Core {axial_name}",
                hoverinfo="name",
            )
        )

    # The fell, where the converging yarns become braid.
    if paths.fell_height > 0 and paths.fell_radius is not None:
        angles = np.linspace(0.0, 2 * np.pi, 73)
        ax, ay = paths.axis
        traces.append(
            go.Scatter3d(
                x=ax + paths.fell_radius * np.cos(angles),
                y=ay + paths.fell_radius * np.sin(angles),
                z=np.full_like(angles, paths.fell_height),
                mode="lines" if paths.fell_radius > 0 else "markers",
                line=dict(color="black", width=4),
                marker=dict(color="black", size=5),
                name="Fell" if paths.fell_radius > 0 else "Braiding point",
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
