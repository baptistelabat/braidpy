# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Drawing the yarns in 3D, with Plotly, standing on whatever laid them."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Optional

import numpy as np

from braidpy.utils import lazy_module

from .paths import StrandTrajectories, YarnPaths

if TYPE_CHECKING:
    import plotly.graph_objects as go
else:
    go = lazy_module("plotly.graph_objects")


def _outline_traces(trajectories: StrandTrajectories) -> list[go.Scatter3d]:
    """The source's outlines, drawn on the plane at z = 0, so the yarns stand
    on what laid them: a machine's gears, a disk's rim.

    Args:
        trajectories: Where the strands went, with the outlines of what moved
            them (:attr:`~braidpy.take_off.paths.StrandTrajectories.outlines`)
            and the name to show for them (``outline_name``).

    Returns:
        One Plotly trace holding every outline, each a closed line, the next
        apart from it by a gap; none if the source has no outlines.
    """
    if not trajectories.outlines:
        return []
    xs: list[float | None] = []
    ys: list[float | None] = []
    for outline in trajectories.outlines:
        xs.extend(outline[:, 0].tolist() + [None])
        ys.extend(outline[:, 1].tolist() + [None])
    return [
        go.Scatter3d(
            x=xs,
            y=ys,
            z=[0.0 if x is not None else None for x in xs],
            mode="lines",
            line=dict(color="rgba(110,110,110,0.7)", width=3),
            name=trajectories.outline_name,
            hoverinfo="skip",
        )
    ]


def visualize_yarns(
    paths: YarnPaths,
    output_html: Optional[str] = None,
    title: Optional[str] = None,
    tube_diameter: Optional[float] = None,
    n_around: int = 12,
    show_deck: bool = True,
    colors: Optional[Sequence[str]] = None,
    extra_traces: Sequence[go.BaseTraceType] = (),
) -> go.Figure:
    """The yarns in 3D, standing on whatever laid them.

    Each yarn ends in a marker at the plane, where its carrier is now; the
    source's outlines are drawn there, and the fell or braiding point where
    the yarns meet.

    Args:
        paths: The yarns to draw.
        output_html: If given, write the figure to this HTML file.
        title: Figure title; says which model the yarns follow if None.
        tube_diameter: Draw the yarns as tubes this thick.  Defaults to the
            yarn diameter the braid was made for, if any; 0 draws lines.
        n_around: Points round each tube, when drawing them.
        show_deck: Draw the source's outlines at z = 0.
        colors: One colour per yarn, cycled; the horn gear animation's if None,
            so a yarn can be matched to its bobbin there.
        extra_traces: Anything else to draw in the same scene.

    Returns:
        The figure.
    """
    if colors is None:
        from braidpy.utils import PALETTE

        colors = PALETTE

    if title is None:
        if paths.fell_radius is None:
            title = "Braid as laid (no tension)"
        elif paths.fell_radius == 0:
            title = "Braid formed at a braiding point"
        else:
            title = f"Braid formed on a fell of radius {paths.fell_radius:.3g}"

    if tube_diameter is None:
        tube_diameter = paths.yarn_diameter
    if not tube_diameter:
        tube_diameter = None

    # The yarns themselves are drawn as any parametric braid is, upright,
    # sampled as finely as they were laid.
    label = paths.trajectories.label
    names = [f"{label}{key}" for key in paths.points]
    fig = paths.to_parametric_braid().figure(
        n_sample=len(paths.times),
        title=title,
        tube_diameter=tube_diameter,
        n_around=n_around,
        opacity=1.0,
        colors=colors,
        names=names,
        line_width=6,
        z_title="z (take-off)",
        flip_z=False,
    )

    traces: list[go.BaseTraceType] = []
    if show_deck:
        traces.extend(_outline_traces(paths.trajectories))

    for index, (key, points) in enumerate(paths.points.items()):
        x0, y0, z0 = points[-1]
        traces.append(
            go.Scatter3d(
                x=[x0],
                y=[y0],
                z=[z0],
                mode="markers",
                marker=dict(
                    size=6,
                    color=colors[index % len(colors)],
                    line=dict(color="white", width=1),
                ),
                name=str(key),
                legendgroup=names[index],
                showlegend=False,
                hoverinfo="name",
            )
        )

    # The fell, where the converging yarns become braid.
    if paths.fell_height > 0 and paths.fell_radius is not None:
        angles = np.linspace(0.0, 2 * np.pi, 73)
        ax, ay = paths.axis
        traces.append(
            go.Scatter3d(
                x=ax + paths.fell_radius * np.cos(angles),
                y=ay + paths.fell_radius * np.sin(angles),
                z=np.full_like(angles, paths.fell_height),
                mode="lines" if paths.fell_radius > 0 else "markers",
                line=dict(color="black", width=4),
                marker=dict(color="black", size=5),
                name="Fell" if paths.fell_radius > 0 else "Braiding point",
                hoverinfo="name",
            )
        )

    traces.extend(extra_traces)
    fig.add_traces(traces)
    fig.update_layout(
        scene=dict(xaxis_title="x", yaxis_title="y"),
        margin=dict(l=0, r=0, b=0, t=40),
    )
    if output_html:
        fig.write_html(output_html)
    return fig
