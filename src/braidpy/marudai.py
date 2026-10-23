# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A disk braid made as on a marudai: move by move, each moved yarn laid
over the others and drawn tight, the braid turning to balance.

``web/marudai.js``, which Braid Studio runs in the browser, in Python: the
same algorithm, step for step, in the same order
(``tests/test_marudai_python.py`` runs both and compares them).  The method
is braid3dmin's, a kumihimo simulation in three.js;
``docs/source/marudai.md`` describes it as done here.  The code is this
project's own.  In short:

- Each yarn is a chain of beads a unit apart, two units thick.  A link pulls
  its beads together only when stretched, as a rope does; two beads less
  than two units apart push each other away.
- Each yarn's end is drawn towards its carrier, out on the rim and above the
  braid's tip, by a constant pull: its bobbin.
- A move lays the yarn's end over the top of everything on its way to its
  new carrier, then draws the new stretch tight as a string would go: each
  bead to between its neighbours, or round a yarn in the way.
- The braid then relaxes from what moved: a bead at a time, each moved by
  its forces, its neighbours and the beads near it then queued, with steps
  shrinking until the queue dies down.
- Hanging free, the braid turns until its yarns' ends pull it no way round.
- Well behind a yarn's end, the braid is made: frozen.

Inside, lengths are in units of half a yarn diameter, y up, as the method was
given; what :func:`make` returns is in yarn diameters, z up.

It follows the JavaScript step for step: JavaScript's rounding to whole
numbers (:func:`_round`), its floating-point random numbers
(``Machine._shuffle``), and the order beads are found and woken in (the grid
of cells as linked lists, and bead numbers reused as the JavaScript reuses
them).  Given the same numbers from the maths library, it makes the same
braid bead for bead.  The libraries themselves differ in the last place —
Python's ``math.hypot`` is correctly rounded, JavaScript's ``Math.hypot``
not always — and thousands of relaxation steps make that visible, as they
would any change: the two braids are alike, not identical.  It is pure
Python and slow — tens of times slower than in a browser — which suits
checking it, not making long braids.
"""

from __future__ import annotations

import math
from typing import Any, Callable, Dict, List, Optional, Sequence

__all__ = ["Machine", "begin", "make"]

REACH = 20  # the rim's box: ends beyond it are cut off
RIM = REACH - 1  # the carriers' circle
WEIGHT = 2  # the carriers stand REACH / WEIGHT above the braid's tip
PULL = 1.2  # the bobbins' pull
STIFF = 10  # links and contacts
KEEP = 40  # beads behind what moved left free
RING = 30  # the most yarns the method was made for: tied round one ring
CHUNK = 20000

# Spatial grid: cells of CELL units, so the 27 round a point hold all beads
# within CELL of it: all a bead touches, and all it may wake once it has
# moved its most.  y wraps round, the braid's made part leaving it.
CELL = 2.6
NXZ, NY = 20, 64
OXZ = (NXZ * CELL) / 2

# The height map: the top of the yarns, per half unit square.
HM = 2 * REACH + 4
HW = 2 * HM + 1


def _round(x: float) -> int:
    """JavaScript's ``Math.round``: halves go up, not to even."""
    return math.floor(x + 0.5)


TAIL = _round(math.sqrt(REACH * REACH * (1 + 1 / (WEIGHT * WEIGHT))))  # tip to rim


def _wrap(a: float) -> float:
    """An angle brought into [-π, π)."""
    return a - 2 * math.pi * math.floor((a + math.pi) / (2 * math.pi))


def _cx(x: float) -> int:
    return min(NXZ - 1, max(0, math.floor((x + OXZ) / CELL)))


def _cy(y: float) -> int:
    return math.floor(y / CELL) & (NY - 1)


def _cell_at(x: float, y: float, z: float) -> int:
    return (_cx(x) * NXZ + _cx(z)) * NY + _cy(y)


class _Thread:
    __slots__ = ("beads", "dir", "tx", "ty", "tz")

    def __init__(self) -> None:
        self.beads: List[int] = []
        self.dir = 0.0
        self.tx = self.ty = self.tz = 0.0


