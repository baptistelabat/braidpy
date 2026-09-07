# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/visualization.py
===========================

Interactive Plotly visualizations for horn gear braiding machines.

Three entry points:

- ``visualize_machine``:   Static diagram of gear layout and connections.
- ``visualize_tracks``:    Tracks drawn as circular arcs connecting physical
                           gear-contact points (no straight-line jumps).
- ``animate``:             Smooth sub-step animation showing continuous
                           gear rotation (e.g. quarter-turns for 4-slot gears).

Key geometric conventions
--------------------------
Each gear G has a layout position (cx, cy) and radius r.
When two gears G and H are connected, their physical contact point lies on
the line segment between their centres, at distance r_G from G and r_H from H.
From G's centre the contact is at angle  ``theta_GH = atan2(y_H-y_G, x_H-x_G)``.

The gear rotation offset ``phi_G`` orients the gear so that its connection
slot(s) align with those angles.  All slot angles in the visualisation are
computed as::

    angle(slot, t, frac) = phi_G + 2π*(slot + dir_G*(t+frac)) / N_G
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go

from .layout import compute_layout, gear_radii
from .model import BraidingMachine
from .simulation import CollisionError, MachineState, load_carriers, simulate
from .tracks import Track, compute_tracks

_PALETTE = [
    "#e41a1c",
    "#377eb8",
    "#4daf4a",
    "#984ea3",
    "#ff7f00",
    "#a65628",
    "#f781bf",
    "#999999",
    "#66c2a5",
    "#fc8d62",
    "#8da0cb",
    "#e78ac3",
]


# ── Geometry helpers ───────────────────────────────────────────────────────────


def _contact_angle(
    layout: Dict[str, Tuple[float, float]], gear: str, neighbor: str
) -> float:
    """Angle (rad) from gear's centre toward neighbor's centre – the contact direction."""
    cx, cy = layout[gear]
    nx, ny = layout[neighbor]
    return math.atan2(ny - cy, nx - cx)


def _gear_constraints(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, List[float]]:
    """Per gear, the rotation offset each of its connections asks for.

    A connection ``gear_a[slot_a0] ↔ gear_b[slot_b0]`` wants slot ``slot_a0`` of
    gear_a to point at gear_b, i.e. ``phi_a = theta_ab - 2π*slot_a0/N_a``.  A
    gear with several connections gets one such value per connection; they all
    agree only when the connection slots match the physical layout.
    """
    wanted: Dict[str, List[float]] = {name: [] for name in machine.gears}
    for conn in machine.connections:
        for gname, other, slot0 in [
            (conn.gear_a, conn.gear_b, conn.slot_a0),
            (conn.gear_b, conn.gear_a, conn.slot_b0),
        ]:
            gear = machine.gears[gname]
            theta = _contact_angle(layout, gname, other)
            wanted[gname].append(theta - 2 * math.pi * slot0 / gear.n_slots)
    return wanted


def _compute_offsets(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, float]:
    """Per-gear rotation offset phi so connection slots point toward their neighbors.

    Every connection of a gear is taken into account, via the circular mean of
    the offsets they each ask for.  When the machine's connection slots match
    its layout the requests coincide and the mean reproduces them exactly; when
    they do not, the residual error is shared between the contacts instead of
    being dumped entirely onto whichever connection happened to come second.
    """
    offsets: Dict[str, float] = {}
    for name, wanted in _gear_constraints(machine, layout).items():
        if not wanted:
            offsets[name] = 0.0
            continue
        sin_sum = sum(math.sin(a) for a in wanted)
        cos_sum = sum(math.cos(a) for a in wanted)
        # Degenerate: requests cancel out (e.g. exactly opposed).  The mean is
        # meaningless there, so honour the first connection rather than spin.
        if math.hypot(sin_sum, cos_sum) < 1e-9:
            offsets[name] = wanted[0]
        else:
            offsets[name] = math.atan2(sin_sum, cos_sum)
    return offsets


def _offset_residuals(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
) -> Dict[str, float]:
    """Worst angular error (radians) between each gear's slots and its contacts.

    Zero means every contact of that gear falls exactly on a slot.  A non-zero
    value means the machine's connection slots cannot be reconciled with its
    layout, and carriers will appear to jump when they transfer there.
    """
    offsets = _compute_offsets(machine, layout)
    residuals: Dict[str, float] = {}
    for name, wanted in _gear_constraints(machine, layout).items():
        phi = offsets[name]
        residuals[name] = max(
            (abs((a - phi + math.pi) % (2 * math.pi) - math.pi) for a in wanted),
            default=0.0,
        )
    return residuals


