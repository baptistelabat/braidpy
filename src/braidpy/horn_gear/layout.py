# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/layout.py
===================

Automatic 2-D layout of horn gears from the connection graph.

Strategy: spring / Kamada-Kawai layout where the rest length of each
edge is proportional to (r_A + r_B), the sum of the two gear radii.
Gear radius is proportional to sqrt(n_slots) so that the disk area
scales linearly with slot count.
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

    return {n: (float(xy[0]), float(xy[1])) for n, xy in pos.items()}


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
