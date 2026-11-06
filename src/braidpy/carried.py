# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid made by its carriers: each yarn drawn by its carrier going round
the machine, through a forming ring, into the braid taken off above.

Nothing here is laid in advance.  The carriers go round their tracks
(:func:`~braidpy.horn_gear.take_off.carrier_trajectories`), and the yarns
follow:

- **To scale.**  Lengths are in yarn diameters, the machine at its real
  size: a gear some 5.5 cm across is ``GEAR_DIAMETER`` of 1100 dtex yarn,
  about 0.4 mm thick; the forming ring stands ``RING_HEIGHT`` above the
  carriers' eyes, 3 cm.
- **Pulled by the carriers.**  Each yarn runs straight from its carrier's
  eye up to ``BELOW`` under the ring; from there to the braid it is a chain
  of beads.  Its carrier pulls it with a steady tension, as a carrier's
  spring tensioner does: the lowest bead is pulled towards the eye, and
  yarn is paid out — a bead added at the bottom — when the braid draws it
  up, or taken back when it slackens.  No bead is ever renamed, so a
  contact remembers its friction for as long as it lasts.
- **The forming ring**, a torus of wire round the braid's axis, the yarns
  passing inside it: it brings them together where the braid forms.
- **Friction** holds the yarns where they cross, as on a real machine: a
  crossing is beaten up at the fell and carried up with the braid.  With
  none, two taut yarns slide to wherever they touch, and the braid taken
  off would have no crossings at all.
- **The braid taken off**: ``ABOVE`` over the ring, the yarns are made —
  frozen — and drawn up at a steady rate, ``TAKE_OFF`` a step of the
  machine.

