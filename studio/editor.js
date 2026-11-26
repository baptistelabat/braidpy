// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A disk or a sinnet's moves, typed in or clicked on a drawing of the disk.
// The drawing shows the moves made up to a cursor: the last of them, unless
// stepped back and forth with the buttons, as a machine's handle is turned
// (machine.js), or put on a move by the caret in the moves typed.  Stepping
// changes no move; a move clicked goes in after the cursor, and Undo takes
// out the one at it.

import { inTime } from "./page.js?v=746e23d191";

function hue(i, n) {
  return `hsl(${(360 * i) / Math.max(n, 1)}, 100%, 50%)`;
}

function pairs(text) {
  return spans(text).map(({ move }) => move);
}

// Each move typed, and where it is in the text: from its first number to
// the end of its second.
function spans(text) {
  const numbers = [...String(text).matchAll(/\d+/g)];
  const out = [];
  for (let i = 0; i + 1 < numbers.length; i += 2) {
    const [a, b] = [numbers[i], numbers[i + 1]];
    out.push({ move: [Number(a[0]), Number(b[0])], start: a.index, end: b.index + b[0].length });
  }
  return out;
}

export function attachEditor(source, holder) {
  const moves = holder.querySelector("[name=moves]");
  const label = moves.closest("label");
  const box = document.createElement("div");
  box.className = "editor";
  box.dataset.custom = "";
  box.hidden = label.hidden;
  const canvas = document.createElement("canvas");
  canvas.setAttribute(
    "aria-label",
    source === "mobidai"
      ? "The disk: click a strand, then the slot it goes to"
      : "The spaces: click a space to move from, then one to move to",
  );
  const help = document.createElement("small");
  const undo = document.createElement("button");
  undo.type = "button";
  undo.textContent = "Undo move";
  const clear = document.createElement("button");
  clear.type = "button";
  clear.textContent = "Clear moves";
  const buttons = document.createElement("div");
  buttons.className = "examples";
  buttons.append(undo, clear);
  const button = (text, title) => {
    const made = document.createElement("button");
    made.type = "button";
    made.textContent = text;
    made.title = title;
    return made;
  };
  const first = button("⏮", "Before the first move");
  const back = button("◀", "A move back");
  const forward = button("▶", "A move on");
  const end = button("⏭", "After the last move");
  const reading = document.createElement("span");
  reading.className = "step";
  const stepper = document.createElement("div");
  stepper.className = "examples handle";
  stepper.append(first, back, forward, end, reading);
  box.append(canvas, help, stepper, buttons);
  label.after(box);

  let chosen = null;
  // How many moves are made where the drawing is; null, all of them.
  let cursor = null;
  const count = () => pairs(moves.value).length;
  const made = () => Math.min(cursor ?? Infinity, count());
  // Moves changed here are changed as if typed: the braid becomes your own.
  const changed = () => {
    chosen = null;
    moves.dispatchEvent(new Event("input", { bubbles: true }));
  };
  // A move clicked goes in after the cursor, the moves after it kept.
  const add = (from, to) => {
    const at = made();
    const typed = spans(moves.value);
    if (at >= typed.length) {
      const list = moves.value.trim();
      moves.value = (list ? list + ", " : "") + `${from}>${to}`;
    } else {
      const where = at ? typed[at - 1].end : typed[0].start;
      const text = at ? `, ${from}>${to}` : `${from}>${to}, `;
      moves.value = moves.value.slice(0, where) + text + moves.value.slice(where);
    }
    if (cursor !== null) cursor = at + 1;
    changed();
  };
  undo.addEventListener("click", () => {
    const at = made();
    if (!at) return;
    const list = pairs(moves.value);
    list.splice(at - 1, 1);
    moves.value = list.map(([a, b]) => `${a}>${b}`).join(", ");
    if (cursor !== null) cursor = at - 1;
    changed();
  });
  clear.addEventListener("click", () => {
    moves.value = "";
    cursor = null;
    changed();
  });

  // Stepped to a move: it is drawn made, the last, and picked out in the
  // moves typed.  Past the last, the drawing follows the moves as they grow.
  function stepTo(at) {
    const n = count();
    cursor = Math.max(0, Math.min(at, n));
    if (cursor === n) cursor = null;
    chosen = null;
    const typed = spans(moves.value);
    const shown = made();
    if (document.activeElement !== moves) moves.focus({ preventScroll: true });
    if (shown) moves.setSelectionRange(typed[shown - 1].start, typed[shown - 1].end);
    else moves.setSelectionRange(0, 0);
    draw();
  }
  first.addEventListener("click", (event) => inTime(event) && stepTo(0));
  back.addEventListener("click", (event) => inTime(event) && stepTo(made() - 1));
  forward.addEventListener("click", (event) => inTime(event) && stepTo(made() + 1));
  end.addEventListener("click", (event) => inTime(event) && stepTo(count()));
  // The caret on a move, or just after it, puts the cursor there; a move
  // selected, as stepping selects it, too.
  function fromCaret() {
    const caret = moves.selectionEnd;
    const before = spans(moves.value).filter(({ start }) => start < caret).length;
    const atEnd = !moves.value.slice(caret).match(/\d/);
    cursor = atEnd ? null : before;
    draw();
  }
  for (const heard of ["click", "keyup", "select"]) moves.addEventListener(heard, fromCaret);

  // What there is to draw and click: places round a circle, and who is
  // where once the moves up to the cursor are made.
  function state() {
    const upTo = pairs(moves.value).slice(0, made());
    if (source === "mobidai") {
      const n = Math.max(3, Number(holder.querySelector("[name=n_slots]").value) || 32);
      const start = (holder.querySelector("[name=slots]").value.match(/\d+/g) || []).map(Number);
      const at = new Map(start.map((slot, i) => [slot, i]));
      for (const [from, to] of upTo) {
        if (!at.has(from) || at.has(to)) continue;
        at.set(to, at.get(from));
        at.delete(from);
      }
      return { n, at, strands: start.length };
    }
    const counts = (holder.querySelector("[name=counts]").value.match(/\d+/g) || []).map(Number);
    const groups = [];
    let next = 0;
    for (const count of counts) {
      groups.push(Array.from({ length: count }, () => next++));
    }
    for (const [from, to] of upTo) {
      const leaving = groups[from - 1];
      const joining = groups[to - 1];
      if (!leaving || !joining || !leaving.length || from === to) continue;
      const mover = from % 2 ? leaving.pop() : leaving.shift();
      if (to % 2) joining.unshift(mover);
      else joining.push(mover);
    }
    return { n: counts.length, groups, strands: next };
  }

  // Where a place is on the canvas: a disk's slots clockwise from the top,
  // half a slot round, as the page draws it; a sinnet's spaces
  // anticlockwise from the top, the first and the last meeting there, as
  // the top view shows them.
  function place(index, n, size, fraction = 0.5) {
    const turn =
      source === "mobidai"
        ? -Math.PI / 2 + (2 * Math.PI * (index - 1 + fraction)) / n
        : -Math.PI / 2 - (2 * Math.PI * (index - 1 + fraction)) / n;
    return [Math.cos(turn), Math.sin(turn)];
  }

  function draw() {
    // Gone with its fields, when another source was chosen.
    if (!canvas.isConnected) return observer.disconnect();
    const ratio = Math.min(window.devicePixelRatio || 1, 2);
    const size = canvas.clientWidth || 260;
    canvas.width = canvas.height = Math.round(size * ratio);
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    ctx.clearRect(0, 0, size, size);
    const style = getComputedStyle(document.documentElement);
    const muted = style.getPropertyValue("--muted").trim();
    const accent = style.getPropertyValue("--accent").trim();
    const c = size / 2;
    const r = size / 2 - 22;
    const view = state();
    ctx.strokeStyle = muted;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(c, c, r, 0, 2 * Math.PI);
    ctx.stroke();
    ctx.font = "10px system-ui, sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    if (source === "mobidai") {
      const every = Math.max(1, Math.ceil(view.n / 16));
      for (let slot = 1; slot <= view.n; slot++) {
        const [x, y] = place(slot, view.n, size);
        ctx.fillStyle = muted;
        ctx.beginPath();
        ctx.arc(c + r * x, c + r * y, 2, 0, 2 * Math.PI);
        ctx.fill();
        if ((slot - 1) % every === 0) ctx.fillText(slot, c + (r + 12) * x, c + (r + 12) * y);
      }
      for (const [slot, strand] of view.at) {
        const [x, y] = place(slot, view.n, size);
        ctx.fillStyle = hue(strand, view.strands);
        ctx.beginPath();
        ctx.arc(c + r * x, c + r * y, slot === chosen ? 8 : 5.5, 0, 2 * Math.PI);
        ctx.fill();
        if (slot === chosen) {
          ctx.strokeStyle = accent;
          ctx.lineWidth = 2;
          ctx.stroke();
        }
      }
    } else {
      for (let space = 1; space <= view.n; space++) {
        const [x0, y0] = place(space, view.n, size, 0);
        ctx.strokeStyle = muted;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(c + (r - 26) * x0, c + (r - 26) * y0);
        ctx.lineTo(c + (r + 4) * x0, c + (r + 4) * y0);
        ctx.stroke();
        const [lx, ly] = place(space, view.n, size);
        ctx.fillStyle = space === chosen ? accent : muted;
        ctx.font = space === chosen ? "bold 12px system-ui, sans-serif" : "11px system-ui, sans-serif";
        ctx.fillText(space, c + (r + 13) * lx, c + (r + 13) * ly);
        const group = view.groups[space - 1];
        group.forEach((strand, i) => {
          const fraction = 0.15 + (0.7 * (i + 0.5)) / group.length;
          const [x, y] = place(space, view.n, size, fraction);
          ctx.fillStyle = hue(strand, view.strands);
          ctx.beginPath();
          ctx.arc(c + (r - 12) * x, c + (r - 12) * y, 5, 0, 2 * Math.PI);
          ctx.fill();
        });
      }
    }
    // The last move made, from where the strand left to where it went.
    const shown = made();
    const last = shown ? pairs(moves.value)[shown - 1] : null;
    if (last && chosen === null) {
      const reach = source === "mobidai" ? r - 9 : r - 22;
      const at = (where) => {
        const [x, y] = place(where, view.n, size);
        return [c + reach * x, c + reach * y];
      };
      const [x0, y0] = at(last[0]);
      const [x1, y1] = at(last[1]);
      const bend = 0.35;
      const [mx, my] = [c + (x0 + x1 - 2 * c) * bend, c + (y0 + y1 - 2 * c) * bend];
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.quadraticCurveTo(mx, my, x1, y1);
      ctx.stroke();
      const angle = Math.atan2(y1 - my, x1 - mx);
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x1 - 9 * Math.cos(angle - 0.4), y1 - 9 * Math.sin(angle - 0.4));
      ctx.lineTo(x1 - 9 * Math.cos(angle + 0.4), y1 - 9 * Math.sin(angle + 0.4));
      ctx.closePath();
      ctx.fill();
    }
    const n = count();
    reading.textContent = n ? `Move ${shown} of ${n}${last ? `: ${last[0]}>${last[1]}` : ""}` : "";
    first.disabled = back.disabled = !shown;
    forward.disabled = end.disabled = shown >= n;
    help.textContent =
      chosen === null
        ? source === "mobidai"
          ? `Click a strand, then the slot it goes to${shown < n ? `: it goes in after move ${shown}` : ""}.`
          : `Click the space a strand leaves, then the one it goes to${shown < n ? `: it goes in after move ${shown}` : ""}.`
        : source === "mobidai"
          ? `Now the slot strand at ${chosen} goes to.`
          : `Now the space it goes to, from space ${chosen}.`;
  }

  canvas.addEventListener("click", (event) => {
    const box = canvas.getBoundingClientRect();
    const size = box.width;
    const x = event.clientX - box.left - size / 2;
    const y = event.clientY - box.top - size / 2;
    const view = state();
    if (source === "mobidai") {
      // The nearest slot to where the click was.
      const angle = Math.atan2(y, x);
      const slot =
        ((Math.round(((angle + Math.PI / 2) * view.n) / (2 * Math.PI) - 0.5) % view.n) + view.n) %
          view.n +
        1;
      if (view.at.has(slot)) chosen = slot;
      else if (chosen !== null) return add(chosen, slot);
    } else {
      // Anticlockwise from the top, in the plane with y up.
      const angle = Math.atan2(-y, x);
      const round = (((angle - Math.PI / 2) % (2 * Math.PI)) + 2 * Math.PI) % (2 * Math.PI);
      const space = (Math.floor((round * view.n) / (2 * Math.PI)) % view.n) + 1;
      if (chosen === null) {
        if (view.groups[space - 1].length) chosen = space;
      } else if (space === chosen) {
        chosen = null;
      } else {
        return add(chosen, space);
      }
    }
    draw();
  });
  for (const input of holder.querySelectorAll("input, textarea")) {
    input.addEventListener("input", draw);
  }
  holder.querySelector("select[name=name]").addEventListener("change", () => {
    chosen = null;
    cursor = null;
    requestAnimationFrame(draw);
  });
  const observer = new ResizeObserver(draw);
  observer.observe(canvas);
  draw();
}

