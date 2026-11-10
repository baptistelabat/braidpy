# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Tightening a laid braid: every yarn shortened under tension, each sample
kept at its height, no two yarns closer than a diameter."""

from __future__ import annotations

import math
import warnings
from collections.abc import Callable, Collection, Hashable
from dataclasses import dataclass, replace

import numpy as np

from .contact import _level_pairs, _offsets
from .paths import YarnPaths


def _thomas(
    lower: np.ndarray, diagonal: np.ndarray, upper: np.ndarray
) -> Callable[[np.ndarray], np.ndarray]:
    """Solves a tridiagonal system by the Thomas algorithm.

    Its forward sweep depends on the matrix only, and is done once: each
    solve then costs time proportional to the size.  The same as ``thomas``
    in web/tighten.js.

    Args:
        lower: The subdiagonal, ``lower[i]`` in row ``i``; ``lower[0]``
            unused.
        diagonal: The diagonal.
        upper: The superdiagonal, ``upper[i]`` in row ``i``; the last unused.

    Returns:
        A function taking ``b``, ``(n, m)``, one column per right-hand side,
        and returning ``x``.
    """
    n = len(diagonal)
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


def _tension_solver(
    n: int, h: float, hold_top: bool
) -> Callable[[np.ndarray], np.ndarray]:
    """Solves (I + h L) x = b, L the second difference along a yarn of ``n``
    samples: its last sample fixed, its first fixed too if ``hold_top``,
    else free.

    The matrix is tridiagonal, so :func:`_thomas` solves it in time and
    memory proportional to ``n``, where inverting it costs ``n²`` memory and
    ``n³`` time.  The same solve as ``makeSettle`` in web/tighten.js.

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
    return _thomas(lower, diagonal, upper)


#: How far, in diameters, a yarn may move sideways between two levels and
#: tightening still keep yarns from passing through each other.  It looks for
#: contact between samples only, and two yarns can cross between two levels
#: without a sample of either coming within a diameter of the other only if
#: their steps there add up to two diameters or more.
SAFE_STEP = 1.0


#: How close, in the braid's units, a sample at the fell end of a window must
#: be to its partner's at the top for the two to be one level met twice.
#: Laid, they are some 1e-15 apart; the page gets positions rounded to 1e-9,
#: and must see the same.
TIED = 1e-6


@dataclass(frozen=True)
class Periodic:
    """How the bottom of a tightened braid continues into its top.

    A braid off a machine repeats, so a length of it is a window on something
    endless.  Holding both ends still is a boundary the real braid does not
    have, and it is felt for a few periods in from each end.  Saying instead
    that the yarn leaving the bottom of the window arrives at the top of it
    removes the boundary altogether: what is solved is one window of an
    endless braid rather than a short piece of a held one.

    The window must be a whole number of periods, and the pattern must come
    back to itself over it -- same positions, possibly a different yarn in
    each.  ``partner`` says which: the yarn that leaves the fell end of yarn
    ``a`` arrives at the top end of yarn ``partner[a]``.  For a braid whose
    period permutes its strands this is that permutation; where the window is
    a whole number of full cycles it is the identity.

    A window over which the pattern also turns about the axis is not handled:
    choose a whole number of turns, where there is nothing to undo.

    Args:
        partner: Yarn index to yarn index, a permutation.  Yarns are numbered
            in the order of :attr:`YarnPaths.points`.
    """

    partner: tuple[int, ...]

    def __post_init__(self) -> None:
        order = tuple(int(a) for a in self.partner)
        object.__setattr__(self, "partner", order)
        if sorted(order) != list(range(len(order))):
            raise ValueError(
                f"partner must be a permutation of 0..{len(order) - 1}, got {order}"
            )

    @classmethod
    def closing(cls, formed: np.ndarray) -> Periodic | None:
        """The wrap a laid braid closes on, if it does.

        A braid laid over a whole number of periods ends where it began:
        each yarn's last level sits on some yarn's first.

        Args:
            formed: Yarn samples, shape ``(n_yarns, n_levels, 3)``.

        Returns:
            The wrap that joins each yarn's last level to the first it sits
            on, or None if the braid does not close.
        """
        last = formed[:, -1, None, :2]
        first = formed[None, :, 0, :2]
        gap = np.max(np.abs(last - first), axis=-1)
        partner = np.argmin(gap, axis=1)
        closes = np.max(gap[np.arange(len(partner)), partner]) <= TIED
        if not closes or len(set(partner.tolist())) != len(partner):
            return None
        return cls(tuple(partner.tolist()))

    def check(self, n_yarns: int) -> None:
        """Raise if the wrap does not cover ``n_yarns`` yarns."""
        if len(self.partner) != n_yarns:
            raise ValueError(
                f"partner covers {len(self.partner)} yarns, the braid has {n_yarns}"
            )

    def loops(
        self, n_yarns: int, n_levels: int, tied: bool = False
    ) -> list[np.ndarray]:
        """The closed loops the wrap makes, as sample indices in order.

        Following a yarn down to the fell and on into its partner comes back
        to where it started after one cycle of the permutation, so the samples
        fall into one loop per cycle.

        Args:
            n_yarns: Number of yarns.
            n_levels: Samples per yarn.
            tied: The last level repeats the first, so it is not a sample of
                its own and is left out of the loop.

        Returns:
            One array of sample indices per loop, each in the order the yarn
            runs.
        """
        self.check(n_yarns)
        grid = np.arange(n_yarns * n_levels).reshape(n_yarns, n_levels)
        seen: set[int] = set()
        found: list[np.ndarray] = []
        last = n_levels - 1 if tied else n_levels
        for start in range(n_yarns):
            if start in seen:
                continue
            cycle = []
            here = start
            while here not in seen:
                seen.add(here)
                cycle.append(here)
                here = self.partner[here]
            found.append(np.concatenate([grid[c][:last] for c in cycle]))
        return found


