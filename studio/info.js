// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The card beside the braid: what is known of it, its words to copy or
// make again, the other ways of making it and the braids nearest it, and
// notes.

import { catalogue } from "./fields.js?v=bccf4f55b3";
import { $, round } from "./page.js?v=bccf4f55b3";
import { lastResult } from "./scene.js?v=bccf4f55b3";
import { writeSpec } from "./spec.js?v=bccf4f55b3";
import { pending, submit, worker } from "./workers.js?v=bccf4f55b3";

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

// The braid's kin (braidpy.topology_catalog.for_page): every other way of
// making the same braid, and the braids nearest it, each a button to make
// it.  None: nothing known yet, nothing shown.
export function showKin(kin) {
  const box = $("kin");
  box.replaceChildren();
  if (!kin) return;
  const lists = [
    [
      "Also made as",
      kin.same,
      "The same braid, made another way: nothing braidpy measures tells them apart",
    ],
    [
      "Nearest braids",
      kin.near,
      "Braids of the catalogues most like this one, by their topology — strands, loops, crossings, linking and Alexander polynomial — whatever way each is made",
    ],
  ];
  for (const [heading, methods, about] of lists) {
    if (!methods.length) continue;
    const title = document.createElement("h3");
    title.textContent = heading;
    title.title = about;
    const list = document.createElement("ul");
    for (const method of methods) {
      const item = document.createElement("li");
      const make = document.createElement("button");
      make.type = "button";
      make.className = "link";
      make.textContent = method.title;
      make.title = `Make it: ${method.title}`;
      make.addEventListener("click", () => {
        writeSpec(method.spec);
        submit();
      });
      const from = document.createElement("span");
      from.className = "muted";
      const source = catalogue[method.source]?.title ?? method.source;
      from.textContent =
        method.distance === undefined ? ` ${source}` : ` ${source} · ${method.distance}`;
      if (method.distance !== undefined) from.title = "How unlike: 0 the same, up to 5";
      item.append(make, from);
      list.append(item);
    }
    box.append(title, list);
  }
}

// The braid made other ways (braidpy.bridges): its repeating unit as a
// kumihimo disk's moves, to make here; as a lace machine's punchcard, to
// copy or download; and, when asked, as a sinnet on Ashley's stand, which
// is searched for.  None: nothing shown.
export function showBridges(bridges) {
  const box = $("bridges");
  box.replaceChildren();
  if (!bridges || !bridges.lace) return;
  const title = document.createElement("h3");
  title.textContent = "Make it as…";
  title.title = "The same braid, made another way: each checked by reading the braid back off what makes it";
  const list = document.createElement("ul");
  const item = (...parts) => {
    const li = document.createElement("li");
    li.append(...parts);
    list.append(li);
    return li;
  };
  const muted = (text) => {
    const span = document.createElement("span");
    span.className = "muted";
    span.textContent = text;
    return span;
  };
  const link = (text, spec) => {
    const make = document.createElement("button");
    make.type = "button";
    make.className = "link";
    make.textContent = text;
    make.addEventListener("click", () => {
      writeSpec(spec);
      submit();
    });
    return make;
  };
  const small = (text, act) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "small";
    button.textContent = text;
    button.addEventListener("click", () => act(button));
    return button;
  };

  if (bridges.disk) {
    const moves = bridges.disk.moves.split(", ").length;
    item(
      link("Kumihimo disk", bridges.disk.spec),
      muted(` ${moves} moves a repeat `),
      small("Copy moves", (button) => copyText(bridges.disk.moves, button)),
    );
  }

  const sinnet = item(
    document.createTextNode("Ashley's stand "),
    small("Find a sinnet", (button) => {
      button.disabled = true;
      button.textContent = "Searching…";
      const asked = pending;
      const heard = ({ detail }) => {
        if (detail.id !== asked) return;
        document.removeEventListener("braid-sinnet", heard);
        const found = detail.sinnet;
        sinnet.replaceChildren();
        if (found?.spec) {
          sinnet.append(
            link("Ashley's stand", found.spec),
            muted(` a sinnet: spaces of ${found.spec.counts}, moves ${found.spec.moves}`),
          );
        } else if (found?.exact) {
          // No sinnet of the book's kind: the braid itself, one strand a space.
          const moves = found.exact.moves.split(", ").length;
          sinnet.append(
            link("Ashley's stand", found.exact),
            muted(` one strand a space, ${moves} moves a repeat: no sinnet of the book's kind makes it`),
          );
        } else {
          sinnet.append(muted("Ashley's stand: no sinnet found"));
        }
      };
      document.addEventListener("braid-sinnet", heard);
      worker.postMessage({ type: "sinnet", id: asked });
    }),
  );

  const lace = bridges.lace;
  const card =
    `Lace machine of ${lace.gears} gears; bobbins in notches ${lace.threading}.\n` +
    "Two lines a step, ● punched: the gears turning anticlockwise ↺, then clockwise ↻.\n" +
    lace.card +
    "\n";
  item(
    document.createTextNode("Lace machine"),
    muted(` ${lace.gears} gears, ${lace.steps} steps a repeat `),
    small("Copy card", (button) => copyText(card, button)),
    small("Download", () => {
      const file = new Blob([card], { type: "text/plain" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(file);
      a.download = "lace-card.txt";
      a.click();
      URL.revokeObjectURL(a.href);
    }),
  );
  box.append(title, list);
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