// A sinnet made from a shape, drawn as Ashley draws it once braidpy has
// made it (braidpy.web's ashley_shape): its grid's cells, its lines,
// coloured by track, each with an arrow the way its move goes, and its
// spaces, numbered, sized by the strands they start with.  As chosen,
// clicking a track turns it round; clicking a space gives it a strand
// more, shift-clicking takes one off; clicking a cell adds it to the shape
// or takes it off.  The braid is made again.
const SVG = "http://www.w3.org/2000/svg";
// Margin round the shape, and the radius of a space with one strand, in
// the drawing's spacings between lines.
const SHAPE_MARGIN = 0.8;
const SPACE_RADIUS = 0.28;
// An arrow's length, in spacings, its width a share of it, and how far
// along its line it points.
const ARROW = 0.35;
const ARROW_WIDTH = 0.5;
const ARROW_AT = 0.55;
// Widths of a line, of the wider line unseen round it that takes a click,
// and of the outline and the spaces' rims, in spacings.
const LINE_WIDTH = 0.08;
const CLICK_WIDTH = 0.4;
const RIM_WIDTH = 0.04;
// The outline, faint beside the lines, and the grid's cells fainter still.
const OUTLINE_OPACITY = 0.4;
const CELL_OPACITY = 0.12;
// What a click on a shape's drawing does.
const CLICKS = [
  ["tracks", "Click a track to turn it round"],
  ["strands", "Click a space for a strand more, shift-click for one less"],
  ["shape", "Click a cell to add it or take it off"],
];
// A space's number, as a share of the radius of a space of one strand.
const NUMBER_SIZE = 1.3;

