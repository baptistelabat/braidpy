// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The rope tests' cases, run by tests/test_rope.py: each settles yarns with
// web/rope.js (or makes them with web/form.js) and prints the yarns and how
// it went, as JSON.  Only the physics is here: braidpy, in Python, lays a
// braid word as yarns, reads the word back off them and measures their
// closure's linking numbers (braidpy.parametric_strand, braidpy.linking).
const path = require("path");
const { settle } = require(path.join(__dirname, "..", "..", "web", "rope.js"));
const fs = require("fs");
const { tightenYarns } = require(path.join(__dirname, "..", "..", "web", "tighten.js"));
const { relay } = require(path.join(__dirname, "..", "..", "web", "rope.js"));
const { form } = require(path.join(__dirname, "..", "..", "web", "form.js"));
const { rounded } = require("./rounded.js");
const ROPE = path.join(__dirname, "..", "..", "web", "rope.js");
const FORM = path.join(__dirname, "..", "..", "web", "form.js");

// Yarns laid by braidpy, as JSON: each yarn's points, x y z after x y z,
// laid again with beads half a diameter apart.
function laidYarns(file) {
  return JSON.parse(fs.readFileSync(file, "utf8")).map((y) => Array.from(relay(Float64Array.from(y), 0.5)));
}

function helices(turns, height, radius, spacing) {
  return [0, Math.PI].map((phase) => {
    const beads = Math.round(Math.hypot(height, 2 * Math.PI * radius * turns) / spacing) + 1;
    const out = [];
    for (let i = 0; i < beads; i++) {
      const t = i / (beads - 1);
      const a = phase + 2 * Math.PI * turns * t;
      out.push(radius * Math.cos(a), radius * Math.sin(a), height * t);
    }
    return out;
  });
}

function length(yarn) {
  let total = 0;
  for (let i = 3; i < yarn.length; i += 3) {
    total += Math.hypot(yarn[i] - yarn[i - 3], yarn[i + 1] - yarn[i - 2], yarn[i + 2] - yarn[i - 1]);
  }
  return total;
}

// rope.js and form.js with the maths library rounded (rounded.js), for
// braidpy's ports, rounded the same way, to match bead for bead.  form.js
// takes rope.js's mechanics as rope.js leaves them: rounded too.
function roundedPhysics() {
  const rope = rounded(ROPE);
  return { ...rope, form: rounded(FORM).form };
}

