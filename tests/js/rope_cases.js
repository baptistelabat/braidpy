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
const { make } = require(path.join(__dirname, "..", "..", "web", "marudai.js"));

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

  // A disk braid made move by move (marudai.js), from braidpy's disk
  // program: how long it is, how close its yarns come above the start, and
  // how far from the axis they lie half way up.
  marudai() {
    const disk = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const out = make(disk);
    const yarns = out.yarns;
    let closest = Infinity;
    for (let a = 0; a < yarns.length; a++) {
      for (let b = a + 1; b < yarns.length; b++) {
        const A = yarns[a], B = yarns[b];
        for (let i = 0; i < A.length; i += 3) {
          if (A[i + 2] < 1) continue;
          for (let j = 0; j < B.length; j += 3) {
            if (B[j + 2] < 1) continue;
            closest = Math.min(closest, Math.hypot(A[i] - B[j], A[i + 1] - B[j + 1], A[i + 2] - B[j + 2]));
          }
        }
      }
    }
    // Where each yarn crosses half the braid's length, about their middle.
    const half = out.tip / 2;
    const cut = [];
    for (const y of yarns) {
      for (let i = 3; i < y.length; i += 3) {
        if ((y[i - 1] - half) * (y[i + 2] - half) <= 0 && y[i - 1] !== y[i + 2]) {
          const f = (half - y[i - 1]) / (y[i + 2] - y[i - 1]);
          cut.push([y[i - 3] + f * (y[i] - y[i - 3]), y[i - 2] + f * (y[i + 1] - y[i - 2])]);
          break;
        }
      }
    }
    const mx = cut.reduce((s, p) => s + p[0], 0) / cut.length;
    const my = cut.reduce((s, p) => s + p[1], 0) / cut.length;
    const radius = cut.reduce((s, p) => s + Math.hypot(p[0] - mx, p[1] - my), 0) / cut.length;
    return { tip: out.tip, closest, radius, crossings: cut.length };
  },

  // A braid made on a marudai, and braidpy's own as the page draws it, by
  // the sum of the Gauss linking integrand over their pairs of yarns: a
  // mirror image flips its sign.  The made braid as the page shows it,
  // turned upside down.
  handedness() {
    const { disk, strands } = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const made = make(disk);
    const yarns = made.yarns.map((y) => {
      const points = [];
      for (let i = 0; i < y.length; i += 3) points.push([y[i], y[i + 1], y[i + 2]]);
      return points;
    });
    const top = Math.max(...yarns.flat().map((p) => p[2]));
    const shown = yarns.map((y) => y.map(([x, yy, z]) => [x, -yy, top - z]));
    return { braidpy: gauss(strands), made: gauss(shown), tip: made.tip };
  },
};

function gauss(yarns) {
  let sum = 0;
  for (let a = 0; a < yarns.length; a++) {
    for (let b = a + 1; b < yarns.length; b++) {
      const A = yarns[a], B = yarns[b];
      for (let i = 0; i + 1 < A.length; i++) {
        for (let j = 0; j + 1 < B.length; j++) {
          const da = [0, 1, 2].map((k) => A[i + 1][k] - A[i][k]);
          const db = [0, 1, 2].map((k) => B[j + 1][k] - B[j][k]);
          const r = [0, 1, 2].map((k) => (A[i][k] + A[i + 1][k] - B[j][k] - B[j + 1][k]) / 2);
          const d = Math.hypot(...r);
          if (d < 1e-9) continue;
          const cross = [da[1] * db[2] - da[2] * db[1], da[2] * db[0] - da[0] * db[2], da[0] * db[1] - da[1] * db[0]];
          sum += (cross[0] * r[0] + cross[1] * r[1] + cross[2] * r[2]) / (d * d * d);
        }
      }
    }
  }
  return sum / (4 * Math.PI);
}

console.log(JSON.stringify(cases[process.argv[2]]()));
