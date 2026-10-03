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

from typing import Dict, Hashable, List, Mapping, Optional, Sequence

import numpy as np
import plotly.graph_objects as go

from braidpy.take_off import (
    StrandTrajectories,
    crossing_rows,
    disk_crossing_steps,
    lay_yarns,
    ring_trajectories,
    tighten_yarns,
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
    import matplotlib
    import matplotlib.colors as mcolors

    wheel = matplotlib.colormaps["hsv"]
    return [mcolors.to_hex(c) for c in wheel(np.linspace(0, 1, n, endpoint=False))]


class BraidGrowth:
    """The braid a disk is making, as it grows below it — for a side view.

    The braid is laid once, from its crossings round a ring and tightened
    (see :func:`~braidpy.take_off.disk_braid`), and shown as the disk is
    worked: each crossing reaches the fell, just under the disk, as the
    strand making it passes the one it crosses on the disk, the older rows
    carried down by the take-off.  Rows are made in the order their
    crossings are, so nothing shows below the disk before it is made on it.
    The braid hangs from the disk and turns with it.  Only the last
    ``window_rows`` rows are shown, as a braider sees the length of braid
    nearest the disk.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots.
        n_slots: Slots round the disk.
        yarn_diameter: Yarn diameter.
        clockwise: Whether slot numbers go round clockwise, seen from above.
        take_off_per_row: Braid taken off per row of crossings, in diameters.
        window_rows: Rows of braid shown below the fell.
        iterations: Tightening steps.
        samples_per_row: Points along each yarn per row, as tightened: fewer
            and the tightening can snap a yarn across its neighbour.
        shown_per_row: Points along each yarn per row, as drawn.

    Raises:
        ValueError: If the moves cross no strands: there is no braid.
    """

    def __init__(
        self,
        start,
        steps,
        n_slots: int,
        yarn_diameter: float = 0.12,
        clockwise: bool = True,
        take_off_per_row: float = 1.5,
        window_rows: float = 12,
        iterations: int = 300,
        samples_per_row: int = 12,
        shown_per_row: int = 4,
    ) -> None:
        order, crossings, made_at = disk_crossing_steps(start, steps, n_slots)
        if not crossings:
            raise ValueError("The moves cross no strands: there is no braid.")
        rows = crossing_rows(order, crossings, in_turn=True)
        # Each crossing is half way through its row on the ring: that is
        # when it is at the fell.
        self.knot_times = np.array([0.0, *made_at, float(len(steps))])
        self.knot_rows = np.array([0.0, *(r + 0.5 for r in rows), rows[-1] + 1.0])

        ring = ring_trajectories(
            order,
            crossings,
            yarn_diameter,
            samples_per_row=samples_per_row,
            clockwise=clockwise,
            rows=rows,
        )
        self.ring_times = np.asarray(ring.times)
        self.ring_xy = ring.xy
        self.per_row = take_off_per_row * yarn_diameter
        laid = lay_yarns(ring, take_off=self.per_row, yarn_diameter=yarn_diameter)
        braid, _ = tighten_yarns(laid, yarn_diameter, iterations=iterations)
        stride = max(1, samples_per_row // max(1, shown_per_row))
        formed = braid.formed()[:, ::stride]
        self.keys: List[Hashable] = list(braid.points)
        self.xy = {k: formed[i, :, :2] for i, k in enumerate(self.keys)}
        self.times = np.asarray(braid.times[: braid.formed_count])[::stride]
        self.window = float(window_rows)
        self.diameter = yarn_diameter
        self.reach = float(np.max(np.hypot(formed[:, :, 0], formed[:, :, 1])))
        self.reach += yarn_diameter

    def rows_at(self, time: float) -> float:
        """How many rows the braid has, ``time`` disk steps in."""
        return float(np.interp(time, self.knot_times, self.knot_rows))

    def turn_at(self, rows: float, carriers: Mapping[Hashable, Sequence[float]]):
        """How far round the braid hangs, its strands nearest their carriers.

        Args:
            rows: Rows made.
            carriers: Each strand's carrier on the disk, from its centre.

        Returns:
            The angle, anticlockwise seen from above, to turn the braid by.
        """
        pull = 0j
        for k in self.keys:
            if k not in carriers:
                continue
            xy = self.ring_xy[k]
            x = np.interp(rows, self.ring_times, xy[:, 0])
            y = np.interp(rows, self.ring_times, xy[:, 1])
            cx, cy = carriers[k]
            pull += (
                complex(cx, cy)
                / max(abs(complex(cx, cy)), 1e-12)
                * complex(x, -y)
                / max(abs(complex(x, y)), 1e-12)
            )
        return float(np.angle(pull)) if abs(pull) > 1e-12 else 0.0

    def traces(
        self,
        time: float,
        colour: Mapping[Hashable, str],
        carriers: Optional[Mapping[Hashable, Sequence[float]]] = None,
    ) -> List[go.Scatter3d]:
        """Each yarn's visible length, ``time`` disk steps in.

        Args:
            time: Disk steps made.
            colour: Each strand's colour.
            carriers: Each strand's carrier on the disk, from its centre, to
                turn the braid as the disk is; not turned if None.
        """
        rows = self.rows_at(time)
        shown = (self.times <= rows + 1e-9) & (self.times >= rows - self.window)
        if not np.any(shown):
            shown = self.times == self.times[0]
        z = -self.per_row * (rows - self.times[shown])
        turn = self.turn_at(rows, carriers) if carriers is not None else 0.0
        c, s = np.cos(turn), np.sin(turn)
        out = []
        for k in self.keys:
            x, y = self.xy[k][shown].T
            out.append(
                go.Scatter3d(
                    x=np.round(c * x - s * y, 4),
                    y=np.round(s * x + c * y, 4),
                    z=np.round(z, 4),
                    mode="lines",
                    line=dict(color=colour[k], width=9),
                    hoverinfo="skip",
                    showlegend=False,
                    scene="scene",
                )
            )
        return out

    def fell(self) -> go.Scatter3d:
        """A ring at the fell, where the braid forms, just under the disk."""
        angles = np.linspace(0.0, 2 * np.pi, 49)
        r = self.reach
        return go.Scatter3d(
            x=r * np.cos(angles),
            y=r * np.sin(angles),
            z=np.zeros_like(angles),
            mode="lines",
            line=dict(color="rgba(110,110,110,0.8)", width=3),
            hoverinfo="skip",
            showlegend=False,
            scene="scene",
        )

    def scene(self) -> dict:
        """The side view's scene: seen from the front of the disk as drawn
        from above — its bottom edge — the braid hanging down."""
        depth = self.window * self.per_row
        r = self.reach
        hidden = dict(visible=False, showgrid=False, zeroline=False)
        tall = depth + 2 * self.diameter
        return dict(
            domain=dict(x=[0.52, 1.0], y=[0.08, 1.0]),
            xaxis=dict(range=[-r, r], **hidden),
            yaxis=dict(range=[-r, r], **hidden),
            zaxis=dict(range=[-depth - self.diameter, self.diameter], **hidden),
            aspectmode="manual",
            aspectratio=dict(x=2 * r / tall, y=2 * r / tall, z=1),
            camera=dict(
                eye=dict(x=0.0, y=-1.3, z=0.15),
                center=dict(x=0, y=0, z=0),
                up=dict(x=0, y=0, z=1),
            ),
        )


def animate_disk(
    trajectories: StrandTrajectories,
    step_labels: Optional[Sequence[str]] = None,
    title: str = "Braiding disk",
    output_html: Optional[str] = None,
    colors: Optional[Sequence[str]] = None,
    show_ids: bool = True,
    frame_duration_ms: int = 50,
    max_frames: int = 900,
    braid: Optional[BraidGrowth] = None,
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
        braid: Show the braid the disk is making beside it, growing below
            the disk — see :class:`BraidGrowth`.
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

    # Plain SVG traces.  WebGL would redraw a frame in one pass, but the
    # Plotly.js bundled here (3.0.1) cannot animate WebGL traces: the first
    # frame fails and every strand vanishes.
    Moving = go.Scatter

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
            under.append(Moving(**spoke))
            # A strand that is not lifted still sends its edging and its copy,
            # shrunk to nothing at the braiding point, where every spoke meets
            # anyway.  Not as no points: Plotly leaves a trace alone when a
            # frame gives it none, so the last lift would stay on screen.  Not
            # as gaps either: a WebGL trace of nothing but gaps stops the
            # whole WebGL layer drawing, every strand with it.
            gap = (
                {}
                if lifted
                else {"x": [centre[0], centre[0]], "y": [centre[1], centre[1]]}
            )
            edging.append(
                Moving(
                    **{
                        **spoke,
                        "line": dict(
                            color="white", width=_SPOKE_WIDTH + _EDGING * lift
                        ),
                        **gap,
                    }
                )
            )
            over.append(Moving(**{**spoke, **gap}))
        xs = [trajectories.xy[k][i][0] for k in keys]
        ys = [trajectories.xy[k][i][1] for k in keys]
        carriers = Moving(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(
                size=14,
                color=[colour[k] for k in keys],
                line=dict(color="white", width=1.5),
            ),
            hovertext=[f"{trajectories.label}{k}" for k in keys],
            hoverinfo="text",
            showlegend=False,
        )
        return under + edging + over + [carriers]

    def strand_names(i: int) -> List[dict]:
        """Each strand's name on its carrier, as annotations.

        Not as text on the carriers' trace: text on a WebGL trace can stop
        the whole WebGL layer drawing, strands and all.  Not as a trace of its
        own either: a WebGL layer is painted over every plain trace, so the
        names would sit under the carriers.  Annotations are drawn above both.
        """
        if not show_ids:
            return []
        return [
            dict(
                x=round(float(trajectories.xy[k][i][0]), 4),
                y=round(float(trajectories.xy[k][i][1]), 4),
                text=str(k),
                showarrow=False,
                font=dict(size=8, color="white"),
            )
            for k in keys
        ]

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
    # The side view's traces come after the disk's: the fell, which stays,
    # then the yarns.
    side: list = []
    if braid is not None:
        grey = "#888888"
        braid_colour = {k: colour.get(k, grey) for k in braid.keys}
        side = [braid.fell()]
        after = moving[-1] + 1 + len(side)
        moving += list(range(after, after + len(braid.keys)))

    def frame_traces(i: int) -> list:
        traces: list = [rounded(t) for t in strand_traces(i)]
        if braid is not None:
            carriers = {k: trajectories.xy[k][i] - np.asarray(centre) for k in keys}
            traces += braid.traces(float(times[i]), braid_colour, carriers)
        return traces

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
            data=frame_traces(i),
            traces=moving,
            layout=dict(annotations=strand_names(i)),
            name=str(i),
        )
        for i in samples
    ]
    first = frame_traces(0)
    drawn = 3 * len(keys) + 1
    fig = go.Figure(data=still + first[:drawn] + side + first[drawn:], frames=frames)
    fig.update_layout(annotations=strand_names(0))
    reach = rim * 1.2
    fig.update_layout(
        title=title,
        xaxis=dict(
            range=[centre[0] - reach, centre[0] + reach],
            scaleanchor="y",
            scaleratio=1,
            visible=False,
            domain=[0.0, 0.5] if braid is not None else [0.0, 1.0],
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
    if braid is not None:
        fig.update_layout(scene=braid.scene())
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
    side_view: bool = False,
    yarn_diameter: float = 0.12,
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
        side_view: Also show the braid growing below the disk, from the side.
        yarn_diameter: The yarn's diameter in the side view, the disk's
            radius being 1.
        **kwargs: Passed on to :func:`animate_disk`.

    Returns:
        The figure.
    """
    pattern = kumihimo if isinstance(kumihimo, str) else kumihimo.pattern
    n = n_strands if isinstance(kumihimo, str) else kumihimo.n
    if n is None:
        raise ValueError("A pattern needs n_strands.")
    trajectories = kumihimo_trajectories(
        kumihimo, n_strands, samples_per_step=samples_per_step
    )
    kwargs.setdefault("colors", _hsv_colours(n))
    if side_view:
        n_slots, start, steps = kumihimo_steps(kumihimo, n_strands)
        kwargs.setdefault(
            "braid",
            BraidGrowth(start, steps, n_slots, yarn_diameter, clockwise=False),
        )
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
    side_view: bool = False,
    yarn_diameter: float = 0.12,
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
        side_view: Also show the braid growing below the disk, from the side.
        yarn_diameter: The yarn's diameter in the side view, the disk's
            radius being 1.
        **kwargs: Passed on to :func:`animate_disk`.

    Returns:
        The figure.
    """
    config = getattr(mobidai, "config", mobidai)
    start, steps = mobidai_steps(config, n_cycles, drift)
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
    if side_view:
        kwargs.setdefault(
            "braid",
            BraidGrowth(
                start,
                steps,
                config.n_slots,
                yarn_diameter,
                clockwise=getattr(config, "is_clockwise", True),
            ),
        )
    return animate_disk(
        trajectories,
        step_labels=labels,
        title=title
        or f"Mobidai, {len(config.strands)} strands on {config.n_slots} slots",
        output_html=output_html,
        **kwargs,
    )
