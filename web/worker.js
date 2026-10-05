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
importScripts("tighten.js", "rope.js", "form.js");

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
  const physics = spec.settle === "physics" || spec.settle === "crossing";
  if (job && physics && result.timeline?.kind !== "disk") {
    result.notes = [
      ...(result.notes || []),
      "Settling by physics is for disk braids for now: these yarns were tightened sideways.",
    ];
  }
  if (job) {
    // Shown as laid straight away, then replaced once tight.
    self.postMessage({ type: "laid", id, result });
    if (physics && result.timeline?.kind === "disk") {
      result = spec.settle === "crossing" ? formed(id, result, job) : settled(id, result, job);
    } else {
      status("Tightening the yarns…");
      const tight = tightenYarns(job, (fraction) =>
        status(`Tightening the yarns… ${Math.round(100 * fraction)}%`),
      );
      result = tightened(result, job, tight);
    }
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

// The braid settled by its own physics (rope.js): pulled clear of itself
// sideways first, then each yarn a chain of beads, clamped at the fell,
// fed at its oldest end from a bobbin pulling it back, and the braid drawn
// off by a weight lighter than the yarns' pull, so it is beaten up until
// its crossings jam.  Shown as it goes.
function settled(id, result, job) {
  // Pulled clear sideways first, far enough that no two yarns overlap when
  // seen in 3D: overlaps left for the physics to push apart could part
  // the wrong way.
  status("Pulling the yarns clear…");
  const clear = tightenYarns({ ...job, iterations: Math.max(job.iterations, 100) });
  const d = job.yarn_diameter;
  const [cx, cy] = job.centre;
  const yarns = [];
  for (let a = 0; a < job.n_yarns; a++) {
    const points = [];
    for (let i = job.n - 1; i >= 0; i--) {
      const k = a * job.n + i;
      points.push(
        (clear.xy[2 * k] - cx) / d,
        (clear.xy[2 * k + 1] - cy) / d,
        ((job.n - 1 - i) * job.spacing) / d,
      );
    }
    yarns.push(relay(points, 0.5));
  }
  const height = ((job.n - 1) * job.spacing) / d;
  const started = performance.now();
  let shown = started;
  const rest = settleRope({
    yarns,
    spacing: 0.5,
    feed: 1,
    force: 0.25 * job.n_yarns,
    turns: true,
    stretch: 100,
    contact: 100,
    steps: 200000,
    tolerance: 1e-3,
    progress: ({ yarns: now, rise, largestForce }) => {
      status(
        `Settling by physics… ${((performance.now() - started) / 1000).toFixed(0)} s, ` +
          `${Math.round((100 * -rise) / height)}% shorter`,
      );
      if (performance.now() - shown > 700) {
        shown = performance.now();
        self.postMessage({ type: "laid", id, result: onLevels(result, now, d) });
      }
      void largestForce;
    },
  });
  const out = onLevels(result, rest.yarns, d);
  out.info.closest_approach = round((1 - rest.deepest) * d);
  out.notes = [
    ...(out.notes || []),
    `Settled by physics: beaten up from ${height.toFixed(1)} to ` +
      `${(height + rest.rise).toFixed(1)} yarn diameters long, the end turning ` +
      `${((rest.turn * 180) / Math.PI).toFixed(0)}°.`,
  ];
  return out;
}

// The braid made crossing by crossing (form.js): from its oldest row up,
// each row beaten up against the made braid, with friction, and frozen
// into it; then the whole settled by its own physics (rope.js), as above,
// from that start rather than from the braid as laid.
function formed(id, result, job) {
  status("Pulling the yarns clear…");
  const clear = tightenYarns({ ...job, iterations: Math.max(job.iterations, 100) });
  const d = job.yarn_diameter;
  const [cx, cy] = job.centre;
  // Oldest end first, rising.
  const yarns = [];
  for (let a = 0; a < job.n_yarns; a++) {
    const points = [];
    for (let i = 0; i < job.n; i++) {
      const k = a * job.n + i;
      points.push((clear.xy[2 * k] - cx) / d, (clear.xy[2 * k + 1] - cy) / d, (i * job.spacing) / d);
    }
    yarns.push(points);
  }
  const height = ((job.n - 1) * job.spacing) / d;
  const started = performance.now();
  let shown = started;
  const show = (now) => {
    if (performance.now() - shown > 700) {
      shown = performance.now();
      self.postMessage({ type: "laid", id, result: onLevels(result, fellFirst(now), d) });
    }
  };
  const made = formBraid({
    yarns,
    // As braidpy lays a disk braid: a row every one and a half diameters.
    row: 1.5,
    friction: 0.3,
    feed: 1,
    weight: 0.25 * job.n_yarns,
    progress: ({ fraction, yarns: now }) => {
      status(
        `Making it crossing by crossing… ${Math.round(100 * fraction)}%, ` +
          `${((performance.now() - started) / 1000).toFixed(0)} s`,
      );
      show(now);
    },
  });
  const madeHeight = Math.max(...made.yarns.map((y) => y[y.length - 1]));
  const rest = settleRope({
    yarns: made.yarns,
    spacing: 0.5,
    feed: 1,
    force: 0.25 * job.n_yarns,
    turns: true,
    stretch: 100,
    contact: 100,
    steps: 200000,
    tolerance: 1e-3,
    progress: ({ yarns: now }) => {
      status(`Settling it… ${((performance.now() - started) / 1000).toFixed(0)} s`);
      show(now);
    },
  });
  const out = onLevels(result, fellFirst(rest.yarns), d);
  out.info.closest_approach = round((1 - rest.deepest) * d);
  out.notes = [
    ...(out.notes || []),
    `Made crossing by crossing, with friction: beaten up from ${height.toFixed(1)} to ` +
      `${madeHeight.toFixed(1)} yarn diameters long; then settled to ` +
      `${(madeHeight + rest.rise).toFixed(1)}, the end turning ` +
      `${((rest.turn * 180) / Math.PI).toFixed(0)}°.`,
  ];
  return out;
}

// Yarns turned over, newest end first, the fell at height 0: as rope.js
// gives them, for onLevels.
function fellFirst(yarns) {
  const top = Math.max(...yarns.map((y) => Math.max(...y.filter((_, k) => k % 3 === 2))));
  return yarns.map((y) => {
    const out = [];
    for (let i = y.length - 3; i >= 0; i -= 3) out.push(y[i], y[i + 1], top - y[i + 2]);
    return out;
  });
}

// Each yarn at the heights the page draws it at, highest first — its
// heights scaled to the settled braid's length.
function onLevels(result, yarns, d) {
  const out = structuredClone(result);
  const top = Math.max(...yarns.map((y) => y[y.length - 1]));
  out.strands.forEach((strand, a) => {
    const y = yarns[a];
    const laidTop = strand.points[0][2] || 1;
    strand.points = strand.points.map(([, , z]) => {
      const want = (z / laidTop) * top;
      // Where the yarn, going up, first comes to that height.
      for (let i = 3; i < y.length; i += 3) {
        if (y[i + 2] >= want) {
          const f = (want - y[i - 1]) / (y[i + 2] - y[i - 1] || 1);
          return [
            round((y[i - 3] + f * (y[i] - y[i - 3])) * d),
            round((y[i - 2] + f * (y[i + 1] - y[i - 2])) * d),
            round(want * d),
          ];
        }
      }
      return [round(y[y.length - 3] * d), round(y[y.length - 2] * d), round(want * d)];
    });
  });
  return out;
}

// A yarn's points again, evenly spaced, as rope.js wants them.
function relay(points, spacing) {
  return Array.from(self.relayYarn(Float64Array.from(points), spacing));
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
