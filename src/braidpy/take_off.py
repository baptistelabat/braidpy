# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
take_off.py
===========

A braid as it comes off whatever made it: laid, drawn in, and tightened.

Everything here works from one thing only — where each strand's carrier was,
in a plane, over time (:class:`StrandTrajectories`).  A horn gear machine,
a braid word, a kumihimo disk: each says where its strands go, and from then
on the braid is made the same way.

- :func:`~braidpy.horn_gear.take_off.carrier_trajectories` follows the bobbins
  of a horn gear machine.
- :func:`parametric_trajectories` reads a
  :class:`~braidpy.parametric_braid.ParametricBraid`, and
  :func:`braid_word_trajectories` a braid word through it — so anything that
  produces a word, kumihimo included, can be laid.
- :func:`disk_trajectories` moves strands between the slots of a disk, and
  :func:`mobidai_trajectories` and :func:`kumihimo_trajectories` read a
  mobidai or a kumihimo sequence into it — the motion, for animating.  For
  the braid itself, :func:`mobidai_braid` and :func:`kumihimo_braid` keep
  only the crossings the moves make and lay them round a ring
  (:func:`disk_braid`): where a disk's strands wait is not where a braid
  holds them.

Laying
------
The braid is drawn off along the axis square to that plane at a steady rate,
and a yarn is taken to stay where its carrier put it.  The piece laid at time
``t`` sits over the point the carrier occupied then, carried up by the braid
taken off since:

    yarn(t) = (x(t), y(t), take_off * (T - t))

for a braid observed at time ``T``.  That gets the *topology* exactly: which
yarn passes which, and on which side.

The fell
--------
Real yarns run straight from their carriers up to the *fell*, where the braid
forms, at ``fell_height``.  Above it each level of the braid is the carriers'
footprint drawn in toward the axis by a factor ``k``: the fell's own size at
the fell (``k = 0`` is a braiding point), and away from it as tight as the
yarn allows (:func:`jammed_contraction`).  Any positive ``k`` at each level
keeps which yarn passes over which, so the braid made is the braid kept.

Tightening
----------
:func:`tighten_yarns` then shortens every yarn under tension, keeping every
point at its height and no two yarns closer than a diameter — the problem of
*Solving a braid's shape numerically*.  Far from the fell the braid settles to
the shape its yarns pull it into, whatever the fell started it as.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import (
    TYPE_CHECKING,
    Collection,
    Dict,
    Hashable,
    List,
    Mapping,
    Optional,
    Sequence,
    Tuple,
)

import numpy as np
from braidpy.utils import lazy_module

if TYPE_CHECKING:
    import plotly.graph_objects as go
else:
    go = lazy_module("plotly.graph_objects")


@dataclass(frozen=True)
class StrandTrajectories:
    """Where every strand's carrier went, sampled over time.

    This is all the rest of the module needs: a braid is laid from it, drawn
    in and tightened without knowing what made it.

    Args:
        times: Time of each sample, evenly spaced; shape ``(n,)``.  The units
            are whatever the source counts in — machine steps, moves, or the
            0 to 1 of a parametric strand — and ``take_off`` is per unit.
        xy: Per strand, its position in the plane at each of those times;
            shape ``(n, 2)``.
        outlines: Closed curves to draw on the plane under the braid — the
            gears, a disk's rim — each of shape ``(m, 2)``.
        axis: The braid's axis in the plane, if the source knows where it is;
            the middle of the samples otherwise.
        label: Prefix naming a strand in a drawing, followed by its key.
        outline_name: What the outlines are, in a drawing's legend.
        slots: Named places in the plane to mark in a drawing — a disk's
            slots — as ``(x, y, name)``.
    """

    times: np.ndarray
    xy: Dict[Hashable, np.ndarray]
    outlines: Tuple[np.ndarray, ...] = ()
    axis: Optional[Tuple[float, float]] = None
    label: str = "Yarn "
    outline_name: str = "Deck"
    slots: Tuple[Tuple[float, float, str], ...] = ()

    def __post_init__(self) -> None:
        if len(self.times) < 2:
            raise ValueError("Trajectories need at least two samples.")
        steps = np.diff(self.times)
        if np.any(steps <= 0) or not np.allclose(steps, steps[0]):
            raise ValueError("Trajectory samples must be evenly spaced in time.")
        for key, xy in self.xy.items():
            if np.shape(xy) != (len(self.times), 2):
                raise ValueError(f"Strand {key!r}: expected {len(self.times)} (x, y).")

    def centre(self) -> Tuple[float, float]:
        """The braid's axis: the source's, or the middle of every sample."""
        if self.axis is not None:
            return self.axis
        every = np.concatenate(list(self.xy.values()))
        return float(every[:, 0].mean()), float(every[:, 1].mean())


@dataclass(frozen=True)
class YarnPaths:
    """The yarns of a braid, as they stand at one instant.

    Args:
        times: When each point of a yarn was laid, in the trajectories' units; shape ``(n,)``.
        points: Per strand, its yarn's centreline; shape ``(n, 3)``, in the
            same order as ``times``, so the last point is the one at the deck, where the yarn leaves its carrier.
        take_off: Length of braid drawn off per unit of time.
        trajectories: The strand motion the yarns were laid from.
        fell_height: Height of the fell over the deck; 0 if the yarns do not
            converge on one.
        fell_radius: Radius of the fell, 0 for a braiding point; None if the
            yarns do not converge.
        axis: The braid's axis, in the deck plane.
        contraction: How far the braid itself is drawn in, away from the fell.
        n_formed: Points per yarn above the fell; all of them if None.
        yarn_diameter: The yarn's thickness, if the braid was made for one;
            it is then drawn that thick.
    """

    times: np.ndarray
    points: Dict[Hashable, np.ndarray]
    take_off: float
    trajectories: "StrandTrajectories"
    fell_height: float = 0.0
    fell_radius: Optional[float] = None
    axis: Tuple[float, float] = (0.0, 0.0)
    contraction: float = 1.0
    n_formed: Optional[int] = None
    yarn_diameter: Optional[float] = None

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

    def closest_approach(self, include_fell: bool = True) -> float:
        """The nearest two different yarns come in the braid, over its samples.

        Args:
            include_fell: Count the fell itself.  At a braiding point every
                yarn meets there, so the answer is 0 unless it is left out.
        """
        formed = self.formed()
        if not include_fell:
            formed = formed[:, :-1]
        return _closest_approach(formed, self._level_spacing())

    def _level_spacing(self) -> float:
        n = self.formed_count
        return self.take_off * float(self.times[1] - self.times[0]) if n > 1 else 0.0

    def to_parametric_braid(self):
        """The same yarns as a :class:`~braidpy.parametric_braid.ParametricBraid`.

        Each strand is parametrised from the deck (0) to the oldest yarn (1),
        and interpolated linearly between samples, so the drawing and the
        measuring done on parametric braids apply here too.

        Returns:
            ParametricBraid: One strand per yarn, in order.
        """
        from braidpy.parametric_braid import ParametricBraid
        from braidpy.parametric_strand import ParametricStrand

        def strand(points: np.ndarray) -> ParametricStrand:
            path = points[::-1]
            s = np.linspace(0.0, 1.0, len(path))

            def func(u: float) -> Tuple[float, float, float]:
                x, y, z = (float(np.interp(u, s, path[:, i])) for i in range(3))
                return x, y, z

            return ParametricStrand(func)

        return ParametricBraid([strand(self.points[cid]) for cid in self.points])


