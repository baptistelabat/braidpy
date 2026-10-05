// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Working a braiding machine by hand.
//
// The page holds the carriers and the step number; braidpy holds everything
// else.  Stepping forward asks it where the carriers go and whether any two
// have met; stepping back pops the state off a stack, which is what makes the
// handle turn both ways without the machine needing to run in reverse.

const SVG = "http://www.w3.org/2000/svg";
// The same Pyodide the rest of the site uses, overridable the same way.
const PYODIDE =
  new URLSearchParams(location.search).get("pyodide") ||
  "https://cdn.jsdelivr.net/pyodide/v0.27.8/full/";
// Stepping by hand shows the step in a few distinct poses, so the way a gear
// turns can be read off its slots moving even with nothing riding them.
const SUBSTEPS = 3;
const SUBSTEP_MS = 70;
// Running glides instead, a step every STEP_MS, drawn every frame the browser
// offers rather than in poses.
const STEP_MS = 420;

const view = document.getElementById("view");
const statusLine = document.getElementById("status");
const stepOut = document.getElementById("step");
const countOut = document.getElementById("count");
const machineBox = document.getElementById("machine");
const buttons = {
  back: document.getElementById("back"),
  play: document.getElementById("play"),
  forward: document.getElementById("forward"),
  reload: document.getElementById("reload"),
  clear: document.getElementById("clear"),
  rewind: document.getElementById("rewind"),
};

let worker = null;
let nextId = 1;
const waiting = new Map();

let shape = null; // the machine's geometry, sent once
let carriers = []; // [[gear, slot], ...]
let time = 0;
let past = []; // {carriers, time} before each step taken
let clashes = []; // what braidpy last reported as met
let running = false; // true while the handle is turning itself
let frac = 0; // how far into the current step the drawing is, 0 to 1

function say(text) {
  statusLine.textContent = text;
}

function ask(message) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    waiting.set(id, { resolve, reject });
    worker.postMessage({ ...message, id });
  });
}

function startWorker() {
  worker = new Worker("console_worker.js");
  worker.onmessage = (event) => {
    const message = event.data;
    if (message.type === "status") {
      say(message.text);
      return;
    }
    if (message.type === "ready") {
      for (const entry of message.catalogue) {
        const option = document.createElement("option");
        option.value = entry.id;
        option.textContent = entry.title;
        machineBox.append(option);
      }
      machineBox.disabled = false;
      machineBox.value = "multiband_10_15_10";
      load(machineBox.value);
      return;
    }
    const pending = waiting.get(message.id);
    if (!pending) {
      // Nothing is waiting on it, so it came from starting up: say it rather
      // than leave the page sitting on "Loading…" for ever.
      if (message.type === "error") say(`braidpy could not start: ${message.message}`);
      return;
    }
    waiting.delete(message.id);
    if (message.type === "error") pending.reject(new Error(message.message));
    else pending.resolve(message.result);
  };
  worker.postMessage({ type: "init", pyodideUrl: PYODIDE });
}

async function load(name) {
  stop();
  enable(false);
  say("Reading the machine…");
  try {
    shape = await ask({ type: "geometry", name });
  } catch (error) {
    say(`Could not read the machine: ${error.message}`);
    return;
  }
  carriers = shape.loading.map((p) => [p[0], p[1]]);
  time = 0;
  frac = 0;
  past = [];
  clashes = [];
  draw();
  enable(true);
  say(
    `${shape.title}: ${shape.gears.length} gears, ` +
      `${totalSlots()} slots. Click a slot to add or remove a carrier.`,
  );
}

function totalSlots() {
  return shape.gears.reduce((sum, gear) => sum + gear.slots, 0);
}

function enable(on) {
  for (const button of Object.values(buttons)) button.disabled = !on;
}

// Where a slot sits at the current step.  The gear turns `direction` slots a
// step; the slot index itself is not mirrored.
function slotAt(gear, slot) {
  const angle =
    gear.offset +
    (2 * Math.PI * (slot + gear.direction * (time + frac))) / gear.slots;
  return [
    gear.x + gear.ride * Math.cos(angle),
    gear.y + gear.ride * Math.sin(angle),
  ];
}

