// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The yarns settled: tightened sideways, settled by physics, or made move
// by move on a marudai — the slow part of making a braid, in a worker of
// its own, apart from Python, so the page can stop it at once by ending
// this worker, and keep braidpy loaded in the other.
//
// Messages in:   {type: "settle", id, result, job, settle, twist}
//                  braidpy's braid as laid, what tightening it needs, and how
// Messages out:  {type: "status", text}
//                {type: "laid", id, result}      the braid as it goes
//                {type: "frame", id, frame, disk, colours}
//                {type: "result", id, result, seconds}
//                {type: "error", id, message}

importScripts("tighten.js?v=ad08f375cb", "rope.js?v=ad08f375cb", "form.js?v=ad08f375cb", "marudai.js?v=ad08f375cb");

function status(text) {
  self.postMessage({ type: "status", text });
}

// The braid on the marudai, kept to make more of; and the newest braid
// asked for, waiting for the one in hand to let it in.
let onDisk = null;
let asked = null;
let busy = false;

self.onmessage = ({ data }) => {
  if (data.type !== "settle") return;
  asked = data;
  if (!busy) run();
};

async function run() {
  busy = true;
  while (asked) {
    const message = asked;
    asked = null;
    try {
      const started = performance.now();
      const result = await settle(message);
      if (result) {
        const seconds = (performance.now() - started) / 1000;
        self.postMessage({ type: "result", id: message.id, result, seconds });
      }
    } catch (error) {
      self.postMessage({ type: "error", id: message.id, message: String(error?.message ?? error) });
    }
  }
  busy = false;
}

async function settle({ id, result, job, settle, twist }) {
  if (job) {
    if (settle === "marudai") result = await onMarudai(id, result, { ...job, twist });
    else if (settle === "crossing") result = formed(id, result, { ...job, twist });
    else if (settle !== "sideways") result = settled(id, result, { ...job, twist });
    else {
      status("Tightening the yarns…");
      const tight = tightenYarns(job, (fraction) =>
        status(`Tightening the yarns… ${Math.round(100 * fraction)}%`),
      );
      result = tightened(result, job, tight);
    }
    if (!result) return null;
    result.settled = settle;
  }
  // What the braid was made with, for the page to show what was taken by
  // default: the marudai pulls its yarns tight itself, in no set steps.
  result.used = {
    yarn_diameter: result.yarn_diameter,
    iterations: settle === "marudai" && job ? null : job?.iterations ?? 0,
    // The braid's own choices, for the page to mark as its defaults.
    settle: job ? (result.disk ? "marudai" : "sideways") : undefined,
    twist:
      !job || settle === "sideways"
        ? undefined
        : settle !== "marudai"
          ? "free"
          : result.disk.held
            ? "keep"
            : result.disk.twists
              ? "turns"
              : "free",
  };
  return result;
}

// The strands' points, moved to where the tightening left them: sideways
// only, so every point keeps its height.
function tightened(result, job, tight) {
  const [cx, cy] = job.centre;
  result.strands.forEach((strand, a) => {
    strand.points = strand.points.map(([, , z], j) => {
      const k = a * job.n + job.chosen[j];
      return [
        round(tight.xy[2 * k] - cx),
        round(tight.xy[2 * k + 1] - cy),
        z,
      ];
    });
  });
  if (Number.isFinite(tight.closest)) {
    result.info.closest_approach = round(tight.closest);
  }
  return result;
}

// The yarns pulled clear sideways, ten rounds at a time, as tight as they
// go while every pair winds round each other as it was laid.  Tightened
// level by level, two yarns can circle each other at one level without
// touching, undoing a turn of the braid between levels; the physics would
// keep that wrong turn.  The round before a pair's winding changes by half
// a turn is kept.
function pulledClear(job) {
  const most = Math.max(job.iterations, 100);
  let clear = tightenYarns({ ...job, iterations: 0 });
  const laid = windings(clear.xy, job.n_yarns, job.n);
  for (let done = 0; done < most; done += 10) {
    const next = tightenYarns({ ...job, xy: clear.xy, iterations: 10 });
    const now = windings(next.xy, job.n_yarns, job.n);
    if (now.some((w, k) => Math.abs(w - laid[k]) > Math.PI)) break;
    clear = next;
  }
  return clear;
}

