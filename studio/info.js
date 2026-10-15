// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The card beside the braid: what is known of it, its words to copy or
// make again, and notes.

import { $, round } from "./page.js?v=613ec263e5";
import { lastResult } from "./scene.js?v=613ec263e5";
import { writeSpec } from "./spec.js?v=613ec263e5";
import { submit } from "./workers.js?v=613ec263e5";

export function describe(result, seconds) {
  $("about").hidden = false;
  $("title").textContent = result.title;
  const info = result.info;
  const rows = [
    ["Strands", info.n_strands],
    [
      // Every strand back where it started: after so many of its words, or
      // of its moves' cycles; so many made, and whether that is pure.
      "Pure after",
      info.repeated &&
        (info.pure_after === null
          ? `over 64 ${info.repeated}s`
          : times(info.pure_after, info.repeated)),
    ],
    ["Made", info.made && info.repeated && times(info.made, info.repeated)],
    ["Pure", info.pure === undefined ? undefined : info.pure ? "yes" : "no"],
    ["Should look", info.expected_shape && `${info.expected_shape} in cross-section`],
    ["Crossings", info.crossings],
    ["Exponent sum", info.exponent_sum],
    ["Permutation", info.permutation && info.permutation.join(" ")],
    [
      "Closed up",
      info.components === undefined
        ? undefined
        : info.components === 1
          ? "a knot"
          : `a link of ${info.components} pieces`,
    ],
    [
      "Normal form",
      info.garside &&
        `Δ^${info.garside.half_twists} and ${info.garside.factors} permutation braids`,
    ],
    ["Full twists", info.garside && info.garside.full_twists],
    ["Word", info.word, { layout: "row" }],
    ["Ring word", info.annular_word, { layout: "ring" }],
    [
      "Closest yarns",
      info.closest_approach === undefined
        ? undefined
        : `${info.closest_approach} for a yarn of ${round(result.yarn_diameter)}`,
    ],
    ["Computed in", seconds ? `${seconds.toFixed(1)} s` : undefined],
    ["", seconds === null ? "As laid — tightening…" : undefined],
  ];
  const list = $("info");
  list.replaceChildren();
  for (const [name, value, code] of rows) {
    if (value === undefined || value === null || value === "") continue;
    const term = document.createElement("dt");
    term.textContent = name;
    const detail = document.createElement("dd");
    if (code) {
      const text = String(value);
      const element = document.createElement("code");
      element.textContent = text;
      element.title = text;
      detail.append(element);
      if (code.layout) detail.append(wordActions(text, code.layout, info.n_strands));
    } else {
      detail.textContent = value;
    }
    list.append(term, detail);
  }
  const notes = $("notes");
  notes.replaceChildren(
    ...result.notes.map((note) => {
      const item = document.createElement("li");
      item.textContent = note;
      return item;
    }),
  );
}

// A braid's own word, to make again as a braid word — the same braid — or
// to copy.
function wordActions(word, layout, strands) {
  const actions = document.createElement("span");
  actions.className = "actions";
  const make = document.createElement("button");
  make.type = "button";
  make.textContent = "Make from it";
  make.title = `Make this ${layout === "ring" ? "ring word" : "braid word"} as a braid word, once`;
  make.addEventListener("click", () => {
    // The same yarn, for the same look.
    const yarn = lastResult?.yarn_diameter;
    writeSpec({ source: "word", layout, word, n_strands: strands, repeat: 1 });
    if (yarn) $("yarn_diameter").value = round(yarn);
    submit();
  });
  const copy = document.createElement("button");
  copy.type = "button";
  copy.textContent = "Copy";
  copy.addEventListener("click", () => copyText(word, copy));
  actions.append(make, copy);
  return actions;
}

// Text to the clipboard, said so on the button that asked; where the
// browser will not, the text shown to copy by hand.
export async function copyText(text, button) {
  let copied = false;
  try {
    await navigator.clipboard.writeText(text);
    copied = true;
  } catch {
    const area = document.createElement("textarea");
    area.value = text;
    area.setAttribute("readonly", "");
    area.style.position = "fixed";
    area.style.opacity = "0";
    document.body.append(area);
    area.select();
    try {
      copied = document.execCommand("copy");
    } catch {
      copied = false;
    }
    area.remove();
  }
  if (!copied) {
    window.prompt("Copy it from here:", text);
    return;
  }
  const was = button.textContent;
  button.textContent = "Copied ✓";
  setTimeout(() => (button.textContent = was), 1500);
}

function times(count, what) {
  return `${count} ${what}${count > 1 ? "s" : ""}`;
}
