// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The 3D view: the braid, as laid and as it settles, its making replayed
// by Grow, and the camera.

import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { onChosen, paint } from "./colours.js?v=6acbd58c1f";
import { describe } from "./info.js?v=6acbd58c1f";
import { drawSection, drawTop } from "./insets.js?v=6acbd58c1f";
import { $ } from "./page.js?v=6acbd58c1f";
import { pending } from "./workers.js?v=6acbd58c1f";

export let lastResult = null;

const viewer = $("viewer");
export const renderer = new THREE.WebGLRenderer({
  antialias: true,
  preserveDrawingBuffer: true,
});
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
viewer.append(renderer.domElement);

export const scene = new THREE.Scene();
export const camera = new THREE.PerspectiveCamera(35, 1, 0.01, 1000);
camera.up.set(0, 0, 1);
export const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.autoRotateSpeed = 1.5;

scene.add(new THREE.HemisphereLight(0xffffff, 0x8a8478, 1.6));
const key = new THREE.DirectionalLight(0xffffff, 1.6);
key.position.set(4, -6, 8);
scene.add(key);
const fill = new THREE.DirectionalLight(0xffffff, 0.5);
fill.position.set(-6, 4, -2);
scene.add(fill);

function stageColour() {
  return getComputedStyle(document.documentElement)
    .getPropertyValue("--stage")
    .trim();
}
scene.background = new THREE.Color(stageColour());
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
  scene.background = new THREE.Color(stageColour());
});

function resize() {
  const { clientWidth: width, clientHeight: height } = viewer;
  if (!width || !height) return;
  renderer.setSize(width, height, false);
  renderer.domElement.style.width = width + "px";
  renderer.domElement.style.height = height + "px";
  camera.aspect = width / height;
  clearOfCard();
}
new ResizeObserver(() => {
  resize();
  if (braid) drawTop(currentTime());
  drawSection(lastResult);
}).observe(viewer);

// What is known of the braid lies over the view's left: the braid is drawn
// in the middle of what it leaves free, not behind it.
function cardCover() {
  const card = $("about");
  if (card.hidden || getComputedStyle(card).position !== "absolute") return 0;
  return card.getBoundingClientRect().right - viewer.getBoundingClientRect().left;
}

function clearOfCard() {
  const { clientWidth: width, clientHeight: height } = viewer;
  if (!width || !height) return;
  const cover = Math.min(cardCover(), width / 2);
  if (cover > 0) camera.setViewOffset(width, height, -cover / 2, 0, width, height);
  else camera.clearViewOffset();
  camera.updateProjectionMatrix();
}
$("about").addEventListener("toggle", clearOfCard);
new ResizeObserver(clearOfCard).observe($("about"));

function currentTime() {
  const [first, last] = braid.span;
  return first + (Number($("made").value) / 1000) * (last - first);
}
resize();

// What is drawn: per yarn its tube and its line, each revealed up to how
// much of the braid is made.
export let braid = null;
// How far round the vertical the starting view is turned, per source, so
// the braid's seam — where its numbering round the ring closes, and no
// strand crosses — is away from the viewer.
const VIEW_TURN = { word: Math.PI, kumihimo: Math.PI, sinnet: Math.PI / 2 };

// Where a disk's numbering closes — between its first slot (or space) and
// its last — as an angle seen from above, in the top view's frame.
function seamOf(timeline) {
  if (timeline?.kind !== "disk") return null;
  const named = timeline.slots.filter(([, , name]) => Number.isFinite(Number(name)));
  if (named.length < 2) return null;
  // Numbered from 0 or from 1.
  const first = named.reduce((a, b) => (Number(b[2]) < Number(a[2]) ? b : a));
  const last = named.reduce((a, b) => (Number(b[2]) > Number(a[2]) ? b : a));
  const unit = ([x, y]) => [x / (Math.hypot(x, y) || 1), y / (Math.hypot(x, y) || 1)];
  const [ax, ay] = unit(first);
  const [bx, by] = unit(last);
  return Math.atan2(ay + by, ax + bx);
}

// A disk braid made on a marudai, seen in the top view's frame turned so
// its seam is up, away from the viewer at the bottom: how far to turn the
// 3D braid about the vertical for its carriers to be where the top view
// has them.  Measured where they start: each strand's slot as marudai.js
// takes it, in the 3D view, hanging or not, against where the top view has
// it.  The braid turning as it is made turns both alike.
function alignment() {
  const view = braid.timeline;
  const program = braid.program;
  const sense = program.clockwise ? -1 : 1;
  let sx = 0;
  let sy = 0;
  program.start.forEach((slot, k) => {
    const angle = (sense * 2 * Math.PI * (slot - 1)) / program.n_slots;
    // The page has the braid turned over (y the other way); hanging turns
    // it back.
    const seen = braid.stand.rotation.x ? angle : -angle;
    const [tx, ty] = view.strands[k][0];
    const d = seen - Math.atan2(ty, tx);
    sx += Math.cos(d);
    sy += Math.sin(d);
  });
  return braid.topTurn - Math.atan2(sy, sx);
}