// How far each pair of yarns winds round the other from the first level to
// the last, in radians: x and y, yarn after yarn, level by level.
function windings(xy, nYarns, n) {
  const out = [];
  for (let a = 0; a < nYarns; a++) {
    for (let b = a + 1; b < nYarns; b++) {
      let total = 0;
      let last = null;
      for (let i = 0; i < n; i++) {
        const angle = Math.atan2(xy[2 * (b * n + i) + 1] - xy[2 * (a * n + i) + 1], xy[2 * (b * n + i)] - xy[2 * (a * n + i)]);
        if (last !== null) total += Math.atan2(Math.sin(angle - last), Math.cos(angle - last));
        last = angle;
      }
      out.push(total);
    }
  }
  return out;
}

// The braid settled by its own physics (rope.js): pulled clear of itself
// sideways first, then each yarn a chain of beads, clamped at the fell,
// fed at its oldest end from a bobbin pulling it back, and the braid drawn
// off by a weight lighter than the yarns' pull, so it is beaten up until
// its crossings jam.  Shown as it goes.
function settled(id, result, job) {
  // Pulled clear sideways first, far enough that no two yarns overlap when
  // seen in 3D: overlaps left for the physics to push apart could part
  // the wrong way.
  status("Pulling the yarns clear…");
  const clear = pulledClear(job);
  const d = job.yarn_diameter;
  const [cx, cy] = job.centre;
  const yarns = [];
  for (let a = 0; a < job.n_yarns; a++) {
    const points = [];
    for (let i = job.n - 1; i >= 0; i--) {
      const k = a * job.n + i;
      points.push(
        (clear.xy[2 * k] - cx) / d,
        (clear.xy[2 * k + 1] - cy) / d,
        ((job.n - 1 - i) * job.spacing) / d,
      );
    }
    yarns.push(relay(points, 0.5));
  }
  const height = ((job.n - 1) * job.spacing) / d;
  const started = performance.now();
  let shown = started;
  const rest = settleRope({
    yarns,
    spacing: 0.5,
    feed: 1,
    force: 0.25 * job.n_yarns,
    // The end plate free to turn, the braid untwists; held, its twist is kept.
    turns: job.twist !== "keep",
    stretch: 100,
    contact: 100,
    steps: 200000,
    tolerance: 1e-3,
    progress: ({ yarns: now, rise, largestForce }) => {
      status(
        `Settling by physics… ${((performance.now() - started) / 1000).toFixed(0)} s, ` +
          `${Math.round((100 * -rise) / height)}% shorter`,
      );
      if (performance.now() - shown > 700) {
        shown = performance.now();
        self.postMessage({ type: "laid", id, result: onLevels(result, now, d) });
      }
      void largestForce;
    },
  });
  const straight = unbraided(rest, height, job.twist);
  const out = onLevels(result, straight || rest.yarns, d);
  out.info.closest_approach = round((1 - rest.deepest) * d);
  out.notes = [
    ...(out.notes || []),
    `Settled by physics: beaten up from ${height.toFixed(1)} to ` +
      `${(height + rest.rise).toFixed(1)} yarn diameters long, the end turning ` +
      `${((rest.turn * 180) / Math.PI).toFixed(0)}°.`,
  ];
  if (straight) out.notes.push(UNBRAIDED);
  return out;
}

// Untwisted, a braid that was only twist — a rope, a two-ply — has nothing
// left to jam once its end has turned it out: its yarns would be drawn in
// to nothing.  They hang straight instead, side by side, touching round
// their middle, each where its end left the plate, as long as the braid
// was laid; null for a braid still braided.
function unbraided(rest, height, twist) {
  if (twist === "keep") return null;
  const tops = rest.yarns.map((y) => Math.max(...y.filter((_, k) => k % 3 === 2)));
  if (Math.max(...tops) >= 1) return null;
  const n = rest.yarns.length;
  const apart = n > 1 ? 0.5 / Math.sin(Math.PI / n) : 0;
  const rows = Math.ceil(2 * height);
  return rest.yarns.map((y) => {
    const angle = Math.atan2(y[y.length - 2], y[y.length - 3]);
    const [x, yy] = [apart * Math.cos(angle), apart * Math.sin(angle)];
    const points = [];
    for (let i = 0; i <= rows; i++) points.push(x, yy, (height * i) / rows);
    return points;
  });
}

