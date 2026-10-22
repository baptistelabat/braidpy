# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Linking numbers: how many times the loops of a braid's closure wind round
each other.

Close a braid — join the top of each slot to the bottom of the same slot,
round the outside — and its strands become loops, one per cycle of its
permutation (:func:`braidpy.pure_braid.cycles`).  Two loops have a linking
number: how many times one winds round the other, counted with a sign.
It does not change however the loops are bent, stretched or pulled tight,
as long as neither passes through the other, so it is what is checked to
know that a braid settled by physics is still the braid that was laid.

It is found two ways here, which agree:

- from the braid word (:func:`linking_matrix`): half the signed number of
  crossings between the two loops' strands, the usual combinatorial
  formula (Rolfsen, *Knots and Links*, 1976, §5.D);
- from the yarns themselves, as curves in space (:func:`yarn_linking`): the
  Gauss linking integral, summed exactly over pairs of straight segments as
  the solid angle each pair subtends (Klenin and Langowski, *Computation of
  writhe in modeling of supercoiled DNA*, Biopolymers 54, 307, 2000), after
  closing the yarns up round the outside (:func:`close_yarns`).

From the word, a positive generator is a positive crossing, the usual
convention: σ₁² closes into a Hopf link of linking number +1.  braidpy's own
drawing of a word in space (:func:`braidpy.parametric_strand.strand_paths`,
a positive generator's lower strand passing over towards +y, the braid
rising along z) is its mirror image: yarns laid that way measure the
opposite sign.  Either way, what is compared — a braid laid, then settled —
is measured the same way.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence

import numpy as np

__all__ = ["close_yarns", "gauss_linking_number", "linking_matrix", "yarn_linking"]


def linking_matrix(braid) -> np.ndarray:
    """The linking numbers of a braid's closure, from its word.

    Each crossing between strands of two different loops adds half its sign
    to their linking number; crossings of a loop with itself add nothing.

    Args:
        braid: A :class:`~braidpy.braid.Braid`.

    Returns:
        A symmetric matrix of whole numbers, one row and column per loop,
        the loops in the order of :func:`braidpy.pure_braid.cycles` (by
        their first strand); zero on the diagonal.
    """
    from braidpy.pure_braid import cycles

    loops = cycles(braid)
    loop_of = {strand: k for k, loop in enumerate(loops) for strand in loop}
    history = braid.slot_history()
    twice = np.zeros((len(loops), len(loops)), dtype=int)
    for step, generator in enumerate(braid.generators):
        if not generator:
            continue
        lower = abs(generator) - 1
        row = history[step]
        a = loop_of[row.index(lower)]
        b = loop_of[row.index(lower + 1)]
        if a != b:
            sign = 1 if generator > 0 else -1
            twice[a, b] += sign
            twice[b, a] += sign
    return twice // 2


def gauss_linking_number(first: np.ndarray, second: np.ndarray) -> float:
    """The linking number of two closed polygons, from their geometry.

    The Gauss linking integral, summed exactly over every pair of edges as
    the solid angle the pair subtends (Klenin and Langowski, 2000, eq. 15
    and 16).  For two closed curves that do not meet it is a whole number;
    any difference from one measures how near they come to touching.

    Args:
        first: The first polygon's corners, ``(n, 3)``; its last corner
            joins its first.
        second: The second's, ``(m, 3)``.

    Returns:
        The linking number.
    """
    a0 = np.asarray(first, dtype=float)
    a1 = np.roll(a0, -1, axis=0)
    b0 = np.asarray(second, dtype=float)
    b1 = np.roll(b0, -1, axis=0)
    # Every edge of the first against every edge of the second.
    p1, p2 = a0[:, None, :], a1[:, None, :]
    p3, p4 = b0[None, :, :], b1[None, :, :]
    r13, r14, r23, r24 = p3 - p1, p4 - p1, p3 - p2, p4 - p2

    def unit(v: np.ndarray) -> np.ndarray:
        size = np.linalg.norm(v, axis=-1, keepdims=True)
        return np.where(size > 1e-15, v / np.maximum(size, 1e-300), 0.0)

    n1 = unit(np.cross(r13, r14))
    n2 = unit(np.cross(r14, r24))
    n3 = unit(np.cross(r24, r23))
    n4 = unit(np.cross(r23, r13))

    def angle(u: np.ndarray, v: np.ndarray) -> np.ndarray:
        return np.arcsin(np.clip(np.sum(u * v, axis=-1), -1.0, 1.0))

    omega = angle(n1, n2) + angle(n2, n3) + angle(n3, n4) + angle(n4, n1)
    omega *= np.sign(np.sum(np.cross(p4 - p3, p2 - p1) * r13, axis=-1))
    return float(np.sum(omega) / (4 * math.pi))


