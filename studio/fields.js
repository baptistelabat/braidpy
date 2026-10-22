// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The form: what each source asks for, filled in from braidpy's catalogue,
// and the examples a source offers.

import { attachDiagram } from "./diagram.js?v=2d6d1b8e75";
import { attachEditor } from "./editor.js?v=2d6d1b8e75";
import { attachMachine } from "./machine.js?v=2d6d1b8e75";
import { $ } from "./page.js?v=2d6d1b8e75";
import { submit } from "./workers.js?v=2d6d1b8e75";

// What each source asks for.  ``entries`` and ``examples`` come from
// braidpy's own catalogue once it has loaded.
const FIELDS = {
  word: [
    {
      name: "layout",
      label: "Strands",
      kind: "choice",
      choices: [
        ["row", "In a row: a braid word"],
        ["ring", "Round a ring: a ring word"],
      ],
    },
    {
      name: "word",
      label: "Braid word",
      kind: "textarea",
      hint: "Signed generators — 1 -2 — or s1 s2^-1, or letters, aB.",
    },
    { name: "n_strands", label: "How many", kind: "number", min: 2, max: 32 },
    { name: "repeat", label: "Repeat", kind: "number", min: 1, max: 50 },
  ],
  kumihimo: [
    {
      name: "pattern",
      label: "Moves",
      kind: "text",
      hint: "S swaps the top and bottom strands, R turns the disk a quarter.",
    },
    { name: "n_strands", label: "Strands", kind: "number", min: 4, max: 32, step: 4 },
    { name: "repeat", label: "Repeat", kind: "number", min: 1, max: 50 },
  ],
  mobidai: [
    { name: "name", label: "Braid", kind: "entries" },
    {
      name: "slots",
      label: "Strands start in slots",
      kind: "text",
      custom: true,
      hint: "One slot per strand; slots are numbered clockwise from the top.",
    },
    {
      name: "moves",
      label: "Moves, in order",
      kind: "textarea",
      custom: true,
      hint: "From slot > to slot, for example 1>15, 17>31. A strand goes the short way round, over the strands it passes. Change them, here or on the disk, to make your own braid: the one chosen stays as it is.",
    },
    { name: "n_slots", label: "Slots", kind: "number", min: 3, max: 128, custom: true },
    {
      name: "shift",
      label: "Turn after a cycle",
      kind: "number",
      min: -128,
      max: 128,
      custom: true,
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 40 },
  ],
  sinnet: [
    { name: "name", label: "Sinnet", kind: "entries" },
    {
      name: "counts",
      label: "Strands in each space",
      kind: "text",
      custom: true,
      hint: "Spaces are numbered anticlockwise from the top, as the top view shows them: the first and the last meet there.",
    },
    {
      name: "moves",
      label: "Moves, in order",
      kind: "textarea",
      custom: true,
      hint: "From space > to space. Odd spaces send their right-hand strand anticlockwise, even spaces their left-hand one clockwise, over all.",
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 12 },
  ],
  machine: [
    { name: "name", label: "Machine", kind: "entries" },
    {
      name: "carriers",
      label: "Carriers",
      kind: "text",
      hint: "Each as gear:slot, slots numbered from each gear's first. Click a slot on the machine to put a carrier on it or take it off: carriers that meet stop the braiding there.",
    },
    {
      name: "cores",
      label: "Cores",
      kind: "choice",
      choices: [
        ["yarn", "Yarn: gives way to the yarns braided round it"],
        ["rigid", "Rigid: stays straight"],
      ],
      hint: "For a machine that braids round cores.",
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 8 },
  ],
};

export let catalogue = null;

// Set once braidpy has loaded and said what it can make.
export function setCatalogue(value) {
  catalogue = value;
}
// Sources left out of the "Made by" menu for now.
export const UNLISTED = new Set(["kumihimo"]);
// Sources whose catalogued braids always show what they are made of.
const ALWAYS_SHOWN = new Set(["mobidai", "sinnet"]);

