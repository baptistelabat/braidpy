// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

import { PALETTE, strandColour } from "./colours.js?v=118df43990";

// A braid word drawn as it is typed, before it is made: flat, or round a
// ring.


// braidpy.web.parse_word, in JavaScript: 1 -2, s1 s2^-1 or aB.
function parseWord(text) {
  text = text.trim();
  if (!text) return [];
  if (/^[A-Za-z]+$/.test(text) && !/[sσ]\d/.test(text)) {
    return [...text].map((c) =>
      c === c.toLowerCase() ? c.charCodeAt(0) - 96 : -(c.charCodeAt(0) - 64),
    );
  }
  const word = [];
  for (const token of text.split(/[\s,;.]+/)) {
    if (!token) continue;
    if (/^[+-]?\d+$/.test(token)) {
      word.push(Number(token));
      continue;
    }
    const named = token.match(/^[sσ](\d+)(\^?\(?(-?1)\)?)?$/);
    if (!named) throw new Error(`Cannot read “${token}” as a generator.`);
    word.push(named[3] === "-1" ? -Number(named[1]) : Number(named[1]));
  }
  if (word.some((g) => g === 0)) throw new Error("Generators are numbered from 1.");
  return word;
}

// A ring word reads the strands round a circle, as on a marudai: past the
// braid word's crossings, n crosses the last strand and the first, across
// the seam, and n + 1 turns every strand one place round.
const WORD_HINTS = {
  row: ["Braid word", "Signed generators — 1 -2 — or s1 s2^-1, or letters, aB."],
  ring: [
    "Ring word",
    "As a braid word, round a ring of n strands: n crosses the last strand and the first, across the seam; n + 1 turns every strand one place round. Drawn on a cylinder cut at the seam.",
  ],
};

export function attachDiagram(holder) {
  const wordField = holder.querySelector("[name=word]");
  const strandsField = holder.querySelector("[name=n_strands]");
  const layoutField = holder.querySelector("[name=layout]");
  const wordLabel = wordField.closest("label");
  const named = () => {
    const [title, hint] = WORD_HINTS[layoutField.value] || WORD_HINTS.row;
    wordLabel.querySelector("span").textContent = title;
    wordLabel.querySelector("small").textContent = hint;
  };
  layoutField.addEventListener("change", () => {
    named();
    draw();
  });
  document.addEventListener("strand-colours", () => draw());
  named();
  const figure = document.createElement("div");
  figure.className = "diagram";
  // However long the word, rows stay readable: the drawing scrolls.
  const scroller = document.createElement("div");
  scroller.className = "diagram-scroll";
  const canvas = document.createElement("canvas");
  scroller.append(canvas);
  const caption = document.createElement("small");
  figure.append(scroller, caption);
  wordField.closest("label").after(figure);
  const draw = () =>
    drawDiagram(
      canvas,
      caption,
      wordField.value,
      Number(strandsField.value),
      layoutField.value === "ring",
    );
  wordField.addEventListener("input", draw);
  strandsField.addEventListener("input", draw);
  new ResizeObserver(() => {
    if (!canvas.isConnected) return;
    draw();
  }).observe(figure);
  draw();
}

