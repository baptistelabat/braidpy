# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Filename: gen_docs_figures.py
Description: Draws the figures for the rope and braided-tube documentation
Authors: Baptiste Labat
Created: 2025-05-26
Repository: https://github.com/baptistelabat/braidpy
License: Mozilla Public License 2.0

Every figure here is computed by the same functions the documentation
describes, and the claims the pages make about them are asserted rather than
asserted-by-hand, so a drawing cannot drift from the formula it explains.
Run it after changing either and the pictures follow:

    python gen_docs_figures.py

It writes SVG into ``docs/source/``.  Pass ``--png DIR`` to also drop PNG
copies somewhere for eyeballing.
"""

from __future__ import annotations

import argparse
import math
import sys
from collections.abc import Sequence
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from typing import Optional

from braidpy.annulus_braid import (
    TubularBraidStrand,
    cover_factor,
    crossing_binds_above,
    lay_radius,
    minimum_lay,
    packing_radius,
    radius_for_cover,
    tubular_braid,
    tubular_braid_radius,
)

DOCS = Path(__file__).parent.parent / "docs" / "source"

INK = "#1f2933"
MUTED = "#7b8794"
OUT = "#1b6ac9"  # the strand passing outside
IN = "#c2410c"  # the strand passing inside
MARK = "#15803d"  # the answer being pointed at
LIMIT = "#9f1239"  # a bound or a limit


def _style() -> None:
    # A committed generated file must not churn: without a fixed hash salt
    # matplotlib names its SVG elements randomly, and without a pinned date
    # it stamps every file with the time it ran.  Either one makes the whole
    # figure show up as modified on a run that changed nothing.
    matplotlib.rcParams["svg.hashsalt"] = "braidpy-docs"
    plt.rcParams.update(
        {
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "axes.edgecolor": MUTED,
            "axes.labelcolor": INK,
            "text.color": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 9,
            "axes.titlesize": 10,
            "legend.frameon": False,
            "svg.fonttype": "none",
        }
    )


def _save(fig, name: str, png_dir: Path | None, note: Optional[str] = None) -> None:
    if note:
        fig.text(0.0, -0.02, note, color=MUTED, fontsize=8, va="top")
    DOCS.mkdir(parents=True, exist_ok=True)
    fig.savefig(DOCS / f"{name}.svg", bbox_inches="tight", metadata={"Date": None})
    if png_dir is not None:
        png_dir.mkdir(parents=True, exist_ok=True)
        fig.savefig(png_dir / f"{name}.png", dpi=130, bbox_inches="tight")
    plt.close(fig)
    print(f"  {name}.svg")


def _crossings(
    strands: Sequence[TubularBraidStrand], index: int = 0
) -> list[tuple[float, int]]:
    """Every height at which one strand crosses a strand going the other way.

    Solved rather than sampled.  Strand ``i`` is at angle ``t`` after
    climbing ``z = R t / tan q``; a strand going the other way is at
    ``-t + phase``.  They share an angle when ``2t = phase + 2 pi m``.
    """
    one = strands[index]
    turn = 2.0 * math.pi
    found: list[tuple[float, int]] = []
    for other_index, other in enumerate(strands):
        if other.direction == one.direction:
            continue
        for wrap in range(2):
            traveled = (other.phase - one.phase + turn * wrap) / 2.0
            if 0.0 <= traveled < turn:
                height = traveled * one.radius / math.tan(one.braid_angle)
                found.append((height, other_index))
    return sorted(found)


# ── The rope ──────────────────────────────────────────────────────────────────


def rope_one_curve_repeated(png_dir: Path | None) -> None:
    """The rope's strands are one helix, slid along by k n-ths of a lay."""
    n, diameter, lay = 3, 0.4, 2.0
    radius = lay_radius(n, diameter, lay)
    fig, ax = plt.subplots(figsize=(5.4, 3.0))

    angle = np.linspace(0, 2 * math.pi, 200)
    for k in range(n):
        ax.plot(
            radius * angle,
            lay * angle / (2 * math.pi) + k * lay / n,
            color=OUT if k == 0 else MUTED,
            lw=5 if k == 0 else 3.5,
            solid_capstyle="round",
            alpha=1.0 if k == 0 else 0.5,
            label="strand 0" if k == 0 else ("the other two, slid" if k == 1 else None),
        )

    span = radius * 2 * math.pi
    ax.annotate(
        "",
        xy=(span * 0.62, lay * 0.62 + lay / n),
        xytext=(span * 0.62, lay * 0.62),
        arrowprops=dict(arrowstyle="<->", color=MARK, lw=1.4),
    )
    ax.text(
        span * 0.60,
        lay * 0.62 + lay / (2 * n),
        f"$\\lambda/n$ = {lay / n:.2f}  ",
        color=MARK,
        va="center",
        ha="right",
        fontsize=9,
    )
    ax.set_xlabel("distance round the rope  $R\\theta$")
    ax.set_ylabel("height  $z$")
    ax.set_title(
        f"One helix at {n} phases — cut open and laid flat "
        f"($\\lambda$ = {lay:g}, R = {radius:.3f})"
    )
    ax.legend(loc="lower right")
    _save(
        fig,
        "rope_one_curve_repeated",
        png_dir,
        "Flattening preserves the repeat, not the distances: the strands' true\n"
        "clearance is measured through the rope, not across this sheet.",
    )


def rope_clearance(png_dir: Path | None) -> None:
    """D(w), and why the packing radius is only the zero-lay answer."""
    n, diameter, lay = 3, 0.4, 2.0
    radius = lay_radius(n, diameter, lay)

    w = np.linspace(0.0, lay, 2000)
    slide = lay / n  # neighbouring strands
    distance = np.hypot(2 * radius * np.sin(math.pi * w / lay), slide - w)
    chord = 2 * radius * math.sin(math.pi / n)
    best = int(np.argmin(distance))

    assert abs(distance[best] - diameter) < 1e-3, "the rope should be just touching"
    assert distance[best] < chord, "the true minimum must beat the chord"

    fig, ax = plt.subplots(figsize=(5.6, 3.4))
    ax.plot(w, distance, color=INK, lw=1.9, label="$D(w)$", zorder=3)
    ax.axhline(diameter, color=LIMIT, ls="--", lw=1.1, zorder=1)
    ax.text(lay * 0.5, diameter - 0.07, "d", color=LIMIT, va="top", fontsize=9)

    ax.plot([slide], [chord], "o", color=OUT, ms=6, zorder=4)
    ax.annotate(
        f"$w=\\lambda/n$: the chord between\nneighbours, {chord:.3f}\n"
        "— what packing_radius sees",
        xy=(slide, chord),
        xytext=(lay * 0.52, 1.02),
        color=OUT,
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=OUT, lw=1.0),
    )

    ax.plot([0.0], [slide], "o", color=IN, ms=6, zorder=4)
    ax.annotate(
        f"$w=0$: pure axial offset,\n$\\lambda/n$ = {slide:.3f}\n"
        "— what minimum_lay sees",
        xy=(0.0, slide),
        xytext=(lay * 0.06, 1.02),
        color=IN,
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=IN, lw=1.0),
    )

    ax.plot([w[best]], [distance[best]], "o", color=MARK, ms=7, zorder=5)
    ax.annotate(
        f"the nearest approach\n$w$ = {w[best]:.3f},  D = {distance[best]:.3f}",
        xy=(w[best], distance[best]),
        xytext=(lay * 0.30, 0.09),
        color=MARK,
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=MARK, lw=1.0),
    )

    ax.set_xlabel("slide along the axis between the two strands,  $w$")
    ax.set_ylabel("distance between centres,  $D$")
    ax.set_title(
        f"How close two strands come ({n} strands, $\\lambda$ = {lay:g}, "
        f"R = {radius:.3f})"
    )
    ax.set_ylim(0, float(distance.max()) * 1.12)
    ax.legend(loc="upper left")
    _save(fig, "rope_clearance", png_dir)


