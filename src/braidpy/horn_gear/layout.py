# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/layout.py
===================

Where everything sits: gear centres, the notches between them, the circles a
carrier rides on, and the columns a braid forms around.

Gears are placed from the connection graph — BFS along the x-axis for a chain,
Kamada-Kawai relaxed till every two gears that mesh touch for anything with a
cycle (:func:`ring_geometry`) — unless the machine pins its own
geometry, in which case :meth:`~braidpy.horn_gear.model.BraidingMachine
.preferred_layout` wins.  Gear radius goes as sqrt(n_slots), which is a
drawing convention and not a mechanical one — see :func:`_gear_radius`.

Everything else here is derived from those centres: where two gears meet
(:func:`contact_point`), how far out a carrier rides (:func:`carrier_radius`),
how each gear must be turned for its slots to face its notches
(:func:`slot_offsets`), by how much that fails where a line of gears bends
(:func:`offset_residuals`), and how the slots are drawn so that carriers are
handed on without jumping all the same (:func:`slot_angles`).  It is all plain
geometry with no drawing in it, so it can be measured and tested directly.
"""

from __future__ import annotations

import bisect
import math
import weakref
from collections import deque
from dataclasses import dataclass
from typing import Optional

import networkx as nx
import numpy as np

from .model import Axial, BraidingMachine


def _gear_radius(n_slots: int, scale: float = 1.0) -> float:
    """Drawing radius of a gear with n_slots slots.

    The square root makes the disc *area* proportional to the slot count, so
    every slot is drawn with the same share of its gear — exactly
    ``pi * scale**2`` of area, whatever the gear size.  A radius linear in the
    slot count would give a 16-slot gear four times the radius and sixteen
    times the area of a 4-slot one, which swamps a picture containing both.

    What it does **not** do is keep the slots the same width: the arc per slot
    is ``2 pi scale / sqrt(n_slots)``, so it shrinks as gears grow — 3.14 at
    four slots against 1.11 at thirty-two.  The two properties cannot both
    hold, since constant arc width needs a radius linear in the slot count.

    **This is a convention for drawing, not a kinematic constraint.**  A real
    machine does need a constant slot pitch, because two gears hand a carrier
    over only when a notch of each arrives at the contact together, and equal
    pitch is what keeps them in register; commercial machines sidestep the
    question by giving every gear the same size and usually four slots.
    braidpy does not need it, because a step advances every gear by one slot
    whatever its size and rotation is counted in slots rather than in angle —
    so the radius never enters the simulation.  It decides the picture, and
    through the picture the tangency of :func:`compute_layout` and everything
    derived from it, such as :func:`contact_point` and :func:`carrier_radius`.

    Args:
        n_slots: Number of slots on the gear.
        scale: Global scale factor.

    Returns:
        Radius in layout units.
    """
    return scale * math.sqrt(n_slots)


def compute_layout(
    machine: BraidingMachine,
    scale: float = 1.0,
    seed: int | None = 42,
    iterations: int = 500,
) -> dict[str, tuple[float, float]]:
    """Compute 2-D positions for all gears with adjacent circles exactly tangential.

    For tree / path graphs (flat braid): BFS-based placement along the x-axis
    guarantees every pair of adjacent gear circles touches exactly.

    For cyclic graphs (a tubular braider's ring, a matrix of gears):
    :func:`ring_geometry`, which also sizes the gears so that they touch.

    Args:
        machine: The BraidingMachine whose gears to position.
        scale: Overall scale factor for gear radii.
        seed: Random seed for reproducibility (cyclic graphs only).
        iterations: Spring-layout iterations (cyclic fallback only).

    Returns:
        Dict mapping gear name → (x, y) in layout coordinates.
    """
    preferred = machine.preferred_layout(scale)
    if preferred is not None:
        return preferred

    if len(machine.gears) == 0:
        return {}
    if len(machine.gears) == 1:
        return {next(iter(machine.gears)): (0.0, 0.0)}

    # ── Tree / path: exact BFS placement ──────────────────────────────────────
    if nx.is_forest(machine.graph):
        return _layout_bfs(machine, scale)

    # ── Cyclic graph: Kamada-Kawai, relaxed till the gears touch ──────────────
    return ring_geometry(machine, scale, seed=seed, iterations=iterations)[0]


# How far a gear in a ring may grow or shrink from the drawing convention
# (:func:`_gear_radius`) so that it touches its neighbours, as a factor of
# the convention's radius: a matrix of gears of several sizes cannot always
# be laid out with every gear its own size and touching every neighbour.
RADIUS_RANGE = (0.75, 1.3)
# What share of the gap between two gears that do not mesh is kept, past
# touching, as a share of their two radii: room for the carriers going by.
CLEARANCE = 0.1
# How much of a mesh's error a round of :func:`_relax` gives to the radii,
# the rest to moving the centres: the sizes change only as far as needed.
RADIUS_GIVE = 0.2
# Rounds of :func:`_relax`, at most, and the error at which it stops: a mesh
# that far off, as a share of its length, is touching for any drawing.
RELAX_ROUNDS = 3000
RELAX_TOLERANCE = 1e-3


def ring_geometry(
    machine: BraidingMachine,
    scale: float = 1.0,
    seed: int | None = 42,
    iterations: int = 500,
) -> tuple[dict[str, tuple[float, float]], dict[str, float]]:
    """Where the gears of a machine with a ring of gears stand, and how large
    they are drawn, so that every two that mesh touch and no two others
    overlap.

    Kamada-Kawai lays the graph out with each mesh as long as the two radii,
    which it can do exactly for one ring of gears alike, as a tubular
    braider is.  Where it cannot, as in a matrix of gears of several sizes,
    its compromise is relaxed (:func:`_relax`): the gears that mesh are
    drawn to touch, moving their centres and, within ``RADIUS_RANGE``,
    their sizes; those that do not are pushed apart, past touching.  Not an
    exact solution, but no gear runs through another, nor does a carrier
    through another's path.  A layout that is right already is kept as it
    is.

    Args:
        machine: The machine; its graph has a cycle.
        scale: Overall scale for the radii.
        seed: Random seed for the spring layout, the fallback.
        iterations: Iterations of the spring layout.
    Returns:
        Gear name → centre, and gear name → radius.
    """
    key = (scale, seed, iterations)
    solved = _RING_GEOMETRY.setdefault(machine, {})
    if key not in solved:
        solved[key] = _ring_geometry(machine, scale, seed, iterations)
    centers, radii = solved[key]
    return dict(centers), dict(radii)


# Each machine's ring geometry, worked out once: the layout and the radii
# are asked for at every turn of a machine, and Kamada-Kawai takes time.
_RING_GEOMETRY: weakref.WeakKeyDictionary = weakref.WeakKeyDictionary()


def _ring_geometry(machine, scale, seed, iterations):
    """:func:`ring_geometry`, worked out."""
    convention = {
        name: _gear_radius(gear.size or gear.n_slots, scale)
        for name, gear in machine.gears.items()
    }
    g = machine.graph.copy()
    for u, v in g.edges():
        g[u][v]["len"] = convention[u] + convention[v]
    try:
        raw = nx.kamada_kawai_layout(g, weight="len")
    # Without SciPy (in a browser) or for a graph it cannot lay out, the
    # spring layout instead.
    except Exception:  # noqa: BLE001
        raw = nx.spring_layout(g, seed=seed, iterations=iterations)
    pos = {n: np.array(xy) for n, xy in raw.items()}
    # Scaled so that no mesh is longer than its two radii: exact for a ring
    # of gears alike, every mesh then as long as it should be.
    min_ratio = float("inf")
    for u, v in g.edges():
        actual = float(np.linalg.norm(pos[u] - pos[v]))
        if actual > 1e-9:
            min_ratio = min(min_ratio, g[u][v]["len"] / actual)
    if math.isfinite(min_ratio) and min_ratio > 0:
        pos = {n: xy * min_ratio for n, xy in pos.items()}
    names = list(g.nodes)
    centers = np.array([pos[n] for n in names], dtype=float)
    radii = np.array([convention[n] for n in names])
    index = {n: i for i, n in enumerate(names)}
    meshes = [(index[u], index[v]) for u, v in g.edges()]
    others = [
        (index[u], index[v])
        for i, u in enumerate(names)
        for v in names[i + 1 :]
        if not g.has_edge(u, v)
    ]
    if _worst(centers, radii, meshes, others) > RELAX_TOLERANCE:
        centers, radii = min(
            (
                _relax(start, radii, meshes, others)
                for start in _starts(g, names, centers, meshes, radii, seed)
            ),
            key=lambda solved: _worst(*solved, meshes, others),
        )
    placed = {n: (float(x), float(y)) for n, (x, y) in zip(names, centers)}
    return _orient(machine, placed), {n: float(r) for n, r in zip(names, radii)}


# How many spring layouts, besides Kamada-Kawai's and a planar one, a ring
# is relaxed from (:func:`_starts`): a start can fold a ring of gears into a
# bow-tie, which relaxing cannot undo, and another start does not.
SPRING_STARTS = 3


def _starts(g, names, centers, meshes, radii, seed):
    """Layouts to relax a ring from (:func:`ring_geometry`), each scaled so
    that its middle mesh is as long as it should be: Kamada-Kawai's, a
    planar one where the gears can be drawn without crossing, and
    ``SPRING_STARTS`` spring layouts."""
    shapes = [centers]
    if nx.check_planarity(g)[0]:
        planar = nx.planar_layout(g)
        shapes.append(np.array([planar[n] for n in names], dtype=float))
    for k in range(SPRING_STARTS):
        spring = nx.spring_layout(g, seed=None if seed is None else seed + k)
        shapes.append(np.array([spring[n] for n in names], dtype=float))
    for shape in shapes:
        a, b, _, distance = _pairs(shape, meshes)
        ratio = (radii[a] + radii[b]) / np.maximum(distance, 1e-12)
        yield shape * float(np.median(ratio))


def _pairs(centers: np.ndarray, pairs: list) -> tuple[np.ndarray, ...]:
    """Two index arrays for ``pairs``, the unit vector from the first of each
    to the second, and their distance."""
    a = np.array([p[0] for p in pairs], dtype=int)
    b = np.array([p[1] for p in pairs], dtype=int)
    gap = centers[b] - centers[a]
    distance = np.linalg.norm(gap, axis=1)
    return a, b, gap / np.maximum(distance, 1e-12)[:, None], distance


def _worst(centers, radii, meshes, others) -> float:
    """The worst error of a layout, as a share of the length it should be:
    a mesh too long or too short, or two gears that do not mesh closer than
    touching, past ``CLEARANCE``."""
    worst = 0.0
    if meshes:
        a, b, _, distance = _pairs(centers, meshes)
        wanted = radii[a] + radii[b]
        worst = float(np.max(np.abs(distance - wanted) / wanted))
    if others:
        a, b, _, distance = _pairs(centers, others)
        wanted = (radii[a] + radii[b]) * (1 + CLEARANCE)
        worst = max(worst, float(np.max((wanted - distance) / wanted)))
    return worst


def _relax(centers, radii, meshes, others):
    """Draw gears that mesh to touch and push the others apart, a round at a
    time, every constraint at once and each gear moved by the mean of what
    its constraints ask, till the worst is within ``RELAX_TOLERANCE`` or
    ``RELAX_ROUNDS`` have passed.  A mesh's error goes to its centres and,
    ``RADIUS_GIVE`` of it, to the radii, kept within ``RADIUS_RANGE`` of
    where they started."""
    centers = centers.copy()
    least, most = radii * RADIUS_RANGE[0], radii * RADIUS_RANGE[1]
    radii = radii.copy()
    n = len(radii)
    for _ in range(RELAX_ROUNDS):
        if _worst(centers, radii, meshes, others) <= RELAX_TOLERANCE:
            break
        moves = np.zeros_like(centers)
        counts = np.zeros(n)
        grows = np.zeros(n)
        a, b, unit, distance = _pairs(centers, meshes)
        error = distance - (radii[a] + radii[b])
        push = unit * (error * (1 - RADIUS_GIVE) / 2)[:, None]
        np.add.at(moves, a, push)
        np.add.at(moves, b, -push)
        np.add.at(counts, a, 1)
        np.add.at(counts, b, 1)
        np.add.at(grows, a, error * RADIUS_GIVE / 2)
        np.add.at(grows, b, error * RADIUS_GIVE / 2)
        if others:
            a, b, unit, distance = _pairs(centers, others)
            short = np.maximum((radii[a] + radii[b]) * (1 + CLEARANCE) - distance, 0)
            push = unit * (short / 2)[:, None]
            np.add.at(moves, a, -push)
            np.add.at(moves, b, push)
            pushed = (short > 0).astype(float)
            np.add.at(counts, a, pushed)
            np.add.at(counts, b, pushed)
        counts = np.maximum(counts, 1)
        centers += moves / counts[:, None]
        radii = np.clip(radii + grows / counts, least, most)
    return centers, radii


# Rounds of :func:`time_ring`, at most, and the error at which it stops, as
# a share of a mesh's length or of the gap between two horns.
TIMING_ROUNDS = 400
TIMING_TOLERANCE = 1e-7
# Levenberg-Marquardt's damping in time_ring to start with, how it changes
# after a step that helps and one that does not, and the least it may be:
# undamped, the fit's free directions (every gear turned alike, the whole
# layout moved) leave its equations singular.
DAMPING = 1e-2
DAMPING_EASE = 3.0
DAMPING_STIFFEN = 4.0
DAMPING_LEAST = 1e-9
# Two centres closer than this are at one place, with no direction between
# them: a step there is taken from this far apart.
SAME_PLACE = 1e-12
# A contact handing over this close to a whole step hands over at its end.
WHOLE_STEP = 1e-3


@dataclass(frozen=True)
class RingContacts:
    """When a ring's contacts come round, for :func:`time_ring`: one entry a
    contact, between gear ``first`` and gear ``second`` (indices).

    A gear of ``n`` slots a part, turning ``d`` (+1 anticlockwise) and
    turned ``psi`` to start with, brings its part ``p`` of ``k`` to a
    contact at angle ``alpha`` at the times ``t`` with
    ``d n (alpha - psi) / 2 pi - d p / k = t`` (mod 1).  Written with the
    gear's start ``x = d n psi / 2 pi``, that is
    ``turns * alpha - x - part = t``.

    Each start is a timer's: by default each gear's, its parts a fixed
    share of a step apart; or, with ``timer_first`` and ``timer_second``,
    one of ``n_timers``, so that the parts of a split gear, stacked on one
    axle, each start where they are set, as their horn plates are when the
    machine is assembled (``part`` then 0).

    Attributes:
        first: Each contact's first gear.
        second: Its second gear.
        turns: ``d n / 2 pi`` of each gear, by index.
        part_first: ``d p / k`` of the first gear's part there.
        part_second: The same of the second's.
        weight: A miss of one step at the contact, as a share of the gap
            between two horns of the first gear.
        timer_first: The timer of the first gear's part, by index; the
            gear's own if None.
        timer_second: The same of the second's.
        n_timers: How many timers; as many as gears if None.
        apart: Timers set so far apart once fitted, as ``(timer, other,
            share of a step)``: the parts of a split gear, their horns
            taking turns round its axle.  Where no contact ties the two, as
            two bands joined by split gears, the first's whole band is
            turned so, which changes no contact of it.
    """

    first: np.ndarray
    second: np.ndarray
    turns: np.ndarray
    part_first: np.ndarray
    part_second: np.ndarray
    weight: np.ndarray
    timer_first: np.ndarray | None = None
    timer_second: np.ndarray | None = None
    n_timers: int | None = None
    apart: tuple[tuple[int, int, float], ...] = ()


def _wrap(x):
    """``x`` mod 1, between -1/2 and 1/2."""
    return (x + 0.5) % 1.0 - 0.5


class _Timing:
    """What :func:`time_ring` fits: the gears' centres, radii and starts,
    packed into one vector ``z``, and the errors it drives to nothing, with
    their derivatives."""

    def __init__(self, convention, meshes, others, contacts: RingContacts):
        self.n = len(convention)
        self.meshes, self.others, self.contacts = meshes, others, contacts
        c = contacts
        # Whose start each contact's two horns keep time by.
        self.m = self.n if c.n_timers is None else c.n_timers
        self.timed_first = c.first if c.timer_first is None else c.timer_first
        self.timed_second = c.second if c.timer_second is None else c.timer_second
        # A contact asks first's start minus second's to be
        # slope * alpha + offset, alpha its angle seen from first.
        self.slope = c.turns[c.first] - c.turns[c.second]
        self.offset = -c.part_first + c.part_second - c.turns[c.second] * math.pi
        self.least = convention * RADIUS_RANGE[0]
        self.most = convention * RADIUS_RANGE[1]

    def split(self, z):
        """The centres, radii and starts packed in ``z``."""
        n = self.n
        return z[: 2 * n].reshape(n, 2), z[2 * n : 3 * n], z[3 * n :]

    def angle(self, centers):
        """Each contact's angle, seen from its first gear, and the vector
        from that gear's centre to the second's."""
        c = self.contacts
        gap = centers[c.second] - centers[c.first]
        return np.arctan2(gap[:, 1], gap[:, 0]), gap

    def miss(self, z):
        """How far each contact's two horns miss each other, in steps."""
        centers, _, turned = self.split(z)
        alpha, _ = self.angle(centers)
        wanted = self.slope * alpha + self.offset
        return _wrap(turned[self.timed_first] - turned[self.timed_second] - wanted)

    def residuals(self, z):
        """Every error, as a share of what it is measured against: each mesh
        too long or too short, each two gears that do not mesh closer than
        ``CLEARANCE``, each contact's two horns missing each other."""
        centers, radii, _ = self.split(z)
        a, b, _, apart = _pairs(centers, self.meshes)
        mesh = apart / (radii[a] + radii[b]) - 1
        a, b, _, apart = _pairs(centers, self.others)
        clear = (1 + CLEARANCE) * (radii[a] + radii[b])
        overlap = np.maximum(clear - apart, 0) / clear
        return np.concatenate([mesh, overlap, self.contacts.weight * self.miss(z)])

    def jacobian(self, z):
        """The derivative of each error of :meth:`residuals` with respect to
        each number of ``z``, one row an error."""
        centers, radii, _ = self.split(z)
        n = self.n
        rows = []
        a, b, unit, apart = _pairs(centers, self.meshes)
        apart = np.maximum(apart, SAME_PLACE)
        touch = radii[a] + radii[b]
        mesh = np.zeros((len(a), 3 * n + self.m))
        k = np.arange(len(a))
        for axis in (0, 1):
            mesh[k, 2 * b + axis] += unit[:, axis] / touch
            mesh[k, 2 * a + axis] -= unit[:, axis] / touch
        mesh[k, 2 * n + a] = mesh[k, 2 * n + b] = -apart / touch**2
        rows.append(mesh)
        a, b, unit, apart = _pairs(centers, self.others)
        apart = np.maximum(apart, SAME_PLACE)
        clear = (1 + CLEARANCE) * (radii[a] + radii[b])
        near = apart < clear
        overlap = np.zeros((len(a), 3 * n + self.m))
        k = np.arange(len(a))[near]
        a, b, unit, apart, clear = (
            a[near],
            b[near],
            unit[near],
            apart[near],
            clear[near],
        )
        for axis in (0, 1):
            overlap[k, 2 * b + axis] -= unit[:, axis] / clear
            overlap[k, 2 * a + axis] += unit[:, axis] / clear
        overlap[k, 2 * n + a] = overlap[k, 2 * n + b] = (
            apart * (1 + CLEARANCE) / clear**2
        )
        rows.append(overlap)
        c = self.contacts
        _, gap = self.angle(centers)
        gx, gy = gap[:, 0], gap[:, 1]
        square = np.maximum(gx * gx + gy * gy, SAME_PLACE**2)
        turn = np.stack([-gy / square, gx / square], axis=1)
        pull = (c.weight * self.slope)[:, None] * turn
        timing = np.zeros((len(c.first), 3 * n + self.m))
        k = np.arange(len(c.first))
        for axis in (0, 1):
            timing[k, 2 * c.second + axis] -= pull[:, axis]
            timing[k, 2 * c.first + axis] += pull[:, axis]
        timing[k, 3 * n + self.timed_first] += c.weight
        timing[k, 3 * n + self.timed_second] -= c.weight
        rows.append(timing)
        return np.vstack(rows)

    def clip(self, z):
        """``z`` with each radius within ``RADIUS_RANGE`` of its
        convention."""
        z = z.copy()
        n = self.n
        z[2 * n : 3 * n] = np.clip(z[2 * n : 3 * n], self.least, self.most)
        return z

    def start(self, centers):
        """Each timer's start from a spanning tree of its contacts, the rest
        of the contacts left to the fit."""
        turned = np.zeros(self.m)
        alpha, _ = self.angle(centers)
        wanted = self.slope * alpha + self.offset
        placed = {0}
        while len(placed) < self.m:
            for k, (u, v) in enumerate(zip(self.timed_first, self.timed_second)):
                if (u in placed) != (v in placed):
                    if u in placed:
                        turned[v] = turned[u] - wanted[k]
                        placed.add(int(v))
                    else:
                        turned[u] = turned[v] + wanted[k]
                        placed.add(int(u))
                    break
            else:
                # Timers no contact joins to those placed, as the parts of
                # split gears braiding apart: their own tree, from 0.
                placed.add(min(set(range(self.m)) - placed))
        return turned


def time_ring(
    centers: np.ndarray,
    radii: np.ndarray,
    convention: np.ndarray,
    meshes: list[tuple[int, int]],
    others: list[tuple[int, int]],
    contacts: RingContacts,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, list[float]]:
    """Move and size the gears of a ring, from :func:`ring_geometry`'s
    layout, so that each contact's two horns come round to it together, and
    say when.

    A contact between two gears asks their starts to differ by so much, mod
    1 (:class:`RingContacts`): one equation a contact, and one start a
    gear, so round each ring of gears one equation is left over, which the
    layout has to meet.  Round a single ring of gears alike it cancels.
    Every two gears that mesh touch, no two others come within
    ``CLEARANCE``, each radius stays within ``RADIUS_RANGE`` of its
    convention, and the horns arrive together: a least-squares fit of all
    of it, by Levenberg-Marquardt with exact derivatives.

    Args:
        centers: Each gear's centre, ``(n, 2)``.
        radii: Each gear's radius as drawn.
        convention: Each gear's radius by the drawing convention
            (:func:`_gear_radius`), which its radius may leave by
            ``RADIUS_RANGE`` at most.
        meshes: The gears that mesh, as index pairs.
        others: Those that do not.
        contacts: When the contacts come round.

    Returns:
        The centres, the radii, each gear's start (``x`` of
        :class:`RingContacts`), and when each contact hands over, as a share
        of a step.
    """
    fit = _Timing(convention, meshes, others, contacts)
    z = np.concatenate([centers.ravel(), radii, fit.start(centers)])
    damping = DAMPING
    error = fit.residuals(z)
    for _ in range(TIMING_ROUNDS):
        if np.max(np.abs(error)) < TIMING_TOLERANCE:
            break
        jac = fit.jacobian(z)
        normal = jac.T @ jac + damping * np.eye(len(z))
        try:
            step = np.linalg.solve(normal, -jac.T @ error)
        except np.linalg.LinAlgError:
            damping *= DAMPING_STIFFEN
            continue
        trial = fit.clip(z + step)
        trial_error = fit.residuals(trial)
        if np.all(np.isfinite(trial_error)) and np.sum(trial_error**2) < np.sum(
            error**2
        ):
            z, error = trial, trial_error
            damping = max(damping / DAMPING_EASE, DAMPING_LEAST)
        else:
            damping *= DAMPING_STIFFEN
    centers, radii, turned = fit.split(z)
    turned = _set_apart(turned.copy(), fit, contacts.apart)
    alpha, _ = fit.angle(centers)
    c = contacts
    # When the first gear's part comes round, the miss shared with the
    # second's by halves.
    own = c.turns[c.first] * alpha - turned[fit.timed_first] - c.part_first
    phases = [
        0.0 if min(phase, 1 - phase) < WHOLE_STEP else phase
        for phase in ((own + fit.miss(z) / 2) % 1.0).tolist()
    ]
    return centers.copy(), radii.copy(), turned.copy(), phases


def _set_apart(
    turned: np.ndarray,
    fit: _Timing,
    apart: tuple[tuple[int, int, float], ...],
) -> np.ndarray:
    """The timers, each band of them that no contact ties to another shifted
    together, which changes none of its contacts, so that its timers stand
    as far from the other band's as ``apart`` asks (:class:`RingContacts`);
    a band already tied to the other, by a contact or an earlier shift,
    stays as it is.

    Args:
        turned: Each timer's start, as fitted; shifted in place.
        fit: The fit, for which timers each contact keeps time by.
        apart: ``(timer, other, share of a step)``: ``timer``'s band
            shifted so that it starts that share after ``other``.

    Returns:
        The timers' starts.
    """
    band = list(range(len(turned)))

    def root(t: int) -> int:
        """The timer that stands for ``t``'s band (union-find)."""
        while band[t] != t:
            band[t] = band[band[t]]
            t = band[t]
        return t

    for u, v in zip(fit.timed_first, fit.timed_second):
        band[root(int(u))] = root(int(v))
    for timer, other, share in apart:
        mine, theirs = root(timer), root(other)
        if mine == theirs:
            continue
        shift = turned[other] + share - turned[timer]
        turned[[t for t in range(len(turned)) if root(t) == mine]] += shift
        band[mine] = theirs
    return turned


def _orient(
    machine: BraidingMachine,
    placed: dict[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    """Settle a ring layout's handedness so it comes out the same every time.

    A graph layout solver is free to hand back a machine or its mirror image,
    and which one it chooses can change with the solver's version.  That is not
    a cosmetic difference here: a machine's connection slots are chosen to face
    its neighbours in a particular layout, so a mirrored one leaves every slot
    pointing at the wrong side and reverses which way its carriers circulate.

    Rings are therefore always laid out running clockwise in screen
    coordinates, by flipping the result when it comes back the other way.  The
    choice is arbitrary, but it has to be made somewhere and the machines'
    connection slots are written against it.
    """
    cycles = nx.cycle_basis(machine.graph)
    if not cycles:
        return placed

    # Walk the ring in a settled order — from its first gear by name, towards
    # whichever of its two neighbours sorts first — so the sign below means the
    # same thing whatever order the cycle was handed back in.
    ring = max(cycles, key=len)
    members = set(ring)
    start = min(ring)
    walk = [start]
    previous = None
    current = start
    while len(walk) < len(ring):
        neighbors = sorted(
            n
            for n in machine.graph.neighbors(current)
            if n in members and n != previous
        )
        if not neighbors:
            return placed
        previous, current = current, neighbors[0]
        walk.append(current)

    area = 0.0
    for i, name in enumerate(walk):
        x1, y1 = placed[name]
        x2, y2 = placed[walk[(i + 1) % len(walk)]]
        area += x1 * y2 - x2 * y1

    if area <= 0:
        return placed
    return {name: (x, -y) for name, (x, y) in placed.items()}


def _spread(back: float | None, n_onward: int) -> list[float]:
    """Directions out of a gear for the gears placed from it.

    The layout grows out from the first gear (:func:`_layout_bfs`): each
    other gear is placed from a neighbour already placed, and ``back`` is
    the direction from the gear to that neighbour, None for the first gear.
    The ``n_onward`` gears placed from it go evenly round it with the way
    back, so one carries straight on and two branch at ±60°; round the
    whole of the first gear, the first to the right."""
    if back is None:
        return [2 * math.pi * i / n_onward for i in range(n_onward)]
    if n_onward == 1:
        # Straight on, the way it came in, to the last bit: a chain stays on
        # the x-axis exactly.
        return [back - math.pi]
    return [back + 2 * math.pi * (i + 1) / (n_onward + 1) for i in range(n_onward)]


def _layout_bfs(
    machine: BraidingMachine,
    scale: float = 1.0,
    directions=None,
) -> dict[str, tuple[float, float]]:
    """Exact tangential layout for tree graphs via BFS.

    The first gear at the origin; then, gear by gear, outwards, each gear's
    neighbours not yet placed round it, each rim touching its own, in the
    directions :func:`_spread` gives — a chain carries straight on along the
    x-axis, a gear with several neighbours onward branches.

    Args:
        machine: The machine, its gears in a tree.
        scale: Overall scale factor.
        directions: How to choose the directions out of a gear for its
            gears placed from it instead: called with the gear, the direction
            back to the neighbour it was placed from (None for the first
            gear) and the neighbours to place from it, it gives a direction
            for each.
    Returns:
        Gear name -> (x, y).
    """
    radii = gear_radii(machine, scale)
    root = next(iter(machine.gears))
    choose = directions or (lambda gear, back, onward: _spread(back, len(onward)))

    pos: dict[str, tuple[float, float]] = {root: (0.0, 0.0)}
    back: dict[str, float | None] = {root: None}
    queue: deque = deque([root])
    while queue:
        gear = queue.popleft()
        onward = sorted(n for n in machine.graph.neighbors(gear) if n not in pos)
        x, y = pos[gear]
        for placed, angle in zip(onward, choose(gear, back[gear], onward)):
            apart = radii[gear] + radii[placed]
            pos[placed] = (x + apart * math.cos(angle), y + apart * math.sin(angle))
            back[placed] = angle + math.pi
            queue.append(placed)
    return pos


def axial_position(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
    axial: Axial,
) -> tuple[float, float]:
    """Where an axial's column stands: the centroid of the gears it anchors to.

    One gear gives that gear's own centre; a ring of gears gives the centre of
    the hole they enclose.

    Args:
        machine: The machine the axial belongs to.
        layout: Gear centre positions from compute_layout.
        axial: The axial to place.

    Returns:
        (x, y) of the column in layout coordinates.
    """
    xs = [layout[name][0] for name in axial.anchor]
    ys = [layout[name][1] for name in axial.anchor]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def axial_positions(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    """Column position for every axial on the machine, keyed by axial name."""
    return {a.name: axial_position(machine, layout, a) for a in machine.axials}


def axial_clearance(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
    position: tuple[float, float],
    scale: float = 1.0,
) -> float:
    """Free space around a column: the distance to the nearest carrier path.

    Carriers on a gear ride that gear's rim, so the distance from a point to
    the nearest carrier is ``|distance to the centre - radius|``, minimised
    over every gear.  The one expression covers both anchors: a column at a
    gear's centre clears that gear's radius, while a column in a tube clears
    the gap between the hole's centre and the surrounding rims.

    A value at or below zero means carriers pass through the column in this
    projection.  That is a genuine clash for a tube core, but expected for a
    flat braid, whose core rises through the convergence point where the
    carriers meet.

    Args:
        machine: The machine.
        layout: Gear centre positions from compute_layout.
        position: The column's (x, y).
        scale: Scale factor (must match the one used for the layout).

    Returns:
        Clearance in layout units.
    """
    px, py = position
    radii = gear_radii(machine, scale)
    return min(
        abs(math.hypot(layout[name][0] - px, layout[name][1] - py) - radii[name])
        for name in machine.gears
    )


def contact_point(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
    gear: str,
    neighbor: str,
    scale: float = 1.0,
) -> tuple[float, float]:
    """The middle of the notch two gears share.

    Where the circles cross, the notch is the chord between the two crossings
    and the bobbin sits at its middle — which lies on the line between the two
    centres.  Where the circles merely touch, the two crossings coincide and
    that middle is the tangent point, so one construction serves both.
    """
    cx, cy = layout[gear]
    nx_, ny_ = layout[neighbor]
    dx, dy = nx_ - cx, ny_ - cy
    dist = math.hypot(dx, dy) or 1.0

    radii = gear_radii(machine, scale)
    along = (dist**2 + radii[gear] ** 2 - radii[neighbor] ** 2) / (2 * dist)
    return cx + along * dx / dist, cy + along * dy / dist


def contact_angle(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
    gear: str,
    neighbor: str,
    scale: float = 1.0,
) -> float:
    """Angle (rad) from a gear's centre toward the notch it shares with a neighbour."""
    cx, cy = layout[gear]
    px, py = contact_point(machine, layout, gear, neighbor, scale)
    return math.atan2(py - cy, px - cx)


def carrier_radius(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
    gear: str,
    scale: float = 1.0,
) -> float:
    """How far from a gear's centre its bobbins ride.

    A bobbin sits *in* a notch, so it turns about the gear at the distance of
    that notch — the gear's own radius when the gears merely touch, and less
    than that when they overlap and the notch is cut back inside the rim.
    """
    radius = gear_radii(machine, scale)[gear]
    contacts = machine.connections_of(gear)
    if not contacts or not machine.gears_interpenetrate:
        # Gears that only touch carry their bobbins on the rim.  Saying so
        # outright keeps them exactly there, rather than a fraction off it
        # because a numerically solved layout left the circles a hair apart.
        return radius

    cx, cy = layout[gear]
    distances = [
        math.dist(
            (cx, cy),
            contact_point(
                machine,
                layout,
                gear,
                conn.gear_b if conn.gear_a == gear else conn.gear_a,
                scale,
            ),
        )
        for conn in contacts
    ]
    return sum(distances) / len(distances)


def _contacts(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
) -> dict[str, list[tuple[float, float]]]:
    """Per gear, each of its contacts: the angle on the gear of the slot that
    is there at every step, ``2π*slot0/N`` — or, for a contact handing over
    ``phase`` of the way through a step, the angle at the step's start of
    the slot there then, a ``phase`` of a slot back — and the contact's
    angle on the deck, seen from the gear's centre."""
    contacts: dict[str, list[tuple[float, float]]] = {
        name: [] for name in machine.gears
    }
    for conn in machine.connections:
        for gname, other, slot0 in [
            (conn.gear_a, conn.gear_b, conn.slot_a0),
            (conn.gear_b, conn.gear_a, conn.slot_b0),
        ]:
            gear = machine.gears[gname]
            contacts[gname].append(
                (
                    2 * math.pi * (slot0 + gear.direction * conn.phase) / gear.n_slots,
                    contact_angle(machine, layout, gname, other),
                )
            )
    return contacts


def _gear_constraints(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
) -> dict[str, list[float]]:
    """Per gear, the rotation offset each of its connections asks for.

    A connection ``gear_a[slot_a0] ↔ gear_b[slot_b0]`` wants slot ``slot_a0`` of
    gear_a to point at gear_b, i.e. ``phi_a = theta_ab - 2π*slot_a0/N_a``.  A
    gear with several connections gets one such value per connection; they all
    agree only when the connection slots match the physical layout.
    """
    return {
        name: [theta - slot for slot, theta in contacts]
        for name, contacts in _contacts(machine, layout).items()
    }


def slot_offsets(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
) -> dict[str, float]:
    """Per-gear rotation offset phi so connection slots point toward their neighbors.

    Every connection of a gear is taken into account, via the circular mean of
    the offsets they each ask for.  When the machine's connection slots match
    its layout the requests coincide and the mean reproduces them exactly; when
    they do not, the residual error is shared between the contacts instead of
    being dumped entirely onto whichever connection happened to come second.
    """
    offsets: dict[str, float] = {}
    for name, wanted in _gear_constraints(machine, layout).items():
        if not wanted:
            offsets[name] = 0.0
            continue
        sin_sum = sum(math.sin(a) for a in wanted)
        cos_sum = sum(math.cos(a) for a in wanted)
        # Degenerate: requests cancel out (e.g. exactly opposed).  The mean is
        # meaningless there, so honour the first connection rather than spin.
        if math.hypot(sin_sum, cos_sum) < 1e-9:
            offsets[name] = wanted[0]
        else:
            offsets[name] = math.atan2(sin_sum, cos_sum)
    return offsets


def offset_residuals(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
) -> dict[str, float]:
    """Worst angular error (radians) between each gear's slots and its contacts.

    Zero means every contact of that gear falls exactly on a slot.  A non-zero
    value means its slots, turned rigidly, cannot meet every contact, as where
    a line of gears bends; :class:`GearAngles` then draws them spread
    unevenly, so that carriers do not jump when they transfer there.
    """
    offsets = slot_offsets(machine, layout)
    residuals: dict[str, float] = {}
    for name, wanted in _gear_constraints(machine, layout).items():
        phi = offsets[name]
        residuals[name] = max(
            (abs((a - phi + math.pi) % (2 * math.pi) - math.pi) for a in wanted),
            default=0.0,
        )
    return residuals


#: How far (radians) a gear's slots may miss its contacts and still be drawn
#: turned rigidly: rounding, not a bend.
FITS = 1e-9


@dataclass(frozen=True)
class GearAngles:
    """Where a gear's slots are drawn on the deck, from their angle on the gear.

    A gear's slots are evenly spaced round it and turn at its rate, and are
    drawn turned by its offset (:func:`slot_offsets`).  That puts a slot on
    every contact at every step only when the contacts are a whole number of
    slots apart round the gear, as on a straight line of gears.  Where a line
    bends at a gear they are not, so its slots are drawn spread unevenly
    instead: the slot at a contact is always drawn on it, and those between
    two contacts evenly between their angles.  A carrier rounds the outside of
    the bend a little faster than the inside, then, and is handed on where it
    is, without jumping.  Which slot is where is the machine's; only the
    drawing changes (see :func:`offset_residuals`).

    Args:
        offset: The gear's offset, from :func:`slot_offsets`.
        knots: Each contact as (angle of its slot on the gear, angle on the
            deck), in order round the gear; empty where turning the slots
            rigidly by ``offset`` puts one on every contact.
    """

    offset: float
    knots: tuple[tuple[float, float], ...] = ()

    def __call__(self, angle: float) -> float:
        """The angle on the deck of a slot at ``angle`` on the gear."""
        if len(self.knots) < 2:
            return self.offset + angle
        turn = 2 * math.pi
        # Where on the gear, in [0, 2π): rounding can carry ``%`` to 2π.
        angle %= turn
        if angle >= turn:
            angle = 0.0
        # The last knot at or before it, the one before the first if none is.
        k = bisect.bisect_right([slot for slot, _ in self.knots], angle) - 1
        here, at = self.knots[k]
        there, to = self.knots[(k + 1) % len(self.knots)]
        span = (there - here) % turn or turn
        return at + ((to - at) % turn or turn) * ((angle - here) % turn) / span


def slot_angles(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
) -> dict[str, GearAngles]:
    """How each gear's slots are drawn: see :class:`GearAngles`.

    Args:
        machine: The machine definition.
        layout: Gear centres, from :func:`compute_layout`.

    Returns:
        Gear name -> its :class:`GearAngles`.
    """
    offsets = slot_offsets(machine, layout)
    residuals = offset_residuals(machine, layout)
    angles = {}
    for name, contacts in _contacts(machine, layout).items():
        if residuals[name] <= FITS:
            angles[name] = GearAngles(offsets[name])
            continue
        # One knot a slot: two contacts on one slot are one point.
        knots = dict(sorted(contacts))
        angles[name] = GearAngles(offsets[name], tuple(knots.items()))
    return angles


def _signed_area(
    face: list[str],
    layout: dict[str, tuple[float, float]],
) -> float:
    """Shoelace area of a face's polygon; sign gives its winding direction."""
    total = 0.0
    for i, name in enumerate(face):
        x1, y1 = layout[name]
        x2, y2 = layout[face[(i + 1) % len(face)]]
        total += x1 * y2 - x2 * y1
    return total / 2


def tube_rings(
    machine: BraidingMachine,
    layout: Optional[dict[str, tuple[float, float]]] = None,
) -> list[list[str]]:
    """Find the rings of gears that enclose a hole — one per tube.

    Gears are tangent circles in the plane, so the connection graph is planar
    and the holes in the machine are exactly the *bounded faces* of its planar
    embedding.  Every face is walked and the outer one — the space around the
    machine rather than a hole inside it — is dropped, being the largest by
    absolute signed area.

    A flat braid has no cycle and so returns no rings; a ring braid returns
    one; a grid of gears returns one per opening.

    Args:
        machine: The machine to inspect.
        layout: Gear centre positions (computed if None).

    Returns:
        List of rings, each a list of gear names in the order they enclose
        the hole.  Empty if the machine has no hole.
    """
    if layout is None:
        layout = compute_layout(machine)

    is_planar, embedding = nx.check_planarity(machine.graph)
    if not is_planar:
        return []

    seen: set = set()
    found: list[list[str]] = []
    for u, v in embedding.edges():
        if (u, v) in seen:
            continue
        face = embedding.traverse_face(u, v, mark_half_edges=seen)
        if len(face) >= 3:
            found.append(list(face))

    if not found:
        return []
    outer = max(found, key=lambda f: abs(_signed_area(f, layout)))
    return [f for f in found if f is not outer]


def tube_axials(
    machine: BraidingMachine,
    layout: Optional[dict[str, tuple[float, float]]] = None,
    min_clearance: float = 1e-6,
    prefix: str = "core",
) -> list[Axial]:
    """One core Axial per tube the machine braids.

    Rings too tight to hold a core — where the surrounding gears reach the
    centre of the hole — are skipped rather than returned, so the result is
    only cores that physically fit.

    Args:
        machine: The machine to inspect.
        layout: Gear centre positions (computed if None).
        min_clearance: Smallest acceptable gap between core and carriers.
        prefix: Name stem; cores are named ``core``, ``core_1``, … in order.

    Returns:
        List of Axial, empty for a machine with no tube.
    """
    if layout is None:
        layout = compute_layout(machine)

    axials: list[Axial] = []
    for ring in tube_rings(machine, layout):
        candidate = Axial(name=prefix, anchor=tuple(ring))
        position = axial_position(machine, layout, candidate)
        if axial_clearance(machine, layout, position) < min_clearance:
            continue
        name = prefix if not axials else f"{prefix}_{len(axials)}"
        axials.append(Axial(name=name, anchor=tuple(ring)))
    return axials


# Gear centres as many decimals alike as this are one axle: a split gear's
# parts, placed on it by the same sums.
_CENTER_DIGITS = 9


def _axle(layout: dict[str, tuple[float, float]], name: str) -> tuple[float, float]:
    """The axle a gear turns on, the same for a split gear's parts."""
    x, y = layout[name]
    return round(x, _CENTER_DIGITS), round(y, _CENTER_DIGITS)


def axial_spots(
    machine: BraidingMachine,
    layout: Optional[dict[str, tuple[float, float]]] = None,
) -> list[Axial]:
    """Every place the machine could feed an axial yarn, loaded or not.

    Up each gear's hollow spindle, at its centre — once for the parts of a
    split gear, which share an axle, named by its first part — and down the
    hole of each ring of gears that leaves room for one (:func:`tube_axials`).
    Which of them a machine braids round is its :attr:`~braidpy.horn_gear
    .model.BraidingMachine.axials`.

    Args:
        machine: The machine to inspect.
        layout: Gear centre positions (computed if None).

    Returns:
        The gears' spots, in the machine's order, then the rings'.
    """
    if layout is None:
        layout = compute_layout(machine)
    spots: list[Axial] = []
    centers: set[tuple[float, float]] = set()
    for name in machine.gears:
        center = _axle(layout, name)
        if center in centers:
            continue
        centers.add(center)
        spots.append(Axial(f"axial_{name}", (name,)))
    return spots + tube_axials(machine, layout)


def ring_core(
    machine: BraidingMachine,
    layout: Optional[dict[str, tuple[float, float]]] = None,
) -> Axial | None:
    """The core a machine that is one ring of gears braids round: down the
    hole the ring encloses, as a tubular machine's or a lace machine's.

    Only a ring of every gear makes a tube: a line folded round, as the
    multiband machine's, encloses a hole between its gears too, but braids
    flat bands, not round it.

    Args:
        machine: The machine.
        layout: Gear centre positions (computed if None).

    Returns:
        The core, named ``centre``; None if the machine is not one ring, or
        its hole has no room for a core.
    """
    for core in tube_axials(machine, layout, prefix="centre"):
        if set(core.anchor) == set(machine.gears):
            return core
    return None


def gear_radii(machine: BraidingMachine, scale: float = 1.0) -> dict[str, float]:
    """Return the visual radius for each gear.

    Args:
        machine: The BraidingMachine.
        scale: Scale factor.

    Returns:
        Dict mapping gear name → radius.
    """
    radii = {
        name: _gear_radius(gear.size or gear.n_slots, scale)
        for name, gear in machine.gears.items()
    }
    # A machine that has solved its own geometry draws as it solved it, and
    # gears in a ring as their layout drew them to touch (ring_geometry).
    preferred = machine.preferred_gear_radii(scale)
    if preferred:
        radii.update({name: r for name, r in preferred.items() if name in radii})
    elif (
        len(machine.gears) > 1
        and machine.preferred_layout(scale) is None
        and not nx.is_forest(machine.graph)
    ):
        radii.update(ring_geometry(machine, scale)[1])
    return radii


def carrier_xy(
    machine: BraidingMachine,
    layout: dict[str, tuple[float, float]],
    angles: dict[str, GearAngles],
    carrier_radii: dict[str, float],
    position: tuple[str, int],
    time: int,
    frac: float = 0.0,
) -> tuple[float, float]:
    """Where in the plane a carrier is, at continuous time ``time + frac``.

    A carrier rides in a horn of its gear, so its angle is simply that slot's
    angle: it turns with the gear and always sits on its slot, drawn where
    :class:`GearAngles` draws it.
    It is drawn on whatever is actually moving it this step — on a machine
    with shared slots that is the receiving gear, see
    :meth:`~braidpy.horn_gear.model.BraidingMachine.riding_position`.

    Transfers stay continuous without any special casing: a carrier moves to
    the neighbour only at the step where its slot is at the contact point, and
    it lands on the neighbour's slot that is at that same contact point at that
    same instant, so the two coincide; where a line bends at a gear, its
    slots are drawn so that they still do (:class:`GearAngles`).

    Args:
        machine: The machine definition.
        layout: Gear centres, from :func:`compute_layout`.
        angles: How each gear's slots are drawn, from :func:`slot_angles`.
        carrier_radii: Per-gear riding radius, from :func:`carrier_radius`.
        position: The carrier's recorded (gear, slot) at ``time``.
        time: The step being taken.
        frac: How far into that step, from 0 to 1.

    Returns:
        The carrier's (x, y).
    """
    gear_name, slot = machine.riding_position(position, time, frac)
    cx, cy = layout[gear_name]
    r = carrier_radii[gear_name]
    ang = angles[gear_name](machine.slot_angle(gear_name, slot, time, frac))
    return cx + r * math.cos(ang), cy + r * math.sin(ang)
