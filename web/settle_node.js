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
// frames.js, a module of the page's, run here as a script: what it exports
// is then ours.
const { pack } = vm.runInThisContext(
  `(() => { ${fs.readFileSync(path.join(__dirname, "frames.js"), "utf8").replace(/^export /gm, "")}; return { pack }; })()`,
  { filename: "frames.js" },
);

// Grow replays a braid made on a marudai moment by moment, each moment
// only its beads still free, packed (frames.js): the rest is put back from
// the braid as it ends.  So many moments, evenly spaced, the first and the
// last among them, as fit in a few megabytes with the braid as it ends; a
// braid too big for two keeps none, and Grow replays it growing, as it does
// any braid not made on a marudai.
const BUDGET = 3e6;
function fewer(marudai) {
  const frames = marudai.frames;
  if (!frames?.length) return marudai;
  const base = JSON.stringify(marudai.base).length;
  const each = frames.reduce((sum, frame) => sum + JSON.stringify(frame).length, 0) / frames.length;
  const room = Math.floor((BUDGET - base) / each);
  if (room >= frames.length) return marudai;
  if (room < 2) return { ...marudai, base: [], frames: [] };
  const kept = Array.from({ length: room }, (_, k) => frames[Math.round((k * (frames.length - 1)) / (room - 1))]);
  return { ...marudai, frames: kept };
}

// Typed arrays written as the arrays they are, not as objects.
const plain = (_, value) => (ArrayBuffer.isView(value) ? Array.from(value) : value);

const result = JSON.parse(fs.readFileSync(from, "utf8"));
const job = result.tighten;
delete result.tighten;
// As the page settles a braid left to its own choices (worker.js).
const settle = result.disk ? "marudai" : "sideways";
globalThis.settle({ id: 1, result, job: job ?? null, settle, twist: undefined }).then((settled) => {
  // Hundredths of a yarn diameter: closer than the eye can tell.
  if (settled.marudai) settled.marudai = fewer(pack(settled.marudai, job.yarn_diameter / 100));
  fs.writeFileSync(to, JSON.stringify(settled, plain));
});
