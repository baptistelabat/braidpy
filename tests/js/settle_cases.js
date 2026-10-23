// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The page's settle worker's cases, run by tests/test_settle_js.py.
const path = require("path");
const fs = require("fs");

const cases = {};

// The page's own settle worker (web/settle.js), run on a braid laid by
// braidpy (read from a file), settled as asked — "settled" beaten up,
// "formed" crossing by crossing — with its twist kept or free: its yarns
// as they went into the physics and as they came out, and how far its end
// turned, for braidpy to measure their closure's linking numbers.
cases.paged = () => {
  const vm = require("vm");
  const web = path.join(__dirname, "..", "..", "web");
  const page = { console, performance, setTimeout, structuredClone, postMessage: () => {} };
  page.self = page;
  page.importScripts = (...names) =>
    names.forEach((name) => vm.runInContext(fs.readFileSync(path.join(web, name), "utf8"), page, { filename: name }));
  vm.createContext(page);
  vm.runInContext(fs.readFileSync(path.join(web, "settle.js"), "utf8"), page, { filename: "settle.js" });
  page.status = () => {};
  const result = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
  const job = result.tighten;
  delete result.tighten;
  const seen = {};
  const settleRope = page.settleRope;
  page.settleRope = (asked) => {
    seen.laid = asked.yarns.map((y) => Array.from(y));
    const rest = settleRope({ ...asked, progress: null });
    seen.settled = rest.yarns;
    seen.turn = rest.turn;
    seen.deepestEver = rest.deepestEver;
    return rest;
  };
  const out = page[process.argv[4]](1, result, { ...job, twist: process.argv[5] });
  return { ...seen, notes: out.notes };
};

// A braid made on a marudai by the page's settle worker, its moments kept
// for Grow as the page keeps them (frames.js), packed as the site keeps
// them and unpacked: each put back together, beside the moment as it was,
// whole.  The largest gap between the two, in yarn diameters; how far the
// braid had turned, in all, by the moments kept; and the share of their
// beads frozen, put back rather than kept.
cases.grown = async () => {
  // Run in this context, as settle_node.js runs it: in a context of its
  // own, the marudai is several times slower.
  const vm = require("vm");
  const web = path.join(__dirname, "..", "..", "web");
  const page = globalThis;
  page.self = page;
  page.postMessage = () => {};
  page.importScripts = (...names) =>
    names.forEach((name) => vm.runInThisContext(fs.readFileSync(path.join(web, name), "utf8"), { filename: name }));
  vm.runInThisContext(fs.readFileSync(path.join(web, "settle.js"), "utf8"), { filename: "settle.js" });
  const frames = fs.readFileSync(path.join(web, "frames.js"), "utf8").replace(/^export /gm, "");
  const { pack, unpack, wholeFrame } = vm.runInThisContext(`(() => { ${frames}; return { pack, unpack, wholeFrame }; })()`);
  page.status = () => {};
  const result = JSON.parse(fs.readFileSync(process.argv[3], "utf8"));
  const job = result.tighten;
  delete result.tighten;
  const d = job.yarn_diameter;
  // Every moment as marudai.js gives it, whole.
  const whole = [];
  const begin = page.beginOnMarudai;
  page.beginOnMarudai = (asked) => {
    const making = begin(asked);
    const look = making.look;
    making.look = () => {
      const moment = look();
      if (!whole.length) whole.push(moment);
      return moment;
    };
    let watch = null;
    Object.defineProperty(making.hooks, "watch", {
      get: () => watch,
      set: (told) => {
        watch = told && ((moment) => (whole.push(moment), told(moment)));
      },
    });
    return making;
  };
  const settled = await page.settle({ id: 1, result, job, settle: "marudai" });
  const marudai = unpack(JSON.parse(JSON.stringify(pack(settled.marudai, d / 100), (_, v) =>
    ArrayBuffer.isView(v) ? Array.from(v) : v)));
  if (marudai.frames.length !== whole.length) throw new Error(`${marudai.frames.length} moments of ${whole.length}`);
  let gap = 0, turned = 0, frozen = 0, all = 0;
  marudai.frames.forEach((frame, k) => {
    const back = wholeFrame(frame, marudai.base);
    const was = whole[k];
    turned = Math.max(turned, Math.abs(Math.atan2(frame.turn[1], frame.turn[0])));
    was.yarns.forEach((yarn, t) => {
      all += yarn.length;
      frozen += 3 * frame.frozen[t];
      for (let i = 0; i < yarn.length; i += 3) {
        const at = [yarn[i] * d, -yarn[i + 1] * d, (was.tip - yarn[i + 2]) * d];
        for (let j = 0; j < 3; j++) gap = Math.max(gap, Math.abs(back.yarns[t][i + j] - at[j]) / d);
      }
    });
  });
  return { moments: whole.length, gap, turned, frozen: frozen / all };
};

Promise.resolve(cases[process.argv[2]]()).then((out) => console.log(JSON.stringify(out)));