def default_take_off(trajectories: StrandTrajectories) -> float:
    """A take-off rate that draws a braid in sensible proportions.

    The strands' mean speed across the plane: a yarn then rises about as fast
    as it travels sideways, so it leaves at roughly 45°, near the angle a
    braid is usually made at.  It sets only how stretched the picture is —
    nothing about which yarn crosses which depends on it.
    """
    duration = float(trajectories.times[-1] - trajectories.times[0])
    travel = [
        float(np.sum(np.linalg.norm(np.diff(xy, axis=0), axis=1)))
        for xy in trajectories.xy.values()
    ]
    speed = sum(travel) / len(travel) / duration
    if speed > 0:
        return speed
    # Nothing moves: fall back on the braid's size, so a picture still comes out.
    every = np.concatenate(list(trajectories.xy.values()))
    return float(np.ptp(every, axis=0).max() or 1.0) / duration


def lay_yarns(
    trajectories: StrandTrajectories,
    take_off: Optional[float] = None,
    fell_radius: Optional[float] = None,
    yarn_diameter: Optional[float] = None,
    fell_height: Optional[float] = None,
    axis: Optional[Tuple[float, float]] = None,
    n_converge: int = 16,
    settle_length: Optional[float] = None,
) -> YarnPaths:
    """The braid laid from these trajectories, as it stands at their last sample.

    With neither ``fell_radius`` nor ``yarn_diameter`` each yarn lies over the
    path its carrier traced, lifted along the axis by the braid taken off
    since.  With either, the yarns converge on a fell and the braid above it
    is drawn in toward the axis.  With both, the fell is only where the braid
    starts: it opens out — or closes in — to as tight as the yarn allows over
    ``settle_length`` of take-off, and :func:`tighten_yarns` takes it from
    there.

    Args:
        trajectories: Where the strands went.
        take_off: Length of braid drawn off per unit of time.  Defaults to
            :func:`default_take_off`.
        fell_radius: Radius of the fell circle the braid is formed on; 0 for
            a braiding point.
        yarn_diameter: Draw the braid in as far as yarns this thick allow —
            see :func:`jammed_contraction` — away from the fell, and at the
            fell too if ``fell_radius`` is not given.  The samples should then
            be closer than a diameter apart along the axis, or contacts
            between them go unseen.
        fell_height: Height of the fell over the plane.  Defaults to as far
            above it as the braid is drawn in, so the yarns converge at about
            45°.
        axis: The braid's axis, in the plane.  Defaults to the trajectories'.
        n_converge: Points along each yarn from the fell down to its carrier.
        settle_length: Take-off over which the braid goes from the fell's size
            to its own, when both ``fell_radius`` and ``yarn_diameter`` are
            given.  Defaults to twice the difference in radius.

    Returns:
        The yarns, one per strand.
    """
    traj = trajectories
    if take_off is None:
        take_off = default_take_off(traj)
    if take_off <= 0:
        raise ValueError("take_off must be positive.")
    if axis is None:
        axis = traj.centre()
    centre = np.asarray(axis, dtype=float)
    rel = np.stack([xy - centre for xy in traj.xy.values()])
    deck_radius = float(np.max(np.linalg.norm(rel, axis=2)))
    if yarn_diameter is not None:
        spacing = take_off * float(traj.times[1] - traj.times[0])
        k = jammed_contraction(rel, spacing, yarn_diameter)
    else:
        k = 1.0
    if fell_radius is not None:
        if fell_radius < 0:
            raise ValueError("fell_radius must not be negative.")
        k_fell = fell_radius / deck_radius if deck_radius > 0 else 0.0
        if yarn_diameter is None:
            k = k_fell
    else:
        k_fell = k
    converging = fell_radius is not None or yarn_diameter is not None
    if fell_height is None:
        fell_height = abs(1.0 - k_fell) * deck_radius if converging else 0.0

    above = take_off * (traj.times[-1] - traj.times)
    heights = fell_height + above
    # How far each level is drawn in: the fell's own size at the fell, the
    # braid's beyond ``settle_length``, and a smooth step between.  Any
    # positive scale at each level leaves the braid the machine made, so the
    # step can be any shape at all.
    if settle_length is None:
        settle_length = 2 * abs(k - k_fell) * deck_radius
    u = (
        np.clip(above / settle_length, 0.0, 1.0)
        if settle_length > 0
        else np.ones_like(above)
    )
    level_k = k_fell + (k - k_fell) * (3 * u**2 - 2 * u**3)
    points: Dict[Hashable, np.ndarray] = {}
    for cid, r in zip(traj.xy, rel):
        formed = np.column_stack([centre + level_k[:, None] * r, heights])
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
        fell_radius=k_fell * deck_radius if converging else None,
        axis=(float(centre[0]), float(centre[1])),
        contraction=k,
        n_formed=n_formed,
        yarn_diameter=yarn_diameter,
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
        room = diameter**2 - (offset * spacing) ** 2
        if offset * spacing >= diameter * (1 - 1e-9):
            # A diameter or more apart in height: they cannot touch.
            break
        sideways = np.linalg.norm(rel[a, : n - offset] - rel[b, offset:], axis=-1)
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
    step: float = 20.0,
    core_radius: Optional[float] = None,
    tolerance: float = 1e-3,
    hold_top: bool = True,
    rigid: Collection[Hashable] = (),
) -> Tuple[YarnPaths, Dict[str, List[float]]]:
    """Pull the yarns taut above the fell, without letting them overlap.

    Each iteration shortens every yarn, sideways only, so every sample keeps
    its height; then it pushes apart any two samples of different yarns closer
    than a diameter, until none are.  The yarn is held where it arrives at the
    fell from its carrier, and at its oldest end, where the take-off holds it.
    Between the two, far enough from the fell, the braid takes the shape its
    yarns pull it into, whatever shape the fell started it in.

    Shortening at fixed height is the length objective of *Solving a braid's
    shape numerically* in its small-slope form — tension pulls a yarn toward
    the middle of its neighbours — and the push is its non-interpenetration
    constraint.  The tension is taken implicitly, as a backward-Euler step of
    ``step`` along that flow, which settles a whole yarn in a few dozen
    iterations where moving each sample toward its neighbours would take
    thousands.  No sample moves more than a fifth of a diameter in one go,
    though, so a yarn cannot jump through another and the braid the machine
    made is the braid that comes out.

    Args:
        paths: The braid to tighten.
        yarn_diameter: Yarn diameter.
        iterations: Shortening steps.
        step: How far along the tension flow each step goes, in units where
            1 moves a sample half way to its neighbours' middle.
        core_radius: Keep the yarns outside a core of this radius round the
            axis, for a braid laid over one.
        tolerance: Overlap, as a fraction of the diameter, that the contact
            push accepts.
        hold_top: Hold the oldest end where it is, as the take-off does.  Left
            free, the end can turn about the axis and untwist the braid.
        rigid: Yarns held where they are all along, as stiff cores: the
            others are pushed off them, and they never move.

    Returns:
        The tightened braid, and its history: ``"length"``, the total yarn
        length above the fell, and ``"closest"``, the closest approach, after
        each iteration.
    """
    if yarn_diameter <= 0:
        raise ValueError("yarn_diameter must be positive.")
    if step <= 0:
        raise ValueError("step must be positive.")

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
    held = (level == n - 1) | ((level == 0) & hold_top)
    held |= np.repeat([k in set(rigid) for k in paths.points], n)

    # Backward Euler on the tension: (I + step * L) x_new = x, with L the
    # second difference along a yarn — the fell end fixed, the top end fixed
    # or free.  Every yarn shares the matrix, so it is inverted once.
    lap = np.zeros((n, n))
    for i in range(1, n - 1):
        lap[i, i - 1 : i + 2] = (-1.0, 2.0, -1.0)
    if not hold_top and n > 1:
        lap[0, :2] = (1.0, -1.0)
    settle = np.linalg.inv(np.eye(n) + 0.5 * step * lap)

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
                    gap = short[hit, None] * unit
                    # Shared between the two, or all to the one that is free
                    # to move when the other is held at the fell.
                    share = (free[p[hit]] / (free[p[hit]] + free[q[hit]]))[:, None]
                    np.add.at(push, p[hit], share * gap)
                    np.add.at(push, q[hit], -(1 - share) * gap)
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

    # A pair of held samples cannot be pushed apart — at a braiding point the
    # yarns all meet there — so contact is only looked for where one of the
    # two is free to move.
    free = (~held).astype(float)

    def movable(pairs):
        p, q, need, rise = pairs
        keep = (free[p] + free[q]) > 0
        return p[keep], q[keep], need[keep], rise[keep]

    def total_length() -> float:
        return float(np.sum(np.linalg.norm(np.diff(formed, axis=1), axis=-1)))

    history: Dict[str, List[float]] = {"length": [], "closest": []}
    p, q, need, rise = movable(neighbours())
    built = xy.copy()
    separate(p, q, need)
    inner = ~held
    for _ in range(iterations):
        lines = xy.reshape(n_yarns, n, 2).transpose(1, 0, 2).reshape(n, -1)
        target = (settle @ lines).reshape(n, n_yarns, 2).transpose(1, 0, 2)
        move = target.reshape(-1, 2) - xy
        xy[inner] += clamp(move[inner])
        separate(p, q, need)
        # The push itself can carry a sample out of the list's reach, so the
        # check comes after it, and a rebuilt list is pushed against again.
        while np.max(np.linalg.norm(xy - built, axis=-1)) > yarn_diameter / 4:
            p, q, need, rise = movable(neighbours())
            built = xy.copy()
            separate(p, q, need)
        history["length"].append(total_length())
        history["closest"].append(closest(p, q, rise))

    points = {}
    for row, (cid, pts) in zip(formed, paths.points.items()):
        points[cid] = np.vstack([row, pts[n:]])
    return replace(paths, points=points, yarn_diameter=yarn_diameter), history


