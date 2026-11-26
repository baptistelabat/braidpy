// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The form: what each source asks for, filled in from braidpy's catalogue,
// and the examples a source offers.

import { attachDiagram } from "./diagram.js?v=7395d32e29";
import { attachEditor, attachShape } from "./editor.js?v=7395d32e29";
import { attachMachine } from "./machine.js?v=7395d32e29";
import { $ } from "./page.js?v=7395d32e29";
import { submit, worker } from "./workers.js?v=7395d32e29";

// The core a braid is made round (braidpy.web._settings.CORE).
const CORE = {
  name: "core",
  label: "Core",
  kind: "choice",
  choices: [
    ["own", "As built: its own cores, of yarn, if it has any"],
    ["none", "None"],
    ["yarn", "Yarn: gives way to the yarns braided round it"],
    ["rigid", "Rigid: stays straight"],
  ],
  hint: "A core goes down the hole a ring of gears encloses, unless the machine has cores of its own.",
};

// A disk's core, down its middle (braidpy.web._settings.DISK_CORE).
const DISK_CORE = {
  name: "core",
  label: "Core",
  kind: "choice",
  choices: [
    ["none", "None"],
    ["yarn", "Yarn: gives way to the yarns braided round it"],
    ["rigid", "Rigid: stays straight"],
  ],
  hint: "A core down the disk's middle, the braid made round it: on a marudai, it rises up the braid's axis and each move passes beside it.",
};

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
        ["band", "Round a circle, any two crossing: a band word"],
      ],
    },
    {
      name: "word",
      label: "Braid word",
      kind: "textarea",
      hint: "Signed generators — 1 -2 — or s1 s2^-1, or letters, aB; in band letters, 4:1 crosses strands 4 and 1 in front of those between, 1:4 the other way.",
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
    DISK_CORE,
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
    DISK_CORE,
    {
      kind: "file",
      label: "Import a braid3d design",
      accept: ".b3d",
      hint: "A .b3d file saved by braid3d, read as your own disk braid: its yarns, in their colours, and its moves, on a disk of as few slots as hold them.",
    },
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
  shape: [
    // The Braid list offers only braids of the grid and shape chosen.
    { name: "grid", label: "Grid", kind: "choice", from: "grids", narrows: true },
    {
      name: "shape",
      label: "Shape",
      kind: "choice",
      from: "shapes",
      by: "grid",
      narrows: true,
    },
    {
      name: "cells",
      label: "Cells",
      kind: "textarea",
      hint: "The shape's own cells, changed by clicking on the drawing: i,j a square, or a rhomb on the skewed grid; on the diamond grid, i,jb, i,jr, i,jt, i,jl the quarter of that square below, right of, above or left of its middle; i,j^ the triangle pointing up from point i,j, i,jv the one down beside it. Empty, the shape chosen. A hole is a hole once a point of the grid is left out, Ashley's lines running through the points.",
    },
    { name: "order", label: "Order of the moves", kind: "choice", from: "orders" },
    {
      name: "turned",
      label: "Tracks turned round",
      kind: "text",
      hint: "Each track's moves made the other way round, by number.",
    },
    {
      name: "extra",
      label: "A strand more in spaces",
      kind: "text",
      hint: "Each space named holds a strand more from the start, twice named two.",
    },
    {
      name: "size",
      label: "Size",
      kind: "number",
      min: 2,
      max: 12,
      hint: "Lines along each side; an oblong's, an L's, a U's or a hollow square's width.",
    },
    {
      name: "height",
      label: "Height",
      kind: "number",
      min: 2,
      max: 12,
      hint: "An oblong's height, or how thick an L's or a U's arms or a hollow square's sides are, in lines.",
    },
    {
      name: "corners",
      label: "At each corner",
      kind: "number",
      min: 0,
      max: 3,
      hint: "Strands more in each space at a corner, or alone on a side, as the book sharpens a triangle's edges (#3049) or a flat oblong's (#3072).",
    },
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 12 },
  ],
  machine: [
    { name: "name", label: "Machine", kind: "entries" },
    {
      name: "graph",
      label: "Gears that mesh",
      kind: "textarea",
      custom: true,
      hint: "Each pair of gears that mesh, as A-B: A-B B-C C-D D-A is four gears in a ring. A gear with its own number of slots is written A:6 wherever it is named. A split gear is written as its parts, each meshing with its own neighbours, joined on their axle: A-B1 B2-C B1+B2 is two plaits side by side, B split in two; a gear may be split in more parts, as H1+H2+H3. Neighbours turn opposite ways, so a ring of an odd number of gears cannot turn. Starts from the machine chosen before.",
    },
    { name: "n_slots", label: "Slots per gear", kind: "number", min: 2, max: 24, custom: true },
    {
      name: "carriers",
      label: "Carriers",
      kind: "text",
      hint: "Each as gear:slot, slots numbered from each gear's first. Click a slot on the machine to put a carrier on it or take it off: carriers that meet stop the braiding there.",
    },
    {
      name: "axials",
      label: "Axial yarns",
      kind: "text",
      hint: "Where straight yarns are fed up through the braid, the carriers braiding round them: a gear, as B, up its hollow spindle; the ring of gears round a hole, as A-B-C-D, down it. Every place there is room for one is marked on the machine: click one to load a spool there or take it off.",
    },
    CORE,
    { name: "cycles", label: "Cycles", kind: "number", min: 1, max: 8 },
  ],
  lace: [
    { name: "name", label: "Lace machine", kind: "entries" },
    { name: "n_gears", label: "Gears", kind: "number", min: 4, max: 72, step: 2, custom: true },
    {
      name: "card",
      label: "Punchcard",
      kind: "textarea",
      custom: true,
      hint: "The gears each step turns, a step after another with / between, for example A C / B / -: A, C, E… turn anticlockwise, first, then B, D, F… clockwise; - is a step turning none, and after Z come AA, AB… Or a step a line in 0 and 1, a digit a gear from A: the gears turning anticlockwise, then those turning clockwise, for example 1010 0100. Change it to make your own: the one chosen stays as it is.",
    },
    {
      name: "carriers",
      label: "Bobbins",
      kind: "text",
      hint: "Each as gear:slot, or by its notch, A-B, as the card names them. A bobbin sits in a notch, where two gears overlap: click one on the machine to put a bobbin in it or take it off. The card turns the gears; bobbins that meet stop the braiding there.",
    },
    CORE,
    { name: "cycles", label: "Passes of the card", kind: "number", min: 1, max: 24 },
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
const ALWAYS_SHOWN = new Set(["mobidai", "sinnet", "lace"]);

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
      // A choice offered by another's value, as a grid's shapes by the grid.
      const offered = field.by ? about[field.from][defaults[field.by]] || {} : about[field.from];
      const choices = field.from ? Object.entries(offered) : field.choices;
      for (const [value, text] of choices) input.append(new Option(text, value));
    } else if (field.kind === "textarea") {
      input = document.createElement("textarea");
      input.rows = 2;
      input.spellcheck = false;
    } else if (field.kind === "file") {
      // Read by braidpy (braidpy.web.from_b3d), which fills the fields with
      // what it holds and makes it.  Unnamed, it is no part of a link.
      input = document.createElement("input");
      input.type = "file";
      input.accept = field.accept;
      input.addEventListener("change", async () => {
        const [file] = input.files;
        if (!file) return;
        worker.postMessage({ type: "b3d", text: await file.text() });
        input.value = "";
      });
    } else {
      input = document.createElement("input");
      input.type = field.kind;
      if (field.kind === "text") input.spellcheck = false;
      for (const key of ["min", "max", "step"]) {
        if (field[key] !== undefined) input[key] = field[key];
      }
    }
    if (field.name) {
      input.name = field.name;
      input.id = `field-${field.name}`;
    }
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
  // Choices offered by another's value follow it as it changes.
  for (const field of FIELDS[source].filter((f) => f.by)) {
    const by = holder.querySelector(`[name=${field.by}]`);
    const input = holder.querySelector(`[name=${field.name}]`);
    by.addEventListener("change", () => {
      const kept = input.value;
      input.replaceChildren(
        ...Object.entries(about[field.from][by.value] || {}).map(([v, t]) => new Option(t, v)),
      );
      if ([...input.options].some((o) => o.value === kept)) input.value = kept;
      input.dispatchEvent(new Event("change"));
    });
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
  if (source === "shape") attachShape(holder);
  if (source === "word") attachDiagram(holder);
  if (source === "machine" || source === "lace") attachMachine(holder);
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
  // Only the braids whose fields that narrow the list are as chosen.
  const narrowing = FIELDS[source].filter((f) => f.narrows).map((f) => f.name);
  const offer = () => {
    const value = (name) => holder.querySelector(`[name=${name}]`)?.value ?? "";
    list.replaceChildren(
      ...examples
        .map((example, k) => [example, k])
        .filter(([example]) => narrowing.every((name) => String(example[name] ?? "") === value(name)))
        .map(([example, k]) => new Option(example.title, String(k))),
      new Option("Your own…", "custom"),
    );
  };
  offer();
  label.append(title, list);
  // After what is chosen first, as a sinnet's grid and shape; else first.
  const after = holder.querySelector("[name=shape]")?.closest("label");
  if (after) after.after(label);
  else holder.prepend(label);
  const shown = () => {
    const value = (name) => holder.querySelector(`[name=${name}]`)?.value ?? "";
    const same = (example) =>
      Object.entries(example).every(
        ([key, wanted]) =>
          key === "title" ||
          String(wanted).replace(/\s+/g, " ").trim() === value(key).replace(/\s+/g, " ").trim(),
      ) && (example.layout ?? "row") === (value("layout") || "row");
    const k = examples.findIndex(same);
    list.value = k < 0 || ![...list.options].some((o) => o.value === String(k)) ? "custom" : String(k);
  };
  for (const name of narrowing) {
    holder.querySelector(`[name=${name}]`).addEventListener("change", () => {
      offer();
      shown();
    });
  }
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
