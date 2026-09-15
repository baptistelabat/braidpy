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
Each gear G has a layout position (cx, cy) and radius r.  Two connected gears
meet at a *notch*: for tangent gears that is the single point where they touch,
and for gears that interpenetrate it is the middle of the chord between the two
places their circles cross.  Either way it lies on the line between the two
centres, and a carrier rides at that distance from its gear's centre — on the
rim when the gears merely touch, inside it when they overlap.

The rotation offset ``phi_G`` turns each gear so its connection slots point at
its notches, fitted across all of them (:func:`slot_offsets`); where a
machine's slots cannot be reconciled with its layout, :func:`offset_residuals`
says by how much and the figure is labelled with it.

Nothing here decides how far a gear has turned, where a carrier goes next, or
which gear is carrying it — those belong to the machine, so that an ordinary
braider and a programme-driven lace machine can both be drawn by this code
without it knowing the difference.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Tuple

import numpy as np
import plotly.graph_objects as go

from .layout import (
    axial_clearance,
    axial_position,
    carrier_radius,
    compute_layout,
    contact_angle,
    contact_point,
    gear_radii,
    offset_residuals,
    slot_offsets,
)
from .model import BraidingMachine
from .simulation import CollisionError, MachineState, simulate
from .tracks import Track, compute_tracks

# Which way a gear is turning, at a glance: green clockwise, red the other
# way, grey standing still.  An ordinary machine turns every gear every step,
# so its colours show the alternation its braid depends on; a machine driven
# gear by gear greys out whatever its programme is holding.
# How far in a slot's radial mark reaches, as a fraction of the gear radius.
# It stops here rather than at the centre so the gear's label stays clear.
_SLOT_MARK_INNER = 0.38

# A bobbin sits in its notch, a little smaller than the notch itself.
_BOBBIN_FILL = 0.82

# Plot width the bobbin sizing is worked out against, in pixels.
_NOMINAL_PLOT_PX = 700

# How strongly the track channels show through behind the machine.
_TRACK_OPACITY = 0.28

_GEAR_COLOURS = {
    "clockwise": ("rgba(60,170,90,0.20)", "rgba(35,135,65,0.85)"),
    "trigonometric": ("rgba(205,60,55,0.16)", "rgba(165,40,35,0.80)"),
    "held": ("rgba(140,140,140,0.14)", "rgba(110,110,110,0.65)"),
}

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


def _gear_state(direction: int, turning: bool) -> str:
    """Which of the three gear colours applies: the way it turns, or held."""
    if not turning:
        return "held"
    return "clockwise" if direction == -1 else "trigonometric"


# ── Geometry helpers ───────────────────────────────────────────────────────────


def _slot_angle(
    machine: BraidingMachine,
    gear_name: str,
    slot: int,
    offset: float,
    t: int = 0,
    frac: float = 0.0,
) -> float:
    """Physical angle (rad) of a slot at continuous time t+frac.

    How far the gear has turned by then is the machine's business — it is
    ``direction * t`` on an ordinary machine and whatever the programme says
    on a Jacquard one — so this only adds the layout offset on top.
    """
    return offset + machine.slot_angle(gear_name, slot, t, frac)


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


def _notch_radius(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    radii: Dict[str, float],
    gear: str,
    scale: float = 1.0,
) -> float:
    """Radius of the notch cut for one slot, in layout units.

    Big enough to read, but never more than a third of the gap between
    neighbouring slots, so the notches of a many-slotted gear stay apart.
    """
    seat = carrier_radius(machine, layout, gear, scale)
    n_slots = machine.gears[gear].n_slots
    return min(radii[gear] * 0.16, 2 * math.pi * seat / n_slots * 0.34)


def _carrier_marker_sizes(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    radii: Dict[str, float],
    scale: float = 1.0,
) -> Dict[str, float]:
    """Marker size per gear, in points, so a bobbin sits snugly in its notch.

    Plotly sizes markers in pixels while the notches are in layout units, so
    the ratio is worked out against the machine's own extent and scaled by a
    nominal plot width.  It is approximate — a reader who zooms will see the
    bobbin and its notch drift apart — but it keeps a bobbin looking like a
    bobbin in its seat across machines of very different sizes, which a fixed
    pixel size cannot.
    """
    xs = [layout[n][0] for n in machine.gears]
    ys = [layout[n][1] for n in machine.gears]
    margin = max(radii.values())
    span = max(max(xs) - min(xs), max(ys) - min(ys)) + 2 * margin

    return {
        name: _NOMINAL_PLOT_PX
        * (2 * _notch_radius(machine, layout, radii, name, scale) * _BOBBIN_FILL)
        / span
        for name in machine.gears
    }


