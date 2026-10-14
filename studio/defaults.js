// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Settings left empty, and choices not made, take the braid's own: shown
// greyed with "default" once it is made.

import { $, round } from "./page.js?v=1c2a33787a";

// A setting left empty takes the braid's own default, shown greyed with
// "default" once the braid is made.  Going into the field puts the default
// in, so its arrows step from there; leaving it unchanged empties it again.
const SETTINGS = {
  yarn_diameter: (used) => round(used.yarn_diameter),
  iterations: (used) => used.iterations,
};

export function forgetDefaults() {
  for (const name of Object.keys(SETTINGS)) {
    const input = $(name);
    delete input.dataset.default;
    input.placeholder = "default";
  }
}

export function showDefaults(used) {
  if (!used) return;
  for (const [name, choice] of Object.entries(CHOICES)) markDefault($(name), choice.used(used));
  fitTwist();
  for (const [name, value] of Object.entries(SETTINGS)) {
    const input = $(name);
    const shown = value(used);
    if (shown === null || shown === undefined) {
      delete input.dataset.default;
      input.placeholder = name === "iterations" ? "not used on a marudai" : "default";
    } else if (input.value === "" || input.value === input.dataset.default) {
      input.dataset.default = String(shown);
      input.placeholder = `${shown} (default)`;
    }
  }
}

// A choice not made is the braid's own, selected and marked "default":
// guessed from its source until it is made, then as it was made.  Chosen
// otherwise, it stays chosen.
export const CHOICES = {
  settle: { guess: (source) => (source === "machine" ? "sideways" : "marudai"), used: (u) => u.settle },
  twist: {
    guess: (source) =>
      $("settle").value !== "marudai" ? "free" : source === "word" ? "turns" : "free",
    used: (u) => u.twist,
  },
};

// The ways of settling the yarns each source can have: a disk braid or a
// braid word any — a word to settle by physics is laid round a ring, as
// from a disk; a machine's braid, laid on its fell ring, sideways or by
// physics, but not on a marudai, which makes only disk moves.  Those it
// cannot have are not offered.
const SETTLES = {
  machine: ["sideways", "physics", "crossing"],
};

function fitSettle() {
  const settle = $("settle");
  const can = SETTLES[$("source").value];
  for (const option of settle.options) option.hidden = option.disabled = can ? !can.includes(option.value) : false;
  if (settle.selectedOptions[0]?.disabled) {
    settle.dataset.chosen = "";
    settle.value = settle.dataset.default;
    markDefault($("twist"), CHOICES.twist.guess($("source").value));
  }
}

// The twist as each way of settling the yarns can have it: on a marudai,
// kept, held while the bobbins turn, or untwisted; settled by physics, the
// end plate held or turning; tightened sideways, nothing to choose — the
// yarns keep the twist they were laid with.
function fitTwist() {
  fitSettle();
  const settle = $("settle").value;
  const twist = $("twist");
  twist.closest("label").hidden = settle === "sideways";
  const turns = twist.querySelector("option[value=turns]");
  turns.hidden = turns.disabled = settle !== "marudai";
  if (settle !== "marudai" && twist.dataset.default === "turns") {
    markDefault(twist, CHOICES.twist.guess($("source").value));
  }
  if (turns.disabled && twist.value === "turns") twist.value = twist.dataset.default;
}

$("settle").addEventListener("change", () => {
  markDefault($("twist"), CHOICES.twist.guess($("source").value));
  fitTwist();
});

function markDefault(select, value) {
  if (!value) return;
  for (const option of select.options) {
    option.dataset.text ??= option.textContent;
    option.textContent = option.dataset.text + (option.value === value ? " (default)" : "");
  }
  const chosen = select.dataset.chosen === "1";
  select.dataset.default = value;
  if (!chosen) select.value = value;
}

export function guessChoices(source, spec = {}) {
  for (const [name, choice] of Object.entries(CHOICES)) {
    const select = $(name);
    const given = spec[name] && spec[name] !== "auto" ? spec[name] : null;
    select.dataset.chosen = given ? "1" : "";
    markDefault(select, choice.guess(source));
    if (given) select.value = given;
  }
  fitTwist();
}

for (const name of Object.keys(CHOICES)) {
  const select = $(name);
  select.addEventListener("change", () => {
    select.dataset.chosen = select.value === select.dataset.default ? "" : "1";
  });
}

for (const name of Object.keys(SETTINGS)) {
  const input = $(name);
  input.addEventListener("focus", () => {
    if (input.value === "" && input.dataset.default) {
      input.value = input.dataset.default;
      input.select();
    }
  });
  input.addEventListener("blur", () => {
    if (input.value === input.dataset.default) input.value = "";
  });
}