// Whether braids hang from their fell, as from a kumihimo disk or a marudai,
// or rise from it, as from a braiding machine: braids made on a marudai —
// disk braids and words — hang unless asked otherwise, machines' rise.
export const hangs = { disk: true, other: false };

function dispose(object) {
  object.traverse((child) => {
    child.geometry?.dispose();
    child.material?.dispose();
  });
}

export let shownLaid = null;

export function show(result, seconds, keepView = false) {
  // One place decides what colour a strand is.
  paint(result);
  shownLaid = seconds === null ? pending : null;
  if (braid) {
    scene.remove(braid.turner);
    dispose(braid.turner);
  }
  lastResult = result;
  const group = new THREE.Group();
  const yarns = [];
  const radius = result.yarn_diameter / 2;
  const times = result.times || result.strands[0].points.map((_, i) => i);
  result.strands.forEach((strand, k) => {
    let laid = strand.points;
    // Made on a marudai: the yarn goes on, one tube, out of the braid at
    // the fell to its carrier over the mirror.
    const tail = result.marudai?.tails[k];
    if (tail) {
      const fell = laid[laid.length - 1][2];
      laid = [...laid, ...tail.filter(([, , z]) => z < fell)];
    }
    const points = laid.map(([x, y, z]) => new THREE.Vector3(x, y, z));
    const pointTimes = points.length > times.length ? [...times, ...Array(points.length - times.length).fill(times[times.length - 1])] : times;
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal");
    const segments = Math.min(Math.max(points.length * 3, 64), 4000);
    const radial = 10;
    // When each tube segment was laid: tubes are cut evenly along their
    // length, which is not evenly along the points.
    const segmentTimes = new Float64Array(segments + 1);
    for (let i = 0; i <= segments; i++) {
      const along = curve.getUtoTmapping(i / segments) * (points.length - 1);
      segmentTimes[i] = sample(pointTimes, along);
    }
    const tube = new THREE.Mesh(
      new THREE.TubeGeometry(curve, segments, radius, radial, false),
      new THREE.MeshStandardMaterial({
        color: strand.colour,
        roughness: 0.55,
        metalness: 0.05,
      }),
    );
    tube.name = strand.name;
    const line = new THREE.Line(
      new THREE.BufferGeometry().setFromPoints(curve.getSpacedPoints(segments)),
      new THREE.LineBasicMaterial({ color: strand.colour }),
    );
    group.add(tube, line);
    yarns.push({ tube, line, segments, radial, segmentTimes });
  });
  for (const core of result.cores || []) {
    const from = new THREE.Vector3(...core.from);
    const to = new THREE.Vector3(...core.to);
    const length = from.distanceTo(to);
    const mesh = new THREE.Mesh(
      new THREE.CylinderGeometry(core.diameter / 2, core.diameter / 2, length, 16),
      new THREE.MeshStandardMaterial({ color: 0x77736c, roughness: 0.8 }),
    );
    mesh.position.copy(from.clone().add(to).multiplyScalar(0.5));
    mesh.quaternion.setFromUnitVectors(
      new THREE.Vector3(0, 1, 0),
      to.clone().sub(from).normalize(),
    );
    mesh.userData.core = true;
    group.add(mesh);
  }
  // Made on a marudai: the mirror the yarns lie over, seen through.
  const tails = [];
  if (result.marudai) {
    const mirror = mirrorMesh(result.marudai.disk);
    mirror.userData.whole = true;
    group.add(mirror);
  }
  // The braid in the disk's turn, then turned rising from its fell or hanging
  // from it: a half turn about a level axis, so it is still the same braid,
  // not its mirror image.
  const stand = new THREE.Group();
  const turner = new THREE.Group();
  stand.add(group);
  turner.add(stand);
  scene.add(turner);
  const timeline = result.timeline;
  // Made on a marudai — a disk braid, or a word rolled onto one — or not.
  const kind = result.disk ? "disk" : "other";
  $("hanging").checked = hangs[kind];
  const clock = timeline
    ? timeline.clock
    : { source: [times[0], times[times.length - 1]], braid: [times[0], times[times.length - 1]] };
  const span = timeline
    ? [timeline.times[0], timeline.times[timeline.times.length - 1]]
    : [clock.source[0], clock.source[clock.source.length - 1]];
  braid = {
    group,
    stand,
    turner,
    kind,
    yarns,
    tails,
    radius,
    frames: result.marudai?.frames,
    source: $("source").value,
    disk: result.marudai?.disk,
    steps: result.disk?.steps.length || 1,
    frame: null,
    times,
    heights: result.strands[0].points.map((p) => p[2]),
    clock,
    span,
    timeline,
    colours: result.strands.map((strand) => strand.colour),
    box: null,
  };
  stand.rotation.x = hangs[kind] ? Math.PI : 0;
  // A disk's top view turned so its seam is away from the viewer, and the
  // braid made on a marudai turned to match it.
  const seam = seamOf(timeline);
  braid.topTurn = seam === null ? 0 : Math.PI / 2 - seam;
  braid.program = result.disk;
  braid.aligned = seam !== null && Boolean(result.disk) && result.settled !== "sideways";
  if (braid.aligned) turner.rotation.z = alignment();
  braid.box = new THREE.Box3().setFromObject(turner);
  showTubes($("tubes").checked);
  $("topview").hidden = !timeline || !$("showtop").checked;
  $("section").hidden = !$("showsection").checked;
  drawSection(result);
  $("made").value = $("made").max;
  made(Number($("made").max));
  if (!keepView) fit();
  describe(result, seconds);
  $("empty").hidden = true;
}

