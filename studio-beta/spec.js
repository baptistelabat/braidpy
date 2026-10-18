// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The braid asked for, read from the form, written into the address, and
// read back from it: a link makes the same braid.

import { chosenColours, useColours } from "./colours.js?v=5bdea3790c";
import { CHOICES, guessChoices } from "./defaults.js?v=5bdea3790c";
import { catalogue, renderFields } from "./fields.js?v=5bdea3790c";
import { $ } from "./page.js?v=5bdea3790c";

export function readSpec() {
  const spec = { source: $("source").value };
  // A catalogued braid is named; what it is made of is the catalogue's.
  const named = $("form").querySelector("select[name=name]")?.value !== "custom";
  for (const element of $("form").elements) {
    if (!element.name || element.name === "source") continue;
    // Every carrier taken off is no carriers, not the machine's own.
    if (element.name === "carriers" && !element.value.trim() && element.dataset.default) {
      spec.carriers = "none";
      continue;
    }
    if (element.value === "" || element.closest("[hidden]")) continue;
    if (named && element.closest("[data-custom]")) continue;
    // A machine's own loading is the machine's to make.
    if (element.name === "carriers" && element.value === element.dataset.default) continue;
    // A choice left as the braid's own default is the braid's to make.
    if (element.name in CHOICES && element.dataset.chosen !== "1") continue;
    spec[element.name] =
      element.type === "number" ? Number(element.value) : element.value;
  }
  // Colours chosen by hand are part of the braid asked for, so a link makes
  // the same braid in the same colours.
  const colours = chosenColours();
  if (colours) spec.colours = colours;
  return spec;
}

export function writeSpec(spec) {
  useColours(spec.colours);
  $("source").value = spec.source;
  renderFields(spec.source, spec);
  $("yarn_diameter").value = spec.yarn_diameter ?? "";
  $("iterations").value = spec.iterations ?? "";
  guessChoices(spec.source, spec);
}

export function specFromHash() {
  if (!location.hash.slice(1)) return null;
  const params = new URLSearchParams(location.hash.slice(1));
  const spec = Object.fromEntries(params.entries());
  if (!catalogue[spec.source]) return null;
  return spec;
}
