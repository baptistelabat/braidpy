# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/layout.py
===================

Where everything sits: gear centres, the notches between them, the circles a
carrier rides on, and the columns a braid forms around.

Gears are placed from the connection graph — BFS along the x-axis for a chain,
Kamada-Kawai for anything with a cycle — unless the machine pins its own
geometry, in which case :meth:`~braidpy.horn_gear.model.BraidingMachine
.preferred_layout` wins.  Gear radius goes as sqrt(n_slots), so disc area
scales with slot count and slot arcs stay about the same width.

Everything else here is derived from those centres: where two gears meet
(:func:`contact_point`), how far out a carrier rides (:func:`carrier_radius`),
how each gear must be turned for its slots to face its notches
(:func:`slot_offsets`) and by how much that fails when a machine's slots cannot
be reconciled with its layout (:func:`offset_residuals`).  It is all plain
geometry with no drawing in it, so it can be measured and tested directly.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Dict, List, Optional, Tuple

import networkx as nx
import numpy as np

from .model import Axial, BraidingMachine


def _gear_radius(n_slots: int, scale: float = 1.0) -> float:
    """Visual radius of a gear with n_slots slots.

    We use sqrt(n_slots) so area ∝ n_slots and slot arcs stay roughly
    constant width regardless of gear size.

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
    seed: Optional[int] = 42,
    iterations: int = 500,
) -> Dict[str, Tuple[float, float]]:
    """Compute 2-D positions for all gears with adjacent circles exactly tangential.

    For tree / path graphs (flat braid): BFS-based placement along the x-axis
    guarantees every pair of adjacent gear circles touches exactly.

    For cyclic graphs (tubular braid ring): Kamada-Kawai layout with edge
    rest-lengths = r_A + r_B, post-scaled so every edge equals its rest-length
    (valid when all gears have the same radius, i.e. same n_slots).

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

    # ── Cyclic graph: Kamada-Kawai + per-edge exact rescaling ─────────────────
    g = machine.graph.copy()
    for u, v in g.edges():
        r_u = _gear_radius(machine.gears[u].n_slots, scale)
        r_v = _gear_radius(machine.gears[v].n_slots, scale)
        g[u][v]["len"] = r_u + r_v

    try:
        raw = nx.kamada_kawai_layout(g, weight="len")
    except Exception:
        raw = nx.spring_layout(g, seed=seed, iterations=iterations)

    pos = {n: np.array(xy) for n, xy in raw.items()}

    # Rescale so the minimum-ratio edge is exactly its rest-length.
    min_ratio = float("inf")
    for u, v in g.edges():
        actual = float(np.linalg.norm(pos[u] - pos[v]))
        desired = g[u][v]["len"]
        if actual > 1e-9:
            min_ratio = min(min_ratio, desired / actual)

    if math.isfinite(min_ratio) and min_ratio > 0:
        pos = {n: xy * min_ratio for n, xy in pos.items()}

    placed = {n: (float(xy[0]), float(xy[1])) for n, xy in pos.items()}
    return _orient(machine, placed)


def _orient(
    machine: BraidingMachine,
    placed: Dict[str, Tuple[float, float]],
) -> Dict[str, Tuple[float, float]]:
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
        neighbours = sorted(
            n
            for n in machine.graph.neighbors(current)
            if n in members and n != previous
        )
        if not neighbours:
            return placed
        previous, current = current, neighbours[0]
        walk.append(current)

    area = 0.0
    for i, name in enumerate(walk):
        x1, y1 = placed[name]
        x2, y2 = placed[walk[(i + 1) % len(walk)]]
        area += x1 * y2 - x2 * y1

    if area <= 0:
        return placed
    return {name: (x, -y) for name, (x, y) in placed.items()}


def _layout_bfs(
    machine: BraidingMachine,
    scale: float = 1.0,
) -> Dict[str, Tuple[float, float]]:
    """Exact tangential layout for tree (path) graphs via BFS.

    Places gears left-to-right along the x-axis so every adjacent pair of
    gear circles touches exactly.  Works for any tree, including linear chains
    and branching topologies.
    """
    radii = {n: _gear_radius(g.n_slots, scale) for n, g in machine.gears.items()}
    root = next(iter(machine.gears))

    pos: Dict[str, Tuple[float, float]] = {root: (0.0, 0.0)}
    visited: set = {root}
    queue: deque = deque([(root, 0.0)])  # (node, parent_x + parent_r)

    while queue:
        parent, right_edge = queue.popleft()
        r_parent = radii[parent]
        cx_parent = pos[parent][0]

        unvisited = [n for n in machine.graph.neighbors(parent) if n not in visited]
        for child in sorted(unvisited):
            r_child = radii[child]
            cx_child = cx_parent + r_parent + r_child
            pos[child] = (cx_child, 0.0)
            visited.add(child)
            queue.append((child, cx_child))

    return pos


