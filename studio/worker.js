// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// braidpy, in the browser: Pyodide runs braidpy itself, in this worker, so
// the page stays responsive while a braid is laid and tightened.
//
// Messages in:   {type: "init", pyodideUrl}
//                {type: "build", id, spec, premade?}
//                  premade: the braid as the site was built with it, for a
//                  catalogue braid as it comes (web/build.py): laid at
//                  once, without waiting for Python
//                {type: "geometry", name}
//                {type: "sinnet", id}
//                {type: "turn", id, name, loading, time}
//                {type: "origin", name, place, time}
// Messages out:  {type: "status", text}
//                {type: "ready", catalogue, version}
//                {type: "laid", id, result, job, settle, twist}
//                  the braid as laid, for settle.js to settle
//                {type: "kin", id, kin}
//                {type: "bridges", id, bridges}
//                  the braid made other ways: a kumihimo disk's moves and a
//                  lace machine's punchcard (braidpy.bridges.for_page)
//                {type: "sinnet", id, sinnet}
//                  a sinnet on Ashley's stand, searched for when asked
//                  the braid's other ways of being made, and the braids
//                  nearest it (braidpy.topology_catalog.for_page)
//                {type: "geometry", name, shape}
//                {type: "turned", id, turned}
//                  a machine's handle turned by hand (web.machine_turned)
//                {type: "origin", origin}
//                  where a carrier put on it then goes in its loading
//                {type: "error", id?, message}

// The yarns are settled in a worker of their own: see settle.js.

let pyodide = null;
let machinesReady = false;
// The catalogue of braids by topology, made with the site: without it, no
// kin are found.
let topologies = false;

function status(text) {
  self.postMessage({ type: "status", text });
}

// Fetched for the browser to keep, nothing more: Pyodide, asking for it
// later, finds it in the browser's cache, or on its way there.
function prefetch(url) {
  return fetch(url)
    .then((response) => response.arrayBuffer())
    .catch(() => {});
}

async function init(pyodideUrl) {
  // What braidpy needs is fetched while Python starts, rather than after:
  // numpy, braidpy's wheels and the catalogue by topology.
  const base = new URL("wheels/", self.location.href);
  const manifest = fetch(new URL("manifest.json", base)).then((r) => r.json());
  manifest.then((m) => m.wheels.forEach((wheel) => prefetch(new URL(wheel, base))));
  fetch(pyodideUrl + "pyodide-lock.json")
    .then((r) => r.json())
    .then((lock) => prefetch(pyodideUrl + lock.packages.numpy.file_name))
    .catch(() => {});
  const topologiesFound = fetch(new URL("topologies.json", self.location.href), {
    cache: "no-cache",
  }).catch(() => null);

  status("Loading Python…");
  importScripts(pyodideUrl + "pyodide.js");
  pyodide = await loadPyodide({ indexURL: pyodideUrl });

  status("Loading braidpy…");
  // Installed as they are, without resolving what they ask for: braidpy's
  // other dependencies are for drawing, which the page does itself, or for
  // what the page does not ask of it (sympy, for Burau matrices).
  const { wheels } = await manifest;
  await pyodide.loadPackage(
    ["numpy", ...wheels.map((wheel) => new URL(wheel, base).href)],
    { messageCallback: () => {} },
  );

  await pyodide.runPythonAsync(`
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import json
from braidpy import web
`);
  const catalogue = JSON.parse(
    await pyodide.runPythonAsync("json.dumps(web.catalogue())"),
  );
  try {
    const found = await topologiesFound;
    if (found?.ok) {
      pyodide.globals.set("topologies_json", await found.text());
      await pyodide.runPythonAsync(`
from braidpy import topology_catalog
topologies = topology_catalog.load(json.loads(topologies_json))
del topologies_json
`);
      topologies = true;
    }
  } catch {
    topologies = false;
  }
  self.postMessage({ type: "ready", catalogue, version: (await manifest).version });
}

// The newest braid asked for: one asked for before it is not laid.
let latest = 0;

async function build(id, spec) {
  if (id !== latest) return;
  if (spec.source === "machine" || spec.source === "lace") await machinery();
  status("Laying the yarns…");
  pyodide.globals.set("spec_json", JSON.stringify(spec));
  let result;
  try {
    // braidpy lays the yarns and says how to tighten them; the tightening
    // itself, the slow part, is done in settle.js.
    const text = await pyodide.runPythonAsync(
      "json.dumps(web.build(json.loads(spec_json), tighten=False))",
    );
    result = JSON.parse(text);
  } catch (error) {
    self.postMessage({ type: "error", id, message: pythonMessage(error) });
    return;
  }
  laid(id, spec, result);
  await kin(id, result.info);
  await bridges(id, result.info);
}

// The braid as braidpy laid it — here, or when the site was built — handed
// on to be settled.
function laid(id, spec, result) {
  const job = result.tighten;
  delete result.tighten;
  // Automatic: a braid whose moves are known — a disk braid, or a word
  // rolled onto a ring — is made on a marudai, the closest to a real braid;
  // any other is tightened sideways.
  let settle = (spec.settle ?? "auto") === "auto" ? (result.disk ? "marudai" : "sideways") : spec.settle;
  // By physics, every yarn is a yarn: a rigid core is not held rigid.
  const rigid = job?.rigid?.some(Boolean);
  if (job && settle !== "sideways" && (settle === "marudai" ? !result.disk : rigid)) {
    result.notes = [
      ...(result.notes || []),
      settle === "marudai"
        ? "Only disk braids and braid words are made on a marudai for now: these yarns were tightened sideways."
        : "Settled by physics, a rigid core would bend as a yarn does: these yarns were tightened sideways.",
    ];
    settle = "sideways";
  }
  // Shown as laid straight away; settled in settle.js.
  self.postMessage({ type: "laid", id, result, job: job ?? null, settle, twist: spec.twist });
}

