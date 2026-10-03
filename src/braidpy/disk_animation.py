# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
disk_animation.py
=================

A braiding disk, animated as the braider sees it: from above.

Each strand runs from its slot on the rim in to the middle, where the braid
goes down through the hole — so it is drawn as a radial line from the centre
to its carrier.  The carriers move continuously, step by step, along the
paths :func:`~braidpy.take_off.disk_trajectories` gives them, so this is the
same motion the braid is laid from, and what is seen here is what
:func:`~braidpy.take_off.lay_yarns` builds on.

A strand lifted over the others passes *inside* the rim — over, seen from
above — and is drawn on top of them while it does, so the picture says which
way every crossing goes.

:func:`animate_kumihimo` and :func:`animate_mobidai` read their sources onto a
disk and animate it; :func:`animate_disk` does the drawing for any disk.
"""

from __future__ import annotations

from typing import Dict, Hashable, List, Optional, Sequence

import numpy as np
import plotly.graph_objects as go

from braidpy.take_off import (
    StrandTrajectories,
    kumihimo_steps,
    kumihimo_trajectories,
    mobidai_steps,
    mobidai_trajectories,
)

# How far into its lift a strand must be before it is drawn over the others,
# as a fraction of the deepest lift.
_LIFTED = 0.01

# Width of every strand's spoke, and how much white edging a strand lifted
# all the way in has either side of it.
_SPOKE_WIDTH = 3
_EDGING = 6


def _rim_radius(trajectories: StrandTrajectories) -> float:
    """The disk's radius: where the carriers sit when they are not moving."""
    return float(max(np.max(np.hypot(*xy.T)) for xy in trajectories.xy.values()) or 1.0)


def _hsv_colours(n: int) -> List[str]:
    """Hues round the colour wheel, one per strand, as Kumihimo draws them.

    Spaced so the wheel does not wrap: Kumihimo's own palette runs from 0 to
    1 inclusive, which makes the first and last strands the same red.
    """
    import matplotlib.colors as mcolors
    import matplotlib.pyplot as plt

    return [mcolors.to_hex(c) for c in plt.cm.hsv(np.linspace(0, 1, n, endpoint=False))]


