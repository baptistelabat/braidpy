// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A braiding machine seen from above, to load it by hand and turn its handle:
// a click puts a carrier on a slot or takes it off, the handle turns it a
// step at a time, forwards or back, and carriers that meet are ringed.

import { PALETTE, strandColour, trueColour } from "./colours.js";
import { inTime } from "./page.js";
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

// Where axial yarns are fed, as written (braidpy.horn_gear.described
// .read_axials): a gear, or a ring of gears in any order.
function readAxials(text) {
  return String(text)
    .split(/[\s,;]+/)
    .filter((token) => token && token !== "none");
}
const axialKey = (at) => at.split("-").sort().join("-");

// A place for an axial yarn: a ring round the gear's name, in carriers'
// sizes, dashed when no spool is loaded there; a click this many of its
// sizes from it reaches it.
const AXIAL_SIZE = 1.6;
const AXIAL_DASH = [3, 3];
const AXIAL_REACH = 1.2;

// A step, turned smoothly: how long it takes, and how long Run waits
// between steps.
const SWEEP_MS = 360;
const RUN_PAUSE_MS = 60;

export function attachMachine(holder) {
  const names = holder.querySelector("select[name=name]");
  const field = holder.querySelector("[name=carriers]");
  // Not on a lace machine, which feeds none.
  const axialField = holder.querySelector("[name=axials]");
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
  const nudge = button("▸", "Hold the handle part way through a step, so the two slots meeting at a contact come apart");
  const run = button("Run", "Turn the handle until carriers meet");
  const reading = document.createElement("span");
  reading.className = "step";
  const handle = document.createElement("div");
  handle.className = "examples handle";
  handle.append(start, back, forward, nudge, run, reading);
  box.append(canvas, help, handle, buttons);
  label.after(box);

  let view = null;
  let met = []; // where carriers met when the braid was made
  let time = 0; // how far the handle is turned
  let turned = null; // braidpy's answer for this machine, loading and step
  let asked = 0; // the newest question to braidpy
  let sweeping = null; // {from, started, at, ms}: a step being turned, from its picture at
  // Held part way through the step, so that the two slots at a contact --
  // which sit on the same point when the step is whole -- come apart and a
  // click can tell them from one another.  0 is the step itself.
  let part = 0;
  let standing = null; // {name, slots}: where the slots were last drawn
  let running = false;
  // A lace machine with a card of your own goes by its gears and card
  // (braidpy.web.machines.OWN_LACE), a horn gear machine of your own by its
  // slots and the gears that mesh (OWN_GEARS).
  const gears = holder.querySelector("[name=n_gears]");
  const card = holder.querySelector("[name=card]");
  const graph = holder.querySelector("[name=graph]");
  const slots = holder.querySelector("[name=n_slots]");
  const words = (input) => input.value.trim().split(/\s+/).join(" ");
  const machineName = () => {
    if (names.value !== "custom") return names.value;
    if (gears && card) return `lace:${gears.value}:${words(card)}`;
    if (graph && slots) return `gears:${slots.value}:${words(graph)}`;
    return names.value;
  };
  const shape = () => machineShapes.get(machineName());
  const slotAt = (gear, slot) => {
    const angle = gear.angles[slot];
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
      name: machineName(),
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
  // Asked again, the loading having changed.  Where the handle is held --
  // the step, and how far through it -- is about where the gears stand, not
  // which slots have carriers on them, so putting one on leaves it alone.
  const fresh = () => {
    turned = null;
    ask(time);
  };

  // The machine's own loading is its default: left as it is, it is not
  // written into the link.
  const fill = () => {
    const known = shape();
    if (!known) return;
    if (known.error) return draw();
    const mine = loadingText(known.loading);
    if (!field.value.trim() || field.value === field.dataset.default) field.value = mine;
    field.dataset.default = mine;
    if (axialField) {
      const fed = known.own_axials.join(" ");
      if (!axialField.value.trim() || axialField.value === axialField.dataset.default) axialField.value = fed;
      axialField.dataset.default = fed;
    }
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
  axialField?.addEventListener("input", () => draw());
  const another = () => {
    field.value = "";
    if (axialField) axialField.value = "";
    met = [];
    time = 0;
    part = 0;
    standing = null;
    running = false;
    turned = null;
    askMachine(machineName());
    draw();
  };
  // Your own machine starts from the one drawn before, written as the gears
  // that mesh (braidpy.web.machines.machine_geometry's graph).
  let drawnBefore = names.value;
  names.addEventListener("change", () => {
    if (names.value !== "custom") drawnBefore = names.value;
    else if (graph && slots) {
      const from = machineShapes.get(drawnBefore)?.graph;
      if (from) {
        graph.value = from.graph;
        slots.value = String(from.n_slots);
      }
    }
    another();
  });
  // Your own card or gears: another machine with every change to them —
  // once the list has turned to "Your own…", as it does on the same change.
  for (const input of [gears, card, graph, slots]) input?.addEventListener("input", () => queueMicrotask(another));
  document.addEventListener("machine-shape", () => {
    if (canvas.isConnected) fill();
  });
  document.addEventListener("machine-met", (event) => {
    if (!canvas.isConnected) return;
    met = event.detail;
    draw();
  });

  // A step forwards: turned smoothly through braidpy's pictures of it,
  // while braidpy works out the next; stopped where carriers meet.  Held
  // part way through it, the handle turns on from there, through what is
  // left of the step, in as much of the time.
  async function step() {
    if (!turned || turned.met.length || sweeping) return false;
    const from = turned;
    const next = answer(ask(from.time + 1));
    const count = from.frames.length;
    const at = Math.min(part, count - 1);
    sweeping = { from, started: performance.now(), at, ms: (SWEEP_MS * (count - at)) / count };
    await new Promise((done) => {
      const frame = () => {
        draw();
        if (performance.now() - sweeping.started < sweeping.ms) requestAnimationFrame(frame);
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
    part = 0;
    draw();
    return reached.time > from.time && !reached.met.length;
  }
  async function goTo(at) {
    running = false;
    part = 0;
    const reached = await answer(ask(Math.max(0, at)));
    if (reached) {
      turned = reached;
      time = reached.time;
    }
    draw();
  }
  // A step on: from where the handle is held, if it is, to the next step.
  forward.addEventListener("click", (event) => {
    if (!inTime(event)) return;
    running = false;
    step();
  });
  // Each press holds the handle a quarter of a step further on; past the
  // last, the step itself is taken and the handle sits on a whole step
  // again.  A quarter, because the two slots at a contact are furthest
  // apart half way through -- so the second press is the one to click on.
  nudge.addEventListener("click", (event) => {
    if (!inTime(event)) return;
    running = false;
    if (!turned || turned.met.length || sweeping) return;
    const by = Math.max(1, Math.round(turned.frames.length / 4));
    if (part + by < turned.frames.length) {
      part += by;
      draw();
    } else {
      // On through the rest of the step, from where it is held.
      step();
    }
  });
  back.addEventListener("click", (event) => inTime(event) && goTo(time - 1));
  start.addEventListener("click", (event) => inTime(event) && goTo(0));
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
      let picture = turned.frames[Math.min(part, turned.frames.length - 1)];
      if (sweeping && sweeping.from === turned) {
        const done = Math.min(1, (performance.now() - sweeping.started) / sweeping.ms);
        const count = turned.frames.length;
        const at = sweeping.at + Math.floor(done * (count - sweeping.at));
        picture = turned.frames[Math.min(count - 1, at)];
      }
      standing = {
        name: names.value,
        slots: turned.slots.map(([gear, slot], i) => ({
          gear,
          slot,
          x: picture.slots[i][0],
          y: picture.slots[i][1],
        })),
      };
      return {
        slots: standing.slots,
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
    // Where the slots stand does not depend on which of them carry, so
    // while braidpy answers about a loading just changed, the ones already
    // drawn still hold -- and the handle does not appear to let go.
    const slots =
      standing && standing.name === names.value
        ? standing.slots
        : known.gears.flatMap((g) =>
            Array.from({ length: g.slots }, (_, slot) => {
              const [x, y] = slotAt(g, slot);
              return { gear: g.name, slot, x, y };
            }),
          );
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
    if (known?.error) {
      help.textContent = known.error;
      view = null;
      handle.hidden = true;
      return;
    }
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
    }
    for (const c of known.contacts) {
      ctx.fillStyle = line;
      ctx.beginPath();
      ctx.arc(X(c.x), Y(c.y), 2, 0, 2 * Math.PI);
      ctx.fill();
    }
    // Where axial yarns may be fed: a spool, in the cores' colour, where one
    // is loaded.
    const fed = new Set(readAxials(axialField?.value ?? "").map(axialKey));
    const spots = axialField
      ? known.axials.map((s) => ({ ...s, x: X(s.x), y: Y(s.y), loaded: fed.has(axialKey(s.at)) }))
      : [];
    for (const s of spots) {
      ctx.beginPath();
      ctx.arc(s.x, s.y, dot * AXIAL_SIZE, 0, 2 * Math.PI);
      if (s.loaded) {
        // Ringed, so as not to be taken for a carrier of the same grey.
        ctx.fillStyle = known.core_colour;
        ctx.fill();
        ctx.strokeStyle = muted;
        ctx.stroke();
      } else {
        ctx.setLineDash(AXIAL_DASH);
        ctx.strokeStyle = known.core_colour;
        ctx.stroke();
        ctx.setLineDash([]);
      }
    }
    // The gears' names, over a spool at their centre.
    ctx.font = "11px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    for (const g of known.gears) {
      ctx.fillStyle = muted;
      ctx.fillText(g.name, X(g.x), Y(g.y));
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
      // In the colour its yarn was made in: the machine may choose its own.
      ctx.fillStyle = strandColour(c.i, trueColour(c.i, PALETTE[c.i % PALETTE.length]));
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
    view = { slots, spots, dot };

    const count = carriers.length;
    const stopped = placed.met.length > 0;
    const ready = Boolean(turned);
    handle.hidden = false;
    forward.disabled = !ready || stopped || Boolean(sweeping) || running;
    back.disabled = !ready || time === 0 || running;
    start.disabled = !ready || time === 0 || running;
    run.disabled = !ready || (stopped && !running);
    run.textContent = running ? "Stop" : "Run";
    nudge.disabled = forward.disabled;
    const parts = turned ? turned.frames.length : 1;
    reading.textContent = ready
      ? part
        ? `Step ${time} and ${part}/${parts}`
        : `Step ${time}`
      : "";
    const carried = `${count} carrier${count === 1 ? "" : "s"}`;
    help.textContent = stopped
      ? `Carriers met at step ${time}, ringed: take one off, or turn back.`
      : clash.size && !met.length
        ? "Two carriers are on the same point, ringed: take one off."
        : met.length && time === 0
          ? "Ringed: where carriers met, and the braiding stopped."
          : time > 0
            ? `Step ${time}: ${carried}. Click a slot to put a carrier on it or take one off: it is loaded where it would have come from.`
            : `${carried} on ${known.gears.length} gears. Click a slot to put a carrier on it or take it off${spots.length ? ", a dashed ring to load an axial yarn there or take it off" : ""}.`;
  }

  canvas.addEventListener("click", async (event) => {
    if (!view || sweeping || running) return;
    const rect = canvas.getBoundingClientRect();
    const x = event.clientX - rect.left, y = event.clientY - rect.top;
    // A spool for an axial yarn, put on or taken off.
    const spot = view.spots.find((s) => Math.hypot(s.x - x, s.y - y) < view.dot * AXIAL_SIZE * AXIAL_REACH);
    if (spot) {
      const fed = readAxials(axialField.value).filter((at) => axialKey(at) !== axialKey(spot.at));
      if (!spot.loaded) fed.push(spot.at);
      axialField.value = fed.join(" ");
      axialField.dispatchEvent(new Event("input", { bubbles: true }));
      return;
    }
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
        worker.postMessage({ type: "origin", name: machineName(), place, time });
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
  askMachine(machineName());
  draw();
}
