// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The view's controls: tubes or lines, the insets, spin, hanging, Grow,
// sharing and saving; and what the page holds, for its tests.

import * as THREE from "three";
import { OBJExporter } from "three/addons/exporters/OBJExporter.js";
import { STLExporter } from "three/addons/exporters/STLExporter.js";
import { copyText } from "./info.js?v=3405c70a71";
import { drawSection, section, top } from "./insets.js?v=3405c70a71";
import { $ } from "./page.js?v=3405c70a71";
import { braid, camera, controls, fit, hangs, lastResult, made, renderer, scene, showTubes } from "./scene.js?v=3405c70a71";

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

let growing = false;
let growFrom = 0;
$("grow").addEventListener("click", () => {
  growing = !growing;
  $("grow").textContent = growing ? "⏸ Pause" : "▶ Grow";
  if (growing) {
    if (Number($("made").value) >= 1000) $("made").value = 0;
    growFrom = performance.now() - Number($("made").value) * 12;
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

$("save").addEventListener("change", (event) => {
  const what = event.target.value;
  event.target.value = "";
  if (!lastResult || !braid) return;
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
    // Twelve seconds from nothing to the whole braid.
    const value = Math.min(1000, (now - growFrom) / 12);
    $("made").value = value;
    made(value);
    if (value >= 1000) {
      growing = false;
      $("grow").textContent = "▶ Grow";
    }
  }
  controls.update();
  renderer.render(scene, camera);
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
