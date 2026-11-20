// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A braid made on the marudai (marudai.js) as a .b3d file, the file
// braid3dmin saves: URL-encoded JSON of each yarn's colour, the way it
// leaves the braid and its beads, and the steps it was made by.
// braid3dmin shows the beads as they are, and lists the steps; the code
// here is this project's own, writing that format.
//
// Angles are braid3dmin's, as marudai.js turns them.  When the disk turns
// with every bobbin on it and the braid with them, nothing moves against
// anything else: braid3dmin has no such step, and the angles after it are
// taken from the braid as it then lies.  Turned while the braid is held,
// the bobbins twist the yarns in: that is written as every yarn moved.
//
// With each step, where every yarn is before it, as braid3dmin writes them.
// A move's angles go the short way round, so a move of half a turn or more
// is written as two steps, each less than half a turn the same way round,
// breaking between two slots: kumihimo's strands across the disk.
//
// braidpy.b3d reads such a file back.  braid3dmin moves the yarn it finds
// at a move's angle, and a repeat step plays its steps again from where it
// puts the yarns back to.  A braid
// whose cycle comes round exactly — the same moves at the same angles, the
// yarns back on the same angles — is written as one cycle and a repeat
// that puts nothing back: braid3dmin makes it as it was made here.  Any
// other braid is written move by move, as braid3dmin would put its yarns
// back its own way.

(function (root) {
  "use strict";

  // The angle of a slot, as marudai.js turns it (loaded before this in the
  // page, required beside it in Node).
  const slotAngle =
    typeof module !== "undefined" && module.exports ? require("./marudai.js?v=8a7291e92f").slotAngle : root.slotAngleOnMarudai;

  const wrap = (a) => a - 2 * Math.PI * Math.floor((a + Math.PI) / (2 * Math.PI));
  const colourNumber = (colour) => (/^#[0-9a-f]{6}$/i.test(colour ?? "") ? parseInt(colour.slice(1), 16) : 0xcccccc);

  /**
   * The .b3d text of a braid made on the marudai.
   *
   * @param {Object} job  The disk program as made (marudai.js's begin):
   *     n_slots, start, steps, clockwise, and held or twists if given.
   * @param {Object} making  What begin() returned, every step made.
   * @param {string[]} colours  Each yarn's colour, as "#rrggbb".
   * @returns {string}
   */
  function b3dText(job, making, colours) {
    const n = job.start.length;
    const sense = job.clockwise ? -1 : 1;
    const twists = job.twists ?? !!job.held;
    const angleOf = (slot) => slotAngle(slot, job.n_slots, job.clockwise);
    const dirs = (job.from ?? job.start).map(angleOf);
    // How far the braid has turned with the disk: angles are given from it.
    let turned = 0;
    const poss = () =>
      dirs
        .map((dir, t) => ({ angle: wrap(dir - turned), id: String(t) }))
        .sort((p, q) => p.angle - q.angle);
    // Each step with where the yarns are before it, as written, and after
    // it, to find a cycle by (repeated()); `before` taken before its moves.
    const step = (type, moves, before, extra = {}) => ({
      type, num: steps.length, moves, tighten: type ? 1 : 0, repeatFrom: 0, repeatTimes: 0, rotate: 0, ...extra,
      poss: before, after: poss(),
    });
    const moved = (t, to) => {
      const move = { from: wrap(dirs[t] - turned), to: wrap(to - turned), id: t };
      dirs[t] = to;
      return move;
    };
    // A move of d slots, as the angle it turns a yarn by.
    const turnOf = (d) => (sense * 2 * Math.PI * d) / job.n_slots;
    // Of a move of half a turn or more, the first step's part: to between
    // the two slots half way along it.
    const long = (d) => 2 * Math.abs(d) >= job.n_slots;
    const firstPart = (d) => Math.sign(d) * (Math.floor(Math.abs(d) / 2) + 0.5);

    const steps = [];
    steps.push(step(null, [], poss()));
    if (job.from) {
      const before = poss();
      steps.push(step("threadMove", job.start.map((slot, t) => moved(t, angleOf(slot))), before));
    }
    const first = steps.length;
    for (const moves of job.steps) {
      const moving = moves.filter(([, d]) => d);
      if (!moving.length) continue;
      if (moving.length === n && moving.every(([, d]) => d === moving[0][1])) {
        const by = (sense * 2 * Math.PI * moving[0][1]) / job.n_slots;
        if (twists) {
          const before = poss();
          steps.push(step("threadMove", dirs.map((dir, t) => moved(t, dir - by)), before));
        }
        else {
          for (let t = 0; t < n; t++) dirs[t] -= by;
          turned -= by;
        }
        continue;
      }
      const before = poss();
      const list = moving.map(([t, d]) => moved(t, dirs[t] - turnOf(long(d) ? firstPart(d) : d)));
      steps.push(step("threadMove", list, before));
      const rest = moving.filter(([, d]) => long(d));
      if (rest.length) {
        const between = poss();
        const ends = rest.map(([t, d]) => moved(t, dirs[t] - turnOf(d - firstPart(d))));
        steps.push(step("threadMove", ends, between));
      }
    }

    // The beads as made, turned back by as far as the braid went with the
    // disk, as the angles are.
    const c = Math.cos(turned), s = Math.sin(turned);
    const machine = making.machine;
    // braid3dmin has no core: the yarns alone.
    const threadStates = machine.threads.slice(0, n).map((thread, t) => ({
      colour: colourNumber(colours[t]),
      dir: wrap(thread.dir - turned),
      poss: machine.positions(t).map(([x, y, z]) => ({ x: x * c + z * s, y, z: -x * s + z * c })),
    }));
    const written = repeated(steps, first).map(({ after, ...step }) => step);
    return encodeURIComponent(JSON.stringify({ nThreads: n, threadStates, steps: written }));
  }

  // The steps from `first` on as one cycle and a repeat, if they come round
  // exactly; else as they are.
  function repeated(steps, first) {
    const same = (a, b) => Math.abs(wrap(a - b)) < 1e-9;
    const angles = (k) => steps[k].after.map((p) => p.angle);
    const sameMoves = (j, k) =>
      steps[j].rotate === steps[k].rotate &&
      steps[j].moves.length === steps[k].moves.length &&
      steps[j].moves.every((m, i) => same(m.from, steps[k].moves[i].from) && same(m.to, steps[k].moves[i].to));
    const sameAngles = (j, k) => angles(j).every((a, i) => same(a, angles(k)[i]));
    const made = steps.length - first;
    for (let cycle = 1; cycle <= made / 2; cycle++) {
      if (made % cycle) continue;
      let comesRound = true;
      for (let k = cycle; k < made && comesRound; k++) {
        comesRound = sameMoves(first + k, first + (k % cycle));
        if (k % cycle === 0) comesRound &&= sameAngles(first - 1 + k, first - 1);
      }
      if (!comesRound || !sameAngles(steps.length - 1, first - 1)) continue;
      const end = steps[steps.length - 1];
      return [
        ...steps.slice(0, first + cycle),
        {
          type: "repeat", num: first + cycle, moves: [], tighten: 0,
          repeatFrom: first, repeatTimes: made / cycle - 1, rotate: 0, poss: end.after, after: end.after,
        },
      ];
    }
    return steps;
  }

  root.b3dText = b3dText;
  if (typeof module !== "undefined" && module.exports) module.exports = { b3dText };
})(typeof self !== "undefined" ? self : globalThis);
