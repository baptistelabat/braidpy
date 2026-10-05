// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A disk braid made as on a marudai: move by move, each moved yarn laid
// over the others, pulled taut by its bobbin, the braid turning to balance.
//
// The ideas are those of braid3dmin, a kumihimo simulation in three.js, as
// docs/source/braid3D.md describes it; the code is this project's own, on
// the physics of rope.js.
//
// - Each yarn is a chain of beads from the start of the braid, held fixed,
//   up through the braid to its free end, which its bobbin pulls with a
//   tension T towards its carrier: on the rim, a little above the braid's
//   tip, so the yarns leave the braid nearly level, as they do over a
//   marudai's mirror.
// - A move takes one yarn's carrier round the rim, past the carriers of the
//   yarns it crosses.  The yarn's free end is carried with it: lifted above
//   every yarn it is to pass over and laid round them, at the rim of the
//   braid's tails, in the move's sense.  It is laid over them, so it passes
//   over them; then its bobbin pulls it taut, and it slides in over them to
//   the tip of the braid, where the crossing is made.
// - Each yarn's tail is kept a few diameters long beyond the tip: yarn is
//   fed in from the bobbin as the braid takes it up.
// - The braid near its tip settles by the physics of rope.js — stretching,
//   bending, soft-over-firm contact — found by FIRE.  Well below the tip it
//   is made: frozen.
// - Hanging free, the braid turns until the bobbins pull it no way round.
//
// Lengths are in yarn diameters.

