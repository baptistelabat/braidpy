// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Making a disk braid, move by move, in three dimensions.
//
// tighten.js pulls laid yarns taut sideways, each sample keeping its height:
// the braid keeps the pitch it was laid with, and a braid laid loose stays
// loose and round.  A real braid is beaten up as it is made: each crossing
// is pulled down against the ones before until they jam, and the pitch and
// the shape of the cross-section — round, square, triangular — are what
// jamming leaves.  So here the braid is made, as on a marudai:
//
// - the yarns lie on a mirror, a disk with a hole in the middle, each from
//   the hole out to its carrier on the rim, and hang through the hole into
//   the braid, which a weight draws down;
// - a move carries one carrier round the rim, its yarn lifted over the yarns
//   it passes — the rule braidpy's disk_crossing_steps reads crossings by —
//   and puts it down;
// - each yarn is a chain of beads, pulled straight by its tension: the chains
//   are resampled as they go, so yarn slides freely through the crossings
//   and out to the carriers, as it does through a real braid;
// - no two yarns come closer than a diameter, tested segment against
//   segment, so no yarn passes through another and the braid is the braid
//   the moves make;
// - well below the hole the braid is made: its beads stop moving, and go
//   down with the weight, as one.
//
// The method is the usual one for ropes in position-based dynamics: moves
// projected out of collisions, segment against segment.
//
// Loaded as a classic script by the worker (importScripts) and required by
// Node for the tests.

