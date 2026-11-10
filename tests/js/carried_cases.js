// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The carried tests' cases, run by tests/test_carried_js.py: each makes a
// braid by its carriers with web/carried.js, from a job braidpy wrote
// (braidpy.carried.carriers_job), and prints what it made, as JSON.
const path = require("path");
const fs = require("fs");
const { rounded } = require("./rounded.js");
const WEB = path.join(__dirname, "..", "..", "web");

const cases = {
  // With the maths library rounded (rounded.js), as braidpy's port is for
  // the test: rope.js and form.js first, whose mechanics carried.js takes
  // as they leave them.
  rounded() {
    rounded(path.join(WEB, "rope.js"));
    rounded(path.join(WEB, "form.js"));
    const { make } = rounded(path.join(WEB, "carried.js"));
    return make(JSON.parse(fs.readFileSync(process.argv[3], "utf8")));
  },
  // With its own.
  plain() {
    const { make } = require(path.join(WEB, "carried.js"));
    return make(JSON.parse(fs.readFileSync(process.argv[3], "utf8")));
  },
};

console.log(JSON.stringify(cases[process.argv[2]]()));