def rope_settling_radius(png_dir: Path | None) -> None:
    """Where the rope settles, against the two bounds that bracket it."""
    n, diameter = 3, 0.4
    shortest = minimum_lay(n, diameter)
    packed = packing_radius(n, diameter)

    lays = np.linspace(shortest * 1.12, shortest * 9.0, 60)
    radii = [lay_radius(n, diameter, float(lay)) for lay in lays]

    assert radii[0] > radii[-1] > packed, (
        "settling radius falls towards the packing one"
    )

    fig, ax = plt.subplots(figsize=(5.6, 3.3))
    ax.plot(lays, radii, color=MARK, lw=2.0, label="lay_radius: where it settles")
    ax.axhline(
        packed,
        color=OUT,
        ls="--",
        lw=1.2,
        label=f"packing_radius = {packed:.3f} (the zero-lay limit)",
    )
    ax.axvline(
        shortest,
        color=LIMIT,
        ls=":",
        lw=1.5,
        label=f"minimum_lay = $n\\,d$ = {shortest:g}",
    )
    ax.annotate(
        f"a tighter lay forces the strands wider:\n{radii[0]:.3f} at "
        f"$\\lambda$ = {lays[0]:.2f}",
        xy=(lays[0], radii[0]),
        xytext=(shortest * 2.6, radii[0] * 0.93),
        color=INK,
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0),
    )

    ax.set_xlabel("lay length  $\\lambda$")
    ax.set_ylabel("radius the strands sit at")
    ax.set_title(f"A {n}-strand rope, {diameter:g} thick, pulled tight")
    ax.legend(loc="center right", fontsize=8)
    _save(fig, "rope_settling_radius", png_dir)


# ── The braided tube ──────────────────────────────────────────────────────────


def tube_cross_section(png_dir: Path | None) -> None:
    """A cut at a crossing height, drawn from the strands' own positions."""
    n, diameter = 8, 0.4
    angle_q = math.pi / 4
    radius = tubular_braid_radius(n, diameter, angle_q)
    bulge = diameter / 2
    strands = tubular_braid(n, radius=radius, braid_angle=angle_q, diameter=diameter)
    height = _crossings(strands)[0][0]

    seats = [strand.position(height) for strand in strands]
    for (x, y, _), strand in zip(seats, strands):
        assert abs(abs(math.hypot(x, y) - radius) - bulge) < 1e-9, (
            "at a crossing height every strand sits at an extreme"
        )

    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    circle = np.linspace(0, 2 * math.pi, 300)
    ax.plot(
        radius * np.cos(circle),
        radius * np.sin(circle),
        color=MUTED,
        ls="--",
        lw=1.0,
        label=f"mean radius R = {radius:.3f}",
    )

    for (x, y, _), strand in zip(seats, strands):
        outward = math.hypot(x, y) > radius
        ax.add_patch(
            plt.Circle(
                (x, y),
                diameter / 2,
                facecolor=(OUT if outward else IN),
                edgecolor="white",
                lw=0.9,
                alpha=0.9,
                zorder=3 if outward else 2,
            )
        )

    ax.annotate(
        "",
        xy=(
            (radius + bulge) * math.cos(math.pi / n),
            (radius + bulge) * math.sin(math.pi / n),
        ),
        xytext=(
            (radius - bulge) * math.cos(math.pi / n),
            (radius - bulge) * math.sin(math.pi / n),
        ),
        arrowprops=dict(arrowstyle="<->", color=MARK, lw=1.5),
        zorder=5,
    )
    ax.text(
        (radius + bulge * 3.4) * math.cos(math.pi / n),
        (radius + bulge * 3.4) * math.sin(math.pi / n),
        f"$2b$ = {2 * bulge:g}",
        color=MARK,
        ha="center",
        fontsize=9,
        zorder=5,
    )
    ax.plot([], [], "o", color=OUT, label="passing outside, at $R+b$")
    ax.plot([], [], "o", color=IN, label="passing inside, at $R-b$")

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title(f"Cut at a crossing height ({n} strands, d = {diameter:g})")
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 0.04), fontsize=8)
    _save(
        fig,
        "tube_cross_section",
        png_dir,
        f"All {n // 2} crossings happen at the same height. Each is a pair sharing\n"
        "one angle, so the cut shows them stacked, not side by side.",
    )


def tube_swing(png_dir: Path | None) -> None:
    """The swing is timed so that every crossing falls on an extreme."""
    n, diameter = 8, 0.4
    angle_q = math.pi / 4
    radius = tubular_braid_radius(n, diameter, angle_q)
    bulge = diameter / 2
    strands = tubular_braid(n, radius=radius, braid_angle=angle_q, diameter=diameter)
    one, other = strands[0], strands[1]
    period = one.length

    z = np.linspace(0, period, 1600)

    def radial(strand):
        return np.array([math.hypot(*strand.position(float(h))[:2]) for h in z])

    meets = [height for height, _ in _crossings(strands) if height <= period]
    for height in meets:
        assert abs(abs(math.hypot(*one.position(height)[:2]) - radius) - bulge) < 1e-9

    fig, ax = plt.subplots(figsize=(5.8, 3.4))
    ax.plot(z, radial(one), color=OUT, lw=1.9, label="one strand", zorder=3)
    ax.plot(
        z,
        radial(other),
        color=IN,
        lw=1.5,
        alpha=0.75,
        label="its neighbour, going the other way",
        zorder=2,
    )
    ax.axhline(radius, color=MUTED, ls="--", lw=0.9)
    ax.text(period * 0.01, radius + 0.008, "R", color=MUTED, fontsize=9)

    for height in meets:
        ax.axvline(height, color=MARK, ls=":", lw=1.0, zorder=1)
    ax.plot(
        meets,
        [math.hypot(*one.position(h)[:2]) for h in meets],
        "o",
        color=MARK,
        ms=5.5,
        zorder=4,
        label="a crossing — always at an extreme",
    )

    ax.set_ylabel("distance from the axis")
    ax.set_xlabel("height along the axis  $z$")
    ax.set_title(
        f"The swing is timed to the crossings ({n} strands, "
        f"q = {math.degrees(angle_q):g}°, b = {bulge:g})"
    )
    ax.set_ylim(radius - bulge * 1.6, radius + bulge * 2.5)
    ax.legend(loc="upper center", ncol=2, fontsize=8)
    _save(
        fig,
        "tube_swing",
        png_dir,
        f"{len(meets)} crossings in one turn of the tube — one with each strand\n"
        "coming the other way, twice each. Not one is missed by the swing.",
    )


