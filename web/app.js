// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Braid Studio: describe a braid, and braidpy — running in a worker through
// Pyodide — lays and tightens it; three.js draws it here.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { OBJExporter } from "three/addons/exporters/OBJExporter.js";
import { STLExporter } from "three/addons/exporters/STLExporter.js";

const PYODIDE_URL =
  new URLSearchParams(location.search).get("pyodide") ||
  "https://cdn.jsdelivr.net/pyodide/v0.27.8/full/";

const $ = (id) => document.getElementById(id);

// ------------------------------------------------------------------ fields

// What each source asks for.  ``entries`` and ``examples`` come from
// braidpy's own catalogue once it has loaded.
const FIELDS = {
  word: [
    {
      name: "word",
      label: "Braid word",
      kind: "textarea",
      hint: "Signed generators — 1 -2 — or s1 s2^-1, or letters, aB.",
    },
    { name: "n_strands", label: "Strands", kind: "number", min: 2, max: 32 },
    { name: "repeat", label: "Repeat", kind: "number", min: 1, max: 50 },
  ],
  kumihimo: [
    {
      name: "pattern",
      label: "Moves",
      kind: "text",
      hint: "S swaps the top and bottom strands, R turns the disk a quarter.",
    },
    { name: "n_strands", label: "Strands", kind: "number", min: 4, max: 32, step: 4 },
    { name: "repeat", label: "Repeat", kind: "number", min: 1, max: 50 },
  ],
  mobidai: [
    { name: "name", label: "Braid", kind: "entries" },
    {
      name: "slots",
      label: "Strands start in slots",
      kind: "text",
      custom: true,
      hint: "One slot per strand; slots are numbered clockwise from the top.",
    },
    {
      name: "moves",
      label: "Moves, in order",
      kind: "textarea",
      custom: true,
      hint: "From slot > to slot, for example 1>15, 17>31. A strand goes the short way round, over the strands it passes.",
    },
    { name: "n_slots", label: "Slots", kind: "number", min: 3, max: 128, custom: true },
    {
      name: "shift",
      label: "Turn after a cycle",
      kind: "number",
      min: -128,
      max: 128,
      custom: true,
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 40 },
  ],
  sinnet: [
    { name: "name", label: "Sinnet", kind: "entries" },
    {
      name: "counts",
      label: "Strands in each space",
      kind: "text",
      custom: true,
      hint: "Spaces are numbered anticlockwise from the left.",
    },
    {
      name: "moves",
      label: "Moves, in order",
      kind: "textarea",
      custom: true,
      hint: "From space > to space. Odd spaces send their right-hand strand anticlockwise, even spaces their left-hand one clockwise, over all.",
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 12 },
  ],
  machine: [
    { name: "name", label: "Machine", kind: "entries" },
    {
      name: "cores",
      label: "Cores",
      kind: "choice",
      choices: [
        ["yarn", "Yarn: gives way to the yarns braided round it"],
        ["rigid", "Rigid: stays straight"],
      ],
      hint: "For a machine that braids round cores.",
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 8 },
  ],
};

let catalogue = null;

function renderFields(source, values = {}) {
  const about = catalogue[source];
  const defaults = { ...about.defaults, ...values };
  const holder = $("fields");
  holder.replaceChildren();
  const numbers = [];
  for (const field of FIELDS[source]) {
    const label = document.createElement("label");
    label.className = "field";
    const title = document.createElement("span");
    title.textContent = field.label;
    label.append(title);
    let input;
    if (field.kind === "entries") {
      input = document.createElement("select");
      for (const entry of about.entries) {
        const option = new Option(entry.title, entry.name);
        input.append(option);
      }
    } else if (field.kind === "choice") {
      input = document.createElement("select");
      for (const [value, text] of field.choices) input.append(new Option(text, value));
    } else if (field.kind === "textarea") {
      input = document.createElement("textarea");
      input.rows = 2;
      input.spellcheck = false;
    } else {
      input = document.createElement("input");
      input.type = field.kind;
      if (field.kind === "text") input.spellcheck = false;
      for (const key of ["min", "max", "step"]) {
        if (field[key] !== undefined) input[key] = field[key];
      }
    }
    input.name = field.name;
    input.id = `field-${field.name}`;
    if (defaults[field.name] !== undefined) input.value = defaults[field.name];
    label.append(input);
    if (field.hint) {
      const hint = document.createElement("small");
      hint.textContent = field.hint;
      label.append(hint);
    }
    if (field.custom) label.dataset.custom = "";
    if (field.kind === "number") numbers.push(label);
    else holder.append(label);
  }
  if (numbers.length) {
    const row = document.createElement("div");
    row.className = "row";
    row.append(...numbers);
    holder.append(row);
  }
  // "Your own moves…" shows what a catalogued braid is made of, ready to
  // change: it starts from the braid chosen before.
  const entries = holder.querySelector("select[name=name]");
  if (entries) {
    let previous = entries.value;
    const reveal = () => {
      const custom = entries.value === "custom";
      for (const label of holder.querySelectorAll("[data-custom]")) {
        label.hidden = !custom;
      }
      if (custom) {
        const from = about.entries.find((entry) => entry.name === previous);
        for (const [key, value] of Object.entries(from?.pattern || {})) {
          const input = holder.querySelector(`[name=${key}]`);
          if (input && (input.value === "" || from)) input.value = value;
        }
      } else {
        previous = entries.value;
      }
    };
    entries.addEventListener("change", reveal);
    if (entries.value === "custom") {
      for (const label of holder.querySelectorAll("[data-custom]")) {
        label.hidden = false;
      }
    } else {
      for (const label of holder.querySelectorAll("[data-custom]")) {
        label.hidden = true;
      }
    }
  }
  if (source === "mobidai" || source === "sinnet") attachEditor(source, holder);
  if (source === "word") attachDiagram(holder);
  if (about.examples) {
    const examples = document.createElement("div");
    examples.className = "examples";
    for (const example of about.examples) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = example.title;
      button.addEventListener("click", () => {
        renderFields(source, example);
        submit();
      });
      examples.append(button);
    }
    holder.append(examples);
  }
}

