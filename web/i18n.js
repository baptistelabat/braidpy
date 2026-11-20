// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The page in the site's language.  braidpy, in Python and in the page,
// writes English; this puts each text into the site's language as it is
// shown, from the catalogue the profile names (web/locales/<language>.toml,
// written by build.py as locale.js).  English has an empty catalogue, and
// shows every text as it is written.
//
// A text is looked up whole, its spaces run together: as it is, or as one
// of the catalogue's patterns, "{}" standing for any words (a braid's
// name), themselves looked up, and "{#}" for a number.  A translation
// takes them in turn, or as "{1}", "{2}"… where its words come in another
// order.  A text the catalogue does not have stays in English, and is
// listed in `untranslated` for whoever completes the catalogue (in the
// browser's console: [...untranslated].join("\n")).  An element marked
// translate="no" keeps its own words, as a braid word.

import { language, texts } from "./locale.js";

const PLACE = /\{#?\}/g;
const wholes = new Map(Object.entries(texts).filter(([english]) => !english.match(PLACE)));

// A pattern's words: a space for any spaces, as a line break in a note.
const literal = (text) =>
  text
    .split(" ")
    .map((word) => word.replace(/[.*+?^$()|[\]\\{}]/g, "\\$&"))
    .join("\\s+");
const patterns = Object.entries(texts)
  .filter(([english]) => english.match(PLACE))
  .map(([english, translated]) => {
    const places = english.match(PLACE).map((place) => (place === "{#}" ? "(-?\\d+(?:\\.\\d+)?)" : "(.+?)"));
    const words = english.split(PLACE);
    // A space just before a place takes one space only: what follows a
    // line break keeps its own, as the lace card's columns.
    const source = words
      .map((word, i) => (places[i] ? literal(word).replace(/\\s\+$/, "\\s") : literal(word)) + (places[i] ?? ""))
      .join("");
    return {
      match: new RegExp(`^${source}$`, "s"),
      translation: translated,
      // Tried first, a pattern ending in words of its own, which hold its
      // end: "{}, {#} cycles" takes "ABOK #3042, 8-strand round, 3 cycles"
      // before "ABOK #{#}, {#}-strand {}" would take "round, 3 cycles" for
      // a shape.  Then the more words of its own, the sooner.
      open: english.endsWith("{}"),
      length: words.join("").length,
    };
  })
  .sort((a, b) => a.open - b.open || b.length - a.length);
// Every text shown translated, so as not to take it for one untranslated.
const shown = new Set(wholes.values());

export const untranslated = new Set();
globalThis.untranslated = untranslated;

// Something worth translating: a word in it, not a colour as #4daf4a.
const WORDY = /\p{L}{2}/u;
const COLOUR = /#[0-9a-f]{3,8}\b/gi;

/** A text in the site's language, or as it is if the catalogue lacks it. */
export function tr(text) {
  if (language === "en") return text;
  const lead = text.match(/^\s*/)[0];
  const trail = text.slice(lead.length).match(/\s*$/)[0];
  const trimmed = text.slice(lead.length, text.length - trail.length);
  const made = translated(trimmed, true) ?? translated(trimmed, false);
  if (made === null) {
    untranslated.add(trimmed.replace(/\s+/g, " "));
    return text;
  }
  return lead + made + trail;
}

// A text translated, or null.  Of the patterns it matches, the first whose
// words are all translated; or, not ``whole``, the first, with its words
// translated where they can be — a file's name, a value typed in.
function translated(text, whole) {
  const core = text.replace(/\s+/g, " ");
  if (!WORDY.test(core.replace(COLOUR, "")) || shown.has(core)) return text;
  const found = wholes.get(core);
  if (found !== undefined) return found;
  for (const { match, translation } of patterns) {
    const parts = text.match(match);
    if (!parts) continue;
    const words = parts.slice(1).map((part) => (whole ? translated(part, true) : tr(part)));
    if (words.includes(null)) continue;
    let next = 0;
    const made = translation.replace(/\{(\d*)\}/g, (_, at) => words[at ? Number(at) - 1 : next++]);
    shown.add(made.replace(/\s+/g, " "));
    return made;
  }
  return null;
}

// The attributes whose words are read or shown.
const ATTRIBUTES = ["title", "placeholder", "aria-label", "alt"];
// What holds no words of the page's own.
const KEPT = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "KBD", "SAMP"]);
// What this set itself, so as not to look it up again.
const done = new WeakMap();

const kept = (element) => !element || KEPT.has(element.tagName) || element.closest("[translate=no]");

function translateText(node) {
  if (done.get(node) === node.data || kept(node.parentElement)) return;
  const out = tr(node.data);
  if (out !== node.data) node.data = out;
  done.set(node, node.data);
}

function translateAttributes(element) {
  if (kept(element)) return;
  for (const name of ATTRIBUTES) {
    const value = element.getAttribute(name);
    if (value === null) continue;
    const out = tr(value);
    if (out !== value) element.setAttribute(name, out);
  }
  if (element.matches('meta[name="description"]')) {
    const out = tr(element.content);
    if (out !== element.content) element.content = out;
  }
}

function translate(root) {
  if (root.nodeType === Node.TEXT_NODE) return translateText(root);
  if (root.nodeType !== Node.ELEMENT_NODE) return;
  translateAttributes(root);
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
  for (let node = walker.nextNode(); node; node = walker.nextNode()) {
    if (node.nodeType === Node.TEXT_NODE) translateText(node);
    else translateAttributes(node);
  }
}

if (language !== "en" && globalThis.document) {
  translate(document.documentElement);
  new MutationObserver((changes) => {
    for (const change of changes) {
      if (change.type === "characterData") translateText(change.target);
      else if (change.type === "attributes") translateAttributes(change.target);
      else change.addedNodes.forEach(translate);
    }
  }).observe(document.documentElement, {
    subtree: true,
    childList: true,
    characterData: true,
    attributes: true,
    attributeFilter: [...ATTRIBUTES, "content"],
  });
}
globalThis.document?.documentElement.classList.remove("untranslated");