def _track_traces(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    tracks: Optional[List[Track]] = None,
    scale: float = 1.0,
    width: float = 2.5,
    opacity: float = 1.0,
) -> List[go.BaseTraceType]:
    """Each carrier track as a closed run of arcs, one trace per track.

    A run of positions on the same gear is drawn as a single arc from the notch
    the carrier came in by to the one it leaves by, following the gear's
    rotation, at the radius the carriers actually ride at — so the tracks lie
    under the carriers rather than beside them.

    Tracks belong to the wiring, so they are the same at every step and can be
    drawn once and left alone.  A machine driven by a programme has none, and
    gets an empty list.
    """
    if not machine.has_fixed_tracks:
        return []
    if tracks is None:
        tracks = compute_tracks(machine)

    radii = {
        name: carrier_radius(machine, layout, name, scale) for name in machine.gears
    }

    # Several carrier cycles can run round the same loop of gears, offset from
    # one another by a slot.  The drawn arc depends only on which gears the
    # carrier crosses, so those cycles come out as the same closed curve: draw
    # it once.  A square braid has four cycles but only the two paths — one
    # each way round the ring — that its counter-rotating braid is made of.
    paths: Dict[Tuple[Tuple[str, str, str], ...], None] = {}
    for track in tracks:
        runs = tuple(_track_runs(track))
        if not runs:
            continue
        # Same loop entered at a different gear is still the same loop.
        paths.setdefault(min(runs[i:] + runs[:i] for i in range(len(runs))), None)

    traces: List[go.BaseTraceType] = []
    for index, runs in enumerate(paths):
        xs_all: List = []
        ys_all: List = []
        for gear_name, prev_gear, next_gear in runs:
            cx, cy = layout[gear_name]
            xs, ys = _arc_xy(
                cx,
                cy,
                radii[gear_name],
                contact_angle(machine, layout, gear_name, prev_gear, scale),
                contact_angle(machine, layout, gear_name, next_gear, scale),
                machine.gears[gear_name].direction,
            )
            xs_all.extend(xs.tolist())
            ys_all.extend(ys.tolist())

        xs_all.append(xs_all[0])  # close the loop
        ys_all.append(ys_all[0])

        # Name the curve by the loop of gears it runs round.  Counting the
        # tracks that fall on it would be misleading: a track can be walked
        # either way, so which of the two curves it lands on depends only on
        # the slot its computation happened to start from.
        label = "Track " + "-".join(gear for gear, _, _ in runs)
        traces.append(
            go.Scatter(
                x=xs_all,
                y=ys_all,
                mode="lines",
                line=dict(color=_PALETTE[index % len(_PALETTE)], width=width),
                opacity=opacity,
                name=label,
                hoverinfo="skip",
            )
        )
    return traces