def animate_disk(
    trajectories: StrandTrajectories,
    step_labels: Optional[Sequence[str]] = None,
    title: str = "Braiding disk",
    output_html: Optional[str] = None,
    colors: Optional[Sequence[str]] = None,
    show_ids: bool = True,
    frame_duration_ms: int = 50,
    max_frames: int = 900,
) -> go.Figure:
    """Animate strands moving round a disk, seen from above.

    Args:
        trajectories: Where the strands go — from
            :func:`~braidpy.take_off.disk_trajectories` or a reader built on
            it.  One unit of time is one step.
        step_labels: What each step is, shown on the slider as it is made.
        title: Figure title.
        output_html: If given, write the animation to this HTML file.
        colors: One colour per strand; the horn gear animation's if None.
        show_ids: Name each strand at its carrier.
        frame_duration_ms: How long each frame is shown.
        max_frames: Frame budget: a long sequence is sampled more coarsely
            rather than written to a page too big to open.

    Returns:
        The figure, with one frame per sample kept.
    """
    if colors is None:
        from braidpy.horn_gear.visualization import _PALETTE

        colors = _PALETTE
    keys: List[Hashable] = list(trajectories.xy)
    colour: Dict[Hashable, str] = {
        k: colors[i % len(colors)] for i, k in enumerate(keys)
    }
    rim = _rim_radius(trajectories)
    centre = trajectories.centre()

    times = trajectories.times
    per_step = max(1, int(round(1.0 / float(times[1] - times[0]))))
    stride = max(1, int(np.ceil(len(times) / max_frames)))
    samples = list(range(0, len(times), stride))
    if samples[-1] != len(times) - 1:
        samples.append(len(times) - 1)

    # How far in a strand is, as a fraction of the deepest any strand goes:
    # 0 on the rim, 1 at the middle of the deepest lift.
    depth = {
        k: (rim - np.hypot(xy[:, 0] - centre[0], xy[:, 1] - centre[1])) / rim
        for k, xy in trajectories.xy.items()
    }
    deepest = max(float(np.max(d)) for d in depth.values())

    def strand_traces(i: int) -> List[go.Scatter]:
        """Every strand as a spoke, then again on top for those lifted over.

        A strand looks the same throughout a move — same width, same colour —
        so nothing about it jumps when it is lifted or set down.  What says it
        is over is a white edging drawn under the copy on top, which widens
        as the strand goes in and narrows as it comes back out: nothing at
        the start of the move, nothing at the end, and widest half way.
        """
        under: List[go.Scatter] = []
        edging: List[go.Scatter] = []
        over: List[go.Scatter] = []
        for k in keys:
            x, y = trajectories.xy[k][i]
            lift = float(depth[k][i]) / deepest if deepest > 0 else 0.0
            lifted = lift > _LIFTED
            spoke = dict(
                x=[centre[0], x],
                y=[centre[1], y],
                mode="lines",
                line=dict(color=colour[k], width=_SPOKE_WIDTH),
                hoverinfo="skip",
                showlegend=False,
            )
            under.append(go.Scatter(**spoke))
            # A strand that is not lifted still sends its edging and its copy,
            # as gaps: Plotly leaves a trace alone when a frame gives it no
            # points, so an empty one would keep showing the last lift.
            gap = {} if lifted else {"x": [None, None], "y": [None, None]}
            edging.append(
                go.Scatter(
                    **{
                        **spoke,
                        "line": dict(
                            color="white", width=_SPOKE_WIDTH + _EDGING * lift
                        ),
                        **gap,
                    }
                )
            )
            over.append(go.Scatter(**{**spoke, **gap}))
        carriers = go.Scatter(
            x=[trajectories.xy[k][i][0] for k in keys],
            y=[trajectories.xy[k][i][1] for k in keys],
            mode="markers+text" if show_ids else "markers",
            marker=dict(
                size=14,
                color=[colour[k] for k in keys],
                line=dict(color="white", width=1.5),
            ),
            text=[str(k) for k in keys],
            textposition="middle center",
            textfont=dict(size=8, color="white"),
            hovertext=[f"{trajectories.label}{k}" for k in keys],
            hoverinfo="text",
            showlegend=False,
        )
        return under + edging + over + [carriers]

    def rounded(trace: go.Scatter) -> go.Scatter:
        if trace.x is not None:
            trace.x = [None if v is None else round(float(v), 4) for v in trace.x]
            trace.y = [None if v is None else round(float(v), 4) for v in trace.y]
        return trace

    still: List[go.BaseTraceType] = []
    for outline in trajectories.outlines:
        still.append(
            go.Scatter(
                x=outline[:, 0],
                y=outline[:, 1],
                mode="lines",
                line=dict(color="rgba(110,110,110,0.8)", width=2),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    if trajectories.slots:
        # Every slot on the rim, and its number just outside it.
        xs, ys, names = zip(*trajectories.slots)
        outward = [
            np.array([x - centre[0], y - centre[1]]) * 1.09 + np.array(centre)
            for x, y in zip(xs, ys)
        ]
        still.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                marker=dict(size=5, color="rgba(110,110,110,0.9)"),
                hovertext=[f"Slot {name}" for name in names],
                hoverinfo="text",
                showlegend=False,
            )
        )
        still.append(
            go.Scatter(
                x=[p[0] for p in outward],
                y=[p[1] for p in outward],
                mode="text",
                text=list(names),
                textfont=dict(size=9, color="rgba(90,90,90,1)"),
                hoverinfo="skip",
                showlegend=False,
            )
        )
    still.append(
        go.Scatter(
            x=[centre[0]],
            y=[centre[1]],
            mode="markers",
            marker=dict(size=7, color="black"),
            hovertext=["Braiding point"],
            hoverinfo="text",
            showlegend=False,
        )
    )
    moving = list(range(len(still), len(still) + 3 * len(keys) + 1))

    def label(i: int) -> str:
        step = min(i // per_step, max(len(times) - 2, 0) // per_step)
        what = (
            f" {step_labels[step]}"
            if step_labels is not None and step < len(step_labels)
            else ""
        )
        # The last sample closes the last step rather than opening another.
        opens = i % per_step == 0 and i < len(times) - 1
        return f"{step}{what}" if opens else ""

    frames = [
        go.Frame(
            data=[rounded(t) for t in strand_traces(i)],
            traces=moving,
            name=str(i),
        )
        for i in samples
    ]
    fig = go.Figure(data=still + strand_traces(0), frames=frames)
    reach = rim * 1.2
    fig.update_layout(
        title=title,
        xaxis=dict(
            range=[centre[0] - reach, centre[0] + reach],
            scaleanchor="y",
            scaleratio=1,
            visible=False,
        ),
        yaxis=dict(range=[centre[1] - reach, centre[1] + reach], visible=False),
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=80, b=20),
        updatemenus=[
            dict(
                type="buttons",
                showactive=False,
                y=1.08,
                x=0.5,
                xanchor="center",
                buttons=[
                    dict(
                        label="▶ Play",
                        method="animate",
                        args=[
                            None,
                            {
                                "frame": {
                                    "duration": frame_duration_ms,
                                    "redraw": True,
                                },
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    ),
                    dict(
                        label="⏸ Pause",
                        method="animate",
                        args=[
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                            },
                        ],
                    ),
                ],
            )
        ],
        sliders=[
            dict(
                steps=[
                    dict(
                        args=[
                            [str(i)],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                            },
                        ],
                        label=label(i),
                        method="animate",
                    )
                    for i in samples
                ],
                active=0,
                x=0,
                y=0,
                len=1.0,
                currentvalue=dict(visible=False),
                transition=dict(duration=0),
            )
        ],
    )
    if output_html:
        fig.write_html(output_html)
    return fig


