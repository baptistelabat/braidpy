// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The form: what each source asks for, filled in from braidpy's catalogue,
// and the examples a source offers.

import { attachDiagram } from "./diagram.js";
import { attachEditor, attachShape } from "./editor.js";
import { attachMachine } from "./machine.js";
import { $ } from "./page.js";
import { submit, worker } from "./workers.js";

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
    // From a shape: shown for that entry only.
    { name: "shape", label: "Shape", kind: "choice", from: "shapes", entry: "shape" },
    {
      name: "size",
      label: "Size",
      kind: "number",
      min: 1,
      max: 12,
      entry: "shape",
      hint: "Lines along each side; an oblong's width.",
    },
    {
      name: "height",
      label: "Height",
      kind: "number",
      min: 1,
      max: 12,
      entry: "shape",
      hint: "An oblong's height, in lines.",
    },
    {
      name: "turned",
      label: "Tracks turned round",
      kind: "text",
      entry: "shape",
      hint: "Each track's moves made the other way round: click a track on the drawing.",
    },
    {
      name: "extra",
      label: "A strand more in spaces",
      kind: "text",
      entry: "shape",
      hint: "Each space named holds a strand more from the start, twice named two: as the book adds them at corners to sharpen the edges. Click a space on the drawing to add one, shift-click to take one off.",
    },
    {
      name: "corners",
      label: "At each corner",
      kind: "number",
      min: 0,
      max: 3,
      entry: "shape",
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
    { name: "n_gears", label: "Gears", kind: "number", min: 4, max: 32, step: 2, custom: true },
    {
      name: "card",
      label: "Punchcard",
      kind: "textarea",
      custom: true,
      hint: "A step a line: the gears turning anticlockwise, then those turning clockwise, a 0 or 1 for each gear from A, for example 1000 0100. A, C, E… turn anticlockwise, B, D, F… clockwise, and two neighbours never turn on the same line. Change it to make your own: the one chosen stays as it is.",
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
      const choices = field.from ? Object.entries(about[field.from]) : field.choices;
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
    if (field.entry) label.dataset.entry = field.entry;
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
    // An entry with fields of its own, as a sinnet from a shape, shows
    // them and not what the others are made of.
    const own = new Set(
      [...holder.querySelectorAll("[data-entry]")].map((label) => label.dataset.entry),
    );
    const showCustom = (shown) => {
      for (const label of holder.querySelectorAll("[data-custom]")) {
        label.hidden = !shown || own.has(entries.value);
      }
      for (const label of holder.querySelectorAll("[data-entry]")) {
        label.hidden = label.dataset.entry !== entries.value;
      }
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
  if (source === "sinnet") attachShape(holder);
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
