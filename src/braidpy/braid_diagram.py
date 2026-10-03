# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: braid_diagram.py
Description: The 2D braid diagram, drawn by braidpy rather than by a library
Authors: Baptiste Labat
Created: 2025-06-06
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

braidpy used to hand this picture to `braid-visualiser`, which drew a
perfectly good diagram in **its own colours** — so a strand was one colour in
the console and another in the plot, and the two could not be read together.
Drawing it here fixes that: the diagram uses
:data:`~braidpy.utils.terminal_colors`, the same palette
:meth:`~braidpy.braid.Braid.draw` uses, so strand 3 is the same colour
wherever you look at it.

The picture is the one braidpy already computes.
:meth:`~braidpy.braid.Braid.to_parametric_strands` gives each strand as a
curve in three coordinates — *across* the braid, *depth* (positive where a
strand passes in front), and *time* — so the diagram is that curve seen from
the front, with the strand that passes behind interrupted where the two meet.
Nothing is re-derived here; the over-and-under already lives in the curve.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .utils import terminal_colors

__all__ = ["DIAGRAM_COLORS", "diagram_segments", "draw_diagram", "strand_color"]

# terminal_colors is written for the console and for plotly, and its last
# entry is a plotly colour string that matplotlib cannot read.  Translate the
# ones that need it and leave the rest alone, so the two palettes stay the
# same colours in the same order.
DIAGRAM_COLORS: Dict[int, str] = {
    index: {"rgb(0,128,128)": "teal"}.get(name, name)
    for index, name in terminal_colors.items()
}


def strand_color(index: int) -> str:
    """The colour of a strand, matching the one the console draws it in.

    Args:
        index: Which strand, from 0.  Wraps round when there are more strands
            than colours, exactly as the console does.

    Returns:
        A colour matplotlib understands.
    """
    return DIAGRAM_COLORS[index % len(DIAGRAM_COLORS)]


def _spacing(paths: Sequence[np.ndarray]) -> float:
    """How far apart the strands sit across the braid.

    Used to size the break at a crossing relative to the drawing, so the gap
    looks the same whatever the braid's width.
    """
    starts = sorted(path[0, 0] for path in paths)
    gaps = [b - a for a, b in zip(starts, starts[1:]) if b - a > 1e-9]
    return min(gaps) if gaps else 1.0


def diagram_segments(
    strands: Sequence,
    n_samples: int = 400,
    gap: float = 0.3,
) -> List[List[np.ndarray]]:
    """Each strand as the pieces of it that are visible from the front.

    A strand is hidden where it passes *behind* another — where the two are
    at the same place across the braid and this one has the lesser depth.
    Breaking the line there is what makes a diagram readable as a braid
    rather than as a tangle.

    Args:
        strands: Objects answering ``sample(n)``, as
            :meth:`~braidpy.braid.Braid.to_parametric_strands` returns.
        n_samples: Points along each strand.  A crossing narrower than the
            spacing between samples would be drawn unbroken.
        gap: How wide the break is, as a fraction of the distance between
            neighbouring strands.

    Returns:
        Per strand, a list of ``(n, 2)`` arrays of ``(time, across)`` to draw
        as separate lines.
    """
    paths = [np.asarray(strand.sample(n_samples)) for strand in strands]
    if not paths:
        return []
    width = gap * _spacing(paths)

    visible = [np.ones(len(path), dtype=bool) for path in paths]
    for first in range(len(paths)):
        for second in range(first + 1, len(paths)):
            here, there = paths[first], paths[second]
            meeting = np.abs(here[:, 0] - there[:, 0]) < width
            behind = here[:, 1] < there[:, 1]
            visible[first][meeting & behind] = False
            visible[second][meeting & ~behind] = False

    pieces: List[List[np.ndarray]] = []
    for path, mask in zip(paths, visible):
        runs: List[np.ndarray] = []
        start = 0
        while start < len(mask):
            while start < len(mask) and not mask[start]:
                start += 1
            end = start
            while end < len(mask) and mask[end]:
                end += 1
            if end - start > 1:
                runs.append(np.column_stack((path[start:end, 2], path[start:end, 0])))
            start = end
        pieces.append(runs)
    return pieces


def draw_diagram(
    braid,
    n_samples: int = 400,
    line_width: float = 3.0,
    gap: float = 0.3,
    color: Optional[str] = None,
    save: Optional[str] = None,
    ax: Optional["plt.Axes"] = None,
) -> "plt.Axes":
    """Draw a braid as a diagram, read from left to right.

    Args:
        braid: The braid to draw.
        n_samples: Points along each strand.
        line_width: Thickness of a strand.
        gap: Width of the break where a strand passes behind, as a fraction
            of the distance between neighbouring strands.
        color: One colour for every strand.  By default each strand takes its
            own, the same colour :meth:`~braidpy.braid.Braid.draw` gives it.
        save: Path to write the figure to, if wanted.
        ax: Axes to draw on; a new figure otherwise.

    Returns:
        The axes drawn on.
    """
    strands = braid.to_parametric_strands()
    pieces = diagram_segments(strands, n_samples=n_samples, gap=gap)

    if ax is None:
        _, ax = plt.subplots(figsize=(1.6 * max(len(braid.generators), 1), 2.4))

    for index, runs in enumerate(pieces):
        shade = color or strand_color(index)
        for number, run in enumerate(runs):
            ax.plot(
                run[:, 0],
                run[:, 1],
                color=shade,
                linewidth=line_width,
                solid_capstyle="round",
                label=f"strand {index}" if number == 0 else None,
            )

    ax.set_xlabel("time")
    ax.set_ylabel("position across the braid")
    ax.set_yticks(
        sorted(
            {float(path[0, 0]) for path in (np.asarray(s.sample(2)) for s in strands)}
        )
    )
    ax.set_yticklabels(range(1, len(strands) + 1))
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    if save:
        ax.figure.savefig(save, bbox_inches="tight")
    return ax