function svg(name, attributes = {}) {
  const element = document.createElementNS(SVG, name);
  for (const [key, value] of Object.entries(attributes)) element.setAttribute(key, value);
  return element;
}

export function attachShape(holder) {
  const turned = holder.querySelector("[name=turned]");
  const extra = holder.querySelector("[name=extra]");
  const cells = holder.querySelector("[name=cells]");
  const box = document.createElement("div");
  box.className = "editor";
  // What a click does: its own control, no part of the braid asked for.
  const mode = document.createElement("select");
  mode.setAttribute("aria-label", "A click on the drawing");
  for (const [value, text] of CLICKS) mode.append(new Option(text, value));
  const drawing = svg("svg", { role: "img" });
  drawing.setAttribute("aria-label", "The shape, its tracks and spaces, and its grid");
  drawing.style.width = "100%";
  const help = document.createElement("small");
  help.textContent = "Made, the shape is drawn here.";
  box.append(mode, drawing, help);
  holder.querySelector("[name=shape]").closest("label").after(box);
  // A shape started from afresh, or resized, is no longer the cells changed.
  for (const name of ["grid", "shape", "size", "height"]) {
    holder.querySelector(`[name=${name}]`).addEventListener("change", () => {
      cells.value = "";
      turned.value = "";
      extra.value = "";
    });
  }
  let last = null;
  mode.addEventListener("change", () => last && draw(last));

  const again = () => document.getElementById("build").click();
  const listed = (field) => (field.value.match(/\d+/g) || []).map(Number);
  const toggle = (track) => {
    const now = listed(turned);
    turned.value = (now.includes(track) ? now.filter((t) => t !== track) : [...now, track])
      .sort((a, b) => a - b)
      .join(" ");
    again();
  };
  const give = (space, more) => {
    const now = listed(extra);
    if (more) now.push(space);
    else if (now.includes(space)) now.splice(now.indexOf(space), 1);
    else return;
    extra.value = now.sort((a, b) => a - b).join(" ");
    again();
  };

  // A cell clicked comes in, or goes out: the cells written out whole, the
  // tracks and strands, numbered on the shape as it was, forgotten.
  const reshape = (cell, shape) => {
    const now = shape.cells.filter((c) => c.in).map((c) => c.name);
    cells.value = (now.includes(cell.name) ? now.filter((n) => n !== cell.name) : [...now, cell.name]).join(" ");
    turned.value = "";
    extra.value = "";
    again();
  };

  function draw(shape) {
    last = shape;
    const clicking = mode.value;
    drawing.replaceChildren();
    const shown = mode.value === "shape" ? shape.cells.flatMap((c) => c.points) : [];
    const xs = [...shape.outline, ...shown].map(([x]) => x);
    const ys = [...shape.outline, ...shown].map(([, y]) => y);
    const [left, right] = [Math.min(...xs) - SHAPE_MARGIN, Math.max(...xs) + SHAPE_MARGIN];
    const [low, high] = [Math.min(...ys) - SHAPE_MARGIN, Math.max(...ys) + SHAPE_MARGIN];
    drawing.setAttribute("viewBox", `${left} ${-high} ${right - left} ${high - low}`);
    // Drawn with y up, as the book draws it.
    const flip = ([x, y]) => [x, -y];
    for (const cell of shape.cells) {
      const area = svg("polygon", {
        points: cell.points.map((p) => flip(p).join(",")).join(" "),
        fill: cell.in ? "currentColor" : "transparent",
        "fill-opacity": cell.in ? CELL_OPACITY : 0,
        stroke: "currentColor",
        "stroke-opacity": cell.in ? CELL_OPACITY : OUTLINE_OPACITY,
        "stroke-width": RIM_WIDTH / 2,
        "stroke-dasharray": cell.in ? "" : `${RIM_WIDTH * 2}`,
      });
      if (clicking === "shape") {
        area.style.cursor = "pointer";
        const title = svg("title");
        title.textContent = cell.in ? "Click to take this cell off" : "Click to add this cell";
        area.append(title);
        area.addEventListener("click", () => reshape(cell, shape));
      } else if (!cell.in) {
        continue;
      }
      drawing.append(area);
    }
    for (const loop of [shape.outline, ...(shape.holes || [])]) {
      drawing.append(
        svg("polygon", {
          points: loop.map((p) => flip(p).join(",")).join(" "),
          fill: "none",
          stroke: "currentColor",
          "stroke-opacity": OUTLINE_OPACITY,
          "stroke-width": RIM_WIDTH,
        }),
      );
    }
    for (const line of shape.lines) {
      const colour = hue(line.track - 1, shape.tracks);
      const [a, b] = [flip(line.start), flip(line.end)];
      const group = svg("g", clicking === "tracks" ? { cursor: "pointer" } : { "pointer-events": "none" });
      const title = svg("title");
      title.textContent = `Track ${line.track}: click to turn it round`;
      group.append(title);
      group.append(
        svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: colour, "stroke-width": LINE_WIDTH }),
        // A wider line, unseen, easier to click.
        svg("line", { x1: a[0], y1: a[1], x2: b[0], y2: b[1], stroke: "transparent", "stroke-width": CLICK_WIDTH }),
      );
      const length = Math.hypot(b[0] - a[0], b[1] - a[1]);
      const [ux, uy] = [(b[0] - a[0]) / length, (b[1] - a[1]) / length];
      const tip = [a[0] + ux * length * ARROW_AT, a[1] + uy * length * ARROW_AT];
      const back = [tip[0] - ux * ARROW, tip[1] - uy * ARROW];
      const side = [-uy * ARROW * ARROW_WIDTH, ux * ARROW * ARROW_WIDTH];
      group.append(
        svg("polygon", {
          points: [tip, [back[0] + side[0], back[1] + side[1]], [back[0] - side[0], back[1] - side[1]]]
            .map((p) => p.join(","))
            .join(" "),
          fill: colour,
        }),
      );
      if (clicking === "tracks") group.addEventListener("click", () => toggle(line.track));
      drawing.append(group);
    }
    shape.spaces.forEach((point, k) => {
      const [x, y] = flip(point);
      const strands = shape.counts[k];
      const group = svg("g", clicking === "strands" ? { cursor: "pointer" } : { "pointer-events": "none" });
      const title = svg("title");
      title.textContent = `Space ${k + 1}: ${strands} strand${strands === 1 ? "" : "s"}; click for one more, shift-click for one less`;
      group.append(
        title,
        svg("circle", {
          cx: x,
          cy: y,
          r: SPACE_RADIUS * Math.sqrt(strands),
          style: "fill: var(--panel)",
          stroke: "currentColor",
          "stroke-width": RIM_WIDTH,
        }),
      );
      const number = svg("text", {
        x,
        y,
        "font-size": SPACE_RADIUS * NUMBER_SIZE,
        "text-anchor": "middle",
        "dominant-baseline": "central",
        fill: "currentColor",
      });
      number.textContent = String(k + 1);
      group.append(number);
      if (clicking === "strands") group.addEventListener("click", (event) => give(k + 1, !event.shiftKey));
      drawing.append(group);
    });
    help.textContent = `${shape.tracks} track${shape.tracks === 1 ? "" : "s"}, ${shape.spaces.length} spaces, ${shape.counts.reduce((a, b) => a + b, 0)} strands.`;
  }

  document.addEventListener("braid-laid", ({ detail }) => {
    if (detail?.ashley_shape && holder.isConnected) draw(detail.ashley_shape);
  });
}
