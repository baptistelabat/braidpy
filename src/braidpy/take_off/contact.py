# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Contact between yarns sampled at common heights: which samples could
touch, the closest any two yarns come, how fast a braid must be drawn off
for its yarns to clear each other, and how tight they let it be drawn in."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING

import numpy as np

if TYPE_CHECKING:
    from .paths import StrandTrajectories


# Every yarn is sampled at the same heights, so two samples can be closer than
# a diameter only if they are fewer than ``diameter / spacing`` levels apart.
# Comparing every yarn against every other at each such offset finds every
# close pair without a spatial index.


def _level_pairs(n_yarns: int, offset: int) -> tuple[np.ndarray, np.ndarray]:
    """Yarn index pairs to compare at a level offset, each unordered pair once."""
    a, b = np.meshgrid(np.arange(n_yarns), np.arange(n_yarns), indexing="ij")
    keep = a < b if offset == 0 else a != b
    return a[keep], b[keep]


def _offsets(spacing: float, diameter: float, n: int) -> range:
    """Level offsets at which two samples can still be within a diameter."""
    if spacing <= 0:
        return range(1)
    return range(min(n, math.ceil(diameter / spacing)))


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


def least_take_off(
    trajectories: StrandTrajectories, yarn_diameter: float, take_off: float
) -> float:
    """The slowest take-off that lifts yarns passing the same point a diameter
    apart, at least ``take_off``.

    Where one strand leaves a place and another comes to the very same point
    later — as each crossing of a braid word does, one strand arriving where
    the other left — no drawing-in can separate them
    (:func:`jammed_contraction`): only the height the take-off puts between
    them can.  The fewer strands move at a time, the slower the default
    take-off, and the closer in height they come.

    Args:
        trajectories: Where the strands went, sampled evenly in time.
        yarn_diameter: Yarn diameter.
        take_off: The take-off to start from.

    Returns:
        ``take_off``, or a little faster than the least take-off that keeps
        the closest such pair a diameter apart.
    """
    centre = np.asarray(trajectories.centre(), dtype=float)
    rel = np.stack([xy - centre for xy in trajectories.xy.values()])
    n_yarns, n, _ = rel.shape
    dt = float(trajectories.times[1] - trajectories.times[0])
    scale = float(np.max(np.abs(rel))) or 1.0
    for offset in _offsets(take_off * dt, yarn_diameter, n):
        if offset == 0:
            continue  # at the same time: no take-off can part them
        a, b = _level_pairs(n_yarns, offset)
        sideways = np.linalg.norm(rel[a, : n - offset] - rel[b, offset:], axis=-1)
        if np.any(sideways <= 1e-12 * scale):
            return max(take_off, 1.01 * yarn_diameter / (offset * dt))
    return take_off


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