def tube_radius_conditions(png_dir: Path | None) -> None:
    """The two terms under the max, and which one binds."""
    n, diameter = 8, 0.4
    bulge = diameter / 2
    angles = np.linspace(math.radians(8), math.radians(82), 400)

    swing = bulge * math.sqrt(1 + n**2 / 4) * np.ones_like(angles)
    climb = bulge * (n / 2) * np.tan(angles)
    needed = np.maximum(swing, climb)
    crossover = math.atan(math.sqrt(1 + 4 / n**2))

    assert not crossing_binds_above(n, crossover - 1e-6)
    assert crossing_binds_above(n, crossover + 1e-6)
    for q, value in zip(angles, needed):
        assert abs(tubular_braid_radius(n, diameter, float(q)) - value) < 1e-12

    fig, ax = plt.subplots(figsize=(5.8, 3.5))
    ax.plot(
        np.degrees(angles),
        swing,
        color=OUT,
        ls="--",
        lw=1.4,
        label="the swing: $b\\sqrt{1+n^2/4}$",
    )
    ax.plot(
        np.degrees(angles),
        climb,
        color=IN,
        ls="--",
        lw=1.4,
        label="the climb: $b\\,(n/2)\\tan q$",
    )
    ax.plot(
        np.degrees(angles),
        needed,
        color=MARK,
        lw=2.5,
        label="tubular_braid_radius: the larger",
    )
    ax.axvline(np.degrees(crossover), color=MUTED, ls=":", lw=1.2)

    top = float(needed.max())
    ax.text(
        np.degrees(crossover) - 1.5,
        top * 0.52,
        f"crossover  $\\tan q^* = \\sqrt{{1+4/n^2}}$\n= {math.degrees(crossover):.1f}°",
        color=INK,
        fontsize=8,
        ha="right",
    )
    ax.text(
        np.degrees(crossover) - 20,
        top * 0.26,
        "the strands' own swing\nholds the tube open",
        color=OUT,
        fontsize=8,
        ha="center",
    )
    ax.text(
        np.degrees(crossover) + 21,
        top * 0.60,
        "how fast they climb past\none another does",
        color=IN,
        fontsize=8,
        ha="center",
    )
    ax.set_xlabel("braid angle  $q$  (degrees from the axis)")
    ax.set_ylabel("narrowest workable radius")
    ax.set_title(f"Which condition binds ({n} strands, b = {bulge:g})")
    ax.set_ylim(0, top * 1.04)
    ax.legend(loc="upper left", fontsize=8)
    _save(fig, "tube_radius_conditions", png_dir)


def tube_cover_gap(png_dir: Path | None) -> None:
    """The model's main limitation: not crowding and looking braided differ."""
    n, diameter = 8, 0.4
    angles = np.linspace(math.radians(15), math.radians(75), 300)

    no_crowding = [tubular_braid_radius(n, diameter, float(q)) for q in angles]
    closed = [radius_for_cover(n, diameter, float(q), 1.0) for q in angles]
    covered = [
        cover_factor(n, r, float(q), diameter) for r, q in zip(no_crowding, angles)
    ]

    assert max(covered) < 1.0, "round strands that just clear cannot close the tube"

    fig, (ax, cover) = plt.subplots(
        2, 1, figsize=(5.8, 4.8), sharex=True, height_ratios=[1.3, 1.0]
    )
    ax.plot(
        np.degrees(angles),
        no_crowding,
        color=MARK,
        lw=2.1,
        label="narrowest that does not crowd",
    )
    ax.plot(
        np.degrees(angles),
        closed,
        color=LIMIT,
        lw=1.7,
        ls="--",
        label="narrow enough to be fully covered",
    )
    ax.fill_between(np.degrees(angles), closed, no_crowding, color=LIMIT, alpha=0.10)
    ax.set_ylabel("radius")
    ax.set_title(
        f"The two radii are not the same number ({n} strands, d = {diameter:g})"
    )
    ax.legend(loc="upper left", fontsize=8)

    cover.plot(np.degrees(angles), covered, color=INK, lw=1.9)
    cover.axhline(1.0, color=LIMIT, ls="--", lw=1.1)
    cover.text(17, 1.0, "closed", color=LIMIT, va="bottom", fontsize=8)
    peak = int(np.argmax(covered))
    cover.annotate(
        f"best this model reaches:\n{covered[peak]:.2f} at "
        f"{math.degrees(angles[peak]):.0f}°",
        xy=(math.degrees(angles[peak]), covered[peak]),
        xytext=(math.degrees(angles[peak]) + 4, covered[peak] - 0.34),
        color=INK,
        fontsize=8,
        arrowprops=dict(arrowstyle="->", color=MUTED, lw=1.0),
    )
    cover.set_ylabel("cover at that radius")
    cover.set_xlabel("braid angle  $q$  (degrees from the axis)")
    cover.set_ylim(0, 1.2)
    _save(
        fig,
        "tube_cover_gap",
        png_dir,
        "Round strands that just clear one another leave the tube open. Closing it\n"
        "needs flattened yarn, which this model does not describe.",
    )


# ---------------------------------------------------------------- the rope solver

ROPE_CASES = Path(__file__).parent.parent / "tests" / "js" / "rope_cases.js"
YARN = [
    "#1b6ac9",
    "#c2410c",
    "#15803d",
    "#7c3aed",
    "#b45309",
    "#0f766e",
    "#be185d",
    "#4d7c0f",
]


def _node(*args: str) -> dict:
    """A case of tests/js/rope_cases.js: web/rope.js run by Node."""
    import json
    import subprocess

    out = subprocess.run(
        ["node", str(ROPE_CASES), *args], capture_output=True, text=True, check=True
    )
    return json.loads(out.stdout)