class Machine:
    """The marudai and its yarns: ``web/marudai.js``'s ``Machine``.

    Args:
        n_threads: How many yarns.
        turning: Whether the braid hangs free and turns to balance.
    """

    def __init__(self, n_threads: int, turning: bool = True) -> None:
        self.n = n_threads
        # While the bobbins turn round the braid, together: held, and the
        # yarns carried round with them, not over each other.
        self._balancing = turning
        self.turning = turning
        self.twisted = False
        # Beads, by number.
        self.X: List[float] = []
        self.Y: List[float] = []
        self.Z: List[float] = []
        self.LX: List[float] = []
        self.LY: List[float] = []
        self.LZ: List[float] = []
        self.stamped: List[int] = []
        self.fixed: List[int] = []
        self.queued: List[int] = []
        self.owner: List[int] = []
        self.place: List[int] = []
        self.cell_of: List[int] = []
        self.cell_next: List[int] = []
        self.cell_prev: List[int] = []
        self.free: List[int] = []
        self.head = [-1] * (NXZ * NXZ * NY)
        self.threads = [_Thread() for _ in range(n_threads)]
        self.queue: List[int] = []
        self.hm_h = [-2.0] * (HW * HW)
        self.hm_t = [-1] * (HW * HW)
        self.highest = 0.0
        self.tip = 1.0
        self.strength = 0.1
        # The same shuffles every time: the same braid every time.
        self.seed = 12345.0
        self.last_moved: List[int] = []
        self.updates = 0
        self.watcher: Optional[Callable[[str, int], None]] = None
        self.quiet = False

    # ------------------------------------------------------------ helpers
    def hold(self, held: bool) -> None:
        self.turning = False if held else self._balancing
        self.twisted = held

    def _last(self, t: int) -> int:
        return self.threads[t].beads[-1]

    def _prev_of(self, b: int) -> int:
        return (
            self.threads[self.owner[b]].beads[self.place[b] - 1]
            if self.place[b] > 0
            else -1
        )

    def _next_of(self, b: int) -> int:
        beads = self.threads[self.owner[b]].beads
        return beads[self.place[b] + 1] if self.place[b] + 1 < len(beads) else -1

    def _seen(self, what: str, t: int) -> None:
        if self.watcher and not self.quiet:
            self.watcher(what, t)

    # ------------------------------------------------------------ the grid
    def _unlink(self, b: int) -> None:
        c = self.cell_of[b]
        if c < 0:
            return
        if self.cell_prev[b] >= 0:
            self.cell_next[self.cell_prev[b]] = self.cell_next[b]
        else:
            self.head[c] = self.cell_next[b]
        if self.cell_next[b] >= 0:
            self.cell_prev[self.cell_next[b]] = self.cell_prev[b]
        self.cell_of[b] = -1

    def _link(self, b: int) -> None:
        c = _cell_at(self.X[b], self.Y[b], self.Z[b])
        if c == self.cell_of[b]:
            return
        self._unlink(b)
        self.cell_of[b] = c
        self.cell_prev[b] = -1
        self.cell_next[b] = self.head[c]
        if self.head[c] >= 0:
            self.cell_prev[self.head[c]] = b
        self.head[c] = b

    def _move_to(self, b: int, x: float, y: float, z: float) -> None:
        self.X[b], self.Y[b], self.Z[b] = x, y, z
        if self.cell_of[b] >= 0 or not self.fixed[b]:
            self._link(b)

    def _near(self, x: float, y: float, z: float) -> List[int]:
        """Every bead within CELL of (x, y, z), and some further."""
        around: List[int] = []
        i0, k0, j0 = _cx(x), _cx(z), math.floor(y / CELL)
        i1, k1 = min(NXZ - 1, i0 + 1), min(NXZ - 1, k0 + 1)
        head, nxt = self.head, self.cell_next
        for i in range(max(0, i0 - 1), i1 + 1):
            for k in range(max(0, k0 - 1), k1 + 1):
                column = (i * NXZ + k) * NY
                for j in range(j0 - 1, j0 + 2):
                    b = head[column + (j & (NY - 1))]
                    while b >= 0:
                        around.append(b)
                        b = nxt[b]
        return around

    # ------------------------------------------------------------ beads
    def _add_bead(self, t: int, x: float, y: float, z: float) -> int:
        if self.free:
            b = self.free.pop()
        else:
            b = len(self.X)
            for array in (self.X, self.Y, self.Z, self.LX, self.LY, self.LZ):
                array.append(0.0)
            for flags in (
                self.stamped,
                self.fixed,
                self.queued,
                self.owner,
                self.place,
            ):
                flags.append(0)
            for links in (self.cell_of, self.cell_next, self.cell_prev):
                links.append(-1)
        beads = self.threads[t].beads
        self.owner[b] = t
        self.place[b] = len(beads)
        beads.append(b)
        self.fixed[b] = self.queued[b] = self.stamped[b] = 0
        self.cell_of[b] = -1
        self.X[b], self.Y[b], self.Z[b] = x, y, z
        self._link(b)
        return b

    def _drop_last(self, t: int) -> None:
        b = self.threads[t].beads.pop()
        self._unlink(b)
        self.fixed[b] = 1
        self.queued[b] = 0
        self.free.append(b)

    def _enqueue(self, b: int) -> None:
        if b < 0 or self.queued[b] or self.fixed[b]:
            return
        self.queued[b] = 1
        self.queue.append(b)

    # ------------------------------------------------------------ heights
    def _hm_clear(self) -> None:
        self.hm_h = [-2.0] * (HW * HW)
        self.hm_t = [-1] * (HW * HW)
        self.highest = 0.0

    def _hm_put(self, x: float, y: float, z: float, t: int) -> None:
        c, l_ = _round(x * 2 - 0.5), _round(z * 2 - 0.5)
        self.highest = max(self.highest, y)
        for f in range(-1, 3):
            for e in range(-1, 3):
                i, k = c + f + HM, l_ + e + HM
                if i < 0 or k < 0 or i >= HW or k >= HW:
                    continue
                h = y - 1 if f < 0 or f > 1 or e < 0 or e > 1 else y
                at = i * HW + k
                if self.hm_h[at] < h:
                    self.hm_h[at] = h
                    self.hm_t[at] = t

    @staticmethod
    def _hm_at(x: float, z: float) -> int:
        i, k = _round(x * 2) + HM, _round(z * 2) + HM
        if i < 0 or k < 0 or i >= HW or k >= HW:
            return -1
        return i * HW + k

    def _clearance(self, x: float, y: float, z: float, t: int) -> float:
        """The squared distance from (x, y, z) to the nearest bead of another
        yarn than t, if under CELL; else 100."""
        best = 100.0
        X, Y, Z, owner = self.X, self.Y, self.Z, self.owner
        for o in self._near(x, y, z):
            if owner[o] == t:
                continue
            dx, dy, dz = X[o] - x, Y[o] - y, Z[o] - z
            d = dx * dx + dy * dy + dz * dz
            if d < best:
                best = d
        return best

    # ------------------------------------------------------------ laying
    def lay(self, t: int, to: float, gentle: bool = False, over: bool = True) -> None:
        """Thread t's end goes to the carrier at angle ``to``: up over what
        lies on its way, then out to the rim, then drawn tight.  Carried round
        with the others, not ``over`` them, it goes straight out to the rim,
        passing nobody."""
        thread = self.threads[t]
        beads = thread.beads
        X, Y, Z = self.X, self.Y, self.Z
        for b in reversed(beads):
            if self.fixed[b]:
                break
            self.LX[b], self.LY[b], self.LZ[b] = X[b], Y[b], Z[b]
            self.stamped[b] = 1
        e0 = self._last(t)
        x, y, z = X[e0], Y[e0], Z[e0]
        top = self.highest - 2 if over else y - 2
        thread.dir = to
        rx, rz = math.cos(to) * RIM, math.sin(to) * RIM
        dx, dz = rx - x, rz - z
        dist = math.hypot(dx, dz)
        if dist < 0.001:
            return
        dx /= dist
        dz /= dist
        g = 0
        while over and g < dist:
            at = self._hm_at(x, z)
            x += dx
            z += dz
            g += 1
            if at < 0 or self.hm_t[at] == t:
                continue
            top = max(top, self.hm_h[at])
        x, z = X[e0], Z[e0]
        while y < top + 2:
            y += 1
            self._add_bead(t, x, y, z)
        ry = max(y, self.tip + REACH / WEIGHT)
        dx, dy, dz = rx - x, ry - y, rz - z
        dist = math.hypot(dx, dy, dz)
        if dist < 0.001:
            return
        dx /= dist
        dy /= dist
        dz /= dist
        g = 0
        while g < dist:
            x += dx
            y += dy
            z += dz
            self._add_bead(t, x, y, z)
            g += 1
        y -= 1
        self._add_bead(t, x, y, z)
        y -= 1
        self._add_bead(t, x, y, z)
        self._seen("carried", t)
        # Carried round with the others, a yarn is not drawn tight on its
        # own: the one drawn last would go straight, the others round it.
        if over:
            self._draw_tight(t, gentle)
        else:
            for b in reversed(beads):
                if self.fixed[b]:
                    break
                self._enqueue(b)
        self._relay(t)
        end = self._last(t)
        thread.tx, thread.ty, thread.tz = X[end], Y[end], Z[end]
        self._enqueue(end)
        for b in reversed(beads):
            if self.fixed[b]:
                break
            self._hm_put(X[b], Y[b], Z[b], t)
        self._seen("drawn", t)

    def _draw_tight(self, t: int, gentle: bool) -> None:
        """Each free bead to between its neighbours, as a string drawn tight;
        where another yarn is in the way, round it."""
        beads = self.threads[t].beads
        for i in range(len(beads) - 2, -1, -1):
            if self.fixed[beads[i]]:
                break
            self._enqueue(beads[i])
        least = 0.0001 if gentle else 0.003
        X, Y, Z = self.X, self.Y, self.Z
        k = 0
        while k < len(self.queue):
            b = self.queue[k]
            k += 1
            self.queued[b] = 0
            p, n = self._prev_of(b), self._next_of(b)
            if p < 0 or n < 0:
                continue
            mx, my, mz = (X[p] + X[n]) / 2, (Y[p] + Y[n]) / 2, (Z[p] + Z[n]) / 2
            length = math.hypot(X[b] - mx, Y[b] - my, Z[b] - mz)
            if length < least:
                continue
            room = self._clearance(mx, my, mz, t)
            moved = False
            if room > 4:
                self._move_to(b, mx, my, mz)
                moved = True
            else:
                # Round the yarn in the way: half way there, and aside,
                # either side.
                kx, ky, kz = mx - X[b], my - Y[b], mz - Z[b]
                hx, hy, hz = mx - X[p], my - Y[p], mz - Z[p]
                if hx * hx + hy * hy + hz * hz < 1e-8:
                    continue
                ox, oy, oz = ky * hz - kz * hy, kz * hx - kx * hz, kx * hy - ky * hx
                m = math.hypot(ox, oy, oz)
                if m < 1e-5:
                    continue
                s = (0.866 * length) / m
                ox *= s
                oy *= s
                oz *= s
                here = min(4, self._clearance(X[b], Y[b], Z[b], t))
                for side in (1, -1):
                    rx = X[b] + kx / 2 + side * ox
                    ry = Y[b] + ky / 2 + side * oy
                    rz = Z[b] + kz / 2 + side * oz
                    there = self._clearance(rx, ry, rz, t)
                    if there > room and there > here:
                        self._move_to(b, rx, ry, rz)
                        moved = True
                        break
            if moved and length >= least:
                self._enqueue(p)
                self._enqueue(n)
        self.queue = []

    def _relay(self, t: int) -> None:
        """Lay the beads that moved out again a unit apart; freeze those well
        behind them."""
        beads = self.threads[t].beads
        X, Y, Z = self.X, self.Y, self.Z
        c = len(beads) - 1
        while c > 0:
            b = beads[c]
            if self.fixed[b]:
                break
            if (
                self.stamped[b]
                and math.hypot(self.LX[b] - X[b], self.LY[b] - Y[b], self.LZ[b] - Z[b])
                < 0.001
            ):
                break
            c -= 1
        j = c - KEEP
        while j >= 0 and not self.fixed[beads[j]]:
            self.fixed[beads[j]] = 1
            j -= 1
        path = [
            (X[beads[j]], Y[beads[j]], Z[beads[j]]) for j in range(c + 1, len(beads))
        ]
        while len(beads) > c + 1:
            self._drop_last(t)
        b0 = beads[c]
        ox, oy, oz = X[b0], Y[b0], Z[b0]
        k = 0
        while k < len(path):
            m = 0.0
            while m < 1 and k < len(path):
                px, py, pz = path[k]
                d = math.hypot(px - ox, py - oy, pz - oz)
                if m + d <= 1:
                    ox, oy, oz = px, py, pz
                    m += d
                    k += 1
                else:
                    f = (1 - m) / d
                    ox += (px - ox) * f
                    oy += (py - oy) * f
                    oz += (pz - oz) * f
                    m = 1
                    self._enqueue(self._add_bead(t, ox, oy, oz))

    # ------------------------------------------------------------ relaxing
    def _shuffle(self, items: List[int]) -> None:
        """JavaScript's shuffle, its arithmetic in floating point as there."""
        for i in range(len(items) - 1, 0, -1):
            self.seed = math.fmod(self.seed * 1103515245 + 12345, 2147483648.0)
            j = math.floor((self.seed / 2147483648) * (i + 1))
            items[i], items[j] = items[j], items[i]

    def _relax_bead(self, b: int) -> None:
        if self.fixed[b]:
            return
        X, Y, Z, owner, place = self.X, self.Y, self.Z, self.owner, self.place
        t, i = owner[b], place[b]
        p, n = self._prev_of(b), self._next_of(b)
        x, y, z = X[b], Y[b], Z[b]
        fx = fy = fz = 0.0
        for o in (p, n):
            if o < 0:
                continue
            dx, dy, dz = X[o] - x, Y[o] - y, Z[o] - z
            d2 = dx * dx + dy * dy + dz * dz
            if d2 > 1:
                d = math.sqrt(d2)
                f = ((d - 1) * STIFF) / d
                fx += dx * f
                fy += dy * f
                fz += dz * f
        thread = self.threads[t]
        px = py = pz = 0.0
        if n < 0:
            px, py, pz = thread.tx, thread.ty - y, thread.tz
            m = math.hypot(px, py, pz)
            px *= PULL / m
            py *= PULL / m
            pz *= PULL / m
            fx += px
            fy += py
            fz += pz
        others = self._near(x, y, z)
        for o in others:
            if o == b or (owner[o] == t and abs(place[o] - i) <= 2):
                continue
            dx, dy, dz = x - X[o], y - Y[o], z - Z[o]
            d2 = dx * dx + dy * dy + dz * dz
            if 0 < d2 < 4:
                d = math.sqrt(d2)
                f = ((2 - d) * STIFF) / d
                fx += dx * f
                fy += dy * f
                fz += dz * f
        fx *= self.strength
        fy *= self.strength
        fz *= self.strength
        s = fx * fx + fy * fy + fz * fz
        if s <= 0.0001:
            return
        if s > 0.09:
            c = 0.3 / math.sqrt(s)
            fx *= c
            fy *= c
            fz *= c
        if n >= 0 or fx * px + fy * py + fz * pz > 0:
            self._move_to(b, x + fx, y + fy, z + fz)
        self._enqueue(p)
        self._enqueue(n)
        if n < 0:
            if self.queue:
                self._enqueue(b)
            return
        # Wake the other yarns' beads near where it now is: all among those
        # found round where it was.
        nx, ny, nz = X[b], Y[b], Z[b]
        for o in others:
            if owner[o] == t:
                continue
            dx, dy, dz = X[o] - nx, Y[o] - ny, Z[o] - nz
            if dx * dx + dy * dy + dz * dz < 5.3:
                self._enqueue(o)

    def relax(self) -> None:
        """Let the braid relax from what moved, then trim, find its tip,
        balance it, and forget the made braid far below."""
        if not self.queue:
            for t in self.last_moved:
                self._enqueue(self._last(t))
        else:
            self.last_moved = list(dict.fromkeys(self.owner[b] for b in self.queue))
        self.strength = 0.11
        peak = len(self.queue)
        while True:
            done = 0
            while self.queue and done < CHUNK:
                peak = max(peak, len(self.queue))
                batch = self.queue
                self.queue = []
                # Held, in no fixed order: an order would favour one yarn,
                # and the twist of a rope would gather round it as a core.
                if self.twisted:
                    self._shuffle(batch)
                for b in batch:
                    self.queued[b] = 0
                    self._relax_bead(b)
                    done += 1
            self.updates += done
            self.strength *= 0.9
            if not (len(self.queue) > peak / 10 and self.strength > 0.01):
                break
        for b in self.queue:
            self.queued[b] = 0
        self.queue = []
        for t in range(self.n):
            self._trim(t)
        self._heights()
        self._find_tip()
        self.quiet = True
        self._balance()
        self.quiet = False
        self._forget()
        self._seen("settled", -1)

    def _trim(self, t: int) -> None:
        beads = self.threads[t].beads
        while beads and not self.fixed[self._last(t)]:
            b = self._last(t)
            if abs(self.X[b]) > REACH or abs(self.Z[b]) > REACH:
                self._drop_last(t)
            else:
                break

    def _heights(self) -> None:
        self._hm_clear()
        for t in range(self.n):
            beads = self.threads[t].beads
            i = len(beads) - 1
            while i >= 0 and i >= len(beads) - 2 * TAIL:
                b = beads[i]
                self._hm_put(self.X[b], self.Y[b], self.Z[b], t)
                i -= 1

    def _find_tip(self) -> None:
        s = 0.0
        for thread in self.threads:
            s += self.Y[thread.beads[max(0, len(thread.beads) - TAIL)]]
        self.tip = s / self.n

    def _balance(self) -> None:
        """Turn the braid about its axis until its yarns' ends pull it no way
        round, then lay the ends out to their carriers again."""
        X, Z = self.X, self.Z
        ax = az = 0.0
        for t in range(self.n):
            ax += X[self._last(t)]
            az += Z[self._last(t)]
        ax /= self.n
        az /= self.n
        span = REACH - 4
        lean = []
        for thread in self.threads:
            beads = thread.beads
            if len(beads) < 20:
                lean.append(0.0)
                continue
            # Its last link's pull, as the method has it; with more yarns than
            # it was made for, its pull along its way from the braid's tip to
            # its end: the last link, just laid, may point any way, and the
            # braid, turned on so many of them, swung back and forth further
            # each time.
            back_by = TAIL if self.n > RING else 1
            e, b = beads[-1], beads[max(0, len(beads) - 1 - back_by)]
            cxv, czv = ax - X[e], az - Z[e]
            out = math.atan2(czv, cxv)
            back = math.atan2(Z[b] - Z[e], X[b] - X[e])
            arm = max(
                -span, min(span, math.sin(_wrap(back - out)) * math.hypot(cxv, czv))
            )
            lean.append(math.asin(arm / span))

        def torque(f: float) -> float:
            total = 0.0
            for r in lean:
                total += math.sin(min(math.pi / 2, max(-math.pi / 2, _wrap(r + f))))
            return total

        lo, hi = -math.pi / 4, math.pi / 4
        while hi - lo > 0.001:
            g, h = (2 * lo + hi) / 3, (lo + 2 * hi) / 3
            tg, th = abs(torque(g)), abs(torque(h))
            if tg > th:
                lo = g
            elif tg < th:
                hi = h
            else:
                lo, hi = g, h
        f = (lo + hi) / 2 if self.turning else 0
        order = sorted(range(self.n), key=lambda t: self.threads[t].dir)
        if abs(f) > 0.01:
            self.turn(ax, az, f)
        if f > 0:
            order.reverse()
        # Held, the yarns are laid out again to their carriers without being
        # carried over each other.
        for t in order:
            self.lay(t, self.threads[t].dir, False, not self.twisted)

    def turn(self, ax: float, az: float, f: float) -> None:
        """The whole braid turned by f about the vertical through (ax, az)."""
        c, s = math.cos(f), math.sin(f)
        for thread in self.threads:
            for b in thread.beads:
                x, z = self.X[b] - ax, self.Z[b] - az
                self._move_to(b, ax + x * c + z * s, self.Y[b], az - x * s + z * c)

    def twist(self, f: float) -> None:
        """The bobbins carried round by f together, the braid held: each
        yarn's free part turns with them about the axis, all of it at its
        carrier and none of it at the braid's tip, twisting the yarns in."""
        for t, thread in enumerate(self.threads):
            beads = thread.beads
            end = self._last(t)
            top = max(self.Y[end], self.tip + 1)
            for b in reversed(beads):
                if self.fixed[b]:
                    break
                w = max(0, min(1, (self.Y[b] - self.tip) / (top - self.tip)))
                if not w:
                    continue
                c, s = math.cos(f * w), math.sin(f * w)
                self._move_to(
                    b,
                    self.X[b] * c - self.Z[b] * s,
                    self.Y[b],
                    self.X[b] * s + self.Z[b] * c,
                )
                self._enqueue(b)
            thread.dir += f
            c, s = math.cos(f), math.sin(f)
            thread.tx, thread.tz = (
                thread.tx * c - thread.tz * s,
                thread.tx * s + thread.tz * c,
            )

    def _forget(self) -> None:
        """The made braid, well below anything free, leaves the grid."""
        low = math.inf
        for thread in self.threads:
            for b in reversed(thread.beads):
                if self.fixed[b]:
                    break
                low = min(low, self.Y[b])
        for thread in self.threads:
            for b in thread.beads:
                if (
                    self.fixed[b]
                    and self.cell_of[b] >= 0
                    and self.Y[b] < low - 3 * CELL
                ):
                    self._unlink(b)

    # ------------------------------------------------------------ start
    def start(self, angles: Sequence[float]) -> None:
        """The yarns tied together where the braid begins: round a ring, as
        the method has it, for as many as it was made for; more, and the ring
        would be so wide the yarns rose from it as a tube, never drawn in to
        a braid.  So then rings of at most ``RING``, one under the other, the
        yarns taken in turn round the disk."""
        rings = math.ceil(self.n / RING)
        each = math.ceil(self.n / rings)
        ring = [0] * self.n
        for k, t in enumerate(sorted(range(self.n), key=lambda t: _wrap(angles[t]))):
            ring[t] = k % rings
        for t, a in enumerate(angles):
            # As the method has it, a third of a unit per yarn; but with six
            # yarns or fewer, their start beads would touch or overlap: far
            # enough apart, then, for them to clear each other.
            touching = 1 / math.sin(math.pi / max(2, each))
            r = each / 3 if each / 3 > touching else 1.1 * touching
            y = -2 * ring[t]
            self.fixed[self._add_bead(t, math.cos(a) * r, y, math.sin(a) * r)] = 1
            self.fixed[self._add_bead(t, math.cos(a) * r, y + 1, math.sin(a) * r)] = 1
            self.lay(t, a)

    def positions(self, t: int) -> List[List[float]]:
        return [[self.X[b], self.Y[b], self.Z[b]] for b in self.threads[t].beads]


