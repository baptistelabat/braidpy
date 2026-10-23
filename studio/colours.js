// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The colour of each strand, chosen by hand.
//
// Whatever makes the braid picks the colours to start with — a word by the
// palette, a machine by its carriers, a sinnet by its own scheme — and this
// lets them be changed afterwards, strand by strand or a group at a time.
// A group is the strands of one colour: changing its colour changes them
// all, and a strand joins a group by taking its colour.  So groups need no
// keeping of their own, and a link says them as it says the colours. The choice is put on
// the braid in one place, so everything drawn from it comes out the same
// colour: the braid in 3D, its cross-section, the view from above, the
// carriers, and the braid grown frame by frame.
//
// A colour change does not remake the braid. The strands are the ones that
// were made; only what they are painted with changes, so it is immediate
// however long the braid took.

import { $ } from "./page.js?v=46dd9b8090";

// The colours braidpy gives a braid's strands (braidpy.utils.PALETTE).
export const PALETTE = [
  "#e41a1c", "#377eb8", "#4daf4a", "#984ea3", "#ff7f00", "#a65628",
  "#f781bf", "#999999", "#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3",
];

// Colour chosen per strand, by its place in the braid; null where none was.
let chosen = [];
// The colours the braid was made with.  Kept because what is drawn is worked
// out afresh each time rather than painted over what was painted before: a
// strand shown among the others has to be able to come back.
let made = [];
// The strands being pointed at in the list — one, or a group.  They keep
// their colour while the others are muted, which is the only way to be sure
// which are about to change when several are the same colour.
let picked = null;
// Which strands the shared colour box is changing, and the colour it is
// showing before it is confirmed: the braid follows the box as it moves, so
// a colour can be judged on the braid rather than in the box, and only
// confirming it writes it down.
let editing = null;
let preview = null;
const listeners = [];

/**
 * Run `callback` whenever a colour changes, to draw the braid again.
 *
 * It is told whether the colour was confirmed: a colour still being chosen
 * is drawn, but not yet written into the braid asked for.
 */
export function onChosen(callback) {
  listeners.push(callback);
}

/** Remember the colours a braid was made with, before any are put on it. */
export function rebase(result) {
  if (result && result.strands) made = result.strands.map((strand) => strand.colour);
}

/** The colour a strand is really in, whatever is drawn while one is picked. */
export function trueColour(i, fallback) {
  if (editing?.includes(i) && preview) return preview;
  return chosen[i] || made[i] || fallback;
}

/** Show some strands among the others — one, or a list; null shows them
 * all alike. */
export function pick(which) {
  const next = which === null ? null : [which].flat();
  if (String(picked) === String(next)) return;
  picked = next;
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
  return picked === null || picked.includes(i) ? own : muted(own);
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

  // Clicking a strand opens the palette below it rather than the browser's
  // own colour box: see openPalette.
  if (into.querySelectorAll("button[data-strand]").length !== strands.length) {
    into.replaceChildren();
    strands.forEach((strand, i) => {
      const row = document.createElement("li");
      const swatch = document.createElement("button");
      swatch.type = "button";
      swatch.className = "swatch";
      swatch.dataset.strand = String(i);
      const name = document.createElement("span");
      swatch.append(name);
      row.append(swatch);
      into.append(row);
    });
  }
  for (const swatch of into.querySelectorAll("button[data-strand]")) {
    const i = Number(swatch.dataset.strand);
    // The swatch shows the strand's own colour, never the muted one it is
    // drawn in while another is shown among the others.
    const own = long(trueColour(i, strands[i].colour));
    swatch.style.setProperty("--swatch", own);
    swatch.firstElementChild.textContent = strands[i].name;
    swatch.title = `${strands[i].name}: ${own}`;
    swatch.setAttribute("aria-label", `The colour of ${strands[i].name}`);
    swatch.closest("li").classList.toggle("picked", picked?.length === 1 && picked[0] === i);
    swatch.closest("li").classList.toggle("changing", Boolean(openFor()?.includes(i)));
  }
  listGroups(strands);
}