def _xyz(yarn: Sequence[float]) -> np.ndarray:
    return np.asarray(yarn, dtype=float).reshape(-1, 3)


def rope_model(png_dir: Path | None) -> None:
    """A yarn as beads; two yarns in contact; the contact force law."""
    from matplotlib.patches import Circle, FancyArrowPatch

    fig, (chain, contact, law) = plt.subplots(
        1, 3, figsize=(11.5, 3.8), gridspec_kw={"width_ratios": [1.15, 1.25, 1.0]}
    )
    fig.subplots_adjust(wspace=0.35)

    # The yarn: a tube, its centreline a chain of beads.
    t = np.linspace(0, 1, 9)
    xs, ys = 3.6 * t, 0.55 * np.sin(2.6 * t * math.pi / 2)
    for x, y in zip(xs, ys):
        chain.add_patch(Circle((x, y), 0.5, color=OUT, alpha=0.08, lw=0))
    chain.plot(xs, ys, color=OUT, lw=1.4)
    chain.plot(xs, ys, "o", color=OUT, ms=5)
    chain.annotate(
        "",
        xy=(xs[3], ys[3] - 0.18),
        xytext=(xs[2], ys[2] - 0.18),
        arrowprops=dict(arrowstyle="<->", color=INK, lw=0.9),
    )
    chain.text(
        (xs[2] + xs[3]) / 2,
        (ys[2] + ys[3]) / 2 - 0.42,
        "link $s$\nstretch $k_s$",
        ha="center",
        va="top",
        fontsize=8,
    )
    chain.plot(xs[5:8], ys[5:8], color=IN, lw=2.6, alpha=0.6)
    chain.text(
        xs[6],
        ys[6] + 0.32,
        "three beads:\nbending $k_b$",
        ha="center",
        fontsize=8,
        color=IN,
    )
    chain.annotate(
        "",
        xy=(xs[0], ys[0] + 0.5),
        xytext=(xs[0], ys[0] - 0.5),
        arrowprops=dict(arrowstyle="<->", color=MUTED, lw=0.8),
    )
    chain.text(xs[0] - 0.12, ys[0], "$d$", ha="right", va="center", color=MUTED)
    chain.set_title("a yarn: beads on its centreline")
    chain.set_xlim(-0.8, 4.3)
    chain.set_ylim(-1.3, 1.5)

    # Two yarns, one passing over the other, seen from the side.
    contact.add_patch(Circle((0, 0), 0.5, color=IN, alpha=0.25, lw=0))
    contact.add_patch(Circle((0, 0), 0.45, fill=False, color=IN, lw=0.8, ls="--"))
    contact.plot(
        [-1.6, 1.6], [0.95, 0.6], color=OUT, lw=10, alpha=0.25, solid_capstyle="round"
    )
    contact.plot([-1.6, 1.6], [0.95, 0.6], color=OUT, lw=1.2)
    contact.plot(0, 0, "o", color=IN, ms=4)
    q = (0.083, 0.768)
    contact.plot(*q, "o", color=OUT, ms=4)
    contact.plot([0, q[0]], [0, q[1]], color=INK, lw=0.7, ls=":")
    contact.add_patch(
        FancyArrowPatch(
            q,
            (q[0] + 0.11, q[1] + 0.95),
            arrowstyle="-|>",
            mutation_scale=12,
            color=MARK,
            lw=1.6,
        )
    )
    contact.text(
        q[0] + 0.2,
        q[1] + 0.9,
        "push, along the line\njoining the closest points:\nmostly up, here",
        color=MARK,
        fontsize=8,
        va="top",
    )
    contact.add_patch(
        FancyArrowPatch(
            (-1.5, 1.25),
            (-0.6, 1.14),
            arrowstyle="<|-|>",
            mutation_scale=10,
            color=MUTED,
            lw=1.0,
        )
    )
    contact.text(
        -1.05,
        1.42,
        "sliding along: no force\n(no friction)",
        ha="center",
        va="bottom",
        color=MUTED,
        fontsize=8,
    )
    contact.text(
        0,
        -0.62,
        "yarn passing under, seen end on:\nsoft surface over a firm core",
        ha="center",
        va="top",
        fontsize=8,
        color=IN,
    )
    contact.set_title("two yarns touching")
    contact.set_xlim(-1.9, 2.4)
    contact.set_ylim(-1.3, 2.0)

    for ax in (chain, contact):
        ax.set_aspect("equal")
        ax.axis("off")

    # The force law: none apart, soft then stiff.
    shell, kr, kc = 0.1, 5.0, 100.0
    r = np.linspace(0.8, 1.1, 400)
    force = np.where(r < 1, kr * (1 - r), 0) + np.where(
        r < 1 - shell, kc * (1 - shell - r), 0
    )
    law.plot(r, force, color=INK, lw=1.6)
    law.axvline(1.0, color=MUTED, lw=0.8, ls="--")
    law.axvline(1 - shell, color=MUTED, lw=0.8, ls="--")
    law.text(1.005, 8.6, "a diameter apart:\nsurfaces meet", fontsize=8, color=MUTED)
    law.text(0.905, 8.6, "cores\nmeet", fontsize=8, color=MUTED)
    law.annotate(
        "soft: $k_r$",
        xy=(0.95, 0.3),
        xytext=(0.96, 2.6),
        fontsize=8,
        color=IN,
        arrowprops=dict(arrowstyle="->", color=IN, lw=0.8),
    )
    law.annotate(
        "stiff: $k_c$",
        xy=(0.86, 4.5),
        xytext=(0.865, 6.4),
        fontsize=8,
        color=IN,
        arrowprops=dict(arrowstyle="->", color=IN, lw=0.8),
    )
    law.set_xlabel("distance between centrelines, in diameters")
    law.set_ylabel("push")
    law.set_ylim(0, 10)
    law.set_title("contact force against distance")
    _save(
        fig,
        "rope_model",
        png_dir,
        "Every force is the gradient of one energy: stretching, bending, contact, and the work of the "
        "ends (next figure).",
    )


