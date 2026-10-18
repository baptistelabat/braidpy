# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Yarns as elastic rods, settled by their own physics: ``web/rope.js``, in
Python.

The same algorithm, step for step, in the same order
(``tests/test_rope_python.py`` runs both and compares them); the model is
``rope.js``'s, and ``docs/source/rope_physics.md`` describes it.  In short,
each yarn is a chain of beads, and its energy is the sum of

- stretching: ``k_s/2 (|x_{i+1} - x_i| - s)²`` per link — stiff, so yarn barely
  stretches;
- bending: ``k_b/2 |x_{i-1} - 2 x_i + x_{i+1}|² / s²`` per bead — slight;
- contact, for any two segments of different yarns (or of one yarn, far
  apart along it): a yarn is a firm core inside a soft surface.  Closer than
  a diameter d, the surfaces press together, ``k_r/2 (d - r)²``; closer
  than d - w, the cores too, ``k_c/2 (d - w - r)²``, much stiffer;

and the ends' work.  The yarns' bottom ends are clamped; their top ends are
fixed to an end plate, drawn up by a force, which may turn about the axis.
The yarns may also be fed through the plate from bobbins pulling them back
with a tension T, their links' rest length then one more unknown.  The
minimum of that energy, the braid at rest, is found by FIRE (Bitzek et al.,
2006).  Lengths are in yarn diameters.

The mechanics (:func:`near_pairs` to :func:`move_beads`, and :func:`relay`)
are shared with :mod:`braidpy.form`, as ``rope.js`` shares them with
``form.js``.

