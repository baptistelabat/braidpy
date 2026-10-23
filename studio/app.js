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
//   frames.js    a marudai's moments, kept short for Grow and put back
//   insets.js    the cross-section and the view from above
//   info.js      the card: what is known of the braid
//   controls.js  the view's controls, sharing and saving
//   page.js      what they all share
//
// Each sets itself up as it loads, in this order.

import "./fields.js?v=ad08f375cb";
import "./diagram.js?v=ad08f375cb";
import "./machine.js?v=ad08f375cb";
import "./editor.js?v=ad08f375cb";
import "./spec.js?v=ad08f375cb";
import "./workers.js?v=ad08f375cb";
import "./defaults.js?v=ad08f375cb";
import "./scene.js?v=ad08f375cb";
import "./insets.js?v=ad08f375cb";
import "./info.js?v=ad08f375cb";
import "./colours.js?v=ad08f375cb";
import "./controls.js?v=ad08f375cb";