def axial_position(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    axial: Axial,
) -> Tuple[float, float]:
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
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, Tuple[float, float]]:
    """Column position for every axial on the machine, keyed by axial name."""
    return {a.name: axial_position(machine, layout, a) for a in machine.axials}


def axial_clearance(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    position: Tuple[float, float],
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
    layout: Dict[str, Tuple[float, float]],
    gear: str,
    neighbor: str,
    scale: float = 1.0,
) -> Tuple[float, float]:
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
    layout: Dict[str, Tuple[float, float]],
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
    layout: Dict[str, Tuple[float, float]],
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


def _gear_constraints(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, List[float]]:
    """Per gear, the rotation offset each of its connections asks for.

    A connection ``gear_a[slot_a0] ↔ gear_b[slot_b0]`` wants slot ``slot_a0`` of
    gear_a to point at gear_b, i.e. ``phi_a = theta_ab - 2π*slot_a0/N_a``.  A
    gear with several connections gets one such value per connection; they all
    agree only when the connection slots match the physical layout.
    """
    wanted: Dict[str, List[float]] = {name: [] for name in machine.gears}
    for conn in machine.connections:
        for gname, other, slot0 in [
            (conn.gear_a, conn.gear_b, conn.slot_a0),
            (conn.gear_b, conn.gear_a, conn.slot_b0),
        ]:
            gear = machine.gears[gname]
            theta = contact_angle(machine, layout, gname, other)
            wanted[gname].append(theta - 2 * math.pi * slot0 / gear.n_slots)
    return wanted


def slot_offsets(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, float]:
    """Per-gear rotation offset phi so connection slots point toward their neighbors.

    Every connection of a gear is taken into account, via the circular mean of
    the offsets they each ask for.  When the machine's connection slots match
    its layout the requests coincide and the mean reproduces them exactly; when
    they do not, the residual error is shared between the contacts instead of
    being dumped entirely onto whichever connection happened to come second.
    """
    offsets: Dict[str, float] = {}
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
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, float]:
    """Worst angular error (radians) between each gear's slots and its contacts.

    Zero means every contact of that gear falls exactly on a slot.  A non-zero
    value means the machine's connection slots cannot be reconciled with its
    layout, and carriers will appear to jump when they transfer there.
    """
    offsets = slot_offsets(machine, layout)
    residuals: Dict[str, float] = {}
    for name, wanted in _gear_constraints(machine, layout).items():
        phi = offsets[name]
        residuals[name] = max(
            (abs((a - phi + math.pi) % (2 * math.pi) - math.pi) for a in wanted),
            default=0.0,
        )
    return residuals


def _signed_area(
    face: List[str],
    layout: Dict[str, Tuple[float, float]],
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
    layout: Optional[Dict[str, Tuple[float, float]]] = None,
) -> List[List[str]]:
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
    found: List[List[str]] = []
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
    layout: Optional[Dict[str, Tuple[float, float]]] = None,
    min_clearance: float = 1e-6,
    prefix: str = "core",
) -> List[Axial]:
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

    axials: List[Axial] = []
    for ring in tube_rings(machine, layout):
        candidate = Axial(name=prefix, anchor=tuple(ring))
        position = axial_position(machine, layout, candidate)
        if axial_clearance(machine, layout, position) < min_clearance:
            continue
        name = prefix if not axials else f"{prefix}_{len(axials)}"
        axials.append(Axial(name=name, anchor=tuple(ring)))
    return axials


def gear_radii(machine: BraidingMachine, scale: float = 1.0) -> Dict[str, float]:
    """Return the visual radius for each gear.

    Args:
        machine: The BraidingMachine.
        scale: Scale factor.

    Returns:
        Dict mapping gear name → radius.
    """
    return {
        name: _gear_radius(gear.n_slots, scale) for name, gear in machine.gears.items()
    }
