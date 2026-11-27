// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The page in the visitor's language.  braidpy, in Python and in the page,
// writes English; this puts each text into the language chosen as it is
// shown, from the catalogues in web/locales/ (written by build.py into
// locale.js).  The site's profile says which language it opens in; the
// menu of every page (a select marked data-language) changes it there and
// then, every text put back into the new one from its English, and the
// choice is kept for the next visit, or given in the address as ?lang=fr.
//
// A text is looked up whole, its spaces run together: as it is, or as one
// of the catalogue's patterns, "{}" standing for any words (a braid's
// name), themselves looked up, and "{#}" for a number.  A translation
// takes them in turn, or as "{1}", "{2}"… where its words come in another
// order.  A text the catalogue does not have stays in English, and is
// listed in `untranslated` for whoever completes the catalogue (in the
// browser's console: [...untranslated].join("\n")).  An element marked
// translate="no" keeps its own words, as a braid word.  A catalogue's
// translation of "English" is its language's own name, in the menu.

import { catalogues, language as siteLanguage } from "./locale.js?v=73cce557c0";

const PLACE = /\{#?\}/g;

// A pattern's words: a space for any spaces, as a line break in a note.
const literal = (text) =>
  text
    .split(" ")
    .map((word) => word.replace(/[.*+?^$()|[\]\\{}]/g, "\\$&"))
    .join("\\s+");

/** A catalogue made ready to look texts up in. */
function compiled(texts) {
  const wholes = new Map(Object.entries(texts).filter(([english]) => !english.match(PLACE)));
  const patterns = Object.entries(texts)
    .filter(([english]) => english.match(PLACE))
    .map(([english, translation]) => {
      const places = english.match(PLACE).map((place) => (place === "{#}" ? "(-?\\d+(?:\\.\\d+)?)" : "(.+?)"));
      const words = english.split(PLACE);
      // A space just before a place takes one space only: what follows a
      // line break keeps its own, as the lace card's columns.
      const source = words
        .map((word, i) => (places[i] ? literal(word).replace(/\\s\+$/, "\\s") : literal(word)) + (places[i] ?? ""))
        .join("");
      return {
        match: new RegExp(`^${source}$`, "s"),
        translation,
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
  return { wholes, patterns, shown: new Set(wholes.values()) };
}

const books = new Map(Object.entries(catalogues).map(([code, texts]) => [code, compiled(texts)]));

/** The languages the page can be shown in, each by its own name. */
export const languages = new Map([
  ["en", "English"],
  ...Object.entries(catalogues).map(([code, texts]) => [code, texts.English ?? code]),
]);

// Where the visitor's choice is kept between visits.
const CHOSEN = "braid-studio-language";

function chosenBefore() {
  try {
    return new URLSearchParams(globalThis.location?.search).get("lang") ?? globalThis.localStorage?.getItem(CHOSEN);
  } catch {
    return null;
  }
}

let current = languages.has(chosenBefore()) ? chosenBefore() : siteLanguage;

/** The language the page is shown in. */
export const language = () => current;

export const untranslated = new Set();
globalThis.untranslated = untranslated;

// Something worth translating: a word in it, not a colour as #4daf4a.
const WORDY = /\p{L}{2}/u;
const COLOUR = /#[0-9a-f]{3,8}\b/gi;

/** A text in the page's language, or as it is if the catalogue lacks it. */
export function tr(text) {
  const book = books.get(current);
  if (!book) return text;
  const lead = text.match(/^\s*/)[0];
  const trail = text.slice(lead.length).match(/\s*$/)[0];
  const trimmed = text.slice(lead.length, text.length - trail.length);
  const made = translated(book, trimmed, true) ?? translated(book, trimmed, false);
  if (made === null) {
    untranslated.add(trimmed.replace(/\s+/g, " "));
    return text;
  }
  return lead + made + trail;
}

// A text translated, or null.  Of the patterns it matches, the first whose
// words are all translated; or, not ``whole``, the first, with its words
// translated where they can be — a file's name, a value typed in.
function translated(book, text, whole) {
  const core = text.replace(/\s+/g, " ");
  if (!WORDY.test(core.replace(COLOUR, "")) || book.shown.has(core)) return text;
  const found = book.wholes.get(core);
  if (found !== undefined) return found;
  for (const { match, translation } of book.patterns) {
    const parts = text.match(match);
    if (!parts) continue;
    const words = parts.slice(1).map((part) => (whole ? translated(book, part, true) : tr(part)));
    if (words.includes(null)) continue;
    let next = 0;
    const made = translation.replace(/\{(\d*)\}/g, (_, at) => words[at ? Number(at) - 1 : next++]);
    book.shown.add(made.replace(/\s+/g, " "));
    return made;
  }
  return null;
}

// ------------------------------------------------------------ the page

// The attributes whose words are read or shown; a page's description too.
const ATTRIBUTES = ["title", "placeholder", "aria-label", "alt"];
const DESCRIPTION = 'meta[name="description"]';
// What holds no words of the page's own.
const KEPT = new Set(["SCRIPT", "STYLE", "TEXTAREA", "CODE", "KBD", "SAMP"]);

// Each text's English, and what this showed for it: a text that is not
// what this showed is new, written in English by the page.
const english = new WeakMap();
const showing = new WeakMap();

const kept = (element) => !element || KEPT.has(element.tagName) || element.closest("[translate=no]");

function translateText(node) {
  if (kept(node.parentElement)) return;
  if (showing.get(node) !== node.data) english.set(node, node.data);
  const out = tr(english.get(node));
  if (out !== node.data) node.data = out;
  showing.set(node, node.data);
}

function translateAttributes(element) {
  if (kept(element)) return;
  const names = element.matches(DESCRIPTION) ? [...ATTRIBUTES, "content"] : ATTRIBUTES;
  for (const name of names) {
    const value = element.getAttribute(name);
    if (value === null) continue;
    if (showing.get(element)?.[name] !== value) {
      english.set(element, { ...english.get(element), [name]: value });
    }
    const out = tr(english.get(element)[name]);
    if (out !== value) element.setAttribute(name, out);
    showing.set(element, { ...showing.get(element), [name]: out });
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

/** An element's text as the page wrote it, in English. */
export function englishText(element) {
  const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT);
  let text = "";
  for (let node = walker.nextNode(); node; node = walker.nextNode()) text += english.get(node) ?? node.data;
  return text;
}

/** Shows the page in ``code``'s language, from now on and next time. */
export function setLanguage(code) {
  if (!languages.has(code)) return;
  current = code;
  untranslated.clear();
  try {
    globalThis.localStorage?.setItem(CHOSEN, code);
  } catch {
    // Not kept: chosen again next time.
  }
  if (!globalThis.document) return;
  document.documentElement.lang = code;
  translate(document.documentElement);
  for (const menu of document.querySelectorAll("select[data-language]")) menu.value = code;
  // What is drawn rather than written, drawn again in it.
  document.dispatchEvent(new CustomEvent("language"));
}

if (globalThis.document) {
  document.documentElement.lang = current;
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
  // The menu, on a page offering more than one language.
  for (const menu of document.querySelectorAll("select[data-language]")) {
    menu.replaceChildren(...[...languages].map(([code, name]) => new Option(name, code)));
    menu.value = current;
    menu.hidden = languages.size < 2;
    menu.addEventListener("change", () => setLanguage(menu.value));
  }
  document.documentElement.classList.remove("untranslated");
}