(function (root) {
  "use strict";

  const SPACING = 0.5;
  const TAIL = 3.5; // the tails' length beyond the braid
  const FREEZE = 5; // below the tip by this, the braid is made
  const LIFT = 1.1; // a moved yarn is laid this far over the others

  /**
   * @param {Object} job
   * @param {number} job.n_slots  Slots round the disk.
   * @param {number[]} job.start  Each yarn's slot, from 1.
   * @param {number[][][]} job.steps  Per step, [yarn, slots moved].
   * @param {boolean} job.clockwise  Slots numbered clockwise, from above.
   * @param {number} [job.tension]  T.
   * @param {number} [job.rise]  How steeply the yarns rise from the tip to
   *     their carriers, in radians.
   * @param {function(Object):void} [job.progress]
   * @returns {{yarns: number[][], tip: number, turned: number}} Each
   *     yarn's beads, oldest first, cut at the braid's tip.
   */
  function make(job) {
    const nYarns = job.start.length;
    const nSlots = job.n_slots;
    const sense = job.clockwise ? -1 : 1;
    const tension = job.tension ?? 1;
    const rise = job.rise ?? 0.25;
    const ks = 100, kb = 0.5, kr = 5, kc = 100, core = 0.9;
    const braidRadius = 0.3 + 0.55 * Math.sqrt(nYarns);
    const tailRadius = braidRadius + TAIL;
    const rim = 12 + nYarns / 2;
    const angleOf = (slot) => (sense * 2 * Math.PI * (slot - 1)) / nSlots;

    // Each yarn: its beads, oldest first; how many at the start are made;
    // where its carrier is.
    const angle = job.start.map(angleOf);
    const yarns = [];
    // The braid starts tied round a ring, the yarns evenly round it in the
    // order of their slots, far enough apart to clear each other; from it
    // each runs out to its carrier's angle.  Kept in order, none crosses.
    const ring = Math.max(0.6, (0.6 * nYarns) / Math.PI);
    const order = [...Array(nYarns).keys()].sort((p, q) => job.start[p] - job.start[q]);
    const place = new Array(nYarns);
    order.forEach((a, k) => (place[a] = (2 * Math.PI * k) / nYarns + angle[order[0]]));
    for (let a = 0; a < nYarns; a++) {
      const t = place[a];
      const points = [];
      for (let z = 0; z <= 1.5; z += SPACING) points.push([ring * Math.cos(t), ring * Math.sin(t), z]);
      const out = [Math.cos(angle[a]) * tailRadius, Math.sin(angle[a]) * tailRadius];
      const from = [ring * Math.cos(t), ring * Math.sin(t)];
      const length = Math.hypot(out[0] - from[0], out[1] - from[1]);
      for (let k = 1; k * SPACING <= length; k++) {
        const f = (k * SPACING) / length;
        points.push([from[0] + f * (out[0] - from[0]), from[1] + f * (out[1] - from[1]), 1.5]);
      }
      yarns.push({ beads: points, made: 1 });
    }
    let tip = 1.5;
    let turned = 0;
    let steps = 0;

    function target(a) {
      return [rim * Math.cos(angle[a]), rim * Math.sin(angle[a]), tip + rim * Math.tan(rise)];
    }

    // ------------------------------------------------------------ settling

    // FIRE on every bead not made, its end pulled towards its carrier.
    function settle(maxSteps) {
      const first = [];
      const x = [];
      const free = [];
      const yarnOf = [];
      yarns.forEach((y, a) => {
        first.push(x.length / 3);
        y.beads.forEach((p, i) => {
          x.push(p[0], p[1], p[2]);
          free.push(i >= y.made ? 1 : 0);
          yarnOf.push(a);
        });
      });
      first.push(x.length / 3);
      const n = first[nYarns];
      const pos = Float64Array.from(x);
      const mobile = Uint8Array.from(free);
      const owner = Int32Array.from(yarnOf);
      const rest = yarns.map((y) => y.rest ?? SPACING);
      const ends = yarns.map((_, a) => first[a + 1] - 1);
      const goal = yarns.map((_, a) => target(a));

      // Segments that can matter: any with a mobile end, and the made ones
      // just below them.
      const low = tip - FREEZE - 2;
      const segs = [];
      for (let a = 0; a < nYarns; a++) {
        for (let g = first[a]; g < first[a + 1] - 1; g++) {
          if (Math.max(pos[3 * g + 2], pos[3 * g + 5]) >= low) segs.push(g);
        }
      }
      const gap = Math.ceil(2 / SPACING) + 1;
      const reach = 1 + 2 * SPACING + 0.5;
      let pairs = new Int32Array(0);
      const built = new Float64Array(3 * n);
      function neighbours() {
        const grid = new Map();
        const cell = new Int32Array(3 * n);
        for (const g of segs) {
          const i = Math.floor((pos[3 * g] + pos[3 * g + 3]) / 2 / reach);
          const j = Math.floor((pos[3 * g + 1] + pos[3 * g + 4]) / 2 / reach);
          const k = Math.floor((pos[3 * g + 2] + pos[3 * g + 5]) / 2 / reach);
          cell[3 * g] = i;
          cell[3 * g + 1] = j;
          cell[3 * g + 2] = k;
          const key = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791);
          let list = grid.get(key);
          if (!list) grid.set(key, (list = []));
          list.push(g);
        }
        const found = [];
        for (const g of segs) {
          const i = cell[3 * g], j = cell[3 * g + 1], k = cell[3 * g + 2];
          for (let di = -1; di <= 1; di++) {
            for (let dj = -1; dj <= 1; dj++) {
              for (let dk = -1; dk <= 1; dk++) {
                const list = grid.get(((i + di) * 73856093) ^ ((j + dj) * 19349663) ^ ((k + dk) * 83492791));
                if (!list) continue;
                for (const h of list) {
                  if (h <= g) continue;
                  if (cell[3 * h] !== i + di || cell[3 * h + 1] !== j + dj || cell[3 * h + 2] !== k + dk) continue;
                  if (owner[h] === owner[g] && h - g < gap) continue;
                  if (!mobile[g] && !mobile[g + 1] && !mobile[h] && !mobile[h + 1]) continue;
                  const mx = pos[3 * g] + pos[3 * g + 3] - pos[3 * h] - pos[3 * h + 3];
                  const my = pos[3 * g + 1] + pos[3 * g + 4] - pos[3 * h + 1] - pos[3 * h + 4];
                  const mz = pos[3 * g + 2] + pos[3 * g + 5] - pos[3 * h + 2] - pos[3 * h + 5];
                  if (mx * mx + my * my + mz * mz > 4 * reach * reach) continue;
                  found.push(g, h);
                }
              }
            }
          }
        }
        pairs = Int32Array.from(found);
        built.set(pos);
      }
      function stale() {
        for (let k = 0; k < 3 * n; k += 3) {
          const dx = pos[k] - built[k], dy = pos[k + 1] - built[k + 1], dz = pos[k + 2] - built[k + 2];
          if (dx * dx + dy * dy + dz * dz > 0.0625) return true;
        }
        return false;
      }

      const f = new Float64Array(3 * n);
      function forces() {
        f.fill(0);
        for (let a = 0; a < nYarns; a++) {
          const s0 = rest[a];
          for (let g = first[a]; g < first[a + 1] - 1; g++) {
            if (!mobile[g] && !mobile[g + 1]) continue;
            const dx = pos[3 * g + 3] - pos[3 * g], dy = pos[3 * g + 4] - pos[3 * g + 1], dz = pos[3 * g + 5] - pos[3 * g + 2];
            const r = Math.sqrt(dx * dx + dy * dy + dz * dz);
            const t = (ks * (r - s0)) / r;
            f[3 * g] += t * dx;
            f[3 * g + 1] += t * dy;
            f[3 * g + 2] += t * dz;
            f[3 * g + 3] -= t * dx;
            f[3 * g + 4] -= t * dy;
            f[3 * g + 5] -= t * dz;
          }
          const b = kb / (s0 * s0);
          for (let g = first[a] + 1; g < first[a + 1] - 1; g++) {
            if (!mobile[g - 1] && !mobile[g] && !mobile[g + 1]) continue;
            for (let c = 0; c < 3; c++) {
              const curve = pos[3 * g - 3 + c] - 2 * pos[3 * g + c] + pos[3 * g + 3 + c];
              f[3 * g - 3 + c] -= b * curve;
              f[3 * g + c] += 2 * b * curve;
              f[3 * g + 3 + c] -= b * curve;
            }
          }
          // The bobbin.
          const e = ends[a];
          const gx = goal[a][0] - pos[3 * e], gy = goal[a][1] - pos[3 * e + 1], gz = goal[a][2] - pos[3 * e + 2];
          const gl = Math.max(Math.hypot(gx, gy, gz), 1e-9);
          f[3 * e] += (tension * gx) / gl;
          f[3 * e + 1] += (tension * gy) / gl;
          f[3 * e + 2] += (tension * gz) / gl;
        }
        for (let q = 0; q < pairs.length; q += 2) {
          const i = 3 * pairs[q], j = 3 * pairs[q + 1];
          const ax = pos[i + 3] - pos[i], ay = pos[i + 4] - pos[i + 1], az = pos[i + 5] - pos[i + 2];
          const bx = pos[j + 3] - pos[j], by = pos[j + 4] - pos[j + 1], bz = pos[j + 5] - pos[j + 2];
          const rx = pos[i] - pos[j], ry = pos[i + 1] - pos[j + 1], rz = pos[i + 2] - pos[j + 2];
          const aa = ax * ax + ay * ay + az * az;
          const bb = bx * bx + by * by + bz * bz;
          const ab = ax * bx + ay * by + az * bz;
          const ar = ax * rx + ay * ry + az * rz;
          const br = bx * rx + by * ry + bz * rz;
          const den = aa * bb - ab * ab;
          let u = den > 1e-12 * aa * bb ? (ab * br - ar * bb) / den : 0;
          u = u < 0 ? 0 : u > 1 ? 1 : u;
          let w = (ab * u + br) / bb;
          if (w < 0) {
            w = 0;
            u = Math.min(1, Math.max(0, -ar / aa));
          } else if (w > 1) {
            w = 1;
            u = Math.min(1, Math.max(0, (ab - ar) / aa));
          }
          const px = rx + u * ax - w * bx, py = ry + u * ay - w * by, pz = rz + u * az - w * bz;
          const r2 = px * px + py * py + pz * pz;
          if (r2 >= 1) continue;
          const r = Math.sqrt(r2);
          let push = (kr * (1 - r)) / Math.max(r, 1e-9);
          if (r < core) {
            push += (kc * (core - r)) / Math.max(r, 1e-9);
            deepestEver = Math.max(deepestEver, core - r);
          }
          const qx = push * px, qy = push * py, qz = push * pz;
          f[i] += (1 - u) * qx;
          f[i + 1] += (1 - u) * qy;
          f[i + 2] += (1 - u) * qz;
          f[i + 3] += u * qx;
          f[i + 4] += u * qy;
          f[i + 5] += u * qz;
          f[j] -= (1 - w) * qx;
          f[j + 1] -= (1 - w) * qy;
          f[j + 2] -= (1 - w) * qz;
          f[j + 3] -= w * qx;
          f[j + 4] -= w * qy;
          f[j + 5] -= w * qz;
        }
      }

      const v = new Float64Array(3 * n);
      let dt = 0.01, alpha = 0.1, downhill = 0, step = 0;
      neighbours();
      for (; step < maxSteps; step++) {
        if (stale()) neighbours();
        forces();
        let power = 0, fNorm = 0, vNorm = 0, largest = 0;
        for (let g = 0; g < n; g++) {
          if (!mobile[g]) continue;
          for (let c = 0; c < 3; c++) {
            const k = 3 * g + c;
            power += f[k] * v[k];
            fNorm += f[k] * f[k];
            vNorm += v[k] * v[k];
            if (Math.abs(f[k]) > largest) largest = Math.abs(f[k]);
          }
        }
        if (largest < 2e-3) break;
        fNorm = Math.sqrt(fNorm);
        vNorm = Math.sqrt(vNorm);
        const mix = fNorm > 0 ? (alpha * vNorm) / fNorm : 0;
        for (let g = 0; g < n; g++) {
          if (!mobile[g]) continue;
          for (let c = 0; c < 3; c++) v[3 * g + c] = (1 - alpha) * v[3 * g + c] + mix * f[3 * g + c];
        }
        if (power > 0) {
          if (++downhill > 5) {
            dt = Math.min(dt * 1.1, 0.05);
            alpha *= 0.99;
          }
        } else {
          downhill = 0;
          dt *= 0.5;
          alpha = 0.1;
          v.fill(0);
        }
        for (let g = 0; g < n; g++) {
          if (!mobile[g]) continue;
          v[3 * g] += dt * f[3 * g];
          v[3 * g + 1] += dt * f[3 * g + 1];
          v[3 * g + 2] += dt * f[3 * g + 2];
          const mx = dt * v[3 * g], my = dt * v[3 * g + 1], mz = dt * v[3 * g + 2];
          const size = Math.sqrt(mx * mx + my * my + mz * mz);
          const k = size > 0.1 ? 0.1 / size : 1;
          pos[3 * g] += mx * k;
          pos[3 * g + 1] += my * k;
          pos[3 * g + 2] += mz * k;
        }
      }
      steps += step;
      yarns.forEach((y, a) => {
        y.beads = y.beads.map((_, i) => {
          const g = first[a] + i;
          return [pos[3 * g], pos[3 * g + 1], pos[3 * g + 2]];
        });
      });
    }
    let deepestEver = 0;

    // ------------------------------------------------------------ the braid

    // Where the braid's tip is: the highest beads still inside its radius,
    // yarn by yarn, on average.
    function findTip() {
      let sum = 0;
      for (const y of yarns) {
        let high = 0;
        for (const p of y.beads) if (Math.hypot(p[0], p[1]) < braidRadius + 0.5) high = Math.max(high, p[2]);
        sum += high;
      }
      tip = Math.max(tip, sum / nYarns);
    }

    // Each yarn's tail kept about TAIL beyond the braid: fed from its
    // bobbin, or wound back.
    function feed() {
      yarns.forEach((y, a) => {
        const b = y.beads;
        const reachOf = (p) => Math.hypot(p[0], p[1]);
        while (b.length > y.made + 3 && reachOf(b[b.length - 1]) > tailRadius + 1) b.pop();
        const goal = target(a);
        while (reachOf(b[b.length - 1]) < tailRadius - 1) {
          const e = b[b.length - 1];
          const d = [goal[0] - e[0], goal[1] - e[1], goal[2] - e[2]];
          const l = Math.hypot(...d);
          b.push([e[0] + (SPACING * d[0]) / l, e[1] + (SPACING * d[1]) / l, e[2] + (SPACING * d[2]) / l]);
        }
      });
    }

    // Deep enough, made.
    function freeze() {
      for (const y of yarns) {
        while (y.made < y.beads.length - 4 && y.beads[y.made][2] < tip - FREEZE) y.made++;
      }
    }

    // Hanging free, the braid turns until its bobbins pull it no way round.
    function balance() {
      const torque = (phi) => {
        const c = Math.cos(phi), s = Math.sin(phi);
        let total = 0;
        yarns.forEach((y, a) => {
          const e = y.beads[y.beads.length - 1];
          const x = c * e[0] - s * e[1], yy = s * e[0] + c * e[1];
          const g = target(a);
          const dx = g[0] - x, dy = g[1] - yy, dz = g[2] - e[2];
          const l = Math.hypot(dx, dy, dz);
          total += (x * dy - yy * dx) / l;
        });
        return total;
      };
      // The turn where the torque changes sign, near no turn.
      let lo = -0.4, hi = 0.4;
      if (torque(lo) * torque(hi) > 0) return;
      for (let k = 0; k < 40; k++) {
        const mid = (lo + hi) / 2;
        if (torque(lo) * torque(mid) <= 0) hi = mid;
        else lo = mid;
      }
      const phi = (lo + hi) / 2;
      const c = Math.cos(phi), s = Math.sin(phi);
      for (const y of yarns) {
        y.beads = y.beads.map(([x, yy, z]) => [c * x - s * yy, s * x + c * yy, z]);
      }
      turned += phi;
    }

    // A move: the yarn's end carried round the rim of the tails, laid over
    // every yarn there, from its old carrier's angle to its new one.
    function move(a, delta) {
      const sweep = (sense * 2 * Math.PI * delta) / nSlots;
      const y = yarns[a];
      const from = Math.atan2(y.beads[y.beads.length - 1][1], y.beads[y.beads.length - 1][0]);
      // Above every other yarn round the rim, in the sector swept.
      let height = tip;
      yarns.forEach((other, b) => {
        if (b === a) return;
        for (const p of other.beads) {
          const r = Math.hypot(p[0], p[1]);
          if (r < braidRadius - 0.5) continue;
          // How far round from where the end starts, in the move's sense.
          const turn = Math.sign(sweep) * (Math.atan2(p[1], p[0]) - from);
          const off = ((turn % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
          if (off <= Math.abs(sweep) + 0.3 || off >= 2 * Math.PI - 0.3) height = Math.max(height, p[2]);
        }
      });
      height += LIFT;
      const end = y.beads[y.beads.length - 1];
      // Out first, beyond every tail, where there is nothing to pass
      // through, so a yarn lying across this one stays across it; then up;
      // then round.
      const r0 = tailRadius + 2;
      const r1 = Math.hypot(end[0], end[1]);
      const ux = end[0] / r1, uy = end[1] / r1;
      for (let r = r1 + SPACING; r < r0; r += SPACING) y.beads.push([r * ux, r * uy, end[2]]);
      for (let z = end[2] + SPACING; z < height; z += SPACING) y.beads.push([r0 * ux, r0 * uy, z]);
      const turns = Math.ceil((Math.abs(sweep) * r0) / SPACING);
      for (let k = 1; k <= turns; k++) {
        const t = from + (sweep * k) / turns;
        y.beads.push([r0 * Math.cos(t), r0 * Math.sin(t), height]);
      }
      angle[a] += sweep;
    }

    // For finding faults: the closest any two yarns' beads come.
    function closestBeads() {
      let best = Infinity, where = null;
      for (let a = 0; a < nYarns; a++) {
        for (let b = a + 1; b < nYarns; b++) {
          for (const p of yarns[a].beads) {
            if (p[2] < tip - FREEZE - 2) continue;
            for (const q of yarns[b].beads) {
              const d = Math.hypot(p[0] - q[0], p[1] - q[1], p[2] - q[2]);
              if (d < best) { best = d; where = [a, b, p[2].toFixed(1)]; }
            }
          }
        }
      }
      return [best, where];
    }
    const check = (label) => {
      if (!job.debug) return;
      const [d, where] = closestBeads();
      if (d < 0.7) job.debug(label, d.toFixed(3), JSON.stringify(where));
    };

    // ------------------------------------------------------------ the moves

    feed();
    settle(3000);
    const all = job.steps;
    for (let number = 0; number < all.length; number++) {
      const moving = all[number].filter(([, d]) => d);
      if (!moving.length) continue;
      if (moving.length === nYarns && moving.every(([, d]) => d === moving[0][1])) {
        // The disk turns, and the braid hanging from it: nothing crosses.
        const by = (sense * 2 * Math.PI * moving[0][1]) / nSlots;
        const c = Math.cos(by), s = Math.sin(by);
        for (const y of yarns) y.beads = y.beads.map(([x, yy, z]) => [c * x - s * yy, s * x + c * yy, z]);
        for (let a = 0; a < nYarns; a++) angle[a] += by;
        continue;
      }
      check(`step ${number} before`);
      if (moving.length === 1 && Math.abs(moving[0][1]) > 1) {
        move(moving[0][0], moving[0][1]);
        check(`step ${number} laid over`);
      } else {
        // Carriers sliding along together pass nobody: their yarns follow.
        for (const [a, d] of moving) angle[a] += (sense * 2 * Math.PI * d) / nSlots;
      }
      settle(8000);
      check(`step ${number} settled`);
      findTip();
      feed();
      check(`step ${number} fed`);
      balance();
      check(`step ${number} balanced`);
      freeze();
      if (job.progress) job.progress({ fraction: (number + 1) / all.length, yarns: cut(), tip });
    }
    settle(8000);
    findTip();
    return {
      yarns: cut(),
      whole: yarns.map((y) => y.beads.flat()),
      tip,
      turned,
      steps,
      deepestEver,
    };

    // Each yarn up to the braid's tip: the tails left off.
    function cut() {
      return yarns.map((y) => {
        const out = [];
        for (const p of y.beads) {
          if (p[2] > tip + 0.5 && Math.hypot(p[0], p[1]) > braidRadius) break;
          out.push(p[0], p[1], p[2]);
        }
        return out;
      });
    }
  }

  root.makeOnMarudai = make;
  if (typeof module !== "undefined" && module.exports) module.exports = { make };
})(typeof self !== "undefined" ? self : globalThis);
