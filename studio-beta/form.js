// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Making a braid crossing by crossing: beaten up, row by row, with friction.
//
// rope.js beats a whole laid braid up at once.  Here the braid is made from
// its oldest row up, as a braid is made: its yarns as laid by braidpy, in the
// order their crossings are made, so the crossings are the right ones.
//
// The yarns are in three parts:
//
// - made: below a working window, the braid already beaten up, frozen;
// - working: the window, a row or two, where the yarns move — the same
//   stretching, bending and contact as rope.js, plus friction;
// - to come: above it, the rest of the braid as laid, moving as one block.
//   The yarns' tension draws it down onto the window, a weight draws it up:
//   while the yarns pull harder, the newest row is beaten up against the made
//   braid, until its crossings jam.
//
// Each yarn slides into the window from the block at its tension, as from a
// bobbin.  Once a row is beaten up, the lower part of the window is frozen
// into the made braid, and the window takes in the next row from the block.
// The block only ever moves as one, and the window's yarns never pass
// through each other or through the yarns above or below, so the braid made
// is the braid laid.
//
// Friction: two yarns in contact hold each other along their surfaces with a
// spring from where they first touched, until its pull reaches mu times the
// push between them, when they slip (Coulomb's law, as the discrete element
// method has it).  It is what keeps a beaten crossing where it was beaten.
//
// The working window is settled by FIRE, as rope.js is, with rope.js's own
// mechanics (its yarnMechanics: stretching, bending, contact and FIRE's
// steps), so the two cannot drift apart.  The friction springs are kept
// between steps and between rows, so it remembers.
//
// Lengths are in yarn diameters.  docs/source/rope_physics.md describes
// how a braid is made this way; tests/test_rope.py checks that the braid
// made is the braid laid (the same linking numbers).
//
// References:
// - Friction as a tangential spring, capped by Coulomb's law: P. A.
//   Cundall and O. D. L. Strack, "A discrete numerical model for granular
//   assemblies", Géotechnique 29, 47 (1979),
//   https://doi.org/10.1680/geot.1979.29.1.47; a free-to-read review in
//   docs/source/rope_physics.md.
// - FIRE, and the contact geometry: see rope.js.