// ----------------------------------------------------------------- diagram

// The braid word drawn as it is typed, before it is made: strands running
// down the page, the one passing behind broken where they cross.  σᵢ takes
// strand i over strand i + 1, as braidpy draws it.

// The colours braidpy gives a word's strands (web._PALETTE).
const PALETTE = [
  "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#a65628",
  "#f781bf", "#999999", "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
];

// braidpy.web.parse_word, in JavaScript: 1 -2, s1 s2^-1 or aB.
function parseWord(text) {
  text = text.trim();
  if (!text) return [];
  if (/^[A-Za-z]+$/.test(text) && !/[sσ]\d/.test(text)) {
    return [...text].map((c) =>
      c === c.toLowerCase() ? c.charCodeAt(0) - 96 : -(c.charCodeAt(0) - 64),
    );
  }
  const word = [];
  for (const token of text.split(/[\s,;.]+/)) {
    if (!token) continue;
    if (/^[+-]?\d+$/.test(token)) {
      word.push(Number(token));
      continue;
    }
    const named = token.match(/^[sσ](\d+)(\^?\(?(-?1)\)?)?$/);
    if (!named) throw new Error(`Cannot read “${token}” as a generator.`);
    word.push(named[3] === "-1" ? -Number(named[1]) : Number(named[1]));
  }
  if (word.some((g) => g === 0)) throw new Error("Generators are numbered from 1.");
  return word;
}

function attachDiagram(holder) {
  const wordField = holder.querySelector("[name=word]");
  const strandsField = holder.querySelector("[name=n_strands]");
  const figure = document.createElement("div");
  figure.className = "diagram";
  const canvas = document.createElement("canvas");
  const caption = document.createElement("small");
  figure.append(canvas, caption);
  wordField.closest("label").after(figure);
  const draw = () => drawDiagram(canvas, caption, wordField.value, Number(strandsField.value));
  wordField.addEventListener("input", draw);
  strandsField.addEventListener("input", draw);
  new ResizeObserver(() => {
    if (!canvas.isConnected) return;
    draw();
  }).observe(figure);
  draw();
}

function drawDiagram(canvas, caption, text, strands) {
  let word;
  try {
    word = parseWord(text);
    caption.textContent = "";
  } catch (error) {
    caption.textContent = error.message;
    canvas.hidden = true;
    return;
  }
  const needed = word.length ? Math.max(...word.map(Math.abs)) + 1 : 2;
  const n = Math.max(needed, Number.isFinite(strands) ? strands : 0, 2);
  canvas.hidden = !word.length;
  if (!word.length) return;
  if (n > (Number.isFinite(strands) ? strands : n)) {
    caption.textContent = `σ${needed - 1} needs ${needed} strands: drawn with ${n}.`;
  }
  const width = canvas.parentElement.clientWidth;
  const row = Math.max(6, Math.min(28, 360 / word.length));
  const height = row * (word.length + 1);
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  const column = Math.min(44, (width - 24) / n);
  const left = (width - column * (n - 1)) / 2;
  const X = (slot) => left + slot * column;
  const lineWidth = Math.max(1.5, Math.min(3, column / 8));
  const background = getComputedStyle(canvas).backgroundColor;
  // Which strand is in each slot, row by row.
  let order = [...Array(n).keys()];
  ctx.lineCap = "round";
  const stroke = (strand, from, to, y, wide) => {
    ctx.beginPath();
    ctx.moveTo(X(from), y);
    ctx.bezierCurveTo(X(from), y + row / 2, X(to), y + row / 2, X(to), y + row);
    ctx.strokeStyle = wide ? background : PALETTE[strand % PALETTE.length];
    ctx.lineWidth = wide ? lineWidth * 3.5 : lineWidth;
    ctx.stroke();
  };
  word.forEach((g, k) => {
    const y = row / 2 + k * row;
    const i = Math.abs(g) - 1;
    for (let slot = 0; slot < n; slot++) {
      if (slot !== i && slot !== i + 1) stroke(order[slot], slot, slot, y);
    }
    // σᵢ: the strand in slot i passes over; its inverse, under.
    const [under, over] = g > 0 ? [i + 1, i] : [i, i + 1];
    stroke(order[under], under, under === i ? i + 1 : i, y);
    stroke(order[over], over, over === i ? i + 1 : i, y, true);
    stroke(order[over], over, over === i ? i + 1 : i, y);
    [order[i], order[i + 1]] = [order[i + 1], order[i]];
  });
}

