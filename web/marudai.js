// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A disk braid made as on a marudai: move by move, each moved yarn laid
// over the others and drawn tight, the braid turning to balance.
//
// The method is that of braid3dmin, a kumihimo simulation in three.js, as
// docs/source/braid3D.md describes it; the code is this project's own.
//
// - Each yarn is a chain of beads a unit apart, two units thick.  A link
//   pulls its beads together only when stretched, as a rope does; two beads
//   less than two units apart push each other away.
// - Each yarn's end is drawn towards its carrier, out on the rim and above
//   the braid's tip, by a constant pull: its bobbin.  The end is never drawn
//   back in.
// - A move lays the yarn's end over the top of everything on its way to its
//   new carrier, then draws the new stretch tight as a string would go:
//   each bead to between its neighbours, or round a yarn in the way.
// - The braid then relaxes from what moved: a bead at a time, each moved by
//   its forces, its neighbours and the beads near it then put on the queue,
//   with steps shrinking until the queue dies down.
// - Hanging free, the braid turns until its yarns' ends pull it no way round.
// - Well behind a yarn's end, the braid is made: frozen.
//
// Inside, lengths are in units of half a yarn diameter, y up, as the method
// was given; what comes out is in yarn diameters, z up.

(function (root) {
  "use strict";

  const REACH = 20; // the rim's box: ends beyond it are cut off
  const RIM = REACH - 1; // the carriers' circle
  const WEIGHT = 2; // the carriers stand REACH / WEIGHT above the braid's tip
  const PULL = 1.2; // the bobbins' pull
  const STIFF = 10; // links and contacts
  const TAIL = Math.round(Math.sqrt(REACH * REACH * (1 + 1 / (WEIGHT * WEIGHT)))); // beads from tip to rim
  const KEEP = 40; // beads behind what moved left free
  const CHUNK = 20000;

  // Spatial grid: cells of CELL units, so the 27 round a point hold all
  // beads within CELL of it: all a bead touches, and all it may wake once it
  // has moved its most.  y wraps round, the braid's made part leaving it.
  const CELL = 2.6;
  const NXZ = 20, NY = 64;
  const OXZ = (NXZ * CELL) / 2;

  // The height map: the top of the yarns, per half unit square.
  const HM = 2 * REACH + 4;
  const HW = 2 * HM + 1;

  const wrap = (a) => a - 2 * Math.PI * Math.floor((a + Math.PI) / (2 * Math.PI));

  function Machine(nThreads, turning = true, twisted = !turning) {
    // Held for a while, as the bobbins turn round the braid; then free again.
    function hold(held) {
      turning = !held;
      twisted = held;
    }
    // ------------------------------------------------------------ beads
    let cap = 1024;
    let X = new Float64Array(cap), Y = new Float64Array(cap), Z = new Float64Array(cap);
    let LX = new Float64Array(cap), LY = new Float64Array(cap), LZ = new Float64Array(cap);
    let stamped = new Uint8Array(cap), fixed = new Uint8Array(cap), queued = new Uint8Array(cap);
    let owner = new Int32Array(cap), place = new Int32Array(cap);
    let cellOf = new Int32Array(cap), cellNext = new Int32Array(cap), cellPrev = new Int32Array(cap);
    let count = 0;
    const free = [];

    function grow() {
      cap *= 2;
      const more = (A) => { const B = new A.constructor(cap); B.set(A); return B; };
      X = more(X); Y = more(Y); Z = more(Z); LX = more(LX); LY = more(LY); LZ = more(LZ);
      stamped = more(stamped); fixed = more(fixed); queued = more(queued);
      owner = more(owner); place = more(place);
      cellOf = more(cellOf); cellNext = more(cellNext); cellPrev = more(cellPrev);
    }

    const head = new Int32Array(NXZ * NXZ * NY).fill(-1);
    const cx = (x) => Math.min(NXZ - 1, Math.max(0, Math.floor((x + OXZ) / CELL)));
    const cy = (y) => Math.floor(y / CELL) & (NY - 1);
    const cellAt = (x, y, z) => (cx(x) * NXZ + cx(z)) * NY + cy(y);

    function unlink(b) {
      const c = cellOf[b];
      if (c < 0) return;
      if (cellPrev[b] >= 0) cellNext[cellPrev[b]] = cellNext[b];
      else head[c] = cellNext[b];
      if (cellNext[b] >= 0) cellPrev[cellNext[b]] = cellPrev[b];
      cellOf[b] = -1;
    }
    function link(b) {
      const c = cellAt(X[b], Y[b], Z[b]);
      if (c === cellOf[b]) return;
      unlink(b);
      cellOf[b] = c;
      cellPrev[b] = -1;
      cellNext[b] = head[c];
      if (head[c] >= 0) cellPrev[head[c]] = b;
      head[c] = b;
    }
    function moveTo(b, x, y, z) {
      X[b] = x; Y[b] = y; Z[b] = z;
      if (cellOf[b] >= 0 || !fixed[b]) link(b);
    }

    // Every bead within CELL of (x, y, z), and some further.
    const around = [];
    function near(x, y, z) {
      around.length = 0;
      const i0 = cx(x), k0 = cx(z), j0 = Math.floor(y / CELL);
      const i1 = Math.min(NXZ - 1, i0 + 1), k1 = Math.min(NXZ - 1, k0 + 1);
      for (let i = Math.max(0, i0 - 1); i <= i1; i++) {
        for (let k = Math.max(0, k0 - 1); k <= k1; k++) {
          const column = (i * NXZ + k) * NY;
          for (let j = j0 - 1; j <= j0 + 1; j++) {
            for (let b = head[column + (j & (NY - 1))]; b >= 0; b = cellNext[b]) around.push(b);
          }
        }
      }
      return around;
    }

    // ------------------------------------------------------------ yarns
    const threads = [];
    for (let t = 0; t < nThreads; t++) threads.push({ beads: [], dir: 0, tx: 0, ty: 0, tz: 0 });
    const last = (t) => threads[t].beads[threads[t].beads.length - 1];
    const prevOf = (b) => (place[b] > 0 ? threads[owner[b]].beads[place[b] - 1] : -1);
    const nextOf = (b) => {
      const list = threads[owner[b]].beads;
      return place[b] + 1 < list.length ? list[place[b] + 1] : -1;
    };

    function addBead(t, x, y, z) {
      if (count === cap) grow();
      const b = free.length ? free.pop() : count++;
      const list = threads[t].beads;
      owner[b] = t; place[b] = list.length; list.push(b);
      fixed[b] = 0; queued[b] = 0; stamped[b] = 0; cellOf[b] = -1;
      X[b] = x; Y[b] = y; Z[b] = z;
      link(b);
      return b;
    }
    function dropLast(t) {
      const b = threads[t].beads.pop();
      unlink(b);
      fixed[b] = 1;
      queued[b] = 0;
      free.push(b);
    }

    // ------------------------------------------------------------ queue
    let queue = [];
    function enqueue(b) {
      if (b < 0 || queued[b] || fixed[b]) return;
      queued[b] = 1;
      queue.push(b);
    }

    // ------------------------------------------------------------ heights
    const hmH = new Float64Array(HW * HW), hmT = new Int32Array(HW * HW);
    let highest = 0;
    function hmClear() { hmH.fill(-2); hmT.fill(-1); highest = 0; }
    hmClear();
    function hmPut(x, y, z, t) {
      const c = Math.round(x * 2 - 0.5), l = Math.round(z * 2 - 0.5);
      highest = Math.max(highest, y);
      for (let f = -1; f <= 2; f++) {
        for (let e = -1; e <= 2; e++) {
          const i = c + f + HM, k = l + e + HM;
          if (i < 0 || k < 0 || i >= HW || k >= HW) continue;
          const h = f < 0 || f > 1 || e < 0 || e > 1 ? y - 1 : y;
          const at = i * HW + k;
          if (hmH[at] < h) { hmH[at] = h; hmT[at] = t; }
        }
      }
    }
    function hmAt(x, z) {
      const i = Math.round(x * 2) + HM, k = Math.round(z * 2) + HM;
      if (i < 0 || k < 0 || i >= HW || k >= HW) return -1;
      return i * HW + k;
    }

    let tip = 1;

    // The squared distance from (x, y, z) to the nearest bead of another
    // yarn than t, if under CELL; else 100.
    function clearance(x, y, z, t) {
      let best = 100;
      for (const o of near(x, y, z)) {
        if (owner[o] === t) continue;
        const dx = X[o] - x, dy = Y[o] - y, dz = Z[o] - z;
        const d = dx * dx + dy * dy + dz * dz;
        if (d < best) best = d;
      }
      return best;
    }

    // ------------------------------------------------------------ laying

    // Thread t's end goes to the carrier at angle `to`: up over what lies
    // on its way, then out to the rim, then drawn tight.  Carried round
    // with the others, not `over` them, it goes straight out to the rim,
    // passing nobody.
    function lay(t, to, gentle, over = true) {
      const thread = threads[t];
      const list = thread.beads;
      for (let i = list.length - 1; i >= 0 && !fixed[list[i]]; i--) {
        const b = list[i];
        LX[b] = X[b]; LY[b] = Y[b]; LZ[b] = Z[b]; stamped[b] = 1;
      }
      const e0 = last(t);
      let x = X[e0], y = Y[e0], z = Z[e0];
      let top = over ? highest - 2 : y - 2;
      thread.dir = to;
      const rx = Math.cos(to) * RIM, rz = Math.sin(to) * RIM;
      let dx = rx - x, dz = rz - z;
      let dist = Math.hypot(dx, dz);
      if (dist < 0.001) return;
      dx /= dist; dz /= dist;
      for (let g = 0; over && g < dist; g++) {
        const at = hmAt(x, z);
        x += dx; z += dz;
        if (at < 0 || hmT[at] === t) continue;
        top = Math.max(top, hmH[at]);
      }
      x = X[e0]; z = Z[e0];
      while (y < top + 2) addBead(t, x, ++y, z);
      const ry = Math.max(y, tip + REACH / WEIGHT);
      let dy;
      dx = rx - x; dy = ry - y; dz = rz - z;
      dist = Math.hypot(dx, dy, dz);
      if (dist < 0.001) return;
      dx /= dist; dy /= dist; dz /= dist;
      for (let g = 0; g < dist; g++) { x += dx; y += dy; z += dz; addBead(t, x, y, z); }
      addBead(t, x, --y, z);
      addBead(t, x, --y, z);
      seen("carried", t);
      // Carried round with the others, a yarn is not drawn tight on its
      // own: the one drawn last would go straight, the others round it.
      if (over) drawTight(t, gentle);
      else for (let i = list.length - 1; i >= 0 && !fixed[list[i]]; i--) enqueue(list[i]);
      relay(t);
      const end = last(t);
      thread.tx = X[end]; thread.ty = Y[end]; thread.tz = Z[end];
      enqueue(end);
      for (let i = list.length - 1; i >= 0 && !fixed[list[i]]; i--) hmPut(X[list[i]], Y[list[i]], Z[list[i]], t);
      seen("drawn", t);
    }

    // Someone watching: told when a yarn has been carried over the others,
    // when drawn tight, and when the braid has settled after a step — not
    // while the braid turns to balance and its ends are laid out again.
    let watcher = null, quiet = false;
    function seen(what, t) {
      if (watcher && !quiet) watcher(what, t);
    }

    // Each free bead to between its neighbours, as a string drawn tight;
    // where another yarn is in the way, round it.
    function drawTight(t, gentle) {
      const list = threads[t].beads;
      for (let i = list.length - 2; i >= 0 && !fixed[list[i]]; i--) enqueue(list[i]);
      const least = gentle ? 0.0001 : 0.003;
      for (let k = 0; k < queue.length; k++) {
        const b = queue[k];
        queued[b] = 0;
        const p = prevOf(b), n = nextOf(b);
        if (p < 0 || n < 0) continue;
        const mx = (X[p] + X[n]) / 2, my = (Y[p] + Y[n]) / 2, mz = (Z[p] + Z[n]) / 2;
        const l = Math.hypot(X[b] - mx, Y[b] - my, Z[b] - mz);
        if (l < least) continue;
        const room = clearance(mx, my, mz, t);
        let moved = false;
        if (room > 4) {
          moveTo(b, mx, my, mz);
          moved = true;
        } else {
          // Round the yarn in the way: half way there, and aside, either side.
          const kx = mx - X[b], ky = my - Y[b], kz = mz - Z[b];
          const hx = mx - X[p], hy = my - Y[p], hz = mz - Z[p];
          if (hx * hx + hy * hy + hz * hz < 1e-8) continue;
          let ox = ky * hz - kz * hy, oy = kz * hx - kx * hz, oz = kx * hy - ky * hx;
          const m = Math.hypot(ox, oy, oz);
          if (m < 1e-5) continue;
          const s = (0.866 * l) / m;
          ox *= s; oy *= s; oz *= s;
          const here = Math.min(4, clearance(X[b], Y[b], Z[b], t));
          for (const side of [1, -1]) {
            const rx = X[b] + kx / 2 + side * ox, ry = Y[b] + ky / 2 + side * oy, rz = Z[b] + kz / 2 + side * oz;
            const there = clearance(rx, ry, rz, t);
            if (there > room && there > here) {
              moveTo(b, rx, ry, rz);
              moved = true;
              break;
            }
          }
        }
        if (moved && l >= least) { enqueue(p); enqueue(n); }
      }
      queue = [];
    }

    // Lay the beads that moved out again a unit apart; freeze those well
    // behind them.
    function relay(t) {
      const list = threads[t].beads;
      let c = list.length - 1;
      for (; c > 0; c--) {
        const b = list[c];
        if (fixed[b]) break;
        if (stamped[b] && Math.hypot(LX[b] - X[b], LY[b] - Y[b], LZ[b] - Z[b]) < 0.001) break;
      }
      for (let j = c - KEEP; j >= 0 && !fixed[list[j]]; j--) fixed[list[j]] = 1;
      const path = [];
      for (let j = c + 1; j < list.length; j++) path.push([X[list[j]], Y[list[j]], Z[list[j]]]);
      while (list.length > c + 1) dropLast(t);
      const b0 = list[c];
      let ox = X[b0], oy = Y[b0], oz = Z[b0];
      let k = 0;
      while (k < path.length) {
        let m = 0;
        while (m < 1 && k < path.length) {
          const [px, py, pz] = path[k];
          const d = Math.hypot(px - ox, py - oy, pz - oz);
          if (m + d <= 1) {
            ox = px; oy = py; oz = pz; m += d; k++;
          } else {
            const f = (1 - m) / d;
            ox += (px - ox) * f; oy += (py - oy) * f; oz += (pz - oz) * f;
            m = 1;
            enqueue(addBead(t, ox, oy, oz));
          }
        }
      }
    }

    // ------------------------------------------------------------ relaxing

    let strength = 0.1;
    // The same shuffles every time: the same braid every time.
    let seed = 12345;
    function shuffle(list) {
      for (let i = list.length - 1; i > 0; i--) {
        seed = (seed * 1103515245 + 12345) % 2147483648;
        const j = Math.floor((seed / 2147483648) * (i + 1));
        [list[i], list[j]] = [list[j], list[i]];
      }
    }
    function relaxBead(b) {
      if (fixed[b]) return;
      const t = owner[b], i = place[b];
      const p = prevOf(b), n = nextOf(b);
      const x = X[b], y = Y[b], z = Z[b];
      let fx = 0, fy = 0, fz = 0;
      for (let side = 0; side < 2; side++) {
        const o = side ? n : p;
        if (o < 0) continue;
        const dx = X[o] - x, dy = Y[o] - y, dz = Z[o] - z;
        const d2 = dx * dx + dy * dy + dz * dz;
        if (d2 > 1) {
          const d = Math.sqrt(d2), f = ((d - 1) * STIFF) / d;
          fx += dx * f; fy += dy * f; fz += dz * f;
        }
      }
      const thread = threads[t];
      let px = 0, py = 0, pz = 0;
      if (n < 0) {
        px = thread.tx; py = thread.ty - y; pz = thread.tz;
        const m = Math.hypot(px, py, pz);
        px *= PULL / m; py *= PULL / m; pz *= PULL / m;
        fx += px; fy += py; fz += pz;
      }
      const others = near(x, y, z);
      for (let k = 0; k < others.length; k++) {
        const o = others[k];
        if (o === b || (owner[o] === t && Math.abs(place[o] - i) <= 2)) continue;
        const dx = x - X[o], dy = y - Y[o], dz = z - Z[o];
        const d2 = dx * dx + dy * dy + dz * dz;
        if (d2 < 4 && d2 > 0) {
          const d = Math.sqrt(d2), f = ((2 - d) * STIFF) / d;
          fx += dx * f; fy += dy * f; fz += dz * f;
        }
      }
      fx *= strength; fy *= strength; fz *= strength;
      const s = fx * fx + fy * fy + fz * fz;
      if (s <= 0.0001) return;
      if (s > 0.09) { const c = 0.3 / Math.sqrt(s); fx *= c; fy *= c; fz *= c; }
      if (n >= 0 || fx * px + fy * py + fz * pz > 0) moveTo(b, x + fx, y + fy, z + fz);
      enqueue(p);
      enqueue(n);
      if (n < 0) {
        if (queue.length) enqueue(b);
        return;
      }
      // Wake the other yarns' beads near where it now is: all among those
      // found round where it was.
      const nx = X[b], ny = Y[b], nz = Z[b];
      for (let k = 0; k < others.length; k++) {
        const o = others[k];
        if (owner[o] === t) continue;
        const dx = X[o] - nx, dy = Y[o] - ny, dz = Z[o] - nz;
        if (dx * dx + dy * dy + dz * dz < 5.3) enqueue(o);
      }
    }

    let lastMoved = new Set();
    let updates = 0;
    function relax() {
      if (!queue.length) for (const t of lastMoved) enqueue(last(t));
      else lastMoved = new Set(queue.map((b) => owner[b]));
      strength = 0.11;
      let peak = queue.length;
      for (;;) {
        let done = 0;
        while (queue.length && done < CHUNK) {
          peak = Math.max(peak, queue.length);
          const batch = queue;
          queue = [];
          // Held, in no fixed order: an order would favour one yarn, and the
          // twist of a rope would gather round it as a core.
          if (twisted) shuffle(batch);
          for (const b of batch) {
            queued[b] = 0;
            relaxBead(b);
            done++;
          }
        }
        updates += done;
        strength *= 0.9;
        if (!(queue.length > peak / 10 && strength > 0.01)) break;
      }
      for (const b of queue) queued[b] = 0;
      queue = [];
      for (let t = 0; t < nThreads; t++) trim(t);
      heights();
      findTip();
      quiet = true;
      balance();
      quiet = false;
      forget();
      seen("settled", -1);
    }

    function trim(t) {
      const list = threads[t].beads;
      while (list.length && !fixed[last(t)]) {
        const b = last(t);
        if (Math.abs(X[b]) > REACH || Math.abs(Z[b]) > REACH) dropLast(t);
        else break;
      }
    }

    function heights() {
      hmClear();
      for (let t = 0; t < nThreads; t++) {
        const list = threads[t].beads;
        for (let i = list.length - 1; i >= 0 && i >= list.length - 2 * TAIL; i--) hmPut(X[list[i]], Y[list[i]], Z[list[i]], t);
      }
    }

    function findTip() {
      let s = 0;
      for (const thread of threads) s += Y[thread.beads[Math.max(0, thread.beads.length - TAIL)]];
      tip = s / nThreads;
    }

    // Turn the braid about its axis until its yarns' ends pull it no way
    // round, then lay the ends out to their carriers again.
    function balance() {
      let ax = 0, az = 0;
      for (let t = 0; t < nThreads; t++) { ax += X[last(t)]; az += Z[last(t)]; }
      ax /= nThreads; az /= nThreads;
      const span = REACH - 4;
      const lean = threads.map((thread) => {
        const list = thread.beads;
        if (list.length < 20) return 0;
        const e = list[list.length - 1], b = list[list.length - 2];
        const cxv = ax - X[e], czv = az - Z[e];
        const out = Math.atan2(czv, cxv), back = Math.atan2(Z[b] - Z[e], X[b] - X[e]);
        const arm = Math.max(-span, Math.min(span, Math.sin(wrap(back - out)) * Math.hypot(cxv, czv)));
        return Math.asin(arm / span);
      });
      const torque = (f) => lean.reduce((s, r) => s + Math.sin(Math.min(Math.PI / 2, Math.max(-Math.PI / 2, wrap(r + f)))), 0);
      let lo = -Math.PI / 4, hi = Math.PI / 4;
      while (hi - lo > 0.001) {
        const g = (2 * lo + hi) / 3, h = (lo + 2 * hi) / 3;
        const tg = Math.abs(torque(g)), th = Math.abs(torque(h));
        if (tg > th) lo = g;
        else if (tg < th) hi = h;
        else { lo = g; hi = h; }
      }
      const f = turning ? (lo + hi) / 2 : 0;
      const order = [...threads.keys()].sort((p, q) => threads[p].dir - threads[q].dir);
      if (Math.abs(f) > 0.01) turn(ax, az, f);
      if (f > 0) order.reverse();
      // Held, the yarns are laid out again to their carriers without being
      // carried over each other.
      for (const t of order) lay(t, threads[t].dir, false, !twisted);
    }

    // The whole braid turned by f about the vertical through (ax, az).
    function turn(ax, az, f) {
      const c = Math.cos(f), s = Math.sin(f);
      for (const thread of threads) {
        for (const b of thread.beads) {
          const x = X[b] - ax, z = Z[b] - az;
          moveTo(b, ax + x * c + z * s, Y[b], az - x * s + z * c);
        }
      }
    }

    // The bobbins carried round by f together, the braid held: each yarn's
    // free part turns with them about the axis, all of it at its carrier
    // and none of it at the braid's tip, twisting the yarns in there.
    function twist(f) {
      for (const thread of threads) {
        const list = thread.beads;
        const end = last(threads.indexOf(thread));
        const top = Math.max(Y[end], tip + 1);
        for (let i = list.length - 1; i >= 0 && !fixed[list[i]]; i--) {
          const b = list[i];
          const w = Math.max(0, Math.min(1, (Y[b] - tip) / (top - tip)));
          if (!w) continue;
          const c = Math.cos(f * w), s = Math.sin(f * w);
          moveTo(b, X[b] * c - Z[b] * s, Y[b], X[b] * s + Z[b] * c);
          enqueue(b);
        }
        thread.dir += f;
        const c = Math.cos(f), s = Math.sin(f);
        [thread.tx, thread.tz] = [thread.tx * c - thread.tz * s, thread.tx * s + thread.tz * c];
      }
    }

    // The made braid, well below anything free, leaves the grid.
    function forget() {
      let low = Infinity;
      for (const thread of threads) {
        const list = thread.beads;
        for (let i = list.length - 1; i >= 0 && !fixed[list[i]]; i--) low = Math.min(low, Y[list[i]]);
      }
      for (const thread of threads) {
        for (const b of thread.beads) if (fixed[b] && cellOf[b] >= 0 && Y[b] < low - 3 * CELL) unlink(b);
      }
    }

    // ------------------------------------------------------------ start
    function start(angles) {
      angles.forEach((a, t) => {
        // As the method has it, a third of a unit per yarn; but with six
        // yarns or fewer, their start beads would touch or overlap: far
        // enough apart, then, for them to clear each other.
        const touching = 1 / Math.sin(Math.PI / Math.max(2, nThreads));
        const r = nThreads / 3 > touching ? nThreads / 3 : 1.1 * touching;
        fixed[addBead(t, Math.cos(a) * r, 0, Math.sin(a) * r)] = 1;
        fixed[addBead(t, Math.cos(a) * r, 1, Math.sin(a) * r)] = 1;
        lay(t, a);
      });
    }

    return {
      start,
      hold,
      lay,
      twist,
      relax,
      turn,
      threads,
      get tip() { return tip; },
      get updates() { return updates; },
      positions: (t) => threads[t].beads.map((b) => [X[b], Y[b], Z[b]]),
      // Every yarn's beads, flat, in yarn diameters, z up, as make returns them.
      snapshot() {
        return threads.map(({ beads }) => {
          const out = new Float32Array(3 * beads.length);
          beads.forEach((b, i) => {
            out[3 * i] = X[b] / 2;
            out[3 * i + 1] = -Z[b] / 2;
            out[3 * i + 2] = Y[b] / 2;
          });
          return out;
        });
      },
      watch(f) { watcher = f; },
    };
  }

  /**
   * A disk braid made move by move.
   *
   * @param {Object} job
   * @param {number} job.n_slots  Slots round the disk.
   * @param {number[]} job.start  Each yarn's slot, from 1.
   * @param {number[][][]} job.steps  Per step, [yarn, slots moved].  When
   *     every yarn moves alike, the disk turns; else each yarn named is
   *     moved, in turn, and the braid relaxes.
   * @param {boolean} job.clockwise  Slots numbered clockwise, from above.
   * @param {boolean} [job.split]  A move of more than nine tenths of a half
   *     turn goes in two halves, so it passes over what lies on its own
   *     side round (true).
   * @param {boolean} [job.held]  The braid held, as a braider holds it,
   *     rather than hanging free: it does not turn to balance, and when every
   *     yarn moves alike the bobbins turn round it, twisting the yarns in,
   *     rather than the disk and the braid turning together.
   * @param {boolean} [job.twists]  When every yarn moves alike, the bobbins
   *     turn round the braid, held for as long as they turn, twisting the
   *     yarns in; it hangs free again for the other moves (job.held).
   * @param {number[]} [job.from]  Each yarn's slot to lay it from first, if
   *     not job.start: the yarns then go from these to job.start as a first
   *     step.
   * @param {function(Object):void} [job.watch]  Told of each yarn carried
   *     over the others, drawn tight, and of the braid settled after each
   *     step: {what, thread, step, tip, yarns}, the yarns whole as returned.
   * @param {function(Object):void} [job.progress]
   * @returns {{yarns: number[][], whole: number[][], tails: number[][],
   *     rim: {radius: number, height: number}, tip: number, updates: number}}
   *     Each yarn's beads, flat [x, y, z, …] in yarn diameters, z up,
   *     oldest first: cut at the braid's tip, whole, and its tail from the
   *     tip out to its carrier; and the carriers' circle.
   */
  function make(job) {
    const n = job.start.length;
    const sense = job.clockwise ? -1 : 1;
    // braid3dmin's angles turn the other way round from ours.
    const angleOf = (slot) => -(sense * 2 * Math.PI * (slot - 1)) / job.n_slots;
    const split = job.split ?? true;
    const twists = job.twists ?? !!job.held;
    const machine = Machine(n, job.turning ?? !job.held);
    let current = -1;
    if (job.watch) {
      machine.watch((what, thread) =>
        job.watch({ what, thread, step: current, tip: machine.tip / 2, yarns: machine.snapshot() }),
      );
    }
    const first = job.from ?? job.start;
    machine.start(first.map(angleOf));
    for (let t = 0; t < n; t++) machine.lay(t, job.from ? angleOf(job.start[t]) : machine.threads[t].dir);
    machine.relax();
    job.steps.forEach((step, number) => {
      current = number;
      const moving = step.filter(([, d]) => d);
      if (!moving.length) return;
      if (moving.length === n && moving.every(([, d]) => d === moving[0][1])) {
        const by = (sense * 2 * Math.PI * moving[0][1]) / job.n_slots;
        if (twists) {
          // The bobbins turned: each carried round its rim,
          // a little at a time, never as far as the next one; the yarns'
          // pull twists them in at the tip.
          const parts = Math.max(2, Math.ceil((2 * Math.abs(by) * n) / (2 * Math.PI)));
          if (!job.held) machine.hold(true);
          for (let k = 0; k < parts; k++) {
            machine.twist(-by / parts);
            machine.relax();
          }
          if (!job.held) machine.hold(false);
          return;
        }
        machine.turn(0, 0, by);
        for (const thread of machine.threads) thread.dir -= by;
        if (job.watch) job.watch({ what: "turned", thread: -1, step: number, tip: machine.tip / 2, yarns: machine.snapshot() });
        return;
      }
      for (const [a, d] of moving) {
        const sweep = -(sense * 2 * Math.PI * d) / job.n_slots;
        const parts = split && Math.abs(sweep) > Math.PI * 0.9 ? 2 : 1;
        for (let k = 0; k < parts; k++) machine.lay(a, machine.threads[a].dir + sweep / parts);
      }
      machine.relax();
      if (job.progress) {
        job.progress({ fraction: (number + 1) / job.steps.length, tip: machine.tip / 2, yarns: () => shape().yarns });
      }
    });
    return { ...shape(), updates: machine.updates };

    // The yarns as they are, in our units and frame.
    function mean(values) {
      const kept = values.filter(Number.isFinite);
      return kept.length ? kept.reduce((sum, v) => sum + v, 0) / kept.length : NaN;
    }
    function shape() {
      const tip = machine.tip / 2;
      const ours = (p) => [p[0] / 2, -p[2] / 2, p[1] / 2];
      const whole = machine.threads.map((_, t) => machine.positions(t).map(ours));
      // Each yarn's tail: from the last of it in the braid out to its
      // carrier.
      const tails = whole.map((y) => {
        let from = 0;
        y.forEach((p, i) => { if (p[2] <= tip) from = i; });
        return y.slice(from).flat();
      });
      return {
        yarns: whole.map((y) => y.filter((p) => p[2] <= tip).flat()),
        whole: whole.map((y) => y.flat()),
        tails,
        // Where the yarns' ends are, about the carriers' circle: the
        // marudai's mirror they lie over.
        rim: {
          radius: mean(tails.map((t) => Math.hypot(t[t.length - 3], t[t.length - 2]))) || RIM / 2,
          height: mean(tails.map((t) => t[t.length - 1])) || tip + REACH / WEIGHT / 2,
        },
        tip,
      };
    }
  }

  root.makeOnMarudai = make;
  if (typeof module !== "undefined" && module.exports) module.exports = { make, Machine };
})(typeof self !== "undefined" ? self : globalThis);