def _slot_angle(
    slot: int,
    n_slots: int,
    direction: int,
    offset: float,
    t: int = 0,
    frac: float = 0.0,
) -> float:
    """Physical angle (rad) of a slot at continuous time t+frac."""
    return offset + 2 * math.pi * (slot + direction * (t + frac)) / n_slots


def _arc_xy(
    cx: float,
    cy: float,
    r: float,
    theta_start: float,
    theta_end: float,
    direction: int,
    n_points: int = 60,
) -> Tuple[np.ndarray, np.ndarray]:
    """Arc on a circle from theta_start to theta_end following rotation direction.

    direction +1 → CCW (angle increases), -1 → CW (angle decreases).
    Handles the wraparound so the arc always goes the "short" angular distance
    in the rotation direction (which may be > π, e.g. for single-connection gears).
    """
    if direction > 0:  # CCW: need theta_end > theta_start
        while theta_end <= theta_start:
            theta_end += 2 * math.pi
    else:  # CW: need theta_end < theta_start
        while theta_end >= theta_start:
            theta_end -= 2 * math.pi
    angles = np.linspace(theta_start, theta_end, n_points)
    return cx + r * np.cos(angles), cy + r * np.sin(angles)


# ── Track run decomposition ────────────────────────────────────────────────────


def _track_runs(
    track: Track,
) -> List[Tuple[str, str, str]]:
    """Decompose a cyclic track into (gear, prev_gear, next_gear) run descriptors.

    A "run" is a maximal consecutive sub-sequence of the (cyclic) track that
    stays on the same gear.  For each run we only need to know which gear the
    carrier came from (prev_gear) and which it goes to (next_gear), because
    the arc is drawn entirely from the incoming contact point to the outgoing
    contact point on the circumference of the current gear.

    Returns a list of (gear_name, prev_gear_name, next_gear_name) tuples.
    """
    n = len(track)
    if n == 0:
        return []

    # Find transfer positions (where gear changes between step i and step i+1)
    transfers = [i for i in range(n) if track[i][0] != track[(i + 1) % n][0]]

    if not transfers:
        # Single-gear track – unusual but handled: one run, no neighbour info.
        # Draw a full circle (dummy prev/next = same gear).
        return [(track[0][0], track[0][0], track[0][0])]

    # Build runs starting from the position right after the first transfer.
    runs: List[Tuple[str, str, str]] = []
    # Each transfer[k] ends the k-th run; the run starts at transfers[k-1]+1.
    m = len(transfers)
    for k in range(m):
        # Run k goes from just after transfers[k-1] up to and including transfers[k].
        prev_transfer = transfers[(k - 1) % m]
        this_transfer = transfers[k]
        gear_name = track[(prev_transfer + 1) % n][0]
        prev_gear = track[prev_transfer][0]  # gear we came from
        next_gear = track[(this_transfer + 1) % n][0]  # gear we go to
        runs.append((gear_name, prev_gear, next_gear))

    return runs


# ── Static machine traces ──────────────────────────────────────────────────────


