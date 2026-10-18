// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A braiding machine seen from above, to load it by hand and turn its handle:
// a click puts a carrier on a slot or takes it off, the handle turns it a
// step at a time, forwards or back, and carriers that meet are ringed.

import { PALETTE, strandColour } from "./colours.js";
import { worker } from "./workers.js";

// A machine seen from above, to load by hand: its gears, the contacts
// between them, and every slot, a carrier on it or not.  Clicking a slot
// puts a carrier on it or takes it off; two carriers on the same point are
// ringed at once, and where carriers met when it was made, too.
//
// Its handle turns it (braidpy.horn_gear.handle): what is turned is always
// the loading at step 0 — the carriers the machine braids with — so going
// back is turning one step fewer, and a carrier put on a slot at a later
// step is loaded where it would have come from.  braidpy says where every
// slot and carrier is (web.machine_turned), through the next step too, so
// a step is seen to turn.
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

// A step, turned smoothly: how long it takes, and how long Run waits
// between steps.
const SWEEP_MS = 360;
const RUN_PAUSE_MS = 60;

export function attachMachine(holder) {
  const names = holder.querySelector("select[name=name]");
  const field = holder.querySelector("[name=carriers]");
  const label = field.closest("label");
  const box = document.createElement("div");
  box.className = "editor machine";
  const canvas = document.createElement("canvas");
  canvas.setAttribute("aria-label", "The machine from above: click a slot to put a carrier on it or take it off");
  const help = document.createElement("small");
  const button = (text, title) => {
    const made = document.createElement("button");
    made.type = "button";
    made.textContent = text;
    if (title) made.title = title;
    return made;
  };
  const own = button("Its own loading");
  const empty = button("Take all off");
  const buttons = document.createElement("div");
  buttons.className = "examples";
  buttons.append(own, empty);
  // The handle.
  const start = button("⏮", "Back to step 0");
  const back = button("◀", "Turn the handle back a step");
  const forward = button("▶", "Turn the handle a step");
  const run = button("Run", "Turn the handle until carriers meet");
  const reading = document.createElement("span");
  reading.className = "step";
  const handle = document.createElement("div");
  handle.className = "examples handle";
  handle.append(start, back, forward, run, reading);
  box.append(canvas, help, handle, buttons);
  label.after(box);

  let view = null;
  let met = []; // where carriers met when the braid was made
  let time = 0; // how far the handle is turned
  let turned = null; // braidpy's answer for this machine, loading and step
  let asked = 0; // the newest question to braidpy
  let sweeping = null; // {from, started}: a step being turned
  let running = false;
  const shape = () => machineShapes.get(names.value);
  const slotAt = (gear, slot) => {
    const angle = gear.offset + (2 * Math.PI * slot) / gear.slots;
    return [gear.x + gear.ride * Math.cos(angle), gear.y + gear.ride * Math.sin(angle)];
  };

  // braidpy, asked where the machine is at a step.  An answer awaited is
  // handed to whoever awaits it; any other is shown if it answers the
  // newest question, and left unread if not.
  function ask(at) {
    asked += 1;
    worker.postMessage({
      type: "turn",
      id: asked,
      name: names.value,
      loading: readLoading(field.value),
      time: at,
    });
    return asked;
  }
  const waiting = new Map(); // id -> resolve
  document.addEventListener("machine-turned", ({ detail }) => {
    const resolve = waiting.get(detail.id);
    waiting.delete(detail.id);
    if (resolve) resolve(detail.turned);
    else if (detail.id === asked && canvas.isConnected) {
      turned = detail.turned;
      if (turned) time = turned.time;
      draw();
    }
  });
  const answer = (id) => new Promise((resolve) => waiting.set(id, resolve));
  const fresh = () => {
    turned = null;
    ask(time);
  };

  // The machine's own loading is its default: left as it is, it is not
  // written into the link.
  const fill = () => {
    const known = shape();
    if (!known) return;
    const mine = loadingText(known.loading);
    if (!field.value.trim() || field.value === field.dataset.default) field.value = mine;
    field.dataset.default = mine;
    fresh();
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
    fresh();
    draw();
  });
  names.addEventListener("change", () => {
    field.value = "";
    met = [];
    time = 0;
    running = false;
    turned = null;
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

  // A step forwards: turned smoothly through braidpy's pictures of it,
  // while braidpy works out the next; stopped where carriers meet.
  async function step() {
    if (!turned || turned.met.length || sweeping) return false;
    const from = turned;
    const next = answer(ask(from.time + 1));
    sweeping = { from, started: performance.now() };
    await new Promise((done) => {
      const frame = () => {
        draw();
        if (performance.now() - sweeping.started < SWEEP_MS) requestAnimationFrame(frame);
        else done();
      };
      requestAnimationFrame(frame);
    });
    const reached = await next;
    sweeping = null;
    // A new loading or machine meanwhile: that one is shown instead.
    if (turned !== from || !reached) {
      draw();
      return false;
    }
    turned = reached;
    time = reached.time;
    draw();
    return reached.time > from.time && !reached.met.length;
  }
  async function goTo(at) {
    running = false;
    const reached = await answer(ask(Math.max(0, at)));
    if (reached) {
      turned = reached;
      time = reached.time;
    }
    draw();
  }
  forward.addEventListener("click", () => {
    running = false;
    step();
  });
  back.addEventListener("click", () => goTo(time - 1));
  start.addEventListener("click", () => goTo(0));
  run.addEventListener("click", async () => {
    if (running) {
      running = false;
      draw();
      return;
    }
    running = true;
    draw();
    while (running && canvas.isConnected && (await step())) {
      await new Promise((wait) => setTimeout(wait, RUN_PAUSE_MS));
    }
    running = false;
    draw();
  });

  // Where every slot and carrier is to be drawn: braidpy's pictures of the
  // step, part way through it while it turns; until braidpy has said, the
  // machine as loaded, from its shape.
  function places(known) {
    const loading = readLoading(field.value);
    if (turned && turned.carriers.length === loading.length) {
      let picture = turned.frames[0];
      if (sweeping && sweeping.from === turned) {
        const done = Math.min(1, (performance.now() - sweeping.started) / SWEEP_MS);
        const last = turned.frames.length - 1;
        picture = turned.frames[Math.min(last, Math.floor(done * turned.frames.length))];
      }
      return {
        slots: turned.slots.map(([gear, slot], i) => ({
          gear,
          slot,
          x: picture.slots[i][0],
          y: picture.slots[i][1],
        })),
        carriers: turned.carriers.map(([gear, slot], i) => ({
          gear,
          slot,
          i,
          x: picture.carriers[i][0],
          y: picture.carriers[i][1],
        })),
        met: turned.met,
      };
    }
    const slots = [];
    for (const g of known.gears) {
      for (let slot = 0; slot < g.slots; slot++) {
        const [x, y] = slotAt(g, slot);
        slots.push({ gear: g.name, slot, x, y });
      }
    }
    const carriers = loading
      .map(([gear, slot], i) => {
        const at = slots.find((p) => p.gear === gear && p.slot === slot);
        return at && { ...at, i };
      })
      .filter(Boolean);
    return { slots, carriers, met: [] };
  }

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
      handle.hidden = true;
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
    const placed = places(known);
    const slots = placed.slots.map((p) => ({ ...p, x: X(p.x), y: Y(p.y) }));
    const carriers = placed.carriers.map((p) => ({ ...p, x: X(p.x), y: Y(p.y) }));
    const taken = new Set(carriers.map((c) => `${c.gear}:${c.slot}`));
    ctx.strokeStyle = muted;
    for (const p of slots) {
      if (taken.has(`${p.gear}:${p.slot}`)) continue;
      ctx.beginPath();
      ctx.arc(p.x, p.y, dot * 0.55, 0, 2 * Math.PI);
      ctx.stroke();
    }
    for (const c of carriers) {
      ctx.fillStyle = strandColour(c.i, PALETTE[c.i % PALETTE.length]);
      ctx.beginPath();
      ctx.arc(c.x, c.y, dot, 0, 2 * Math.PI);
      ctx.fill();
    }
    // Two carriers on the same point already; where the handle stopped
    // because carriers met; where they met when the braid was made.
    const clash = new Set();
    for (let a = 0; a < carriers.length; a++) {
      for (let b = a + 1; b < carriers.length; b++) {
        if (Math.hypot(carriers[a].x - carriers[b].x, carriers[a].y - carriers[b].y) < dot) {
          clash.add(carriers[a]);
          clash.add(carriers[b]);
        }
      }
    }
    const ringed = time === 0 ? [...placed.met, ...met] : placed.met;
    for (const [g, slot] of ringed) {
      for (const c of carriers) if (c.gear === g && c.slot === slot) clash.add(c);
    }
    ctx.strokeStyle = error;
    ctx.lineWidth = 2;
    for (const p of clash) {
      ctx.beginPath();
      ctx.arc(p.x, p.y, dot * 1.9, 0, 2 * Math.PI);
      ctx.stroke();
    }
    view = { slots, dot };

    const count = carriers.length;
    const stopped = placed.met.length > 0;
    const ready = Boolean(turned);
    handle.hidden = false;
    forward.disabled = !ready || stopped || Boolean(sweeping) || running;
    back.disabled = !ready || time === 0 || running;
    start.disabled = !ready || time === 0 || running;
    run.disabled = !ready || (stopped && !running);
    run.textContent = running ? "Stop" : "Run";
    reading.textContent = ready ? `Step ${time}` : "";
    const carried = `${count} carrier${count === 1 ? "" : "s"}`;
    help.textContent = stopped
      ? `Carriers met at step ${time}, ringed: take one off, or turn back.`
      : clash.size && !met.length
        ? "Two carriers are on the same point, ringed: take one off."
        : met.length && time === 0
          ? "Ringed: where carriers met, and the braiding stopped."
          : time > 0
            ? `Step ${time}: ${carried}. Click a slot to put a carrier on it or take one off: it is loaded where it would have come from.`
            : `${carried} on ${known.gears.length} gears. Click a slot to put a carrier on it or take it off.`;
  }

  canvas.addEventListener("click", async (event) => {
    if (!view || sweeping || running) return;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left, y = event.clientY - rect.top;
    let best = null;
    for (const p of view.slots) {
      const d = Math.hypot(p.x - x, p.y - y);
      if (d < view.dot * 2.2 && (!best || d < best.d)) best = { ...p, d };
    }
    if (!best) return;
    // At a later step, the slot at step 0 it would have come from.
    let place = [best.gear, best.slot];
    if (time > 0) {
      place = await new Promise((resolve) => {
        const heard = ({ detail }) => {
          document.removeEventListener("machine-origin", heard);
          resolve(detail.origin);
        };
        document.addEventListener("machine-origin", heard);
        worker.postMessage({ type: "origin", name: names.value, place, time });
      });
      if (!place) return;
    }
    const loading = readLoading(field.value);
    const at = loading.findIndex(([g, slot]) => g === place[0] && slot === place[1]);
    if (at >= 0) loading.splice(at, 1);
    else loading.push(place);
    field.value = loadingText(loading);
    changed();
  });
  const observer = new ResizeObserver(draw);
  observer.observe(canvas);
  document.addEventListener("strand-colours", draw);
  askMachine(names.value);
  draw();
}