(function (root) {
  "use strict";

  const { relay, nearPairs, stale, touching, spread, stretchAndBend, fireSums, fireMix, steer, moveBeads } =
    root.yarnMechanics || require("./rope.js?v=50fb1afccf").yarnMechanics;

  /**
   * @param {Object} job
   * @param {number[][]} job.yarns  Each yarn's points, x y z after x y z,
   *     its oldest end first, rising: the braid as laid.
   * @param {number} job.row  Height of a row as laid.
   * @param {number} [job.friction]  mu; 0 for none.
   * @param {number} [job.feed]  T, each yarn's tension.
   * @param {number} [job.weight]  W, drawing the braid off, all yarns
   *     together.
   * @param {function(Object):void} [job.progress]
   * @returns {Object} The yarns as made, and how it went.
   */
  function form(job) {
    const spacing = 0.5;
    const ks = job.stretch ?? 100;
    const kb = job.bend ?? 0.5;
    const kc = job.contact ?? 100;
    const kr = job.soft ?? 5;
    const core = 1 - (job.shell ?? 0.1);
    const mu = job.friction ?? 0.3;
    const kt = job.grip ?? 20;
    const feed = job.feed ?? 1;
    const nYarns = job.yarns.length;
    const weight = job.weight ?? 0.25 * nYarns;
    const row = job.row;
    const keep = job.keep ?? 2;
    const window = job.window ?? 2;
    const stepsPerRow = job.stepsPerRow ?? 4000;
    const tolerance = job.tolerance ?? 2e-3;

    // Each yarn: made beads (fixed), working beads, and beads to come, these
    // at their laid place lifted (or lowered) by the block's offset.
    let nextId = 0;
    const yarns = job.yarns.map((points) => {
      const all = relay(Float64Array.from(points), spacing);
      const beads = [];
      for (let i = 0; i < all.length; i += 3) beads.push({ p: [all[i], all[i + 1], all[i + 2]], id: nextId++ });
      return { made: beads.slice(0, 1), working: [], toCome: beads.slice(1) };
    });
    let offset = 0; // the block's
    const top = Math.max(...yarns.map((y) => y.toCome[y.toCome.length - 1].p[2]));
    // Friction springs, by pair of beads: their tangential stretch.
    const grips = new Map();
    let stage = 0;
    let deepestEver = 0;
    let steps = 0;

    for (let cut = window * row; ; cut += row) {
      // The next rows join the window, where they are now.
      for (const y of yarns) {
        while (y.toCome.length > 1 && y.toCome[0].p[2] <= cut) {
          const b = y.toCome.shift();
          y.working.push({ p: [b.p[0], b.p[1], b.p[2] + offset], id: b.id });
        }
      }
      const last = yarns.every((y) => y.toCome.length <= 1);
      steps += settleWindow(last ? stepsPerRow * 3 : stepsPerRow, last);
      stage++;
      if (job.progress) job.progress({ stage, fraction: Math.min(1, cut / top), yarns: snapshot(), offset });
      if (last) break;
      // Freeze all but the top of the window.
      let high = -Infinity;
      for (const y of yarns) for (const b of y.working) high = Math.max(high, b.p[2]);
      for (const y of yarns) {
        while (y.working.length > 2 && y.working[0].p[2] < high - keep) y.made.push(y.working.shift());
      }
    }

    return { yarns: snapshot(), offset, steps, deepestEver, stages: stage };

    function snapshot() {
      return yarns.map((y) => {
        const out = [];
        for (const b of y.made) out.push(...b.p);
        for (const b of y.working) out.push(...b.p);
        for (const b of y.toCome) out.push(b.p[0], b.p[1], b.p[2] + offset);
        return out;
      });
    }

    // FIRE on the window, with the block and each yarn's rest length.
    function settleWindow(maxSteps, last) {
      let relays = 0;
      for (;;) {
        const outcome = run();
        if (outcome.done) return outcome.steps;
        if (++relays > 50) return outcome.steps;
        // Lay out again the working beads of yarns whose links have grown
        // too long or too short, from the made braid to the block.
        for (const a of outcome.relay) relayWorking(yarns[a]);
      }

      function run() {
        // Flat arrays: working beads, then the obstacles near them: made
        // beads just below, beads to come just above.
        let low = Infinity, high = -Infinity;
        for (const y of yarns) for (const b of y.working) { low = Math.min(low, b.p[2]); high = Math.max(high, b.p[2]); }
        const chains = []; // per yarn: [index of first bead, count, kind]
        const xs = [];
        const ids = [];
        const kinds = []; // 0 made, 1 working, 2 to come
        const ofYarn = [];
        const restOf = [];
        yarns.forEach((y, a) => {
          // A chain per yarn: the last made beads (near), the working beads,
          // the first beads to come (near).
          const from = xs.length / 3;
          let firstMade = y.made.length - 1;
          while (firstMade > 0 && y.made[firstMade - 1].p[2] > low - 2) firstMade--;
          for (let i = firstMade; i < y.made.length; i++) push(y.made[i].p, y.made[i].id, 0, a);
          for (const b of y.working) push(b.p, b.id, 1, a);
          let lastToCome = 0;
          while (lastToCome < y.toCome.length - 1 && y.toCome[lastToCome + 1].p[2] + offset < high + 2) lastToCome++;
          for (let i = 0; i <= Math.min(lastToCome, y.toCome.length - 1); i++) {
            const b = y.toCome[i];
            push([b.p[0], b.p[1], b.p[2] + offset], b.id, 2, a);
          }
          chains.push([from, xs.length / 3 - from, y.made.length - firstMade]);
          restOf.push(y.rest ?? spacing);
        });
        function push(p, id, kind, a) {
          xs.push(p[0], p[1], p[2]);
          ids.push(id);
          kinds.push(kind);
          ofYarn.push(a);
        }
        const n = ids.length;
        if (job.debug) job.debug({ stage, n, working: kinds.filter((k) => k === 1).length, made: kinds.filter((k) => k === 0).length, toCome: kinds.filter((k) => k === 2).length, low, high, offset });
        const x = Float64Array.from(xs);
        const kind = Uint8Array.from(kinds);
        const yarnOf = Int32Array.from(ofYarn);
        const s = Float64Array.from(restOf);
        // Working links of each yarn: from its last made bead to its first
        // bead to come.
        const linkFrom = new Int32Array(nYarns);
        const linkTo = new Int32Array(nYarns);
        chains.forEach(([from, count, made], a) => {
          linkFrom[a] = from + made - 1;
          linkTo[a] = from + made + yarns[a].working.length; // first to come
          if (linkTo[a] >= from + count) linkTo[a] = from + count - 1;
        });
        const links = new Float64Array(nYarns);
        for (let a = 0; a < nYarns; a++) links[a] = Math.max(1, linkTo[a] - linkFrom[a]);
        const base = x.slice(); // the block's beads, before it moves
        let block = 0; // the block's move this run

        // Segments: consecutive beads of a chain.
        const segs = [];
        chains.forEach(([from, count]) => {
          for (let i = from; i < from + count - 1; i++) segs.push(i);
        });
        const gap = Math.ceil(2 / spacing) + 1;
        const reach = 1 + 2 * spacing + 0.5;
        let pairs = new Int32Array(0);
        const built = new Float64Array(3 * n);
        const cells = new Int32Array(3 * n);
        // Something in a pair must be able to move: a working bead, or the
        // block against the made braid.
        const movable = (g, h) =>
          kind[g] === 1 || kind[g + 1] === 1 || kind[h] === 1 || kind[h + 1] === 1 ||
          ((kind[g] === 2 || kind[h] === 2) && kind[g] !== kind[h]);
        function neighbours() {
          pairs = nearPairs(x, segs, yarnOf, gap, reach, cells, movable);
          built.set(x);
        }

        const f = new Float64Array(3 * n);
        const fs = new Float64Array(nYarns);
        let blockForce = 0;
        const v = new Float64Array(3 * n);
        const vs = new Float64Array(nYarns);
        let vBlock = 0;
        const touched = new Set();
        let deepest = 0;
        function forces(dt) {
          f.fill(0);
          fs.fill(0);
          for (let a = 0; a < nYarns; a++) {
            const strain = stretchAndBend(x, f, linkFrom[a], linkTo[a], s[a], ks, kb);
            fs[a] = ks * strain - feed * links[a];
          }
          deepest = 0;
          touched.clear();
          stepDt = dt;
          touching(x, pairs, touch);
          // Contacts that came apart let go of their springs.
          for (const key of keysHere) if (!touched.has(key)) grips.delete(key);
          // The block: the weight, and what the window does to its beads.
          blockForce = weight;
          for (let g = 0; g < n; g++) if (kind[g] === 2) blockForce += f[3 * g + 2];
          if (last) blockForce = weight + Math.min(0, blockForce - weight);
        }
        // A contact: the cores' and soft surfaces' push along the line
        // between the closest points, and friction across it.
        let stepDt = 0;
        function touch(e, u, w, px, py, pz, r2) {
          const g = pairs[e], h = pairs[e + 1];
          const i = 3 * g, j = 3 * h;
          const key = ids[g] * 4194304 + ids[h];
          const r = Math.sqrt(r2);
          let push = kr * (1 - r);
          if (r < core) {
            deepest = Math.max(deepest, core - r);
            push += kc * (core - r);
          }
          const nx = px / Math.max(r, 1e-9), ny = py / Math.max(r, 1e-9), nz = pz / Math.max(r, 1e-9);
          let qx = push * nx, qy = push * ny, qz = push * nz;
          if (mu > 0) {
            // Friction: the tangential spring, stretched by how the
            // contact points slid past each other this step.
            touched.add(key);
            let spring = grips.get(key);
            if (!spring) grips.set(key, (spring = [0, 0, 0]));
            const vx = (1 - u) * v[i] + u * v[i + 3] - (1 - w) * v[j] - w * v[j + 3];
            const vy = (1 - u) * v[i + 1] + u * v[i + 4] - (1 - w) * v[j + 1] - w * v[j + 4];
            const vz = (1 - u) * v[i + 2] + u * v[i + 5] - (1 - w) * v[j + 2] - w * v[j + 5];
            spring[0] += vx * stepDt;
            spring[1] += vy * stepDt;
            spring[2] += vz * stepDt;
            // Kept in the contact's tangent plane.
            const along = spring[0] * nx + spring[1] * ny + spring[2] * nz;
            spring[0] -= along * nx;
            spring[1] -= along * ny;
            spring[2] -= along * nz;
            let tx = -kt * spring[0], ty = -kt * spring[1], tz = -kt * spring[2];
            const size = Math.hypot(tx, ty, tz);
            const most = mu * push;
            if (size > most) {
              // Slipping: the spring gives way to what friction holds.
              const k = most / size;
              tx *= k;
              ty *= k;
              tz *= k;
              spring[0] *= k;
              spring[1] *= k;
              spring[2] *= k;
            }
            qx += tx;
            qy += ty;
            qz += tz;
          }
          spread(f, i, j, u, w, qx, qy, qz);
        }
        // The pairs this window can see: springs of other pairs are kept.
        let keysHere = new Set();

        let dt = 0.01, alpha = 0.1, downhill = 0, step = 0, largest = Infinity;
        const working = kind.map((k) => (k === 1 ? 1 : 0));
        const sums = new Float64Array(4);
        neighbours();
        keysHere = new Set();
        for (let e = 0; e < pairs.length; e += 2) keysHere.add(ids[pairs[e]] * 4194304 + ids[pairs[e + 1]]);
        for (; step < maxSteps; step++) {
          if (stale(x, built)) {
            neighbours();
            keysHere = new Set();
            for (let e = 0; e < pairs.length; e += 2) keysHere.add(ids[pairs[e]] * 4194304 + ids[pairs[e + 1]]);
          }
          forces(dt);
          deepestEver = Math.max(deepestEver, deepest);
          sums[0] = blockForce * vBlock;
          sums[1] = blockForce * blockForce;
          sums[2] = vBlock * vBlock;
          sums[3] = Math.abs(blockForce) / nYarns;
          fireSums(f, v, working, fs, vs, links, sums);
          largest = sums[3];
          if (largest < tolerance) break;
          const mix = fireMix(sums, alpha);
          steer(v, f, working, vs, fs, alpha, mix);
          vBlock = (1 - alpha) * vBlock + mix * blockForce;
          if (sums[0] > 0) {
            if (++downhill > 5) {
              dt = Math.min(dt * 1.1, 0.05);
              alpha *= 0.99;
            }
          } else {
            downhill = 0;
            dt *= 0.5;
            alpha = 0.1;
            v.fill(0);
            vs.fill(0);
            vBlock = 0;
          }
          moveBeads(x, v, f, dt, working);
          // The block moves as one, its beads' velocity its own, for the
          // friction they feel.
          vBlock += (dt * blockForce) / nYarns;
          const by = Math.max(-0.1, Math.min(0.1, dt * vBlock));
          block += by;
          for (let g = 0; g < n; g++) {
            if (kind[g] !== 2) continue;
            x[3 * g + 2] = base[3 * g + 2] + block;
            v[3 * g] = v[3 * g + 1] = 0;
            v[3 * g + 2] = vBlock;
          }
          let relayNeeded = [];
          for (let a = 0; a < nYarns; a++) {
            vs[a] += (dt * fs[a]) / links[a];
            s[a] += Math.max(-0.01, Math.min(0.01, dt * vs[a]));
            if (s[a] > 1.5 * spacing || s[a] < 0.6 * spacing) relayNeeded.push(a);
          }
          if (relayNeeded.length) {
            keepState();
            return { done: false, relay: relayNeeded, steps: step + 1 };
          }
        }
        keepState();
        return { done: true, steps: step };

        function keepState() {
          offset += block;
          yarns.forEach((y, a) => {
            const [from, , made] = chains[a];
            y.working.forEach((b, k) => {
              const g = from + made + k;
              b.p = [x[3 * g], x[3 * g + 1], x[3 * g + 2]];
            });
            y.rest = s[a];
          });
        }
      }
    }

    // A yarn's working beads laid out again, evenly, from its last made bead
    // to its first bead to come; new beads get new names, and lose their
    // friction springs.
    function relayWorking(y) {
      const first = y.made[y.made.length - 1].p;
      const next = y.toCome[0];
      const end = [next.p[0], next.p[1], next.p[2] + offset];
      const points = [...first, ...y.working.flatMap((b) => b.p), ...end];
      const out = relay(Float64Array.from(points), spacing);
      y.working = [];
      for (let i = 3; i < out.length - 3; i += 3) y.working.push({ p: [out[i], out[i + 1], out[i + 2]], id: nextId++ });
      y.rest = spacing;
    }
  }

  root.formBraid = form;
  if (typeof module !== "undefined" && module.exports) module.exports = { form };
})(typeof self !== "undefined" ? self : globalThis);
