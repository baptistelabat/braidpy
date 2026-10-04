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

let pyodide = null;
let machinesReady = false;

function status(text) {
  self.postMessage({ type: "status", text });
}

async function init(pyodideUrl) {
  status("Loading Python…");
  importScripts(pyodideUrl + "pyodide.js");
  pyodide = await loadPyodide({ indexURL: pyodideUrl });

  status("Loading numpy and sympy…");
  await pyodide.loadPackage(["numpy", "sympy"], { messageCallback: () => {} });

  status("Loading braidpy…");
  const base = new URL("wheels/", self.location.href);
  const manifest = await (await fetch(new URL("manifest.json", base))).json();
  // Installed as they are, without resolving what they ask for: braidpy's
  // other dependencies are for drawing, which the page does itself, and
  // Pyodide's own numpy and sympy serve.
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

async function build(id, spec) {
  if (spec.source === "machine" && !machinesReady) {
    status("Loading networkx, for the machines…");
    await pyodide.loadPackage(["networkx"], { messageCallback: () => {} });
    machinesReady = true;
  }
  status("Laying and tightening the yarns…");
  const started = performance.now();
  pyodide.globals.set("spec_json", JSON.stringify(spec));
  try {
    const text = await pyodide.runPythonAsync(
      "json.dumps(web.build(json.loads(spec_json)))",
    );
    const seconds = (performance.now() - started) / 1000;
    self.postMessage({ type: "result", id, result: JSON.parse(text), seconds });
  } catch (error) {
    self.postMessage({ type: "error", id, message: pythonMessage(error) });
  }
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