// ------------------------------------------------------------------ editor

// Your own moves, made by clicking: a strand (or a space), then where it
// goes.  The moves typed in and the disk drawn here are the same list.

function hue(i, n) {
  return `hsl(${(360 * i) / Math.max(n, 1)}, 100%, 50%)`;
}

function pairs(text) {
  const numbers = (String(text).match(/\d+/g) || []).map(Number);
  const out = [];
  for (let i = 0; i + 1 < numbers.length; i += 2) out.push([numbers[i], numbers[i + 1]]);
  return out;
}

function attachEditor(source, holder) {
  const moves = holder.querySelector("[name=moves]");
  const label = moves.closest("label");
  const box = document.createElement("div");
  box.className = "editor";
  box.dataset.custom = "";
  box.hidden = label.hidden;
  const canvas = document.createElement("canvas");
  canvas.setAttribute(
    "aria-label",
    source === "mobidai"
      ? "The disk: click a strand, then the slot it goes to"
      : "The spaces: click a space to move from, then one to move to",
  );
  const help = document.createElement("small");
  const undo = document.createElement("button");
  undo.type = "button";
  undo.textContent = "Undo move";
  const clear = document.createElement("button");
  clear.type = "button";
  clear.textContent = "Clear moves";
  const buttons = document.createElement("div");
  buttons.className = "examples";
  buttons.append(undo, clear);
  box.append(canvas, help, buttons);
  label.after(box);

  let chosen = null;
  const add = (from, to) => {
    const list = moves.value.trim();
    moves.value = (list ? list + ", " : "") + `${from}>${to}`;
    chosen = null;
    draw();
  };
  undo.addEventListener("click", () => {
    const list = pairs(moves.value);
    list.pop();
    moves.value = list.map(([a, b]) => `${a}>${b}`).join(", ");
    chosen = null;
    draw();
  });
  clear.addEventListener("click", () => {
    moves.value = "";
    chosen = null;
    draw();
  });

  // What there is to draw and click: places round a circle, and who is
  // where once every move so far is made.
  function state() {
    if (source === "mobidai") {
      const n = Math.max(3, Number(holder.querySelector("[name=n_slots]").value) || 32);
      const start = (holder.querySelector("[name=slots]").value.match(/\d+/g) || []).map(Number);
      const at = new Map(start.map((slot, i) => [slot, i]));
      for (const [from, to] of pairs(moves.value)) {
        if (!at.has(from) || at.has(to)) continue;
        at.set(to, at.get(from));
        at.delete(from);
      }
      return { n, at, strands: start.length };
    }
    const counts = (holder.querySelector("[name=counts]").value.match(/\d+/g) || []).map(Number);
    const groups = [];
    let next = 0;
    for (const count of counts) {
      groups.push(Array.from({ length: count }, () => next++));
    }
    for (const [from, to] of pairs(moves.value)) {
      const leaving = groups[from - 1];
      const joining = groups[to - 1];
      if (!leaving || !joining || !leaving.length || from === to) continue;
      const mover = from % 2 ? leaving.pop() : leaving.shift();
      if (to % 2) joining.unshift(mover);
      else joining.push(mover);
    }
    return { n: counts.length, groups, strands: next };
  }

  // Where a place is on the canvas: a disk's slots clockwise from the top,
  // half a slot round, as the page draws it; a sinnet's spaces
  // anticlockwise from the left, as the book does.
  function place(index, n, size, fraction = 0.5) {
    const turn =
      source === "mobidai"
        ? -Math.PI / 2 + (2 * Math.PI * (index - 1 + fraction)) / n
        : Math.PI - (2 * Math.PI * (index - 1 + fraction)) / n;
    return [Math.cos(turn), Math.sin(turn)];
  }

  function draw() {
    // Gone with its fields, when another source was chosen.
    if (!canvas.isConnected) return observer.disconnect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const size = canvas.clientWidth || 260;
    canvas.width = canvas.height = Math.round(size * ratio);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, size, size);
    const style = getComputedStyle(document.documentElement);
    const muted = style.getPropertyValue("--muted").trim();
    const accent = style.getPropertyValue("--accent").trim();
    const c = size / 2;
    const r = size / 2 - 22;
    const view = state();
    ctx.strokeStyle = muted;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(c, c, r, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    if (source === "mobidai") {
      const every = Math.max(1, Math.ceil(view.n / 16));
      for (let slot = 1; slot <= view.n; slot++) {
        const [x, y] = place(slot, view.n, size);
        ctx.fillStyle = muted;
        ctx.beginPath();
        ctx.arc(c + r * x, c + r * y, 2, 0, 2 * Math.PI);
        ctx.fill();
        if ((slot - 1) % every === 0) ctx.fillText(slot, c + (r + 12) * x, c + (r + 12) * y);
      }
      for (const [slot, strand] of view.at) {
        const [x, y] = place(slot, view.n, size);
        ctx.fillStyle = hue(strand, view.strands);
        ctx.beginPath();
        ctx.arc(c + r * x, c + r * y, slot === chosen ? 8 : 5.5, 0, 2 * Math.PI);
        ctx.fill();
        if (slot === chosen) {
          ctx.strokeStyle = accent;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
    } else {
      for (let space = 1; space <= view.n; space++) {
        const [x0, y0] = place(space, view.n, size, 0);
        ctx.strokeStyle = muted;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(c + (r - 26) * x0, c + (r - 26) * y0);
        ctx.lineTo(c + (r + 4) * x0, c + (r + 4) * y0);
        ctx.stroke();
        const [lx, ly] = place(space, view.n, size);
        ctx.fillStyle = space === chosen ? accent : muted;
        ctx.font = space === chosen ? "bold 12px system-ui, sans-serif" : "11px system-ui, sans-serif";
        ctx.fillText(space, c + (r + 13) * lx, c + (r + 13) * ly);
        const group = view.groups[space - 1];
        group.forEach((strand, i) => {
          const fraction = 0.15 + (0.7 * (i + 0.5)) / group.length;
          const [x, y] = place(space, view.n, size, fraction);
          ctx.fillStyle = hue(strand, view.strands);
          ctx.beginPath();
          ctx.arc(c + (r - 12) * x, c + (r - 12) * y, 5, 0, 2 * Math.PI);
          ctx.fill();
        });
      }
    }
    const count = pairs(moves.value).length;
    help.textContent =
      chosen === null
        ? source === "mobidai"
          ? `Click a strand, then the slot it goes to. ${count} move${count === 1 ? "" : "s"}.`
          : `Click the space a strand leaves, then the one it goes to. ${count} move${count === 1 ? "" : "s"}.`
        : source === "mobidai"
          ? `Now the slot strand at ${chosen} goes to.`
          : `Now the space it goes to, from space ${chosen}.`;
  }

  canvas.addEventListener("click", (event) => {
    const box = canvas.getBoundingClientRect();
    const size = box.width;
    const x = event.clientX - box.left - size / 2;
    const y = event.clientY - box.top - size / 2;
    const view = state();
    if (source === "mobidai") {
      // The nearest slot to where the click was.
      const angle = Math.atan2(y, x);
      const slot =
        ((Math.round(((angle + Math.PI / 2) * view.n) / (2 * Math.PI) - 0.5) % view.n) + view.n) %
          view.n +
        1;
      if (view.at.has(slot)) chosen = slot;
      else if (chosen !== null) return add(chosen, slot);
    } else {
      // Anticlockwise from the left, in the plane with y up.
      const angle = Math.atan2(-y, x);
      const round = (((angle - Math.PI) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
      const space = (Math.floor((round * view.n) / (2 * Math.PI)) % view.n) + 1;
      if (chosen === null) {
        if (view.groups[space - 1].length) chosen = space;
      } else if (space === chosen) {
        chosen = null;
      } else {
        return add(chosen, space);
      }
    }
    draw();
  });
  for (const input of holder.querySelectorAll("input, textarea")) {
    input.addEventListener("input", draw);
  }
  holder.querySelector("select[name=name]").addEventListener("change", () => {
    chosen = null;
    requestAnimationFrame(draw);
  });
  const observer = new ResizeObserver(draw);
  observer.observe(canvas);
  draw();
}

function readSpec() {
  const spec = { source: $("source").value };
  for (const element of $("form").elements) {
    if (!element.name || element.name === "source") continue;
    if (element.value === "" || element.closest("[hidden]")) continue;
    spec[element.name] =
      element.type === "number" ? Number(element.value) : element.value;
  }
  return spec;
}

function writeSpec(spec) {
  $("source").value = spec.source;
  renderFields(spec.source, spec);
  $("yarn_diameter").value = spec.yarn_diameter ?? "";
  $("iterations").value = spec.iterations ?? "";
  $("settle").value = spec.settle ?? "auto";
}

function specFromHash() {
  if (!location.hash.slice(1)) return null;
  const params = new URLSearchParams(location.hash.slice(1));
  const spec = Object.fromEntries(params.entries());
  if (!catalogue[spec.source]) return null;
  return spec;
}

// ------------------------------------------------------------------ worker

const worker = new Worker("worker.js");
let pending = 0;
let lastResult = null;

function setStatus(text, error = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", error);
}

worker.onmessage = ({ data }) => {
  if (data.type === "status") {
    setStatus(data.text);
  } else if (data.type === "ready") {
    catalogue = data.catalogue;
    const select = $("source");
    for (const [source, about] of Object.entries(catalogue)) {
      select.append(new Option(about.title, source));
    }
    const spec = specFromHash() || { source: "word", ...catalogue.word.defaults };
    writeSpec(spec);
    $("build").disabled = false;
    $("build").textContent = "Make the braid";
    submit();
  } else if (data.type === "laid") {
    if (data.id !== pending) return;
    // Settling sends the braid as it goes: the view stays put.
    show(data.result, null, shownLaid === data.id);
  } else if (data.type === "result") {
    if (data.id !== pending) return;
    $("build").disabled = false;
    setStatus(
      data.seconds ? `Made in ${data.seconds.toFixed(1)} s.` : "Made before: shown again.",
    );
    // The tight braid replaces the laid one where the view already is —
    // unless it was beaten up, much shorter than it was laid.
    show(data.result, data.seconds, shownLaid === data.id && data.result.settled === "sideways");
  } else if (data.type === "error") {
    if (data.id !== undefined && data.id !== pending) return;
    $("build").disabled = !catalogue;
    setStatus(data.message, true);
  }
};

worker.postMessage({ type: "init", pyodideUrl: PYODIDE_URL });

function submit() {
  const spec = readSpec();
  pending += 1;
  $("build").disabled = true;
  history.replaceState(null, "", "#" + new URLSearchParams(spec).toString());
  worker.postMessage({ type: "build", id: pending, spec });
}

$("form").addEventListener("submit", (event) => {
  event.preventDefault();
  submit();
});

$("source").addEventListener("change", () => renderFields($("source").value));

// ------------------------------------------------------------------- scene

const viewer = $("viewer");
const renderer = new THREE.WebGLRenderer({
  antialias: true,
  preserveDrawingBuffer: true,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
viewer.append(renderer.domElement);

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
camera.up.set(0, 0, 1);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.autoRotateSpeed = 1.5;

scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8478, 1.6));
const key = new THREE.DirectionalLight(0xffffff, 1.6);
key.position.set(4, -6, 8);
scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 0.5);
fill.position.set(-6, 4, -2);
scene.add(fill);

function stageColour() {
  return getComputedStyle(document.documentElement)
    .getPropertyValue("--stage")
    .trim();
}
scene.background = new THREE.Color(stageColour());
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  scene.background = new THREE.Color(stageColour());
});

function resize() {
  const { clientWidth: width, clientHeight: height } = viewer;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  renderer.domElement.style.width = width + "px";
  renderer.domElement.style.height = height + "px";
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}
new ResizeObserver(() => {
  resize();
  if (braid) drawTop(currentTime());
  drawSection(lastResult);
}).observe(viewer);

function currentTime() {
  const [first, last] = braid.span;
  return first + (Number($("made").value) / 1000) * (last - first);
}
resize();

// What is drawn: per yarn its tube and its line, each revealed up to how
// much of the braid is made.
let braid = null;
// Whether braids hang from their fell, as from a kumihimo disk or a marudai,
// or rise from it, as from a braiding machine: braids made on a marudai —
// disk braids and words — hang unless asked otherwise, machines' rise.
const hangs = { disk: true, other: false };

function dispose(object) {
  object.traverse((child) => {
    child.geometry?.dispose();
    child.material?.dispose();
  });
}

let shownLaid = null;

function show(result, seconds, keepView = false) {
  shownLaid = seconds === null ? pending : null;
  if (braid) {
    scene.remove(braid.turner);
    dispose(braid.turner);
  }
  lastResult = result;
  const group = new THREE.Group();
  const yarns = [];
  const radius = result.yarn_diameter / 2;
  const times = result.times || result.strands[0].points.map((_, i) => i);
  for (const strand of result.strands) {
    const points = strand.points.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal");
    const segments = Math.min(Math.max(points.length * 3, 64), 4000);
    const radial = 10;
    // When each tube segment was laid: tubes are cut evenly along their
    // length, which is not evenly along the points.
    const segmentTimes = new Float64Array(segments + 1);
    for (let i = 0; i <= segments; i++) {
      const along = curve.getUtoTmapping(i / segments) * (points.length - 1);
      segmentTimes[i] = sample(times, along);
    }
    const tube = new THREE.Mesh(
      new THREE.TubeGeometry(curve, segments, radius, radial, false),
      new THREE.MeshStandardMaterial({
        color: strand.colour,
        roughness: 0.55,
        metalness: 0.05,
      }),
    );
    tube.name = strand.name;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curve.getSpacedPoints(segments)),
      new THREE.LineBasicMaterial({ color: strand.colour }),
    );
    group.add(tube, line);
    yarns.push({ tube, line, segments, radial, segmentTimes });
  }
  for (const core of result.cores || []) {
    const from = new THREE.Vector3(...core.from);
    const to = new THREE.Vector3(...core.to);
    const length = from.distanceTo(to);
    const mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(core.diameter / 2, core.diameter / 2, length, 16),
      new THREE.MeshStandardMaterial({ color: 0x77736c, roughness: 0.8 }),
    );
    mesh.position.copy(from.clone().add(to).multiplyScalar(0.5));
    mesh.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      to.clone().sub(from).normalize(),
    );
    mesh.userData.core = true;
    group.add(mesh);
  }
  // Made on a marudai: each yarn's tail above the fell, out to its carrier,
  // and the marudai's mirror they lie over, seen through.
  const tails = [];
  if (result.marudai) {
    result.marudai.tails.forEach((points, i) => {
      if (points.length < 2) return;
      const colour = result.strands[i].colour;
      const curve = new THREE.CatmullRomCurve3(
        points.map(([x, y, z]) => new THREE.Vector3(x, y, z)),
        false,
        "centripetal",
      );
      const segments = Math.min(Math.max(points.length * 3, 32), 2000);
      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, segments, radius, 10, false),
        new THREE.MeshStandardMaterial({ color: colour, roughness: 0.55, metalness: 0.05 }),
      );
      const line = new THREE.Line(
        new THREE.BufferGeometry().setFromPoints(curve.getSpacedPoints(segments)),
        new THREE.LineBasicMaterial({ color: colour }),
      );
      tube.userData.whole = line.userData.whole = true;
      group.add(tube, line);
      tails.push({ tube, line });
    });
    const { z, radius: rim, hole } = result.marudai.disk;
    const mirror = new THREE.Mesh(
      new THREE.RingGeometry(hole, rim * 1.08, 96),
      new THREE.MeshStandardMaterial({
        color: 0xc9bfae,
        roughness: 0.4,
        transparent: true,
        opacity: 0.28,
        side: THREE.DoubleSide,
        depthWrite: false,
      }),
    );
    mirror.position.z = z;
    mirror.userData.whole = true;
    group.add(mirror);
  }
  // The braid in the disk's turn, then turned rising from its fell or hanging
  // from it: a half turn about a level axis, so it is still the same braid,
  // not its mirror image.
  const stand = new THREE.Group();
  const turner = new THREE.Group();
  stand.add(group);
  turner.add(stand);
  scene.add(turner);
  const timeline = result.timeline;
  // Made on a marudai — a disk braid, or a word rolled onto one — or not.
  const kind = result.disk ? "disk" : "other";
  $("hanging").checked = hangs[kind];
  const clock = timeline
    ? timeline.clock
    : { source: [times[0], times[times.length - 1]], braid: [times[0], times[times.length - 1]] };
  const span = timeline
    ? [timeline.times[0], timeline.times[timeline.times.length - 1]]
    : [clock.source[0], clock.source[clock.source.length - 1]];
  braid = {
    group,
    stand,
    turner,
    kind,
    yarns,
    tails,
    times,
    heights: result.strands[0].points.map((p) => p[2]),
    clock,
    span,
    timeline,
    colours: result.strands.map((strand) => strand.colour),
    box: null,
  };
  stand.rotation.x = hangs[kind] ? Math.PI : 0;
  braid.box = new THREE.Box3().setFromObject(turner);
  showTubes($("tubes").checked);
  $("topview").hidden = !timeline || !$("showtop").checked;
  $("section").hidden = !$("showsection").checked;
  drawSection(result);
  $("made").value = $("made").max;
  made(Number($("made").max));
  if (!keepView) fit();
  describe(result, seconds);
  $("empty").hidden = true;
}