(function (root) {
  "use strict";

  // Lengths in yarn diameters, until the very end.
  const SPACING = 0.5; // between beads
  const SLACK = 2e-3; // overlap let pass
  const MOVE = 0.1; // the most a bead moves at once
  const LIFT = 1.6; // a moving yarn rides this high over the others
  const DEPTH = 7; // below the mirror, the braid is made
  const KEEP = 3; // made beads still touched, below that
  const RAISE = 3; // a moving yarn's carrier is raised this high
  const FELL = -1; // the braid is drawn down to keep its fell here

  // Solve (I + h L) x = b in place in values[0..n), L the second difference
  // along a chain whose two ends are held: the Thomas algorithm.
  function settleChain(values, n, h, c, m) {
    m[0] = 1;
    c[0] = 0;
    for (let i = 1; i < n; i++) {
      const inner = i < n - 1;
      const lower = inner ? -h : 0;
      m[i] = (inner ? 1 + 2 * h : 1) - lower * c[i - 1];
      c[i] = (inner ? -h : 0) / m[i];
      values[i] = (values[i] - lower * values[i - 1]) / m[i];
    }
    for (let i = n - 2; i >= 0; i--) values[i] -= c[i] * values[i + 1];
  }

  /**
   * Make a disk braid.
   *
   * @param {Object} job
   * @param {number} job.n_slots  Slots round the disk.
   * @param {number[]} job.start  Each yarn's slot, from 1.
   * @param {number[][][]} job.steps  Per step, [yarn, slots moved] for each
   *     yarn that moves.
   * @param {boolean} job.clockwise  Whether slots are numbered clockwise,
   *     seen from above.
   * @param {number} job.yarn_diameter
   * @param {number} [job.weight]  The braid's weight against the yarns'
   *     pull, per yarn: the lighter, the tighter the braid is beaten up.
   * @param {function(number):void} [progress]
   * @returns {{points: number[][][], times: number[][], closest: number}}
   *     Each yarn as made, from its start up to the fell, drawn growing up
   *     from the fell at height 0; and when each point was made, in steps.
   */
  function formBraid(job, progress) {
    const nYarns = job.start.length;
    const nSlots = job.n_slots;
    const sense = job.clockwise ? -1 : 1;
    const weight = job.weight === undefined ? 0.3 : job.weight;
    const rim = 7 + nYarns / 4;
    const hole = rim / 2;
    // Near enough the axis to be in the braid, or about to be.
    const braidRadius = 1.5 + 0.35 * Math.sqrt(nYarns);
    const angleOf = (slot) => (sense * 2 * Math.PI * (slot - 1)) / nSlots;

    // Carriers: where each yarn is pulled to.  A carrier on the move is
    // raised in over the hole and taken round there, above where the yarns
    // meet, so its yarn passes over those it sweeps, not round them.
    const angle = job.start.map(angleOf);
    const radius = job.start.map(() => rim);
    const raised = new Float64Array(nYarns);
    const lifted = new Uint8Array(nYarns);
    const carrier = (a) => [
      radius[a] * Math.cos(angle[a]),
      radius[a] * Math.sin(angle[a]),
      0.5 + raised[a],
    ];

    function line(corners) {
      const out = [];
      for (let k = 0; k + 1 < corners.length; k++) {
        const [a, b] = [corners[k], corners[k + 1]];
        const steps = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]) / SPACING));
        for (let i = k ? 1 : 0; i <= steps; i++) {
          const f = i / steps;
          out.push([a[0] + f * (b[0] - a[0]), a[1] + f * (b[1] - a[1]), a[2] + f * (b[2] - a[2])]);
        }
      }
      return out;
    }

    // Each yarn, made beads first: from where the braid starts, a ring
    // below the hole, up through it and out to its carrier.
    const yarns = [];
    const ring = Math.max(0.6, (0.6 * nYarns) / (2 * Math.PI));
    for (let a = 0; a < nYarns; a++) {
      const t = angle[a];
      const from = [ring * Math.cos(t), ring * Math.sin(t), -DEPTH - KEEP - 1];
      const via = [ring * Math.cos(t), ring * Math.sin(t), 0];
      yarns.push({ made: [from], madeAt: [0], active: line([from, via, carrier(a)]).slice(1) });
    }

    // The working arrays: every active bead, after the last few made beads
    // of its yarn, which active ones may still touch.
    const keep = Math.ceil(KEEP / SPACING) + 1;
    let p = new Float64Array(0);
    let mobile = new Uint8Array(0);
    let yarnOf = new Int32Array(0);
    let first = new Int32Array(nYarns + 1);
    let kept = new Int32Array(nYarns);
    function gather() {
      let total = 0;
      for (const y of yarns) total += Math.min(y.made.length, keep) + y.active.length;
      p = new Float64Array(3 * total);
      mobile = new Uint8Array(total);
      yarnOf = new Int32Array(total);
      first = new Int32Array(nYarns + 1);
      kept = new Int32Array(nYarns);
      let g = 0;
      yarns.forEach((y, a) => {
        first[a] = g;
        kept[a] = Math.min(y.made.length, keep);
        for (let i = y.made.length - kept[a]; i < y.made.length; i++) put(g++, y.made[i], 0, a);
        y.active.forEach((point, i) => put(g++, point, i < y.active.length - 1 ? 1 : 0, a));
      });
      first[nYarns] = g;
    }
    function put(g, point, free, a) {
      p[3 * g] = point[0];
      p[3 * g + 1] = point[1];
      p[3 * g + 2] = point[2];
      mobile[g] = free;
      yarnOf[g] = a;
    }
    function scatter() {
      yarns.forEach((y, a) => {
        const k = kept[a];
        for (let i = 0; i < k; i++) {
          const g = first[a] + i;
          y.made[y.made.length - k + i] = [p[3 * g], p[3 * g + 1], p[3 * g + 2]];
        }
        const base = first[a] + k;
        y.active = y.active.map((_, i) => [p[3 * (base + i)], p[3 * (base + i) + 1], p[3 * (base + i) + 2]]);
      });
    }

    // The active part of each yarn again, evenly spaced from its last made
    // bead to its carrier; beads gone deep enough are made.
    function resample(now) {
      scatter();
      yarns.forEach((y, a) => {
        const chain = [y.made[y.made.length - 1], ...y.active];
        chain[chain.length - 1] = carrier(a);
        const cumulative = [0];
        for (let i = 1; i < chain.length; i++) {
          const [u, v] = [chain[i - 1], chain[i]];
          cumulative.push(cumulative[i - 1] + Math.hypot(v[0] - u[0], v[1] - u[1], v[2] - u[2]));
        }
        const total = cumulative[cumulative.length - 1];
        const beads = Math.max(2, Math.round(total / SPACING));
        const out = [];
        let j = 0;
        for (let b = 1; b <= beads; b++) {
          const along = (total * b) / beads;
          while (j < chain.length - 2 && cumulative[j + 1] < along) j++;
          const span = cumulative[j + 1] - cumulative[j];
          const f = span > 0 ? Math.min(1, (along - cumulative[j]) / span) : 0;
          const [u, v] = [chain[j], chain[j + 1]];
          out.push([u[0] + f * (v[0] - u[0]), u[1] + f * (v[1] - u[1]), u[2] + f * (v[2] - u[2])]);
        }
        // Made, from the bottom up, while deep enough.
        let m = 0;
        while (m < out.length - 2 && out[m][2] < -DEPTH) {
          y.made.push(out[m]);
          y.madeAt.push(now);
          m++;
        }
        y.active = out.slice(m);
      });
      gather();
    }

    // Pairs of segments near enough to touch before the list is rebuilt.
    const margin = 0.5;
    let pairs = new Int32Array(0);
    let built = new Float64Array(0);
    function neighbours() {
      let longest = 0;
      for (let a = 0; a < nYarns; a++) {
        for (let g = first[a]; g < first[a + 1] - 1; g++) {
          longest = Math.max(
            longest,
            Math.hypot(p[3 * g + 3] - p[3 * g], p[3 * g + 4] - p[3 * g + 1], p[3 * g + 5] - p[3 * g + 2]),
          );
        }
      }
      const reach = 1 + longest + margin;
      const grid = new Map();
      const key = (x, y, z) => (x * 73856093) ^ (y * 19349663) ^ (z * 83492791);
      const cells = new Int32Array(3 * first[nYarns]);
      for (let a = 0; a < nYarns; a++) {
        for (let g = first[a]; g < first[a + 1] - 1; g++) {
          const x = Math.floor((p[3 * g] + p[3 * g + 3]) / 2 / reach);
          const y = Math.floor((p[3 * g + 1] + p[3 * g + 4]) / 2 / reach);
          const z = Math.floor((p[3 * g + 2] + p[3 * g + 5]) / 2 / reach);
          cells[3 * g] = x;
          cells[3 * g + 1] = y;
          cells[3 * g + 2] = z;
          const h = key(x, y, z);
          let list = grid.get(h);
          if (!list) grid.set(h, (list = []));
          list.push(g);
        }
      }
      const found = [];
      const gap = Math.ceil(1.5 / SPACING) + 1;
      for (let a = 0; a < nYarns; a++) {
        for (let s = first[a]; s < first[a + 1] - 1; s++) {
          const x = cells[3 * s], y = cells[3 * s + 1], z = cells[3 * s + 2];
          for (let ox = -1; ox <= 1; ox++) {
            for (let oy = -1; oy <= 1; oy++) {
              for (let oz = -1; oz <= 1; oz++) {
                const list = grid.get(key(x + ox, y + oy, z + oz));
                if (!list) continue;
                for (const t of list) {
                  if (t <= s) continue;
                  if (cells[3 * t] !== x + ox || cells[3 * t + 1] !== y + oy || cells[3 * t + 2] !== z + oz) continue;
                  if (yarnOf[t] === a && t - s < gap) continue;
                  if (!mobile[s] && !mobile[s + 1] && !mobile[t] && !mobile[t + 1]) continue;
                  const dx = p[3 * s] + p[3 * s + 3] - p[3 * t] - p[3 * t + 3];
                  const dy = p[3 * s + 1] + p[3 * s + 4] - p[3 * t + 1] - p[3 * t + 4];
                  const dz = p[3 * s + 2] + p[3 * s + 5] - p[3 * t + 2] - p[3 * t + 5];
                  if (dx * dx + dy * dy + dz * dz < 4 * reach * reach) found.push(s, t);
                }
              }
            }
          }
        }
      }
      pairs = Int32Array.from(found);
      built = Float64Array.from(p);
    }

    function stale() {
      if (built.length !== p.length) return true;
      for (let k = 0; k < p.length; k += 3) {
        if (Math.hypot(p[k] - built[k], p[k + 1] - built[k + 1], p[k + 2] - built[k + 2]) > margin / 3) {
          return true;
        }
      }
      return false;
    }

    // The closest points of segments s and t, as fractions along each, in
    // st[0..1]; and how far apart they are.
    const st = new Float64Array(2);
    function closest(s, t) {
      const i = 3 * s, j = 3 * t;
      const ax = p[i + 3] - p[i], ay = p[i + 4] - p[i + 1], az = p[i + 5] - p[i + 2];
      const bx = p[j + 3] - p[j], by = p[j + 4] - p[j + 1], bz = p[j + 5] - p[j + 2];
      const rx = p[i] - p[j], ry = p[i + 1] - p[j + 1], rz = p[i + 2] - p[j + 2];
      const aa = ax * ax + ay * ay + az * az;
      const bb = bx * bx + by * by + bz * bz;
      const ab = ax * bx + ay * by + az * bz;
      const ar = ax * rx + ay * ry + az * rz;
      const br = bx * rx + by * ry + bz * rz;
      const den = aa * bb - ab * ab;
      let u = den > 1e-12 * aa * bb ? (ab * br - ar * bb) / den : 0;
      u = Math.min(1, Math.max(0, u));
      let v = bb > 0 ? (ab * u + br) / bb : 0;
      if (v < 0) {
        v = 0;
        u = aa > 0 ? Math.min(1, Math.max(0, -ar / aa)) : 0;
      } else if (v > 1) {
        v = 1;
        u = aa > 0 ? Math.min(1, Math.max(0, (ab - ar) / aa)) : 0;
      }
      st[0] = u;
      st[1] = v;
      const ux = rx + u * ax - v * bx, uy = ry + u * ay - v * by, uz = rz + u * az - v * bz;
      return Math.sqrt(ux * ux + uy * uy + uz * uz);
    }

    // Beads kept on the mirror, and a moving yarn over the others.
    function surfaces() {
      let worst = 0;
      for (let g = 0; g < first[nYarns]; g++) {
        if (!mobile[g]) continue;
        const x = p[3 * g], y = p[3 * g + 1], z = p[3 * g + 2];
        const r = Math.hypot(x, y);
        let floor = 0.5;
        if (lifted[yarnOf[g]] && r > hole + 0.5) {
          floor += LIFT * Math.min(1, (r - hole - 0.5) / 1.5);
        }
        if (r >= hole) {
          if (z < floor) {
            worst = Math.max(worst, floor - z);
            p[3 * g + 2] = Math.min(floor, z + MOVE);
          }
        } else if (z < 0.5) {
          // Round the edge of the hole.
          const er = hole - r;
          const ez = Math.max(0, z);
          const dist = Math.hypot(er, ez);
          if (dist < 0.5) {
            worst = Math.max(worst, 0.5 - dist);
            const f = Math.min(MOVE, 0.5 - dist) / Math.max(dist, 1e-9);
            const ox = r > 1e-9 ? x / r : 1;
            const oy = r > 1e-9 ? y / r : 0;
            p[3 * g] -= ox * er * f;
            p[3 * g + 1] -= oy * er * f;
            p[3 * g + 2] += ez * f;
          }
        }
      }
      return worst;
    }

    let push = new Float64Array(0);
    let asked = new Float64Array(0);
    function give(g, amount, vx, vy, vz) {
      if (!mobile[g] || amount === 0) return;
      push[3 * g] += amount * vx;
      push[3 * g + 1] += amount * vy;
      push[3 * g + 2] += amount * vz;
      asked[g] += 1;
    }
    function separate(rounds) {
      let worst = 0;
      if (push.length !== p.length) {
        push = new Float64Array(p.length);
        asked = new Float64Array(p.length / 3);
      }
      for (let round = 0; round < rounds; round++) {
        push.fill(0);
        asked.fill(0);
        worst = 0;
        for (let e = 0; e < pairs.length; e += 2) {
          const s = pairs[e], t = pairs[e + 1];
          const dist = closest(s, t);
          const short = 1 - dist;
          if (short <= SLACK) continue;
          if (short > worst) worst = short;
          const u = st[0], v = st[1];
          let vx = p[3 * s] + u * (p[3 * s + 3] - p[3 * s]) - p[3 * t] - v * (p[3 * t + 3] - p[3 * t]);
          let vy = p[3 * s + 1] + u * (p[3 * s + 4] - p[3 * s + 1]) - p[3 * t + 1] - v * (p[3 * t + 4] - p[3 * t + 1]);
          let vz = p[3 * s + 2] + u * (p[3 * s + 5] - p[3 * s + 2]) - p[3 * t + 2] - v * (p[3 * t + 5] - p[3 * t + 2]);
          if (dist > 1e-12) {
            vx /= dist;
            vy /= dist;
            vz /= dist;
          } else {
            vx = 1;
            vy = vz = 0;
          }
          const ws0 = mobile[s] * (1 - u), ws1 = mobile[s + 1] * u;
          const wt0 = mobile[t] * (1 - v), wt1 = mobile[t + 1] * v;
          const total = ws0 * ws0 + ws1 * ws1 + wt0 * wt0 + wt1 * wt1;
          if (total <= 0) continue;
          const l = short / total;
          give(s, ws0 * l, vx, vy, vz);
          give(s + 1, ws1 * l, vx, vy, vz);
          give(t, -wt0 * l, vx, vy, vz);
          give(t + 1, -wt1 * l, vx, vy, vz);
        }
        worst = Math.max(worst, surfaces());
        if (worst <= SLACK) break;
        for (let g = 0; g < first[nYarns]; g++) {
          if (!asked[g]) continue;
          // Contacts on the same bead overlap: half of each is plenty.
          const f = 1 / Math.max(1, 0.5 * asked[g]);
          const mx = push[3 * g] * f, my = push[3 * g + 1] * f, mz = push[3 * g + 2] * f;
          const c = Math.min(1, MOVE / Math.max(Math.sqrt(mx * mx + my * my + mz * mz), 1e-300));
          p[3 * g] += mx * c;
          p[3 * g + 1] += my * c;
          p[3 * g + 2] += mz * c;
        }
      }
      return worst;
    }

    // Tension: each yarn's active beads drawn straight between its last
    // made bead and its carrier, implicitly, and never further at once than
    // the contacts can make good.
    let column = new Float64Array(0);
    let cc = new Float64Array(0);
    let mm = new Float64Array(0);
    let was = new Float64Array(0);
    function pull(h) {
      if (was.length !== p.length) was = new Float64Array(p.length);
      was.set(p);
      for (let a = 0; a < nYarns; a++) {
        const from = first[a] + kept[a] - 1;
        const n = first[a + 1] - from;
        if (column.length < n) {
          column = new Float64Array(n);
          cc = new Float64Array(n);
          mm = new Float64Array(n);
        }
        for (let c = 0; c < 3; c++) {
          for (let i = 0; i < n; i++) column[i] = p[3 * (from + i) + c];
          settleChain(column, n, h, cc, mm);
          for (let i = 1; i < n - 1; i++) p[3 * (from + i) + c] = column[i];
        }
      }
      for (let g = 0; g < first[nYarns]; g++) {
        if (!mobile[g]) continue;
        const mx = p[3 * g] - was[3 * g], my = p[3 * g + 1] - was[3 * g + 1], mz = p[3 * g + 2] - was[3 * g + 2];
        const size = Math.sqrt(mx * mx + my * my + mz * mz);
        if (size > MOVE) {
          const f = MOVE / size;
          p[3 * g] = was[3 * g] + mx * f;
          p[3 * g + 1] = was[3 * g + 1] + my * f;
          p[3 * g + 2] = was[3 * g + 2] + mz * f;
        }
      }
    }

    // The take-off: whenever a yarn near the axis rises above the fell's
    // height, the made braid is drawn down, the crossings above it with it.
    // It draws no further: what packs the crossings together is the yarns'
    // pull out to their carriers, beating each new one up against the last,
    // so the braid's pitch is what jamming leaves.
    let lastUp = 0;
    function takeOff() {
      let top = -Infinity;
      for (let a = 0; a < nYarns; a++) {
        // Not the yarn on the move, raised over the others.
        if (lifted[a]) continue;
        for (let g = first[a] + kept[a]; g < first[a + 1]; g++) {
          if (Math.hypot(p[3 * g], p[3 * g + 1]) < braidRadius) top = Math.max(top, p[3 * g + 2]);
        }
      }
      lastUp = top;
      const by = -Math.max(0, Math.min(MOVE / 10, top - FELL));
      if (!by) return;
      for (const y of yarns) {
        for (let i = 0; i < y.made.length - kept[yarns.indexOf(y)]; i++) y.made[i][2] += by;
      }
      for (let a = 0; a < nYarns; a++) {
        for (let g = first[a]; g < first[a] + kept[a]; g++) p[3 * g + 2] += by;
      }
    }

    function setCarrier(a) {
      const g = first[a + 1] - 1;
      const [x, y, z] = carrier(a);
      p[3 * g] = x;
      p[3 * g + 1] = y;
      p[3 * g + 2] = z;
    }

    function relax(iterations, now) {
      for (let k = 0; k < iterations; k++) {
        pull(8);
        takeOff();
        if (stale()) neighbours();
        separate(30);
      }
      resample(now);
      neighbours();
    }

    gather();
    neighbours();
    separate(200);
    relax(40, 0);

    const steps = job.steps;
    for (let number = 0; number < steps.length; number++) {
      const moving = steps[number].filter(([, delta]) => delta);
      if (!moving.length) continue;
      if (moving.length === nYarns && moving.every(([, delta]) => delta === moving[0][1])) {
        // The disk turns, the braid hanging from it with it: nothing crosses.
        const by = (sense * 2 * Math.PI * moving[0][1]) / nSlots;
        const c = Math.cos(by), s = Math.sin(by);
        const turn = (point) => {
          const [x, y] = point;
          point[0] = c * x - s * y;
          point[1] = s * x + c * y;
        };
        scatter();
        for (const y of yarns) {
          y.made.forEach(turn);
          y.active.forEach(turn);
        }
        for (let a = 0; a < nYarns; a++) angle[a] += by;
        gather();
        neighbours();
        continue;
      }
      // One yarn raised over those it passes; several sliding along
      // together pass nobody, and stay down on the rim.
      const arcs = moving.map(([a, delta]) => [a, (sense * 2 * Math.PI * delta) / nSlots]);
      const longest = Math.max(...arcs.map(([, arc]) => Math.abs(arc)));
      if (moving.length === 1 && Math.abs(moving[0][1]) > 1) {
        const [[a, arc]] = arcs;
        const inner = 0.5 + 0.35 * Math.sqrt(nYarns);
        lifted[a] = 1;
        const travel = (toRadius, toRaise) => {
          const [r0, h0] = [radius[a], raised[a]];
          const parts = Math.max(1, Math.ceil(Math.hypot(toRadius - r0, toRaise - h0) / 0.4));
          for (let part = 1; part <= parts; part++) {
            radius[a] = r0 + ((toRadius - r0) * part) / parts;
            raised[a] = h0 + ((toRaise - h0) * part) / parts;
            setCarrier(a);
            relax(5, number + 0.5 * (part / parts) * (toRadius < r0 ? 0 : 1));
          }
        };
        travel(inner, RAISE);
        const parts = Math.max(1, Math.ceil((Math.abs(arc) * inner) / 0.3));
        for (let part = 1; part <= parts; part++) {
          angle[a] += arc / parts;
          setCarrier(a);
          relax(5, number + (0.5 * part) / parts);
        }
        travel(rim, 0);
        lifted[a] = 0;
      } else {
        const parts = Math.max(1, Math.ceil((longest * rim) / 0.4));
        for (let part = 1; part <= parts; part++) {
          for (const [a, arc] of arcs) {
            angle[a] += arc / parts;
            setCarrier(a);
          }
          relax(5, number + part / parts);
        }
      }
      relax(job.settle || 30, number + 1);
      if (job.debug) console.error(number, "up", lastUp.toFixed(3), "bottom", Math.min(...yarns.map((y) => y.made[0][2])).toFixed(2), "made", yarns.map((y) => y.made.length).join(","), "beads", first[nYarns], "pairs", pairs.length / 2);
      if (progress) progress((number + 1) / steps.length);
    }
    relax(60, steps.length);
    if (job.debug) {
      const slack = () => {
        let total = 0;
        for (const y of yarns) {
          const c = [y.made[y.made.length - 1], ...y.active];
          let L = 0;
          for (let i = 1; i < c.length; i++) L += Math.hypot(c[i][0] - c[i - 1][0], c[i][1] - c[i - 1][1], c[i][2] - c[i - 1][2]);
          const a = c[0], b = c[c.length - 1];
          total += L - Math.hypot(b[0] - a[0], b[1] - a[1], b[2] - a[2]);
        }
        return total.toFixed(1);
      };
      for (let k = 0; k < 6; k++) {
        console.error("slack", slack());
        relax(100, steps.length);
      }
    }

    if (job.raw) {
      scatter();
      return { raw: yarns.map((y) => [...y.made, ...y.active]) };
    }
    // The braid as made, up to where it meets the mirror, turned over to
    // grow up from its fell: a turn, not a mirror, so it keeps its hand.
    scatter();
    let nearest = Infinity;
    for (let e = 0; e < pairs.length; e += 2) nearest = Math.min(nearest, closest(pairs[e], pairs[e + 1]));
    const d = job.yarn_diameter;
    const top = -0.5;
    const points = [];
    const times = [];
    let bottom = Infinity;
    for (const y of yarns) bottom = Math.min(bottom, y.made[0][2]);
    for (const y of yarns) {
      const chain = [...y.made, ...y.active];
      const when = [...y.madeAt, ...y.active.map(() => steps.length)];
      const yarn = [];
      const at = [];
      for (let i = 0; i < chain.length && chain[i][2] <= top; i++) {
        const [x, yy, z] = chain[i];
        yarn.push([x * d, -yy * d, (top - z) * d]);
        at.push(when[i]);
      }
      points.push(yarn);
      times.push(at);
    }
    return { points, times, closest: nearest * d, height: (top - bottom) * d };
  }

  root.formBraid = formBraid;
  if (typeof module !== "undefined" && module.exports) {
    module.exports = { formBraid };
  }
})(typeof self !== "undefined" ? self : globalThis);
