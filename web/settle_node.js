// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The page's own settling (settle.js), run by Node when the site is built
// (web/build.py): a braid made with the site, laid by braidpy, settled as
// the page would settle it as it comes — on a marudai if it is made move by
// move, sideways if not — so a visitor is shown it settled at once.
//
//   node web/settle_node.js laid.json settled.json
//
// settle.js is a worker's script: it is run here as it is there, its
// importScripts and postMessage given to it.

const fs = require("fs");
const path = require("path");
const vm = require("vm");

const [, , from, to] = process.argv;
// Run in this context, not a vm context of its own: the code's every global
// would be looked up through the context there, several times slower.
globalThis.self = globalThis;
globalThis.postMessage = () => {};
globalThis.importScripts = (...names) =>
  names.forEach((name) => vm.runInThisContext(fs.readFileSync(path.join(__dirname, name), "utf8"), { filename: name }));
vm.runInThisContext(fs.readFileSync(path.join(__dirname, "settle.js"), "utf8"), { filename: "settle.js" });

// Grow replays a braid made on a marudai frame by frame, each frame every
// yarn whole: a big sinnet's frames are hundreds of megabytes, even thinned.
// So many, evenly spaced, the first and the last among them, as fit in a
// few megabytes, replay a small braid's making; a big one keeps none, and
// Grow replays it growing, as it does any braid not made on a marudai.
const BUDGET = 3e6;
function fewer(frames) {
  if (!frames?.length) return frames;
  const each = JSON.stringify(frames[frames.length - 1]).length;
  const room = Math.floor(BUDGET / each);
  if (room >= frames.length) return frames;
  if (room < 2) return [];
  return Array.from({ length: room }, (_, k) => frames[Math.round((k * (frames.length - 1)) / (room - 1))]);
}

const result = JSON.parse(fs.readFileSync(from, "utf8"));
const job = result.tighten;
delete result.tighten;
// As the page settles a braid left to its own choices (worker.js).
const settle = result.disk ? "marudai" : "sideways";
globalThis.settle({ id: 1, result, job: job ?? null, settle, twist: undefined }).then((settled) => {
  if (settled.marudai) settled.marudai.frames = fewer(settled.marudai.frames);
  fs.writeFileSync(to, JSON.stringify(settled));
});