def _gear_traces(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    radii: Dict[str, float],
    offsets: Dict[str, float],
    t: int = 0,
    frac: float = 0.0,
    scale: float = 1.0,
) -> List[go.BaseTraceType]:
    """Discs, tick marks and labels for *all* the gears, in a handful of traces.

    Every gear could have its own traces, but a real lace machine has dozens of
    them and a trace per gear per frame makes an animation crawl.  Plotly draws
    a separate polygon for each ``None``-separated run, so all the discs that
    share a colour go in one trace, all the ticks in another, all the labels in
    a third — a fixed handful however many gears there are.

    Discs are coloured green while a gear turns and red while it is held, but
    only for a machine driven gear by gear: one whose gears are geared together
    is always turning, so saying so would say nothing.
    """
    turning = machine.turning_gears(t)
    theta = np.linspace(0, 2 * math.pi, 90)

    traces: List[go.BaseTraceType] = []

    # One trace per gear, always in the same order.  Plotly matches traces
    # between frames by position, so a gear must keep its own trace: batching
    # the discs by colour would put different gears in the same slot from one
    # frame to the next and the circles would appear to fly about.  Only the
    # fill changes; the geometry is identical every frame.
    for name in machine.gears:
        cx, cy = layout[name]
        r = radii[name]
        fill, edge = _GEAR_COLOURS[
            _gear_state(machine.gears[name].direction, name in turning)
        ]
        traces.append(
            go.Scatter(
                x=cx + r * np.cos(theta),
                y=cy + r * np.sin(theta),
                fill="toself",
                fillcolor=fill,
                line=dict(color=edge, width=1.8),
                mode="lines",
                showlegend=False,
                hoverinfo="skip",
            )
        )

    # Slots, drawn as what they are: a rounded notch cut into the rim with a
    # radial mark through it, so they stay legible as the gear turns.  Notch
    # and mark share one trace, separated by None, which keeps the number of
    # traces fixed however many slots a machine has.
    slot_xs: List = []
    slot_ys: List = []
    for name, gear in machine.gears.items():
        cx, cy = layout[name]
        rim = radii[name]
        seat = carrier_radius(machine, layout, name, scale)
        notch = _notch_radius(machine, layout, radii, name, scale)

        for slot in range(gear.n_slots):
            angle = _slot_angle(machine, name, slot, offsets[name], t, frac)
            px = cx + seat * math.cos(angle)
            py = cy + seat * math.sin(angle)

            # The half facing into the gear: the cut itself.
            arc = np.linspace(angle + math.pi / 2, angle + 3 * math.pi / 2, 24)
            slot_xs.extend((px + notch * np.cos(arc)).tolist() + [None])
            slot_ys.extend((py + notch * np.sin(arc)).tolist() + [None])

            # A radial mark running inward from the notch, stopping short of
            # the middle so it does not cross the gear's label.
            slot_xs += [px, cx + rim * _SLOT_MARK_INNER * math.cos(angle), None]
            slot_ys += [py, cy + rim * _SLOT_MARK_INNER * math.sin(angle), None]

    traces.append(
        go.Scatter(
            x=slot_xs,
            y=slot_ys,
            mode="lines",
            line=dict(color="rgba(70,70,160,0.75)", width=1.4),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    traces.append(
        go.Scatter(
            x=[layout[n][0] for n in machine.gears],
            y=[layout[n][1] for n in machine.gears],
            mode="text",
            text=[
                f"<b>{n}</b><br>{g.n_slots}s {'↺' if g.direction == 1 else '↻'}"
                for n, g in machine.gears.items()
            ],
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
    """Dashed link and label for every connection, batched into two traces.

    A lace machine has dozens of connections and this is redrawn every frame,
    so all the links go in one ``None``-separated trace and all the labels in
    another, rather than a pair of traces per connection.
    """
    xs: List = []
    ys: List = []
    label_x, label_y, labels = [], [], []
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
        xs += [ex_a, ex_b, None]
        ys += [ey_a, ey_b, None]
        label_x.append(ex_b)
        label_y.append(ey_b)
        labels.append(conn.name or f"{conn.gear_a}↔{conn.gear_b}")

    return [
        go.Scatter(
            x=xs,
            y=ys,
            mode="lines",
            line=dict(color="rgba(80,80,80,0.35)", width=2, dash="dash"),
            showlegend=False,
            hoverinfo="skip",
        ),
        go.Scatter(
            x=label_x,
            y=label_y,
            mode="text",
            text=labels,
            textposition="top center",
            showlegend=False,
            hoverinfo="skip",
        ),
    ]


def _axial_traces(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
) -> List[go.BaseTraceType]:
    """Column marker for each axial — a ring with a dot, the column end-on.

    Axials never move, so the same marker is drawn in every animation frame.
    """
    if not machine.axials:
        return []
    xs, ys, labels = [], [], []
    for axial in machine.axials:
        x, y = axial_position(machine, layout, axial)
        xs.append(x)
        ys.append(y)
        clear = axial_clearance(machine, layout, (x, y))
        labels.append(
            f"{axial.name}<br>anchor: {'-'.join(axial.anchor)}"
            f"<br>clearance: {clear:.2f}"
        )
    return [
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(
                size=17,
                symbol="circle-open-dot",
                color="rgba(150,105,30,0.95)",
                line=dict(width=2.5, color="rgba(150,105,30,0.95)"),
            ),
            text=labels,
            hoverinfo="text",
            name="Axials",
            showlegend=False,
        )
    ]


def _punchcard_traces(
    machine: BraidingMachine,
    layout: Dict[str, Tuple[float, float]],
    radii: Dict[str, float],
    current_phase: Optional[int] = None,
) -> List[go.BaseTraceType]:
    """Draw the machine's programme below it, as the punchcard it is.

    One column per gear and one row per phase, read downwards.  A punched hole
    means that gear is let turn; an unpunched position means it is held.  The
    clockwise row of each step is shifted half a punch to the right of its
    trigonometric partner, because the two are driven one after the other
    rather than together.

    Returns an empty list for a machine that has no programme.
    """
    rows = machine.program_rows()
    if not rows:
        return []

    names = list(machine.gears)
    xs_gear = [layout[n][0] for n in names]
    ys_gear = [layout[n][1] for n in names]
    span = max(max(xs_gear) - min(xs_gear), 1.0) + 2 * max(radii.values())
    dx = span / max(len(names), 1)
    dy = dx * 0.62
    x0 = (min(xs_gear) + max(xs_gear)) / 2 - (len(names) - 1) * dx / 2 - dx / 4
    y0 = min(ys_gear) - max(radii.values()) - dy * 2.0

    # Every punch keeps its own place in one trace, with colour, symbol and
    # size carried per point.  Splitting them into "lit" and "unlit" traces
    # would shuffle which punch sits at which index from frame to frame, and
    # Plotly — which pairs traces up by index — would slide them about.
    xs: List[float] = []
    ys: List[float] = []
    colors: List[str] = []
    symbols: List[str] = []
    sizes: List[int] = []
    hovers: List[str] = []

    for row_index, (label, flags) in enumerate(rows):
        shift = dx / 2 if label == "clockwise" else 0.0
        y = y0 - row_index * dy
        live = row_index == current_phase
        for column, (name, on) in enumerate(zip(names, flags)):
            xs.append(x0 + column * dx + shift)
            ys.append(y)
            if not on:
                colors.append("rgba(150,150,150,0.45)")
                symbols.append("circle-open")
                sizes.append(7)
            elif live:
                colors.append("rgba(35,135,65,0.95)")
                symbols.append("circle")
                sizes.append(12)
            else:
                colors.append("rgba(45,45,45,0.85)")
                symbols.append("circle")
                sizes.append(9)
            hovers.append(
                f"step {row_index // 2} · {label}<br>{name} {'turns' if on else 'held'}"
            )

    traces: List[go.BaseTraceType] = [
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(
                size=sizes,
                color=colors,
                symbol=symbols,
                line=dict(width=1, color="rgba(255,255,255,0.8)"),
            ),
            text=hovers,
            hoverinfo="text",
            name="Programme",
            showlegend=False,
        )
    ]

    # Row labels, with an arrow on the row being driven.
    traces.append(
        go.Scatter(
            x=[x0 - dx * 0.85] * len(rows),
            y=[y0 - i * dy for i in range(len(rows))],
            mode="text",
            text=[
                f"{'▶ ' if i == current_phase else ''}{i // 2}"
                f"{'↺' if label == 'trigonometric' else '↻'}"
                for i, (label, _) in enumerate(rows)
            ],
            textposition="middle left",
            textfont=dict(size=9, color="rgba(90,90,90,0.9)"),
            showlegend=False,
            hoverinfo="skip",
        )
    )

    # Gear names across the top of the card.
    traces.append(
        go.Scatter(
            x=[x0 + i * dx for i in range(len(names))],
            y=[y0 + dy * 0.8] * len(names),
            mode="text",
            text=names,
            textfont=dict(size=9, color="rgba(90,90,90,0.9)"),
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
    """X marker at each notch where two gear circles meet."""
    xs, ys, labels = [], [], []
    for conn in machine.connections:
        x, y = contact_point(machine, layout, conn.gear_a, conn.gear_b)
        xs.append(x)
        ys.append(y)
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


def visualize_machine(
    machine: BraidingMachine,
    scale: float = 1.0,
    output_html: Optional[str] = None,
    title: str = "Horn Gear Braiding Machine",
) -> go.Figure:
    """Static diagram of the machine layout with oriented slot tick marks."""
    layout = compute_layout(machine, scale=scale)
    radii = gear_radii(machine, scale=scale)
    offsets = slot_offsets(machine, layout)

    traces: List[go.BaseTraceType] = []
    traces.extend(_connection_traces(machine, layout, radii))
    traces.extend(_contact_point_traces(machine, layout, radii))
    traces.extend(_gear_traces(machine, layout, radii, offsets, scale=scale))

    # Slot dots, in the notches the bobbins ride in.
    seat_sizes = _carrier_marker_sizes(machine, layout, radii, scale)
    xs, ys, labels, dot_sizes = [], [], [], []
    for name, gear in machine.gears.items():
        cx, cy = layout[name]
        r_carrier = carrier_radius(machine, layout, name, scale)
        for s in range(gear.n_slots):
            ang = _slot_angle(machine, name, s, offsets[name])
            xs.append(cx + r_carrier * math.cos(ang))
            ys.append(cy + r_carrier * math.sin(ang))
            labels.append(f"{name}[{s}]")
            dot_sizes.append(seat_sizes[name] * 0.55)
    traces.append(
        go.Scatter(
            x=xs,
            y=ys,
            mode="markers",
            marker=dict(
                size=dot_sizes,
                color="rgba(60,60,60,0.55)",
                line=dict(width=1, color="white"),
            ),
            text=labels,
            hoverinfo="text",
            showlegend=False,
        )
    )

    traces.extend(_axial_traces(machine, layout))
    traces.extend(_punchcard_traces(machine, layout, radii))

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

    for trace in _track_traces(machine, layout, tracks, scale):
        fig.add_trace(trace)

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
    offsets = slot_offsets(machine, layout_pos)
    bobbin_sizes = _carrier_marker_sizes(machine, layout_pos, radii_dict, scale)

    # The tracks are a property of the wiring, so they are identical in
    # every frame: build them once and hand the same traces to each.
    #
    # Drawn as wide as a bobbin, so a track reads as the channel its carriers
    # run along rather than a hairline beside them, and faint enough to stay
    # behind everything else.  The narrowest bobbin sets the width, so the
    # band never grows wider than the notches it threads.
    track_traces = _track_traces(
        machine,
        layout_pos,
        scale=scale,
        width=min(bobbin_sizes.values()),
        opacity=_TRACK_OPACITY,
    )
    _rows = machine.program_rows()
    _phases = len(_rows) if _rows else 1
    carrier_radii = {
        name: carrier_radius(machine, layout_pos, name, scale) for name in machine.gears
    }
    if carrier_positions is None:
        carrier_positions = machine.default_carriers()

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
    worst = max(offset_residuals(machine, layout_pos).values(), default=0.0)
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
    # match its layout — see ``offset_residuals``).

    def _build(state: MachineState, frac: float) -> List[go.BaseTraceType]:
        t = state.time
        out: List[go.BaseTraceType] = []
        out.extend(_connection_traces(machine, layout_pos, radii_dict))
        out.extend(_contact_point_traces(machine, layout_pos, radii_dict))
        out.extend(
            _gear_traces(machine, layout_pos, radii_dict, offsets, t, frac, scale)
        )
        out.extend(_axial_traces(machine, layout_pos))
        out.extend(
            _punchcard_traces(
                machine, layout_pos, radii_dict, current_phase=t % _phases
            )
        )

        xs, ys, htexts, colors_list, texts, sizes = [], [], [], [], [], []
        for c in state.carriers:
            # Draw the carrier on whatever is actually moving it this step,
            # which on a machine with shared slots is the receiving gear.
            gear_name, slot = machine.riding_position(c.position, t)
            cx, cy = layout_pos[gear_name]
            r = carrier_radii[gear_name]

            ang = _slot_angle(machine, gear_name, slot, offsets[gear_name], t, frac)

            xs.append(cx + r * math.cos(ang))
            ys.append(cy + r * math.sin(ang))
            htexts.append(f"C{c.carrier_id} @ {c.gear}[{c.slot}]")
            colors_list.append(carrier_colors[c.carrier_id])
            texts.append(str(c.carrier_id))
            sizes.append(bobbin_sizes[gear_name])

        out.append(
            go.Scatter(
                x=xs,
                y=ys,
                mode="markers+text",
                marker=dict(
                    size=sizes,
                    color=colors_list,
                    line=dict(width=1.5, color="white"),
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

    # The tracks go in first so they sit underneath, and every frame is told to
    # update only the traces after them.  They never change, so repeating them
    # in each frame would copy the same arcs a hundred times over — on an
    # eight-gear braid that alone was two thirds of the finished page.
    first = len(track_traces)
    moving = _build(history[0], 0.0)
    updates = list(range(first, first + len(moving)))

    for t_idx in range(n_steps):
        state = history[t_idx]
        for k in range(n_substeps):
            fname = f"{t_idx}_{k}"
            frames.append(
                go.Frame(data=_build(state, k / n_substeps), traces=updates, name=fname)
            )
            frame_names.append(fname)

    final_name = f"{n_steps}_0"
    frames.append(
        go.Frame(data=_build(history[n_steps], 0.0), traces=updates, name=final_name)
    )
    frame_names.append(final_name)

    fig = go.Figure(data=track_traces + moving, frames=frames)
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
