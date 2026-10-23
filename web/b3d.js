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

(function (root) {
  "use strict";

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
    const angleOf = (slot) => -(sense * 2 * Math.PI * (slot - 1)) / job.n_slots;
    const dirs = (job.from ?? job.start).map(angleOf);
    // How far the braid has turned with the disk: angles are given from it.
    let turned = 0;
    const poss = () =>
      dirs
        .map((dir, t) => ({ angle: wrap(dir - turned), id: String(t) }))
        .sort((p, q) => p.angle - q.angle);
    const step = (type, moves, extra = {}) => ({
      type, num: steps.length, moves, tighten: type ? 1 : 0, repeatFrom: 0, repeatTimes: 0, rotate: 0, ...extra, poss: poss(),
    });
    const moved = (t, to) => {
      const move = { from: wrap(dirs[t] - turned), to: wrap(to - turned), id: t };
      dirs[t] = to;
      return move;
    };

    const steps = [];
    steps.push(step(null, []));
    if (job.from) steps.push(step("threadMove", job.start.map((slot, t) => moved(t, angleOf(slot)))));
    for (const moves of job.steps) {
      const moving = moves.filter(([, d]) => d);
      if (!moving.length) continue;
      if (moving.length === n && moving.every(([, d]) => d === moving[0][1])) {
        const by = (sense * 2 * Math.PI * moving[0][1]) / job.n_slots;
        if (twists) steps.push(step("threadMove", dirs.map((dir, t) => moved(t, dir - by))));
        else {
          for (let t = 0; t < n; t++) dirs[t] -= by;
          turned -= by;
        }
        continue;
      }
      const list = moving.map(([t, d]) => moved(t, dirs[t] - (sense * 2 * Math.PI * d) / job.n_slots));
      steps.push(step("threadMove", list));
    }

    // The beads as made, turned back by as far as the braid went with the
    // disk, as the angles are.
    const c = Math.cos(turned), s = Math.sin(turned);
    const machine = making.machine;
    const threadStates = machine.threads.map((thread, t) => ({
      colour: colourNumber(colours[t]),
      dir: wrap(thread.dir - turned),
      poss: machine.positions(t).map(([x, y, z]) => ({ x: x * c + z * s, y, z: -x * s + z * c })),
    }));
    return encodeURIComponent(JSON.stringify({ nThreads: n, threadStates, steps }));
  }

  root.b3dText = b3dText;
  if (typeof module !== "undefined" && module.exports) module.exports = { b3dText };
})(typeof self !== "undefined" ? self : globalThis);
