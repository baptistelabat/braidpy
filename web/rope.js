// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Yarns as elastic rods, settled by their own physics.
//
// Each yarn is a chain of beads.  Its energy is the sum of
//
// - stretching: k_s/2 (|x_{i+1} - x_i| - s)^2 per link — stiff, so yarn
//   barely stretches;
// - bending: k_b/2 |x_{i-1} - 2 x_i + x_{i+1}|^2 / s^2 per bead — slight;
// - contact, for any two segments of different yarns (or of one yarn, far
//   apart along it): a yarn is a firm core inside a soft surface.  Closer
//   than a diameter d, the surfaces press together, k_r/2 (d - r)^2; closer
//   than d - w, the cores too, k_c/2 (d - w - r)^2, much stiffer.  Yarns
//   feel each other coming, meet gently, and touch at about a diameter;
//
// and the ends' work.  The yarns' bottom ends are clamped.  Their top ends
// are fixed to an end plate, which moves up and down, drawn up by a force,
// and may turn about the axis, but never lets the ends move with respect to
// one another, so the braid cannot come undone.
//
// The yarns may also be fed: each yarn slides through its place on the
// plate, from a bobbin pulling it back with a tension T, as a braid's
// yarns come from their carriers.  The yarn inside then costs T per unit
// length, and how much there is becomes one more unknown, its links' rest
// length s.  A plate drawn up by less than the yarns' tension beats the
// braid up, until its crossings jam: the pitch, and the shape of the
// cross-section, are then what jamming leaves.  When the links grow too
// long or too short, the yarn is laid out again with new beads.
//
// The minimum of that energy is the braid at rest.  It is found by FIRE
// (Bitzek et al., Phys. Rev. Lett. 97, 170201, 2006): damped dynamics that
// speed up while going downhill and stop dead when going up.  The damping
// is FIRE's own — each step turns the velocity towards the force, and any
// step uphill stops every bead — so there is no friction term to tune.
// Every force here is the gradient of the energy, so at rest they balance:
// the tests check that they do.
//
// Lengths are in yarn diameters.