function showTubes(tubes) {
  if (!braid) return;
  for (const yarn of [...braid.yarns, ...braid.tails]) {
    yarn.tube.visible = tubes;
    yarn.line.visible = !tubes;
  }
  made(Number($("made").value));
}

// Show the braid as it was ``value`` thousandths of the way through its
// making, by the clock of whatever made it: the oldest rows first, carried
// up by the take-off, the newest at the fell.  The top view shows what made
// it, at that same instant.
function made(value) {
  if (!braid) return;
  const fraction = value / 1000;
  const [first, last] = braid.span;
  const now = first + fraction * (last - first);
  const laid = interpolate(braid.clock.source, braid.clock.braid, now);
  for (const yarn of braid.yarns) {
    const shown = Math.max(1, countUpTo(yarn.segmentTimes, laid + 1e-9) - 1);
    yarn.tube.geometry.setDrawRange(0, shown * yarn.radial * 6);
    yarn.line.geometry.setDrawRange(0, shown + 1);
  }
  const heights = braid.heights;
  const newest = interpolate(braid.times, heights, laid);
  braid.group.position.z = heights[heights.length - 1] - newest;
  // A disk's braid hangs from it and turns with it.
  const timeline = braid.timeline;
  braid.turner.rotation.z = timeline?.turn
    ? interpolate(timeline.times, timeline.turn, now)
    : 0;
  // The cores, and a marudai's tails and mirror, once the braid is made.
  const tubes = $("tubes").checked;
  for (const child of braid.group.children) {
    if (child.userData.core) child.visible = fraction > 0.999;
    if (child.userData.whole) {
      const kind = child.isMesh && child.geometry.type === "TubeGeometry" ? tubes : child.isLine ? !tubes : true;
      child.visible = fraction > 0.999 && kind;
    }
  }
  drawTop(now);
}

