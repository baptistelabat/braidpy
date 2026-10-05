// The rope tests' cases, run by tests/test_rope.py: each settles yarns with
// web/rope.js and prints what the test checks, as JSON.
const path = require("path");
const { settle } = require(path.join(__dirname, "..", "..", "web", "rope.js"));
const fs = require("fs");
const { layWord, readWord } = require("./braidgeo.js");
const { linkingMatrix } = require("./linking.js");
const { tightenYarns } = require(path.join(__dirname, "..", "..", "web", "tighten.js"));
const { relay } = require(path.join(__dirname, "..", "..", "web", "rope.js"));
const { form } = require(path.join(__dirname, "..", "..", "web", "form.js"));

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

const cases = {
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
  plait() {
    const word = [1, -2, 1, -2];
    const out = settle({ yarns: layWord(word, 3), spacing: 0.5, force: 1, turns: true, steps: 60000, tolerance: 1e-3 });
    return { laid: word, settled: readWord(out.yarns), turn: out.turn, deepest: out.deepest, largestForce: out.largestForce };
  },
  // For the documentation's figures: the yarns, settled, and how the
  // settling went.
  shapes() {
    const ys = helices(2, 10, 1, 0.5);
    const spacing = Math.hypot(ys[0][3] - ys[0][0], ys[0][4] - ys[0][1], ys[0][5] - ys[0][2]);
    const rope = settle({ yarns: ys, spacing, force: 1, turns: false, steps: 60000, tolerance: 1e-3 });
    const word = [1, -2, 1, -2, 1, -2];
    const plait = settle({ yarns: layWord(word, 3), spacing: 0.5, force: 1, turns: true, steps: 60000, tolerance: 1e-3 });
    return { ropeLaid: ys, rope: rope.yarns, plaitLaid: layWord(word, 3), plait: plait.yarns };
  },
  // A sinnet made crossing by crossing, as the page makes it, then
  // settled: its closure's linking numbers at each stage.
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
      laid: linkingMatrix(yarns, 0),
      made: linkingMatrix(made.yarns, 0),
      settled: linkingMatrix(rest.yarns, rest.turn),
      height: top(yarns),
      madeHeight: top(made.yarns),
      deepestEver: Math.max(made.deepestEver, rest.deepestEver),
      largestForce: rest.largestForce,
    };
  },
  // A sinnet, laid by braidpy (its tightening job read from a file), beaten
  // up as the page beats it up: its closure's linking numbers before and
  // after.
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
      before: linkingMatrix(yarns, 0),
      after: linkingMatrix(out.yarns, out.turn),
      height,
      settledHeight: height + out.rise,
      deepestEver: out.deepestEver,
      startOverlap: start.deepestEver,
      largestForce: out.largestForce,
      ...(process.argv[4] === "shapes" ? { laid: yarns, settled: out.yarns, history } : {}),
    };
  },
};

console.log(JSON.stringify(cases[process.argv[2]]()));