const UNBRAIDED =
  "Untwisted: hanging free, the end turned the braid's twist out, and nothing is left braided: the yarns hang straight, side by side. The words above are the braid asked for, not what was made.";

// The braid made crossing by crossing (form.js): from its oldest row up,
// each row beaten up against the made braid, with friction, and frozen
// into it; then the whole settled by its own physics (rope.js), as above,
// from that start rather than from the braid as laid.
function formed(id, result, job) {
  status("Pulling the yarns clear…");
  const clear = pulledClear(job);
  const d = job.yarn_diameter;
  const [cx, cy] = job.centre;
  // Oldest end first, rising.
  const yarns = [];
  for (let a = 0; a < job.n_yarns; a++) {
    const points = [];
    for (let i = 0; i < job.n; i++) {
      const k = a * job.n + i;
      points.push((clear.xy[2 * k] - cx) / d, (clear.xy[2 * k + 1] - cy) / d, (i * job.spacing) / d);
    }
    yarns.push(points);
  }
  const height = ((job.n - 1) * job.spacing) / d;
  const started = performance.now();
  let shown = started;
  const show = (now) => {
    if (performance.now() - shown > 700) {
      shown = performance.now();
      self.postMessage({ type: "laid", id, result: onLevels(result, fellFirst(now), d) });
    }
  };
  const made = formBraid({
    yarns,
    // As braidpy lays a disk braid: a row every one and a half diameters.
    row: 1.5,
    friction: 0.3,
    feed: 1,
    weight: 0.25 * job.n_yarns,
    progress: ({ fraction, yarns: now }) => {
      status(
        `Making it crossing by crossing… ${Math.round(100 * fraction)}%, ` +
          `${((performance.now() - started) / 1000).toFixed(0)} s`,
      );
      show(now);
    },
  });
  const madeHeight = Math.max(...made.yarns.map((y) => y[y.length - 1]));
  const rest = settleRope({
    yarns: made.yarns,
    spacing: 0.5,
    feed: 1,
    force: 0.25 * job.n_yarns,
    // The end plate free to turn, the braid untwists; held, its twist is kept.
    turns: job.twist !== "keep",
    stretch: 100,
    contact: 100,
    steps: 200000,
    tolerance: 1e-3,
    progress: ({ yarns: now }) => {
      status(`Settling it… ${((performance.now() - started) / 1000).toFixed(0)} s`);
      show(now);
    },
  });
  const straight = unbraided(rest, height, job.twist);
  const out = onLevels(result, straight || fellFirst(rest.yarns), d);
  out.info.closest_approach = round((1 - rest.deepest) * d);
  out.notes = [
    ...(out.notes || []),
    `Made crossing by crossing, with friction: beaten up from ${height.toFixed(1)} to ` +
      `${madeHeight.toFixed(1)} yarn diameters long; then settled to ` +
      `${(madeHeight + rest.rise).toFixed(1)}, the end turning ` +
      `${((rest.turn * 180) / Math.PI).toFixed(0)}°.`,
  ];
  if (straight) out.notes.push(UNBRAIDED);
  return out;
}

