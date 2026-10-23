# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Making a braid crossing by crossing — beaten up, row by row, with
friction: ``web/form.js``, in Python.

The same algorithm, step for step, in the same order
(``tests/test_rope_python.py`` runs both and compares them).
:func:`braidpy.rope.settle` beats a whole laid braid up at once.  Here the
braid is made from its oldest row up, as a braid is made: its yarns as laid
by braidpy, in the order their crossings are made, so the crossings are the
right ones.

The yarns are in three parts:

- made: below a working window, the braid already beaten up, frozen;
- working: the window, a row or two, where the yarns move — the same
  stretching, bending and contact as :mod:`braidpy.rope`, plus friction;
- to come: above it, the rest of the braid as laid, moving as one block.
  The yarns' tension draws it down onto the window, a weight draws it up:
  while the yarns pull harder, the newest row is beaten up against the made
  braid, until its crossings jam.

Each yarn slides into the window from the block at its tension, as from a
bobbin.  Once a row is beaten up, the lower part of the window is frozen
into the made braid, and the window takes in the next row from the block.

Friction: two yarns in contact hold each other along their surfaces with a
spring from where they first touched, until its pull reaches mu times the
push between them, when they slip (Coulomb's law, as the discrete element
method has it).  It is what keeps a beaten crossing where it was beaten.

The window is settled by FIRE, with :mod:`braidpy.rope`'s own mechanics, as
``form.js`` uses ``rope.js``'s.  Lengths are in yarn diameters.  Pure
Python, and slow: for checking, not for long braids.

References:

- Friction as a tangential spring, capped by Coulomb's law: P. A. Cundall
  and O. D. L. Strack, "A discrete numerical model for granular
  assemblies", Géotechnique 29, 47 (1979),
  https://doi.org/10.1680/geot.1979.29.1.47 (not free to read).  The same
  tangential spring, among other contact models, free to read: "Review of
  contact models used in Discrete Element Method (DEM)",
  https://arxiv.org/abs/2509.07461.
- FIRE, and the contact geometry: see :mod:`braidpy.rope`.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import Any

from braidpy.rope import (
    fire_mix,
    fire_sums,
    move_beads,
    near_pairs,
    relay,
    spread,
    stale,
    steer,
    stretch_and_bend,
    touching,
)

__all__ = ["form"]

# Bead names in a friction spring's key: the first times this, plus the
# second.
_KEY = 4194304


@dataclass
class _Bead:
    p: list[float]
    id: int


@dataclass
class _Yarn:
    made: list[_Bead]
    working: list[_Bead]
    to_come: list[_Bead]
    rest: float | None = None


@dataclass
class _Outcome:
    done: bool
    steps: int
    relay: list[int] = field(default_factory=list)