// A marudai's mirror, seen through: a ring from its hole to its edge.
function mirrorMesh({ z, radius, hole }) {
  const mirror = new THREE.Mesh(
    new THREE.RingGeometry(hole, radius, 128),
    new THREE.MeshStandardMaterial({
      color: 0xc9bfae,
      roughness: 0.4,
      transparent: true,
      opacity: 0.28,
      side: THREE.DoubleSide,
      depthWrite: false,
    }),
  );
  mirror.position.z = z;
  return mirror;
}

// A moment in the making on a marudai, in place of the braid as made:
// every yarn whole, from the start of the braid out over the mirror to its
// bobbin, one tube each, and the mirror.
export function showFrame(frame, disk, colours) {
  if (!braid) return;
  clearFrame();
  const shown = new THREE.Group();
  const tubes = $("tubes").checked;
  frame.yarns.forEach((flat, i) => {
    const points = [];
    for (let k = 0; k < flat.length; k += 3) points.push(new THREE.Vector3(flat[k], flat[k + 1], flat[k + 2]));
    if (points.length < 2) return;
    const curve = new THREE.CatmullRomCurve3(points, false, "centripetal");
    const segments = Math.min(Math.max(points.length * 2, 32), 1500);
    shown.add(
      tubes
        ? new THREE.Mesh(
            new THREE.TubeGeometry(curve, segments, braid.radius, 8, false),
            new THREE.MeshStandardMaterial({ color: colours[i], roughness: 0.55, metalness: 0.05 }),
          )
        : new THREE.Line(
            new THREE.BufferGeometry().setFromPoints(curve.getSpacedPoints(segments)),
            new THREE.LineBasicMaterial({ color: colours[i] }),
          ),
    );
  });
  if (disk) shown.add(mirrorMesh(disk));
  for (const child of braid.group.children) child.visible = false;
  braid.group.add(shown);
  braid.frame = shown;
  braid.group.position.z = 0;
  // The braid's own turning is in the moment already.
  braid.turner.rotation.z = braid.aligned ? alignment() : 0;
}

function clearFrame() {
  if (!braid?.frame) return;
  braid.group.remove(braid.frame);
  dispose(braid.frame);
  braid.frame = null;
}

export function showTubes(tubes) {
  if (!braid) return;
  for (const yarn of [...braid.yarns, ...braid.tails]) {
    yarn.tube.visible = tubes;
    yarn.line.visible = !tubes;
  }
  made(Number($("made").value));
}