(function (root) {
  "use strict";

  // A yarn's beads again, evenly spaced about ``spacing`` apart, its two
  // ends kept.
  function relay(yarn, spacing) {
    const k = yarn.length / 3;
    const along = new Float64Array(k);
    for (let i = 1; i < k; i++) {
      along[i] =
        along[i - 1] +
        Math.hypot(yarn[3 * i] - yarn[3 * i - 3], yarn[3 * i + 1] - yarn[3 * i - 2], yarn[3 * i + 2] - yarn[3 * i - 1]);
    }
    const beads = Math.max(2, Math.round(along[k - 1] / spacing) + 1);
    const out = new Float64Array(3 * beads);
    let j = 0;
    for (let b = 0; b < beads; b++) {
      const at = (along[k - 1] * b) / (beads - 1);
      while (j < k - 2 && along[j + 1] < at) j++;
      const span = along[j + 1] - along[j];
      const f = span > 0 ? Math.min(1, Math.max(0, (at - along[j]) / span)) : 0;
      for (let c = 0; c < 3; c++) out[3 * b + c] = yarn[3 * j + c] + f * (yarn[3 * j + 3 + c] - yarn[3 * j + c]);
    }
    return out;
  }

  /**
   * @param {Object} job
   * @param {number[][]} job.yarns  Each yarn's beads, x y z after x y z,
   *     bottom end first.
   * @param {number} [job.spacing]  Rest length of a link; by default each
   *     yarn's first link's.
   * @param {number} [job.force]  Drawing the end plate up.
   * @param {boolean} [job.turns]  Whether the end plate may turn.
   * @param {number} [job.feed]  T: feed the yarns through the plate at this
   *     tension.  Without it, each yarn keeps its length.
   * @param {number} [job.stretch]  k_s.
   * @param {number} [job.bend]  k_b.
   * @param {number} [job.contact]  k_c, the cores'.
   * @param {number} [job.soft]  k_r, the soft surfaces'.
   * @param {number} [job.shell]  w, how thick the soft surface is, of a
   *     diameter; 0 for a yarn hard all through.
   * @param {number} [job.steps]  The most steps to take.
   * @param {number} [job.tolerance]  Stop once no force is larger.
   * @param {function(Object):void} [job.progress]  Told, now and then, the
   *     yarns as they are and how far along.
   * @returns {Object} The yarns at rest, the end plate's rise and turn, and
   *     how near rest they are.
   */
  function settle(job) {
    const ks = job.stretch ?? 400;
    const kb = job.bend ?? 0.5;
    const kc = job.contact ?? 400;
    const kr = job.soft ?? 5;
    const shell = job.shell ?? 0.1;
    const core = 1 - shell;
    const force = job.force ?? 1;
    const turns = Boolean(job.turns);
    const feed = job.feed ?? null;
    const steps = job.steps ?? 20000;
    const tolerance = job.tolerance ?? 1e-3;
    const nYarns = job.yarns.length;

    // The end plate, kept from one laying out of the beads to the next:
    // where each top end sits on it, its rise and its turn.
    let rise = 0;
    let turn = 0;
    const plate = job.yarns.map((yarn) => yarn.slice(yarn.length - 3));
    let rest = job.yarns.map(
      (yarn) => job.spacing ?? Math.hypot(yarn[3] - yarn[0], yarn[4] - yarn[1], yarn[5] - yarn[2]),
    );
    const spacing = rest.reduce((a, b) => a + b) / nYarns;
    let yarns = job.yarns.map((yarn) => Float64Array.from(yarn));

    let step = 0;
    let largest = Infinity;
    let contacts = 0;
    let deepest = 0;
    // The deepest the cores ever pressed into each other: any yarn passing
    // through another would have had to come right through.
    let deepestEver = 0;
    while (step < steps) {
      const outcome = run();
      if (outcome === "settled" || outcome === "spent") break;
      // Links grown too long or too short: lay the yarns out again.
      yarns = yarns.map((yarn) => relay(yarn, spacing));
      rest = yarns.map((yarn) => Math.hypot(yarn[3] - yarn[0], yarn[4] - yarn[1], yarn[5] - yarn[2]));
    }
    return {
      yarns: yarns.map((yarn) => Array.from(yarn)),
      rise,
      turn,
      steps: step,
      largestForce: largest,
      contacts,
      deepest,
      deepestEver,
      spacing: rest,
    };

    // FIRE, until at rest, out of steps, or the beads want laying out again.
    function run() {
      const first = new Int32Array(nYarns + 1);
      for (let a = 0; a < nYarns; a++) first[a + 1] = first[a] + yarns[a].length / 3;
      const n = first[nYarns];
      const x = new Float64Array(3 * n);
      yarns.forEach((yarn, a) => x.set(yarn, 3 * first[a]));
      const yarnOf = new Int32Array(n);
      const free = new Uint8Array(n).fill(1);
      const isTop = new Uint8Array(n);
      const tops = new Int32Array(nYarns);
      for (let a = 0; a < nYarns; a++) {
        yarnOf.fill(a, first[a], first[a + 1]);
        free[first[a]] = 0;
        free[first[a + 1] - 1] = 0;
        isTop[first[a + 1] - 1] = 1;
        tops[a] = first[a + 1] - 1;
      }
      const s = Float64Array.from(rest);
      const links = new Float64Array(nYarns);
      for (let a = 0; a < nYarns; a++) links[a] = first[a + 1] - first[a] - 1;

      function placeTops() {
        const c = Math.cos(turn), sn = Math.sin(turn);
        for (let a = 0; a < nYarns; a++) {
          const g = tops[a];
          const [px, py, pz] = plate[a];
          x[3 * g] = c * px - sn * py;
          x[3 * g + 1] = sn * px + c * py;
          x[3 * g + 2] = pz + rise;
        }
      }

      // Pairs of segments near enough to touch, rebuilt as beads move.
      const gap = Math.ceil(2 / spacing) + 1;
      const reach = 1 + 2 * spacing + 0.5;
      let pairs = new Int32Array(0);
      const built = new Float64Array(3 * n);
      const cells = new Int32Array(3 * n);
      function neighbours() {
        const grid = new Map();
        for (let g = 0; g < n; g++) {
          if (isTop[g]) continue;
          const i = Math.floor((x[3 * g] + x[3 * g + 3]) / 2 / reach);
          const j = Math.floor((x[3 * g + 1] + x[3 * g + 4]) / 2 / reach);
          const k = Math.floor((x[3 * g + 2] + x[3 * g + 5]) / 2 / reach);
          cells[3 * g] = i;
          cells[3 * g + 1] = j;
          cells[3 * g + 2] = k;
          const key = (i * 73856093) ^ (j * 19349663) ^ (k * 83492791);
          let list = grid.get(key);
          if (!list) grid.set(key, (list = []));
          list.push(g);
        }
        const found = [];
        for (let g = 0; g < n; g++) {
          if (isTop[g]) continue;
          const i = cells[3 * g], j = cells[3 * g + 1], k = cells[3 * g + 2];
          for (let di = -1; di <= 1; di++) {
            for (let dj = -1; dj <= 1; dj++) {
              for (let dk = -1; dk <= 1; dk++) {
                const list = grid.get(((i + di) * 73856093) ^ ((j + dj) * 19349663) ^ ((k + dk) * 83492791));
                if (!list) continue;
                for (const h of list) {
                  if (h <= g) continue;
                  if (cells[3 * h] !== i + di || cells[3 * h + 1] !== j + dj || cells[3 * h + 2] !== k + dk) continue;
                  if (yarnOf[h] === yarnOf[g] && h - g < gap) continue;
                  found.push(g, h);
                }
              }
            }
          }
        }
        pairs = Int32Array.from(found);
        built.set(x);
      }
      function stale() {
        for (let k = 0; k < 3 * n; k += 3) {
          const dx = x[k] - built[k], dy = x[k + 1] - built[k + 1], dz = x[k + 2] - built[k + 2];
          if (dx * dx + dy * dy + dz * dz > 0.0625) return true;
        }
        return false;
      }

      // The energy's gradient: f holds the forces, minus the gradient, and
      // fs the forces on the links' rest lengths, for fed yarns.
      const f = new Float64Array(3 * n);
      const fs = new Float64Array(nYarns);
      function forces() {
        f.fill(0);
        fs.fill(0);
        for (let a = 0; a < nYarns; a++) {
          const s0 = s[a];
          let strain = 0;
          for (let g = first[a]; g < first[a + 1] - 1; g++) {
            const dx = x[3 * g + 3] - x[3 * g], dy = x[3 * g + 4] - x[3 * g + 1], dz = x[3 * g + 5] - x[3 * g + 2];
            const r = Math.sqrt(dx * dx + dy * dy + dz * dz);
            strain += r - s0;
            const t = (ks * (r - s0)) / r;
            f[3 * g] += t * dx;
            f[3 * g + 1] += t * dy;
            f[3 * g + 2] += t * dz;
            f[3 * g + 3] -= t * dx;
            f[3 * g + 4] -= t * dy;
            f[3 * g + 5] -= t * dz;
          }
          if (feed !== null) fs[a] = ks * strain - feed * links[a];
          const b = kb / (s0 * s0);
          for (let g = first[a] + 1; g < first[a + 1] - 1; g++) {
            for (let c = 0; c < 3; c++) {
              const curve = x[3 * g - 3 + c] - 2 * x[3 * g + c] + x[3 * g + 3 + c];
              f[3 * g - 3 + c] -= b * curve;
              f[3 * g + c] += 2 * b * curve;
              f[3 * g + 3 + c] -= b * curve;
            }
          }
        }
        contacts = 0;
        deepest = 0;
        for (let e = 0; e < pairs.length; e += 2) {
          const i = 3 * pairs[e], j = 3 * pairs[e + 1];
          const ax = x[i + 3] - x[i], ay = x[i + 4] - x[i + 1], az = x[i + 5] - x[i + 2];
          const bx = x[j + 3] - x[j], by = x[j + 4] - x[j + 1], bz = x[j + 5] - x[j + 2];
          const rx = x[i] - x[j], ry = x[i + 1] - x[j + 1], rz = x[i + 2] - x[j + 2];
          const aa = ax * ax + ay * ay + az * az;
          const bb = bx * bx + by * by + bz * bz;
          const ab = ax * bx + ay * by + az * bz;
          const ar = ax * rx + ay * ry + az * rz;
          const br = bx * rx + by * ry + bz * rz;
          const den = aa * bb - ab * ab;
          let u = den > 1e-12 * aa * bb ? (ab * br - ar * bb) / den : 0;
          u = u < 0 ? 0 : u > 1 ? 1 : u;
          let v = (ab * u + br) / bb;
          if (v < 0) {
            v = 0;
            u = Math.min(1, Math.max(0, -ar / aa));
          } else if (v > 1) {
            v = 1;
            u = Math.min(1, Math.max(0, (ab - ar) / aa));
          }
          const px = rx + u * ax - v * bx, py = ry + u * ay - v * by, pz = rz + u * az - v * bz;
          const r2 = px * px + py * py + pz * pz;
          if (r2 >= 1) continue;
          const r = Math.sqrt(r2);
          let push = (kr * (1 - r)) / Math.max(r, 1e-9);
          if (r < core) {
            contacts++;
            if (core - r > deepest) deepest = core - r;
            if (core - r > deepestEver) deepestEver = core - r;
            push += (kc * (core - r)) / Math.max(r, 1e-9);
          }
          const qx = push * px, qy = push * py, qz = push * pz;
          f[i] += (1 - u) * qx;
          f[i + 1] += (1 - u) * qy;
          f[i + 2] += (1 - u) * qz;
          f[i + 3] += u * qx;
          f[i + 4] += u * qy;
          f[i + 5] += u * qz;
          f[j] -= (1 - v) * qx;
          f[j + 1] -= (1 - v) * qy;
          f[j + 2] -= (1 - v) * qz;
          f[j + 3] -= v * qx;
          f[j + 4] -= v * qy;
          f[j + 5] -= v * qz;
        }
      }

      const v = new Float64Array(3 * n);
      const vs = new Float64Array(nYarns);
      let vRise = 0, vTurn = 0;
      const plateMass = nYarns;
      const plateInertia = Math.max(1e-9, plate.reduce((sum, [px, py]) => sum + px * px + py * py, 0));
      let dt = 0.01;
      const dtMax = job.dtMax ?? 0.05;
      let alpha = 0.1;
      let downhill = 0;
      let restarts = 0;
      placeTops();
      neighbours();
      for (; step < steps; step++) {
        if (step % 4 === 0 && stale()) neighbours();
        forces();
        let up = force;
        let torque = 0;
        for (let a = 0; a < nYarns; a++) {
          const g = tops[a];
          up += f[3 * g + 2];
          torque += x[3 * g] * f[3 * g + 1] - x[3 * g + 1] * f[3 * g];
        }
        if (!turns) torque = 0;
        largest = Math.max(Math.abs(up), Math.abs(torque));
        let power = up * vRise + torque * vTurn;
        let fNorm = up * up + torque * torque;
        let vNorm = vRise * vRise + vTurn * vTurn;
        for (let a = 0; a < nYarns; a++) {
          // Per link, so a yarn's rest length is weighed like a bead.
          const per = fs[a] / links[a];
          largest = Math.max(largest, Math.abs(per));
          power += fs[a] * vs[a];
          fNorm += fs[a] * fs[a];
          vNorm += vs[a] * vs[a];
        }
        for (let g = 0; g < n; g++) {
          if (!free[g]) continue;
          for (let c = 0; c < 3; c++) {
            const k = 3 * g + c;
            power += f[k] * v[k];
            fNorm += f[k] * f[k];
            vNorm += v[k] * v[k];
            if (Math.abs(f[k]) > largest) largest = Math.abs(f[k]);
          }
        }
        if (step % 500 === 0 && job.progress) {
          job.progress({ step, largestForce: largest, yarns: snapshot(), rise, turn, dt, restarts, spacing: Array.from(s) });
        }
        if (largest < tolerance) {
          keep();
          return "settled";
        }
        fNorm = Math.sqrt(fNorm);
        vNorm = Math.sqrt(vNorm);
        const mix = fNorm > 0 ? (alpha * vNorm) / fNorm : 0;
        for (let g = 0; g < n; g++) {
          if (!free[g]) continue;
          for (let c = 0; c < 3; c++) v[3 * g + c] = (1 - alpha) * v[3 * g + c] + mix * f[3 * g + c];
        }
        for (let a = 0; a < nYarns; a++) vs[a] = (1 - alpha) * vs[a] + mix * fs[a];
        vRise = (1 - alpha) * vRise + mix * up;
        vTurn = (1 - alpha) * vTurn + mix * torque;
        if (power > 0) {
          if (++downhill > 5) {
            dt = Math.min(dt * 1.1, dtMax);
            alpha *= 0.99;
          }
        } else {
          restarts++;
          downhill = 0;
          dt *= 0.5;
          alpha = 0.1;
          v.fill(0);
          vs.fill(0);
          vRise = vTurn = 0;
        }
        // Semi-implicit Euler, no bead moving more than a tenth of a
        // diameter in a step, so none can pass through another.
        for (let g = 0; g < n; g++) {
          if (!free[g]) continue;
          v[3 * g] += dt * f[3 * g];
          v[3 * g + 1] += dt * f[3 * g + 1];
          v[3 * g + 2] += dt * f[3 * g + 2];
          const mx = dt * v[3 * g], my = dt * v[3 * g + 1], mz = dt * v[3 * g + 2];
          const size = Math.sqrt(mx * mx + my * my + mz * mz);
          const k = size > 0.1 ? 0.1 / size : 1;
          x[3 * g] += mx * k;
          x[3 * g + 1] += my * k;
          x[3 * g + 2] += mz * k;
        }
        let relay = false;
        for (let a = 0; a < nYarns; a++) {
          // A yarn's rest length moves its links all together: weighed so
          // it answers as fast as a bead.
          vs[a] += (dt * fs[a]) / links[a];
          s[a] += Math.max(-0.01, Math.min(0.01, dt * vs[a]));
          if (s[a] > 1.5 * spacing || s[a] < 0.6 * spacing) relay = true;
        }
        vRise += (dt * up) / plateMass;
        vTurn += (dt * torque) / plateInertia;
        rise += Math.max(-0.1, Math.min(0.1, dt * vRise));
        turn += Math.max(-0.02, Math.min(0.02, dt * vTurn));
        placeTops();
        if (relay) {
          step++;
          keep();
          return "relay";
        }
      }
      keep();
      return "spent";

      function snapshot() {
        const out = [];
        for (let a = 0; a < nYarns; a++) out.push(Array.from(x.subarray(3 * first[a], 3 * first[a + 1])));
        return out;
      }
      function keep() {
        for (let a = 0; a < nYarns; a++) yarns[a] = x.slice(3 * first[a], 3 * first[a + 1]);
        rest = Array.from(s);
      }
    }
  }

  root.settleRope = settle;
  root.relayYarn = relay;
  if (typeof module !== "undefined" && module.exports) module.exports = { settle, relay };
})(typeof self !== "undefined" ? self : globalThis);
