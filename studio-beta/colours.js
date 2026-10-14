// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The colour of each strand, chosen by hand.
//
// Whatever makes the braid picks the colours to start with — a word by the
// palette, a machine by its carriers, a sinnet by its own scheme — and this
// lets them be changed afterwards, strand by strand. The choice is put on
// the braid in one place, so everything drawn from it comes out the same
// colour: the braid in 3D, its cross-section, the view from above, the
// carriers, and the braid grown frame by frame.
//
// A colour change does not remake the braid. The strands are the ones that
// were made; only what they are painted with changes, so it is immediate
// however long the braid took.

import { $ } from "./page.js?v=0e16307d69";

// Colour chosen per strand, by its place in the braid; null where none was.
let chosen = [];
// The colours the braid was made with.  Kept because what is drawn is worked
// out afresh each time rather than painted over what was painted before: a
// strand shown among the others has to be able to come back.
let made = [];
// The strand being pointed at in the list.  It keeps its colour while the
// others are muted, which is the only way to be sure which one is about to
// change when several are the same colour.
let picked = null;
const listeners = [];

/** Run `callback` whenever a colour is chosen, to draw the braid again. */
export function onChosen(callback) {
  listeners.push(callback);
}

/** Remember the colours a braid was made with, before any are put on it. */
export function rebase(result) {
  if (result && result.strands) made = result.strands.map((strand) => strand.colour);
}

/** The colour a strand is really in, whatever is drawn while one is picked. */
export function trueColour(i, fallback) {
  return chosen[i] || made[i] || fallback;
}

/** Show one strand among the others; null shows them all alike. */
export function pick(i) {
  if (picked === i) return;
  picked = i;
  tell();
}

// Muting is a blend, not a fade: the three ways a strand is drawn — a
// three.js material and two canvases — all take a solid colour, so mixing it
// here keeps one mechanism where opacity would need three.  A quarter of the
// strand's own colour is left in it, enough to keep the braid readable.
function muted(colour) {
  const hex = long(colour);
  const mix = (at) => Math.round(parseInt(hex.slice(at, at + 2), 16) * 0.25 + 0x8c * 0.75);
  return (
    "#" +
    [1, 3, 5]
      .map((at) => mix(at).toString(16).padStart(2, "0"))
      .join("")
  );
}

/**
 * The colour to draw strand `i` in: the one chosen for it, or `fallback`.
 *
 * For the drawings made before the braid is — the word as it is typed, the
 * carriers on the machine — which have a palette of their own to fall back
 * on rather than a braid to take colours from.
 */
export function strandColour(i, fallback) {
  const own = chosen[i] || fallback;
  return picked === null || picked === i ? own : muted(own);
}

/** The colours chosen, as the description writes them: `#rgb,,#rgb`. */
export function chosenColours() {
  if (!chosen.some(Boolean)) return "";
  return chosen.map((colour) => colour || "").join(",");
}

/** Take the colours from a description, as `readSpec` wrote them. */
export function useColours(text) {
  chosen = String(text || "")
    .split(",")
    .map((part) => (part.trim() ? part.trim().toLowerCase() : null));
  if (!chosen.some(Boolean)) chosen = [];
}

/**
 * Put the chosen colours on a braid, and list its strands.
 *
 * Called wherever a braid is about to be drawn, so there is one place that
 * decides what colour a strand is.
 */
export function paint(result) {
  if (!result || !result.strands) return result;
  result.strands.forEach((strand, i) => {
    strand.colour = strandColour(i, trueColour(i, strand.colour));
  });
  list(result);
  return result;
}

function list(result) {
  const panel = $("strands");
  const into = $("strand-list");
  if (!panel || !into) return;
  const strands = result.strands;
  panel.hidden = false;

  // Rebuilt only when the braid has different strands: a colour picker the
  // pointer is inside must not be taken away while it is being used.
  if (into.childElementCount !== strands.length) {
    into.replaceChildren();
    strands.forEach((strand, i) => {
      const row = document.createElement("li");
      const label = document.createElement("label");
      const picker = document.createElement("input");
      picker.type = "color";
      picker.dataset.strand = String(i);
      picker.title = `The colour of ${strand.name}`;
      const name = document.createElement("span");
      name.textContent = strand.name;
      label.append(picker, name);
      row.append(label);
      into.append(row);
    });
  }
  for (const picker of into.querySelectorAll("input[type=color]")) {
    const i = Number(picker.dataset.strand);
    // The swatch shows the strand's own colour, never the muted one it is
    // drawn in while another is picked.  A colour input only understands
    // #rrggbb, and a palette may be shorter.
    picker.value = long(trueColour(i, strands[i].colour));
    picker.nextElementSibling.textContent = strands[i].name;
    picker.closest("li").classList.toggle("picked", picked === i);
  }
}

function long(colour) {
  const text = String(colour || "#000000").trim();
  if (/^#[0-9a-fA-F]{3}$/.test(text)) {
    return "#" + [...text.slice(1)].map((c) => c + c).join("");
  }
  return /^#[0-9a-fA-F]{6}$/.test(text) ? text : "#000000";
}

function tell() {
  for (const listener of listeners) listener();
  // For the drawings that keep themselves: the word as it is typed, and the
  // carriers on the machine.
  document.dispatchEvent(new CustomEvent("strand-colours"));
}

document.addEventListener("input", (event) => {
  const picker = event.target.closest?.("#strand-list input[type=color]");
  if (!picker) return;
  const i = Number(picker.dataset.strand);
  while (chosen.length <= i) chosen.push(null);
  chosen[i] = picker.value.toLowerCase();
  tell();
});

// Pointing at a strand in the list, or stepping onto it with the keyboard,
// shows it among the others until the pointer or the focus leaves.
function strandAt(target) {
  const picker = target?.closest?.("#strand-list input[type=color]");
  return picker ? Number(picker.dataset.strand) : null;
}

document.addEventListener("pointerover", (event) => {
  const i = strandAt(event.target);
  if (i !== null) pick(i);
});
document.addEventListener("pointerout", (event) => {
  if (strandAt(event.target) !== null && strandAt(event.relatedTarget) === null) {
    pick(null);
  }
});
document.addEventListener("focusin", (event) => {
  const i = strandAt(event.target);
  if (i !== null) pick(i);
});
document.addEventListener("focusout", (event) => {
  if (strandAt(event.target) !== null) pick(null);
});
