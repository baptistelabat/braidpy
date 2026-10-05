// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The machine console's half of braidpy, in the browser.  Pyodide runs
// braidpy.console here so that a step is the machine's own step and a
// collision is the machine's own collision, not a guess made in JavaScript.
//
// Messages in:   {type: "init", pyodideUrl}
//                {type: "geometry", id, name}
//                {type: "advance", id, name, carriers, time}
//                {type: "trouble", id, name, carriers, time}
// Messages out:  {type: "status", text}
//                {type: "ready", catalogue, version}
//                {type: "answer", id, result}
//                {type: "error", id, message}

let pyodide = null;

function status(text) {
  self.postMessage({ type: "status", text });
}

async function init(pyodideUrl) {
  status("Loading Python…");
  importScripts(pyodideUrl + "pyodide.js");
  pyodide = await loadPyodide({ indexURL: pyodideUrl });

  // networkx as well as numpy: the console asks braidpy where the gears are,
  // and compute_layout falls back on a graph drawing for anything with a
  // cycle in it.
  status("Loading numpy and networkx…");
  await pyodide.loadPackage(["numpy", "networkx"], { messageCallback: () => {} });

  status("Loading braidpy…");
  const base = new URL("wheels/", self.location.href);
  const manifest = await (await fetch(new URL("manifest.json", base))).json();
  await pyodide.loadPackage(
    manifest.wheels.map((wheel) => new URL(wheel, base).href),
    { messageCallback: () => {} },
  );

  await pyodide.runPythonAsync(`
import warnings
warnings.filterwarnings("ignore", category=SyntaxWarning)
import json
from braidpy import console
`);
  const catalogue = JSON.parse(
    await pyodide.runPythonAsync("json.dumps(console.catalogue())"),
  );
  self.postMessage({ type: "ready", catalogue, version: manifest.version });
}

// Hand the arguments over as JSON rather than building a Python literal, so
// nothing has to be escaped and a machine name cannot become code.
async function call(python, args) {
  pyodide.globals.set("_args", JSON.stringify(args));
  const text = await pyodide.runPythonAsync(
    `json.dumps(${python}(**json.loads(_args)))`,
  );
  return JSON.parse(text);
}

function pythonMessage(error) {
  const text = String(error && error.message ? error.message : error);
  const lines = text.trimEnd().split("\n").filter((line) => line.trim());
  if (!lines.length) return text;
  // The last line of a Python traceback is the message; a Pyodide failure
  // ends with a link to its docs instead, so keep what came before it too.
  const tail = lines.slice(-3).join(" | ");
  return tail.length > 400 ? `${tail.slice(0, 400)}…` : tail;
}

self.onmessage = (event) => {
  const message = event.data;
  (async () => {
    try {
      if (message.type === "init") {
        await init(message.pyodideUrl);
        return;
      }
      if (message.type === "geometry") {
        const result = await call("console.geometry", { name: message.name });
        self.postMessage({ type: "answer", id: message.id, result });
        return;
      }
      if (message.type === "advance") {
        const result = await call("console.advance", {
          name: message.name,
          carriers: message.carriers,
          time: message.time,
        });
        self.postMessage({ type: "answer", id: message.id, result });
        return;
      }
      if (message.type === "trouble") {
        const result = await call("console.trouble", {
          name: message.name,
          carriers: message.carriers,
          time: message.time,
        });
        self.postMessage({ type: "answer", id: message.id, result });
        return;
      }
    } catch (error) {
      self.postMessage({
        type: "error",
        id: message.id,
        message: pythonMessage(error),
      });
    }
  })();
};
