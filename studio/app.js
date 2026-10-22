// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// Braid Studio: describe a braid, and braidpy — running in a worker through
// Pyodide — lays and tightens it; three.js draws it here.
//
// The page is in modules, each one part of it:
//
//   fields.js    the form: what each source asks for, and its examples
//   diagram.js   a braid word drawn as it is typed
//   machine.js   a machine from above, loaded by hand
//   editor.js    a disk or sinnet's moves, typed in or clicked
//   spec.js      the braid asked for, in the form and in the address
//   workers.js   braidpy and the settling, each in a worker of its own
//   defaults.js  settings left empty and choices not made: the braid's own
//   scene.js     the 3D view: the braid, as laid, as settled, as made
//   insets.js    the cross-section and the view from above
//   info.js      the card: what is known of the braid
//   controls.js  the view's controls, sharing and saving
//   page.js      what they all share
//
// Each sets itself up as it loads, in this order.

import "./fields.js?v=dfbc233bbc";
import "./diagram.js?v=dfbc233bbc";
import "./machine.js?v=dfbc233bbc";
import "./editor.js?v=dfbc233bbc";
import "./spec.js?v=dfbc233bbc";
import "./workers.js?v=dfbc233bbc";
import "./defaults.js?v=dfbc233bbc";
import "./scene.js?v=dfbc233bbc";
import "./insets.js?v=dfbc233bbc";
import "./info.js?v=dfbc233bbc";
import "./colours.js?v=dfbc233bbc";
import "./controls.js?v=dfbc233bbc";
