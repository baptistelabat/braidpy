// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The two workers: braidpy, through Pyodide, lays the braid (worker.js);
// settle.js settles it, and can be stopped and started afresh.  Braids made
// are kept, a dozen of them, to go back to at once; one being made goes on
// from where it was when more of it is asked for.

import { onChosen, rebase } from "./colours.js";
import { showMaking, showKin } from "./info.js";
import * as THREE from "three";
import { forgetDefaults, guessChoices, showDefaults } from "./defaults.js";
import { UNLISTED, catalogue, renderFields, setCatalogue } from "./fields.js";
import { unpack } from "./frames.js";
import { machineShapes, machineWanted } from "./machine.js";
import { $ } from "./page.js";
import { braid, fit, show, showFrame, shownLaid, topAtFrame } from "./scene.js";
import { readSpec, specFromHash, writeSpec } from "./spec.js";

// Started by the page itself, before its modules (index.html).
export const worker = window.braidpy.worker;
export let pending = 0;

function setStatus(text, error = false) {
  $("status").textContent = text;
  $("status").classList.toggle("error", error);
}

// The yarns are settled in a worker of their own (settle.js): ended and
// started again, it stops at once whatever it was making.  It keeps the
// braid on its marudai between braids, to make more of it.
let settler = null;
let settling = null; // {id, settle} while it works
// A .b3d asked of the settler, waiting: its id and what to tell.
let b3dAsked = null;
let b3dCount = 0;
function startSettler() {
  if (settler) settler.terminate();
  settler = new Worker("settle.js");
  settling = null;
  b3dAsked?.reject(new Error("another braid was asked for"));
  b3dAsked = null;
  settler.onmessage = ({ data }) => {
    if (data.type === "b3d") {
      if (b3dAsked?.id !== data.id) return;
      if (data.error) b3dAsked.reject(new Error(data.error));
      else b3dAsked.resolve(data.text);
      b3dAsked = null;
      return;
    }
    if ((data.type === "result" || data.type === "error") && settling?.id === data.id) settling = null;
    heard(data);
  };
}
startSettler();

// The braid as braid3dmin saves it, made on the marudai by the settler
// (b3d.js): a promise of the file's text.
export function b3dOf(result) {
  b3dAsked?.reject(new Error("asked again"));
  return new Promise((resolve, reject) => {
    b3dAsked = { id: ++b3dCount, resolve, reject };
    settler.postMessage({
      type: "b3d",
      id: b3dCount,
      result,
      twist: result.used?.twist,
      d: result.used?.yarn_diameter ?? result.yarn_diameter,
    });
  });
}

// The braids made, by what they were made from: going back to one is then
// instant.
const madeBefore = new Map();
const KEEP = 12;
const keys = new Map(); // id -> what it was made from
// Each braid's kin, by what it was made from, for when it is shown again.
const kinOf = new Map();
// And the braid made other ways.
const makingOf = new Map();

function fromBraidpy({ data }) {
  // Laid by braidpy: shown, and handed on to be settled — stopping what
  // was being settled unless it can go on from it, on the marudai.
  if (data.type === "laid" && "settle" in data) {
    if (data.id !== pending) return;
    if (settling && settling.settle !== "marudai") startSettler();
    settling = { id: data.id, settle: data.settle };
    const { result, job, settle, twist } = data;
    settler.postMessage({ type: "settle", id: data.id, result, job, settle, twist });
    heard({ type: "laid", id: data.id, result });
    return;
  }
  heard(data);
}

// A braid made with the site, shown at once: what Python says as it starts
// follows that, rather than replacing it.
const AT_ONCE = "Made with the site: shown at once.";
let shownAtOnce = 0;

