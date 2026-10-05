// The rope tests' cases, run by tests/test_rope.py: each settles yarns with
// web/rope.js and prints what the test checks, as JSON.
const path = require("path");
const { settle } = require(path.join(__dirname, "..", "..", "web", "rope.js"));
const fs = require("fs");
const { layWord, readWord } = require("./braidgeo.js");
const { linkingMatrix } = require("./linking.js");
const { tightenYarns } = require(path.join(__dirname, "..", "..", "web", "tighten.js"));
const { relay } = require(path.join(__dirname, "..", "..", "web", "rope.js"));

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
  // A sinnet, laid by braidpy (its tightening job read from a file), beaten
  // up as the page beats it up: its closure's linking numbers before and
  // after.
  sinnet() {
    const job = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const clear = tightenYarns({ ...job, iterations: Math.min(job.iterations, 30) });
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
    const out = settle({
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
      largestForce: out.largestForce,
    };
  },
};

console.log(JSON.stringify(cases[process.argv[2]]()));
