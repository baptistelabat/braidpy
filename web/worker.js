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
importScripts("tighten.js", "rope.js", "form.js", "marudai.js");

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
  if (job) {
    // Shown as laid straight away, then replaced once tight.
    self.postMessage({ type: "laid", id, result });
    if (settle !== "sideways") {
      if (settle === "marudai") result = onMarudai(id, result, { ...job, twist: spec.twist });
      else if (settle === "crossing") result = formed(id, result, job);
      else result = settled(id, result, job);
    } else {
      status("Tightening the yarns…");
      const tight = tightenYarns(job, (fraction) =>
        status(`Tightening the yarns… ${Math.round(100 * fraction)}%`),
      );
      result = tightened(result, job, tight);
    }
    result.settled = settle;
  }
  // What the braid was made with, for the page to show what was taken by
  // default: the marudai pulls its yarns tight itself, in no set steps.
  result.used = {
    yarn_diameter: result.yarn_diameter,
    iterations: settle === "marudai" && job ? null : job?.iterations ?? 0,
    // The braid's own choices, for the page to mark as its defaults.
    settle: job ? (result.disk ? "marudai" : "sideways") : undefined,
    twist: result.disk ? (result.disk.held ? "keep" : result.disk.twists ? "turns" : "free") : undefined,
  };
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

// The braid made move by move as on a marudai (marudai.js): the disk's own
// moves, each moved yarn laid over the others to its new carrier and drawn
// tight, the braid relaxing and turning to balance after each step.
function onMarudai(id, result, job) {
  const d = job.yarn_diameter;
  const started = performance.now();
  let shown = started;
  // Each moment of the making, kept for Grow to replay, and shown as it
  // comes, a few times a second; the mirror as the first moments have it.
  const frames = [];
  let mirror = null;
  // Kept, the braid is held throughout, its twist kept; untwisted, it
  // hangs free throughout, and turning the bobbins together turns it along.
  const twist = job.twist ?? "auto";
  const holding = {
    keep: { held: true, twists: true },
    turns: { held: false, twists: true },
    free: { held: false, twists: false },
  }[twist] ?? {};
  const made = makeOnMarudai({
    ...result.disk,
    ...holding,
    watch: (frame) => {
      frames.push(frame);
      if (performance.now() - shown < 80) return;
      shown = performance.now();
      if (!mirror) {
        const ends = frame.yarns.filter((y) => y.length).map((y) => [y[y.length - 3], y[y.length - 2], y[y.length - 1]]);
        mirror = mirrorOf(
          {
            rim: {
              radius: ends.reduce((s, [x, y]) => s + Math.hypot(x, y), 0) / ends.length,
              height: ends.reduce((s, [, , z]) => s + z, 0) / ends.length,
            },
            tip: frame.tip,
          },
          d,
        );
      }
      const disk = { z: round(-mirror.above), radius: round(mirror.radius), hole: round(mirror.hole) };
      self.postMessage({ type: "frame", id, frame: pageFrame(frame, d, mirror), disk, colours: result.strands.map((s) => s.colour) });
    },
    progress: ({ fraction }) => {
      status(
        `Making it move by move… ${Math.round(100 * fraction)}%, ` +
          `${((performance.now() - started) / 1000).toFixed(0)} s`,
      );
    },
  });
  const out = onLevels(result, upsideDown(made.yarns), d);
  // Kept to a few hundred moments: Grow replays them in twelve seconds.
  const every = Math.max(1, Math.ceil(frames.length / 600));
  const kept = frames.filter((_, i) => i % every === 0 || i === frames.length - 1);
  out.marudai = onMarudaiFrame(made, d, kept);
  out.notes = [
    ...(out.notes || []),
    `Made move by move, as on a marudai: ${made.tip.toFixed(1)} yarn diameters long.`,
  ];
  // Every bobbin turning together, the braid hanging free: it turns along,
  // and what those turns would have twisted in is not there.
  const n = result.disk.start.length;
  const turns = result.disk.steps.some(
    (step) => step.length === n && step.every(([, d]) => d && d === step[0][1]),
  );
  // (A disk braid's own turns carry the braid round anyway, as a disk does.)
  if (twist === "free" && turns && result.disk.twists) {
    out.notes.push(
      made.tip < 1
        ? "Untwisted: hanging free, the braid turned along with the bobbins, and nothing braided."
        : "Untwisted: hanging free, the braid turned along with the bobbins, so their turns twisted nothing in. It is no longer the braid its word says.",
    );
  }
  return out;
}