# ── Drawing ───────────────────────────────────────────────────────────────────


def _outline_traces(trajectories: StrandTrajectories) -> List[go.Scatter3d]:
    """The source's outlines on the plane at z = 0, so the yarns have a footing."""
    if not trajectories.outlines:
        return []
    xs: List[Optional[float]] = []
    ys: List[Optional[float]] = []
    for outline in trajectories.outlines:
        xs.extend(outline[:, 0].tolist() + [None])
        ys.extend(outline[:, 1].tolist() + [None])
    return [
        go.Scatter3d(
            x=xs,
            y=ys,
            z=[0.0 if x is not None else None for x in xs],
            mode="lines",
            line=dict(color="rgba(110,110,110,0.7)", width=3),
            name=trajectories.outline_name,
            hoverinfo="skip",
        )
    ]


def visualize_yarns(
    paths: YarnPaths,
    output_html: Optional[str] = None,
    title: Optional[str] = None,
    tube_diameter: Optional[float] = None,
    n_around: int = 12,
    show_deck: bool = True,
    colors: Optional[Sequence[str]] = None,
    extra_traces: Sequence[go.BaseTraceType] = (),
) -> go.Figure:
    """The yarns in 3D, standing on whatever laid them.

    Each yarn ends in a marker at the plane, where its carrier is now; the
    source's outlines are drawn there, and the fell or braiding point where
    the yarns meet.

    Args:
        paths: The yarns to draw.
        output_html: If given, write the figure to this HTML file.
        title: Figure title; says which model the yarns follow if None.
        tube_diameter: Draw the yarns as tubes this thick.  Defaults to the
            yarn diameter the braid was made for, if any; 0 draws lines.
        n_around: Points round each tube, when drawing them.
        show_deck: Draw the source's outlines at z = 0.
        colors: One colour per yarn, cycled; the horn gear animation's if None,
            so a yarn can be matched to its bobbin there.
        extra_traces: Anything else to draw in the same scene.

    Returns:
        The figure.
    """
    if colors is None:
        from braidpy.horn_gear.visualization import _PALETTE

        colors = _PALETTE

    if title is None:
        if paths.fell_radius is None:
            title = "Braid as laid (no tension)"
        elif paths.fell_radius == 0:
            title = "Braid formed at a braiding point"
        else:
            title = f"Braid formed on a fell of radius {paths.fell_radius:.3g}"

    if tube_diameter is None:
        tube_diameter = paths.yarn_diameter
    if not tube_diameter:
        tube_diameter = None

    # The yarns themselves are drawn as any parametric braid is, upright,
    # sampled as finely as they were laid.
    label = paths.trajectories.label
    names = [f"{label}{key}" for key in paths.points]
    fig = paths.to_parametric_braid().figure(
        n_sample=len(paths.times),
        title=title,
        tube_diameter=tube_diameter,
        n_around=n_around,
        opacity=1.0,
        colors=colors,
        names=names,
        line_width=6,
        z_title="z (take-off)",
        flip_z=False,
    )

    traces: List[go.BaseTraceType] = []
    if show_deck:
        traces.extend(_outline_traces(paths.trajectories))

    for index, (key, points) in enumerate(paths.points.items()):
        x0, y0, z0 = points[-1]
        traces.append(
            go.Scatter3d(
                x=[x0],
                y=[y0],
                z=[z0],
                mode="markers",
                marker=dict(
                    size=6,
                    color=colors[index % len(colors)],
                    line=dict(color="white", width=1),
                ),
                name=str(key),
                legendgroup=names[index],
                showlegend=False,
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

    traces.extend(extra_traces)
    fig.add_traces(traces)
    fig.update_layout(
        scene=dict(xaxis_title="x", yaxis_title="y"),
        margin=dict(l=0, r=0, b=0, t=40),
    )
    if output_html:
        fig.write_html(output_html)
    return fig


# ── Sources: where strands go ─────────────────────────────────────────────────


def parametric_trajectories(
    braid,
    n_samples: int = 400,
    label: str = "Strand ",
) -> StrandTrajectories:
    """The strands of a parametric braid, as trajectories to lay.

    A :class:`~braidpy.parametric_strand.ParametricStrand` is a curve
    ``γ(t) = (x, y, z)`` for ``t`` from 0 to 1.  Its ``(x, y)`` is taken as
    where its carrier was at time ``t``, so the strand drawn first is laid
    first and ends up highest, as ``ParametricBraid.plot`` draws it — over and
    under come from ``y``, as they do there.

    Args:
        braid: A :class:`~braidpy.parametric_braid.ParametricBraid`, or a
            sequence of strands.
        n_samples: Samples along each strand.
        label: Prefix naming a strand in a drawing.

    Returns:
        The trajectories, over times 0 to 1.
    """
    strands = getattr(braid, "strands", braid)
    if n_samples < 2:
        raise ValueError("n_samples must be at least 2.")
    times = np.linspace(0.0, 1.0, n_samples)
    xy: Dict[Hashable, np.ndarray] = {
        index: np.array([strand.evaluate(float(t))[:2] for t in times])
        for index, strand in enumerate(strands)
    }
    return StrandTrajectories(times=times, xy=xy, label=label)


def braid_word_trajectories(
    braid,
    samples_per_crossing: int = 24,
    spacing: float = 1.0,
    lift: float = 0.5,
) -> StrandTrajectories:
    """A braid word's strands, as trajectories to lay.

    The strands stand in a row ``spacing`` apart, and a crossing swaps two
    neighbours, the one going over lifted ``lift * spacing`` to one side and
    the one going under to the other — the drawing of
    :meth:`~braidpy.braid.Braid.to_parametric_strands`.  Anything that makes
    a braid word can therefore be laid, tightened and drawn: a kumihimo
    sequence, a catalogue braid, or a word read off a machine.

    Args:
        braid: A :class:`~braidpy.braid.Braid`, or its generators as signed
            integers.
        samples_per_crossing: Samples per generator.
        spacing: Distance between neighbouring strands.
        lift: How far a crossing strand moves off the row, as a fraction of
            ``spacing``.

    Returns:
        The trajectories, over times 0 to 1.
    """
    from braidpy.braid import Braid

    if not isinstance(braid, Braid):
        braid = Braid(tuple(braid))
    strands = braid.to_parametric_strands(amplitude=1.0)
    n_segments = len(braid.generators) + 1
    traj = parametric_trajectories(
        strands, n_samples=samples_per_crossing * n_segments + 1
    )
    # Drawn with the row and the lift both one unit; stretch each to size.
    stretch = np.array([spacing, lift * spacing])
    return replace(traj, xy={k: xy * stretch for k, xy in traj.xy.items()})


def _disk_point(
    slot: np.ndarray,
    radius: np.ndarray,
    n_slots: int,
    clockwise: bool,
    slot_offset: float = 0.0,
):
    """Where slot ``slot`` (1-based, may be fractional) is on a disk.

    Slot 1 at the top, counting clockwise or not — the mobidai's drawing —
    unless ``slot_offset`` turns the numbering round by that many slots.
    """
    angle = 2 * np.pi * (slot - 1 + slot_offset) / n_slots * (1 if clockwise else -1)
    return np.column_stack([radius * np.sin(angle), radius * np.cos(angle)])


def disk_trajectories(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
    radius: float = 1.0,
    lift: float = 0.15,
    samples_per_step: int = 12,
    clockwise: bool = True,
    label: str = "Strand ",
    slot_offset: float = 0.0,
    slot_names: Optional[Mapping[int, str]] = None,
) -> StrandTrajectories:
    """Strands moved between the slots round a disk, as trajectories to lay.

    This is how a kumihimo disk or a mobidai is worked: each step moves some
    strands round the rim by a number of slots — positive toward higher slot
    numbers — and a step that moves every strand alike is the disk itself
    turning.

    A strand that moves while others stay is lifted over the ones it passes —
    over as seen from above the disk, the side the braider works from, with
    the braid going down through the middle.  Over is therefore *inside*: the
    moving strand travels round inside the rim, a ``lift`` fraction of the
    radius in, and comes back out to its new slot.  Read in slot order with
    inside as over, that gives the crossings the mobidai's own braid word
    records on a clockwise disk — a move toward higher slots crosses over,
    positively.

    That is the opposite way round from :mod:`braidpy.annulus_braid`, which
    looks at a tube from outside, where over is outside.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots.
        n_slots: Slots round the disk.
        radius: The disk's radius.
        lift: How far in a moving strand travels, as a fraction of the radius.
        samples_per_step: Samples per step.
        clockwise: Whether slot numbers go round clockwise, seen from above.
        label: Prefix naming a strand in a drawing.
        slot_offset: Slots the numbering is turned by, so slot 1 sits that far
            round from the top.  A kumihimo disk marks the top between its
            last slot and slot 1: half a slot.
        slot_names: What to call each slot that is marked, by slot number;
            every slot by its number if None.

    Returns:
        The trajectories, one unit of time per step.

    Raises:
        ValueError: If a strand is not on a slot, or a step leaves two strands
            in one slot.
    """
    if samples_per_step < 1:
        raise ValueError("samples_per_step must be at least 1.")
    keys = list(start)
    where = {k: float(start[k]) for k in keys}
    for key, slot in where.items():
        if not 1 <= slot <= n_slots or slot != int(slot):
            raise ValueError(f"Strand {key!r} is not on a slot: {slot}.")
    if len(set(where.values())) < len(where):
        raise ValueError("Two strands start in the same slot.")

    slots: Dict[Hashable, List[float]] = {k: [] for k in keys}
    rims: Dict[Hashable, List[float]] = {k: [] for k in keys}
    fractions = np.arange(samples_per_step) / samples_per_step
    for number, step in enumerate(steps):
        unknown = set(step) - set(keys)
        if unknown:
            raise ValueError(f"Step {number} moves unknown strands {unknown}.")
        turning = set(step) == set(keys) and len(set(step.values())) == 1
        for key in keys:
            delta = float(step.get(key, 0))
            slots[key].extend(where[key] + delta * fractions)
            inward = 0.0 if turning or delta == 0 else lift
            rims[key].extend(radius * (1 - inward * np.sin(np.pi * fractions)))
            where[key] = (where[key] + delta - 1) % n_slots + 1
        if len({round(s) for s in where.values()}) < len(where):
            raise ValueError(f"Step {number} leaves two strands in one slot.")
    for key in keys:
        slots[key].append(where[key])
        rims[key].append(radius)

    times = np.arange(len(steps) * samples_per_step + 1) / samples_per_step
    xy = {
        k: _disk_point(
            np.array(slots[k]), np.array(rims[k]), n_slots, clockwise, slot_offset
        )
        for k in keys
    }
    rim = _disk_point(
        np.linspace(1, n_slots + 1, 4 * n_slots + 1),
        np.full(4 * n_slots + 1, radius),
        n_slots,
        clockwise,
        slot_offset,
    )
    if slot_names is None:
        slot_names = {slot: str(slot) for slot in range(1, n_slots + 1)}
    numbered = sorted(slot_names)
    marks = _disk_point(
        np.array(numbered, dtype=float),
        np.full(len(numbered), radius),
        n_slots,
        clockwise,
        slot_offset,
    )
    return StrandTrajectories(
        times=times,
        xy=xy,
        slots=tuple(
            (float(x), float(y), slot_names[slot])
            for (x, y), slot in zip(marks, numbered)
        ),
        outlines=(rim,),
        axis=(0.0, 0.0),
        label=label,
        outline_name="Disk",
    )


def mobidai_steps(
    mobidai, n_cycles: int = 1, drift: Optional[int] = None
) -> Tuple[Dict[Hashable, int], List[Dict[Hashable, int]]]:
    """A mobidai's cycles, as the start and steps :func:`disk_trajectories` takes.

    Reads either a ``Mobidai`` or its ``MobidaiConfig`` (see
    :mod:`braidpy.mobidai`) without running it, and follows its rules: a move
    goes the short way round unless forced, a move from an empty slot does
    nothing, and the disk turns ``n_shift_after_cycle`` slots after each cycle.

    Some braids do not come back to the slots they started in after a cycle
    but one or more slots round from them — kongo gumi creeps one slot back
    each time — and the braider simply repeats the same moves from where the
    strands now are: cycle ``c`` makes every move ``c * drift`` slots round
    from the first cycle's.  The drift is read off the cycle itself, as
    :class:`~braidpy.mobidai.Mobidai` does (see
    :func:`~braidpy.mobidai.cycle_drift`).

    Args:
        mobidai: The mobidai, or its configuration.
        n_cycles: Cycles to work.
        drift: Slots each cycle's moves are shifted from the one before;
            read off the cycle if None.

    Returns:
        Each strand's starting slot, keyed by strand id, and the steps.
    """
    config = getattr(mobidai, "config", mobidai)
    n = config.n_slots
    where: Dict[Hashable, int] = {}
    for index, strand in enumerate(config.strands):
        key = strand.id if getattr(strand, "id", -1) >= 0 else index
        where[key] = strand.position
    start = dict(where)
    if drift is None:
        from braidpy.mobidai import cycle_drift

        drift = cycle_drift(
            list(start.values()), config.moves, n, config.n_shift_after_cycle
        )

    steps: List[Dict[Hashable, int]] = []
    for cycle in range(n_cycles):
        for move in config.moves:
            source = (move.from_slot - 1 + cycle * drift) % n + 1
            target = (move.to_slot - 1 + cycle * drift) % n + 1
            mover = next((k for k, s in where.items() if s == source), None)
            if mover is None:
                continue
            diff = (target - source) % n
            force = getattr(move, "force_direction", 0)
            increasing = force == 1 or (force == 0 and diff <= n // 2)
            steps.append({mover: diff if increasing else diff - n})
            where[mover] = target
        shift = config.n_shift_after_cycle
        if shift:
            steps.append({k: shift for k in where})
            where = {k: (s - 1 + shift) % n + 1 for k, s in where.items()}
    return start, steps


def mobidai_trajectories(
    mobidai,
    n_cycles: int = 3,
    drift: Optional[int] = None,
    radius: float = 1.0,
    lift: float = 0.15,
    samples_per_step: int = 12,
    slot_offset: float = 0.0,
) -> StrandTrajectories:
    """A mobidai worked for ``n_cycles`` cycles, as trajectories to lay.

    Args:
        mobidai: A ``Mobidai`` or ``MobidaiConfig`` (see :mod:`braidpy.mobidai`).
        n_cycles: Cycles to work.
        drift: Slots each cycle's moves are shifted from the one before; read
            off the cycle if None — see :func:`mobidai_steps`.
        radius: The disk's radius.
        lift: How far in a moving strand travels, as a fraction of the radius.
        samples_per_step: Samples per move.
        slot_offset: Slots the numbering is turned by — see
            :func:`disk_trajectories`.

    Returns:
        The trajectories, one unit of time per move.
    """
    config = getattr(mobidai, "config", mobidai)
    start, steps = mobidai_steps(config, n_cycles, drift)
    return disk_trajectories(
        start,
        steps,
        config.n_slots,
        radius=radius,
        lift=lift,
        samples_per_step=samples_per_step,
        clockwise=getattr(config, "is_clockwise", True),
        slot_offset=slot_offset,
    )


def kumihimo_steps(
    kumihimo, n_strands: Optional[int] = None
) -> Tuple[int, Dict[Hashable, int], List[Dict[Hashable, int]]]:
    """A kumihimo sequence, as the disk and steps :func:`disk_trajectories` takes.

    Reads a :class:`~braidpy.kumihimo.Kumihimo` — its strand count and the
    ``S`` and ``R`` moves it has recorded — or a pattern string such as
    ``"SRSR"`` for ``n_strands`` strands, without running anything.

    The disk is given twice as many slots as there are strands, so that a
    swap has somewhere to pass: position ``p`` is slot ``2p + 1``.  A swap of
    the top and bottom strands is then the move
    :meth:`~braidpy.kumihimo.Kumihimo.swap_top_bottom` writes down — the top
    strand goes over every strand on its way to just past the bottom one, the
    bottom one comes back over the others to the top, and the first settles
    into its place.  A rotation turns the whole disk, a quarter turn
    clockwise per ``R``.

    Args:
        kumihimo: A ``Kumihimo``, or a pattern of ``S`` and ``R``.
        n_strands: Strands, when given a pattern.

    Returns:
        The number of slots, each strand's starting slot, and the steps.
    """
    if isinstance(kumihimo, str):
        if n_strands is None:
            raise ValueError("A pattern needs n_strands.")
        n = n_strands
        moves = [m if m == "S" else "R**1" for m in kumihimo]
        start_order = list(range(n))
    else:
        n = kumihimo.n
        moves = list(kumihimo.history)
        start_order = list(kumihimo.frames[0])
    if n % 4:
        raise ValueError("A kumihimo disk takes a multiple of four strands.")

    position: Dict[Hashable, int] = {s: p for p, s in enumerate(start_order)}
    start: Dict[Hashable, int] = {s: 2 * p + 1 for s, p in position.items()}
    steps: List[Dict[Hashable, int]] = []
    for move in moves:
        if move == "S":
            at = {p: strand for strand, p in position.items()}
            top, bottom = at[0], at[n // 2]
            steps += [{top: n + 1}, {bottom: -n}, {top: -1}]
            position[top], position[bottom] = n // 2, 0
        elif move.startswith("R"):
            turns = int(move.split("**")[1]) if "**" in move else 1
            shift = (n // 4) * turns
            steps.append({strand: -2 * shift for strand in position})
            position = {s: (p - shift) % n for s, p in position.items()}
        else:
            raise ValueError(f"Unknown kumihimo move {move!r}.")
    return 2 * n, start, steps


def kumihimo_trajectories(
    kumihimo,
    n_strands: Optional[int] = None,
    radius: float = 1.0,
    lift: float = 0.15,
    samples_per_step: int = 12,
) -> StrandTrajectories:
    """A kumihimo sequence worked on its disk, as trajectories to lay.

    Positions are numbered anticlockwise from the top, as
    :meth:`~braidpy.kumihimo.Kumihimo.plot_timeline` draws them.

    Args:
        kumihimo: A ``Kumihimo``, or a pattern of ``S`` and ``R``.
        n_strands: Strands, when given a pattern.
        radius: The disk's radius.
        lift: How far in a moving strand travels, as a fraction of the radius.
        samples_per_step: Samples per step.

    Returns:
        The trajectories, one unit of time per step.
    """
    n_slots, start, steps = kumihimo_steps(kumihimo, n_strands)
    return disk_trajectories(
        start,
        steps,
        n_slots,
        radius=radius,
        lift=lift,
        samples_per_step=samples_per_step,
        clockwise=False,
        # Kumihimo's positions are the odd slots; the even ones are only
        # somewhere for a swap to pass.
        slot_names={2 * p + 1: str(p) for p in range(n_slots // 2)},
    )


# ── A disk's braid, laid on a ring ────────────────────────────────────────────
#
# A disk's strands spend most of their time waiting on the rim while one
# moves, and where they wait is not the braid's cross-section: laid as it is,
# a kongo comes out flat and lopsided.  What the moves decide is only the
# order of the strands round the axis and, where two cross, which goes over.
# So that is all that is kept: the strands stand evenly round a small ring in
# their order round the disk, and each crossing the moves make swaps two
# neighbours on it, the one going over passing inside.


def disk_crossings(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
) -> Tuple[List[Hashable], List[Tuple[Hashable, Hashable]]]:
    """The crossings a disk's moves make, in the order they are made.

    See :func:`disk_crossing_steps`, which also says which step made each.

    Returns:
        The strands in slot order from slot 1 at the start, and each crossing
        as ``(over, under)``.
    """
    order, crossings, _ = disk_crossing_steps(start, steps, n_slots)
    return order, crossings


def disk_crossing_steps(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
) -> Tuple[List[Hashable], List[Tuple[Hashable, Hashable]], List[float]]:
    """The crossings a disk's moves make, and when each is made.

    A strand that moves while the others stay passes over each strand
    between its slot and its new one, one after another, nearest first —
    the rule :func:`disk_trajectories` draws and the mobidai's own word
    records.  A step that moves every strand alike turns the disk and
    crosses nothing; so does one that slides a few strands along together,
    as long as no strand that stays is in their way.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots, as
            :func:`mobidai_steps` and :func:`kumihimo_steps` give them.
        n_slots: Slots round the disk.

    Returns:
        The strands in slot order from slot 1 at the start, each crossing as
        ``(over, under)``, and when each is made, in steps: a strand moving
        ``n`` slots passes the slot ``j`` along at ``j / n`` of its step, as
        :func:`disk_trajectories` moves it.

    Raises:
        ValueError: If two strands move at once other than by turning the
            disk or sliding along together, which this cannot order into
            crossings.
    """
    where = dict(start)
    order = sorted(where, key=lambda k: where[k])
    crossings: List[Tuple[Hashable, Hashable]] = []
    made_at: List[float] = []
    for number, step in enumerate(steps):
        moving = {k: d for k, d in step.items() if d}
        if not moving:
            continue
        if _slides(where, moving, n_slots):
            delta = next(iter(moving.values()))
            for k in moving:
                where[k] = (where[k] - 1 + delta) % n_slots + 1
            continue
        if len(moving) > 1:
            raise ValueError(f"Step {number} moves several strands at once.")
        ((mover, delta),) = moving.items()
        sense = 1 if delta > 0 else -1
        slot = where[mover]
        by_slot = {s: k for k, s in where.items()}
        for passed in range(1, abs(delta)):
            slot = (slot - 1 + sense) % n_slots + 1
            if slot in by_slot:
                crossings.append((mover, by_slot[slot]))
                made_at.append(number + passed / abs(delta))
        where[mover] = (where[mover] - 1 + delta) % n_slots + 1
    return order, crossings, made_at


def _slides(
    where: Mapping[Hashable, int], moving: Mapping[Hashable, int], n_slots: int
) -> bool:
    """Whether a step carries strands along together, crossing nobody.

    Every strand moves alike — the disk turning — or several move alike and
    no strand that stays is in the slots they sweep.  A single strand
    moving is not a slide: it crosses whoever it passes.
    """
    if len(set(moving.values())) != 1:
        return False
    if set(moving) == set(where):
        return True
    if len(moving) < 2:
        return False
    delta = next(iter(moving.values()))
    sense = 1 if delta > 0 else -1
    staying = {where[k] for k in where if k not in moving}
    for k in moving:
        slot = where[k]
        for _ in range(abs(delta)):
            slot = (slot - 1 + sense) % n_slots + 1
            if slot in staying:
                return False
    return True


def disk_annular_word(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
    clockwise: bool = True,
) -> Tuple[List[int], int]:
    """The annular braid a disk's moves make — see :mod:`braidpy.annulus_braid`.

    The strands are numbered in order round the disk, seen from above and
    read clockwise from the seam between the last slot and slot 1, so an
    anticlockwise disk is read from its last slot back.  A strand lifted
    over another — over, seen from above — passes inside it, nearer the
    braid's axis, and the annulus counts a crossing by who is outside: a
    move clockwise over a strand is a negative crossing, anticlockwise a
    positive one.

    A strand passing between the last slot and slot 1, crossing nobody,
    changes nothing on the disk, but every strand's number then moves on
    one: a turn (:func:`~braidpy.annulus_braid.turn`), as the disk turning
    by one strand would be.  Which strands are numbered from where depends
    only on where slot 1 is; another starting point gives the same braid,
    conjugated.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots, as
            :func:`disk_crossings` takes them.
        n_slots: Slots round the disk.
        clockwise: Whether slot numbers go round clockwise, seen from above.

    Returns:
        The word, crossings ``±1`` to ``±n`` and turns ``±(n + 1)``, and the
        number of strands ``n``.

    Raises:
        ValueError: As :func:`disk_crossings`.
    """

    def read(slot: int) -> int:
        """A slot as numbered clockwise, the seam staying where it is."""
        return slot if clockwise else n_slots + 1 - slot

    where = {k: read(s) for k, s in start.items()}
    n = len(where)
    # The strands in order round the ring, from slot 1.
    ring = sorted(where, key=lambda k: where[k])
    word: List[int] = []
    for number, step in enumerate(steps):
        moving = {k: (d if clockwise else -d) for k, d in step.items() if d}
        if not moving:
            continue
        sliding = _slides(where, moving, n_slots)
        if len(moving) > 1 and not sliding:
            raise ValueError(f"Step {number} moves several strands at once.")
        delta = next(iter(moving.values()))
        sense = 1 if delta > 0 else -1
        for _ in range(abs(delta)):
            by_slot = {s: k for k, s in where.items()}
            # Front runners first, so nobody steps into a slot still held.
            for k in sorted(moving, key=lambda k: -sense * where[k]):
                here = where[k]
                there = (here - 1 + sense) % n_slots + 1
                if sense > 0 and there == 1:
                    # Last round the ring becomes first: everyone moves on.
                    ring.remove(k)
                    ring.insert(0, k)
                    word.append(n + 1)
                elif sense < 0 and here == 1:
                    ring.remove(k)
                    ring.append(k)
                    word.append(-(n + 1))
                other = by_slot.get(there)
                if not sliding and other is not None and other != k:
                    i = ring.index(k)
                    if sense > 0:
                        # The mover is first of the pair, and inside.
                        word.append(-(i + 1))
                        ring[i], ring[i + 1] = ring[i + 1], ring[i]
                    else:
                        # The other is first of the pair, and outside.
                        word.append(i)
                        ring[i - 1], ring[i] = ring[i], ring[i - 1]
                where[k] = there
    return word, n


def crossing_rows(
    order: Sequence[Hashable],
    crossings: Sequence[Tuple[Hashable, Hashable]],
    in_turn: bool = False,
) -> List[int]:
    """The row of the ring each crossing is made in — see :func:`ring_trajectories`.

    Each crossing goes in the first row after both its strands' last ones,
    so crossings of different strands are made side by side and each
    strand's crossings stay in order.

    Args:
        order: The strands round the ring.
        crossings: ``(over, under)`` in the order they are made.
        in_turn: Never put a crossing in a row before an earlier crossing's,
            so the rows are made in the order the crossings are, as a braid
            grows below a disk.

    Returns:
        One row index per crossing.
    """
    free_from = {k: 0 for k in order}
    rows: List[int] = []
    for over, under in crossings:
        row = max(free_from[over], free_from[under])
        if in_turn and rows:
            row = max(row, rows[-1])
        rows.append(row)
        free_from[over] = free_from[under] = row + 1
    return rows


def ring_trajectories(
    order: Sequence[Hashable],
    crossings: Sequence[Tuple[Hashable, Hashable]],
    diameter: float = 1.0,
    samples_per_row: int = 12,
    clockwise: bool = True,
    label: str = "Strand ",
    rows: Optional[Sequence[int]] = None,
) -> StrandTrajectories:
    """Strands standing evenly round a ring, swapping neighbours as they cross.

    Every crossing is made by two strands next to each other round the ring:
    they change places, the one going over passing inside, the other outside,
    a ``diameter`` apart where they meet.  Crossings of different strands are
    made side by side, in rows, as long as each strand's crossings stay in
    order; each row takes one unit of time.

    Nothing about which strand passes which, or on which side, is lost —
    inside is over, as on a disk seen from above — so a braid laid from this
    is the braid the moves made, with the strands where a braid holds them
    rather than where a disk does.

    Args:
        order: The strands round the ring, in slot order.
        crossings: ``(over, under)`` in the order they are made; each pair
            must be neighbours on the ring when its turn comes.
        diameter: Yarn diameter, setting the ring's size and how far apart
            the two strands of a crossing pass.
        samples_per_row: Samples per row of crossings.
        clockwise: Whether the order runs clockwise, seen from above.
        label: Prefix naming a strand in a drawing.
        rows: The row of each crossing; :func:`crossing_rows` if None.

    Returns:
        The trajectories, one unit of time per row.

    Raises:
        ValueError: If a crossing's strands are not neighbours on the ring.
    """
    if samples_per_row < 1:
        raise ValueError("samples_per_row must be at least 1.")
    n = len(order)
    rank = {k: i for i, k in enumerate(order)}
    if rows is None:
        rows = crossing_rows(order, crossings)
    by_row: List[List[Tuple[Hashable, Hashable]]] = []
    for crossing, index in zip(crossings, rows):
        while len(by_row) <= index:
            by_row.append([])
        by_row[index].append(crossing)

    # Even round a ring a little looser than the strands' own width.
    radius = n * diameter / (2 * np.pi) / 0.8
    turn = 1 if clockwise else -1
    # Each strand's place round the ring, in units of one place; it is not
    # wrapped, so a strand that goes round keeps going round.
    angle = {k: float(rank[k]) for k in order}
    slot = dict(rank)
    fractions = np.arange(samples_per_row) / samples_per_row
    ease = 0.5 - 0.5 * np.cos(np.pi * fractions)
    xs: Dict[Hashable, List[float]] = {k: [] for k in order}
    ys: Dict[Hashable, List[float]] = {k: [] for k in order}

    def place(k: Hashable, a: np.ndarray, r: np.ndarray) -> None:
        theta = 2 * np.pi * a / n * turn
        xs[k].extend(r * np.sin(theta))
        ys[k].extend(r * np.cos(theta))

    for number, row in enumerate(by_row):
        moving: Dict[Hashable, Tuple[int, float]] = {}
        for over, under in row:
            gap = (slot[under] - slot[over]) % n
            if gap not in (1, n - 1):
                raise ValueError(
                    f"Crossing {over!r} over {under!r} in row {number}: "
                    "they are not neighbours on the ring."
                )
            step = 1 if gap == 1 else -1
            moving[over] = (step, -1.0)
            moving[under] = (-step, 1.0)
            slot[over], slot[under] = slot[under], slot[over]
        for k in order:
            here = angle[k]
            if k in moving:
                sense, side = moving[k]
                a = here + sense * ease
                r = radius + side * diameter / 2 * np.sin(np.pi * fractions)
            else:
                a = np.full(samples_per_row, here)
                r = np.full(samples_per_row, radius)
            place(k, a, r)
        for k, (sense, _) in moving.items():
            angle[k] += sense
    for k in order:
        place(k, np.array([angle[k]]), np.array([radius]))

    times = np.arange(len(by_row) * samples_per_row + 1) / samples_per_row
    ring = np.linspace(0, 2 * np.pi, 4 * n + 1)
    return StrandTrajectories(
        times=times,
        xy={k: np.column_stack([xs[k], ys[k]]) for k in order},
        outlines=(np.column_stack([radius * np.sin(ring), radius * np.cos(ring)]),),
        axis=(0.0, 0.0),
        label=label,
        outline_name="Ring",
    )


def disk_braid(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
    yarn_diameter: float,
    take_off_per_row: float = 1.5,
    iterations: int = 300,
    clockwise: bool = True,
) -> YarnPaths:
    """The braid a disk's moves make: laid on a ring, drawn in and tightened.

    The crossings are read off the moves (:func:`disk_crossings`), the
    strands set evenly round a ring and crossed there
    (:func:`ring_trajectories`), and the braid laid and tightened as any
    other (:func:`lay_yarns`, :func:`tighten_yarns`).

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots.
        n_slots: Slots round the disk.
        yarn_diameter: Yarn diameter.
        take_off_per_row: Braid taken off per row of crossings, in yarn
            diameters.  Above one: two strands often cross back over each
            other a row later, along the same path, and need that much room.
        iterations: Tightening steps.
        clockwise: Whether slot numbers go round clockwise, seen from above.

    Returns:
        The tightened braid.
    """
    order, crossings = disk_crossings(start, steps, n_slots)
    ring = ring_trajectories(order, crossings, yarn_diameter, clockwise=clockwise)
    paths = lay_yarns(
        ring, take_off=take_off_per_row * yarn_diameter, yarn_diameter=yarn_diameter
    )
    braid, _ = tighten_yarns(paths, yarn_diameter, iterations=iterations)
    return braid


def mobidai_braid(
    mobidai, yarn_diameter: float, n_cycles: int = 8, **kwargs
) -> YarnPaths:
    """The braid a mobidai makes in ``n_cycles`` cycles — see :func:`disk_braid`.

    Args:
        mobidai: A ``Mobidai`` or ``MobidaiConfig`` (see :mod:`braidpy.mobidai`).
        yarn_diameter: Yarn diameter.
        n_cycles: Cycles to work.
        **kwargs: Passed on to :func:`disk_braid`.

    Returns:
        The tightened braid, one yarn per strand, keyed as the mobidai's.
    """
    config = getattr(mobidai, "config", mobidai)
    start, steps = mobidai_steps(config, n_cycles)
    kwargs.setdefault("clockwise", getattr(config, "is_clockwise", True))
    return disk_braid(start, steps, config.n_slots, yarn_diameter, **kwargs)


def kumihimo_braid(
    kumihimo, yarn_diameter: float, n_strands: Optional[int] = None, **kwargs
) -> YarnPaths:
    """The braid a kumihimo sequence makes — see :func:`disk_braid`.

    Args:
        kumihimo: A ``Kumihimo``, or a pattern of ``S`` and ``R``.
        yarn_diameter: Yarn diameter.
        n_strands: Strands, when given a pattern.
        **kwargs: Passed on to :func:`disk_braid`.

    Returns:
        The tightened braid.
    """
    n_slots, start, steps = kumihimo_steps(kumihimo, n_strands)
    kwargs.setdefault("clockwise", False)
    return disk_braid(start, steps, n_slots, yarn_diameter, **kwargs)
