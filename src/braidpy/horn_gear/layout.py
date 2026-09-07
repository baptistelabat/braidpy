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
from typing import Dict, Optional, Tuple

import networkx as nx
import numpy as np

from .model import BraidingMachine


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