def _rotate(point: np.ndarray, angle: float) -> np.ndarray:
    c, s = math.cos(angle), math.sin(angle)
    return np.array(
        [c * point[0] - s * point[1], s * point[0] + c * point[1], point[2]]
    )


def close_yarns(
    yarns: Sequence[np.ndarray],
    turn: float = 0.0,
    pairing: Optional[Sequence[int]] = None,
    bottom_turn: float = 0.0,
    reach: float = 40.0,
) -> List[np.ndarray]:
    """A braid's yarns closed up into its loops, round the outside.

    Each yarn's top end is turned back by ``turn`` — the turn of the plate
    holding the top ends, so the top ends are where they were laid again —
    then taken up above the braid, out to ``reach`` from the axis, down the
    outside and in, under the braid, to the bottom end it joins, turned back
    by ``bottom_turn``.  Each yarn rises and falls at heights of its own, so
    no two closing paths meet.

    Args:
        yarns: Each yarn's centreline, ``(n, 3)``, bottom end first, the
            braid rising along z round the z axis.
        turn: How far the top ends have turned since they were laid, in
            radians.
        pairing: For each yarn, the yarn whose bottom end its top end joins;
            by default the one whose bottom end is nearest it in angle, the
            top end turned back.
        bottom_turn: How far the bottom ends have turned.
        reach: How far out the closing paths go: well clear of the braid.

    Returns:
        One polygon per loop: the yarns of each, in order, with their
        closing paths.

    Raises:
        ValueError: If the top ends do not each find a bottom end of their
            own.
    """
    yarns = [np.asarray(y, dtype=float).reshape(-1, 3) for y in yarns]
    n = len(yarns)
    bottoms = [y[0] for y in yarns]
    tops = [_rotate(y[-1], -turn) for y in yarns]
    below = min(y[0, 2] for y in yarns) - 3
    above = max(y[-1, 2] for y in yarns) + 3

    def angle(p: np.ndarray) -> float:
        return math.atan2(p[1], p[0])

    if pairing is None:

        def apart(top: np.ndarray, bottom: np.ndarray) -> float:
            return abs(
                ((angle(top) - angle(bottom) + 3 * math.pi) % (2 * math.pi)) - math.pi
            )

        pairing = [min(range(n), key=lambda k: apart(top, bottoms[k])) for top in tops]
    if len(set(pairing)) != n:
        raise ValueError("The yarns' ends do not pair up.")

    steps = 30
    closed: List[np.ndarray] = []
    for a, yarn in enumerate(yarns):
        top = yarn[-1]
        # The top end turned back, rigidly, all ends alike, just above the
        # braid.
        up = [
            _rotate(top, -turn * k / steps) + np.array([0.0, 0.0, 0.1 * k])
            for k in range(1, steps + 1)
        ]
        end = up[-1]
        start = bottoms[pairing[a]]
        # The bottom end, turned back too, below the braid.
        under = _rotate(start, -bottom_turn)
        u, v = angle(end), angle(under)
        lift, sink = above + 0.5 * a, below - 0.5 * a
        out = [
            [end[0], end[1], lift],
            [reach * math.cos(u), reach * math.sin(u), lift],
            [reach * math.cos(u), reach * math.sin(u), sink],
            [reach * math.cos(v), reach * math.sin(v), sink],
            [under[0], under[1], sink],
        ]
        down = [
            _rotate(start, -bottom_turn * k / steps)
            - np.array([0.0, 0.0, 0.1 * (k + 1)])
            for k in range(steps - 1, -1, -1)
        ]
        closed.append(np.vstack([yarn, up, out, down]))

    # Loops: follow each yarn into the yarn whose bottom end it joins.
    seen = [False] * n
    loops: List[np.ndarray] = []
    for first in range(n):
        if seen[first]:
            continue
        parts = []
        a = first
        while not seen[a]:
            seen[a] = True
            parts.append(closed[a])
            a = pairing[a]
        loops.append(np.vstack(parts))
    return loops


def yarn_linking(
    yarns: Sequence[np.ndarray],
    turn: float = 0.0,
    pairing: Optional[Sequence[int]] = None,
    bottom_turn: float = 0.0,
) -> Dict[str, object]:
    """The linking numbers of yarns' closure, from their geometry.

    Args:
        yarns: Each yarn's centreline, bottom end first; see
            :func:`close_yarns`, which takes the other arguments too.
        turn: How far the top ends have turned.
        pairing: Which bottom end each top end joins.
        bottom_turn: How far the bottom ends have turned.

    Returns:
        ``components``, how many loops; and ``links``, the linking number of
        every pair of loops, ``(0, 1), (0, 2), … (1, 2), …``, not rounded.
    """
    loops = close_yarns(yarns, turn, pairing, bottom_turn)
    links: List[float] = [
        gauss_linking_number(loops[i], loops[j])
        for i in range(len(loops))
        for j in range(i + 1, len(loops))
    ]
    return {"components": len(loops), "links": links}
