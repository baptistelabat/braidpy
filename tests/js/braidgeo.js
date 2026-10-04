// Test helpers for web/rope.js: lay a braid word as 3D yarns, and read the
// word back off yarns.

// Lay a braid word as 3D yarns (strands at slots along x, rising in z),
// and read a braid word back off 3D yarns.
function layWord(word, n, { gap = 1.5, rise = 3, lift = 0.7, spacing = 0.5 } = {}) {
  const slot = [...Array(n).keys()];  // strand in each slot
  const paths = [...Array(n)].map(() => []);
  const at = (k) => (k - (n - 1) / 2) * gap;
  word.forEach((g, step) => {
    const i = Math.abs(g) - 1;
    const over = g > 0 ? i : i + 1;     // slot whose strand passes over (toward -y)
    for (let q = 0; q < 20; q++) {
      const t = q / 20, z = (step + t) * rise;
      for (let k = 0; k < n; k++) {
        const s = slot[k];
        let x = at(k), y = 0;
        if (k === i || k === i + 1) {
          const to = k === i ? i + 1 : i;
          const e = (1 - Math.cos(Math.PI * t)) / 2;
          x = at(k) + (at(to) - at(k)) * e;
          y = (k === over ? -lift : lift) * Math.sin(Math.PI * t);
        }
        paths[s].push([x, y, z]);
      }
    }
    [slot[i], slot[i + 1]] = [slot[i + 1], slot[i]];
  });
  for (let k = 0; k < n; k++) paths[slot[k]].push([at(k), 0, word.length * rise]);
  return paths.map((p) => resample(p, spacing));
}
function resample(p, s) {
  const cum = [0];
  for (let i = 1; i < p.length; i++) cum.push(cum[i - 1] + Math.hypot(p[i][0]-p[i-1][0], p[i][1]-p[i-1][1], p[i][2]-p[i-1][2]));
  const total = cum[cum.length - 1], beads = Math.round(total / s) + 1, out = [];
  let j = 0;
  for (let b = 0; b < beads; b++) {
    const along = total * b / (beads - 1);
    while (j < p.length - 2 && cum[j + 1] < along) j++;
    const f = Math.min(1, (along - cum[j]) / (cum[j + 1] - cum[j] || 1));
    out.push(...[0, 1, 2].map((c) => p[j][c] + f * (p[j + 1][c] - p[j][c])));
  }
  return out;
}
// The braid word read off yarns: strands ordered along x at each height,
// a swap of neighbours a crossing, its sign from which is nearer -y.
function readWord(yarns, levels = 2000) {
  const zs = yarns.map((y) => [y[2], y[y.length - 1]]);
  const lo = Math.max(...zs.map((z) => z[0])), hi = Math.min(...zs.map((z) => z[1]));
  const atZ = (y, z) => {
    for (let i = 3; i < y.length; i += 3) {
      if ((y[i - 1] - z) * (y[i + 2] - z) <= 0 && y[i + 2] !== y[i - 1]) {
        const f = (z - y[i - 1]) / (y[i + 2] - y[i - 1]);
        return [y[i - 3] + f * (y[i] - y[i - 3]), y[i - 2] + f * (y[i + 1] - y[i - 2])];
      }
    }
    return null;
  };
  let order = null; const word = [];
  for (let l = 0; l <= levels; l++) {
    const z = lo + (hi - lo) * l / levels;
    const pts = yarns.map((y) => atZ(y, z));
    if (pts.some((p) => !p)) return null;  // not monotone in z
    const now = [...pts.keys()].sort((a, b) => pts[a][0] - pts[b][0]);
    if (order) {
      // bubble from old order to new, recording adjacent swaps
      const cur = order.slice();
      for (let k = 0; k < now.length; k++) {
        let j = cur.indexOf(now[k]);
        while (j > k) {
          const a = cur[j - 1], b = cur[j];
          // b moves left past a: the one nearer -y passes over
          const sign = pts[a][1] < pts[b][1] ? 1 : -1;  // left strand (a) over => positive
          word.push(sign * j);
          [cur[j - 1], cur[j]] = [cur[j], cur[j - 1]];
          j--;
        }
      }
    }
    order = now;
  }
  return word;
}
module.exports = { layWord, readWord, resample };
