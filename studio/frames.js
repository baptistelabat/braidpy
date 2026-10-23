// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at https://mozilla.org/MPL/2.0/.

// The moments of a braid's making on a marudai, kept for Grow to replay
// (settle.js, onMarudaiFrame), each only as much as it needs: of each yarn,
// only the beads still free.  A frozen bead (marudai.js) moves only as the
// whole braid turns, so where it was is where the braid ends it (base),
// turned back by the moment's turn and raised by its lift.
//
// Kept with the site (settle_node.js), the moments are packed: each value a
// whole number of hundredths of a yarn diameter, given as the change from
// the same value a bead before, short to write and to compress.

// A moment as it was, every yarn whole, for the page to draw.
export function wholeFrame(frame, base) {
  if (!frame.frozen) return frame;
  const [c, s, tx, ty] = frame.turn;
  const yarns = frame.yarns.map((free, t) => {
    const from = base[t];
    const n = 3 * frame.frozen[t];
    const out = new Float32Array(n + free.length);
    for (let i = 0; i < n; i += 3) {
      const x = from[i], y = from[i + 1];
      out[i] = c * x + s * y + tx;
      out[i + 1] = -s * x + c * y + ty;
      out[i + 2] = from[i + 2] + frame.lift;
    }
    out.set(free, n);
    return out;
  });
  return { ...frame, yarns };
}

// A marudai's moments packed to be kept as JSON, ``step`` apart.
export function pack(marudai, step) {
  const packed = (values) => {
    const out = new Array(values.length);
    for (let i = 0; i < values.length; i++) {
      out[i] = Math.round(values[i] / step) - (i >= 3 ? Math.round(values[i - 3] / step) : 0);
    }
    return out;
  };
  return {
    ...marudai,
    packed: step,
    base: marudai.base.map(packed),
    frames: marudai.frames.map((frame) => ({ ...frame, yarns: frame.yarns.map(packed) })),
  };
}

// A marudai's moments as they were before pack(): unchanged if not packed.
export function unpack(marudai) {
  const step = marudai?.packed;
  if (!step) return marudai;
  const unpacked = (values) => {
    const out = new Float32Array(values.length);
    const whole = new Array(values.length);
    for (let i = 0; i < values.length; i++) {
      whole[i] = values[i] + (i >= 3 ? whole[i - 3] : 0);
      out[i] = whole[i] * step;
    }
    return out;
  };
  const { packed, ...rest } = marudai;
  return {
    ...rest,
    base: marudai.base.map(unpacked),
    frames: marudai.frames.map((frame) => ({ ...frame, yarns: frame.yarns.map(unpacked) })),
  };
}
