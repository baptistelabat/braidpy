// The page's settle worker's cases, run by tests/test_settle_js.py.
const path = require("path");
const fs = require("fs");
const { linkingMatrix } = require("./linking.js");

const cases = {};

// The page's own settle worker (web/settle.js), run on a braid laid by
// braidpy (read from a file), settled as asked — "settled" beaten up,
// "formed" crossing by crossing — with its twist kept or free: its
// closure's linking numbers as it went into the physics and as it came
// out, its end turned back.
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
    seen.laid = linkingMatrix(asked.yarns, 0);
    const rest = settleRope({ ...asked, progress: null });
    seen.settled = linkingMatrix(rest.yarns, rest.turn);
    seen.turn = rest.turn;
    seen.deepestEver = rest.deepestEver;
    return rest;
  };
  const out = page[process.argv[4]](1, result, { ...job, twist: process.argv[5] });
  return { ...seen, notes: out.notes };
};

console.log(JSON.stringify(cases[process.argv[2]]()));