export function renderFields(source, values = {}) {
  const about = catalogue[source];
  const defaults = { ...about.defaults, ...values };
  const holder = $("fields");
  holder.replaceChildren();
  const numbers = [];
  for (const field of FIELDS[source]) {
    const label = document.createElement("label");
    label.className = "field";
    const title = document.createElement("span");
    title.textContent = field.label;
    label.append(title);
    let input;
    if (field.kind === "entries") {
      input = document.createElement("select");
      for (const entry of about.entries) {
        const option = new Option(entry.title, entry.name);
        input.append(option);
      }
    } else if (field.kind === "choice") {
      input = document.createElement("select");
      for (const [value, text] of field.choices) input.append(new Option(text, value));
    } else if (field.kind === "textarea") {
      input = document.createElement("textarea");
      input.rows = 2;
      input.spellcheck = false;
    } else {
      input = document.createElement("input");
      input.type = field.kind;
      if (field.kind === "text") input.spellcheck = false;
      for (const key of ["min", "max", "step"]) {
        if (field[key] !== undefined) input[key] = field[key];
      }
    }
    input.name = field.name;
    input.id = `field-${field.name}`;
    if (defaults[field.name] !== undefined) input.value = defaults[field.name];
    label.append(input);
    if (field.hint) {
      const hint = document.createElement("small");
      hint.textContent = field.hint;
      label.append(hint);
    }
    if (field.custom) label.dataset.custom = "";
    if (field.kind === "number") numbers.push(label);
    else holder.append(label);
  }
  if (numbers.length) {
    const row = document.createElement("div");
    row.className = "row";
    row.append(...numbers);
    holder.append(row);
  }
  // "Your own moves…" shows what a catalogued braid is made of, ready to
  // change: it starts from the braid chosen before.  A kumihimo disk's
  // braid, or an Ashley sinnet, shows its moves always, ready to change: changing them makes it
  // your own, and the catalogued braid stays as it was, to choose again.
  const entries = holder.querySelector("select[name=name]");
  if (entries) {
    const always = ALWAYS_SHOWN.has(source);
    let previous = entries.value;
    let filling = false;
    const fill = (name) => {
      const entry = about.entries.find((e) => e.name === name);
      filling = true;
      for (const [key, value] of Object.entries(entry?.pattern || {})) {
        const input = holder.querySelector(`[name=${key}]`);
        if (input) input.value = value;
      }
      filling = false;
    };
    const showCustom = (shown) => {
      for (const label of holder.querySelectorAll("[data-custom]")) label.hidden = !shown;
    };
    entries.addEventListener("change", () => {
      const custom = entries.value === "custom";
      showCustom(custom || always);
      if (custom) {
        // From the braid chosen before, unless it is already showing.
        if (!always) {
          const from = about.entries.find((entry) => entry.name === previous);
          for (const [key, value] of Object.entries(from?.pattern || {})) {
            const input = holder.querySelector(`[name=${key}]`);
            if (input && (input.value === "" || from)) input.value = value;
          }
        }
      } else {
        previous = entries.value;
        if (always) fill(entries.value);
      }
    });
    showCustom(entries.value === "custom" || always);
    if (always && entries.value !== "custom") fill(entries.value);
    if (always) {
      for (const label of holder.querySelectorAll("[data-custom]")) {
        label.addEventListener("input", () => {
          if (!filling && entries.value !== "custom") entries.value = "custom";
        });
      }
    }
  }
  if (source === "mobidai" || source === "sinnet") attachEditor(source, holder);
  if (source === "word") attachDiagram(holder);
  if (source === "machine") attachMachine(holder);
  if (about.examples) attachExamples(source, about.examples, holder);
}

// A source's examples, chosen from a list at the top of its fields, as a
// catalogue's braids are: choosing one makes it.  Changing what it is made
// of makes it your own.
function attachExamples(source, examples, holder) {
  const label = document.createElement("label");
  label.className = "field";
  const title = document.createElement("span");
  title.textContent = "Braid";
  const list = document.createElement("select");
  list.id = "field-example";
  examples.forEach((example, k) => list.append(new Option(example.title, String(k))));
  list.append(new Option("Your own…", "custom"));
  label.append(title, list);
  holder.prepend(label);
  const shown = () => {
    const value = (name) => holder.querySelector(`[name=${name}]`)?.value ?? "";
    const same = (example) =>
      Object.entries(example).every(
        ([key, wanted]) =>
          key === "title" ||
          String(wanted).replace(/\s+/g, " ").trim() === value(key).replace(/\s+/g, " ").trim(),
      ) && (example.layout ?? "row") === (value("layout") || "row");
    const k = examples.findIndex(same);
    list.value = k < 0 ? "custom" : String(k);
  };
  list.addEventListener("change", () => {
    if (list.value === "custom") return;
    renderFields(source, examples[Number(list.value)]);
    submit();
  });
  for (const input of holder.querySelectorAll("input, select:not(#field-example), textarea")) {
    input.addEventListener("input", shown);
    input.addEventListener("change", shown);
  }
  shown();
}
