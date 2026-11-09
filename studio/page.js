// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// What the whole page shares.

export const $ = (id) => document.getElementById(id);

// A press handled this long after it was made — the page busy drawing a big
// braid — is let go rather than acted on late: a stepper pressed a few times
// while the page was busy does not run on by itself once it is free.
const STALE_MS = 1000;
export function inTime(event) {
  return performance.now() - event.timeStamp < STALE_MS;
}

export function round(value) {
  return Number(value.toPrecision(3));
}
