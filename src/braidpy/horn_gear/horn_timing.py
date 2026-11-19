# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/horn_timing.py
========================

When the horns of two gears meet at their contact, and where to put the
gears so that they meet there together.

A gear turns one slot a step, so a horn of it comes round to each of its
contacts once a step, at a time fixed by where the contact is round the
gear and how far the gear was turned to start with.  Two gears can hand a
carrier over only when a horn of each is at their contact at once.  Where
every contact of a gear is a whole number of slots from the others, as
round a ring of gears alike, they all hand over at the end of each step.
Round a ring of gears of several sizes, as in a matrix of gears, they can
not be: the angles at the corners of its squares, each a whole number of
slots, do not add up to a turn.  A contact may then hand over at any
fraction of a step (:class:`~braidpy.horn_gear.model.Connection`'s
``phase``), as long as both gears' horns come round to it then.

Say gear ``u``, of ``n`` slots a part and turning ``d`` (+1 anticlockwise),
is turned ``psi`` to start with, and its part ``p`` of ``k`` comes round to
a contact at angle ``alpha`` at times ``t`` with

    d (alpha - psi) n / 2pi - d p / k = t  (mod 1).

Writing ``x_u = d n psi / 2pi``, a contact between ``u`` and ``v`` asks

    x_u - x_v = d_u n_u alpha_u / 2pi - d_u p_u / k_u
                - d_v n_v alpha_v / 2pi + d_v p_v / k_v   (mod 1),

with ``alpha_v = alpha_u + pi``.  There is one ``x`` a gear and one such
equation a contact, so round each ring of gears one equation is left over,
and the layout has to meet it.  :func:`time_horns` moves the gears and
changes their sizes, within ``RADIUS_RANGE``, till every two that mesh
touch, no two others overlap, and every contact's two horns arrive at once:
a least-squares fit, by Levenberg-Marquardt, of all three together.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from .layout import CLEARANCE, RADIUS_RANGE

# Rounds of :func:`time_horns`, at most, and the error at which it stops, as a
# share of a mesh's length or of the gap between two horns.
TIMING_ROUNDS = 400
TIMING_TOLERANCE = 1e-7
# Levenberg-Marquardt's damping to start with, and how it changes after a
# step that helps and one that does not.
DAMPING = 1e-2
DAMPING_EASE = 3.0
DAMPING_STIFFEN = 4.0
# The least damping: undamped, the fit's free directions (every gear turned
# alike, the whole layout moved) leave its equations singular.
DAMPING_LEAST = 1e-9
# Two centres closer than this are at one place, with no direction between
# them: a step there is taken from this far apart.
SAME_PLACE = 1e-12
# A contact handing over this close to a whole step hands over at its end.
WHOLE_STEP = 1e-3


@dataclass(frozen=True)
class Axle:
    """A gear's axle, as the timing sees it.

    Args:
        centre: Where it stands.
        radius: How large it is drawn.
        convention: Its size by the drawing convention, which ``radius`` may
            leave by ``RADIUS_RANGE`` at most.
        size: Horns round the whole of it, all its parts'.
        slots: Slots of each of its parts.
        direction: +1 turning anticlockwise, -1 clockwise.
    """

    centre: tuple[float, float]
    radius: float
    convention: float
    size: int
    slots: int
    direction: int


@dataclass(frozen=True)
class Meeting:
    """A contact between parts of two axles.

    Args:
        u: The first axle's index.
        v: The second's.
        part_u: Which of its parts meets there, as a share of a step: part
            ``p`` of ``k`` is ``p / k``.
        part_v: The same for the second.
    """

    u: int
    v: int
    part_u: float
    part_v: float


@dataclass(frozen=True)
class Timed:
    """Where the axles stand, how large they are, and when each contact hands
    over.

    Args:
        centres: Each axle's centre.
        radii: Each axle's radius.
        turned: Each axle's start, as ``x`` (see the module).
        phases: Each contact's hand-over, as a share of a step.
        miss: The worst a contact's two horns miss each other, as a share
            of the gap between two horns.
    """

    centres: np.ndarray
    radii: np.ndarray
    turned: np.ndarray
    phases: list[float]
    miss: float