// Show the braid as it was ``value`` thousandths of the way through its
// making, by the clock of whatever made it: the oldest rows first, carried
// up by the take-off, the newest at the fell.  The top view shows what made
// it, at that same instant.
export function made(value) {
  if (!braid) return;
  const fraction = value / 1000;
  const [first, last] = braid.span;
  // Made on a marudai: the making itself, move by move, until it is made.
  const frames = braid.frames;
  if (frames?.length && fraction < 0.999) {
    const frame = frames[Math.min(frames.length - 1, Math.floor(fraction * frames.length))];
    showFrame(frame, braid.disk, braid.colours);
    topAtFrame(frame);
    return;
  }
  clearFrame();
  const tubesShown = $("tubes").checked;
  for (const yarn of braid.yarns) {
    yarn.tube.visible = tubesShown;
    yarn.line.visible = !tubesShown;
  }
  const now = first + fraction * (last - first);
  const laid = interpolate(braid.clock.source, braid.clock.braid, now);
  for (const yarn of braid.yarns) {
    const shown = Math.max(1, countUpTo(yarn.segmentTimes, laid + 1e-9) - 1);
    yarn.tube.geometry.setDrawRange(0, shown * yarn.radial * 6);
    yarn.line.geometry.setDrawRange(0, shown + 1);
  }
  const heights = braid.heights;
  const newest = interpolate(braid.times, heights, laid);
  braid.group.position.z = heights[heights.length - 1] - newest;
  // A disk's braid hangs from it and turns with it.
  const timeline = braid.timeline;
  braid.turner.rotation.z = braid.aligned
    ? alignment()
    : timeline?.turn
      ? interpolate(timeline.times, timeline.turn, now)
      : 0;
  // The cores, and a marudai's tails and mirror, once the braid is made.
  const tubes = $("tubes").checked;
  for (const child of braid.group.children) {
    if (child.userData.core) child.visible = fraction > 0.999;
    if (child.userData.whole) {
      const kind = child.isMesh && child.geometry.type === "TubeGeometry" ? tubes : child.isLine ? !tubes : true;
      child.visible = fraction > 0.999 && kind;
    }
  }
  drawTop(now);
}

// The top view at a moment of the making on a marudai: during a move, the
// yarns it has carried so far already where it takes them, the others still
// where they were.
export function topAtFrame(frame) {
  const [first, last] = braid.span;
  const at = (k) => first + Math.max(0, Math.min(1, k / braid.steps)) * (last - first);
  const moved = frame.moved && new Set(frame.moved);
  drawTop(at(frame.step + 1), moved && { before: at(frame.step), moved });
}

// ``ys`` at ``x``, between the samples ``xs`` (ascending), held at the ends.
function interpolate(xs, ys, x) {
  const n = xs.length;
  if (x <= xs[0]) return ys[0];
  if (x >= xs[n - 1]) return ys[n - 1];
  let low = 0;
  let high = n - 1;
  while (high - low > 1) {
    const middle = (low + high) >> 1;
    if (xs[middle] <= x) low = middle;
    else high = middle;
  }
  const span = xs[high] - xs[low];
  const t = span > 0 ? (x - xs[low]) / span : 0;
  return ys[low] + t * (ys[high] - ys[low]);
}

// ``values`` at a fractional index.
function sample(values, at) {
  const low = Math.floor(at);
  const high = Math.min(low + 1, values.length - 1);
  return values[low] + (at - low) * (values[high] - values[low]);
}

// How many of the ascending ``values`` are at most ``limit``.
function countUpTo(values, limit) {
  let low = 0;
  let high = values.length;
  while (low < high) {
    const middle = (low + high) >> 1;
    if (values[middle] <= limit) low = middle + 1;
    else high = middle;
  }
  return low;
}

export function fit() {
  if (!braid) return;
  const box = braid.box;
  const centre = box.getCenter(new THREE.Vector3());
  const size = box.getSize(new THREE.Vector3());
  const height = size.z;
  const across = Math.max(size.x, size.y);
  const fov = THREE.MathUtils.degToRad(camera.fov);
  const tall = height / 2 / Math.tan(fov / 2);
  // Wide enough for what the card leaves free.
  const free = Math.max(0.5, 1 - Math.min(cardCover(), viewer.clientWidth / 2) / viewer.clientWidth);
  const wide = across / 2 / Math.tan(fov / 2) / Math.max(camera.aspect * free, 0.3);
  const distance = 1.25 * Math.max(tall, wide, across * 2);
  // Seen from the side the strands' seam is not: a disk braid made on a
  // marudai from the top view's bottom, as it is turned; others turned
  // about the vertical as each kind of braid needs it.
  const direction = braid.aligned
    ? new THREE.Vector3(0.2, -1, 0.3).normalize()
    : new THREE.Vector3(1, -0.45, 0.25)
        .normalize()
        .applyAxisAngle(new THREE.Vector3(0, 0, 1), VIEW_TURN[braid.source] ?? 0);
  camera.position.copy(centre).addScaledVector(direction, distance);
  camera.near = distance / 100;
  camera.far = distance * 100;
  camera.updateProjectionMatrix();
  controls.target.copy(centre);
  controls.update();
}

// Choosing a colour does not remake the braid: the strands are the ones that
// were made, and only what they are painted with changes.
onChosen(() => {
  if (lastResult) show(lastResult, null, true);
});