// The braid's strands by colour, in the order the colours first come.
function groupsOf(strands) {
  const groups = new Map();
  strands.forEach((strand, i) => {
    const colour = long(trueColour(i, strand.colour));
    if (!groups.has(colour)) groups.set(colour, []);
    groups.get(colour).push(i);
  });
  return groups;
}

// The groups, above the strands: shown when some strands share a colour.
// Rebuilt only when who is in which group changes, so a group pointed at,
// or stepped onto with the keyboard, stays where it is while it is shown.
function listGroups(strands) {
  const into = $("strand-groups");
  if (!into) return;
  const groups = [...groupsOf(strands)];
  const shared = groups.some(([, members]) => members.length > 1);
  into.hidden = !shared;
  const caption = into.previousElementSibling;
  if (caption?.classList.contains("groups-caption")) caption.hidden = !shared;
  const who = groups.map(([, members]) => members.join(",")).join(";");
  if (into.dataset.who !== who) {
    into.dataset.who = who;
    into.replaceChildren(
      ...groups.map(([, members]) => {
        const row = document.createElement("li");
        const swatch = document.createElement("button");
        swatch.type = "button";
        swatch.className = "swatch";
        swatch.dataset.strands = members.join(",");
        swatch.append(document.createElement("span"));
        row.append(swatch);
        return row;
      }),
    );
  }
  for (const swatch of into.querySelectorAll("button[data-strands]")) {
    const members = swatch.dataset.strands.split(",").map(Number);
    const colour = long(trueColour(members[0], strands[members[0]].colour));
    const names = members.map((i) => strands[i].name).join(", ");
    const count = members.length === 1 ? "1 strand" : `${members.length} strands`;
    swatch.style.setProperty("--swatch", colour);
    swatch.firstElementChild.textContent = count;
    swatch.title = `${count} in ${colour}: ${names}`;
    swatch.setAttribute("aria-label", `The colour of ${count}: ${names}`);
    swatch.closest("li").classList.toggle("picked", same(picked, members) && members.length > 1);
    swatch.closest("li").classList.toggle("changing", same(openFor(), members));
  }
}

function same(a, b) {
  return a !== null && b !== null && String(a) === String(b);
}

// A few neutrals past the braid's own colours, for marking a strand out.
const NEUTRALS = ["#000000", "#555555", "#aaaaaa", "#ffffff"];

// The palette, opened under the strand it is for.
//
// Not the browser's own colour box, for a plain reason: the box is the
// system's, and on some of them — the GTK one Firefox opens on Linux —
// nothing reaches the page until Select is pressed, so a colour cannot be
// tried on the braid, only committed to.  Colours offered here are the
// page's own, so clicking one puts it on the braid at once.  The system box
// is still a click away for anything not offered.
function openPalette(strands, anchor) {
  const holder = $("strand-palette");
  if (!holder) return;
  if (same(openFor(), strands)) {
    closePalette();
    return;
  }
  holder.dataset.strands = strands.join(",");
  holder.replaceChildren();
  // The colours the braid is in come first, so a strand can join a group in
  // one click, whatever colour that group was given.
  const swatches = [...document.querySelectorAll("#strand-list button[data-strand]")];
  const inUse = swatches.map((swatch) => swatch.style.getPropertyValue("--swatch").trim());
  for (const colour of new Set([...inUse, ...PALETTE, ...NEUTRALS].map(long))) {
    const dab = document.createElement("button");
    dab.type = "button";
    dab.className = "dab";
    dab.dataset.colour = colour;
    dab.style.setProperty("--swatch", colour);
    dab.title = colour;
    dab.setAttribute("aria-label", colour);
    holder.append(dab);
  }
  const more = document.createElement("button");
  more.type = "button";
  more.className = "more";
  more.id = "strand-more";
  more.textContent = "Another colour…";
  holder.append(more);

  // Which strands it is for, since it opens below the whole list: inside it,
  // the list would count it among the strands and rebuild it away.
  const whose = document.createElement("span");
  whose.className = "whose";
  const names = strands.map(
    (i) => swatches[i]?.firstElementChild.textContent ?? `Strand ${i}`,
  );
  whose.textContent =
    names.length === 1
      ? `${names[0]} — Ctrl- or Shift-click other strands to colour them too`
      : `${names.length} strands: ${names.join(", ")}`;
  holder.prepend(whose);

  holder.hidden = false;
  holder.querySelector(".dab")?.focus();
}