// The braid made move by move as on a marudai (marudai.js): the disk's own
// moves, each moved yarn laid over the others to its new carrier and drawn
// tight, the braid relaxing and turning to balance after each step.
//
// The marudai is kept between braids.  Asked for one whose moves begin
// with those already made — the same braid, more of it — it makes only the
// moves still to come.  It looks every few hundredths of a second whether
// it is asked for another braid: if so, it leaves this one where it is,
// to go on with should the other begin as this one does.  Returns null
// when left so.
async function onMarudai(id, result, job) {
  const d = job.yarn_diameter;
  const started = performance.now();
  let shown = started;
  // Kept, the braid is held throughout, its twist kept; untwisted, it
  // hangs free throughout, and turning the bobbins together turns it along.
  const twist = job.twist ?? "auto";
  const holding = {
    keep: { held: true, twists: true },
    turns: { held: false, twists: true },
    free: { held: false, twists: false },
  }[twist] ?? {};
  const program = { ...result.disk, ...holding };
  const same = JSON.stringify({ ...program, steps: undefined, d });
  const goesOn =
    onDisk &&
    onDisk.same === same &&
    onDisk.done <= program.steps.length &&
    JSON.stringify(program.steps.slice(0, onDisk.done)) === onDisk.made;
  if (!goesOn) {
    const making = beginOnMarudai(program);
    // Grow starts from the yarns as they are laid out, before any move.
    onDisk = { same, done: 0, made: "[]", frames: [kept(making.look())], mirror: null, making };
  }
  const from = onDisk.done;
  const making = onDisk.making;
  // Each moment of the making, kept for Grow to replay, and shown as it
  // comes, a few times a second; the mirror as the first moments have it.
  making.hooks.total = program.steps.length;
  making.hooks.watch = (frame) => {
    // Which yarns this move has carried so far, for the top view to show
    // them on their way while the others wait; once settled, all of them.
    if (onDisk.moving?.step !== frame.step) onDisk.moving = { step: frame.step, threads: [] };
    const moving = onDisk.moving;
    if (frame.what === "carried" && !moving.threads.includes(frame.thread)) moving.threads.push(frame.thread);
    frame.moved = frame.what === "settled" || frame.what === "turned" ? null : [...moving.threads];
    onDisk.frames.push(kept(frame));
    if (performance.now() - shown < 80) return;
    shown = performance.now();
    if (!onDisk.mirror) {
      const ends = frame.yarns.filter((y) => y.length).map((y) => [y[y.length - 3], y[y.length - 2], y[y.length - 1]]);
      onDisk.mirror = mirrorOf(
        {
          rim: {
            radius: ends.reduce((s, [x, y]) => s + Math.hypot(x, y), 0) / ends.length,
            height: ends.reduce((s, [, , z]) => s + z, 0) / ends.length,
          },
          tip: frame.tip,
        },
        d,
      );
    }
    const mirror = onDisk.mirror;
    const disk = { z: round(-mirror.above), radius: round(mirror.radius), hole: round(mirror.hole) };
    self.postMessage({ type: "frame", id, frame: pageFrame(frame, d, mirror), disk, colours: result.strands.map((s) => s.colour) });
  };
  making.hooks.progress = ({ fraction }) => {
    status(
      (from ? `Making more of it, from move ${from}… ` : "Making it move by move… ") +
        `${Math.round(100 * fraction)}%, ${((performance.now() - started) / 1000).toFixed(0)} s`,
    );
  };
  let looked = performance.now();
  for (let k = from; k < program.steps.length; k++) {
    making.step(program.steps[k], k);
    onDisk.done = k + 1;
    onDisk.made = JSON.stringify(program.steps.slice(0, k + 1));
    if (performance.now() - looked > 50) {
      await new Promise((resolve) => setTimeout(resolve, 0));
      looked = performance.now();
      if (asked) return null;
    }
  }
  making.hooks.watch = making.hooks.progress = null;
  const made = making.result();
  // Nothing braided — untwisted, a rope's turns only carried the braid
  // round — the yarns hang straight down from where they leave the mirror,
  // side by side, as long as the braid was laid.
  let yarns = made.yarns;
  if (!(made.tip >= 1)) {
    const zs = result.strands.flatMap((s) => s.points.map((p) => p[2]));
    const long = Math.max(2, (Math.max(...zs) - Math.min(...zs)) / d);
    const rows = Math.ceil(2 * long);
    // Touching, round their middle, each on the side its tail leaves for.
    const n = made.tails.length;
    const apart = n > 1 ? 0.5 / Math.sin(Math.PI / n) : 0;
    yarns = made.tails.map((tail, k) => {
      const angle =
        tail.length >= 6 ? Math.atan2(tail[tail.length - 2], tail[tail.length - 3]) : (2 * Math.PI * k) / n;
      const [x, y] = [apart * Math.cos(angle), apart * Math.sin(angle)];
      const points = [];
      for (let i = 0; i <= rows; i++) points.push(x, y, made.tip - long + (long * i) / rows);
      return points;
    });
  }
  const out = onLevels(result, upsideDown(yarns), d);
  // Kept to a few hundred moments: Grow replays them in twelve seconds.
  const frames = onDisk.frames;
  const every = Math.max(1, Math.ceil(frames.length / 600));
  const shownFrames = frames.filter((_, i) => i % every === 0 || i === frames.length - 1);
  out.marudai = onMarudaiFrame(made, d, shownFrames, making.look());
  out.notes = [
    ...(out.notes || []),
    `Made move by move, as on a marudai: ${made.tip.toFixed(1)} yarn diameters long.`,
  ];
  // Every bobbin turning together, the braid hanging free: it turns along,
  // and what those turns would have twisted in is not there.
  const n = result.disk.start.length;
  const turns = result.disk.steps.some(
    (step) => step.length === n && step.every(([, d]) => d && d === step[0][1]),
  );
  // (A disk braid's own turns carry the braid round anyway, as a disk does.)
  if (from) out.notes.push(`Made on from where it was left, after ${from} of its ${program.steps.length} moves.`);
  if (twist === "free" && turns && result.disk.twists) {
    out.notes.push(
      made.tip < 1
        ? "Untwisted: hanging free, the braid turned along with the bobbins, and nothing braided: the yarns hang straight, side by side. The words above are the word asked for, not what was made."
        : "Untwisted: hanging free, the braid turned along with the bobbins, so their turns twisted nothing in. It is no longer the braid its word says: the words above are the word asked for.",
    );
  }
  return out;
}

