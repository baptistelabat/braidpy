// Test helper: the linking numbers of a braid's closure, computed exactly
// from the yarns as polylines (the solid angle each pair of segments
// subtends: Klenin and Langowski, Biopolymers 54, 307, 2000).  A yarn
// passing through a yarn of another closed loop changes their linking
// number by one, however the yarns fold.
function closeUp(yarns, turnBack = 0) {
  const n = yarns.length;
  const ends = yarns.map((y) => ({ b: y.slice(0, 3), t: y.slice(y.length - 3) }));
  const zb = Math.min(...yarns.map((y) => y[2])) - 3;
  const zt = Math.max(...yarns.map((y) => y[y.length - 1])) + 3;
  const R = 40;
  const ang = (p) => Math.atan2(p[1], p[0]);
  // Top end of yarn a, turned back, joins the bottom end nearest it in angle.
  const tops = ends.map(({ t }) => { const c = Math.cos(-turnBack), s = Math.sin(-turnBack); return [c * t[0] - s * t[1], s * t[0] + c * t[1], t[2]]; });
  const next = tops.map((t) => { let best = -1, d = Infinity; ends.forEach(({ b }, k) => { let e = Math.abs(((ang(t) - ang(b) + 3 * Math.PI) % (2 * Math.PI)) - Math.PI); if (e < d) { d = e; best = k; } }); return best; });
  if (new Set(next).size !== n) throw new Error("ends do not pair up");
  const loops = yarns.map((y, a) => {
    const pts = [];
    for (let i = 0; i < y.length; i += 3) pts.push([y[i], y[i + 1], y[i + 2]]);
    const top = pts[pts.length - 1];
    // Turn the end back, rigidly, all ends alike, just above the braid.
    for (let k = 1; k <= 30; k++) { const f = -turnBack * k / 30, c = Math.cos(f), s = Math.sin(f); pts.push([c * top[0] - s * top[1], s * top[0] + c * top[1], top[2] + 0.1 * k]); }
    const t = pts[pts.length - 1], b = ends[next[a]].b, u = ang(t), v = ang(b);
    const lift = zt + 0.5 * a, sink = zb - 0.5 * a;
    pts.push([t[0], t[1], lift], [R * Math.cos(u), R * Math.sin(u), lift], [R * Math.cos(u), R * Math.sin(u), sink], [R * Math.cos(v), R * Math.sin(v), sink], [b[0], b[1], sink], [b[0], b[1], b[2]]);
    return { pts, next: next[a] };
  });
  // Components: follow yarn -> next yarn's start.
  const seen = new Array(n).fill(false), comps = [];
  for (let a = 0; a < n; a++) { if (seen[a]) continue; const c = []; for (let k = a; !seen[k]; k = loops[k].next) { seen[k] = true; c.push(...loops[k].pts); } comps.push(c); }
  return comps;
}
function cross(a, b) { return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]; }
function sub(a, b) { return [a[0] - b[0], a[1] - b[1], a[2] - b[2]]; }
function dot(a, b) { return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]; }
function unit(a) { const l = Math.hypot(...a); return l > 1e-15 ? [a[0] / l, a[1] / l, a[2] / l] : [0, 0, 0]; }
function link(A, B) {
  let total = 0;
  for (let i = 0; i < A.length; i++) {
    const p1 = A[i], p2 = A[(i + 1) % A.length];
    for (let j = 0; j < B.length; j++) {
      const p3 = B[j], p4 = B[(j + 1) % B.length];
      const r13 = sub(p3, p1), r14 = sub(p4, p1), r23 = sub(p3, p2), r24 = sub(p4, p2);
      const n1 = unit(cross(r13, r14)), n2 = unit(cross(r14, r24)), n3 = unit(cross(r24, r23)), n4 = unit(cross(r23, r13));
      const cl = (x) => Math.max(-1, Math.min(1, x));
      let om = Math.asin(cl(dot(n1, n2))) + Math.asin(cl(dot(n2, n3))) + Math.asin(cl(dot(n3, n4))) + Math.asin(cl(dot(n4, n1)));
      om *= Math.sign(dot(cross(sub(p4, p3), sub(p2, p1)), r13));
      total += om;
    }
  }
  return total / (4 * Math.PI);
}
function linkingMatrix(yarns, turnBack) {
  const comps = closeUp(yarns, turnBack);
  const m = [];
  for (let i = 0; i < comps.length; i++) for (let j = i + 1; j < comps.length; j++) m.push(Math.round(link(comps[i], comps[j]) * 1000) / 1000);
  return { components: comps.length, links: m };
}
module.exports = { linkingMatrix };