// The braid made other ways (braidpy.bridges): cheap, worked out for every
// braid; a sinnet on Ashley's stand is searched for only when asked.
let lastInfo = null;
async function bridges(id, info) {
  if (id !== latest) return;
  lastInfo = info;
  pyodide.globals.set("info_json", JSON.stringify(info));
  try {
    const text = await pyodide.runPythonAsync(`
from braidpy import bridges as _bridges
json.dumps(_bridges.for_page(json.loads(info_json)))
`);
    self.postMessage({ type: "bridges", id, bridges: JSON.parse(text) });
  } catch {
    // Nothing shown.
  }
}

async function sinnet(id) {
  if (!lastInfo) return;
  pyodide.globals.set("info_json", JSON.stringify(lastInfo));
  let found = null;
  try {
    found = JSON.parse(
      await pyodide.runPythonAsync(`
from braidpy import bridges as _bridges
json.dumps(_bridges.sinnet_for_page(json.loads(info_json)))
`),
    );
  } catch {
    found = null;
  }
  self.postMessage({ type: "sinnet", id, sinnet: found });
}

// The braid's kin, once it is on its way: what it costs is the braid's
// fingerprint, milliseconds.  Not finding them is no error worth showing.
async function kin(id, info) {
  if (!topologies || id !== latest) return;
  pyodide.globals.set("info_json", JSON.stringify(info));
  try {
    const text = await pyodide.runPythonAsync(
      "json.dumps(topology_catalog.for_page(json.loads(spec_json), json.loads(info_json), topologies))",
    );
    self.postMessage({ type: "kin", id, kin: JSON.parse(text) });
  } catch {
    // Nothing shown.
  }
}

// The last line of a Python traceback is what went wrong.
function pythonMessage(error) {
  const text = String(error && error.message ? error.message : error);
  const lines = text.trim().split("\n").filter((line) => line.trim());
  const last = lines[lines.length - 1] || text;
  return last.replace(/^[\w.]*(Error|Exception):\s*/, "");
}

let queue = Promise.resolve();
// A machine from above, for the page to load it by hand.
async function geometry(name) {
  await machinery();
  pyodide.globals.set("machine_name", name);
  // A card of your own that cannot drive the machine says why, in the panel.
  let shape;
  try {
    shape = JSON.parse(await pyodide.runPythonAsync("json.dumps(web.machine_geometry(machine_name))"));
  } catch (error) {
    shape = { error: pythonMessage(error) };
  }
  self.postMessage({ type: "geometry", name, shape });
}

// A machine's handle turned by hand, and where a carrier put on it at a
// later step goes in its loading: see braidpy.horn_gear.handle.
async function turn(message) {
  await machinery();
  pyodide.globals.set("turn_job", JSON.stringify(message));
  // Not turned — a loading braidpy cannot read — is no error worth
  // showing: the machine is drawn as loaded.
  let turned = null;
  try {
    turned = JSON.parse(
      await pyodide.runPythonAsync(`
job = json.loads(turn_job)
json.dumps(web.machine_turned(job["name"], job["loading"], job["time"]))
`),
    );
  } catch {
    turned = null;
  }
  self.postMessage({ type: "turned", id: message.id, turned });
}

async function origin(message) {
  await machinery();
  pyodide.globals.set("origin_job", JSON.stringify(message));
  let found = null;
  try {
    found = JSON.parse(
      await pyodide.runPythonAsync(`
job = json.loads(origin_job)
json.dumps(web.machine_origin(job["name"], job["place"], job["time"]))
`),
    );
  } catch {
    found = null;
  }
  self.postMessage({ type: "origin", origin: found });
}

async function machinery() {
  if (machinesReady) return;
  status("Loading networkx, for the machines…");
  await pyodide.loadPackage(["networkx"], { messageCallback: () => {} });
  machinesReady = true;
}

self.onmessage = (event) => {
  const message = event.data;
  if (message.type === "build") latest = message.id;
  // A catalogue braid made with the site is laid at once, Python or not:
  // only what is found from it — its kin, its other ways — waits for Python.
  if (message.type === "build" && message.premade) {
    const { id, spec, premade } = message;
    laid(id, spec, premade);
    queue = queue.then(async () => {
      if (id !== latest) return;
      await kin(id, premade.info);
      await bridges(id, premade.info);
    });
    return;
  }
  queue = queue.then(async () => {
    try {
      if (message.type === "init") await init(message.pyodideUrl);
      else if (message.type === "build") await build(message.id, message.spec);
      else if (message.type === "geometry") await geometry(message.name);
      else if (message.type === "turn") await turn(message);
      else if (message.type === "sinnet") await sinnet(message.id);
      else if (message.type === "origin") await origin(message);
    } catch (error) {
      self.postMessage({
        type: "error",
        id: message.id,
        message: pythonMessage(error),
      });
    }
  });
};
