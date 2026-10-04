// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Braid Studio: describe a braid, and braidpy — running in a worker through
// Pyodide — lays and tightens it; three.js draws it here.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

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
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 40 },
  ],
  sinnet: [
    { name: "name", label: "Sinnet", kind: "entries" },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 12 },
  ],
  machine: [
    { name: "name", label: "Machine", kind: "entries" },
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
    if (field.kind === "number") numbers.push(label);
    else holder.append(label);
  }
  if (numbers.length) {
    const row = document.createElement("div");
    row.className = "row";
    row.append(...numbers);
    holder.append(row);
  }
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

function readSpec() {
  const spec = { source: $("source").value };
  for (const element of $("form").elements) {
    if (!element.name || element.name === "source") continue;
    if (element.value === "") continue;
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
  } else if (data.type === "result") {
    if (data.id !== pending) return;
    $("build").disabled = false;
    setStatus(`Made in ${data.seconds.toFixed(1)} s.`);
    show(data.result, data.seconds);
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
new ResizeObserver(resize).observe(viewer);
resize();

// What is drawn: per yarn its tube and its line, each revealed up to how
// much of the braid is made.
let braid = null;

function dispose(object) {
  object.traverse((child) => {
    child.geometry?.dispose();
    child.material?.dispose();
  });
}

function show(result, seconds) {
  if (braid) {
    scene.remove(braid.group);
    dispose(braid.group);
  }
  lastResult = result;
  const group = new THREE.Group();
  const yarns = [];
  const radius = result.yarn_diameter / 2;
  for (const strand of result.strands) {
    const points = strand.points.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal");
    const segments = Math.min(Math.max(points.length * 3, 64), 4000);
    const radial = 10;
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
      new THREE.BufferGeometry().setFromPoints(curve.getPoints(segments)),
      new THREE.LineBasicMaterial({ color: strand.colour }),
    );
    group.add(tube, line);
    yarns.push({ tube, line, segments, radial, heights: points.map((p) => p.z) });
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
  scene.add(group);
  braid = { group, yarns, box: new THREE.Box3().setFromObject(group) };
  showTubes($("tubes").checked);
  made(Number($("made").max));
  $("made").value = $("made").max;
  fit();
  describe(result, seconds);
  $("empty").hidden = true;
}

function showTubes(tubes) {
  if (!braid) return;
  for (const yarn of braid.yarns) {
    yarn.tube.visible = tubes;
    yarn.line.visible = !tubes;
  }
}

// Show the braid as it was when ``value`` thousandths of it were made: the
// oldest rows first, carried up by the take-off, the newest at the fell.
function made(value) {
  if (!braid) return;
  const fraction = value / 1000;
  for (const yarn of braid.yarns) {
    const shown = Math.max(1, Math.round(fraction * yarn.segments));
    yarn.tube.geometry.setDrawRange(0, shown * yarn.radial * 6);
    yarn.line.geometry.setDrawRange(0, shown + 1);
  }
  const heights = braid.yarns[0].heights;
  const last = heights.length - 1;
  const at = Math.round(fraction * last);
  braid.group.position.z = heights[last] - heights[at];
  for (const child of braid.group.children) {
    if (child.userData.core) child.visible = fraction > 0.999;
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
    ["Crossings", info.crossings],
    ["Exponent sum", info.exponent_sum],
    ["Permutation", info.permutation && info.permutation.join(" ")],
    ["Pure", info.pure === undefined ? undefined : info.pure ? "yes" : "no"],
    ["Word", info.word, true],
    ["Ring word", info.annular_word, true],
    [
      "Closest yarns",
      info.closest_approach === undefined
        ? undefined
        : `${info.closest_approach} for a yarn of ${round(result.yarn_diameter)}`,
    ],
    ["Computed in", `${seconds.toFixed(1)} s`],
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
$("spin").addEventListener("change", (event) => {
  controls.autoRotate = event.target.checked;
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
    growFrom = performance.now() - Number($("made").value) * 8;
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

$("save").addEventListener("click", () => {
  if (!lastResult) return;
  const link = document.createElement("a");
  link.download = lastResult.title.replace(/[^\w-]+/g, "_") + ".png";
  link.href = renderer.domElement.toDataURL("image/png");
  link.click();
});

function frame(now) {
  if (growing && braid) {
    // Eight seconds from nothing to the whole braid.
    const value = Math.min(1000, (now - growFrom) / 8);
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