def form(
    yarns: Sequence[Sequence[float]],
    row: float,
    friction: float = 0.3,
    feed: float = 1.0,
    weight: float | None = None,
    stretch: float = 100.0,
    bend: float = 0.5,
    contact: float = 100.0,
    soft: float = 5.0,
    shell: float = 0.1,
    grip: float = 20.0,
    keep: float = 2.0,
    window: float = 2.0,
    steps_per_row: int = 4000,
    tolerance: float = 2e-3,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> dict[str, Any]:
    """A braid made crossing by crossing: ``form.js``'s ``form``.

    Args:
        yarns: Each yarn's points, x y z after x y z, its oldest end first,
            rising: the braid as laid.
        row: Height of a row as laid.
        friction: mu; 0 for none.
        feed: T, each yarn's tension.
        weight: W, drawing the braid off, all yarns together; by default a
            quarter of the yarns' tension.
        stretch: k_s.
        bend: k_b.
        contact: k_c, the cores'.
        soft: k_r, the soft surfaces'.
        shell: w, how thick the soft surface is, of a diameter.
        grip: k_t, the friction springs' stiffness.
        keep: How much of the window, at its top, is not frozen once a row
            is made.
        window: How many rows the window starts with.
        steps_per_row: The most steps to settle a row (three times as many
            for the last).
        tolerance: A row is settled once no force is larger.
        progress: Told, after each row, the yarns and how far along.

    Returns:
        ``yarns`` as made; the block's ``offset``; the ``steps`` taken;
        ``deepestEver``, the deepest the cores ever pressed into each other;
        and how many ``stages``.
    """
    spacing = 0.5
    ks, kb, kc, kr = stretch, bend, contact, soft
    core = 1 - shell
    mu = friction
    kt = grip
    n_yarns = len(yarns)
    if weight is None:
        weight = 0.25 * n_yarns
    w_draw = weight

    # Each yarn: made beads (fixed), working beads, and beads to come, these
    # at their laid place lifted (or lowered) by the block's offset.
    next_id = 0
    chains: list[_Yarn] = []
    for points in yarns:
        laid = relay([float(c) for c in points], spacing)
        beads = []
        for i in range(0, len(laid), 3):
            beads.append(_Bead([laid[i], laid[i + 1], laid[i + 2]], next_id))
            next_id += 1
        chains.append(_Yarn(made=beads[:1], working=[], to_come=beads[1:]))
    state: dict[str, Any] = {"offset": 0.0, "deepestEver": 0.0}
    top = max(y.to_come[-1].p[2] for y in chains)
    # Friction springs, by pair of beads: their tangential stretch.
    grips: dict[int, list[float]] = {}

    def snapshot() -> list[list[float]]:
        out = []
        for y in chains:
            points: list[float] = []
            for b in y.made:
                points.extend(b.p)
            for b in y.working:
                points.extend(b.p)
            for b in y.to_come:
                points.extend([b.p[0], b.p[1], b.p[2] + state["offset"]])
            out.append(points)
        return out

    def relay_working(y: _Yarn) -> None:
        """A yarn's working beads laid out again, evenly, from its last made
        bead to its first bead to come; new beads get new names, and lose
        their friction springs."""
        nonlocal next_id
        start = y.made[-1].p
        following = y.to_come[0]
        end = [following.p[0], following.p[1], following.p[2] + state["offset"]]
        points = list(start)
        for b in y.working:
            points.extend(b.p)
        points.extend(end)
        out = relay(points, spacing)
        y.working = []
        for i in range(3, len(out) - 3, 3):
            y.working.append(_Bead([out[i], out[i + 1], out[i + 2]], next_id))
            next_id += 1
        y.rest = spacing

    def settle_window(max_steps: int, last: bool) -> int:
        """FIRE on the window, with the block and each yarn's rest length."""
        relays = 0
        while True:
            outcome = run(max_steps, last)
            if outcome.done:
                return outcome.steps
            relays += 1
            if relays > 50:
                return outcome.steps
            # Lay out again the working beads of yarns whose links have
            # grown too long or too short, from the made braid to the block.
            for a in outcome.relay:
                relay_working(chains[a])

    def run(max_steps: int, last: bool) -> _Outcome:
        # Flat lists: working beads, then the obstacles near them: made
        # beads just below, beads to come just above.
        offset = state["offset"]
        low, high = math.inf, -math.inf
        for y in chains:
            for b in y.working:
                low = min(low, b.p[2])
                high = max(high, b.p[2])
        spans: list[list[int]] = []  # per yarn: first bead, count, made
        xs: list[float] = []
        ids: list[int] = []
        kinds: list[int] = []  # 0 made, 1 working, 2 to come
        of_yarn: list[int] = []
        rest_of: list[float] = []

        def push(p: Sequence[float], name: int, kind: int, a: int) -> None:
            xs.extend([p[0], p[1], p[2]])
            ids.append(name)
            kinds.append(kind)
            of_yarn.append(a)

        for a, y in enumerate(chains):
            # A chain per yarn: the last made beads (near), the working
            # beads, the first beads to come (near).
            start = len(xs) // 3
            first_made = len(y.made) - 1
            while first_made > 0 and y.made[first_made - 1].p[2] > low - 2:
                first_made -= 1
            for i in range(first_made, len(y.made)):
                push(y.made[i].p, y.made[i].id, 0, a)
            for b in y.working:
                push(b.p, b.id, 1, a)
            last_to_come = 0
            while (
                last_to_come < len(y.to_come) - 1
                and y.to_come[last_to_come + 1].p[2] + offset < high + 2
            ):
                last_to_come += 1
            for i in range(min(last_to_come, len(y.to_come) - 1) + 1):
                b = y.to_come[i]
                push([b.p[0], b.p[1], b.p[2] + offset], b.id, 2, a)
            spans.append([start, len(xs) // 3 - start, len(y.made) - first_made])
            rest_of.append(y.rest if y.rest is not None else spacing)
        n = len(ids)
        x = list(xs)
        kind = kinds
        yarn_of = of_yarn
        s = list(rest_of)
        # Working links of each yarn: from its last made bead to its first
        # bead to come.
        link_from = [0] * n_yarns
        link_to = [0] * n_yarns
        for a, (start, count, made) in enumerate(spans):
            link_from[a] = start + made - 1
            link_to[a] = start + made + len(chains[a].working)  # first to come
            if link_to[a] >= start + count:
                link_to[a] = start + count - 1
        links = [float(max(1, link_to[a] - link_from[a])) for a in range(n_yarns)]
        base = list(x)  # the block's beads, before it moves
        block = 0.0  # the block's move this run

        # Segments: consecutive beads of a chain.
        segs: list[int] = []
        for start, count, _ in spans:
            segs.extend(range(start, start + count - 1))
        gap = math.ceil(2 / spacing) + 1
        reach = 1 + 2 * spacing + 0.5
        pairs: list[int] = []
        built = [0.0] * (3 * n)
        cells = [0] * (3 * n)

        def movable(g: int, h: int) -> bool:
            """Something in a pair must be able to move: a working bead, or
            the block against the made braid."""
            return (
                kind[g] == 1
                or kind[g + 1] == 1
                or kind[h] == 1
                or kind[h + 1] == 1
                or ((kind[g] == 2 or kind[h] == 2) and kind[g] != kind[h])
            )

        keys_here: set[int] = set()

        def neighbours() -> None:
            nonlocal pairs, keys_here
            pairs = near_pairs(x, segs, yarn_of, gap, reach, cells, movable)
            built[:] = x
            # The pairs this window can see: springs of other pairs are kept.
            keys_here = {
                ids[pairs[e]] * _KEY + ids[pairs[e + 1]]
                for e in range(0, len(pairs), 2)
            }

        f = [0.0] * (3 * n)
        fs = [0.0] * n_yarns
        v = [0.0] * (3 * n)
        vs = [0.0] * n_yarns
        touched: set[int] = set()
        now: dict[str, float] = {"dt": 0.0, "deepest": 0.0, "blockForce": 0.0}

        def touch(
            e: int, u: float, w: float, px: float, py: float, pz: float, r2: float
        ) -> None:
            """A contact: the cores' and soft surfaces' push along the line
            between the closest points, and friction across it."""
            g, h = pairs[e], pairs[e + 1]
            i, j = 3 * g, 3 * h
            key = ids[g] * _KEY + ids[h]
            r = math.sqrt(r2)
            push = kr * (1 - r)
            if r < core:
                now["deepest"] = max(now["deepest"], core - r)
                push += kc * (core - r)
            nx = px / max(r, 1e-9)
            ny = py / max(r, 1e-9)
            nz = pz / max(r, 1e-9)
            qx, qy, qz = push * nx, push * ny, push * nz
            if mu > 0:
                # Friction: the tangential spring, stretched by how the
                # contact points slid past each other this step.
                touched.add(key)
                spring = grips.get(key)
                if spring is None:
                    spring = grips[key] = [0.0, 0.0, 0.0]
                vx = (1 - u) * v[i] + u * v[i + 3] - (1 - w) * v[j] - w * v[j + 3]
                vy = (
                    (1 - u) * v[i + 1]
                    + u * v[i + 4]
                    - (1 - w) * v[j + 1]
                    - w * v[j + 4]
                )
                vz = (
                    (1 - u) * v[i + 2]
                    + u * v[i + 5]
                    - (1 - w) * v[j + 2]
                    - w * v[j + 5]
                )
                spring[0] += vx * now["dt"]
                spring[1] += vy * now["dt"]
                spring[2] += vz * now["dt"]
                # Kept in the contact's tangent plane.
                along = spring[0] * nx + spring[1] * ny + spring[2] * nz
                spring[0] -= along * nx
                spring[1] -= along * ny
                spring[2] -= along * nz
                tx, ty, tz = -kt * spring[0], -kt * spring[1], -kt * spring[2]
                size = math.hypot(tx, ty, tz)
                most = mu * push
                if size > most:
                    # Slipping: the spring gives way to what friction holds.
                    k = most / size
                    tx *= k
                    ty *= k
                    tz *= k
                    spring[0] *= k
                    spring[1] *= k
                    spring[2] *= k
                qx += tx
                qy += ty
                qz += tz
            spread(f, i, j, u, w, qx, qy, qz)

        def forces(dt: float) -> None:
            f[:] = [0.0] * (3 * n)
            fs[:] = [0.0] * n_yarns
            for a in range(n_yarns):
                strain = stretch_and_bend(x, f, link_from[a], link_to[a], s[a], ks, kb)
                fs[a] = ks * strain - feed * links[a]
            now["deepest"] = 0.0
            touched.clear()
            now["dt"] = dt
            touching(x, pairs, touch)
            # Contacts that came apart let go of their springs.
            for key in keys_here:
                if key not in touched:
                    grips.pop(key, None)
            # The block: the weight, and what the window does to its beads.
            block_force = w_draw
            for g in range(n):
                if kind[g] == 2:
                    block_force += f[3 * g + 2]
            if last:
                block_force = w_draw + min(0.0, block_force - w_draw)
            now["blockForce"] = block_force

        def keep_state() -> None:
            state["offset"] += block
            for a, y in enumerate(chains):
                start, _, made = spans[a]
                for k, b in enumerate(y.working):
                    g = start + made + k
                    b.p = [x[3 * g], x[3 * g + 1], x[3 * g + 2]]
                y.rest = s[a]

        dt, alpha, downhill = 0.01, 0.1, 0
        v_block = 0.0
        working = [1 if k == 1 else 0 for k in kind]
        sums = [0.0] * 4
        neighbours()
        step = 0
        while step < max_steps:
            if stale(x, built):
                neighbours()
            forces(dt)
            state["deepestEver"] = max(state["deepestEver"], now["deepest"])
            block_force = now["blockForce"]
            sums[0] = block_force * v_block
            sums[1] = block_force * block_force
            sums[2] = v_block * v_block
            sums[3] = abs(block_force) / n_yarns
            fire_sums(f, v, working, fs, vs, links, sums)
            if sums[3] < tolerance:
                break
            mix = fire_mix(sums, alpha)
            steer(v, f, working, vs, fs, alpha, mix)
            v_block = (1 - alpha) * v_block + mix * block_force
            if sums[0] > 0:
                downhill += 1
                if downhill > 5:
                    dt = min(dt * 1.1, 0.05)
                    alpha *= 0.99
            else:
                downhill = 0
                dt *= 0.5
                alpha = 0.1
                v[:] = [0.0] * (3 * n)
                vs[:] = [0.0] * n_yarns
                v_block = 0.0
            move_beads(x, v, f, dt, working)
            # The block moves as one, its beads' velocity its own, for the
            # friction they feel.
            v_block += (dt * block_force) / n_yarns
            by = max(-0.1, min(0.1, dt * v_block))
            block += by
            for g in range(n):
                if kind[g] != 2:
                    continue
                x[3 * g + 2] = base[3 * g + 2] + block
                v[3 * g] = v[3 * g + 1] = 0.0
                v[3 * g + 2] = v_block
            again = []
            for a in range(n_yarns):
                vs[a] += (dt * fs[a]) / links[a]
                s[a] += max(-0.01, min(0.01, dt * vs[a]))
                if s[a] > 1.5 * spacing or s[a] < 0.6 * spacing:
                    again.append(a)
            if again:
                keep_state()
                return _Outcome(done=False, steps=step + 1, relay=again)
            step += 1
        keep_state()
        return _Outcome(done=True, steps=step)

    stage = 0
    steps = 0
    cut = window * row
    while True:
        # The next rows join the window, where they are now.
        for y in chains:
            while len(y.to_come) > 1 and y.to_come[0].p[2] <= cut:
                b = y.to_come.pop(0)
                y.working.append(
                    _Bead([b.p[0], b.p[1], b.p[2] + state["offset"]], b.id)
                )
        last = all(len(y.to_come) <= 1 for y in chains)
        steps += settle_window(steps_per_row * 3 if last else steps_per_row, last)
        stage += 1
        if progress is not None:
            progress(
                {
                    "stage": stage,
                    "fraction": min(1.0, cut / top),
                    "yarns": snapshot(),
                    "offset": state["offset"],
                }
            )
        if last:
            break
        # Freeze all but the top of the window.
        high = -math.inf
        for y in chains:
            for b in y.working:
                high = max(high, b.p[2])
        for y in chains:
            while len(y.working) > 2 and y.working[0].p[2] < high - keep:
                y.made.append(y.working.pop(0))
        cut += row

    return {
        "yarns": snapshot(),
        "offset": state["offset"],
        "steps": steps,
        "deepestEver": state["deepestEver"],
        "stages": stage,
    }
