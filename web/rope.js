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
// Lengths are in yarn diameters.  docs/source/rope_physics.md describes the
// model and what it gives; tests/test_rope.py checks it against physics and
// against braidpy (the braid laid is the braid settled: same word, same
// linking numbers).
//
// References:
// - FIRE: E. Bitzek, P. Koskinen, F. Gähler, M. Moseler, P. Gumbsch,
//   "Structural relaxation made simple", Phys. Rev. Lett. 97, 170201 (2006).
// - Closest points of two segments: C. Ericson, Real-Time Collision
//   Detection (Morgan Kaufmann, 2005), §5.1.9.
// - The grid of cells, hashed with three large primes: M. Teschner, B.
//   Heidelberger, M. Müller, D. Pomeranets, M. Gross, "Optimized spatial
//   hashing for collision detection of deformable objects", Vision,
//   Modeling, and Visualization (2003).
// - Linking numbers, how the tests know no yarn passed through another: a
//   yarn passing through another changes them (braidpy.linking).

(function (root) {
  "use strict";

  // ------------------------------------------------------------------
  // What rope.js and form.js both do to yarns of beads, in flat arrays:
  // x the beads' places, x y z after x y z; segment g joins beads g and
  // g + 1, and its offset in x is 3 g.

  // Pairs of segments near enough to touch before the beads move a quarter
  // diameter, found on a grid of cells ``reach`` wide: of ``segs``, neither
  // two segments of a yarn closer than ``gap`` along it, nor a pair
  // ``accept`` turns down.  ``cells`` holds three numbers a bead.
  //
  // Each segment is put in the cell of its midpoint, the cells kept in a
  // hash table by three large primes (Teschner et al., 2003), and compared
  // with the segments of its own and the 26 neighbouring cells.  A pair is
  // kept if its midpoints are within 2 reach: two segments a link long whose
  // surfaces could touch have midpoints within a diameter and a link, and
  // the margin left is what beads may move before the list is rebuilt
  // (``stale``).
  function nearPairs(x, segs, yarnOf, gap, reach, cells, accept) {
    const grid = new Map();
    for (let e = 0; e < segs.length; e++) {
      const g = segs[e];
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
    for (let e = 0; e < segs.length; e++) {
      const g = segs[e];
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
              // Near enough to touch before the list is rebuilt.
              const mx = x[3 * g] + x[3 * g + 3] - x[3 * h] - x[3 * h + 3];
              const my = x[3 * g + 1] + x[3 * g + 4] - x[3 * h + 1] - x[3 * h + 4];
              const mz = x[3 * g + 2] + x[3 * g + 5] - x[3 * h + 2] - x[3 * h + 5];
              if (mx * mx + my * my + mz * mz > 4 * reach * reach) continue;
              if (accept && !accept(g, h)) continue;
              found.push(g, h);
            }
          }
        }
      }
    }
    return Int32Array.from(found);
  }

  // Whether a bead has moved a quarter diameter since ``built``: the pairs
  // near enough to touch want finding again.
  function stale(x, built) {
    for (let k = 0; k < x.length; k += 3) {
      const dx = x[k] - built[k], dy = x[k + 1] - built[k + 1], dz = x[k + 2] - built[k + 2];
      if (dx * dx + dy * dy + dz * dz > 0.0625) return true;
    }
    return false;
  }

  // Each pair of segments, at offsets i and j of x, whose closest points
  // are less than a diameter apart: ``touch(e, u, w, px, py, pz, r2)`` with
  // the pair's place in ``pairs``, how far along each segment the points
  // are, the vector between them, from the second to the first, and its
  // length squared.
  //
  // The closest points (Ericson, 2005, §5.1.9): those of the two infinite
  // lines, u along the first clamped to the segment; then w along the
  // second, nearest that point, and if it falls off the second segment, w
  // clamped and u found again nearest it.  Parallel segments (den near 0)
  // take u = 0.
  function touching(x, pairs, touch) {
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
      if (r2 < 1) touch(e, u, w, px, py, pz, r2);
    }
  }

  // A force q between the segments at offsets i and j, at u and w along
  // them: onto the first, and its opposite onto the second, shared between
  // each one's two beads.
  function spread(f, i, j, u, w, qx, qy, qz) {
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

  // A yarn's beads ``from`` to ``to`` stretching, links of rest length s0,
  // and bending, onto f: k_s (r - s0)² / 2 a link, and k_b / s0² |curve|² / 2
  // a bead between two others.  Returns the links' stretch, all told.
  function stretchAndBend(x, f, from, to, s0, ks, kb) {
    let strain = 0;
    for (let g = from; g < to; g++) {
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
    const b = kb / (s0 * s0);
    for (let g = from + 1; g < to; g++) {
      for (let c = 0; c < 3; c++) {
        const curve = x[3 * g - 3 + c] - 2 * x[3 * g + c] + x[3 * g + 3 + c];
        f[3 * g - 3 + c] -= b * curve;
        f[3 * g + c] += 2 * b * curve;
        f[3 * g + 3 + c] -= b * curve;
      }
    }
    return strain;
  }

  // FIRE's sums, added to ``sums`` as the power f · v, |f|², |v|² and the
  // largest force: over each yarn's rest length — f ``fs``, v ``vs``,
  // weighed per link — then over the beads that move.
  //
  // FIRE (Bitzek et al., 2006) is damped dynamics: each step it turns the
  // velocity towards the force by a fraction alpha (``steer``), and while
  // the power f · v stays positive — going downhill — it lengthens the time
  // step and lessens alpha; once it goes uphill it stops everything dead,
  // halves the step and starts again.  These sums are what it decides by.
  function fireSums(f, v, moves, fs, vs, links, sums) {
    let power = sums[0], fNorm = sums[1], vNorm = sums[2], largest = sums[3];
    for (let a = 0; a < fs.length; a++) {
      // Per link, so a yarn's rest length is weighed like a bead.
      largest = Math.max(largest, Math.abs(fs[a] / links[a]));
      power += fs[a] * vs[a];
      fNorm += fs[a] * fs[a];
      vNorm += vs[a] * vs[a];
    }
    for (let g = 0; g < moves.length; g++) {
      if (!moves[g]) continue;
      for (let c = 0; c < 3; c++) {
        const k = 3 * g + c;
        power += f[k] * v[k];
        fNorm += f[k] * f[k];
        vNorm += v[k] * v[k];
        if (Math.abs(f[k]) > largest) largest = Math.abs(f[k]);
      }
    }
    sums[0] = power;
    sums[1] = fNorm;
    sums[2] = vNorm;
    sums[3] = largest;
  }

  // How much of the force FIRE mixes into the velocity, from its sums.
  function fireMix(sums, alpha) {
    const fNorm = Math.sqrt(sums[1]);
    const vNorm = Math.sqrt(sums[2]);
    return fNorm > 0 ? (alpha * vNorm) / fNorm : 0;
  }

  // FIRE's turn of the velocity towards the force: the beads' that move,
  // and the rest lengths'.
  function steer(v, f, moves, vs, fs, alpha, mix) {
    for (let g = 0; g < moves.length; g++) {
      if (!moves[g]) continue;
      for (let c = 0; c < 3; c++) v[3 * g + c] = (1 - alpha) * v[3 * g + c] + mix * f[3 * g + c];
    }
    for (let a = 0; a < vs.length; a++) vs[a] = (1 - alpha) * vs[a] + mix * fs[a];
  }

  // Semi-implicit Euler, no bead moving more than a tenth of a diameter in
  // a step, so none can pass through another.
  function moveBeads(x, v, f, dt, moves) {
    for (let g = 0; g < moves.length; g++) {
      if (!moves[g]) continue;
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
  }

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
      const segs = Int32Array.from({ length: n }, (_, g) => g).filter((g) => !isTop[g]);
      function neighbours() {
        pairs = nearPairs(x, segs, yarnOf, gap, reach, cells);
        built.set(x);
      }

      // The energy's gradient: f holds the forces, minus the gradient, and
      // fs the forces on the links' rest lengths, for fed yarns.
      const f = new Float64Array(3 * n);
      const fs = new Float64Array(nYarns);
      function forces() {
        f.fill(0);
        fs.fill(0);
        for (let a = 0; a < nYarns; a++) {
          const strain = stretchAndBend(x, f, first[a], first[a + 1] - 1, s[a], ks, kb);
          if (feed !== null) fs[a] = ks * strain - feed * links[a];
        }
        contacts = 0;
        deepest = 0;
        touching(x, pairs, touch);
      }
      function touch(e, u, w, px, py, pz, r2) {
        const r = Math.sqrt(r2);
        let push = (kr * (1 - r)) / Math.max(r, 1e-9);
        if (r < core) {
          contacts++;
          if (core - r > deepest) deepest = core - r;
          if (core - r > deepestEver) deepestEver = core - r;
          push += (kc * (core - r)) / Math.max(r, 1e-9);
        }
        spread(f, 3 * pairs[e], 3 * pairs[e + 1], u, w, push * px, push * py, push * pz);
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
      const sums = new Float64Array(4);
      placeTops();
      neighbours();
      for (; step < steps; step++) {
        // Every step: two beads moving a tenth of a diameter each, apart,
        // would otherwise close the list's margin unseen.
        if (stale(x, built)) neighbours();
        forces();
        let up = force;
        let torque = 0;
        for (let a = 0; a < nYarns; a++) {
          const g = tops[a];
          up += f[3 * g + 2];
          torque += x[3 * g] * f[3 * g + 1] - x[3 * g + 1] * f[3 * g];
        }
        if (!turns) torque = 0;
        sums[0] = up * vRise + torque * vTurn;
        sums[1] = up * up + torque * torque;
        sums[2] = vRise * vRise + vTurn * vTurn;
        sums[3] = Math.max(Math.abs(up), Math.abs(torque));
        fireSums(f, v, free, fs, vs, links, sums);
        largest = sums[3];
        if (step % 500 === 0 && job.progress) {
          job.progress({ step, largestForce: largest, yarns: snapshot(), rise, turn, dt, restarts, spacing: Array.from(s) });
        }
        if (largest < tolerance) {
          keep();
          return "settled";
        }
        const mix = fireMix(sums, alpha);
        steer(v, f, free, vs, fs, alpha, mix);
        vRise = (1 - alpha) * vRise + mix * up;
        vTurn = (1 - alpha) * vTurn + mix * torque;
        if (sums[0] > 0) {
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
        moveBeads(x, v, f, dt, free);
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

  // What form.js shares.
  const yarnMechanics = { relay, nearPairs, stale, touching, spread, stretchAndBend, fireSums, fireMix, steer, moveBeads };
  root.settleRope = settle;
  root.yarnMechanics = yarnMechanics;
  if (typeof module !== "undefined" && module.exports) module.exports = { settle, relay, yarnMechanics };
})(typeof self !== "undefined" ? self : globalThis);
