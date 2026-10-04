// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Tightening the yarns, for the page: braidpy.take_off.tighten_yarns, step
// for step, in JavaScript.
//
// It is the one slow part of making a braid, and in Python it is slow for a
// reason JavaScript does not share: every step is many small numpy calls
// over a hundred thousand pairs of samples, each paying its way in and out
// of numpy — and more so in WebAssembly.  Here the same loops run as they
// are written, compiled by the browser.
//
// The Python stays the reference: tests/test_web.py tightens the same braid
// both ways and checks they agree.  Everything here mirrors it, in the same
// order; the one change is that (I + step/2 L) x = b is solved as the
// tridiagonal system it is, rather than by multiplying by its inverse.
//
// Loaded as a classic script by the worker (importScripts) and required by
// Node for the tests.

(function (root) {
  "use strict";

  // Solve (I + h L) x = b in place in ``b``, for L the second difference
  // along a yarn: the last row fixed, the first fixed or free.
  function makeSettle(n, h, holdTop) {
    const lower = new Float64Array(n);
    const diagonal = new Float64Array(n);
    const upper = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      diagonal[i] = 1;
    }
    for (let i = 1; i < n - 1; i++) {
      lower[i] = -h;
      diagonal[i] = 1 + 2 * h;
      upper[i] = -h;
    }
    if (!holdTop && n > 1) {
      diagonal[0] = 1 + h;
      upper[0] = -h;
    }
    // Thomas algorithm: the forward sweep depends on the matrix only.
    const c = new Float64Array(n);
    const m = new Float64Array(n);
    m[0] = diagonal[0];
    c[0] = n > 1 ? upper[0] / m[0] : 0;
    for (let i = 1; i < n; i++) {
      m[i] = diagonal[i] - lower[i] * c[i - 1];
      c[i] = i < n - 1 ? upper[i] / m[i] : 0;
    }
    const d = new Float64Array(n);
    return function settle(values) {
      d[0] = values[0] / m[0];
      for (let i = 1; i < n; i++) {
        d[i] = (values[i] - lower[i] * d[i - 1]) / m[i];
      }
      values[n - 1] = d[n - 1];
      for (let i = n - 2; i >= 0; i--) {
        values[i] = d[i] - c[i] * values[i + 1];
      }
    };
  }

  /**
   * Pull the yarns taut, without letting them overlap.
   *
   * @param {Object} job
   * @param {Float64Array|number[]} job.xy  Samples' x and y, yarn after yarn:
   *     sample i of yarn a at (a * n + i) * 2.
   * @param {number} job.n_yarns
   * @param {number} job.n  Samples per yarn, oldest first.
   * @param {number} job.spacing  Height between levels.
   * @param {number} job.yarn_diameter
   * @param {number} job.iterations
   * @param {number} job.step
   * @param {number} job.tolerance
   * @param {boolean} job.hold_top
   * @param {?number} job.core_radius
   * @param {number[]} job.centre  The axis, for the core.
   * @param {boolean[]} [job.rigid]  Yarns held where they are all along,
   *     as stiff cores.
   * @param {function(number):void} [progress]  Told the fraction done.
   * @returns {{xy: Float64Array, closest: number}}
   */
  function tightenYarns(job, progress) {
    const nYarns = job.n_yarns;
    const n = job.n;
    const d = job.yarn_diameter;
    const spacing = job.spacing;
    const rows = nYarns * n;
    const xy = Float64Array.from(job.xy);
    const maxMove = d / 5;
    const slack = job.tolerance * d;
    const [cx, cy] = job.centre;
    const core = job.core_radius;

    const offsets = [];
    const count = spacing <= 0 ? 1 : Math.min(n, Math.ceil(d / spacing));
    for (let o = 0; o < count; o++) offsets.push(o);

    const held = new Uint8Array(rows);
    const free = new Float64Array(rows);
    for (let k = 0; k < rows; k++) {
      const level = k % n;
      const rigid = job.rigid && job.rigid[Math.floor(k / n)];
      held[k] = rigid || level === n - 1 || (level === 0 && job.hold_top) ? 1 : 0;
      free[k] = held[k] ? 0 : 1;
    }
    const settle = makeSettle(n, 0.5 * job.step, job.hold_top);

    // Pairs of samples that could touch before the list is rebuilt.
    let p = new Int32Array(0);
    let q = new Int32Array(0);
    let need = new Float64Array(0);
    let rise = new Float64Array(0);
    function neighbours() {
      const ps = [];
      const qs = [];
      const needs = [];
      const rises = [];
      for (const o of offsets) {
        const reach = Math.sqrt(Math.max(d * d - (o * spacing) ** 2, 0));
        for (let a = 0; a < nYarns; a++) {
          for (let b = 0; b < nYarns; b++) {
            if (o === 0 ? a >= b : a === b) continue;
            for (let i = 0; i < n - o; i++) {
              const s = a * n + i;
              const t = b * n + i + o;
              // Only where one of the two is free to move.
              if (free[s] + free[t] <= 0) continue;
              const dx = xy[2 * s] - xy[2 * t];
              const dy = xy[2 * s + 1] - xy[2 * t + 1];
              if (Math.sqrt(dx * dx + dy * dy) < reach + d) {
                ps.push(s);
                qs.push(t);
                needs.push(reach);
                rises.push(o * spacing);
              }
            }
          }
        }
      }
      p = Int32Array.from(ps);
      q = Int32Array.from(qs);
      need = Float64Array.from(needs);
      rise = Float64Array.from(rises);
    }

    const push = new Float64Array(2 * rows);
    function separate() {
      for (let round = 0; round < 50; round++) {
        push.fill(0);
        let worst = 0;
        for (let j = 0; j < p.length; j++) {
          const s = p[j];
          const t = q[j];
          const dx = xy[2 * s] - xy[2 * t];
          const dy = xy[2 * s + 1] - xy[2 * t + 1];
          const dist = Math.sqrt(dx * dx + dy * dy);
          const short = need[j] - dist;
          if (short > slack) {
            if (short > worst) worst = short;
            // In numpy's order, operation for operation: where yarns meet,
            // at a braiding point, which way two samples part is decided
            // by the last digit.
            const length = Math.max(dist, 1e-300);
            const gx = short * (dx / length);
            const gy = short * (dy / length);
            // Shared between the two, or all to the one free to move.
            const share = free[s] / (free[s] + free[t]);
            push[2 * s] += share * gx;
            push[2 * s + 1] += share * gy;
            push[2 * t] += -(1 - share) * gx;
            push[2 * t + 1] += -(1 - share) * gy;
          }
        }
        if (core !== null && core !== undefined) {
          const inner = core + d / 2;
          for (let k = 0; k < rows; k++) {
            const rx = xy[2 * k] - cx;
            const ry = xy[2 * k + 1] - cy;
            const r = Math.sqrt(rx * rx + ry * ry);
            if (r < inner) {
              if (inner - r > worst) worst = inner - r;
              const length = Math.max(r, 1e-300);
              push[2 * k] += (rx / length) * (inner - r);
              push[2 * k + 1] += (ry / length) * (inner - r);
            }
          }
        }
        if (worst <= slack) return;
        for (let k = 0; k < rows; k++) {
          if (held[k]) continue;
          clampAdd(k, push[2 * k], push[2 * k + 1]);
        }
      }
    }

    // Move a sample, but never more than a fifth of a diameter at once.
    function clampAdd(k, mx, my) {
      const size = Math.sqrt(mx * mx + my * my);
      const factor = Math.min(1, maxMove / Math.max(size, 1e-300));
      xy[2 * k] += mx * factor;
      xy[2 * k + 1] += my * factor;
    }

    function movedSince(built) {
      let most = 0;
      for (let k = 0; k < rows; k++) {
        const dx = xy[2 * k] - built[2 * k];
        const dy = xy[2 * k + 1] - built[2 * k + 1];
        const moved = Math.sqrt(dx * dx + dy * dy);
        if (moved > most) most = moved;
      }
      return most;
    }

    function closest() {
      let best = Infinity;
      for (let j = 0; j < p.length; j++) {
        const dx = xy[2 * p[j]] - xy[2 * q[j]];
        const dy = xy[2 * p[j] + 1] - xy[2 * q[j] + 1];
        const squared = dx * dx + dy * dy + rise[j] * rise[j];
        if (squared < best) best = squared;
      }
      return Math.sqrt(best);
    }

    neighbours();
    let built = Float64Array.from(xy);
    separate();
    const column = new Float64Array(n);
    const target = new Float64Array(2 * rows);
    for (let iteration = 0; iteration < job.iterations; iteration++) {
      // Tension: every yarn, x and y alike, settled along its length.
      for (let a = 0; a < nYarns; a++) {
        for (let c = 0; c < 2; c++) {
          for (let i = 0; i < n; i++) column[i] = xy[2 * (a * n + i) + c];
          settle(column);
          for (let i = 0; i < n; i++) target[2 * (a * n + i) + c] = column[i];
        }
      }
      for (let k = 0; k < rows; k++) {
        if (held[k]) continue;
        clampAdd(k, target[2 * k] - xy[2 * k], target[2 * k + 1] - xy[2 * k + 1]);
      }
      separate();
      // The push itself can carry a sample out of the list's reach.
      while (movedSince(built) > d / 4) {
        neighbours();
        built = Float64Array.from(xy);
        separate();
      }
      if (progress && iteration % 10 === 0) progress(iteration / job.iterations);
    }
    return { xy, closest: closest() };
  }

  root.tightenYarns = tightenYarns;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { tightenYarns };
  }
})(typeof self !== "undefined" ? self : globalThis);
