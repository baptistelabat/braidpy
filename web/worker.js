// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// braidpy, in the browser: Pyodide runs braidpy itself, in this worker, so
// the page stays responsive while a braid is laid and tightened.
//
// Messages in:   {type: "init", pyodideUrl}
//                {type: "build", id, spec}
// Messages out:  {type: "status", text}
//                {type: "ready", catalogue, version}
//                {type: "result", id, result, seconds}
//                {type: "error", id?, message}

// The yarns are tightened here, in JavaScript: see tighten.js.
importScripts("tighten.js");

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

// The last few braids made, by what they were made from: going back to one
// is then instant.
const made = new Map();
const KEEP = 12;

async function build(id, spec) {
  const key = JSON.stringify(spec, Object.keys(spec).sort());
  if (made.has(key)) {
    const result = made.get(key);
    made.delete(key);
    made.set(key, result);
    self.postMessage({ type: "result", id, result, seconds: 0 });
    return;
  }
  if (spec.source === "machine" && !machinesReady) {
    status("Loading networkx, for the machines…");
    await pyodide.loadPackage(["networkx"], { messageCallback: () => {} });
    machinesReady = true;
  }
  status("Laying the yarns…");
  const started = performance.now();
  pyodide.globals.set("spec_json", JSON.stringify(spec));
  let result;
  try {
    // braidpy lays the yarns and says how to tighten them; the tightening
    // itself, the slow part, is done below in JavaScript.
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
  if (job) {
    // Shown as laid straight away, then replaced once tight.
    self.postMessage({ type: "laid", id, result });
    status("Tightening the yarns…");
    const tight = tightenYarns(job, (fraction) =>
      status(`Tightening the yarns… ${Math.round(100 * fraction)}%`),
    );
    result = tightened(result, job, tight);
  }
  const seconds = (performance.now() - started) / 1000;
  made.set(key, result);
  if (made.size > KEEP) made.delete(made.keys().next().value);
  self.postMessage({ type: "result", id, result, seconds });
}

// The strands' points, moved to where the tightening left them: sideways
// only, so every point keeps its height.
function tightened(result, job, tight) {
  const [cx, cy] = job.centre;
  result.strands.forEach((strand, a) => {
    strand.points = strand.points.map(([, , z], j) => {
      const k = a * job.n + job.chosen[j];
      return [
        round(tight.xy[2 * k] - cx),
        round(tight.xy[2 * k + 1] - cy),
        z,
      ];
    });
  });
  if (Number.isFinite(tight.closest)) {
    result.info.closest_approach = round(tight.closest);
  }
  return result;
}

function round(value) {
  return Math.round(value * 1e4) / 1e4;
}

// The last line of a Python traceback is what went wrong.
function pythonMessage(error) {
  const text = String(error && error.message ? error.message : error);
  const lines = text.trim().split("\n").filter((line) => line.trim());
  const last = lines[lines.length - 1] || text;
  return last.replace(/^\w*(Error|Exception):\s*/, "");
}

let queue = Promise.resolve();
self.onmessage = (event) => {
  const message = event.data;
  queue = queue.then(async () => {
    try {
      if (message.type === "init") await init(message.pyodideUrl);
      else if (message.type === "build") await build(message.id, message.spec);
    } catch (error) {
      self.postMessage({
        type: "error",
        id: message.id,
        message: pythonMessage(error),
      });
    }
  });
};