def rope_ends(png_dir: Path | None) -> None:
    """The braid's ends: clamped at the fell, held by a plate, fed from bobbins."""
    from matplotlib.patches import FancyArrowPatch, Rectangle

    fig, ax = plt.subplots(figsize=(7.6, 4.6))
    z = np.linspace(0, 6, 300)
    for k, color in enumerate(YARN[:4]):
        x = 0.9 * np.sin(2.1 * z + k * math.pi / 2)
        ax.plot(x, z, color=color, lw=2.4, alpha=0.85)
    ax.add_patch(Rectangle((-1.6, -0.35), 3.2, 0.35, color=MUTED, alpha=0.35, lw=0))
    ax.text(
        -1.75,
        -0.18,
        "the fell: each yarn\nclamped where it is",
        ha="right",
        va="center",
        fontsize=8,
    )
    ax.add_patch(Rectangle((-1.6, 6.0), 3.2, 0.25, color=INK, alpha=0.75, lw=0))
    ax.text(
        -1.75,
        6.12,
        "end plate: rises, turns,\nholds the ends apart",
        ha="right",
        va="center",
        fontsize=8,
    )
    ax.add_patch(
        FancyArrowPatch(
            (0, 6.3), (0, 7.6), arrowstyle="-|>", mutation_scale=14, color=MARK, lw=1.8
        )
    )
    ax.text(
        0.12, 7.35, "$W$: the braid drawn off,\nby a weight", color=MARK, fontsize=8
    )
    ax.annotate(
        "",
        xy=(1.25, 6.55),
        xytext=(-1.25, 6.55),
        arrowprops=dict(
            arrowstyle="->", color=MUTED, lw=1.0, connectionstyle="arc3,rad=-0.35"
        ),
    )
    ax.text(1.35, 6.75, "free to turn", color=MUTED, fontsize=8)
    for k, color in enumerate(YARN[:4]):
        x0 = 0.9 * math.sin(2.1 * 6 + k * math.pi / 2)
        bx = 2.6 + 0.55 * k
        ax.plot([x0, bx], [6.12, 6.12 + 0.15 * (k + 1)], color=color, lw=1.0, ls=":")
        ax.plot(
            [bx, bx],
            [6.12 + 0.15 * (k + 1), 3.6 - 0.25 * k],
            color=color,
            lw=1.0,
            ls=":",
        )
        ax.add_patch(
            Rectangle(
                (bx - 0.13, 3.3 - 0.25 * k), 0.26, 0.3, color=color, alpha=0.8, lw=0
            )
        )
    ax.add_patch(
        FancyArrowPatch(
            (3.4, 2.4),
            (3.4, 1.6),
            arrowstyle="-|>",
            mutation_scale=12,
            color=IN,
            lw=1.6,
        )
    )
    ax.text(
        3.6,
        2.0,
        "$T$ per yarn: each yarn fed\nthrough the plate from a bobbin\npulling it back",
        color=IN,
        fontsize=8,
        va="center",
    )
    ax.text(
        0,
        3.0,
        "beaten up while\n$W < n\\,T\\cos\\alpha$",
        ha="center",
        fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec=MUTED, lw=0.6),
    )
    ax.set_xlim(-4.6, 7.4)
    ax.set_ylim(-0.8, 8.0)
    ax.set_aspect("equal")
    ax.axis("off")
    _save(
        fig,
        "rope_ends",
        png_dir,
        "The plate settles where the weight balances the yarns' pull along the axis: n yarns at angle "
        "alpha to it pull it\ndown by n T cos(alpha). A light weight draws the yarns round, until the "
        "crossings jam and the contacts take the rest.",
    )


def rope_results(png_dir: Path | None) -> None:
    """The solver's own results: a rope, a plait, and a sinnet beaten up."""
    import json
    import shutil
    import tempfile

    if shutil.which("node") is None:
        print("  rope_results: skipped, needs Node.js")
        return
    from braidpy.braid import Braid
    from braidpy.linking import yarn_linking
    from braidpy.parametric_strand import SMOOTHSTEP, sample_strands, strand_paths
    from braidpy.web import build

    # A plait, laid by braidpy as the rope tests lay it.
    plait = strand_paths(
        Braid((1, -2) * 3, 3), spacing=1.5, amplitude=0.7, profile=SMOOTHSTEP
    )
    spec = {"source": "sinnet", "name": "abok_3044", "cycles": 4, "settle": "physics"}
    with tempfile.TemporaryDirectory() as scratch:
        laid = Path(scratch) / "plait.json"
        laid.write_text(
            json.dumps([y.ravel().tolist() for y in sample_strands(plait, rise=3.0)])
        )
        shapes = _node("shapes", str(laid))
        job = Path(scratch) / "job.json"
        job.write_text(json.dumps(build(spec, tighten=False)["tighten"]))
        sinnet = _node("sinnet", str(job), "shapes")
    before = yarn_linking([_xyz(y) for y in sinnet["laid"]])
    after = yarn_linking([_xyz(y) for y in sinnet["settled"]], sinnet["turn"])
    assert [round(x) for x in after["links"]] == [round(x) for x in before["links"]]

    fig = plt.figure(figsize=(11, 7.4))
    grid = fig.add_gridspec(2, 6, height_ratios=[1, 1.05])

    def side(ax, yarns, title, colors=YARN):
        for k, y in enumerate(yarns):
            p = _xyz(y)
            ax.plot(p[:, 0], p[:, 2], color=colors[k % len(colors)], lw=2.2, alpha=0.9)
        ax.set_aspect("equal")
        ax.set_title(title, fontsize=9)
        ax.tick_params(labelsize=7)

    def section(ax, yarns, title, colors=YARN):
        tops = [_xyz(y)[:, 2].max() for y in yarns]
        height = min(tops)
        lo, hi, mid = 0.3 * height, 0.7 * height, 0.5 * height
        from matplotlib.patches import Circle

        middle = np.concatenate(
            [_xyz(y)[(_xyz(y)[:, 2] > lo) & (_xyz(y)[:, 2] < hi)] for y in yarns]
        )
        cx, cy = middle[:, :2].mean(axis=0)
        for k, y in enumerate(yarns):
            p = _xyz(y)
            m = (p[:, 2] > lo) & (p[:, 2] < hi)
            color = colors[k % len(colors)]
            ax.plot(p[m, 0] - cx, p[m, 1] - cy, color=color, lw=0.8, alpha=0.6)
            for i in range(len(p) - 1):
                if (p[i, 2] - mid) * (p[i + 1, 2] - mid) <= 0 and p[i, 2] != p[
                    i + 1, 2
                ]:
                    f = (mid - p[i, 2]) / (p[i + 1, 2] - p[i, 2])
                    c = p[i] + f * (p[i + 1] - p[i])
                    ax.add_patch(
                        Circle(
                            (c[0] - cx, c[1] - cy), 0.5, color=color, alpha=0.75, lw=0
                        )
                    )
                    break
        ax.set_aspect("equal")
        ax.autoscale()
        ax.set_title(title, fontsize=9)
        ax.tick_params(labelsize=7)

    side(fig.add_subplot(grid[0, 0]), shapes["ropeLaid"], "two-ply rope,\nlaid loose")
    side(fig.add_subplot(grid[0, 1]), shapes["rope"], "pulled taut:\nradius 1/2")
    section(
        fig.add_subplot(grid[0, 2]), shapes["rope"], "its cross-section:\none track"
    )
    side(fig.add_subplot(grid[0, 3]), shapes["plaitLaid"], "plait, laid")
    side(fig.add_subplot(grid[0, 4]), shapes["plait"], "pulled taut,\nfree to turn")
    section(
        fig.add_subplot(grid[0, 5]),
        shapes["plait"],
        "its cross-section:\none flat track",
    )

    side(
        fig.add_subplot(grid[1, 0]),
        sinnet["laid"],
        "ABOK #3044, 4 cycles:\nlaid by braidpy",
    )
    side(fig.add_subplot(grid[1, 1]), sinnet["settled"], "beaten up")
    section(fig.add_subplot(grid[1, 2]), sinnet["settled"], "beaten up:\ncross-section")
    history = np.asarray(sinnet["history"], dtype=float)
    ax = fig.add_subplot(grid[1, 3:])
    ax.plot(history[:, 0], sinnet["height"] + history[:, 1], color=INK, lw=1.5)
    ax.set_xlabel("steps")
    ax.set_ylabel("braid length, diameters", color=INK)
    twin = ax.twinx()
    twin.semilogy(history[:, 0], history[:, 2], color=IN, lw=1.0)
    twin.set_ylabel("largest force left", color=IN)
    twin.spines["right"].set_visible(True)
    twin.tick_params(colors=IN)
    ax.set_title("how the sinnet settles", fontsize=9)
    fig.tight_layout()
    _save(
        fig,
        "rope_results",
        png_dir,
        "Computed by web/rope.js (tests/js/rope_cases.js). The sinnet's closure links the same before "
        "and after, checked here and in tests/test_rope.py.",
    )