def _gear_traces(
    cx: float,
    cy: float,
    r: float,
    name: str,
    n_slots: int,
    direction: int,
    offset: float,
    t: int = 0,
    frac: float = 0.0,
) -> List[go.BaseTraceType]:
    """Disk, rotating tick marks and centre label for one gear."""
    traces: List[go.BaseTraceType] = []
    theta = np.linspace(0, 2 * math.pi, 120)

    # Disk circle
    traces.append(
        go.Scatter(
            x=cx + r * np.cos(theta),
            y=cy + r * np.sin(theta),
            fill="toself",
            fillcolor="rgba(100,100,200,0.10)",
            line=dict(color="rgba(80,80,180,0.50)", width=1.5),
            mode="lines",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Tick marks – rotate with the gear
    tick_len = r * 0.15
    tick_xs: List = []
    tick_ys: List = []
    for slot in range(n_slots):
        ang = _slot_angle(slot, n_slots, direction, offset, t, frac)
        x0 = cx + (r - tick_len) * math.cos(ang)
        y0 = cy + (r - tick_len) * math.sin(ang)
        x1 = cx + r * math.cos(ang)
        y1 = cy + r * math.sin(ang)
        tick_xs += [x0, x1, None]
        tick_ys += [y0, y1, None]
    traces.append(
        go.Scatter(
            x=tick_xs,
            y=tick_ys,
            mode="lines",
            line=dict(color="rgba(80,80,180,0.60)", width=1.2),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Centre label
    arrow = "↺" if direction == 1 else "↻"
    traces.append(
        go.Scatter(
            x=[cx],
            y=[cy],
            mode="text",
            text=[f"<b>{name}</b><br>{n_slots}s {arrow}"],
            textposition="middle center",
            showlegend=False,
            hoverinfo="skip",
            textfont=dict(size=11),
        )
    )
    return traces


def _connection_traces(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    radii: Dict[str, float],
) -> List[go.BaseTraceType]:
    traces = []
    for conn in machine.connections:
        cx_a, cy_a = layout[conn.gear_a]
        cx_b, cy_b = layout[conn.gear_b]
        dx = cx_b - cx_a
        dy = cy_b - cy_a
        dist = math.hypot(dx, dy) or 1.0
        ex_a = cx_a + radii[conn.gear_a] * dx / dist
        ey_a = cy_a + radii[conn.gear_a] * dy / dist
        ex_b = cx_b - radii[conn.gear_b] * dx / dist
        ey_b = cy_b - radii[conn.gear_b] * dy / dist
        label = conn.name or f"{conn.gear_a}↔{conn.gear_b}"
        traces.append(
            go.Scatter(
                x=[ex_a, ex_b],
                y=[ey_a, ey_b],
                mode="lines+text",
                line=dict(color="rgba(80,80,80,0.35)", width=2, dash="dash"),
                text=["", label],
                textposition="top center",
                showlegend=False,
                hoverinfo="skip",
            )
        )
    return traces


def _contact_point_traces(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    radii: Dict[str, float],
) -> List[go.BaseTraceType]:
    """X marker at each physical contact point (tangent between gear circles)."""
    xs, ys, labels = [], [], []
    for conn in machine.connections:
        cx_a, cy_a = layout[conn.gear_a]
        cx_b, cy_b = layout[conn.gear_b]
        dx = cx_b - cx_a
        dy = cy_b - cy_a
        dist = math.hypot(dx, dy) or 1.0
        r_a = radii[conn.gear_a]
        xs.append(cx_a + r_a * dx / dist)
        ys.append(cy_a + r_a * dy / dist)
        labels.append(conn.name or f"{conn.gear_a}↔{conn.gear_b}")
    return [
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(
                size=14,
                symbol="x",
                color="rgba(220,80,0,0.90)",
                line=dict(width=2.5, color="rgba(180,60,0,0.90)"),
            ),
            text=labels,
            hoverinfo="text",
            name="Contact points",
            showlegend=False,
        )
    ]


# ── Public API ─────────────────────────────────────────────────────────────────


def visualize_machine(
    machine: BraidingMachine,
    scale: float = 1.0,
    output_html: Optional[str] = None,
    title: str = "Horn Gear Braiding Machine",
) -> go.Figure:
    """Static diagram of the machine layout with oriented slot tick marks."""
    layout = compute_layout(machine, scale=scale)
    radii = gear_radii(machine, scale=scale)
    offsets = _compute_offsets(machine, layout)

    traces: List[go.BaseTraceType] = []
    traces.extend(_connection_traces(machine, layout, radii))
    traces.extend(_contact_point_traces(machine, layout, radii))

    for name, gear in machine.gears.items():
        cx, cy = layout[name]
        r = radii[name]
        phi = offsets[name]
        traces.extend(_gear_traces(cx, cy, r, name, gear.n_slots, gear.direction, phi))

        # Slot dots at their oriented positions
        xs, ys, labels = [], [], []
        for s in range(gear.n_slots):
            ang = _slot_angle(s, gear.n_slots, gear.direction, phi)
            xs.append(cx + r * math.cos(ang))
            ys.append(cy + r * math.sin(ang))
            labels.append(f"{name}[{s}]")
        traces.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers",
                marker=dict(
                    size=7,
                    color="rgba(60,60,60,0.55)",
                    line=dict(width=1, color="white"),
                ),
                text=labels,
                hoverinfo="text",
                showlegend=False,
            )
        )

    fig = go.Figure(data=traces)
    fig.update_layout(
        title=title,
        xaxis=dict(
            scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, visible=False
        ),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
        plot_bgcolor="white",
        margin=dict(l=20, r=20, t=60, b=20),
        hovermode="closest",
    )
    if output_html:
        fig.write_html(output_html)
    return fig


def visualize_tracks(
    machine: BraidingMachine,
    tracks: Optional[List[Track]] = None,
    scale: float = 1.0,
    output_html: Optional[str] = None,
    title: str = "Carrier Tracks",
) -> go.Figure:
    """Draw carrier tracks as circular arcs that meet at physical contact points.

    For each run of consecutive positions on the same gear, the arc runs from
    the physical contact point with the incoming gear to the physical contact
    point with the outgoing gear, following the gear's rotation direction.
    Gear transfers happen exactly at the tangent point between gear
    circumferences – no jump lines.

    Args:
        machine: The machine to visualise.
        tracks: Precomputed tracks (computed if None).
        scale: Layout scale.
        output_html: If given, write figure to this HTML file path.
        title: Figure title.

    Returns:
        Plotly Figure.
    """
    if tracks is None:
        tracks = compute_tracks(machine)

    fig = visualize_machine(machine, scale=scale, title=title)
    layout = compute_layout(machine, scale=scale)
    radii = gear_radii(machine, scale=scale)

    for ti, track in enumerate(tracks):
        color = _PALETTE[ti % len(_PALETTE)]
        runs = _track_runs(track)

        xs_all: List = []
        ys_all: List = []

        for gear_name, prev_gear, next_gear in runs:
            cx, cy = layout[gear_name]
            r = radii[gear_name]
            direction = machine.gears[gear_name].direction

            # Arc goes FROM incoming contact TO outgoing contact.
            # Contact with prev_gear: angle from gear_name toward prev_gear.
            theta_in = _contact_angle(layout, gear_name, prev_gear)
            # Contact with next_gear: angle from gear_name toward next_gear.
            theta_out = _contact_angle(layout, gear_name, next_gear)

            xs, ys = _arc_xy(cx, cy, r, theta_in, theta_out, direction)
            xs_all.extend(xs.tolist())
            ys_all.extend(ys.tolist())

        # Close the curve
        if xs_all:
            xs_all.append(xs_all[0])
            ys_all.append(ys_all[0])

        fig.add_trace(
            go.Scatter(
                x=xs_all,
                y=ys_all,
                mode="lines",
                line=dict(color=color, width=2.5),
                name=f"Track {ti}  (len={len(track)})",
                hoverinfo="skip",
            )
        )

    if output_html:
        fig.write_html(output_html)
    return fig


def animate(
    machine: BraidingMachine,
    n_steps: int,
    carrier_positions: Optional[Dict] = None,
    scale: float = 1.0,
    output_html: Optional[str] = None,
    title: str = "Carrier Animation",
    frame_duration_ms: int = 40,
    n_substeps: int = 9,
) -> go.Figure:
    """Animate carriers with smooth gear rotation between simulation steps.

    Each simulation step is split into ``n_substeps`` intermediate frames.
    Carrier and tick-mark positions are interpolated so a 4-slot gear shows
    a smooth 90° (quarter-turn) rotation per step.

    Args:
        machine: The machine definition.
        n_steps: Number of simulation steps to animate.
        carrier_positions: Optional initial carrier placement.
        scale: Layout scale.
        output_html: If given, write figure to this HTML file path.
        title: Figure title.
        frame_duration_ms: Duration of each sub-frame in ms.
        n_substeps: Intermediate frames per simulation step.

    Returns:
        Plotly Figure with animation frames.
    """
    layout_pos = compute_layout(machine, scale=scale)
    radii_dict = gear_radii(machine, scale=scale)
    offsets = _compute_offsets(machine, layout_pos)
    if carrier_positions is None:
        carrier_positions = load_carriers(machine)

    collision_info: Optional[CollisionError] = None
    try:
        history = simulate(machine, n_steps, carrier_positions)
    except CollisionError as e:
        collision_info = e
        history = e.history
        n_steps = len(history) - 1  # animate only the valid steps

    if collision_info is not None:
        coll_detail = "; ".join(
            f"{g}[{s}]: C{ids}" for (g, s), ids in collision_info.collisions.items()
        )
        title = f"{title} — COLLISION at step {collision_info.step} ({coll_detail})"

    # Warn when the machine's connection slots cannot be reconciled with its
    # layout: carriers then visibly jump as they transfer.  That is a property
    # of the machine definition, not of the animation.
    worst = max(_offset_residuals(machine, layout_pos).values(), default=0.0)
    if math.degrees(worst) > 1.0:
        title = (
            f"{title}<br><sub>slots miss their contacts by up to "
            f"{math.degrees(worst):.0f}° — carriers jump when transferring</sub>"
        )

    carrier_colors = {
        c.carrier_id: _PALETTE[i % len(_PALETTE)]
        for i, c in enumerate(history[0].carriers)
    }

    # A carrier rides in a horn of its gear, so its angle is simply that slot's
    # angle — the very same ``_slot_angle`` used to draw the tick marks.  It
    # therefore turns at exactly the gear's rate and always sits on its slot.
    #
    # Transfers stay continuous without any special casing: a carrier moves to
    # the neighbour only at the step where its slot is at the contact point, and
    # it lands on the neighbour's slot that is at that same contact point at that
    # same instant, so the two coincide (provided the machine's connection slots
    # match its layout — see ``_offset_residuals``).

    def _build(state: MachineState, frac: float) -> List[go.BaseTraceType]:
        t = state.time
        out: List[go.BaseTraceType] = []
        out.extend(_connection_traces(machine, layout_pos, radii_dict))
        out.extend(_contact_point_traces(machine, layout_pos, radii_dict))
        for name, gear in machine.gears.items():
            cx, cy = layout_pos[name]
            r = radii_dict[name]
            out.extend(
                _gear_traces(
                    cx,
                    cy,
                    r,
                    name,
                    gear.n_slots,
                    gear.direction,
                    offsets[name],
                    t,
                    frac,
                )
            )

        xs, ys, htexts, colors_list, texts = [], [], [], [], []
        for c in state.carriers:
            gear = machine.gears[c.gear]
            cx, cy = layout_pos[c.gear]
            r = radii_dict[c.gear]

            ang = _slot_angle(
                c.slot, gear.n_slots, gear.direction, offsets[c.gear], t, frac
            )

            xs.append(cx + r * math.cos(ang))
            ys.append(cy + r * math.sin(ang))
            htexts.append(f"C{c.carrier_id} @ {c.gear}[{c.slot}]")
            colors_list.append(carrier_colors[c.carrier_id])
            texts.append(str(c.carrier_id))

        out.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                marker=dict(
                    size=14, color=colors_list, line=dict(width=1.5, color="white")
                ),
                text=texts,
                textposition="middle center",
                textfont=dict(size=9, color="white"),
                hovertext=htexts,
                hoverinfo="text",
                name="Carriers",
                showlegend=False,
            )
        )
        return out

    frames: List[go.Frame] = []
    frame_names: List[str] = []

    for t_idx in range(n_steps):
        state = history[t_idx]
        for k in range(n_substeps):
            fname = f"{t_idx}_{k}"
            frames.append(go.Frame(data=_build(state, k / n_substeps), name=fname))
            frame_names.append(fname)

    final_name = f"{n_steps}_0"
    frames.append(go.Frame(data=_build(history[n_steps], 0.0), name=final_name))
    frame_names.append(final_name)

    fig = go.Figure(data=_build(history[0], 0.0), frames=frames)
    fig.update_layout(
        title=title,
        xaxis=dict(
            scaleanchor="y", scaleratio=1, showgrid=False, zeroline=False, visible=False
        ),
        yaxis=dict(showgrid=False, zeroline=False, visible=False),
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
                            [fn],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                            },
                        ],
                        label=str(i),
                        method="animate",
                    )
                    for i, fn in enumerate(frame_names)
                ],
                active=0,
                y=0,
                x=0,
                xanchor="left",
                len=1.0,
                currentvalue=dict(prefix="Frame: ", visible=True, xanchor="center"),
                transition=dict(duration=0),
            )
        ],
    )

    if output_html:
        fig.write_html(output_html)
    return fig