function held(gearName, slot) {
  return carriers.some((c) => c[0] === gearName && c[1] === slot);
}

function clashed(gearName, slot) {
  return clashes.some((c) => c.gear === gearName && c.slot === slot);
}

function draw() {
  view.replaceChildren();

  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const gear of shape.gears) {
    minX = Math.min(minX, gear.x - gear.radius);
    maxX = Math.max(maxX, gear.x + gear.radius);
    minY = Math.min(minY, gear.y - gear.radius);
    maxY = Math.max(maxY, gear.y + gear.radius);
  }
  const pad = 0.6;
  // y is flipped so the drawing matches braidpy's own figures
  view.setAttribute(
    "viewBox",
    `${minX - pad} ${-maxY - pad} ${maxX - minX + 2 * pad} ${maxY - minY + 2 * pad}`,
  );

  const scene = document.createElementNS(SVG, "g");
  scene.setAttribute("transform", "scale(1,-1)");
  scene.id = "scene";

  const switchedGears = new Set();
  for (const contact of shape.contacts) {
    if (!contact.switched) continue;
    switchedGears.add(contact.a);
    switchedGears.add(contact.b);
  }

  for (const gear of shape.gears) {
    const circle = document.createElementNS(SVG, "circle");
    circle.setAttribute("cx", gear.x);
    circle.setAttribute("cy", gear.y);
    circle.setAttribute("r", gear.radius);
    circle.setAttribute(
      "class",
      switchedGears.has(gear.name) ? "gear gear-switched" : "gear",
    );
    scene.append(circle);
  }

  for (const contact of shape.contacts) {
    const mark = document.createElementNS(SVG, "circle");
    mark.setAttribute("cx", contact.x);
    mark.setAttribute("cy", contact.y);
    mark.setAttribute("r", contact.switched ? 0.17 : 0.1);
    mark.setAttribute(
      "class",
      contact.switched ? "contact contact-switched" : "contact",
    );
    scene.append(mark);
  }

  for (const gear of shape.gears) {
    for (let slot = 0; slot < gear.slots; slot += 1) {
      const [x, y] = slotAt(gear, slot);
      const taken = held(gear.name, slot);
      const dot = document.createElementNS(SVG, "circle");
      dot.setAttribute("cx", x);
      dot.setAttribute("cy", y);
      dot.setAttribute("r", taken ? 0.17 : 0.1);
      dot.setAttribute("class", taken ? "carrier" : "slot");
      dot.dataset.gear = gear.name;
      dot.dataset.slot = String(slot);
      const label = document.createElementNS(SVG, "title");
      label.textContent = `${gear.name} slot ${slot}${taken ? " — carrier" : ""}`;
      dot.append(label);
      scene.append(dot);

      if (clashed(gear.name, slot)) {
        const ring = document.createElementNS(SVG, "circle");
        ring.setAttribute("cx", x);
        ring.setAttribute("cy", y);
        ring.setAttribute("r", 0.34);
        ring.setAttribute("class", "clash");
        scene.append(ring);
      }
    }
  }

  for (const gear of shape.gears) {
    const text = document.createElementNS(SVG, "text");
    text.setAttribute("x", gear.x);
    text.setAttribute("y", -gear.y);
    text.setAttribute("class", "gear-label");
    text.setAttribute("transform", "scale(1,-1)");
    text.textContent = `${gear.name}·${gear.slots}`;
    scene.append(text);
  }

  view.append(scene);
  stepOut.textContent = String(time);
  countOut.textContent = String(carriers.length);
}

view.addEventListener("click", (event) => {
  const target = event.target.closest("[data-gear]");
  if (!target || !shape) return;
  toggle(target.dataset.gear, Number(target.dataset.slot));
});

async function toggle(gearName, slot) {
  stop();
  const at = carriers.findIndex((c) => c[0] === gearName && c[1] === slot);
  if (at >= 0) carriers.splice(at, 1);
  else carriers.push([gearName, slot]);
  // Editing forks the past: what came before no longer leads here.
  past = [];
  await check(
    at >= 0
      ? `Took the carrier off ${gearName} slot ${slot}.`
      : `Put a carrier on ${gearName} slot ${slot}.`,
  );
}

