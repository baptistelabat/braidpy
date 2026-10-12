// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// braidpy, in the browser: Pyodide runs braidpy itself, in this worker, so
// the page stays responsive while a braid is laid and tightened.
//
// Messages in:   {type: "init", pyodideUrl}
//                {type: "build", id, spec}
//                {type: "geometry", name}
// Messages out:  {type: "status", text}
//                {type: "ready", catalogue, version}
//                {type: "laid", id, result, job, settle, twist}
//                  the braid as laid, for settle.js to settle
//                {type: "geometry", name, shape}
//                {type: "error", id?, message}

// The yarns are settled in a worker of their own: see settle.js.

let pyodide = null;
let machinesReady = false;

function status(text) {
  self.postMessage({ type: "status", text });
}

async function init(pyodideUrl) {
  status("Loading Python…");
  importScripts(pyodideUrl + "pyodide.js");
  pyodide = await loadPyodide({ indexURL: pyodideUrl });

  status("Loading numpy…");
  await pyodide.loadPackage(["numpy"], { messageCallback: () => {} });

  status("Loading braidpy…");
  const base = new URL("wheels/", self.location.href);
  const manifest = await (await fetch(new URL("manifest.json", base))).json();
  // Installed as they are, without resolving what they ask for: braidpy's
  // other dependencies are for drawing, which the page does itself, or for
  // what the page does not ask of it (sympy, for Burau matrices).
  await pyodide.loadPackage(
    manifest.wheels.map((wheel) => new URL(wheel, base).href),
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
  self.postMessage({ type: "ready", catalogue, version: manifest.version });
}

// The newest braid asked for: one asked for before it is not laid.
let latest = 0;

async function build(id, spec) {
  if (id !== latest) return;
  if (spec.source === "machine") await machinery();
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
  const job = result.tighten;
  delete result.tighten;
  // Automatic: a braid whose moves are known — a disk braid, or a word
  // rolled onto a ring — is made on a marudai, the closest to a real braid;
  // any other is tightened sideways.
  let settle = (spec.settle ?? "auto") === "auto" ? (result.disk ? "marudai" : "sideways") : spec.settle;
  const disk = result.timeline?.kind === "disk";
  if (job && settle !== "sideways" && !(settle === "marudai" ? result.disk : disk)) {
    result.notes = [
      ...(result.notes || []),
      settle === "marudai"
        ? "Only disk braids and braid words are made on a marudai for now: these yarns were tightened sideways."
        : "Settling by physics is for disk braids for now: these yarns were tightened sideways.",
    ];
    settle = "sideways";
  }
  // Shown as laid straight away; settled in settle.js.
  self.postMessage({ type: "laid", id, result, job: job ?? null, settle, twist: spec.twist });
}

// The last line of a Python traceback is what went wrong.
function pythonMessage(error) {
  const text = String(error && error.message ? error.message : error);
  const lines = text.trim().split("\n").filter((line) => line.trim());
  const last = lines[lines.length - 1] || text;
  return last.replace(/^\w*(Error|Exception):\s*/, "");
}

let queue = Promise.resolve();
// A machine from above, for the page to load it by hand.
async function geometry(name) {
  await machinery();
  pyodide.globals.set("machine_name", name);
  const text = await pyodide.runPythonAsync("json.dumps(web.machine_geometry(machine_name))");
  self.postMessage({ type: "geometry", name, shape: JSON.parse(text) });
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
  queue = queue.then(async () => {
    try {
      if (message.type === "init") await init(message.pyodideUrl);
      else if (message.type === "build") await build(message.id, message.spec);
      else if (message.type === "geometry") await geometry(message.name);
    } catch (error) {
      self.postMessage({
        type: "error",
        id: message.id,
        message: pythonMessage(error),
      });
    }
  });
};