# The ladder of horn gears, two of its gears split, that horn_gear_layout.md
# is about: the graph as Braid Studio's "Your own machine" takes it.
SPLIT_LADDER = (
    "A0-A1:3 A0-B0 A1-A2:3 A1-B1:3 A2-A3a A2-B2:3 A3a-B3a B0-B1 B1-B2 B2-B3a "
    "A3b-A4:3 A3b-B3b A4-A5:3 A4-B4:3 A5-A6 A5-B5:3 A6-B6 B3b-B4 B4-B5 B5-B6 "
    "A3a+A3b B3a+B3b"
)


def _wrapped(note: str) -> str:
    """A figure's note in lines, not one as wide as its words: the horn
    gear figures' notes are long."""
    import textwrap

    return textwrap.fill(note, 120)


def _axles(machine) -> tuple[dict, dict, list]:
    """A machine's axles: each centre once, its radius, and the pairs of axles
    that mesh, the parts of a split gear being one axle."""
    from braidpy.horn_gear.layout import compute_layout, gear_radii

    centers, radii = compute_layout(machine), gear_radii(machine)
    axle = {name: name.rstrip("ab") if name[-1] in "ab" else name for name in centers}
    at = {axle[n]: centers[n] for n in centers}
    size = {axle[n]: radii[n] for n in centers}
    meshes = sorted(
        {tuple(sorted((axle[c.gear_a], axle[c.gear_b]))) for c in machine.connections}
    )
    return at, size, meshes


def _draw_gears(ax, at, size, meshes) -> tuple[float, float]:
    """Gears as circles, each mesh a line between centres: green if the two
    touch, within 1%, red if not; two gears that do not mesh but overlap are
    joined in red too.  Returns the worst mesh error and the worst overlap,
    as shares of the two radii."""
    worst_mesh = worst_overlap = 0.0
    for name, (x, y) in at.items():
        ax.add_patch(plt.Circle((x, y), size[name], fill=False, color=INK, lw=0.8))
        ax.text(x, y, name, ha="center", va="center", fontsize=7, color=MUTED)
    names = sorted(at)
    for i, a in enumerate(names):
        for b in names[i + 1 :]:
            touching = size[a] + size[b]
            apart = math.dist(at[a], at[b])
            if (a, b) in meshes:
                error = abs(apart - touching) / touching
                worst_mesh = max(worst_mesh, error)
                color = MARK if error < 0.01 else LIMIT
            elif apart < touching:
                worst_overlap = max(worst_overlap, (touching - apart) / touching)
                color = LIMIT
            else:
                continue
            ax.plot(*zip(at[a], at[b]), color=color, lw=1.4)
    ax.set_aspect("equal")
    ax.autoscale_view()
    ax.axis("off")
    return worst_mesh, worst_overlap


def gear_layout_ladder(png_dir: Path | None) -> None:
    """The split ladder laid out as Kamada-Kawai shrunk left it, and relaxed."""
    import networkx as nx

    from braidpy.horn_gear.described import machine_from_graph

    machine = machine_from_graph(SPLIT_LADDER, 4)
    at, size, meshes = _axles(machine)
    # Before: the graph laid out, each mesh as long as its two radii at the
    # convention (radius sqrt(horns)), then shrunk till no mesh was longer,
    # as compute_layout did.
    horns = {name: 4 for name in at}
    for part in SPLIT_LADDER.split():
        if ":3" in part:
            horns[part.split("-")[1].split(":")[0]] = 3
    horns.update({"A3": 8, "B3": 8})
    convention = {name: math.sqrt(h) for name, h in horns.items()}
    graph = nx.Graph()
    for a, b in meshes:
        graph.add_edge(a, b, len=convention[a] + convention[b])
    try:
        raw = nx.kamada_kawai_layout(graph, weight="len")
    except ImportError:  # without SciPy, the spring layout, as compute_layout did
        raw = nx.spring_layout(graph, seed=42, iterations=500)
    shrink = min(
        graph[a][b]["len"] / math.dist(raw[a], raw[b]) for a, b in graph.edges()
    )
    before = {name: tuple(shrink * np.asarray(xy)) for name, xy in raw.items()}

    fig, (left, right) = plt.subplots(1, 2, figsize=(9.5, 4.6))
    mesh_before, overlap_before = _draw_gears(left, before, convention, meshes)
    left.set_title("before: laid out, then shrunk\ntill no mesh is too long")
    mesh_after, overlap_after = _draw_gears(right, at, size, meshes)
    right.set_title("after: relaxed (ring_geometry),\nthen timed (time_ring)")
    # The claims horn_gear_layout.md makes of these two pictures.
    assert mesh_before > 0.5 and overlap_before > 0.2
    assert mesh_after < 0.01 and overlap_after == 0.0
    _save(
        fig,
        "gear_layout_ladder",
        png_dir,
        _wrapped(
            f"Green: two gears that mesh and touch (within 1%). Red: a mesh too short "
            f"or too long, or two gears that do not mesh but overlap. Before, the "
            f"worst mesh is {mesh_before:.0%} off; after, {mesh_after:.1%}, every gear "
            f"its own size within 0.75 to 1.3 of sqrt(horns)."
        ),
    )


