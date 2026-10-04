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
// - contact: k_c/2 (d - r)^2 for any two segments of different yarns (or of
//   one yarn, far apart along it) whose axes come closer than a diameter d;
//
// and the ends' work: the yarns' bottom ends are clamped, and their top ends
// are fixed to an end plate, which moves up and down — pulled up by a force
// — and may turn about the axis, but never lets the ends move with respect
// to one another, so the braid cannot come undone.
//
// The minimum of that energy is the braid at rest, its yarns pulled taut.
// It is found by FIRE (Bitzek et al., Phys. Rev. Lett. 97, 170201, 2006):
// damped dynamics that speed up while going downhill and stop dead when
// going up.  Every force here is the gradient of the energy, so at rest
// they balance: the tests check that they do.
//
// Lengths are in yarn diameters.

(function (root) {
  "use strict";

  /**
   * @param {Object} job
   * @param {number[][]} job.yarns  Each yarn's beads, x y z after x y z,
   *     bottom end first.
   * @param {number} [job.spacing]  Rest length of a link; by default each
   *     yarn's first link's.
   * @param {number} [job.force]  Pulling the end plate up.
   * @param {boolean} [job.turns]  Whether the end plate may turn.
   * @param {number} [job.stretch]  k_s.
   * @param {number} [job.bend]  k_b.
   * @param {number} [job.contact]  k_c.
   * @param {number} [job.steps]  The most steps to take.
   * @param {number} [job.tolerance]  Stop once no force is larger.
   * @returns {Object} The yarns at rest, the end plate's rise and turn, and
   *     how near rest they are.
   */
  function settle(job) {
    const ks = job.stretch ?? 400;
    const kb = job.bend ?? 0.5;
    const kc = job.contact ?? 400;
    const force = job.force ?? 1;
    const turns = Boolean(job.turns);
    const steps = job.steps ?? 20000;
    const tolerance = job.tolerance ?? 1e-3;

    const nYarns = job.yarns.length;
    const first = [0];
    for (const yarn of job.yarns) first.push(first[first.length - 1] + yarn.length / 3);
    const n = first[nYarns];
    const x = new Float64Array(3 * n);
    job.yarns.forEach((yarn, a) => x.set(yarn, 3 * first[a]));
    const rest = job.yarns.map((yarn) =>
      job.spacing ?? Math.hypot(yarn[3] - yarn[0], yarn[4] - yarn[1], yarn[5] - yarn[2]),
    );
    const yarnOf = new Int32Array(n);
    for (let a = 0; a < nYarns; a++) yarnOf.fill(a, first[a], first[a + 1]);
    const bottom = (g) => first.includes(g);
    const top = (g) => first.includes(g + 1);

    // The end plate: where it is, how far turned, and where each yarn's top
    // end sits on it.
    const tops = [];
    for (let a = 0; a < nYarns; a++) tops.push(first[a + 1] - 1);
    let rise = 0;
    let turn = 0;
    const plate = tops.map((g) => [x[3 * g], x[3 * g + 1], x[3 * g + 2]]);
    function placeTops() {
      const c = Math.cos(turn), s = Math.sin(turn);
      tops.forEach((g, a) => {
        const [px, py, pz] = plate[a];
        x[3 * g] = c * px - s * py;
        x[3 * g + 1] = s * px + c * py;
        x[3 * g + 2] = pz + rise;
      });
    }

    // Pairs of segments near enough to touch, rebuilt as beads move.
    const gap = Math.ceil(2 / Math.min(...rest)) + 1;
    let pairs = new Int32Array(0);
    let built = new Float64Array(0);
    const reach = 1 + Math.max(...rest) * 1.5 + 0.5;
    function neighbours() {
      const grid = new Map();
      const key = (i, j, k) => `${i},${j},${k}`;
      const cell = (g) => [
        Math.floor((x[3 * g] + x[3 * g + 3]) / 2 / reach),
        Math.floor((x[3 * g + 1] + x[3 * g + 4]) / 2 / reach),
        Math.floor((x[3 * g + 2] + x[3 * g + 5]) / 2 / reach),
      ];
      for (let g = 0; g < n; g++) {
        if (top(g)) continue;
        const k = key(...cell(g));
        if (!grid.has(k)) grid.set(k, []);
        grid.get(k).push(g);
      }
      const found = [];
      for (let g = 0; g < n; g++) {
        if (top(g)) continue;
        const [i, j, k] = cell(g);
        for (let di = -1; di <= 1; di++) {
          for (let dj = -1; dj <= 1; dj++) {
            for (let dk = -1; dk <= 1; dk++) {
              for (const h of grid.get(key(i + di, j + dj, k + dk)) || []) {
                if (h <= g) continue;
                if (yarnOf[h] === yarnOf[g] && h - g < gap) continue;
                found.push(g, h);
              }
            }
          }
        }
      }
      pairs = Int32Array.from(found);
      built = Float64Array.from(x);
    }
    function stale() {
      for (let k = 0; k < 3 * n; k += 3) {
        if (Math.hypot(x[k] - built[k], x[k + 1] - built[k + 1], x[k + 2] - built[k + 2]) > 0.25) {
          return true;
        }
      }
      return false;
    }

    // The closest points of segments g and h: fractions along each.
    function closest(g, h) {
      const i = 3 * g, j = 3 * h;
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
      u = Math.min(1, Math.max(0, u));
      let v = (ab * u + br) / bb;
      if (v < 0) {
        v = 0;
        u = Math.min(1, Math.max(0, -ar / aa));
      } else if (v > 1) {
        v = 1;
        u = Math.min(1, Math.max(0, (ab - ar) / aa));
      }
      return [u, v];
    }

    // The energy's gradient: f holds the forces, minus the gradient.
    const f = new Float64Array(3 * n);
    let contacts = 0;
    let deepest = 0;
    function forces() {
      f.fill(0);
      for (let a = 0; a < nYarns; a++) {
        const s0 = rest[a];
        for (let g = first[a]; g < first[a + 1] - 1; g++) {
          const dx = x[3 * g + 3] - x[3 * g], dy = x[3 * g + 4] - x[3 * g + 1], dz = x[3 * g + 5] - x[3 * g + 2];
          const r = Math.hypot(dx, dy, dz);
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
        const g = pairs[e], h = pairs[e + 1];
        const [u, v] = closest(g, h);
        const px = x[3 * g] + u * (x[3 * g + 3] - x[3 * g]) - x[3 * h] - v * (x[3 * h + 3] - x[3 * h]);
        const py = x[3 * g + 1] + u * (x[3 * g + 4] - x[3 * g + 1]) - x[3 * h + 1] - v * (x[3 * h + 4] - x[3 * h + 1]);
        const pz = x[3 * g + 2] + u * (x[3 * g + 5] - x[3 * g + 2]) - x[3 * h + 2] - v * (x[3 * h + 5] - x[3 * h + 2]);
        const r = Math.hypot(px, py, pz);
        if (r >= 1) continue;
        contacts++;
        deepest = Math.max(deepest, 1 - r);
        const push = (kc * (1 - r)) / Math.max(r, 1e-9);
        for (let c = 0; c < 3; c++) {
          const p = push * [px, py, pz][c];
          f[3 * g + c] += (1 - u) * p;
          f[3 * g + 3 + c] += u * p;
          f[3 * h + c] -= (1 - v) * p;
          f[3 * h + 3 + c] -= v * p;
        }
      }
    }

    // The end plate's own forces, from the yarns' top ends and the pull.
    function plateForces() {
      let up = force;
      let torque = 0;
      for (const g of tops) {
        up += f[3 * g + 2];
        torque += x[3 * g] * f[3 * g + 1] - x[3 * g + 1] * f[3 * g];
      }
      return [up, turns ? torque : 0];
    }

    // FIRE.
    const v = new Float64Array(3 * n);
    let vRise = 0, vTurn = 0;
    const plateMass = nYarns;
    const plateInertia = Math.max(1e-9, plate.reduce((sum, [px, py]) => sum + px * px + py * py, 0));
    let dt = 0.01;
    const dtMax = 0.05;
    let alpha = 0.1;
    let downhill = 0;
    let step = 0;
    let largest = Infinity;
    const free = (g) => !bottom(g) && !top(g);
    placeTops();
    neighbours();
    for (; step < steps; step++) {
      if (stale()) neighbours();
      forces();
      const [up, torque] = plateForces();
      largest = Math.max(Math.abs(up), Math.abs(torque));
      let power = up * vRise + torque * vTurn;
      let fNorm = up * up + torque * torque;
      let vNorm = vRise * vRise + vTurn * vTurn;
      for (let g = 0; g < n; g++) {
        if (!free(g)) continue;
        for (let c = 0; c < 3; c++) {
          const k = 3 * g + c;
          power += f[k] * v[k];
          fNorm += f[k] * f[k];
          vNorm += v[k] * v[k];
          largest = Math.max(largest, Math.abs(f[k]));
        }
      }
      if (largest < tolerance) break;
      fNorm = Math.sqrt(fNorm);
      vNorm = Math.sqrt(vNorm);
      const mix = fNorm > 0 ? (alpha * vNorm) / fNorm : 0;
      for (let g = 0; g < n; g++) {
        if (!free(g)) continue;
        for (let c = 0; c < 3; c++) v[3 * g + c] = (1 - alpha) * v[3 * g + c] + mix * f[3 * g + c];
      }
      vRise = (1 - alpha) * vRise + mix * up;
      vTurn = (1 - alpha) * vTurn + mix * torque;
      if (power > 0) {
        if (++downhill > 5) {
          dt = Math.min(dt * 1.1, dtMax);
          alpha *= 0.99;
        }
      } else {
        downhill = 0;
        dt *= 0.5;
        alpha = 0.1;
        v.fill(0);
        vRise = vTurn = 0;
      }
      // Semi-implicit Euler, no bead moving more than a tenth of a
      // diameter in a step, so none can pass through another.
      for (let g = 0; g < n; g++) {
        if (!free(g)) continue;
        let mx = 0, my = 0, mz = 0;
        v[3 * g] += dt * f[3 * g];
        v[3 * g + 1] += dt * f[3 * g + 1];
        v[3 * g + 2] += dt * f[3 * g + 2];
        mx = dt * v[3 * g];
        my = dt * v[3 * g + 1];
        mz = dt * v[3 * g + 2];
        const size = Math.hypot(mx, my, mz);
        const k = size > 0.1 ? 0.1 / size : 1;
        x[3 * g] += mx * k;
        x[3 * g + 1] += my * k;
        x[3 * g + 2] += mz * k;
      }
      vRise += (dt * up) / plateMass;
      vTurn += (dt * torque) / plateInertia;
      rise += Math.max(-0.1, Math.min(0.1, dt * vRise));
      turn += Math.max(-0.02, Math.min(0.02, dt * vTurn));
      placeTops();
    }

    const yarns = [];
    for (let a = 0; a < nYarns; a++) yarns.push(Array.from(x.subarray(3 * first[a], 3 * first[a + 1])));
    return { yarns, rise, turn, steps: step, largestForce: largest, contacts, deepest };
  }

  root.settleRope = settle;
  if (typeof module !== "undefined" && module.exports) module.exports = { settle };
})(typeof self !== "undefined" ? self : globalThis);
