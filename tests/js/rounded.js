// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A script of web/ loaded again with every result of cos, sin, atan2 and
// asin rounded to single precision.  Python's maths library and
// JavaScript's may differ in the last place; rounded so, they give the same
// numbers, and a Python port rounded the same way (tests/js_maths.py) and
// given JavaScript's hypot makes the same braid, bead for bead.
const fs = require("fs");

function rounded(file) {
  const R = Object.create(Math);
  for (const name of ["cos", "sin", "atan2", "asin"]) {
    R[name] = (...args) => Math.fround(Math[name](...args));
  }
  const exported = { exports: {} };
  new Function("module", "Math", fs.readFileSync(file, "utf8"))(exported, R);
  return exported.exports;
}

module.exports = { rounded };