def _tied_ends(formed: np.ndarray, periodic: Periodic) -> bool:
    """Whether the window's last level is its first over again.

    Args:
        formed: Yarn samples, shape ``(n_yarns, n_levels, 3)``.
        periodic: The wrap.

    Returns:
        True if every yarn's last level sits on its partner's first.
    """
    here = formed[:, -1, :2]
    there = formed[list(periodic.partner), 0, :2]
    return bool(np.max(np.abs(here - there)) <= TIED)


#: The fewest samples round a closed loop that tension can settle: with
#: fewer, a sample's two neighbours are one sample, or itself.
FEWEST_ROUND = 3


def _loop_settler(length: int, weight: float) -> Callable[[np.ndarray], np.ndarray]:
    """Apply ``(I + weight · L)⁻¹`` on a closed loop, where L is its Laplacian.

    Round a loop the matrix is tridiagonal but for its two corners, which
    join the last sample to the first.  Sherman and Morrison's formula
    solves it as the open, tridiagonal system with its first and last
    diagonal terms changed, by :func:`_thomas`, then corrects that by one
    column worked out once: exact, in time proportional to the loop.  The
    same as ``loopSettle`` in web/tighten.js.

    A loop of fewer than :data:`FEWEST_ROUND` samples is left as it is.

    Args:
        length: Samples round the loop.
        weight: The ``0.5 · step`` of the backward Euler step.

    Returns:
        A function taking ``(length, m)`` positions to their settled ones.
    """
    if length < FEWEST_ROUND:
        return lambda values: values.copy()
    side = -weight
    middle = 1.0 + 2.0 * weight
    # B = A - u vᵀ with u = (gamma, 0, …, 0, side), v = (1, 0, …, 0, side/gamma).
    gamma = -middle
    lower = np.full(length, side)
    upper = np.full(length, side)
    diagonal = np.full(length, middle)
    diagonal[0] = middle - gamma
    diagonal[-1] = middle - side * side / gamma
    solve = _thomas(lower, diagonal, upper)
    u = np.zeros((length, 1))
    u[0] = gamma
    u[-1] = side
    z = solve(u)
    below = 1.0 + z[0, 0] + side * z[-1, 0] / gamma

    def settle(values: np.ndarray) -> np.ndarray:
        x = solve(values)
        fact = (x[0] + side * x[-1] / gamma) / below
        return x - fact * z

    return settle


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
    core_radius: float | None = None,
    tolerance: float = 1e-3,
    hold_top: bool = True,
    rigid: Collection[Hashable] = (),
    periodic: Periodic | None = None,
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
            Ignored when ``periodic`` is given, which holds neither end.
        rigid: Yarns held where they are all along, as stiff cores: the
            others are pushed off them, and they never move.
        periodic: Join the fell end of the braid to its top, so that what is
            tightened is one window of an endless braid rather than a short
            piece of a held one.  See :class:`Periodic`: the window must be a
            whole number of periods.

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
    if periodic is None:
        held = (level == n - 1) | ((level == 0) & hold_top)
    else:
        # Neither end is held: the braid runs on into its own copy.
        periodic.check(n_yarns)
        held = np.zeros(n_yarns * n, dtype=bool)
    held |= np.repeat([k in set(rigid) for k in paths.points], n)

    # Endless and tied, each yarn's levels on past the fell end, as the
    # samples they are: level n - 1 + k of a yarn is level k of its partner.
    # The tied level itself, a copy, takes no part in contact; the samples
    # near the fell end meet those at the top of the next copy instead.
    beyond: np.ndarray | None = None
    if periodic is None:
        # Backward Euler on the tension: (I + step/2 L) x_new = x, with L the
        # second difference along a yarn — the fell end fixed, the top end
        # fixed or free — solved as the tridiagonal system it is, for every
        # yarn at once, as web/tighten.js solves it.
        settle = _tension_solver(n, 0.5 * step, hold_top)
    else:
        # A window laid over a whole period ends where it began: lay_yarns
        # gives one sample more than it has intervals, so its last level is
        # its first over again.  That level is not an unknown of its own --
        # it is tied to its twin, and left out of the loop rather than
        # lengthening the braid by one level in every period.
        tied = _tied_ends(formed, periodic)
        loops = periodic.loops(n_yarns, n, tied)
        if tied:
            levels = np.arange(n - 1 + len(offsets))
            beyond = np.where(
                levels < n - 1,
                np.arange(n_yarns)[:, None] * n + levels,
                np.asarray(periodic.partner)[:, None] * n + (levels - (n - 1)),
            )
        rounds = {
            length: (
                np.stack([loop for loop in loops if len(loop) == length]),
                _loop_settler(length, 0.5 * step),
            )
            for length in sorted({len(loop) for loop in loops})
        }
        twin = np.arange(n_yarns) * n + (n - 1)
        twin_of = np.asarray(periodic.partner) * n

    def tie() -> None:
        """Keep each duplicated level on top of the one it repeats."""
        if periodic is not None and tied:
            xy[twin] = xy[twin_of]

    def tension_move() -> np.ndarray:
        """Where the tension step would take every sample, less where it is."""
        if periodic is None:
            lines = xy.reshape(n_yarns, n, 2).transpose(1, 0, 2).reshape(n, -1)
            target = settle(lines).reshape(n, n_yarns, 2).transpose(1, 0, 2)
            return target.reshape(-1, 2) - xy
        move = np.zeros_like(xy)
        # Loops of one length share a solver, and are settled together, a
        # column for each one's x and each one's y.
        for length, (rows, settler) in rounds.items():
            values = xy[rows].transpose(1, 0, 2).reshape(length, -1)
            settled = settler(values).reshape(length, -1, 2).transpose(1, 0, 2)
            move[rows] = settled - xy[rows]
        return move

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
            if beyond is None:
                p, q = grid[a, : n - o].ravel(), grid[b, o:].ravel()
            else:
                # Endless: every level but the tied one, against levels up
                # to past the fell end, in the next copy.
                p, q = grid[a, : n - 1].ravel(), beyond[b, o : o + n - 1].ravel()
                apart = p != q
                p, q = p[apart], q[apart]
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
                break
            push[held] = 0.0
            xy[:] += clamp(push)
        tie()

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
        along = float(np.sum(np.linalg.norm(np.diff(formed, axis=1), axis=-1)))
        if periodic is None or _tied_ends(formed, periodic):
            return along
        # The segment that leaves the fell end and arrives at the top of the
        # next copy is part of the braid too, and the length would not be
        # monotone without it.
        leaving = formed[:, -1, :2]
        arriving = formed[list(periodic.partner), 0, :2]
        across = np.linalg.norm(leaving - arriving, axis=-1)
        return along + float(np.sum(np.sqrt(across**2 + spacing**2)))

    history: dict[str, list[float]] = {"length": [], "closest": []}
    p, q, need, rise = movable(neighbours())
    built = xy.copy()
    separate(p, q, need)
    inner = ~held
    for _ in range(iterations):
        move = tension_move()
        xy[inner] += clamp(move[inner])
        tie()
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