// The yarns' tails above the fell, and the marudai's mirror they lie over,
// in the page's units, turned upside down as the braid is (upsideDown,
// fellFirst): the fell at height 0.  The tails come up from the fell to the
// hole in the mirror, where marudai.js pulls them; from there they lie flat
// across the mirror to its edge, and drop over it towards their bobbins,
// as on a real marudai.  A yarn being carried over the others to its new
// place is still above the mirror: it lies across at its own height.
const MIRROR = 2.5; // the mirror's radius, in its hole's
function mirrorOf(made, d) {
  return {
    hole: 0.97 * made.rim.radius * d,
    radius: MIRROR * made.rim.radius * d,
    // How far above the fell the mirror is, as the yarns' ends are.
    above: (made.rim.height - made.tip) * d,
    drop: 0.4 * made.rim.radius * d,
  };
}

// One yarn, flat [x, y, z, …] as marudai.js gives it, in the page's frame,
// the fell (``tip``) at height 0, and on across the mirror and over its edge.
function onMirror(yarn, tip, d, mirror) {
  const out = [];
  for (let i = 0; i < yarn.length; i += 3) out.push([yarn[i] * d, -yarn[i + 1] * d, (tip - yarn[i + 2]) * d]);
  // While the yarns are first laid out, those still to come have nothing.
  if (!out.length) return out;
  const [x, y, z] = out[out.length - 1];
  const r = Math.hypot(x, y) || 1;
  const ux = x / r, uy = y / r;
  const level = Math.min(-mirror.above, z);
  const at = (radius, height) => [ux * radius, uy * radius, height];
  out.push(
    at(Math.max(r, mirror.hole) + 0.5 * d, level),
    at(mirror.radius, level),
    at(1.02 * mirror.radius, -mirror.above + 0.3 * mirror.drop),
    at(1.03 * mirror.radius, -mirror.above + mirror.drop),
  );
  return out;
}