def gear_layout_relax(png_dir: Path | None) -> None:
    """One round of the relaxation, for a mesh and for two gears apart."""
    fig, (left, right) = plt.subplots(1, 2, figsize=(9.5, 3.2))
    for ax, (ri, rj, d, title, meshing) in zip(
        (left, right),
        (
            (1.0, 0.8, 2.6, "two gears that mesh: drawn to touch", True),
            (1.0, 0.8, 1.5, "two gears that do not: pushed apart", False),
        ),
    ):
        pi, pj = np.array([0.0, 0.0]), np.array([d, 0.0])
        ax.add_patch(plt.Circle(pi, ri, fill=False, color=INK))
        ax.add_patch(plt.Circle(pj, rj, fill=False, color=INK))
        ax.plot([0, d], [0, 0], color=MUTED, lw=0.8)
        ax.text(0, 0.08, "$p_i$", ha="center")
        ax.text(d, 0.08, "$p_j$", ha="center")
        ax.text(-ri / 2, -0.25, "$r_i$", ha="center", color=MUTED)
        ax.text(d + rj / 2, -0.25, "$r_j$", ha="center", color=MUTED)
        ax.annotate(
            "", (d, -1.25), (0, -1.25), arrowprops={"arrowstyle": "<->", "color": INK}
        )
        ax.text(d / 2, -1.45, "$d_{ij}$", ha="center")
        if meshing:
            error = d - (ri + rj)
            ax.annotate(
                "",
                (error / 2, 0.55),
                (0, 0.55),
                arrowprops={"arrowstyle": "->", "color": MARK},
            )
            ax.annotate(
                "",
                (d - error / 2, 0.55),
                (d, 0.55),
                arrowprops={"arrowstyle": "->", "color": MARK},
            )
            ax.text(
                d / 2,
                1.05,
                "$e = d_{ij} - (r_i + r_j) > 0$: closer, and larger",
                ha="center",
                color=MARK,
            )
        else:
            short = 1.1 * (ri + rj) - d
            ax.annotate(
                "",
                (-short / 2, 0.55),
                (0, 0.55),
                arrowprops={"arrowstyle": "->", "color": LIMIT},
            )
            ax.annotate(
                "",
                (d + short / 2, 0.55),
                (d, 0.55),
                arrowprops={"arrowstyle": "->", "color": LIMIT},
            )
            ax.text(
                d / 2,
                1.05,
                "$s = (1 + c)(r_i + r_j) - d_{ij} > 0$: apart",
                ha="center",
                color=LIMIT,
            )
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.set_xlim(-1.4, d + 1.2)
        ax.set_ylim(-1.7, 1.4)
        ax.axis("off")
    _save(fig, "gear_layout_relax", png_dir)


def split_axles_meet(png_dir: Path | None) -> None:
    """Two split axles meshing twice: touching, the a horns meeting at the
    contact as a step begins, the b horns half a step on."""
    from braidpy.horn_gear.described import machine_from_graph

    machine = machine_from_graph("A1-B1 A2-B2 A1+A2 B1+B2", 4)
    phases = {c.name: c.phase for c in machine.connections}
    assert phases == {"A1-B1": 0.0, "A2-B2": 0.5}
    horns = 8
    pitch = 2 * math.pi / horns
    radius = 1.0
    ca, cb = np.array([-radius, 0.0]), np.array([radius, 0.0])
    contact = np.array([0.0, 0.0])

    def horn(center, angle):
        return center + radius * np.array([math.cos(angle), math.sin(angle)])

    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.6))
    for ax, t in zip(axes, (0.0, 0.5)):
        # A step turns each part one of its slots, two pitches of the axle;
        # A anticlockwise, B clockwise, horn 0 of each, part a, at the
        # contact as the step begins.
        there = []
        for center, start, turn in ((ca, 0.0, 1), (cb, math.pi, -1)):
            ax.add_patch(plt.Circle(center, radius, fill=False, color=MUTED, lw=0.8))
            for k in range(horns):
                point = horn(center, start + turn * (k * pitch + t * 2 * pitch))
                part = "a" if k % 2 == 0 else "b"
                ax.plot(*point, "o", color=OUT if part == "a" else IN, ms=6)
                if math.dist(point, contact) < 1e-9:
                    there.append(part)
        assert there == (["a", "a"] if t == 0.0 else ["b", "b"])
        ax.plot(*contact, "s", mfc="none", mec=INK, ms=11)
        ax.text(*(ca + [0, -0.12]), "A", ha="center", color=MUTED)
        ax.text(*(cb + [0, -0.12]), "B", ha="center", color=MUTED)
        ax.set_title(
            "tick 0, the step's end:\nthe a horns meet and hand over"
            if t == 0.0
            else "tick 1, half a step on:\nthe b horns, at the same point"
        )
        ax.set_aspect("equal")
        ax.axis("off")
    _save(
        fig,
        "split_axles_meet",
        png_dir,
        _wrapped(
            "Two split axles of eight horns, parts a (blue) and b (orange) taking "
            "turns, meshing twice: they touch at one contact (square). A turns "
            "anticlockwise, B clockwise, a step being two pitches, so a horn of each "
            "comes round every half step: band a hands over at the step's end, band "
            "b half a step on (Connection.phase 0.5), never there together."
        ),
    )


def machine_size_survey(png_dir: Path | None) -> None:
    """How large every machine must be for its bobbins: its horn gap, in
    bobbin diameters, for the two carriers coming closest to clear."""
    from braidpy.horn_gear.described import machine_from_graph
    from braidpy.horn_gear.simulation import state_period
    from braidpy.horn_gear.take_off import clearance
    from braidpy.machine_catalog import CATALOG

    machines = {name: entry.make for name, entry in sorted(CATALOG.items())}
    machines.update(
        {
            "split in three": lambda: machine_from_graph("H1-A H2-B H3-C H1+H2+H3", 3),
            "split pair, neighbours": lambda: machine_from_graph(
                "X-A1 A1-B1 A2-B2 B2-Y A1+A2 B1+B2", 4
            ),
            "split ladder": lambda: machine_from_graph(SPLIT_LADDER, 4),
        }
    )
    names, needed = [], []
    for name, make in machines.items():
        machine = make()
        loading = machine.default_carriers()
        steps = min(state_period(machine, loading) or 1, 600)
        room = clearance(machine, steps, loading)
        if room is None:
            continue  # driven by a card, or one carrier
        assert room.met is None, name
        names.append(name)
        needed.append(1 / room.share)
    cataloged = needed[: len([n for n in names if n in CATALOG])]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    colors = [LIMIT if n not in CATALOG else MUTED for n in names]
    ax.barh(names, needed, color=colors)
    ax.invert_yaxis()
    ax.set_xlabel("smallest horn gap needed, in bobbin diameters")
    _save(
        fig,
        "machine_size_survey",
        png_dir,
        _wrapped(
            f"Cataloged machines need horns {min(cataloged):.1f} to "
            f"{max(cataloged):.1f} bobbin diameters apart for their carriers to "
            "clear each other; in red, the machines of your own this page "
            "describes."
        ),
    )