// ``ys`` at ``x``, between the samples ``xs`` (ascending), held at the ends.
function interpolate(xs, ys, x) {
  const n = xs.length;
  if (x <= xs[0]) return ys[0];
  if (x >= xs[n - 1]) return ys[n - 1];
  let low = 0;
  let high = n - 1;
  while (high - low > 1) {
    const middle = (low + high) >> 1;
    if (xs[middle] <= x) low = middle;
    else high = middle;
  }
  const span = xs[high] - xs[low];
  const t = span > 0 ? (x - xs[low]) / span : 0;
  return ys[low] + t * (ys[high] - ys[low]);
}

// ``values`` at a fractional index.
function sample(values, at) {
  const low = Math.floor(at);
  const high = Math.min(low + 1, values.length - 1);
  return values[low] + (at - low) * (values[high] - values[low]);
}

// How many of the ascending ``values`` are at most ``limit``.
function countUpTo(values, limit) {
  let low = 0;
  let high = values.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (values[middle] <= limit) low = middle + 1;
    else high = middle;
  }
  return low;
}

// ---------------------------------------------------------------- top view

// ------------------------------------------------------------ cross-section

// The braid seen along its axis, once made: each strand's track over the
// middle of the braid — far from the fell and the held top — and a slice
// half way up, each yarn a disc as thick as it is.  A regular braid has
// settled when its strands share one track, each a step along it.
const section = $("section");