// The moments of the making kept for Grow (kept, onMarudaiFrame), in the
// page's frame, each only as much as it needs: the beads still free, the
// frozen ones being as the braid ends them (base), turned back to where
// they were and raised with the fell.  Grow puts each moment back together
// as it shows it (frames.js).
function onMarudaiFrame(made, d, frames, end) {
  let top = -Infinity;
  for (const y of made.yarns) for (let i = 2; i < y.length; i += 3) top = Math.max(top, y[i]);
  const mirror = mirrorOf(made, d);
  // Frozen in no moment, a bead is not needed as the braid ends it.
  const needed = end.yarns.map((_, t) => Math.max(0, ...frames.map((f) => f.frozen[t])));
  const [endAngle, endX, endY] = end.placed;
  return {
    tails: made.tails.map((tail) => onMirror(tail, top, d, mirror).map((p) => p.map(round))),
    disk: { z: round(-mirror.above), radius: round(mirror.radius), hole: round(mirror.hole) },
    base: end.yarns.map((yarn, t) => {
      const out = new Float32Array(3 * needed[t]);
      for (let i = 0; i < out.length; i += 3) {
        out[i] = yarn[i] * d;
        out[i + 1] = -yarn[i + 1] * d;
        out[i + 2] = (end.tip - yarn[i + 2]) * d;
      }
      return out;
    }),
    frames: frames.map((frame) => {
      // The braid's turn from its end back to this moment: placed, undone
      // to the end's and done again to this one's (marudai.js's turn).
      const angle = frame.placed[0] - endAngle;
      const c = Math.cos(angle), s = Math.sin(angle);
      const [ex, ey] = [endX * d, -endY * d];
      const [fx, fy] = [frame.placed[1] * d, -frame.placed[2] * d];
      return {
        ...pageFrame(frame, d, mirror),
        frozen: frame.frozen,
        turn: [c, s, fx - (c * ex + s * ey), fy - (-s * ex + c * ey)],
        lift: (frame.tip - end.tip) * d,
      };
    }),
  };
}

// A moment of the making as kept for Grow: of each yarn, only its beads
// not yet frozen — the frozen ones are put back from the braid as it ends.
function kept(frame) {
  return { ...frame, yarns: frame.yarns.map((yarn, t) => yarn.slice(3 * frame.frozen[t])) };
}

// A moment in the making, for the page to draw: every yarn whole, in the
// page's frame, its fell at height 0.
function pageFrame(frame, d, mirror) {
  return {
    what: frame.what,
    thread: frame.thread,
    step: frame.step,
    moved: frame.moved,
    yarns: frame.yarns.map((yarn) => Float32Array.from(onMirror(yarn, frame.tip, d, mirror).flat())),
  };
}

// A braid made as on a marudai, its fell on top, turned upside down for
// the page, which draws the fell at the bottom: newest end first, the fell
// at height 0.  Turned over, not reflected — y changes sign with z — so it
// stays the braid it is, not its mirror image.
function upsideDown(yarns) {
  return fellFirst(yarns.map((y) => y.map((v, k) => (k % 3 === 1 ? -v : v))));
}

// Yarns turned over, newest end first, the fell at height 0: as rope.js
// gives them, for onLevels.
function fellFirst(yarns) {
  const top = Math.max(...yarns.map((y) => Math.max(...y.filter((_, k) => k % 3 === 2))));
  return yarns.map((y) => {
    const out = [];
    for (let i = y.length - 3; i >= 0; i -= 3) out.push(y[i], y[i + 1], top - y[i + 2]);
    return out;
  });
}

// Each yarn at the heights the page draws it at, highest first — its
// heights scaled to the settled braid's length.
function onLevels(result, yarns, d) {
  const out = structuredClone(result);
  const top = Math.max(...yarns.map((y) => y[y.length - 1]));
  out.strands.forEach((strand, a) => {
    const y = yarns[a];
    const laidTop = strand.points[0][2] || 1;
    strand.points = strand.points.map(([, , z]) => {
      const want = (z / laidTop) * top;
      // Where the yarn, going up, first comes to that height.
      for (let i = 3; i < y.length; i += 3) {
        if (y[i + 2] >= want) {
          const f = (want - y[i - 1]) / (y[i + 2] - y[i - 1] || 1);
          return [
            round((y[i - 3] + f * (y[i] - y[i - 3])) * d),
            round((y[i - 2] + f * (y[i + 1] - y[i - 2])) * d),
            round(want * d),
          ];
        }
      }
      return [round(y[y.length - 3] * d), round(y[y.length - 2] * d), round(want * d)];
    });
  });
  return out;
}

// A yarn's points again, evenly spaced, as rope.js wants them.
function relay(points, spacing) {
  return Array.from(self.yarnMechanics.relay(Float64Array.from(points), spacing));
}

function round(value) {
  return Math.round(value * 1e4) / 1e4;
}