function heard(data) {
  if (data.type === "status") {
    setStatus(shownAtOnce && shownAtOnce === pending ? `${AT_ONCE} ${data.text}` : data.text);
  } else if (data.type === "ready") {
    offer(data.catalogue);
    $("build").disabled = false;
    $("build").textContent = "Braid";
    // Unless a braid made with the site is already being shown.
    if (!pending) submit();
    else if (shownAtOnce === pending) setStatus(AT_ONCE);
  } else if (data.type === "making") {
    if (data.id !== pending) return;
    if (keys.has(data.id)) {
      makingOf.set(keys.get(data.id), data.making);
      if (makingOf.size > KEEP) makingOf.delete(makingOf.keys().next().value);
    }
    showMaking(data.making);
  } else if (data.type === "sinnet") {
    document.dispatchEvent(new CustomEvent("braid-sinnet", { detail: data }));
  } else if (data.type === "kin") {
    if (data.id !== pending) return;
    if (keys.has(data.id)) {
      kinOf.set(keys.get(data.id), data.kin);
      if (kinOf.size > KEEP) kinOf.delete(kinOf.keys().next().value);
    }
    showKin(data.kin);
  } else if (data.type === "turned" || data.type === "origin") {
    // The machine's handle, turned by hand: for machine.js.
    document.dispatchEvent(new CustomEvent(`machine-${data.type}`, { detail: data }));
  } else if (data.type === "geometry") {
    machineShapes.set(data.name, data.shape);
    if (data.name === machineWanted) document.dispatchEvent(new CustomEvent("machine-shape"));
  } else if (data.type === "frame") {
    if (data.id !== pending || !braid) return;
    // The making, as it goes: framed on it from its first moment.
    showFrame(data.frame, data.disk, data.colours);
    if (!braid.framed) {
      braid.framed = true;
      braid.turner.updateMatrixWorld(true);
      braid.box = new THREE.Box3().setFromObject(braid.frame);
      fit();
    }
    topAtFrame(data.frame);
  } else if (data.type === "laid") {
    if (data.id !== pending) return;
    // Settling sends the braid as it goes: the view stays put.
    rebase(data.result);
    show(data.result, null, shownLaid === data.id);
  } else if (data.type === "result") {
    if (data.id !== pending) return;
    if (keys.has(data.id) && (data.seconds || data.premade)) {
      madeBefore.set(keys.get(data.id), data.result);
      if (madeBefore.size > KEEP) madeBefore.delete(madeBefore.keys().next().value);
    }
    shownAtOnce = data.premade ? data.id : 0;
    setStatus(
      data.premade
        ? AT_ONCE
        : data.seconds
          ? `Made in ${data.seconds.toFixed(1)} s.`
          : "Made before: shown again.",
    );
    // The tight braid replaces the laid one where the view already is —
    // unless it was beaten up, much shorter than it was laid.
    rebase(data.result);
    show(data.result, data.seconds, shownLaid === data.id && data.result.settled === "sideways");
    showDefaults(data.result.used);
    document.dispatchEvent(
      new CustomEvent("machine-met", { detail: data.result.info?.collision?.at ?? [] }),
    );
  } else if (data.type === "error") {
    if (data.id !== undefined && data.id !== pending) return;
    setStatus(data.message, true);
  }
}

// The form, filled with what can be made as soon as that is known: from
// the site (catalogue.json), long before braidpy is ready to make any of
// it — or, without it, from braidpy when it is.
let offered = false;
function offer(sources) {
  if (offered || !sources) return;
  offered = true;
  setCatalogue(sources);
  const select = $("source");
  const spec = specFromHash() || { source: "word", ...catalogue.word.defaults };
  for (const [source, about] of Object.entries(catalogue)) {
    // Out of the menu for now, but still made from a link to it.
    if (UNLISTED.has(source) && spec.source !== source) continue;
    select.append(new Option(about.title, source));
  }
  writeSpec(spec);
  // A braid made with the site is shown at once, before Python is ready.
  premadeFor(readSpec()).then((found) => {
    if (found && !pending) submit();
  });
}

// The braids made with the site (web/build.py, braidpy.web.premade): each
// catalogued braid and braid word example as it comes, laid as braidpy lays
// it.  One asked for is shown from there at once, Python or not.
const premadeIndex = fetch("made/index.json")
  .then((response) => (response.ok ? response.json() : []))
  .catch(() => []);
// What only the page does with a braid — how it is settled, its colours —
// and not what braidpy makes.
const PAGE_ONLY = new Set(["settle", "twist", "colours"]);