function drawDiagram(canvas, caption, text, strands, ring = false) {
  let word;
  try {
    word = parseWord(text);
    caption.textContent = "";
  } catch (error) {
    caption.textContent = error.message;
    canvas.hidden = true;
    return;
  }
  const given = Number.isFinite(strands) && strands > 0 ? strands : 0;
  const top = word.length ? Math.max(...word.map(Math.abs)) : 1;
  // Round a ring, n + 1 is the greatest move there is: a turn.
  const needed = ring ? top - 1 : top + 1;
  const n = Math.max(needed, given || (ring ? top : needed), 2);
  canvas.hidden = !word.length;
  if (!word.length) return;
  if (given && n > given) {
    caption.textContent = ring
      ? `On a ring of ${given} strands, moves go up to ${given + 1}: drawn with ${n}.`
      : `σ${needed - 1} needs ${needed} strands: drawn with ${n}.`;
  }
  // Rows and columns no smaller than can be read: a long word, or many
  // strands, scrolls rather than shrinks.
  const room = canvas.parentElement.clientWidth;
  const row = Math.max(14, Math.min(28, 360 / word.length));
  const height = row * (word.length + 1);
  const across = ring ? n : n - 1;
  const width = Math.max(room, 24 + 14 * across);
  const ratio = Math.min(window.devicePixelRatio || 1, 2);
  canvas.style.width = `${width}px`;
  canvas.style.height = `${height}px`;
  canvas.width = Math.round(width * ratio);
  canvas.height = Math.round(height * ratio);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
  // A ring is drawn on a cylinder cut at its seam: half a column each side,
  // where a strand leaving one edge comes back at the other.
  const column = Math.min(44, (width - 24) / Math.max(across, 1));
  const left = (width - column * (n - 1)) / 2;
  const X = (slot) => left + slot * column;
  const lineWidth = Math.max(1.5, Math.min(3, column / 8));
  const background = getComputedStyle(canvas).backgroundColor;
  // Which strand is in each slot, row by row.
  let order = [...Array(n).keys()];
  ctx.lineCap = "round";
  if (ring) {
    ctx.save();
    ctx.setLineDash([3, 4]);
    ctx.strokeStyle = getComputedStyle(canvas).borderTopColor;
    ctx.lineWidth = 1;
    for (const x of [X(-0.5), X(n - 0.5)]) {
      ctx.beginPath();
      ctx.moveTo(x, 0);
      ctx.lineTo(x, height);
      ctx.stroke();
    }
    ctx.restore();
    ctx.beginPath();
    ctx.rect(X(-0.5), 0, X(n - 0.5) - X(-0.5), height);
    ctx.clip();
  }
  // From one slot to another, a row down.  Round a ring, slot n is slot 0
  // seen past the right-hand edge, and slot -1 the last past the left: what
  // goes off one edge comes back in at the other.
  const stroke = (strand, from, to, y, wide) => {
    const shifts = [0];
    if (ring && Math.max(from, to) >= n) shifts.push(n);
    if (ring && Math.min(from, to) < 0) shifts.push(-n);
    for (const shift of shifts) {
      const a = X(from - shift);
      const b = X(to - shift);
      ctx.beginPath();
      ctx.moveTo(a, y);
      ctx.bezierCurveTo(a, y + row / 2, b, y + row / 2, b, y + row);
      ctx.strokeStyle = wide
        ? background
        : strandColour(strand, PALETTE[strand % PALETTE.length]);
      ctx.lineWidth = wide ? lineWidth * 3.5 : lineWidth;
      ctx.stroke();
    }
  };
  word.forEach((g, k) => {
    const y = row / 2 + k * row;
    const index = Math.abs(g);
    if (ring && index === n + 1) {
      // A turn: every strand one place round, passing nobody.
      const way = g > 0 ? 1 : -1;
      for (let slot = 0; slot < n; slot++) stroke(order[slot], slot, slot + way, y);
      order = way > 0 ? [order[n - 1], ...order.slice(0, -1)] : [...order.slice(1), order[0]];
      return;
    }
    // σᵢ: the strand in slot i - 1 passes over — outside, round a ring —
    // its inverse, under.  Round a ring, σₙ crosses the last slot and the
    // first, drawn as slot n.
    const i = index - 1;
    const j = (i + 1) % n;
    for (let slot = 0; slot < n; slot++) {
      if (slot !== i && slot !== j) stroke(order[slot], slot, slot, y);
    }
    const [under, over] = g > 0 ? [order[j], order[i]] : [order[i], order[j]];
    const [underWay, overWay] = g > 0 ? [[i + 1, i], [i, i + 1]] : [[i, i + 1], [i + 1, i]];
    stroke(under, ...underWay, y);
    stroke(over, ...overWay, y, true);
    stroke(over, ...overWay, y);
    [order[i], order[j]] = [order[j], order[i]];
  });
}
