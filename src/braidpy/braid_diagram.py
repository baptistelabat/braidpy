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

The braid runs **down** the page, the way a braid hangs and the way a braider
works, with the word written above it.  Strands swing across on the
smoothstep profile of :mod:`~braidpy.parametric_strand`, so a crossing is a
curve rather than a corner; pass ``profile=LINEAR`` for straight segments.

Nothing about the braid is re-derived here.
:func:`~braidpy.parametric_strand.strand_paths` gives each strand as a curve
in three coordinates — *across* the braid, *depth* (positive where a strand
passes in front), and *along* — so the diagram is that curve seen from the
front, with the strand passing behind interrupted where the two meet.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .parametric_strand import LINEAR, SMOOTHSTEP, Profile, strand_paths
from .utils import terminal_colors

__all__ = [
    "DIAGRAM_COLORS",
    "LINEAR",
    "SMOOTHSTEP",
    "diagram_segments",
    "draw_diagram",
    "sample_period",
    "strand_color",
]

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


def sample_period(path, n_samples: int) -> np.ndarray:
    """One period of a strand, without the wrap at the end.

    :meth:`~braidpy.parametric_strand.StrandPath.position` takes ``z`` modulo
    the period, so that a closed braid can be followed round and round.  Asked
    for the very last point of one period it therefore answers with the
    *first*, and a diagram drawn from that has every strand jumping back to
    where it started.  Sample up to the period and finish with the slot the
    strand genuinely ends in.

    Args:
        path: A :class:`~braidpy.parametric_strand.StrandPath`.
        n_samples: Points to take.

    Returns:
        An ``(n_samples, 3)`` array of ``(across, depth, along)``.
    """
    heights = np.linspace(0.0, path.length, n_samples, endpoint=False)
    points = [path.position(float(z)) for z in heights]
    points.append((path.slots[-1] * path.spacing, 0.0, float(path.length)))
    return np.asarray(points)


def diagram_segments(
    paths: Sequence,
    n_samples: int = 400,
    gap: float = 0.11,
) -> List[List[np.ndarray]]:
    """Each strand as the pieces of it that are visible from the front.

    A strand is hidden where it passes *behind* another — where the two are
    at the same place across the braid and this one has the lesser depth.
    Breaking the line there is what makes a diagram readable as a braid
    rather than as a tangle.

    Args:
        paths: :class:`~braidpy.parametric_strand.StrandPath` objects, as
            :func:`~braidpy.parametric_strand.strand_paths` returns.
        n_samples: Points along each strand.  A crossing narrower than the
            spacing between samples would be drawn unbroken.
        gap: How wide the break is, as a fraction of the distance between
            neighbouring strands.

    Returns:
        Per strand, a list of ``(n, 2)`` arrays of ``(across, along)`` to
        draw as separate lines.
    """
    if not paths:
        return []
    sampled = [sample_period(path, n_samples) for path in paths]
    width = gap * paths[0].spacing

    visible = [np.ones(len(points), dtype=bool) for points in sampled]
    for first in range(len(sampled)):
        for second in range(first + 1, len(sampled)):
            here, there = sampled[first], sampled[second]
            meeting = np.abs(here[:, 0] - there[:, 0]) < width
            behind = here[:, 1] < there[:, 1]
            visible[first][meeting & behind] = False
            visible[second][meeting & ~behind] = False

    pieces: List[List[np.ndarray]] = []
    for points, mask in zip(sampled, visible):
        runs: List[np.ndarray] = []
        start = 0
        while start < len(mask):
            while start < len(mask) and not mask[start]:
                start += 1
            end = start
            while end < len(mask) and mask[end]:
                end += 1
            if end - start > 1:
                runs.append(points[start:end, [0, 2]])
            start = end
        pieces.append(runs)
    return pieces


def draw_diagram(
    braid,
    n_samples: int = 400,
    line_width: float = 3.0,
    gap: float = 0.11,
    amplitude: float = 0.28,
    profile: Profile = SMOOTHSTEP,
    color: Optional[str] = None,
    title: Optional[str] = None,
    save: Optional[str] = None,
    ax: Optional["plt.Axes"] = None,
) -> "plt.Axes":
    """Draw a braid as a diagram, running down the page.

    Args:
        braid: The braid to draw.
        n_samples: Points along each strand.
        line_width: Thickness of a strand.
        gap: Width of the break where a strand passes behind, as a fraction
            of the distance between neighbouring strands.
        amplitude: How far a strand swings out of line as it crosses.  Larger
            is rounder; the crossing is drawn, not just implied.
        profile: How a strand travels sideways — :data:`SMOOTHSTEP` for
            curves, :data:`LINEAR` for straight segments.
        color: One colour for every strand.  By default each takes its own,
            the same colour :meth:`~braidpy.braid.Braid.draw` gives it.
        title: Heading; the braid's word by default, and "" for none.
        save: Path to write the figure to, if wanted.
        ax: Axes to draw on; a new figure otherwise.

    Returns:
        The axes drawn on.
    """
    paths = strand_paths(braid, amplitude=amplitude, profile=profile)
    pieces = diagram_segments(paths, n_samples=n_samples, gap=gap)
    n_strands = len(paths)
    length = paths[0].length if paths else 1

    if ax is None:
        _, ax = plt.subplots(figsize=(1.1 + 0.7 * n_strands, 1.4 + 0.75 * length))

    for index, runs in enumerate(pieces):
        shade = color or strand_color(index)
        for run in runs:
            ax.plot(
                run[:, 0],
                run[:, 1],
                color=shade,
                linewidth=line_width,
                solid_capstyle="round",
            )

    if title is None:
        title = f"Braid: {braid.format()}"
    if title:
        ax.set_title(title, fontsize=11, pad=12)

    spacing = paths[0].spacing if paths else 1.0
    ax.set_xlim(-0.8 * spacing, (n_strands - 1 + 0.8) * spacing)
    ax.set_ylim(-0.1 * length, length * 1.05)
    ax.invert_yaxis()  # the braid hangs downward, as it is worked
    ax.set_aspect("equal")
    ax.axis("off")
    if save:
        ax.figure.savefig(save, bbox_inches="tight", dpi=150)
    return ax