Between moves of the carriers, the beads settle by FIRE, with the
mechanics of :mod:`braidpy.rope` — stretching, bending, contact — and the
friction of :mod:`braidpy.form`.  Pure Python, and slow: a reference, for
checking, and for a few steps of a small machine.
"""

from __future__ import annotations

import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from braidpy.form import _Bead, friction_force
from braidpy.rope import (
    fire_mix,
    fire_sums,
    move_beads,
    near_pairs,
    spread,
    stale,
    steer,
    stretch_and_bend,
    touching,
)
from braidpy.utils import lazy_module

if TYPE_CHECKING:
    import plotly.graph_objects as go

    from braidpy.horn_gear.model import BraidingMachine
else:
    go = lazy_module("plotly.graph_objects")

__all__ = ["CarriedBraid", "braid_by_carriers", "figure"]

# ------------------------------------------------------------- the machine
# In yarn diameters: 1100 dtex polyester, some 0.4 mm thick.
YARN_MM = 0.4
GEAR_DIAMETER = 140.0  # a gear 5.5 cm across
RING_HEIGHT = 75.0  # the forming ring 3 cm over the carriers' eyes
RING_WIRE = 2.0  # the radius of the ring's wire
RING_ROOM = 2.0  # room inside the ring, round where the yarns start
TAKE_OFF = 1.0  # braid drawn off, a step of the machine
TENSION = 1.0  # each carrier's pull on its yarn

# ---------------------------------------------------------------- the yarns
RADIUS = 0.5  # a yarn's, its diameter being the unit
CLEAR = 1.1  # yarns tied at the start so much further apart than touching
SPACING = 0.5  # beads apart along a yarn
BELOW = 10.0  # beads this far under the ring; below, a straight run
ABOVE = 3.0  # free this far over the ring; above, made
FRICTION = 0.3  # mu, as braidpy.form's
STRETCH = 100.0  # k_s
BEND = 0.5  # k_b
CONTACT = 100.0  # k_c, the yarns' cores
SOFT = 5.0  # k_r, their soft surfaces
SHELL = 0.1  # how thick the soft surface is, of a diameter
GRIP = 20.0  # k_t, the friction springs' stiffness
NEAR_MADE = 8  # the made beads the free ones can touch, at most, a yarn

# ----------------------------------------------------------------- settling
SUBSTEPS = 60  # the carriers' places between settlings, a step
MOST_STEPS = 400  # FIRE steps to settle, at most, each time
TOLERANCE = 2e-2  # settled once no force is larger
# Bead names in a friction spring's key, as braidpy.form's.
_KEY = 4194304
# FIRE's own (Bitzek et al., 2006), as braidpy.form uses them.
_DT, _DT_MOST, _ALPHA = 0.01, 0.05, 0.1
_GROW, _SHRINK, _DAMP, _AFTER = 1.1, 0.5, 0.99, 5
# Near enough to touch before beads move a quarter diameter (rope.stale).
_GAP = math.ceil(2 / SPACING) + 1
_REACH = 1 + 2 * SPACING + 0.5


@dataclass
class _Yarn:
    # Made beads, their heights less the braid's take-off so far.
    made: list[_Bead]
    # Free beads, from the braid down towards the carrier.
    free: list[_Bead]


@dataclass
class CarriedBraid:
    """A braid made by its carriers, and how it was made.

    Attributes:
        yarns: Each yarn, oldest first, as ``(n, 3)``: the braid made, then
            the free yarn down to its carrier's eye.
        made: How many of each yarn's points are the braid made.
        eyes: Each carrier's eye, where it is at the end.
        frames: Moments of the making, for an animation: each
            ``{"time", "yarns", "made", "eyes"}`` as above.
        colours: One colour per yarn.
        machine: The deck: gear centres and radii, to scale.
        ring: The forming ring: ``radius``, ``height``, ``wire``.
        deepest: The deepest any two yarns' cores pressed into each other.
    """

    yarns: list[np.ndarray]
    made: list[int]
    eyes: np.ndarray
    frames: list[dict[str, Any]]
    colours: list[str]
    machine: dict[str, Any]
    ring: dict[str, float]
    deepest: float = 0.0
    settings: dict[str, float] = field(default_factory=dict)


def braid_by_carriers(
    machine: BraidingMachine,
    n_steps: int,
    carriers: dict[int, tuple[str, int]] | None = None,
    gear_diameter: float = GEAR_DIAMETER,
    ring_height: float = RING_HEIGHT,
    ring_radius: float | None = None,
    take_off: float = TAKE_OFF,
    tension: float = TENSION,
    friction: float = FRICTION,
    substeps: int = SUBSTEPS,
    frame_every: int = 0,
    progress: Callable[[dict[str, Any]], None] | None = None,
) -> CarriedBraid:
    """A braid made by a machine's carriers going round; see the module.

    Args:
        machine: The machine.
        n_steps: Steps of the machine to make.
        carriers: The loading; the machine's own if None.
        gear_diameter: The machine's mean gear, across, in yarn diameters.
        ring_height: The forming ring over the carriers' eyes.
        ring_radius: The ring's radius, to its wire's middle; by default as
            wide as the yarns' start, with ``RING_ROOM`` to spare.
        take_off: Braid drawn off, a step.
        tension: Each carrier's pull on its yarn.
        friction: mu, between yarns.
        substeps: The carriers' places between settlings, a step.
        frame_every: Keep a moment of the making every so many settlings;
            0 for none.
        progress: Told after each step: ``{"step", "of"}``.

    Returns:
        The braid made, and how.
    """
    from braidpy.horn_gear import gear_radii
    from braidpy.horn_gear.take_off import carrier_trajectories
    from braidpy.utils import PALETTE

    if carriers is None:
        carriers = machine.default_carriers()
    radii = gear_radii(machine)
    scale = gear_diameter / (2 * float(np.mean(list(radii.values()))))
    traj = carrier_trajectories(machine, n_steps, carriers, n_substeps=substeps)
    centre = np.asarray(traj.centre(), dtype=float)
    keys = list(traj.xy)
    eyes = np.stack([(traj.xy[k] - centre) * scale for k in keys], axis=1)
    n_yarns = len(keys)

    # The yarns start tied round a circle a little more than touching, the
    # ring round them with room to spare.
    start = max(SPACING, CLEAR * RADIUS / math.sin(math.pi / max(2, n_yarns)))
    if ring_radius is None:
        ring_radius = start + RING_ROOM + RING_WIRE + RADIUS
    inside = ring_radius - RING_WIRE - RADIUS
    if inside <= start:
        raise ValueError("The forming ring is too small for the yarns to pass.")
    z_ring = ring_height
    z_low = z_ring - BELOW
    z_made = z_ring + ABOVE
    v_sub = take_off / substeps

    next_id = 0

    def bead(p: Sequence[float]) -> _Bead:
        nonlocal next_id
        next_id += 1
        return _Bead([float(c) for c in p], next_id - 1)

    chains: list[_Yarn] = []
    for k in range(n_yarns):
        eye = eyes[0, k]
        u = eye / max(float(np.linalg.norm(eye)), 1e-9)
        top = np.array([*(u * start), z_made + SPACING])
        # Straight down through the ring and under its wire, then out along
        # the run to the carrier.
        knee = np.array([*(u * start), z_ring - RING_WIRE - RADIUS - SPACING])
        to_eye = np.array([*eye, 0.0]) - knee
        foot = knee + to_eye * ((knee[2] - z_low) / knee[2])
        points = [top]
        for a, b in ((top, knee), (knee, foot)):
            count = max(1, round(float(np.linalg.norm(b - a)) / SPACING))
            points += [a + (b - a) * (i / count) for i in range(1, count + 1)]
        chains.append(
            _Yarn(
                made=[bead(points[0].tolist())],
                free=[bead(p.tolist()) for p in points[1:]],
            )
        )

    offset = 0.0
    grips: dict[int, list[float]] = {}
    deepest = 0.0
    frames: list[dict[str, Any]] = []

    def made_at(b: _Bead) -> list[float]:
        return [b.p[0], b.p[1], b.p[2] + offset]

    def snapshot(at: np.ndarray) -> dict[str, Any]:
        return {
            "yarns": [
                np.array([made_at(b) for b in y.made] + [b.p for b in y.free])
                for y in chains
            ],
            "made": [len(y.made) for y in chains],
            "eyes": np.array([[*e, 0.0] for e in at]),
        }

    for sample in range(1, len(traj.times)):
        offset += v_sub
        at = eyes[sample]
        deepest = max(
            deepest,
            _settle(
                chains,
                offset,
                at,
                grips,
                tension,
                friction,
                (ring_radius, z_ring),
            ),
        )
        _feed(chains, at, z_low, bead)
        for y in chains:
            while len(y.free) > 2 and y.free[0].p[2] > z_made:
                b = y.free.pop(0)
                b.p[2] -= offset
                y.made.append(b)
        if frame_every and sample % frame_every == 0:
            frames.append({"time": float(traj.times[sample]), **snapshot(at)})
        if progress is not None and sample % substeps == 0:
            progress({"step": sample // substeps, "of": n_steps})

    end = snapshot(eyes[-1])
    own: dict[Any, str] = dict(machine.carrier_colours(carriers) or {})
    colours = [own.get(k, PALETTE[i % len(PALETTE)]) for i, k in enumerate(keys)]
    return CarriedBraid(
        yarns=end["yarns"],
        made=end["made"],
        eyes=end["eyes"],
        frames=frames,
        colours=colours,
        machine={
            "centres": {
                g: ((np.asarray(c) - centre) * scale).tolist()
                for g, c in traj.layout.items()
            },
            "radii": {g: r * scale for g, r in traj.radii.items()},
        },
        ring={"radius": ring_radius, "height": z_ring, "wire": RING_WIRE},
        deepest=deepest,
        settings={
            "gear_diameter": gear_diameter,
            "take_off": take_off,
            "tension": tension,
            "friction": friction,
            "yarn_mm": YARN_MM,
        },
    )


def _feed(
    chains: list[_Yarn],
    eyes: np.ndarray,
    z_low: float,
    bead: Callable[[Sequence[float]], _Bead],
) -> None:
    """Each carrier pays yarn out, a bead at the bottom, while the braid has
    drawn its lowest bead up over ``z_low``; and takes it back while the
    yarn has slackened down under it."""
    for k, y in enumerate(chains):
        eye = np.array([*eyes[k], 0.0])
        while True:
            low = np.array(y.free[-1].p)
            if low[2] > z_low:
                way = eye - low
                y.free.append(
                    bead((low + way * (SPACING / float(np.linalg.norm(way)))).tolist())
                )
            elif low[2] < z_low - SPACING and len(y.free) > 2:
                y.free.pop()
            else:
                break


def _settle(
    chains: list[_Yarn],
    offset: float,
    eyes: np.ndarray,
    grips: dict[int, list[float]],
    tension: float,
    mu: float,
    ring: tuple[float, float],
) -> float:
    """The free beads settled by FIRE: stretching and bending, contacts and
    their friction, each carrier's pull and the ring.

    Returns:
        How deep any two yarns' cores pressed into each other.
    """
    core = 1 - SHELL
    ring_radius, z_ring = ring
    xs: list[float] = []
    ids: list[int] = []
    moves: list[int] = []
    yarn_of: list[int] = []
    spans: list[tuple[int, int]] = []
    low = min(b.p[2] for y in chains for b in y.free)
    for a, y in enumerate(chains):
        first = len(ids)
        # The made braid near the free yarns, then the free beads.
        near = [b for b in y.made[-NEAR_MADE:] if b.p[2] + offset > low - _REACH]
        if not near:
            near = y.made[-1:]
        for b in near:
            xs.extend([b.p[0], b.p[1], b.p[2] + offset])
            ids.append(b.id)
            moves.append(0)
            yarn_of.append(a)
        for b in y.free:
            xs.extend(b.p)
            ids.append(b.id)
            moves.append(1)
            yarn_of.append(a)
        spans.append((first, len(ids) - 1))
    n = len(ids)
    x = xs
    segs = [g for first, last in spans for g in range(first, last)]
    cells = [0] * (3 * n)
    built = list(x)
    pairs: list[int] = []
    keys_here: set[int] = set()

    def accept(g: int, h: int) -> bool:
        return bool(moves[g] or moves[g + 1] or moves[h] or moves[h + 1])

    def neighbours() -> None:
        nonlocal pairs, keys_here
        pairs = near_pairs(x, segs, yarn_of, _GAP, _REACH, cells, accept)
        built[:] = x
        keys_here = {
            ids[pairs[e]] * _KEY + ids[pairs[e + 1]] for e in range(0, len(pairs), 2)
        }

    f = [0.0] * (3 * n)
    v = [0.0] * (3 * n)
    touched: set[int] = set()
    now = {"dt": _DT, "deepest": 0.0}

    def touch(
        e: int, u: float, w: float, px: float, py: float, pz: float, r2: float
    ) -> None:
        g, h = pairs[e], pairs[e + 1]
        i, j = 3 * g, 3 * h
        r = math.sqrt(r2)
        push = SOFT * (1 - r)
        if r < core:
            now["deepest"] = max(now["deepest"], core - r)
            push += CONTACT * (core - r)
        nx, ny, nz = px / max(r, 1e-9), py / max(r, 1e-9), pz / max(r, 1e-9)
        qx, qy, qz = push * nx, push * ny, push * nz
        if mu > 0:
            key = ids[g] * _KEY + ids[h]
            touched.add(key)
            tx, ty, tz = friction_force(
                grips, key, v, i, j, u, w, nx, ny, nz, push, now["dt"], mu, GRIP
            )
            qx, qy, qz = qx + tx, qy + ty, qz + tz
        spread(f, i, j, u, w, qx, qy, qz)

    def forces() -> None:
        f[:] = [0.0] * (3 * n)
        for first, last in spans:
            stretch_and_bend(x, f, first, last, SPACING, STRETCH, BEND)
        # Each carrier's pull on its lowest bead.
        for a, (_, last) in enumerate(spans):
            i = 3 * last
            dx, dy, dz = eyes[a][0] - x[i], eyes[a][1] - x[i + 1], -x[i + 2]
            r = math.sqrt(dx * dx + dy * dy + dz * dz)
            f[i] += tension * dx / r
            f[i + 1] += tension * dy / r
            f[i + 2] += tension * dz / r
        # The ring's wire: a bead closer to it than its radius and a half
        # diameter is pushed off it.
        clear = RING_WIRE + RADIUS
        for g in range(n):
            if not moves[g]:
                continue
            i = 3 * g
            r = math.hypot(x[i], x[i + 1])
            qr, qz = r - ring_radius, x[i + 2] - z_ring
            dist = math.hypot(qr, qz)
            if dist < clear:
                push = CONTACT * (clear - dist) / max(dist, 1e-9)
                f[i] += push * qr * x[i] / max(r, 1e-9)
                f[i + 1] += push * qr * x[i + 1] / max(r, 1e-9)
                f[i + 2] += push * qz
        now["deepest"] = 0.0
        touched.clear()
        touching(x, pairs, touch)
        for key in keys_here - touched:
            grips.pop(key, None)

    dt, alpha, downhill = _DT, _ALPHA, 0
    none: list[float] = []
    neighbours()
    deepest = 0.0
    for _ in range(MOST_STEPS):
        if stale(x, built):
            neighbours()
        now["dt"] = dt
        forces()
        deepest = max(deepest, now["deepest"])
        sums = [0.0, 0.0, 0.0, 0.0]
        fire_sums(f, v, moves, none, none, none, sums)
        if sums[3] < TOLERANCE:
            break
        mix = fire_mix(sums, alpha)
        steer(v, f, moves, [], none, alpha, mix)
        if sums[0] > 0:
            downhill += 1
            if downhill > _AFTER:
                dt = min(dt * _GROW, _DT_MOST)
                alpha *= _DAMP
        else:
            downhill = 0
            dt *= _SHRINK
            alpha = _ALPHA
            v[:] = [0.0] * (3 * n)
        move_beads(x, v, f, dt, moves)
    for a, y in enumerate(chains):
        first, last = spans[a]
        for k, b in enumerate(y.free):
            g = last - len(y.free) + 1 + k
            b.p = [x[3 * g], x[3 * g + 1], x[3 * g + 2]]
    return deepest


# --------------------------------------------------------------- the views


def figure(braid: CarriedBraid, view: str = "braid", n_around: int = 12) -> go.Figure:
    """The braid in 3D.

    Args:
        braid: What :func:`braid_by_carriers` made.
        view: ``"braid"``, the braid made and the yarns into it, as tubes,
            near; or ``"machine"``, everything to scale — the deck, the
            carriers, the yarns' straight runs up to the ring, the ring, and
            the braid as small as it is beside them.
        n_around: Points round each tube.

    Returns:
        The figure.
    """
    from braidpy.parametric_strand import tube_mesh

    if view not in ("braid", "machine"):
        raise ValueError("A view is 'braid' or 'machine'.")
    traces: list[go.BaseTraceType] = []
    ring = braid.ring
    for k, yarn in enumerate(braid.yarns):
        colour = braid.colours[k]
        shown = yarn if view == "machine" else yarn[yarn[:, 2] > ring["height"] - BELOW]
        if len(shown) >= 2:
            tx, ty, tz = tube_mesh(shown, RADIUS, n_around)
            traces.append(
                go.Surface(
                    x=tx,
                    y=ty,
                    z=tz,
                    colorscale=[[0, colour], [1, colour]],
                    showscale=False,
                    name=f"Yarn {k}",
                    lighting={"ambient": 0.5, "diffuse": 0.8, "specular": 0.3},
                )
            )
        if view == "machine":
            # Its straight run from the lowest bead to the carrier's eye.
            run = np.array([yarn[-1], braid.eyes[k]])
            traces.append(
                go.Scatter3d(
                    x=run[:, 0],
                    y=run[:, 1],
                    z=run[:, 2],
                    mode="lines",
                    line={"color": colour, "width": 2},
                    showlegend=False,
                )
            )
    if view == "machine":
        traces.append(
            go.Scatter3d(
                x=braid.eyes[:, 0],
                y=braid.eyes[:, 1],
                z=braid.eyes[:, 2],
                mode="markers",
                marker={"size": 4, "color": braid.colours},
                name="Carriers",
            )
        )
        angle = np.linspace(0, 2 * np.pi, 120)
        for name, (cx, cy) in braid.machine["centres"].items():
            r = braid.machine["radii"][name]
            traces.append(
                go.Scatter3d(
                    x=cx + r * np.cos(angle),
                    y=cy + r * np.sin(angle),
                    z=np.zeros_like(angle),
                    mode="lines",
                    line={"color": "#999999", "width": 2},
                    showlegend=False,
                )
            )
    traces.append(_ring_trace(ring, n_around))
    layout = {
        "scene": {"aspectmode": "data"},
        "margin": {"l": 0, "r": 0, "t": 30, "b": 0},
        "title": (
            "The braid made by its carriers"
            if view == "braid"
            else "To scale: the deck, the carriers, the ring and the braid"
        ),
    }
    return go.Figure(data=traces, layout=layout)


def _ring_trace(ring: dict[str, float], n_around: int) -> go.Surface:
    """The forming ring: a torus of wire round the axis."""
    around = np.linspace(0, 2 * np.pi, 96)
    tube = np.linspace(0, 2 * np.pi, n_around + 1)
    a, t = np.meshgrid(around, tube)
    r = ring["radius"] + ring["wire"] * np.cos(t)
    return go.Surface(
        x=r * np.cos(a),
        y=r * np.sin(a),
        z=ring["height"] + ring["wire"] * np.sin(t),
        colorscale=[[0, "#b8b8b8"], [1, "#b8b8b8"]],
        showscale=False,
        opacity=0.6,
        name="Forming ring",
    )