async function check(prefix) {
  try {
    clashes = await ask({
      type: "trouble",
      name: shape.name,
      carriers,
      time,
    });
  } catch (error) {
    say(`braidpy could not check it: ${error.message}`);
    return;
  }
  draw();
  if (clashes.length) {
    say(`${prefix} Two carriers are on the same point — ringed in red.`);
  } else {
    say(`${prefix} ${carriers.length} carriers, nothing meeting.`);
  }
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// Sweep the drawing from one step's pose to the next, so the gears are seen
// to turn.  The carriers stay on the slots they are riding while it does --
// they only change gear at the end of the step, which is where braidpy moves
// them.
async function sweep(from, to) {
  for (let n = 1; n <= SUBSTEPS; n += 1) {
    frac = from + ((to - from) * n) / SUBSTEPS;
    draw();
    if (n < SUBSTEPS) await sleep(SUBSTEP_MS);
  }
}

// The same sweep, but drawn every frame the browser gives us, for running.
function glide(ms) {
  return new Promise((resolve) => {
    const started = performance.now();
    function frame(now) {
      const gone = Math.min(1, (now - started) / ms);
      frac = gone;
      draw();
      if (gone < 1 && running) requestAnimationFrame(frame);
      else resolve();
    }
    requestAnimationFrame(frame);
  });
}

async function forward(smooth = false) {
  if (!shape) return false;
  let answer;
  try {
    answer = await ask({
      type: "advance",
      name: shape.name,
      carriers,
      time,
    });
  } catch (error) {
    stop();
    say(`braidpy could not step it: ${error.message}`);
    return false;
  }
  if (smooth) await glide(STEP_MS);
  else await sweep(0, 1);
  past.push({ carriers: carriers.map((c) => c.slice()), time });
  carriers = answer.carriers.map((p) => [p[0], p[1]]);
  time = answer.time;
  frac = 0;
  clashes = answer.collisions;
  draw();
  if (clashes.length) {
    stop();
    const who = clashes
      .map((c) => `${c.gear} slot ${c.slot}`)
      .join(" and ");
    say(`Stopped at step ${time}: carriers meet at ${who}. Click one to take it off.`);
    return false;
  }
  say(`Step ${time}.`);
  return true;
}

async function back() {
  if (!past.length) {
    say("Nothing to go back to.");
    return;
  }
  const was = past.pop();
  carriers = was.carriers.map((c) => c.slice());
  time = was.time;
  clashes = [];
  // The pose at frac 1 of the earlier step is the one just left, so sweeping
  // down from it runs the same motion backwards.
  frac = 1;
  await sweep(1, 0);
  frac = 0;
  draw();
  say(`Back to step ${time}.`);
}

function stop() {
  if (running) {
    running = false;
    buttons.play.textContent = "▶ Run";
  }
}

// One step at a time, each swept through its substeps, rather than a timer
// that might fire again before the last step has finished drawing.
async function play() {
  if (running) {
    stop();
    say(`Stopped at step ${time}.`);
    return;
  }
  running = true;
  buttons.play.textContent = "❚❚ Stop";
  while (running) {
    const fine = await forward(true);
    if (!fine) {
      stop();
      return;
    }
  }
}

buttons.forward.addEventListener("click", () => {
  stop();
  forward();
});
buttons.back.addEventListener("click", () => {
  stop();
  back();
});
buttons.play.addEventListener("click", play);
buttons.reload.addEventListener("click", async () => {
  stop();
  carriers = shape.loading.map((p) => [p[0], p[1]]);
  time = 0;
  frac = 0;
  past = [];
  await check("Back to the suggested loading.");
});
buttons.clear.addEventListener("click", async () => {
  stop();
  carriers = [];
  past = [];
  await check("Machine empty.");
});
buttons.rewind.addEventListener("click", async () => {
  stop();
  time = 0;
  frac = 0;
  past = [];
  await check("Back to step 0.");
});
machineBox.addEventListener("change", () => load(machineBox.value));

startWorker();
