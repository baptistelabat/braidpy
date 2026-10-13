// The marudai tests' cases, run by tests/test_marudai.py: each makes a
// braid move by move with web/marudai.js and prints what the test checks,
// as JSON.
const path = require("path");
const fs = require("fs");
const { make, begin } = require(path.join(__dirname, "..", "..", "web", "marudai.js"));

const cases = {
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
    // Each yarn's mean distance from the yarns' middle, slice by slice up
    // the braid clear of its ends.
    const radii = yarns.map(() => 0);
    let slices = 0;
    for (let z = 2; z < out.tip - 2; z += 0.5) {
      const at = yarns.map((y) => {
        for (let i = 3; i < y.length; i += 3) {
          if ((y[i - 1] - z) * (y[i + 2] - z) <= 0 && y[i - 1] !== y[i + 2]) {
            const f = (z - y[i - 1]) / (y[i + 2] - y[i - 1]);
            return [y[i - 3] + f * (y[i] - y[i - 3]), y[i - 2] + f * (y[i + 1] - y[i - 2])];
          }
        }
        return null;
      });
      if (at.some((p) => !p)) continue;
      const cx = at.reduce((s, p) => s + p[0], 0) / at.length;
      const cy = at.reduce((s, p) => s + p[1], 0) / at.length;
      at.forEach((p, k) => (radii[k] += Math.hypot(p[0] - cx, p[1] - cy)));
      slices++;
    }
    return {
      tip: out.tip,
      closest,
      radius,
      crossings: cut.length,
      radii: radii.map((r) => r / Math.max(slices, 1)),
    };
  },

  // A disk braid made on a marudai in two goes — its first moves, then on
  // from there to the end — and at once: the same braid, bead for bead.
  continued() {
    const disk = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
    const half = Math.floor(disk.steps.length / 2);
    const making = begin({ ...disk, steps: disk.steps.slice(0, half) });
    disk.steps.slice(0, half).forEach((step, k) => making.step(step, k));
    making.hooks.total = disk.steps.length;
    disk.steps.slice(half).forEach((step, k) => making.step(step, half + k));
    const twice = making.result();
    const once = make(disk);
    return { same: JSON.stringify(twice.yarns) === JSON.stringify(once.yarns), tip: once.tip };
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