const cases = {
  // A job read from a file — its yarns, laid again with beads half a
  // diameter apart, and how to settle them — settled by rope.js, rounded.
  roundedSettle() {
    const { yarns, ...job } = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const { settle, relay } = roundedPhysics();
    return settle({ ...job, yarns: yarns.map((y) => Array.from(relay(Float64Array.from(y), 0.5))) });
  },
  // A job read from a file made crossing by crossing by form.js, rounded.
  roundedForm() {
    const job = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    return roundedPhysics().form(job);
  },
  twoPly() {
    const yarns = helices(2, 10, 1, 0.5);
    const spacing = Math.hypot(yarns[0][3] - yarns[0][0], yarns[0][4] - yarns[0][1], yarns[0][5] - yarns[0][2]);
    const out = settle({ yarns, spacing, force: 1, turns: false, steps: 60000, tolerance: 1e-3 });
    const y = out.yarns[0];
    const n = y.length / 3;
    const radii = [];
    for (let i = Math.floor(n / 3); i < Math.floor((2 * n) / 3); i++) radii.push(Math.hypot(y[3 * i], y[3 * i + 1]));
    return {
      before: length(yarns[0]),
      after: length(y),
      height: 10 + out.rise,
      radius: radii.reduce((a, b) => a + b) / radii.length,
      deepest: out.deepest,
      largestForce: out.largestForce,
    };
  },
  // The same two-ply rope, its end free to turn.
  twoPlyFree() {
    const yarns = helices(2, 10, 1, 0.5);
    const spacing = Math.hypot(yarns[0][3] - yarns[0][0], yarns[0][4] - yarns[0][1], yarns[0][5] - yarns[0][2]);
    const out = settle({ yarns, spacing, force: 1, turns: true, steps: 600000, tolerance: 1e-3 });
    return { length: length(yarns[0]), turn: out.turn, rise: out.rise, largestForce: out.largestForce };
  },
  // A braid word's yarns, laid by braidpy (read from a file), pulled taut,
  // their top ends free to turn.
  word() {
    const yarns = laidYarns(process.argv[3]);
    const out = settle({ yarns, spacing: 0.5, force: 1, turns: true, steps: 60000, tolerance: 1e-3 });
    return { yarns: out.yarns, turn: out.turn, deepest: out.deepest, largestForce: out.largestForce };
  },
  // For the documentation's figures: the yarns, settled, and how the
  // settling went.
  shapes() {
    const ys = helices(2, 10, 1, 0.5);
    const spacing = Math.hypot(ys[0][3] - ys[0][0], ys[0][4] - ys[0][1], ys[0][5] - ys[0][2]);
    const rope = settle({ yarns: ys, spacing, force: 1, turns: false, steps: 60000, tolerance: 1e-3 });
    const plaitLaid = laidYarns(process.argv[3]);
    const plait = settle({ yarns: plaitLaid, spacing: 0.5, force: 1, turns: true, steps: 60000, tolerance: 1e-3 });
    return { ropeLaid: ys, rope: rope.yarns, plaitLaid, plait: plait.yarns };
  },
  // A sinnet made crossing by crossing, as the page makes it, then
  // settled: its yarns at each stage.
  formed() {
    const job = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const clear = tightenYarns({ ...job, iterations: Math.max(job.iterations, 100) });
    const d = job.yarn_diameter;
    const [cx, cy] = job.centre;
    const yarns = [];
    for (let a = 0; a < job.n_yarns; a++) {
      const points = [];
      for (let i = 0; i < job.n; i++) {
        const k = a * job.n + i;
        points.push((clear.xy[2 * k] - cx) / d, (clear.xy[2 * k + 1] - cy) / d, (i * job.spacing) / d);
      }
      yarns.push(Array.from(relay(Float64Array.from(points), 0.5)));
    }
    const made = form({ yarns, row: 1.5, friction: 0.3, feed: 1, weight: 0.25 * job.n_yarns });
    const rest = settle({
      yarns: made.yarns,
      spacing: 0.5,
      feed: 1,
      force: 0.25 * job.n_yarns,
      turns: true,
      stretch: 100,
      contact: 100,
      steps: 60000,
      tolerance: 1e-3,
    });
    const top = (ys) => Math.max(...ys.map((y) => y[y.length - 1]));
    return {
      laid: yarns,
      made: made.yarns,
      settled: rest.yarns,
      turn: rest.turn,
      height: top(yarns),
      madeHeight: top(made.yarns),
      deepestEver: Math.max(made.deepestEver, rest.deepestEver),
      largestForce: rest.largestForce,
    };
  },
  // A sinnet, laid by braidpy (its tightening job read from a file), beaten
  // up as the page beats it up: its yarns before and after.
  sinnet() {
    const job = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const clear = tightenYarns({ ...job, iterations: Math.max(job.iterations, 100) });
    const d = job.yarn_diameter;
    const [cx, cy] = job.centre;
    const yarns = [];
    for (let a = 0; a < job.n_yarns; a++) {
      const points = [];
      for (let i = job.n - 1; i >= 0; i--) {
        const k = a * job.n + i;
        points.push((clear.xy[2 * k] - cx) / d, (clear.xy[2 * k + 1] - cy) / d, ((job.n - 1 - i) * job.spacing) / d);
      }
      yarns.push(Array.from(relay(Float64Array.from(points), 0.5)));
    }
    const start = settle({ yarns, spacing: 0.5, stretch: 100, contact: 100, steps: 1 });
    const history = [];
    const out = settle({
      progress: ({ step, rise, largestForce }) => history.push([step, rise, largestForce]),
      yarns,
      spacing: 0.5,
      feed: 1,
      force: 0.25 * job.n_yarns,
      turns: true,
      stretch: 100,
      contact: 100,
      steps: 60000,
      tolerance: 1e-3,
    });
    const height = ((job.n - 1) * job.spacing) / d;
    return {
      laid: yarns,
      settled: out.yarns,
      turn: out.turn,
      height,
      settledHeight: height + out.rise,
      deepestEver: out.deepestEver,
      startOverlap: start.deepestEver,
      largestForce: out.largestForce,
      ...(process.argv[4] === "shapes" ? { history } : {}),
    };
  },
};

console.log(JSON.stringify(cases[process.argv[2]]()));