def _ashley_panel(ax, title, outline, holes=(), across=None) -> list[tuple[int, int]]:
    """One shape drawn as Ashley draws it, on ``ax``: its outline and holes,
    its lines coloured by direction, each bight a loop beyond the outline,
    numbered as its space.  Returns its sinnet's moves."""
    from braidpy.making.ashley import (
        _loops,
        _round_the_outline,
        _sides,
        shape_diagram,
        sinnet_from_shape,
    )

    colors = [OUT, IN, MARK]
    lines, joins, bights = shape_diagram(outline, holes, across)
    loops = _loops(outline, holes)
    for corners in loops:
        closed = np.vstack([corners, corners[:1]])
        ax.plot(closed[:, 0], closed[:, 1], color=MUTED, lw=1)
    for line in lines:
        (x0, y0), (x1, y1) = line.ends
        ax.plot([x0, x1], [y0, y1], color=colors[line.direction % 3], lw=1.6)
    sides = _sides(loops)
    ends: dict[int, list] = {}
    for line, join in zip(lines, joins):
        for end, space in zip(line.ends, join):
            ends.setdefault(space, []).append(np.asarray(end))
    for number, at in enumerate(bights, start=1):
        p, q = ends[number]
        # Out of the shape, square to the sides its two ends are on: every
        # outline goes round with the shape on its left, a hole's too.
        out = np.zeros(2)
        for end in (p, q):
            a, b = sides[_round_the_outline(loops, end)[2]]
            out += np.array([(b - a)[1], -(b - a)[0]]) / np.linalg.norm(b - a)
        out = out / np.linalg.norm(out)
        # Smaller round a hole, where there is less room.
        reach = 0.5 if _round_the_outline(loops, p)[0] else 1.0
        tip = np.asarray(at) + out * reach * (0.3 + 0.35 * np.linalg.norm(q - p))
        t = np.linspace(0, 1, 30)[:, None]
        loop = (1 - t) ** 2 * p + 2 * (1 - t) * t * tip + t**2 * q
        ax.plot(loop[:, 0], loop[:, 1], color=INK, lw=1)
        ax.text(
            *(tip + out * 0.3 * reach),
            str(number),
            ha="center",
            va="center",
            fontsize=8,
            color=INK,
        )
    ax.set_title(title, fontsize=10, pad=24)
    ax.set_aspect("equal")
    ax.axis("off")
    return sinnet_from_shape(outline, holes=holes, across=across).moves


def ashley_shapes(png_dir: Path | None) -> None:
    """Ashley's diagrams of a triangle and an oblong, as
    sinnet_from_shape draws them: the lines, the bights numbered as the
    spaces, and the moves in his order."""
    from braidpy.making.ashley import oblong, triangle
    from braidpy.solid_sinnets_catalog import abok_3047

    shapes = {"triangle, #3047": triangle(4), "oblong, #3071": oblong(6, 2)}
    fig, axes = plt.subplots(1, 2, figsize=(9.5, 3.8), width_ratios=[1.1, 1.3])
    notes = []
    for ax, (title, outline) in zip(axes, shapes.items()):
        moves = _ashley_panel(ax, title, outline)
        notes.append(f"{title}: " + ", ".join(f"{a}>{b}" for a, b in moves))
    # What the page says of the triangle: the book's own table.
    assert _ashley_panel(plt.figure().gca(), "", shapes["triangle, #3047"]) == [
        tuple(move) for move in abok_3047.moves
    ]
    plt.close()
    _save(
        fig,
        "ashley_shapes",
        png_dir,
        _wrapped(
            "Lines parallel to the sides, half a spacing in, coloured by direction; "
            "each turns at the outline in a bight, numbered as the stand's spaces. "
            "Moves in the book's order: " + "; ".join(notes) + "."
        ),
    )


def ashley_grids(png_dir: Path | None) -> None:
    """Shapes on a grid, as sinnet_from_shape draws them: an L on the
    square grid, its lines cut where the outline turns; a hollow square, the
    spaces round its hole numbered between the outer ones; a square on a
    corner on the diagonal grid, the lines of the book's #3073."""
    from braidpy.making.ashley import _drawn, grid_lines, grid_outline, grid_shape
    from braidpy.solid_sinnets_catalog import abok_3073

    shapes = {
        "an L, 5 lines, arms 2": ("square", "L", 5, 2),
        "a hollow square, 8 lines": ("square", "frame", 8, 2),
        "a square on a corner, #3073": ("diagonal", "square", 6, 2),
    }
    fig, axes = plt.subplots(1, 3, figsize=(11, 4.2))
    for ax, (title, (grid, shape, size, height)) in zip(axes, shapes.items()):
        outline, *holes = grid_outline(grid, grid_shape(grid, shape, size, height))
        moves = _ashley_panel(ax, title, outline, holes, grid_lines(grid))
        if shape == "square":
            # What the page says of it: the book's lines.
            assert _drawn(moves) == _drawn([tuple(m) for m in abok_3073.moves])
    _save(
        fig,
        "ashley_grids",
        png_dir,
        _wrapped(
            "Shapes on a grid: an L, its lines cut where the outline turns back; a "
            "hollow square, the spaces round its hole numbered between the outer ones; "
            "a square on a corner, its lines across and up, the book's #3073."
        ),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--png", type=Path, default=None, help="also write PNG copies")
    args = parser.parse_args()

    _style()
    print("the rope:")
    rope_one_curve_repeated(args.png)
    rope_clearance(args.png)
    rope_settling_radius(args.png)
    print("the braided tube:")
    tube_cross_section(args.png)
    tube_swing(args.png)
    tube_radius_conditions(args.png)
    tube_cover_gap(args.png)
    print("the rope solver:")
    rope_model(args.png)
    rope_ends(args.png)
    rope_results(args.png)
    print("the horn gear machine:")
    gear_layout_ladder(args.png)
    gear_layout_relax(args.png)
    split_axles_meet(args.png)
    machine_size_survey(args.png)
    ashley_shapes(args.png)
    ashley_grids(args.png)
    print("\n15 figures written to docs/source/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
