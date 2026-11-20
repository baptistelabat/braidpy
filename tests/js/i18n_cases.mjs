// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// web/i18n.js, the page in the site's language: each text read as JSON on
// stdin put through tr().  The module is imported from the directory given,
// where tests/test_i18n_js.py put it beside the locale.js web/build.py
// writes; a language given after it is chosen first, as from the page's
// menu.  Prints JSON for the test: each text's translation, and those left
// untranslated.

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

const { setLanguage, tr, untranslated } = await import(pathToFileURL(`${process.argv[2]}/i18n.js`));
if (process.argv[3]) setLanguage(process.argv[3]);
const texts = JSON.parse(readFileSync(0, "utf8"));
const shown = texts.map(tr);
// Shown again, as the page sees its own text change: nothing more is missing.
shown.forEach(tr);
console.log(JSON.stringify({ shown, untranslated: [...untranslated] }));