// The yarns' tails above the fell, and the marudai's mirror they lie over,
// in the page's units, turned upside down as the braid is (upsideDown,
// fellFirst): the fell at height 0.  The tails come up from the fell to the
// hole in the mirror, where marudai.js pulls them; from there they lie flat
// across the mirror to its edge, and drop over it towards their bobbins,
// as on a real marudai.  A yarn being carried over the others to its new
// place is still above the mirror: it lies across at its own height.
const MIRROR = 2.5; // the mirror's radius, in its hole's
function mirrorOf(made, d) {
  return {
    hole: 0.97 * made.rim.radius * d,
    radius: MIRROR * made.rim.radius * d,
    // How far above the fell the mirror is, as the yarns' ends are.
    above: (made.rim.height - made.tip) * d,
    drop: 0.4 * made.rim.radius * d,
  };
}

// One yarn, flat [x, y, z, …] as marudai.js gives it, in the page's frame,
// the fell (``tip``) at height 0, and on across the mirror and over its edge.
function onMirror(yarn, tip, d, mirror) {
  const out = [];
  for (let i = 0; i < yarn.length; i += 3) out.push([yarn[i] * d, -yarn[i + 1] * d, (tip - yarn[i + 2]) * d]);
  // While the yarns are first laid out, those still to come have nothing.
  if (!out.length) return out;
  const [x, y, z] = out[out.length - 1];
  const r = Math.hypot(x, y) || 1;
  const ux = x / r, uy = y / r;
  const level = Math.min(-mirror.above, z);
  const at = (radius, height) => [ux * radius, uy * radius, height];
  out.push(
    at(Math.max(r, mirror.hole) + 0.5 * d, level),
    at(mirror.radius, level),
    at(1.02 * mirror.radius, -mirror.above + 0.3 * mirror.drop),
    at(1.03 * mirror.radius, -mirror.above + mirror.drop),
  );
  return out;
}

function onMarudaiFrame(made, d, frames) {
  let top = -Infinity;
  for (const y of made.yarns) for (let i = 2; i < y.length; i += 3) top = Math.max(top, y[i]);
  const mirror = mirrorOf(made, d);
  return {
    tails: made.tails.map((tail) => onMirror(tail, top, d, mirror).map((p) => p.map(round))),
    disk: { z: round(-mirror.above), radius: round(mirror.radius), hole: round(mirror.hole) },
    frames: frames.map((frame) => pageFrame(frame, d, mirror)),
  };
}

// A moment in the making, for the page to draw: every yarn whole, in the
// page's frame, its fell at height 0.
function pageFrame(frame, d, mirror) {
  return {
    what: frame.what,
    thread: frame.thread,
    step: frame.step,
    yarns: frame.yarns.map((yarn) => Float32Array.from(onMirror(yarn, frame.tip, d, mirror).flat())),
  };
}

// A braid made as on a marudai, its fell on top, turned upside down for
// the page, which draws the fell at the bottom: newest end first, the fell
// at height 0.  Turned over, not reflected — y changes sign with z — so it
// stays the braid it is, not its mirror image.
function upsideDown(yarns) {
  return fellFirst(yarns.map((y) => y.map((v, k) => (k % 3 === 1 ? -v : v))));
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