function drawSection(result) {
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
  const X = (x) => size / 2 + (x - cx) * scale;
  const Y = (y) => size / 2 - up * (y - cy) * scale;
  const style = getComputedStyle(document.documentElement);
  ctx.fillStyle = style.getPropertyValue("--muted").trim();
  ctx.font = "10px system-ui, sans-serif";
  ctx.fillText("Cross-section", 8, 14);
  ctx.globalAlpha = 0.55;
  ctx.lineWidth = 1;
  middle.forEach((points, i) => {
    ctx.strokeStyle = result.strands[i].colour;
    ctx.beginPath();
    points.forEach(([x, y], j) => (j ? ctx.lineTo(X(x), Y(y)) : ctx.moveTo(X(x), Y(y))));
    ctx.stroke();
  });
  ctx.globalAlpha = 0.9;
  const half = Math.floor((to - from) / 2);
  middle.forEach((points, i) => {
    const [x, y] = points[half];
    ctx.fillStyle = result.strands[i].colour;
    ctx.beginPath();
    ctx.arc(X(x), Y(y), radius * scale, 0, 2 * Math.PI);
    ctx.fill();
  });
  ctx.globalAlpha = 1;
}

const top = $("topview");
const topContext = top.getContext("2d");

function drawTop(now) {
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
  const x = (p) => size / 2 + p[0] * scale;
  const y = (p) => size / 2 - p[1] * scale;

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
    ctx.fillText(name, x([sx * out, 0]), y([0, sy * out]));
  }

  // Where each carrier is now; on a disk, the strands lifted over the others
  // are drawn last, on top.
  const last = view.times.length - 1;
  const span = view.times[last] - view.times[0];
  const at = Math.min(
    last,
    Math.max(0, span > 0 ? ((now - view.times[0]) / span) * last : 0),
  );
  const where = view.strands.map((path) => {
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

function fit() {
  if (!braid) return;
  const box = braid.box;
  const centre = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const height = size.z;
  const across = Math.max(size.x, size.y);
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const tall = height / 2 / Math.tan(fov / 2);
  const wide = across / 2 / Math.tan(fov / 2) / Math.max(camera.aspect, 0.3);
  const distance = 1.25 * Math.max(tall, wide, across * 2);
  const direction = new THREE.Vector3(1, -0.45, 0.25).normalize();
  camera.position.copy(centre).addScaledVector(direction, distance);
  camera.near = distance / 100;
  camera.far = distance * 100;
  camera.updateProjectionMatrix();
  controls.target.copy(centre);
  controls.update();
}

// ------------------------------------------------------------- the braid

function describe(result, seconds) {
  $("about").hidden = false;
  $("title").textContent = result.title;
  const info = result.info;
  const rows = [
    ["Strands", info.n_strands],
    ["Should look", info.expected_shape && `${info.expected_shape} in cross-section`],
    ["Crossings", info.crossings],
    ["Exponent sum", info.exponent_sum],
    ["Permutation", info.permutation && info.permutation.join(" ")],
    ["Pure", info.pure === undefined ? undefined : info.pure ? "yes" : "no"],
    [
      "Closed up",
      info.components === undefined
        ? undefined
        : info.components === 1
          ? "a knot"
          : `a link of ${info.components} pieces`,
    ],
    [
      "Normal form",
      info.garside &&
        `Δ^${info.garside.half_twists} and ${info.garside.factors} permutation braids`,
    ],
    ["Full twists", info.garside && info.garside.full_twists],
    ["Word", info.word, true],
    ["Ring word", info.annular_word, true],
    [
      "Closest yarns",
      info.closest_approach === undefined
        ? undefined
        : `${info.closest_approach} for a yarn of ${round(result.yarn_diameter)}`,
    ],
    ["Computed in", seconds ? `${seconds.toFixed(1)} s` : undefined],
    ["", seconds === null ? "As laid — tightening…" : undefined],
  ];
  const list = $("info");
  list.replaceChildren();
  for (const [name, value, code] of rows) {
    if (value === undefined || value === null || value === "") continue;
    const term = document.createElement("dt");
    term.textContent = name;
    const detail = document.createElement("dd");
    if (code) {
      const text = String(value);
      const element = document.createElement("code");
      element.textContent = text.length > 600 ? text.slice(0, 600) + " …" : text;
      element.title = text;
      detail.append(element);
    } else {
      detail.textContent = value;
    }
    list.append(term, detail);
  }
  const notes = $("notes");
  notes.replaceChildren(
    ...result.notes.map((note) => {
      const item = document.createElement("li");
      item.textContent = note;
      return item;
    }),
  );
}

function round(value) {
  return Number(value.toPrecision(3));
}

// ---------------------------------------------------------------- controls

$("tubes").addEventListener("change", (event) => showTubes(event.target.checked));
$("showsection").addEventListener("change", (event) => {
  section.hidden = !event.target.checked || !lastResult;
  drawSection(lastResult);
});
$("showtop").addEventListener("change", (event) => {
  top.hidden = !event.target.checked || !braid || !braid.timeline;
  made(Number($("made").value));
});
$("spin").addEventListener("change", (event) => {
  controls.autoRotate = event.target.checked;
});
$("hanging").addEventListener("change", (event) => {
  if (!braid) return;
  hangs[braid.kind] = event.target.checked;
  braid.stand.rotation.x = event.target.checked ? Math.PI : 0;
  made(Number($("made").value));
  braid.box = new THREE.Box3().setFromObject(braid.turner);
  drawSection(lastResult);
  fit();
});
$("reset").addEventListener("click", fit);
$("made").addEventListener("input", (event) => {
  growing = false;
  $("grow").textContent = "▶ Grow";
  made(Number(event.target.value));
});

let growing = false;
let growFrom = 0;
$("grow").addEventListener("click", () => {
  growing = !growing;
  $("grow").textContent = growing ? "⏸ Pause" : "▶ Grow";
  if (growing) {
    if (Number($("made").value) >= 1000) $("made").value = 0;
    growFrom = performance.now() - Number($("made").value) * 12;
  }
});

$("share").addEventListener("click", async () => {
  try {
    await navigator.clipboard.writeText(location.href);
    setStatus("Link copied.");
  } catch {
    setStatus("Copy the address bar to share this braid.");
  }
});

function fileName(extension) {
  return lastResult.title.replace(/[^\w-]+/g, "_") + "." + extension;
}

function download(name, href) {
  const link = document.createElement("a");
  link.download = name;
  link.href = href;
  link.click();
  if (href.startsWith("blob:")) setTimeout(() => URL.revokeObjectURL(href), 1000);
}

$("save").addEventListener("change", (event) => {
  const what = event.target.value;
  event.target.value = "";
  if (!lastResult || !braid) return;
  if (what === "png") {
    download(fileName("png"), renderer.domElement.toDataURL("image/png"));
    return;
  }
  if (what === "json") {
    const blob = new Blob([JSON.stringify(lastResult)], { type: "application/json" });
    download(fileName("json"), URL.createObjectURL(blob));
    return;
  }
  // The whole braid as solid tubes, as made, in the braid's own units.
  const solid = new THREE.Group();
  for (const yarn of braid.yarns) {
    const tube = new THREE.Mesh(yarn.tube.geometry.clone(), yarn.tube.material);
    tube.geometry.setDrawRange(0, Infinity);
    tube.name = yarn.tube.name;
    solid.add(tube);
  }
  for (const child of braid.group.children) {
    if (child.userData.core) solid.add(child.clone());
  }
  solid.updateMatrixWorld(true);
  if (what === "stl") {
    const data = new STLExporter().parse(solid, { binary: true });
    download(fileName("stl"), URL.createObjectURL(new Blob([data])));
  } else if (what === "obj") {
    const text = new OBJExporter().parse(solid);
    download(fileName("obj"), URL.createObjectURL(new Blob([text])));
  }
  solid.traverse((child) => {
    if (child.isMesh && !child.userData.core) child.geometry.dispose();
  });
});

function frame(now) {
  if (growing && braid) {
    // Twelve seconds from nothing to the whole braid.
    const value = Math.min(1000, (now - growFrom) / 12);
    $("made").value = value;
    made(value);
    if (value >= 1000) {
      growing = false;
      $("grow").textContent = "▶ Grow";
    }
  }
  controls.update();
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// For tests: what the page holds.
window.braidStudio = {
  get result() {
    return lastResult;
  },
  get drawn() {
    return braid ? braid.yarns.length : 0;
  },
};
