// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A braid made by its carriers: each yarn drawn by its carrier going round
// the machine, through a forming ring, into the braid taken off above.
//
// braidpy.carried's make, step for step: braidpy (carriers_job) works out
// where each carrier's eye is at each moment, the yarns as they start, the
// ring and every setting; this makes the braid from them, faster, in the
// page.  The method is described there and in docs/source/rope_physics.md;
// tests/test_carried_js.py runs both and compares them, bead for bead.
//
// The mechanics are rope.js's (stretching, bending, contact, FIRE) and
// form.js's friction, as braidpy.carried uses braidpy.rope's and
// braidpy.form's.

(function (root) {
  "use strict";

  const { nearPairs, stale, touching, spread, stretchAndBend, fireSums, fireMix, steer, moveBeads } =
    root.yarnMechanics || require("./rope.js").yarnMechanics;
  const frictionForce = root.frictionForce || require("./form.js").frictionForce;

  /**
   * The braid made from a job.
   *
   * @param {Object} job  As braidpy.carried.carriers_job gives it: eyes,
   *     per moment each carrier's [x, y]; start, each yarn's beads flat, the
   *     first made; substeps; ring; settings.
   * @param {Object} [hooks]
   * @param {number} [hooks.frameEvery]  Keep a moment every so many
   *     settlings; 0 for none.
   * @param {function(Object):void} [hooks.progress]  Told after each step
   *     of the machine: {step, of}.
   * @returns {{yarns: number[][], made: number[], deepest: number, frames:
   *     Object[]}} Each yarn, oldest first, flat: the braid made, then the
   *     free beads; how many of each are made; how deep any two yarns'
   *     cores pressed into each other; and the moments kept, each {sample,
   *     yarns, made}.
   */
  function make(job, hooks = {}) {
    const st = job.settings;
    const ring = job.ring;
    const substeps = job.substeps;
    const zLow = ring.height - st.below;
    const zMade = ring.height + st.above;
    const vSub = st.take_off / substeps;
    let nextId = 0;
    const bead = (p) => ({ p: [p[0], p[1], p[2]], id: nextId++ });

    const chains = job.start.map((flat) => {
      const beads = [];
      for (let i = 0; i < flat.length; i += 3) beads.push(bead(flat.slice(i, i + 3)));
      return { made: beads.slice(0, 1), free: beads.slice(1) };
    });
    const state = { offset: 0, deepest: 0 };
    const grips = new Map();
    const frames = [];

    function snapshot() {
      return {
        yarns: chains.map((y) => {
          const flat = [];
          for (const b of y.made) flat.push(b.p[0], b.p[1], b.p[2] + state.offset);
          for (const b of y.free) flat.push(...b.p);
          return flat;
        }),
        made: chains.map((y) => y.made.length),
      };
    }

    const samples = job.eyes.length;
    for (let sample = 1; sample < samples; sample++) {
      state.offset += vSub;
      const eyes = job.eyes[sample];
      state.deepest = Math.max(state.deepest, settle(chains, state.offset, eyes, grips, st, ring));
      feed(chains, eyes, zLow, st.spacing, bead);
      for (const y of chains) {
        while (y.free.length > 2 && y.free[0].p[2] > zMade) {
          const b = y.free.shift();
          b.p[2] -= state.offset;
          y.made.push(b);
        }
      }
      if (hooks.frameEvery && sample % hooks.frameEvery === 0) frames.push({ sample, ...snapshot() });
      if (hooks.progress && sample % substeps === 0) {
        hooks.progress({ step: sample / substeps, of: Math.floor((samples - 1) / substeps) });
      }
    }
    return { ...snapshot(), deepest: state.deepest, frames };
  }

  // Each carrier pays yarn out, a bead at the bottom, while the braid has
  // drawn its lowest bead up over zLow; and takes it back while the yarn has
  // slackened down under it.
  function feed(chains, eyes, zLow, spacing, bead) {
    chains.forEach((y, k) => {
      for (;;) {
        const low = y.free[y.free.length - 1].p;
        if (low[2] > zLow) {
          const dx = eyes[k][0] - low[0], dy = eyes[k][1] - low[1], dz = -low[2];
          const f = spacing / Math.sqrt(dx * dx + dy * dy + dz * dz);
          y.free.push(bead([low[0] + dx * f, low[1] + dy * f, low[2] + dz * f]));
        } else if (low[2] < zLow - spacing && y.free.length > 2) {
          y.free.pop();
        } else {
          break;
        }
      }
    });
  }

  // The free beads settled by FIRE: stretching and bending, contacts and
  // their friction, each carrier's pull and the ring.  Returns how deep any
  // two yarns' cores pressed into each other.
  function settle(chains, offset, eyes, grips, st, ring) {
    const spacing = st.spacing;
    const core = 1 - st.shell;
    const mu = st.friction, kt = st.grip, keyOf = st.key;
    const fire = st.fire;
    // Near enough to touch before beads move a quarter diameter, as form.js
    // finds them.
    const gap = Math.ceil(2 / spacing) + 1;
    const reach = 1 + 2 * spacing + 0.5;
    const xs = [], ids = [], moves = [], yarnOf = [], spans = [];
    let low = Infinity;
    for (const y of chains) for (const b of y.free) low = Math.min(low, b.p[2]);
    chains.forEach((y, a) => {
      const first = ids.length;
      // The made braid near the free yarns, then the free beads.
      let near = y.made.slice(-st.near_made).filter((b) => b.p[2] + offset > low - reach);
      if (!near.length) near = y.made.slice(-1);
      for (const b of near) {
        xs.push(b.p[0], b.p[1], b.p[2] + offset);
        ids.push(b.id);
        moves.push(0);
        yarnOf.push(a);
      }
      for (const b of y.free) {
        xs.push(b.p[0], b.p[1], b.p[2]);
        ids.push(b.id);
        moves.push(1);
        yarnOf.push(a);
      }
      spans.push([first, ids.length - 1]);
    });
    const n = ids.length;
    const x = xs;
    const segs = [];
    for (const [first, last] of spans) for (let g = first; g < last; g++) segs.push(g);
    const cells = new Array(3 * n).fill(0);
    let built = x.slice();
    let pairs = [];
    let keysHere = new Set();
    const accept = (g, h) => !!(moves[g] || moves[g + 1] || moves[h] || moves[h + 1]);

    function neighbours() {
      pairs = nearPairs(x, segs, yarnOf, gap, reach, cells, accept);
      built = x.slice();
      keysHere = new Set();
      for (let e = 0; e < pairs.length; e += 2) keysHere.add(ids[pairs[e]] * keyOf + ids[pairs[e + 1]]);
    }

    const f = new Array(3 * n).fill(0);
    let v = new Array(3 * n).fill(0);
    const touched = new Set();
    const now = { dt: fire.dt, deepest: 0 };

    function touch(e, u, w, px, py, pz, r2) {
      const g = pairs[e], h = pairs[e + 1];
      const i = 3 * g, j = 3 * h;
      const r = Math.sqrt(r2);
      let push = st.soft * (1 - r);
      if (r < core) {
        now.deepest = Math.max(now.deepest, core - r);
        push += st.contact * (core - r);
      }
      const nx = px / Math.max(r, 1e-9), ny = py / Math.max(r, 1e-9), nz = pz / Math.max(r, 1e-9);
      let qx = push * nx, qy = push * ny, qz = push * nz;
      if (mu > 0) {
        const key = ids[g] * keyOf + ids[h];
        touched.add(key);
        const [tx, ty, tz] = frictionForce(grips, key, v, i, j, u, w, nx, ny, nz, push, now.dt, mu, kt);
        qx = qx + tx;
        qy = qy + ty;
        qz = qz + tz;
      }
      spread(f, i, j, u, w, qx, qy, qz);
    }

    const clear = ring.wire + st.radius;

    function forces() {
      f.fill(0);
      for (const [first, last] of spans) stretchAndBend(x, f, first, last, spacing, st.stretch, st.bend);
      // Each carrier's pull on its lowest bead.
      spans.forEach(([, last], a) => {
        const i = 3 * last;
        const dx = eyes[a][0] - x[i], dy = eyes[a][1] - x[i + 1], dz = -x[i + 2];
        const r = Math.sqrt(dx * dx + dy * dy + dz * dz);
        f[i] += (st.tension * dx) / r;
        f[i + 1] += (st.tension * dy) / r;
        f[i + 2] += (st.tension * dz) / r;
      });
      // The ring's wire: a bead closer to it than its radius and a yarn's
      // is pushed off it.
      for (let g = 0; g < n; g++) {
        if (!moves[g]) continue;
        const i = 3 * g;
        const r = Math.hypot(x[i], x[i + 1]);
        const qr = r - ring.radius, qz = x[i + 2] - ring.height;
        const dist = Math.hypot(qr, qz);
        if (dist < clear) {
          const push = (st.contact * (clear - dist)) / Math.max(dist, 1e-9);
          f[i] += (push * qr * x[i]) / Math.max(r, 1e-9);
          f[i + 1] += (push * qr * x[i + 1]) / Math.max(r, 1e-9);
          f[i + 2] += push * qz;
        }
      }
      now.deepest = 0;
      touched.clear();
      touching(x, pairs, touch);
      for (const key of keysHere) if (!touched.has(key)) grips.delete(key);
    }

    let dt = fire.dt, alpha = fire.alpha, downhill = 0;
    const none = [];
    neighbours();
    let deepest = 0;
    for (let step = 0; step < st.most_steps; step++) {
      if (stale(x, built)) neighbours();
      now.dt = dt;
      forces();
      deepest = Math.max(deepest, now.deepest);
      const sums = [0, 0, 0, 0];
      fireSums(f, v, moves, none, none, none, sums);
      if (sums[3] < st.tolerance) break;
      const mix = fireMix(sums, alpha);
      steer(v, f, moves, [], none, alpha, mix);
      if (sums[0] > 0) {
        downhill += 1;
        if (downhill > fire.after) {
          dt = Math.min(dt * fire.grow, fire.dt_most);
          alpha *= fire.damp;
        }
      } else {
        downhill = 0;
        dt *= fire.shrink;
        alpha = fire.alpha;
        v.fill(0);
      }
      moveBeads(x, v, f, dt, moves);
    }
    chains.forEach((y, a) => {
      const last = spans[a][1];
      y.free.forEach((b, k) => {
        const g = last - y.free.length + 1 + k;
        b.p = [x[3 * g], x[3 * g + 1], x[3 * g + 2]];
      });
    });
    return deepest;
  }

  root.makeByCarriers = make;
  if (typeof module !== "undefined" && module.exports) module.exports = { make };
})(typeof self !== "undefined" ? self : globalThis);