def make(job: Dict[str, Any]) -> Dict[str, Any]:
    """A disk braid made move by move: ``web/marudai.js``'s ``make``.

    Args:
        job: A disk program, as :mod:`braidpy.web` gives it: ``n_slots``,
            ``start`` (each yarn's slot, from 1), ``steps`` (per step,
            ``[yarn, slots moved]``), ``clockwise``; and optionally
            ``split``, ``held``, ``twists``, ``from`` and ``turning``, as in
            the JavaScript.

    Returns:
        ``yarns`` (each yarn's beads, flat ``[x, y, z, …]`` in yarn
        diameters, z up, oldest first, cut at the braid's tip), ``whole``,
        ``tails``, ``rim``, ``tip`` and ``updates``, as the JavaScript's.
    """
    making = begin(job)
    for number, step in enumerate(job["steps"]):
        making["step"](step, number)
    return making["result"]()


def begin(job: Dict[str, Any]) -> Dict[str, Any]:
    """A braid being made: the marudai set up, its moves made one by one
    with ``step(moves, number)``, the braid as it is so far with
    ``result()``; and the machine itself, as ``machine``."""
    n = len(job["start"])
    sense = -1 if job.get("clockwise") else 1
    n_slots = job["n_slots"]

    def angle_of(slot: float) -> float:
        # braid3dmin's angles turn the other way round from ours.
        return -(sense * 2 * math.pi * (slot - 1)) / n_slots

    split = job.get("split", True)
    twists = job["twists"] if job.get("twists") is not None else bool(job.get("held"))
    turning = job["turning"] if job.get("turning") is not None else not job.get("held")
    machine = Machine(n, turning)
    steps = job["steps"]

    def uniform(step: Sequence[Sequence[float]]) -> bool:
        moving = [m for m in step if m[1]]
        return len(moving) == n and all(d == moving[0][1] for _, d in moving)

    rope = twists and len(steps) > 0 and all(uniform(s) for s in steps)
    if rope:
        machine.hold(True)
    first = job.get("from") or job["start"]
    machine.start([angle_of(s) for s in first])
    for t in range(n):
        machine.lay(
            t, angle_of(job["start"][t]) if job.get("from") else machine.threads[t].dir
        )
    machine.relax()

    def step(moves: Sequence[Sequence[float]], number: int) -> None:
        moving = [m for m in moves if m[1]]
        if not moving:
            return
        if len(moving) == n and all(d == moving[0][1] for _, d in moving):
            by = (sense * 2 * math.pi * moving[0][1]) / n_slots
            if twists:
                # The bobbins turned: each carried round its rim, a little
                # at a time; the yarns' pull twists them in at the tip.
                parts = max(2, math.ceil((2 * abs(by) * n) / (2 * math.pi)))
                machine.hold(True)
                for _ in range(parts):
                    machine.twist(-by / parts)
                    machine.relax()
                if not rope:
                    machine.hold(False)
                return
            machine.turn(0, 0, by)
            for thread in machine.threads:
                thread.dir -= by
            return
        for yarn, d in moving:
            a = int(yarn)
            sweep = -(sense * 2 * math.pi * d) / n_slots
            parts = 2 if split and abs(sweep) > math.pi * 0.9 else 1
            for _ in range(parts):
                machine.lay(a, machine.threads[a].dir + sweep / parts)
        machine.relax()

    def result() -> Dict[str, Any]:
        tip = machine.tip / 2

        def ours(p: List[float]) -> List[float]:
            return [p[0] / 2, -p[2] / 2, p[1] / 2]

        whole = [[ours(p) for p in machine.positions(t)] for t in range(n)]
        tails = []
        for y in whole:
            start = 0
            for i, p in enumerate(y):
                if p[2] <= tip:
                    start = i
            tails.append([c for p in y[start:] for c in p])

        def mean(values: List[float]) -> float:
            kept = [v for v in values if math.isfinite(v)]
            return sum(kept) / len(kept) if kept else math.nan

        radius = mean([math.hypot(t[-3], t[-2]) for t in tails])
        height = mean([t[-1] for t in tails])
        return {
            "yarns": [[c for p in y if p[2] <= tip for c in p] for y in whole],
            "whole": [[c for p in y for c in p] for y in whole],
            "tails": tails,
            "rim": {
                "radius": radius if radius == radius and radius else RIM / 2,
                "height": height
                if height == height and height
                else tip + REACH / WEIGHT / 2,
            },
            "tip": tip,
            "updates": machine.updates,
        }

    return {"step": step, "result": result, "machine": machine}
