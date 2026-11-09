// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The view's controls: tubes or lines, the insets, spin, hanging, Grow,
// sharing and saving; and what the page holds, for its tests.

import * as THREE from "three";
import { OBJExporter } from "three/addons/exporters/OBJExporter.js";
import { STLExporter } from "three/addons/exporters/STLExporter.js";
import { copyText } from "./info.js?v=f65efc4a5f";
import { drawSection, section, top } from "./insets.js?v=f65efc4a5f";
import { $ } from "./page.js?v=f65efc4a5f";
import {
  awake,
  braid,
  camera,
  controls,
  fit,
  hangs,
  lastResult,
  made,
  renderer,
  SUBSTEPS,
  scene,
  showTubes,
} from "./scene.js?v=f65efc4a5f";
import { b3dOf } from "./workers.js?v=f65efc4a5f";

$("tubes").addEventListener("change", (event) => showTubes(event.target.checked));
$("showsection").addEventListener("change", (event) => {
  section.hidden = !event.target.checked || !lastResult;
  drawSection(lastResult);
});
$("showtop").addEventListener("change", (event) => {
  top.hidden = !event.target.checked || !braid || !braid.timeline;
  made(Number($("made").value));
});
$("spin").addEventListener("change", (event) => {
  controls.autoRotate = event.target.checked;
});
$("hanging").addEventListener("change", (event) => {
  if (!braid) return;
  hangs[braid.kind] = event.target.checked;
  braid.stand.rotation.x = event.target.checked ? Math.PI : 0;
  made(Number($("made").value));
  braid.box = new THREE.Box3().setFromObject(braid.turner);
  drawSection(lastResult);
  fit();
});
$("reset").addEventListener("click", fit);
$("made").addEventListener("input", (event) => {
  growing = false;
  $("grow").textContent = "▶ Grow";
  made(Number(event.target.value));
});
// The arrow keys go a sub-step at a time, and with Shift a whole step, by
// the clock of whatever made the braid, from the one it is nearest.
$("made").addEventListener("keydown", (event) => {
  const way = { ArrowRight: 1, ArrowUp: 1, ArrowLeft: -1, ArrowDown: -1 }[event.key];
  if (!way || !braid) return;
  const [first, last] = braid.span;
  const length = last - first;
  // Made in less than a step: the slider's own steps.
  if (!(length >= 1)) return;
  event.preventDefault();
  const slider = $("made");
  const most = Number(slider.max);
  const per = event.shiftKey ? 1 : 1 / SUBSTEPS;
  const at = (Number(slider.value) / most) * length;
  const next = Math.min(length, Math.max(0, (Math.round(at / per) + way) * per));
  slider.value = String(Math.round((next / length) * most));
  slider.dispatchEvent(new Event("input"));
});

// Grow: from nothing to the whole braid in so long.
const GROW_MS = 12000;
let growing = false;
let growFrom = 0;
$("grow").addEventListener("click", () => {
  growing = !growing;
  $("grow").textContent = growing ? "⏸ Pause" : "▶ Grow";
  if (growing) {
    const most = Number($("made").max);
    if (Number($("made").value) >= most) $("made").value = 0;
    growFrom = performance.now() - (Number($("made").value) / most) * GROW_MS;
  }
});

$("share").addEventListener("click", () => copyText(location.href, $("share")));

function fileName(extension) {
  return lastResult.title.replace(/[^\w-]+/g, "_") + "." + extension;
}

function download(name, href) {
  const link = document.createElement("a");
  link.download = name;
  link.href = href;
  link.click();
  if (href.startsWith("blob:")) setTimeout(() => URL.revokeObjectURL(href), 1000);
}

// Only a braid with a disk program can be made on braid3dmin's marudai.
for (const asked of ["focus", "pointerdown"]) {
  $("save").addEventListener(asked, () => {
    $("save-b3d").hidden = !lastResult?.disk;
  });
}

$("save").addEventListener("change", (event) => {
  const what = event.target.value;
  event.target.value = "";
  if (!lastResult || !braid) return;
  if (what === "b3d") {
    if (!lastResult.disk) return;
    const name = fileName("b3d");
    const status = $("status");
    status.textContent = "Making it on the marudai, for braid3dmin…";
    b3dOf(lastResult).then(
      (text) => {
        download(name, URL.createObjectURL(new Blob([text], { type: "text/plain" })));
        status.textContent = `Saved for braid3dmin: ${name}`;
      },
      (error) => {
        status.textContent = `Not saved for braid3dmin: ${error.message}`;
      },
    );
    return;
  }
  if (what === "png") {
    download(fileName("png"), renderer.domElement.toDataURL("image/png"));
    return;
  }
  if (what === "json") {
    const blob = new Blob([JSON.stringify(lastResult)], { type: "application/json" });
    download(fileName("json"), URL.createObjectURL(blob));
    return;
  }
  // The whole braid as solid tubes, as made, in the braid's own units.
  const solid = new THREE.Group();
  for (const yarn of braid.yarns) {
    const tube = new THREE.Mesh(yarn.tube.geometry.clone(), yarn.tube.material);
    tube.geometry.setDrawRange(0, Infinity);
    tube.name = yarn.tube.name;
    solid.add(tube);
  }
  for (const child of braid.group.children) {
    if (child.userData.core) solid.add(child.clone());
  }
  solid.updateMatrixWorld(true);
  if (what === "stl") {
    const data = new STLExporter().parse(solid, { binary: true });
    download(fileName("stl"), URL.createObjectURL(new Blob([data])));
  } else if (what === "obj") {
    const text = new OBJExporter().parse(solid);
    download(fileName("obj"), URL.createObjectURL(new Blob([text])));
  }
  solid.traverse((child) => {
    if (child.isMesh && !child.userData.core) child.geometry.dispose();
  });
});

function frame(now) {
  if (growing && braid) {
    const most = Number($("made").max);
    const value = Math.min(most, ((now - growFrom) / GROW_MS) * most);
    $("made").value = value;
    made(value);
    if (value >= most) {
      growing = false;
      $("grow").textContent = "▶ Grow";
    }
  }
  // Drawn while the view moves, spins or grows, or something changed.
  const moved = controls.update();
  if (moved || growing || controls.autoRotate || awake(now)) renderer.render(scene, camera);
  requestAnimationFrame(frame);
}
requestAnimationFrame(frame);

// For tests: what the page holds.
window.braidStudio = {
  get result() {
    return lastResult;
  },
  get drawn() {
    return braid ? braid.yarns.length : 0;
  },
};
