# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tightening a laid braid: every yarn shortened under tension, each sample
kept at its height, no two yarns closer than a diameter."""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable, Collection, Hashable
from dataclasses import replace
from typing import Optional

import numpy as np

from .contact import _level_pairs, _offsets
from .paths import YarnPaths


def _tension_solver(
    n: int, h: float, hold_top: bool
) -> Callable[[np.ndarray], np.ndarray]:
    """Solves (I + h L) x = b, L the second difference along a yarn of ``n``
    samples: its last sample fixed, its first fixed too if ``hold_top``,
    else free.

    The matrix is tridiagonal, so the Thomas algorithm solves it in time
    and memory proportional to ``n``, where inverting it costs ``n²`` memory
    and ``n³`` time: its forward sweep depends on the matrix only, and is
    done once.  The same solve as ``makeSettle`` in web/tighten.js.

    Returns:
        A function taking ``b``, ``(n, m)``, one column per right-hand side —
        every yarn's x and y at once — and returning ``x``.
    """
    lower = np.zeros(n)
    diagonal = np.ones(n)
    upper = np.zeros(n)
    lower[1 : n - 1] = -h
    diagonal[1 : n - 1] = 1 + 2 * h
    upper[1 : n - 1] = -h
    if not hold_top and n > 1:
        diagonal[0] = 1 + h
        upper[0] = -h
    c = np.zeros(n)
    m = np.empty(n)
    m[0] = diagonal[0]
    c[0] = upper[0] / m[0] if n > 1 else 0.0
    for i in range(1, n):
        m[i] = diagonal[i] - lower[i] * c[i - 1]
        c[i] = upper[i] / m[i] if i < n - 1 else 0.0

    def solve(b: np.ndarray) -> np.ndarray:
        d = np.empty_like(b)
        d[0] = b[0] / m[0]
        for i in range(1, n):
            d[i] = (b[i] - lower[i] * d[i - 1]) / m[i]
        x = np.empty_like(b)
        x[n - 1] = d[n - 1]
        for i in range(n - 2, -1, -1):
            x[i] = d[i] - c[i] * x[i + 1]
        return x

    return solve


#: How far, in diameters, a yarn may move sideways between two levels and
#: tightening still keep yarns from passing through each other.  It looks for
#: contact between samples only, and two yarns can cross between two levels
#: without a sample of either coming within a diameter of the other only if
#: their steps there add up to two diameters or more.
SAFE_STEP = 1.0


def longest_step(paths: YarnPaths) -> float:
    """The furthest any yarn moves sideways between two levels of the braid
    above the fell."""
    formed = paths.formed()
    if formed.shape[1] < 2:
        return 0.0
    return float(np.max(np.linalg.norm(np.diff(formed[:, :, :2], axis=1), axis=-1)))


def warn_if_too_coarse(paths: YarnPaths, yarn_diameter: float) -> None:
    """Warn when the braid is laid too coarsely for :func:`tighten_yarns` to
    keep its yarns apart: see :data:`SAFE_STEP`.

    Args:
        paths: The braid about to be tightened.
        yarn_diameter: Its yarns' diameter.
    """
    step = longest_step(paths) / yarn_diameter
    if step >= SAFE_STEP:
        warnings.warn(
            f"A yarn moves {step:.1f} diameters sideways between two levels: "
            f"tightening may let yarns pass through each other there, "
            f"unseen.  Lay the braid in more samples, or find why it jumps.",
            stacklevel=3,
        )


def tighten_yarns(
    paths: YarnPaths,
    yarn_diameter: float,
    iterations: int = 400,
    step: float = 20.0,
    core_radius: Optional[float] = None,
    tolerance: float = 1e-3,
    hold_top: bool = True,
    rigid: Collection[Hashable] = (),
) -> tuple[YarnPaths, dict[str, list[float]]]:
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

    Warns:
        UserWarning: If the braid is laid too coarsely for contact between
            samples to keep its yarns apart (:func:`warn_if_too_coarse`).
    """
    if yarn_diameter <= 0:
        raise ValueError("yarn_diameter must be positive.")
    if step <= 0:
        raise ValueError("step must be positive.")
    warn_if_too_coarse(paths, yarn_diameter)

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

    # Backward Euler on the tension: (I + step/2 L) x_new = x, with L the
    # second difference along a yarn — the fell end fixed, the top end fixed
    # or free — solved as the tridiagonal system it is, for every yarn at
    # once, as web/tighten.js solves it.
    settle = _tension_solver(n, 0.5 * step, hold_top)

    def clamp(move: np.ndarray) -> np.ndarray:
        size = np.linalg.norm(move, axis=-1, keepdims=True)
        return move * np.minimum(1.0, max_move / np.maximum(size, 1e-300))

    def neighbours() -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
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

    history: dict[str, list[float]] = {"length": [], "closest": []}
    p, q, need, rise = movable(neighbours())
    built = xy.copy()
    separate(p, q, need)
    inner = ~held
    for _ in range(iterations):
        lines = xy.reshape(n_yarns, n, 2).transpose(1, 0, 2).reshape(n, -1)
        target = settle(lines).reshape(n, n_yarns, 2).transpose(1, 0, 2)
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