def _wrap(x):
    """``x`` mod 1, between -1/2 and 1/2."""
    return (x + 0.5) % 1.0 - 0.5


class _Problem:
    """The residuals of :func:`time_horns` and their derivatives."""

    def __init__(self, axles: list[Axle], meetings: list[Meeting]) -> None:
        n = self.n = len(axles)
        self.meetings = meetings
        meshes = sorted({tuple(sorted((m.u, m.v))) for m in meetings})
        self.mesh = np.array(meshes, dtype=int).reshape(-1, 2)
        others = [
            (p, q)
            for p in range(n)
            for q in range(p + 1, n)
            if (p, q) not in set(meshes)
        ]
        self.others = np.array(others, dtype=int).reshape(-1, 2)
        self.mu = np.array([m.u for m in meetings], dtype=int)
        self.mv = np.array([m.v for m in meetings], dtype=int)
        d = np.array([a.direction for a in axles], dtype=float)
        slots = np.array([a.slots for a in axles], dtype=float)
        size = np.array([a.size for a in axles], dtype=float)
        part_u = np.array([m.part_u for m in meetings])
        part_v = np.array([m.part_v for m in meetings])
        u, v = self.mu, self.mv
        # c = a * alpha_u + b: the contact's equation's right-hand side.
        self.slope = (d[u] * slots[u] - d[v] * slots[v]) / (2 * math.pi)
        self.offset = -d[u] * part_u + d[v] * part_v - d[v] * slots[v] / 2
        # A miss of one step, as a share of the gap between two horns: a
        # horn moves a part's slot, of the axle's ``size`` horns, a step.
        self.weight = (2 * math.pi / slots[u]) / (2 * np.sin(math.pi / size[u]))
        convention = np.array([a.convention for a in axles])
        self.least = convention * RADIUS_RANGE[0]
        self.most = convention * RADIUS_RANGE[1]

    def split(self, z):
        n = self.n
        return z[: 2 * n].reshape(n, 2), z[2 * n : 3 * n], z[3 * n :]

    def angle(self, centres):
        gap = centres[self.mv] - centres[self.mu]
        return np.arctan2(gap[:, 1], gap[:, 0]), gap

    def residuals(self, z):
        centres, radii, turned = self.split(z)
        p, q = self.mesh[:, 0], self.mesh[:, 1]
        touch = radii[p] + radii[q]
        mesh = np.linalg.norm(centres[q] - centres[p], axis=1) / touch - 1
        p, q = self.others[:, 0], self.others[:, 1]
        clear = (1 + CLEARANCE) * (radii[p] + radii[q])
        apart = np.linalg.norm(centres[q] - centres[p], axis=1)
        overlap = np.maximum(clear - apart, 0) / clear
        alpha, _ = self.angle(centres)
        wanted = self.slope * alpha + self.offset
        miss = self.weight * _wrap(turned[self.mu] - turned[self.mv] - wanted)
        return np.concatenate([mesh, overlap, miss])

    def jacobian(self, z):
        centres, radii, _ = self.split(z)
        n = self.n
        rows = []
        for p, q in self.mesh:
            row = np.zeros(4 * n)
            gap = centres[q] - centres[p]
            apart = max(float(np.linalg.norm(gap)), SAME_PLACE)
            touch = radii[p] + radii[q]
            unit = gap / apart
            row[2 * q : 2 * q + 2] += unit / touch
            row[2 * p : 2 * p + 2] -= unit / touch
            row[2 * n + p] = row[2 * n + q] = -apart / touch**2
            rows.append(row)
        for p, q in self.others:
            row = np.zeros(4 * n)
            gap = centres[q] - centres[p]
            apart = max(float(np.linalg.norm(gap)), SAME_PLACE)
            clear = (1 + CLEARANCE) * (radii[p] + radii[q])
            if apart < clear:
                unit = gap / apart
                row[2 * q : 2 * q + 2] -= unit / clear
                row[2 * p : 2 * p + 2] += unit / clear
                row[2 * n + p] = row[2 * n + q] = apart * (1 + CLEARANCE) / clear**2
            rows.append(row)
        _, gaps = self.angle(centres)
        for k, (u, v) in enumerate(zip(self.mu, self.mv)):
            row = np.zeros(4 * n)
            gx, gy = gaps[k]
            turn = np.array([-gy, gx]) / max(gx * gx + gy * gy, SAME_PLACE**2)
            row[2 * v : 2 * v + 2] -= self.weight[k] * self.slope[k] * turn
            row[2 * u : 2 * u + 2] += self.weight[k] * self.slope[k] * turn
            row[3 * n + u] += self.weight[k]
            row[3 * n + v] -= self.weight[k]
            rows.append(row)
        return np.array(rows)

    def clip(self, z):
        z = z.copy()
        n = self.n
        z[2 * n : 3 * n] = np.clip(z[2 * n : 3 * n], self.least, self.most)
        return z


