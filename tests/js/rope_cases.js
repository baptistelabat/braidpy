// The rope tests' cases, run by tests/test_rope.py: each settles yarns with
// web/rope.js and prints what the test checks, as JSON.
const path = require("path");
const { settle } = require(path.join(__dirname, "..", "..", "web", "rope.js"));
const { layWord, readWord } = require("./braidgeo.js");

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
};

console.log(JSON.stringify(cases[process.argv[2]]()));