function closePalette() {
  const holder = $("strand-palette");
  if (!holder || holder.hidden) return;
  holder.hidden = true;
  delete holder.dataset.strands;
  tell(false);
}

/** The strands the palette is open for, or null. */
function openFor() {
  const holder = $("strand-palette");
  if (!holder || holder.hidden || holder.dataset.strands === undefined) return null;
  return holder.dataset.strands.split(",").map(Number);
}

/** Give strands a colour, and say so. */
function colour(strands, value) {
  for (const i of strands) {
    while (chosen.length <= i) chosen.push(null);
    chosen[i] = value.toLowerCase();
  }
}

function openBox(strands) {
  const box = $("strand-colour");
  if (!box) return;
  editing = strands;
  preview = null;
  box.value = long(trueColour(strands[0], "#000000"));
  // showPicker is what opens it without the box having to be seen; where it
  // is not understood, clicking the box does the same.
  if (typeof box.showPicker === "function") box.showPicker();
  else box.click();
}

function long(colour) {
  const text = String(colour || "#000000").trim();
  if (/^#[0-9a-fA-F]{3}$/.test(text)) {
    return "#" + [...text.slice(1)].map((c) => c + c).join("");
  }
  return /^#[0-9a-fA-F]{6}$/.test(text) ? text : "#000000";
}

function tell(saved = true) {
  for (const listener of listeners) listener(saved);
  // For the drawings that keep themselves: the word as it is typed, and the
  // carriers on the machine.
  document.dispatchEvent(new CustomEvent("strand-colours"));
}

document.addEventListener("click", (event) => {
  const swatch = event.target.closest?.("#strand-list button[data-strand]");
  if (swatch) {
    const i = Number(swatch.dataset.strand);
    // With Ctrl, Cmd or Shift, a strand is added to those the palette is
    // open for, or taken out: several strands, one colour, a group.
    const open = openFor();
    if (open && (event.ctrlKey || event.metaKey || event.shiftKey)) {
      const now = open.includes(i) ? open.filter((k) => k !== i) : [...open, i].sort((a, b) => a - b);
      if (now.length) openPalette(now, swatch);
      else closePalette();
      tell(false);
      return;
    }
    openPalette([i], swatch);
    return;
  }
  const group = event.target.closest?.("#strand-groups button[data-strands]");
  if (group) {
    openPalette(group.dataset.strands.split(",").map(Number), group);
    return;
  }
  const dab = event.target.closest?.("#strand-palette .dab");
  if (dab) {
    colour(openFor(), dab.dataset.colour);
    preview = null;
    editing = null;
    closePalette();
    tell(true);
    return;
  }
  if (event.target.closest?.("#strand-more")) {
    openBox(openFor());
    return;
  }
  // Anywhere else puts the palette away.
  if (!event.target.closest?.("#strand-palette")) closePalette();
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape") closePalette();
});

// Moving about in the colour box shows the braid in that colour at once,
// without writing it down.
document.addEventListener("input", (event) => {
  if (event.target.id !== "strand-colour" || editing === null) return;
  preview = event.target.value.toLowerCase();
  tell(false);
});

// Confirming it writes it down, and the link follows.
document.addEventListener("change", (event) => {
  if (event.target.id !== "strand-colour" || editing === null) return;
  colour(editing, event.target.value);
  preview = null;
  tell(true);
});

// Pointing at a strand in the list, or a group, or stepping onto it with
// the keyboard, shows it among the others until the pointer or the focus
// leaves.
function strandAt(target) {
  const swatch = target?.closest?.("#strand-list button[data-strand]");
  if (swatch) return [Number(swatch.dataset.strand)];
  const group = target?.closest?.("#strand-groups button[data-strands]");
  return group ? group.dataset.strands.split(",").map(Number) : null;
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
