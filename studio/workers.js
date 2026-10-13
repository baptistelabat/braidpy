// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The two workers: braidpy, through Pyodide, lays the braid (worker.js);
// settle.js settles it, and can be stopped and started afresh.  Braids made
// are kept, a dozen of them, to go back to at once; one being made goes on
// from where it was when more of it is asked for.

import * as THREE from "three";
import { forgetDefaults, guessChoices, showDefaults } from "./defaults.js?v=5cce1842b4";
import { UNLISTED, catalogue, renderFields, setCatalogue } from "./fields.js?v=5cce1842b4";
import { machineShapes, machineWanted } from "./machine.js?v=5cce1842b4";
import { $ } from "./page.js?v=5cce1842b4";
import { braid, fit, show, showFrame, shownLaid, topAtFrame } from "./scene.js?v=5cce1842b4";
import { readSpec, specFromHash, writeSpec } from "./spec.js?v=5cce1842b4";

const PYODIDE_URL =
  new URLSearchParams(location.search).get("pyodide") ||
  "https://cdn.jsdelivr.net/pyodide/v0.27.8/full/";

export const worker = new Worker("worker.js?v=5cce1842b4");
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
function startSettler() {
  if (settler) settler.terminate();
  settler = new Worker("settle.js?v=5cce1842b4");
  settling = null;
  settler.onmessage = ({ data }) => {
    if ((data.type === "result" || data.type === "error") && settling?.id === data.id) settling = null;
    heard(data);
  };
}
startSettler();

// The braids made, by what they were made from: going back to one is then
// instant.
const madeBefore = new Map();
const KEEP = 12;
const keys = new Map(); // id -> what it was made from

worker.onmessage = ({ data }) => {
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
};

function heard(data) {
  if (data.type === "status") {
    setStatus(data.text);
  } else if (data.type === "ready") {
    setCatalogue(data.catalogue);
    const select = $("source");
    const spec = specFromHash() || { source: "word", ...catalogue.word.defaults };
    for (const [source, about] of Object.entries(catalogue)) {
      // Out of the menu for now, but still made from a link to it.
      if (UNLISTED.has(source) && spec.source !== source) continue;
      select.append(new Option(about.title, source));
    }
    writeSpec(spec);
    $("build").disabled = false;
    $("build").textContent = "Braid";
    submit();
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
    show(data.result, null, shownLaid === data.id);
  } else if (data.type === "result") {
    if (data.id !== pending) return;
    if (keys.has(data.id) && data.seconds) {
      madeBefore.set(keys.get(data.id), data.result);
      if (madeBefore.size > KEEP) madeBefore.delete(madeBefore.keys().next().value);
    }
    setStatus(
      data.seconds ? `Made in ${data.seconds.toFixed(1)} s.` : "Made before: shown again.",
    );
    // The tight braid replaces the laid one where the view already is —
    // unless it was beaten up, much shorter than it was laid.
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

worker.postMessage({ type: "init", pyodideUrl: PYODIDE_URL });

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
  if (madeBefore.has(key)) {
    const result = madeBefore.get(key);
    madeBefore.delete(key);
    madeBefore.set(key, result);
    heard({ type: "result", id: pending, result, seconds: 0 });
    return;
  }
  worker.postMessage({ type: "build", id: pending, spec });
}

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