It follows the JavaScript step for step: given the same numbers from the
maths library, it settles the same yarns, bead for bead.  The libraries
differ in the last place (Python's ``math.hypot`` is correctly rounded,
JavaScript's not always), and thousands of steps make that visible: the two
settle alike, not identically.  It is pure Python and slow — tens of times
slower than in a browser — which suits checking it, not settling long
braids.

References:

- FIRE: E. Bitzek, P. Koskinen, F. Gähler, M. Moseler, P. Gumbsch,
  "Structural relaxation made simple", Phys. Rev. Lett. 97, 170201 (2006).
- Closest points of two segments: C. Ericson, *Real-Time Collision
  Detection* (Morgan Kaufmann, 2005), §5.1.9.
- The grid of cells: M. Teschner, B. Heidelberger, M. Müller, D. Pomeranets,
  M. Gross, "Optimized spatial hashing for collision detection of deformable
  objects", Vision, Modeling, and Visualization (2003).  ``rope.js`` hashes
  the cells with three large primes; here a cell is its own key, which finds
  the same pairs in the same order.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

__all__ = ["relay", "settle"]

Touch = Callable[[int, float, float, float, float, float, float], None]


def _round(value: float) -> int:
    """JavaScript's ``Math.round``: halves round up."""
    return math.floor(value + 0.5)


# ----------------------------------------------------------------------
# What rope.py and form.py both do to yarns of beads, in flat lists: x the
# beads' places, x y z after x y z; segment g joins beads g and g + 1, and
# its offset in x is 3 g.


def near_pairs(
    x: Sequence[float],
    segs: Sequence[int],
    yarn_of: Sequence[int],
    gap: int,
    reach: float,
    cells: List[int],
    accept: Optional[Callable[[int, int], bool]] = None,
) -> List[int]:
    """Pairs of segments near enough to touch before the beads move a
    quarter diameter, found on a grid of cells ``reach`` wide: of ``segs``,
    neither two segments of a yarn closer than ``gap`` along it, nor a pair
    ``accept`` turns down.  ``cells`` holds three numbers a bead.

    Each segment is put in the cell of its midpoint, and compared with the
    segments of its own and the 26 neighbouring cells.  A pair is kept if its
    midpoints are within 2 reach: two segments a link long whose surfaces
    could touch have midpoints within a diameter and a link, and the margin
    left is what beads may move before the list is rebuilt (:func:`stale`).

    Returns:
        The pairs, flat: g, h, g, h, ...
    """
    grid: Dict[Tuple[int, int, int], List[int]] = {}
    for g in segs:
        i = math.floor((x[3 * g] + x[3 * g + 3]) / 2 / reach)
        j = math.floor((x[3 * g + 1] + x[3 * g + 4]) / 2 / reach)
        k = math.floor((x[3 * g + 2] + x[3 * g + 5]) / 2 / reach)
        cells[3 * g] = i
        cells[3 * g + 1] = j
        cells[3 * g + 2] = k
        grid.setdefault((i, j, k), []).append(g)
    found: List[int] = []
    for g in segs:
        i, j, k = cells[3 * g], cells[3 * g + 1], cells[3 * g + 2]
        for di in (-1, 0, 1):
            for dj in (-1, 0, 1):
                for dk in (-1, 0, 1):
                    near = grid.get((i + di, j + dj, k + dk))
                    if not near:
                        continue
                    for h in near:
                        if h <= g:
                            continue
                        if yarn_of[h] == yarn_of[g] and h - g < gap:
                            continue
                        # Near enough to touch before the list is rebuilt.
                        mx = x[3 * g] + x[3 * g + 3] - x[3 * h] - x[3 * h + 3]
                        my = x[3 * g + 1] + x[3 * g + 4] - x[3 * h + 1] - x[3 * h + 4]
                        mz = x[3 * g + 2] + x[3 * g + 5] - x[3 * h + 2] - x[3 * h + 5]
                        if mx * mx + my * my + mz * mz > 4 * reach * reach:
                            continue
                        if accept is not None and not accept(g, h):
                            continue
                        found.append(g)
                        found.append(h)
    return found


def stale(x: Sequence[float], built: Sequence[float]) -> bool:
    """Whether a bead has moved a quarter diameter since ``built``: the pairs
    near enough to touch want finding again."""
    for k in range(0, len(x), 3):
        dx, dy, dz = x[k] - built[k], x[k + 1] - built[k + 1], x[k + 2] - built[k + 2]
        if dx * dx + dy * dy + dz * dz > 0.0625:
            return True
    return False


def touching(x: Sequence[float], pairs: Sequence[int], touch: Touch) -> None:
    """Each pair of segments, at offsets i and j of x, whose closest points
    are less than a diameter apart: ``touch(e, u, w, px, py, pz, r2)`` with
    the pair's place in ``pairs``, how far along each segment the points are,
    the vector between them, from the second to the first, and its length
    squared.

    The closest points (Ericson, 2005, §5.1.9): those of the two infinite
    lines, u along the first clamped to the segment; then w along the second,
    nearest that point, and if it falls off the second segment, w clamped and
    u found again nearest it.  Parallel segments (den near 0) take u = 0.
    """
    for e in range(0, len(pairs), 2):
        i, j = 3 * pairs[e], 3 * pairs[e + 1]
        ax, ay, az = x[i + 3] - x[i], x[i + 4] - x[i + 1], x[i + 5] - x[i + 2]
        bx, by, bz = x[j + 3] - x[j], x[j + 4] - x[j + 1], x[j + 5] - x[j + 2]
        rx, ry, rz = x[i] - x[j], x[i + 1] - x[j + 1], x[i + 2] - x[j + 2]
        aa = ax * ax + ay * ay + az * az
        bb = bx * bx + by * by + bz * bz
        ab = ax * bx + ay * by + az * bz
        ar = ax * rx + ay * ry + az * rz
        br = bx * rx + by * ry + bz * rz
        den = aa * bb - ab * ab
        u = (ab * br - ar * bb) / den if den > 1e-12 * aa * bb else 0.0
        u = 0.0 if u < 0 else 1.0 if u > 1 else u
        w = (ab * u + br) / bb
        if w < 0:
            w = 0.0
            u = min(1.0, max(0.0, -ar / aa))
        elif w > 1:
            w = 1.0
            u = min(1.0, max(0.0, (ab - ar) / aa))
        px = rx + u * ax - w * bx
        py = ry + u * ay - w * by
        pz = rz + u * az - w * bz
        r2 = px * px + py * py + pz * pz
        if r2 < 1:
            touch(e, u, w, px, py, pz, r2)


def spread(
    f: List[float],
    i: int,
    j: int,
    u: float,
    w: float,
    qx: float,
    qy: float,
    qz: float,
) -> None:
    """A force q between the segments at offsets i and j, at u and w along
    them: onto the first, and its opposite onto the second, shared between
    each one's two beads."""
    f[i] += (1 - u) * qx
    f[i + 1] += (1 - u) * qy
    f[i + 2] += (1 - u) * qz
    f[i + 3] += u * qx
    f[i + 4] += u * qy
    f[i + 5] += u * qz
    f[j] -= (1 - w) * qx
    f[j + 1] -= (1 - w) * qy
    f[j + 2] -= (1 - w) * qz
    f[j + 3] -= w * qx
    f[j + 4] -= w * qy
    f[j + 5] -= w * qz


def stretch_and_bend(
    x: Sequence[float],
    f: List[float],
    start: int,
    end: int,
    s0: float,
    ks: float,
    kb: float,
) -> float:
    """A yarn's beads ``start`` to ``end`` stretching, links of rest length
    s0, and bending, onto f: ``k_s (r - s0)² / 2`` a link, and
    ``k_b / s0² |curve|² / 2`` a bead between two others.  Returns the links'
    stretch, all told."""
    strain = 0.0
    for g in range(start, end):
        dx = x[3 * g + 3] - x[3 * g]
        dy = x[3 * g + 4] - x[3 * g + 1]
        dz = x[3 * g + 5] - x[3 * g + 2]
        r = math.sqrt(dx * dx + dy * dy + dz * dz)
        strain += r - s0
        t = (ks * (r - s0)) / r
        f[3 * g] += t * dx
        f[3 * g + 1] += t * dy
        f[3 * g + 2] += t * dz
        f[3 * g + 3] -= t * dx
        f[3 * g + 4] -= t * dy
        f[3 * g + 5] -= t * dz
    b = kb / (s0 * s0)
    for g in range(start + 1, end):
        for c in range(3):
            curve = x[3 * g - 3 + c] - 2 * x[3 * g + c] + x[3 * g + 3 + c]
            f[3 * g - 3 + c] -= b * curve
            f[3 * g + c] += 2 * b * curve
            f[3 * g + 3 + c] -= b * curve
    return strain


def fire_sums(
    f: Sequence[float],
    v: Sequence[float],
    moves: Sequence[int],
    fs: Sequence[float],
    vs: Sequence[float],
    links: Sequence[float],
    sums: List[float],
) -> None:
    """FIRE's sums, added to ``sums`` as the power f · v, |f|², |v|² and the
    largest force: over each yarn's rest length — f ``fs``, v ``vs``,
    weighed per link — then over the beads that move.

    FIRE (Bitzek et al., 2006) is damped dynamics: each step it turns the
    velocity towards the force by a fraction alpha (:func:`steer`), and while
    the power f · v stays positive — going downhill — it lengthens the time
    step and lessens alpha; once it goes uphill it stops everything dead,
    halves the step and starts again.  These sums are what it decides by.
    """
    power, f_norm, v_norm, largest = sums
    for a in range(len(fs)):
        # Per link, so a yarn's rest length is weighed like a bead.
        largest = max(largest, abs(fs[a] / links[a]))
        power += fs[a] * vs[a]
        f_norm += fs[a] * fs[a]
        v_norm += vs[a] * vs[a]
    for g in range(len(moves)):
        if not moves[g]:
            continue
        for c in range(3):
            k = 3 * g + c
            power += f[k] * v[k]
            f_norm += f[k] * f[k]
            v_norm += v[k] * v[k]
            if abs(f[k]) > largest:
                largest = abs(f[k])
    sums[0], sums[1], sums[2], sums[3] = power, f_norm, v_norm, largest


def fire_mix(sums: Sequence[float], alpha: float) -> float:
    """How much of the force FIRE mixes into the velocity, from its sums."""
    f_norm = math.sqrt(sums[1])
    v_norm = math.sqrt(sums[2])
    return (alpha * v_norm) / f_norm if f_norm > 0 else 0.0


def steer(
    v: List[float],
    f: Sequence[float],
    moves: Sequence[int],
    vs: List[float],
    fs: Sequence[float],
    alpha: float,
    mix: float,
) -> None:
    """FIRE's turn of the velocity towards the force: the beads' that move,
    and the rest lengths'."""
    for g in range(len(moves)):
        if not moves[g]:
            continue
        for c in range(3):
            v[3 * g + c] = (1 - alpha) * v[3 * g + c] + mix * f[3 * g + c]
    for a in range(len(vs)):
        vs[a] = (1 - alpha) * vs[a] + mix * fs[a]


def move_beads(
    x: List[float],
    v: List[float],
    f: Sequence[float],
    dt: float,
    moves: Sequence[int],
) -> None:
    """Semi-implicit Euler, no bead moving more than a tenth of a diameter in
    a step, so none can pass through another."""
    for g in range(len(moves)):
        if not moves[g]:
            continue
        v[3 * g] += dt * f[3 * g]
        v[3 * g + 1] += dt * f[3 * g + 1]
        v[3 * g + 2] += dt * f[3 * g + 2]
        mx, my, mz = dt * v[3 * g], dt * v[3 * g + 1], dt * v[3 * g + 2]
        size = math.sqrt(mx * mx + my * my + mz * mz)
        k = 0.1 / size if size > 0.1 else 1.0
        x[3 * g] += mx * k
        x[3 * g + 1] += my * k
        x[3 * g + 2] += mz * k


def relay(yarn: Sequence[float], spacing: float) -> List[float]:
    """A yarn's beads again, evenly spaced about ``spacing`` apart, its two
    ends kept."""
    k = len(yarn) // 3
    along = [0.0] * k
    for i in range(1, k):
        along[i] = along[i - 1] + math.hypot(
            yarn[3 * i] - yarn[3 * i - 3],
            yarn[3 * i + 1] - yarn[3 * i - 2],
            yarn[3 * i + 2] - yarn[3 * i - 1],
        )
    beads = max(2, _round(along[k - 1] / spacing) + 1)
    out = [0.0] * (3 * beads)
    j = 0
    for b in range(beads):
        at = (along[k - 1] * b) / (beads - 1)
        while j < k - 2 and along[j + 1] < at:
            j += 1
        span = along[j + 1] - along[j]
        f = min(1.0, max(0.0, (at - along[j]) / span)) if span > 0 else 0.0
        for c in range(3):
            out[3 * b + c] = yarn[3 * j + c] + f * (
                yarn[3 * j + 3 + c] - yarn[3 * j + c]
            )
    return out


def settle(
    yarns: Sequence[Sequence[float]],
    spacing: Optional[float] = None,
    force: float = 1.0,
    turns: bool = False,
    feed: Optional[float] = None,
    stretch: float = 400.0,
    bend: float = 0.5,
    contact: float = 400.0,
    soft: float = 5.0,
    shell: float = 0.1,
    steps: int = 20000,
    tolerance: float = 1e-3,
    dt_max: float = 0.05,
    progress: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Yarns settled at rest: ``rope.js``'s ``settle``.

    Args:
        yarns: Each yarn's beads, x y z after x y z, bottom end first.
        spacing: Rest length of a link; by default each yarn's first link's.
        force: Drawing the end plate up.
        turns: Whether the end plate may turn.
        feed: T: feed the yarns through the plate at this tension.  Without
            it, each yarn keeps its length.
        stretch: k_s.
        bend: k_b.
        contact: k_c, the cores'.
        soft: k_r, the soft surfaces'.
        shell: w, how thick the soft surface is, of a diameter; 0 for a yarn
            hard all through.
        steps: The most steps to take.
        tolerance: Stop once no force is larger.
        dt_max: FIRE's longest time step.
        progress: Told, every 500 steps, the yarns as they are and how far
            along.

    Returns:
        ``yarns``, at rest; the end plate's ``rise`` and ``turn``; ``steps``
        taken; ``largestForce``, how near rest; ``contacts`` and ``deepest``,
        the cores pressing into each other now, and ``deepestEver``, the
        deepest they ever did; and the links' rest lengths, ``spacing``.
    """
    ks, kb, kc, kr = stretch, bend, contact, soft
    core = 1 - shell
    n_yarns = len(yarns)
    state: Dict[str, Any] = {
        # The end plate, kept from one laying out of the beads to the next.
        "rise": 0.0,
        "turn": 0.0,
        "step": 0,
        "largest": math.inf,
        "contacts": 0,
        "deepest": 0.0,
        # The deepest the cores ever pressed into each other: any yarn
        # passing through another would have had to come right through.
        "deepestEver": 0.0,
    }
    plate = [list(yarn[len(yarn) - 3 :]) for yarn in yarns]
    rest = [
        spacing
        if spacing is not None
        else math.hypot(yarn[3] - yarn[0], yarn[4] - yarn[1], yarn[5] - yarn[2])
        for yarn in yarns
    ]
    mean = rest[0]
    for r in rest[1:]:
        mean += r
    mean /= n_yarns
    beads = [[float(c) for c in yarn] for yarn in yarns]

    def run() -> str:
        """FIRE, until at rest, out of steps, or the beads want laying out
        again."""
        first = [0] * (n_yarns + 1)
        for a in range(n_yarns):
            first[a + 1] = first[a] + len(beads[a]) // 3
        n = first[n_yarns]
        x: List[float] = []
        for yarn in beads:
            x.extend(yarn)
        yarn_of = [0] * n
        free = [1] * n
        is_top = [0] * n
        tops = [0] * n_yarns
        for a in range(n_yarns):
            for g in range(first[a], first[a + 1]):
                yarn_of[g] = a
            free[first[a]] = 0
            free[first[a + 1] - 1] = 0
            is_top[first[a + 1] - 1] = 1
            tops[a] = first[a + 1] - 1
        s = list(rest)
        links = [float(first[a + 1] - first[a] - 1) for a in range(n_yarns)]

        def place_tops() -> None:
            c, sn = math.cos(state["turn"]), math.sin(state["turn"])
            for a in range(n_yarns):
                g = tops[a]
                px, py, pz = plate[a]
                x[3 * g] = c * px - sn * py
                x[3 * g + 1] = sn * px + c * py
                x[3 * g + 2] = pz + state["rise"]

        # Pairs of segments near enough to touch, rebuilt as beads move.
        gap = math.ceil(2 / mean) + 1
        reach = 1 + 2 * mean + 0.5
        pairs: List[int] = []
        built = [0.0] * (3 * n)
        cells = [0] * (3 * n)
        segs = [g for g in range(n) if not is_top[g]]

        def neighbours() -> None:
            nonlocal pairs
            pairs = near_pairs(x, segs, yarn_of, gap, reach, cells)
            built[:] = x

        # The energy's gradient: f holds the forces, minus the gradient, and
        # fs the forces on the links' rest lengths, for fed yarns.
        f = [0.0] * (3 * n)
        fs = [0.0] * n_yarns

        def touch(
            e: int, u: float, w: float, px: float, py: float, pz: float, r2: float
        ) -> None:
            r = math.sqrt(r2)
            push = (kr * (1 - r)) / max(r, 1e-9)
            if r < core:
                state["contacts"] += 1
                if core - r > state["deepest"]:
                    state["deepest"] = core - r
                if core - r > state["deepestEver"]:
                    state["deepestEver"] = core - r
                push += (kc * (core - r)) / max(r, 1e-9)
            spread(
                f, 3 * pairs[e], 3 * pairs[e + 1], u, w, push * px, push * py, push * pz
            )

        def forces() -> None:
            f[:] = [0.0] * (3 * n)
            fs[:] = [0.0] * n_yarns
            for a in range(n_yarns):
                strain = stretch_and_bend(
                    x, f, first[a], first[a + 1] - 1, s[a], ks, kb
                )
                if feed is not None:
                    fs[a] = ks * strain - feed * links[a]
            state["contacts"] = 0
            state["deepest"] = 0.0
            touching(x, pairs, touch)

        def snapshot() -> List[List[float]]:
            return [x[3 * first[a] : 3 * first[a + 1]] for a in range(n_yarns)]

        def keep() -> None:
            nonlocal rest
            for a in range(n_yarns):
                beads[a] = x[3 * first[a] : 3 * first[a + 1]]
            rest = list(s)

        v = [0.0] * (3 * n)
        vs = [0.0] * n_yarns
        v_rise = v_turn = 0.0
        plate_mass = n_yarns
        inertia = 0.0
        for px, py, _ in plate:
            inertia = inertia + px * px + py * py
        plate_inertia = max(1e-9, inertia)
        dt = 0.01
        alpha = 0.1
        downhill = 0
        restarts = 0
        sums = [0.0] * 4
        place_tops()
        neighbours()
        while state["step"] < steps:
            step = state["step"]
            # Every step: two beads moving a tenth of a diameter each,
            # apart, would otherwise close the list's margin unseen.
            if stale(x, built):
                neighbours()
            forces()
            up = force
            torque = 0.0
            for a in range(n_yarns):
                g = tops[a]
                up += f[3 * g + 2]
                torque += x[3 * g] * f[3 * g + 1] - x[3 * g + 1] * f[3 * g]
            if not turns:
                torque = 0.0
            sums[0] = up * v_rise + torque * v_turn
            sums[1] = up * up + torque * torque
            sums[2] = v_rise * v_rise + v_turn * v_turn
            sums[3] = max(abs(up), abs(torque))
            fire_sums(f, v, free, fs, vs, links, sums)
            state["largest"] = sums[3]
            if step % 500 == 0 and progress is not None:
                progress(
                    {
                        "step": step,
                        "largestForce": sums[3],
                        "yarns": snapshot(),
                        "rise": state["rise"],
                        "turn": state["turn"],
                        "dt": dt,
                        "restarts": restarts,
                        "spacing": list(s),
                    }
                )
            if sums[3] < tolerance:
                keep()
                return "settled"
            mix = fire_mix(sums, alpha)
            steer(v, f, free, vs, fs, alpha, mix)
            v_rise = (1 - alpha) * v_rise + mix * up
            v_turn = (1 - alpha) * v_turn + mix * torque
            if sums[0] > 0:
                downhill += 1
                if downhill > 5:
                    dt = min(dt * 1.1, dt_max)
                    alpha *= 0.99
            else:
                restarts += 1
                downhill = 0
                dt *= 0.5
                alpha = 0.1
                v[:] = [0.0] * (3 * n)
                vs[:] = [0.0] * n_yarns
                v_rise = v_turn = 0.0
            move_beads(x, v, f, dt, free)
            again = False
            for a in range(n_yarns):
                # A yarn's rest length moves its links all together: weighed
                # so it answers as fast as a bead.
                vs[a] += (dt * fs[a]) / links[a]
                s[a] += max(-0.01, min(0.01, dt * vs[a]))
                if s[a] > 1.5 * mean or s[a] < 0.6 * mean:
                    again = True
            v_rise += (dt * up) / plate_mass
            v_turn += (dt * torque) / plate_inertia
            state["rise"] += max(-0.1, min(0.1, dt * v_rise))
            state["turn"] += max(-0.02, min(0.02, dt * v_turn))
            place_tops()
            state["step"] = step + 1
            if again:
                keep()
                return "relay"
        keep()
        return "spent"

    while state["step"] < steps:
        outcome = run()
        if outcome in ("settled", "spent"):
            break
        # Links grown too long or too short: lay the yarns out again.
        beads = [relay(yarn, mean) for yarn in beads]
        rest = [
            math.hypot(yarn[3] - yarn[0], yarn[4] - yarn[1], yarn[5] - yarn[2])
            for yarn in beads
        ]
    return {
        "yarns": beads,
        "rise": state["rise"],
        "turn": state["turn"],
        "steps": state["step"],
        "largestForce": state["largest"],
        "contacts": state["contacts"],
        "deepest": state["deepest"],
        "deepestEver": state["deepestEver"],
        "spacing": rest,
    }