function same(a, b) {
  if (a === undefined || b === undefined) return a === b;
  const x = Number(a), y = Number(b);
  return String(a).trim() !== "" && Number.isFinite(x) && Number.isFinite(y) ? x === y : String(a) === String(b);
}

// The braid made with the site that is the one asked for: each setting as
// asked, or the source's default where it was not.  Its index entry: the
// file it was laid in, and the one it was settled in, if it was.
async function premadeFor(spec) {
  const defaults = catalogue?.[spec.source]?.defaults;
  if (!defaults) return null;
  for (const entry of await premadeIndex) {
    const made = entry.spec;
    if (made.source !== spec.source) continue;
    const settings = new Set([...Object.keys(made), ...Object.keys(spec)].filter((k) => !PAGE_ONLY.has(k)));
    const as = (from, k) => (k in from ? from[k] : defaults[k]);
    if ([...settings].every((k) => same(as(spec, k), as(made, k)))) return entry;
  }
  return null;
}

async function fetched(file) {
  try {
    const response = await fetch(`made/${file}`);
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

// The braid asked for, made with the site: settled, if it was and is to be
// settled as it comes; laid, for the page to settle, if not.
async function premade(spec) {
  const entry = await premadeFor(spec);
  if (!entry) return null;
  if (entry.settled && !("settle" in spec) && !("twist" in spec)) {
    const settled = await fetched(entry.settled);
    if (settled) return { settled: { ...settled, marudai: unpack(settled.marudai) } };
  }
  const laid = await fetched(entry.file);
  return laid ? { laid } : null;
}
window.braidpy.catalogue.then(offer);

// What braidpy said while the page loaded, then the rest as it comes.
worker.onmessage = fromBraidpy;
for (const data of window.braidpy.early.splice(0)) fromBraidpy({ data });

// Published as a beta, it says so.
if (location.pathname.includes("/studio-beta/")) {
  const badge = document.createElement("span");
  badge.className = "beta";
  badge.textContent = "beta";
  badge.title = "Braid Studio as it is being made: it may change, or break";
  document.querySelector("h1").append(" ", badge);
}

// Braid: the braid described — made before, shown again; more of the one
// on the marudai, made on from it; anything else made anew, stopping what
// was being made.
export function submit() {
  const spec = readSpec();
  pending += 1;
  history.replaceState(null, "", "#" + new URLSearchParams(spec).toString());
  const key = JSON.stringify(spec, Object.keys(spec).sort());
  keys.set(pending, key);
  showKin(kinOf.get(key));
  showMaking(makingOf.get(key));
  if (madeBefore.has(key)) {
    const result = madeBefore.get(key);
    madeBefore.delete(key);
    madeBefore.set(key, result);
    heard({ type: "result", id: pending, result, seconds: 0 });
    return;
  }
  const id = pending;
  premade(spec).then((made) => {
    if (id !== pending) return;
    if (made?.settled) {
      // Shown settled at once; braidpy, when it is ready, finds its kin
      // and other ways from what is known of it.
      heard({ type: "result", id, result: made.settled, seconds: 0, premade: true });
      worker.postMessage({ type: "build", id, spec, info: made.settled.info });
    } else if (made?.laid) {
      worker.postMessage({ type: "build", id, spec, premade: made.laid });
    } else {
      worker.postMessage({ type: "build", id, spec });
    }
  });
}

// A colour chosen by hand belongs to the braid asked for, so the link keeps
// it — written again without making anything, since nothing has changed but
// what the strands are painted with.
onChosen((saved) => {
  if (!saved) return;
  history.replaceState(null, "", "#" + new URLSearchParams(readSpec()).toString());
});

// Reset: stop whatever is being made, and forget the marudai and the
// braids made, so that the next is made from the start.
$("restart").addEventListener("click", () => {
  pending += 1;
  startSettler();
  madeBefore.clear();
  setStatus("Reset: the next braid is made from the start.");
});

$("form").addEventListener("submit", (event) => {
  event.preventDefault();
  submit();
});

$("source").addEventListener("change", () => {
  renderFields($("source").value);
  forgetDefaults();
  guessChoices($("source").value);
});
