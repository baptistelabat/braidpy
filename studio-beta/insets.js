// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The insets over the 3D view: the braid's cross-section, and what made it
// seen from above.

import { $ } from "./page.js?v=6acbd58c1f";
import { braid } from "./scene.js?v=6acbd58c1f";

// The braid seen along its axis, once made: each strand's track over the
// middle of the braid — far from the fell and the held top — and a slice
// half way up, each yarn a disc as thick as it is.  A regular braid has
// settled when its strands share one track, each a step along it.
export const section = $("section");

export function drawSection(result) {
  if (!result || section.hidden) return;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const size = section.clientWidth;
  if (!size) return;
  section.width = section.height = Math.round(size * ratio);
  const ctx = section.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, size, size);
  const n = result.strands[0].points.length;
  const from = Math.floor(0.3 * n);
  const to = Math.max(from + 2, Math.ceil(0.7 * n));
  const middle = result.strands.map((strand) => strand.points.slice(from, to));
  let cx = 0;
  let cy = 0;
  let count = 0;
  for (const points of middle) {
    for (const [x, y] of points) {
      cx += x;
      cy += y;
      count++;
    }
  }
  cx /= count;
  cy /= count;
  const radius = result.yarn_diameter / 2;
  let reach = radius;
  for (const points of middle) {
    for (const [x, y] of points) reach = Math.max(reach, Math.hypot(x - cx, y - cy) + radius);
  }
  const scale = (size / 2 - 14) / reach;
  // Seen from above: a hanging braid is turned over about the x axis.
  const up = braid && braid.stand.rotation.x ? -1 : 1;
  // As the 3D view has it from above: turned with the braid.
  const turn = braid ? braid.turner.rotation.z : 0;
  const tc = Math.cos(turn);
  const ts = Math.sin(turn);
  const X = (x, y) => size / 2 + (tc * (x - cx) - ts * up * (y - cy)) * scale;
  const Y = (y, x) => size / 2 - (ts * (x - cx) + tc * up * (y - cy)) * scale;
  const style = getComputedStyle(document.documentElement);
  ctx.fillStyle = style.getPropertyValue("--muted").trim();
  ctx.font = "10px system-ui, sans-serif";
  ctx.fillText("Cross-section", 8, 14);
  ctx.globalAlpha = 0.55;
  ctx.lineWidth = 1;
  middle.forEach((points, i) => {
    ctx.strokeStyle = result.strands[i].colour;
    ctx.beginPath();
    points.forEach(([x, y], j) => (j ? ctx.lineTo(X(x, y), Y(y, x)) : ctx.moveTo(X(x, y), Y(y, x))));
    ctx.stroke();
  });
  ctx.globalAlpha = 0.9;
  const half = Math.floor((to - from) / 2);
  middle.forEach((points, i) => {
    const [x, y] = points[half];
    ctx.fillStyle = result.strands[i].colour;
    ctx.beginPath();
    ctx.arc(X(x, y), Y(y, x), radius * scale, 0, 2 * Math.PI);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
}

export const top = $("topview");
const topContext = top.getContext("2d");

// ``partly``, during a move made yarn by yarn: the time it started, and the
// yarns already carried, shown at ``now``; the others are shown where they
// were when it started.
export function drawTop(now, partly) {
  if (!braid || !braid.timeline || top.hidden) return;
  const view = braid.timeline;
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  const size = top.clientWidth;
  if (top.width !== Math.round(size * ratio)) {
    top.width = top.height = Math.round(size * ratio);
  }
  const ctx = topContext;
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  ctx.clearRect(0, 0, size, size);
  const style = getComputedStyle(document.documentElement);
  const ink = style.getPropertyValue("--muted").trim();
  const scale = (size / 2 - 18) / (view.reach || 1);
  // Turned so the disk's seam is up, away from the viewer.
  const c = Math.cos(braid.topTurn || 0);
  const s = Math.sin(braid.topTurn || 0);
  const x = (p) => size / 2 + (c * p[0] - s * p[1]) * scale;
  const y = (p) => size / 2 - (s * p[0] + c * p[1]) * scale;

  ctx.lineWidth = 1;
  ctx.strokeStyle = ink;
  for (const outline of view.outlines) {
    ctx.beginPath();
    outline.forEach((p, i) => (i ? ctx.lineTo(x(p), y(p)) : ctx.moveTo(x(p), y(p))));
    ctx.stroke();
  }
  ctx.fillStyle = ink;
  ctx.font = "10px system-ui, sans-serif";
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  // As many names as there is room for round the rim.
  const every = Math.max(1, Math.ceil(view.slots.length / (size / 16)));
  for (const [index, [sx, sy, name]] of view.slots.entries()) {
    if (index % every) continue;
    const out = 1 + 11 / (Math.hypot(sx, sy) * scale || 1);
    ctx.fillText(name, x([sx * out, sy * out]), y([sx * out, sy * out]));
  }

  // Where each carrier is now; on a disk, the strands lifted over the others
  // are drawn last, on top.
  const last = view.times.length - 1;
  const span = view.times[last] - view.times[0];
  const index = (time) => Math.min(last, Math.max(0, span > 0 ? ((time - view.times[0]) / span) * last : 0));
  const after = index(now);
  const before = partly ? index(partly.before) : after;
  const where = view.strands.map((path, i) => {
    const at = !partly || partly.moved.has(i) ? after : before;
    const low = Math.floor(at);
    const high = Math.min(low + 1, path.length - 1);
    const t = at - low;
    return [
      path[low][0] + t * (path[high][0] - path[low][0]),
      path[low][1] + t * (path[high][1] - path[low][1]),
    ];
  });
  const order = where
    .map((p, i) => [Math.hypot(p[0], p[1]), i])
    .sort((a, b) => b[0] - a[0])
    .map(([, i]) => i);
  for (const i of order) {
    const p = where[i];
    ctx.strokeStyle = ctx.fillStyle = braid.colours[i % braid.colours.length];
    if (view.kind === "disk") {
      ctx.lineWidth = 2.5;
      ctx.beginPath();
      ctx.moveTo(size / 2, size / 2);
      ctx.lineTo(x(p), y(p));
      ctx.stroke();
    }
    ctx.beginPath();
    ctx.arc(x(p), y(p), view.kind === "disk" ? 3.5 : 4.5, 0, 2 * Math.PI);
    ctx.fill();
  }
}
