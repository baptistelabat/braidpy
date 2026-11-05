// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// web/colours.js, the colours chosen for a braid's strands, as written into
// its link.  The page itself is a stand-in: only what the module asks of it
// when it loads.  Prints JSON for tests/test_colours_js.py.

globalThis.document = { addEventListener() {}, getElementById: () => null };
const colours = await import("../../web/colours.js");

const braid = (n) => ({ strands: Array.from({ length: n }, () => ({ colour: "#999999" })) });
const out = {};

// Strands 2, 5, 17 and 19 coloured on a braid of twenty.
colours.useColours(",,#ff0000,,,#00ff00" + ",".repeat(12) + "#0000ff,,#123456");
out.chosenOnTwenty = colours.chosenColours();
out.letGo = colours.rebase(braid(20));
// A braid of sixteen made after it.
out.letGoOnSixteen = colours.rebase(braid(16));
out.chosenOnSixteen = colours.chosenColours();
// The same again: nothing more to let go.
out.letGoAgain = colours.rebase(braid(16));
// Empty places after the last colour say nothing.
colours.useColours("#ff0000,,,");
out.trailing = colours.chosenColours();
colours.useColours(",,");
out.none = colours.chosenColours();

console.log(JSON.stringify(out));
