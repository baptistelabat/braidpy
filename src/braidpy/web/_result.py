# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""What :func:`braidpy.web.build` hands the page: the braid as plain data, the
timeline of what made it, and — for a page that tightens the yarns itself —
what tightening them needs."""

from __future__ import annotations

import math
from contextvars import ContextVar
from typing import Any, Dict, Hashable, List, Optional, Sequence, cast

import numpy as np

from braidpy.web._settings import ITERATIONS
from braidpy.web._spec import Count
from braidpy.web._types import Clock, Info, Result, Spec, Strand, Tightening, Timeline

# Points along a yarn are rounded to this many decimals: a tenth of a
# thousandth of a yarn is finer than any screen.
_DECIMALS = 4

# Above this many points along a yarn, the page gets one in so many.
_MAX_POINTS = 1500

# Above this many instants, the timeline of what made a braid gets one in
# so many: smooth enough for Grow to replay, small enough to send.
_MAX_TIMES = 3000

# The same colours the horn gear animation gives its carriers.
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

# Set while a braid is built for a page that tightens it itself: the yarns
# are then only laid, and what tightening them needs is handed over instead.
_PAGE_TIGHTENS: ContextVar[bool] = ContextVar("page_tightens", default=False)

_TIGHTENING: ContextVar[Optional[Dict[str, Any]]] = ContextVar(
    "tightening", default=None
)


def _tightened(
    paths,
    diameter: float,
    iterations: int,
    core_radius=None,
    rigid: Sequence[Hashable] = (),
):
    """The yarns pulled taut — or, for a page that does it itself, as laid,
    with what it needs to do so noted for :func:`_result`."""
    from braidpy.take_off import tighten_yarns

    if iterations == 0:
        return paths
    if _PAGE_TIGHTENS.get():
        formed = paths.formed()
        _TIGHTENING.set(
            {
                "n_yarns": int(formed.shape[0]),
                "n": int(formed.shape[1]),
                "spacing": float(paths._level_spacing()),
                "yarn_diameter": float(diameter),
                "iterations": int(iterations),
                # tighten_yarns' own defaults.
                "step": 20.0,
                "tolerance": 1e-3,
                "hold_top": True,
                "core_radius": None if core_radius is None else float(core_radius),
                "centre": [float(paths.axis[0]), float(paths.axis[1])],
                "xy": np.round(formed[:, :, :2].reshape(-1), 9).tolist(),
                "rigid": [k in rigid for k in paths.points],
            }
        )
        return paths
    tightened, _ = tighten_yarns(
        paths, diameter, iterations=iterations, core_radius=core_radius, rigid=rigid
    )
    return tightened


def _tighten(
    paths,
    spec: Spec,
    diameter: float,
    iterations: Count = ITERATIONS,
    rigid: Sequence[Hashable] = (),
):
    return _tightened(paths, diameter, iterations.read(spec), rigid=rigid)


def _result(
    title: str,
    paths,
    diameter: float,
    colours: Optional[Sequence[str]] = None,
    names: Optional[Sequence[str]] = None,
    info: Optional[Info] = None,
    notes: Sequence[str] = (),
    timeline: Optional[Timeline] = None,
) -> Result:
    """Everything the page draws, as plain data."""
    n = paths.formed_count
    keys: List[Hashable] = list(paths.points)
    stride = max(1, math.ceil(n / _MAX_POINTS))
    centre = np.array([paths.axis[0], paths.axis[1], 0.0])
    chosen = list(range(0, n, stride))
    if chosen[-1] != n - 1:
        chosen.append(n - 1)
    strands: List[Strand] = []
    for i, key in enumerate(keys):
        points = np.asarray(paths.points[key], dtype=float)[chosen] - centre
        if not np.all(np.isfinite(points)):
            raise ValueError("The braid could not be laid: its yarns ran off.")
        colour = colours[i % len(colours)] if colours else _PALETTE[i % len(_PALETTE)]
        name = names[i] if names else f"Strand {key}"
        strands.append(
            {
                "name": name,
                "colour": colour,
                "points": np.round(points, _DECIMALS).tolist(),
            }
        )
    out_info: Info = {"n_strands": len(keys)}
    out_info.update(info or {})
    tightening = _TIGHTENING.get()
    if tightening is None:
        try:
            out_info["closest_approach"] = round(
                float(paths.closest_approach(include_fell=False)), _DECIMALS
            )
        except Exception:  # an estimate only; never worth failing the braid over
            pass
    result: Result = {
        "title": title,
        "strands": strands,
        # When each point was laid, in the source's time: the same for
        # every yarn, since they are laid together.
        "times": np.round(np.asarray(paths.times)[chosen], _DECIMALS).tolist(),
        "yarn_diameter": diameter,
        "info": out_info,
        "notes": list(notes),
    }
    if timeline is not None:
        result["timeline"] = timeline
    if tightening is not None:
        # The axis taken off the strands' points is the tightening's centre.
        result["tighten"] = cast(Tightening, {**tightening, "chosen": chosen})
    return result


def _timeline(
    trajectories,
    keys: Sequence[Hashable],
    kind: str,
    clock: Optional[Clock] = None,
    ring=None,
) -> Timeline:
    """What made the braid, seen from above, over time: for the page to
    animate in step with the braid.

    Args:
        trajectories: The carriers' paths.
        keys: The strands, in the order the braid gives them.
        kind: ``disk`` — strands drawn as spokes to the middle — or
            ``machine``, or ``line``.
        clock: The source's time at some instants, and the braid's then;
            the same times if None.
        ring: For a disk, the strands round the ring the braid was laid
            from: the braid then hangs from the disk turned so each strand
            at the fell is nearest its carrier — see
            :meth:`~braidpy.disk_animation.BraidGrowth.turn_at` — and how
            far it is turned is given at each instant, as ``turn``.
    """
    times = np.asarray(trajectories.times, dtype=float)
    stride = max(1, math.ceil(len(times) / _MAX_TIMES))
    chosen = list(range(0, len(times), stride))
    if chosen[-1] != len(times) - 1:
        chosen.append(len(times) - 1)
    cx, cy = trajectories.centre()
    shift = np.array([cx, cy])

    def plane(points) -> List[List[float]]:
        return np.round(np.asarray(points, dtype=float) - shift, 3).tolist()

    strands = [plane(trajectories.xy[k][chosen]) for k in keys]
    outlines = [
        plane(outline[:: max(1, len(outline) // 400)])
        for outline in trajectories.outlines
    ]
    reach = max(
        float(np.max(np.hypot(*(np.asarray(p) - shift).T)))
        for p in [*trajectories.xy.values(), *trajectories.outlines]
    )
    if clock is None:
        clock = {
            "source": [float(times[0]), float(times[-1])],
            "braid": [float(times[0]), float(times[-1])],
        }
    turn = None
    if ring is not None:
        rows = np.interp(times[chosen], clock["source"], clock["braid"])
        pull = np.zeros(len(chosen), dtype=complex)
        for k in keys:
            at = np.asarray(trajectories.xy[k][chosen], dtype=float) - shift
            on = np.asarray(ring.xy[k], dtype=float)
            x = np.interp(rows, ring.times, on[:, 0])
            y = np.interp(rows, ring.times, on[:, 1])
            carrier = at[:, 0] + 1j * at[:, 1]
            fell = x + 1j * y
            pull += (
                carrier
                / np.maximum(np.abs(carrier), 1e-12)
                * np.conj(fell / np.maximum(np.abs(fell), 1e-12))
            )
        turn = np.round(np.unwrap(np.angle(pull)), 4).tolist()
    timeline: Timeline = {
        "kind": kind,
        "times": np.round(times[chosen], _DECIMALS).tolist(),
        "strands": strands,
        "outlines": outlines,
        "slots": [
            [round(x - cx, 3), round(y - cy, 3), name]
            for x, y, name in trajectories.slots
        ],
        "reach": round(reach, 3),
        "clock": clock,
    }
    if turn is not None:
        timeline["turn"] = turn
    return timeline


def _hues(n: int) -> List[str]:
    from braidpy.ashley_solid_sinnet import strand_colours

    return strand_colours(n)
