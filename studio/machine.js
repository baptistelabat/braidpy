// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A braiding machine seen from above, to load it by hand: a click puts a
// carrier on a slot or takes it off, and carriers that met are ringed.

import { PALETTE } from "./diagram.js?v=f0deb1d221";
import { worker } from "./workers.js?v=f0deb1d221";

// A machine seen from above as it starts, to load by hand: its gears, the
// contacts between them, and every slot, a carrier on it or not.  Clicking a
// slot puts a carrier on it or takes it off; two carriers on the same point
// are ringed at once, and where carriers met when it was made, too.
export const machineShapes = new Map();
export let machineWanted = null;

function askMachine(name) {
  machineWanted = name;
  if (machineShapes.has(name)) document.dispatchEvent(new CustomEvent("machine-shape"));
  else worker.postMessage({ type: "geometry", name });
}

function loadingText(loading) {
  return loading.map(([gear, slot]) => `${gear}:${slot}`).join(" ");
}

function readLoading(text) {
  return String(text)
    .split(/[\s,;]+/)
    .map((token) => token.match(/^([^:\s]+):(\d+)$/))
    .filter(Boolean)
    .map((m) => [m[1], Number(m[2])]);
}

export function attachMachine(holder) {
  const names = holder.querySelector("select[name=name]");
  const field = holder.querySelector("[name=carriers]");
  const label = field.closest("label");
  const box = document.createElement("div");
  box.className = "editor machine";
  const canvas = document.createElement("canvas");
  canvas.setAttribute("aria-label", "The machine from above: click a slot to put a carrier on it or take it off");
  const help = document.createElement("small");
  const own = document.createElement("button");
  own.type = "button";
  own.textContent = "Its own loading";
  const empty = document.createElement("button");
  empty.type = "button";
  empty.textContent = "Take all off";
  const buttons = document.createElement("div");
  buttons.className = "examples";
  buttons.append(own, empty);
  box.append(canvas, help, buttons);
  label.after(box);

  let view = null;
  const shape = () => machineShapes.get(names.value);
  const slotAt = (gear, slot) => {
    const angle = gear.offset + (2 * Math.PI * slot) / gear.slots;
    return [gear.x + gear.ride * Math.cos(angle), gear.y + gear.ride * Math.sin(angle)];
  };
  // The machine's own loading is its default: left as it is, it is not
  // written into the link.
  const fill = () => {
    const known = shape();
    if (!known) return;
    const mine = loadingText(known.loading);
    if (!field.value.trim() || field.value === field.dataset.default) field.value = mine;
    field.dataset.default = mine;
    draw();
  };
  const changed = () => field.dispatchEvent(new Event("input", { bubbles: true }));
  own.addEventListener("click", () => {
    field.value = field.dataset.default ?? "";
    changed();
  });
  empty.addEventListener("click", () => {
    field.value = "";
    changed();
  });
  field.addEventListener("input", () => {
    met = [];
    draw();
  });
  names.addEventListener("change", () => {
    field.value = "";
    met = [];
    askMachine(names.value);
    draw();
  });
  document.addEventListener("machine-shape", () => {
    if (canvas.isConnected) fill();
  });
  document.addEventListener("machine-met", (event) => {
    if (!canvas.isConnected) return;
    met = event.detail;
    draw();
  });
  let met = [];

  function draw() {
    if (!canvas.isConnected) return observer.disconnect();
    const known = shape();
    const style = getComputedStyle(document.documentElement);
    const muted = style.getPropertyValue("--muted").trim();
    const line = style.getPropertyValue("--line").trim();
    const error = style.getPropertyValue("--error").trim();
    if (!known) {
      help.textContent = "Drawing the machine…";
      view = null;
      return;
    }
    let lo = [Infinity, Infinity], hi = [-Infinity, -Infinity];
    for (const g of known.gears) {
      lo = [Math.min(lo[0], g.x - g.radius), Math.min(lo[1], g.y - g.radius)];
      hi = [Math.max(hi[0], g.x + g.radius), Math.max(hi[1], g.y + g.radius)];
    }
    // As wide as the panel, as tall as the machine needs.
    const wide = hi[0] - lo[0], tall = hi[1] - lo[1];
    const width = canvas.clientWidth || 300;
    const height = Math.round(Math.max(0.35, Math.min(1, (tall + 0.6) / (wide + 0.6))) * width);
    canvas.style.height = `${height}px`;
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    canvas.width = Math.round(width * ratio);
    canvas.height = Math.round(height * ratio);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, width, height);
    const scale = Math.min((width - 24) / wide, (height - 24) / tall);
    const cx = (lo[0] + hi[0]) / 2, cy = (lo[1] + hi[1]) / 2;
    // y up, as braidpy draws its machines.
    const X = (x) => width / 2 + (x - cx) * scale;
    const Y = (y) => height / 2 - (y - cy) * scale;
    const dot = Math.max(4, Math.min(8, scale * 0.14));
    ctx.lineWidth = 1;
    for (const g of known.gears) {
      ctx.strokeStyle = line;
      ctx.beginPath();
      ctx.arc(X(g.x), Y(g.y), g.radius * scale, 0, 2 * Math.PI);
      ctx.stroke();
      ctx.fillStyle = muted;
      ctx.font = "11px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(g.name, X(g.x), Y(g.y));
    }
    for (const c of known.contacts) {
      ctx.fillStyle = line;
      ctx.beginPath();
      ctx.arc(X(c.x), Y(c.y), 2, 0, 2 * Math.PI);
      ctx.fill();
    }
    const loading = readLoading(field.value);
    const index = new Map(loading.map(([g, slot], i) => [`${g}:${slot}`, i]));
    const places = [];
    for (const g of known.gears) {
      for (let slot = 0; slot < g.slots; slot++) {
        const [x, y] = slotAt(g, slot);
        const i = index.get(`${g.name}:${slot}`);
        places.push({ gear: g.name, slot, x: X(x), y: Y(y), carrier: i });
        ctx.beginPath();
        ctx.arc(X(x), Y(y), i === undefined ? dot * 0.55 : dot, 0, 2 * Math.PI);
        if (i === undefined) {
          ctx.strokeStyle = muted;
          ctx.stroke();
        } else {
          ctx.fillStyle = PALETTE[i % PALETTE.length];
          ctx.fill();
        }
      }
    }
    // Two carriers on the same point already, or where they met when made.
    const taken = places.filter((p) => p.carrier !== undefined);
    const clash = new Set();
    for (let a = 0; a < taken.length; a++) {
      for (let b = a + 1; b < taken.length; b++) {
        if (Math.hypot(taken[a].x - taken[b].x, taken[a].y - taken[b].y) < dot) {
          clash.add(taken[a]);
          clash.add(taken[b]);
        }
      }
    }
    for (const [g, slot] of met) {
      const p = places.find((q) => q.gear === g && q.slot === slot);
      if (p) clash.add(p);
    }
    ctx.strokeStyle = error;
    ctx.lineWidth = 2;
    for (const p of clash) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, dot * 1.9, 0, 2 * Math.PI);
      ctx.stroke();
    }
    view = { places, dot };
    const count = loading.length;
    help.textContent = clash.size && !met.length
      ? "Two carriers are on the same point, ringed: take one off."
      : met.length
        ? "Ringed: where carriers met, and the braiding stopped."
        : `${count} carrier${count === 1 ? "" : "s"} on ${known.gears.length} gears. Click a slot to put a carrier on it or take it off.`;
  }

  canvas.addEventListener("click", (event) => {
    if (!view) return;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left, y = event.clientY - rect.top;
    let best = null;
    for (const p of view.places) {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d < view.dot * 2.2 && (!best || d < best.d)) best = { ...p, d };
    }
    if (!best) return;
    const loading = readLoading(field.value);
    const at = loading.findIndex(([g, slot]) => g === best.gear && slot === best.slot);
    if (at >= 0) loading.splice(at, 1);
    else loading.push([best.gear, best.slot]);
    field.value = loadingText(loading);
    changed();
  });
  const observer = new ResizeObserver(draw);
  observer.observe(canvas);
  askMachine(names.value);
  draw();
}
