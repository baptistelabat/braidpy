# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Laying a braid from its trajectories: drawn off along its axis at a steady
rate, drawn in to a fell and, above it, as tight as its yarns allow."""

from __future__ import annotations

from collections.abc import Hashable

import numpy as np

from .contact import jammed_contraction, least_take_off
from .paths import StrandTrajectories, YarnPaths


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
    take_off: float | None = None,
    fell_radius: float | None = None,
    yarn_diameter: float | None = None,
    fell_height: float | None = None,
    axis: tuple[float, float] | None = None,
    n_converge: int = 16,
    settle_length: float | None = None,
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
            :func:`default_take_off` — or, with ``yarn_diameter``, faster if
            need be, so that two yarns passing the same point are a diameter
            apart in height there; see :func:`least_take_off`.
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
    if axis is None:
        axis = traj.centre()
    centre = np.asarray(axis, dtype=float)
    rel = np.stack([xy - centre for xy in traj.xy.values()])
    if take_off is None:
        take_off = default_take_off(traj)
        if yarn_diameter is not None:
            take_off = max(take_off, least_take_off(traj, yarn_diameter, take_off))
    if take_off <= 0:
        raise ValueError("take_off must be positive.")
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
    points: dict[Hashable, np.ndarray] = {}
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
