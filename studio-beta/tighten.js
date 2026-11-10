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
// The Python stays the reference: tests/test_tighten_js.py tightens the same braid
// both ways and checks they agree.  Everything here mirrors it, in the same
// order, (I + step/2 L) x = b solved as the same tridiagonal system, or,
// endless, as the same system round a closed loop.
//
// Loaded as a classic script by the worker (importScripts) and required by
// Node for the tests.

(function (root) {
  "use strict";

  // A tridiagonal system, solved in place by the Thomas algorithm: the
  // forward sweep depends on the matrix only, and is done once.  braidpy's
  // _thomas.
  function thomas(lower, diagonal, upper) {
    const n = diagonal.length;
    const c = new Float64Array(n);
    const m = new Float64Array(n);
    m[0] = diagonal[0];
    c[0] = n > 1 ? upper[0] / m[0] : 0;
    for (let i = 1; i < n; i++) {
      m[i] = diagonal[i] - lower[i] * c[i - 1];
      c[i] = i < n - 1 ? upper[i] / m[i] : 0;
    }
    const d = new Float64Array(n);
    return function solve(values) {
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

  // Solve (I + h L) x = b in place in ``b``, for L the second difference
  // along a yarn: the last row fixed, the first fixed or free.  braidpy's
  // _tension_solver.
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
    return thomas(lower, diagonal, upper);
  }

  // The fewest samples round a closed loop that tension can settle: with
  // fewer, a sample's two neighbours are one sample, or itself.  braidpy's
  // FEWEST_ROUND.
  const FEWEST_ROUND = 3;

  // Solve (I + w L) x = b in place in ``b``, for L the second difference
  // round a closed loop: the open system with its corners folded into its
  // first and last diagonal terms, corrected by one column worked out once
  // (Sherman and Morrison).  braidpy's _loop_settler.
  function loopSettle(length, weight) {
    if (length < FEWEST_ROUND) return function settle() {};
    const side = -weight;
    const middle = 1.0 + 2.0 * weight;
    const gamma = -middle;
    const lower = new Float64Array(length).fill(side);
    const upper = new Float64Array(length).fill(side);
    const diagonal = new Float64Array(length).fill(middle);
    diagonal[0] = middle - gamma;
    diagonal[length - 1] = middle - (side * side) / gamma;
    const solve = thomas(lower, diagonal, upper);
    const z = new Float64Array(length);
    z[0] = gamma;
    z[length - 1] = side;
    solve(z);
    const below = 1.0 + z[0] + (side * z[length - 1]) / gamma;
    return function settle(values) {
      solve(values);
      const fact = (values[0] + (side * values[length - 1]) / gamma) / below;
      for (let i = 0; i < length; i++) values[i] = values[i] - fact * z[i];
    };
  }

  // How close a sample at the fell end of a window must be to its
  // partner's at the top for the two to be one level met twice.  braidpy's
  // TIED.
  const TIED = 1e-6;

  // The closed loops the wrap makes, as sample indices in order: one per
  // cycle of the partners, the repeated last level left out if ``tied``.
  // braidpy's Periodic.loops.
  function loopsOf(partner, n, tied) {
    const seen = new Set();
    const found = [];
    const last = tied ? n - 1 : n;
    for (let start = 0; start < partner.length; start++) {
      if (seen.has(start)) continue;
      const loop = [];
      let here = start;
      while (!seen.has(here)) {
        seen.add(here);
        for (let i = 0; i < last; i++) loop.push(here * n + i);
        here = partner[here];
      }
      found.push(Int32Array.from(loop));
    }
    return found;
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
   * @param {?number[]} [job.partner]  The yarn each one runs into past the
   *     fell end, for a braid laid over a whole number of periods.
   * @param {boolean} [job.periodic]  Tighten it as a window on an endless
   *     braid, joining each yarn's fell end to its partner's top, rather
   *     than holding both ends: braidpy's Periodic.
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

    const partner = job.periodic && job.partner ? job.partner : null;
    if (partner && partner.length !== nYarns) {
      throw new Error(`partner covers ${partner.length} yarns, the braid has ${nYarns}`);
    }
    const held = new Uint8Array(rows);
    const free = new Float64Array(rows);
    for (let k = 0; k < rows; k++) {
      const level = k % n;
      const rigid = job.rigid && job.rigid[Math.floor(k / n)];
      // Endless, neither end is held: the braid runs on into its own copy.
      const end = !partner && (level === n - 1 || (level === 0 && job.hold_top));
      held[k] = rigid || end ? 1 : 0;
      free[k] = held[k] ? 0 : 1;
    }
    const settle = partner ? null : makeSettle(n, 0.5 * job.step, job.hold_top);

    // Endless: the last level, laid over a whole period, is the first over
    // again, tied to it rather than a sample of its own.
    let tied = false;
    if (partner) {
      let gap = 0;
      for (let a = 0; a < nYarns; a++) {
        for (let c = 0; c < 2; c++) {
          const off = Math.abs(xy[2 * (a * n + n - 1) + c] - xy[2 * partner[a] * n + c]);
          if (off > gap) gap = off;
        }
      }
      tied = gap <= TIED;
    }
    const loops = partner ? loopsOf(partner, n, tied) : [];
    const settlers = new Map();
    for (const loop of loops) {
      if (!settlers.has(loop.length)) settlers.set(loop.length, loopSettle(loop.length, 0.5 * job.step));
    }
    function tie() {
      if (!tied) return;
      for (let a = 0; a < nYarns; a++) {
        const k = a * n + n - 1;
        const t = partner[a] * n;
        xy[2 * k] = xy[2 * t];
        xy[2 * k + 1] = xy[2 * t + 1];
      }
    }

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
            // Endless and tied: every level but the tied one, against
            // levels up to past the fell end, in the next copy (braidpy's
            // ``beyond``).
            const top = tied ? n - 1 : n - o;
            for (let i = 0; i < top; i++) {
              const s = a * n + i;
              const j = i + o;
              const t = !tied || j < n - 1 ? b * n + j : partner[b] * n + (j - (n - 1));
              if (s === t) continue;
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
        if (worst <= slack) break;
        for (let k = 0; k < rows; k++) {
          if (held[k]) continue;
          clampAdd(k, push[2 * k], push[2 * k + 1]);
        }
      }
      tie();
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
      // Tension: every yarn, x and y alike, settled along its length — or,
      // endless, round its loop.
      if (partner) {
        target.set(xy);
        for (const loop of loops) {
          const round = new Float64Array(loop.length);
          const settleRound = settlers.get(loop.length);
          for (let c = 0; c < 2; c++) {
            for (let i = 0; i < loop.length; i++) round[i] = xy[2 * loop[i] + c];
            settleRound(round);
            for (let i = 0; i < loop.length; i++) target[2 * loop[i] + c] = round[i];
          }
        }
      } else {
        for (let a = 0; a < nYarns; a++) {
          for (let c = 0; c < 2; c++) {
            for (let i = 0; i < n; i++) column[i] = xy[2 * (a * n + i) + c];
            settle(column);
            for (let i = 0; i < n; i++) target[2 * (a * n + i) + c] = column[i];
          }
        }
      }
      for (let k = 0; k < rows; k++) {
        if (held[k]) continue;
        clampAdd(k, target[2 * k] - xy[2 * k], target[2 * k + 1] - xy[2 * k + 1]);
      }
      tie();
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