def kumihimo_step_labels(kumihimo, n_strands: Optional[int] = None) -> List[str]:
    """What each disk step of a kumihimo sequence is, for the slider.

    A swap takes three steps on the disk (see
    :func:`~braidpy.take_off.kumihimo_steps`); a rotation one.
    """
    pattern = isinstance(kumihimo, str)
    moves = kumihimo if pattern else list(kumihimo.history)
    labels: List[str] = []
    for move in moves:
        if move == "S":
            labels += ["S (top over)", "S (bottom over)", "S (settle)"]
        else:
            turns = int(move.split("**")[1]) if "**" in move else 1
            labels.append("R" if turns == 1 else f"R×{turns}")
    if not pattern or n_strands is not None:
        kumihimo_steps(kumihimo, n_strands)  # refuse what the disk refuses
    return labels


def animate_kumihimo(
    kumihimo,
    n_strands: Optional[int] = None,
    output_html: Optional[str] = None,
    title: Optional[str] = None,
    samples_per_step: int = 12,
    **kwargs,
) -> go.Figure:
    """Animate a kumihimo sequence on its disk, seen from above.

    Args:
        kumihimo: A :class:`~braidpy.kumihimo.Kumihimo`, or a pattern of ``S``
            and ``R`` for ``n_strands`` strands.
        n_strands: Strands, when given a pattern.
        output_html: If given, write the animation to this HTML file.
        title: Figure title; names the pattern if None.
        samples_per_step: Frames per disk step.
        **kwargs: Passed on to :func:`animate_disk`.

    Returns:
        The figure.
    """
    pattern = kumihimo if isinstance(kumihimo, str) else kumihimo.pattern
    n = n_strands if isinstance(kumihimo, str) else kumihimo.n
    trajectories = kumihimo_trajectories(
        kumihimo, n_strands, samples_per_step=samples_per_step
    )
    kwargs.setdefault("colors", _hsv_colours(n))
    return animate_disk(
        trajectories,
        step_labels=kumihimo_step_labels(kumihimo, n_strands),
        title=title or f"Kumihimo, {n} strands — {pattern}",
        output_html=output_html,
        **kwargs,
    )


def animate_mobidai(
    mobidai,
    n_cycles: int = 1,
    drift: Optional[int] = None,
    output_html: Optional[str] = None,
    title: Optional[str] = None,
    samples_per_step: int = 12,
    slot_offset: float = 0.0,
    **kwargs,
) -> go.Figure:
    """Animate a mobidai's cycles on its disk, seen from above.

    Args:
        mobidai: A :class:`~braidpy.mobidai.Mobidai` or its configuration.
        n_cycles: Cycles to animate.
        drift: Slots each cycle's moves are shifted from the one before; read
            off the cycle if None — see :func:`~braidpy.take_off.mobidai_steps`.
        output_html: If given, write the animation to this HTML file.
        title: Figure title.
        samples_per_step: Frames per move.
        slot_offset: Slots the numbering is turned by: 0.5 puts the top of
            the disk between the last slot and slot 1, as a kumihimo disk is
            marked.
        **kwargs: Passed on to :func:`animate_disk`.

    Returns:
        The figure.
    """
    config = getattr(mobidai, "config", mobidai)
    _, steps = mobidai_steps(config, n_cycles, drift)
    labels = ["turn" if len(step) == len(config.strands) else "move" for step in steps]
    trajectories = mobidai_trajectories(
        config,
        n_cycles=n_cycles,
        drift=drift,
        samples_per_step=samples_per_step,
        slot_offset=slot_offset,
    )
    kwargs.setdefault(
        "colors",
        [getattr(s, "color", None) or "#888888" for s in config.strands],
    )
    return animate_disk(
        trajectories,
        step_labels=labels,
        title=title
        or f"Mobidai, {len(config.strands)} strands on {config.n_slots} slots",
        output_html=output_html,
        **kwargs,
    )