def _start(problem: _Problem, centres: np.ndarray) -> np.ndarray:
    """Each axle's start from a spanning tree of its contacts, the rest of
    the contacts left to the fit."""
    turned = np.zeros(problem.n)
    alpha, _ = problem.angle(centres)
    wanted = problem.slope * alpha + problem.offset
    placed = {0}
    while len(placed) < problem.n:
        for k, (u, v) in enumerate(zip(problem.mu, problem.mv)):
            if (u in placed) != (v in placed):
                if u in placed:
                    turned[v] = turned[u] - wanted[k]
                    placed.add(int(v))
                else:
                    turned[u] = turned[v] + wanted[k]
                    placed.add(int(u))
                break
        else:
            break  # not connected: the rest stay at 0
    return turned


def time_horns(axles: list[Axle], meetings: list[Meeting]) -> Timed:
    """Move and size the axles so that every contact's two horns arrive
    together, and say when each hands over (see the module).

    Args:
        axles: The axles, laid out as near touching as they can be.
        meetings: Their contacts.

    Returns:
        Where they stand, how large, and each contact's hand-over.
    """
    problem = _Problem(axles, meetings)
    centres = np.array([a.centre for a in axles], dtype=float)
    radii = np.array([a.radius for a in axles], dtype=float)
    z = np.concatenate([centres.ravel(), radii, _start(problem, centres)])
    damping = DAMPING
    error = problem.residuals(z)
    for _ in range(TIMING_ROUNDS):
        if np.max(np.abs(error)) < TIMING_TOLERANCE:
            break
        jac = problem.jacobian(z)
        normal = jac.T @ jac + damping * np.eye(len(z))
        try:
            step = np.linalg.solve(normal, -jac.T @ error)
        except np.linalg.LinAlgError:
            damping *= DAMPING_STIFFEN
            continue
        trial = problem.clip(z + step)
        trial_error = problem.residuals(trial)
        if np.all(np.isfinite(trial_error)) and np.sum(trial_error**2) < np.sum(
            error**2
        ):
            z, error = trial, trial_error
            damping = max(damping / DAMPING_EASE, DAMPING_LEAST)
        else:
            damping *= DAMPING_STIFFEN
    centres, radii, turned = problem.split(z)
    alpha, _ = problem.angle(centres)
    wanted = problem.slope * alpha + problem.offset
    phases = []
    for k, (u, m) in enumerate(zip(problem.mu, meetings)):
        a = axles[u]
        # When part m.part_u of u comes round, as the module says: from the
        # gear's own side, the miss shared with the other's by halves.
        own = (
            a.direction * (alpha[k] * a.slots / (2 * math.pi) - turned[u] / a.direction)
            - a.direction * m.part_u
        )
        shared = own + _wrap(turned[u] - turned[m.v] - wanted[k]) / 2
        phase = float(shared % 1.0)
        phases.append(0.0 if min(phase, 1 - phase) < WHOLE_STEP else phase)
    miss = float(np.max(np.abs(error[-len(meetings) :]), initial=0.0))
    return Timed(centres.copy(), radii.copy(), turned.copy(), phases, miss)
