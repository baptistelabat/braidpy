// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// A disk or a sinnet's moves, typed in or clicked on a drawing of the disk.

function hue(i, n) {
  return `hsl(${(360 * i) / Math.max(n, 1)}, 100%, 50%)`;
}

function pairs(text) {
  const numbers = (String(text).match(/\d+/g) || []).map(Number);
  const out = [];
  for (let i = 0; i + 1 < numbers.length; i += 2) out.push([numbers[i], numbers[i + 1]]);
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
  box.append(canvas, help, buttons);
  label.after(box);

  let chosen = null;
  // Moves changed here are changed as if typed: the braid becomes your own.
  const changed = () => {
    chosen = null;
    moves.dispatchEvent(new Event("input", { bubbles: true }));
  };
  const add = (from, to) => {
    const list = moves.value.trim();
    moves.value = (list ? list + ", " : "") + `${from}>${to}`;
    changed();
  };
  undo.addEventListener("click", () => {
    const list = pairs(moves.value);
    list.pop();
    moves.value = list.map(([a, b]) => `${a}>${b}`).join(", ");
    changed();
  });
  clear.addEventListener("click", () => {
    moves.value = "";
    changed();
  });

  // What there is to draw and click: places round a circle, and who is
  // where once every move so far is made.
  function state() {
    if (source === "mobidai") {
      const n = Math.max(3, Number(holder.querySelector("[name=n_slots]").value) || 32);
      const start = (holder.querySelector("[name=slots]").value.match(/\d+/g) || []).map(Number);
      const at = new Map(start.map((slot, i) => [slot, i]));
      for (const [from, to] of pairs(moves.value)) {
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
    for (const [from, to] of pairs(moves.value)) {
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
    const count = pairs(moves.value).length;
    help.textContent =
      chosen === null
        ? source === "mobidai"
          ? `Click a strand, then the slot it goes to. ${count} move${count === 1 ? "" : "s"}.`
          : `Click the space a strand leaves, then the one it goes to. ${count} move${count === 1 ? "" : "s"}.`
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
    requestAnimationFrame(draw);
  });
  const observer = new ResizeObserver(draw);
  observer.observe(canvas);
  draw();
}
