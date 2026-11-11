# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
horn_gear/word.py
=================

The braid word a machine and its loading make.

A braid word is not a property of a machine alone.  It is a property of the
machine, how it is threaded, and **a direction to look from** — a braid is a
set of curves in space, and a word records which strand passed in front of
which when they are projected onto a plane.  Two projections of the same braid
give different words.

Two projections are offered, because braiding machines come in two shapes:

- :func:`flat_word` looks along the deck's ``y`` axis, so the carriers are
  ordered left to right and the word is an ordinary Artin word.  This is the
  right reading for a flat braider, whose carriers stay strung out along a
  line.
- :func:`annular_word` looks outward from a point you choose, so the carriers
  are ordered by angle around it and the word is an *annular* one — the
  vocabulary of :mod:`braidpy.annulus_braid`, where index ``n`` is the pair
  whose numbering wraps.  This is the right reading for a tubular braider, and
  the point to choose is normally the axis of the tube.

Both read the word from where the carriers actually are, computed exactly from
the machine at each instant by
:func:`~braidpy.horn_gear.layout.carrier_xy` — not sampled off the yarn
geometry.  A crossing is therefore found wherever two carriers exchange order,
with no dependence on how finely a shape was drawn.

:func:`~braidpy.symmetric_braid.braid_word` reads a word off drawn curves
instead, and the two should agree for a flat machine.  The tests check that
they do, which is worth more than either on its own: one works from the
machine's motion, the other from the shape that motion lays down.
"""

from __future__ import annotations

import math
from collections.abc import Hashable, Sequence
from dataclasses import dataclass
from typing import Optional, cast

import numpy as np

from .model import BraidingMachine
from .simulation import CarrierId
from .take_off import carrier_trajectories
from .tracks import Position, simulation_period

__all__ = ["AnnularWord", "annular_word", "deck_centre", "flat_word"]


def _trajectories(
    machine: BraidingMachine,
    carriers: dict[CarrierId, Position] | None,
    n_steps: int | None,
    n_substeps: int,
    scale: float,
):
    """Carrier positions in the deck plane, one cycle by default — and each
    axial yarn's, a strand of the braid that stands still where it rises
    through the deck (:func:`~braidpy.horn_gear.layout.axial_position`),
    numbered after the carriers, in the order the machine lists them.  The
    carriers braid round it, so it belongs in the word as one strand: a
    carrier crosses it where it passes its column."""
    from dataclasses import replace

    from .layout import axial_positions

    if n_steps is None:
        n_steps = simulation_period(machine)
    tracks = carrier_trajectories(
        machine,
        n_steps,
        carrier_positions=carriers,
        n_substeps=n_substeps,
        scale=scale,
    )
    axials = getattr(machine, "axials", ())
    if not axials:
        return tracks
    columns = axial_positions(machine, tracks.layout)
    # Carriers are numbered; the axials after the last of them.
    first = max((k for k in tracks.xy if isinstance(k, int)), default=-1) + 1
    standing: dict[Hashable, np.ndarray] = {
        first + k: np.tile(
            np.asarray(columns[axial.name], dtype=float), (len(tracks.times), 1)
        )
        for k, axial in enumerate(axials)
    }
    return replace(tracks, xy={**tracks.xy, **standing})


def deck_centre(machine: BraidingMachine, scale: float = 1.0) -> tuple[float, float]:
    """The centroid of the gears, as a default point to look out from.

    For a machine whose gears ring a hole — a tubular braider — this is the
    axis of the tube, which is the point :func:`annular_word` wants.  For any
    other shape it is just a centroid, and worth replacing with a point you
    chose on purpose.

    Args:
        machine: The machine definition.
        scale: Layout scale.

    Returns:
        The ``(x, y)`` centroid of the gear centres.
    """
    from .layout import compute_layout

    centres = list(compute_layout(machine, scale=scale).values())
    return (
        sum(x for x, _ in centres) / len(centres),
        sum(y for _, y in centres) / len(centres),
    )


def flat_word(
    machine: BraidingMachine,
    carriers: Optional[dict[CarrierId, Position]] = None,
    n_steps: Optional[int] = None,
    n_substeps: int = 64,
    scale: float = 1.0,
) -> list[int]:
    """The Artin word of the braid this machine makes, seen from the front.

    Carriers are ordered left to right across the deck and a crossing is
    recorded whenever two neighbours exchange places.  Its sign says which
    passed in front: positive when the one arriving from the left passes on
    the near side, the convention
    :func:`~braidpy.symmetric_braid.braid_word` and
    :meth:`~braidpy.braid.Braid.to_parametric_strands` both use.

    This suits a machine whose carriers stay strung out along a line.  On a
    tubular braider the left-to-right order is meaningless — the carriers go
    round — and the word comes out as noise; use :func:`annular_word` there.

    Args:
        machine: The machine definition.
        carriers: The loading; the machine's own if None.
        n_steps: How many steps to read; one full cycle if None.
        n_substeps: Samples per step.  Two carriers exchanging and exchanging
            back within one sample are missed, so this is generous by default.
        scale: Layout scale.

    Returns:
        The word, as signed generator indices.

    """
    tracks = _trajectories(machine, carriers, n_steps, n_substeps, scale)
    ids = sorted(tracks.xy)
    across = np.column_stack([tracks.xy[cid][:, 0] for cid in ids])
    depth = np.column_stack([tracks.xy[cid][:, 1] for cid in ids])

    order = sorted(range(len(ids)), key=lambda k: across[0, k])
    word: list[int] = []
    for sample in range(1, len(tracks.times)):
        for slot in range(len(ids) - 1):
            first, second = order[slot], order[slot + 1]
            before = across[sample - 1, first] - across[sample - 1, second]
            after = across[sample, first] - across[sample, second]
            if before < 0 <= after:
                in_front = depth[sample, first] > depth[sample, second]
                word.append(slot + 1 if in_front else -(slot + 1))
                order[slot], order[slot + 1] = second, first
    return word


@dataclass(frozen=True)
class AnnularWord:
    """A braid read as it winds round a point.

    Args:
        generators: The crossings, as signed indices.  ``i`` in 1..``n-1`` is
            the pair at cyclic positions ``i-1`` and ``i``; ``n`` is the pair
            whose numbering wraps, which a flat word has no room for — the
            same numbering :func:`~braidpy.annulus_braid.wrap_crossing` uses.
            A positive index means the strand arriving from the lower position
            passed **outside**, further from the centre.
        winding: Per carrier, how many times it went round the centre over the
            stretch read.  Half the carriers of a tubular braider go one way
            and half the other, so these come in both signs.
        centre: The point the braid was read around.
        n_strands: How many strands there are, which is the index of the
            wrapping pair.
    """

    generators: list[int]
    winding: dict[CarrierId, float]
    centre: tuple[float, float]
    n_strands: int

    @property
    def net_winding(self) -> float:
        """The whole cross-section's rotation: the sum of the windings.

        Zero for a braid that twists as much one way as the other, which is
        what a balanced tubular braider makes.
        """
        return float(sum(self.winding.values()))


def annular_word(
    machine: BraidingMachine,
    around: Optional[tuple[float, float]] = None,
    carriers: Optional[dict[CarrierId, Position]] = None,
    n_steps: Optional[int] = None,
    n_substeps: int = 64,
    scale: float = 1.0,
) -> AnnularWord:
    """The braid this machine makes, read as it winds round a point.

    Carriers are ordered by their angle about ``around``, and two of them
    cross exactly when their angles coincide — when their *unwrapped* angles
    differ by a whole turn.  The generator's index is where the pair sits in
    that cyclic order, so index ``n`` is the pair straddling the point where
    the numbering wraps, and its sign says which passed outside.

    Nothing distinguishes that wrapping pair physically: it is an artefact of
    having to start numbering somewhere, exactly as in
    :mod:`braidpy.annulus_braid`.

    Args:
        machine: The machine definition.
        around: The point to look out from; :func:`deck_centre` if None.
        carriers: The loading; the machine's own if None.
        n_steps: How many steps to read; one full cycle if None.
        n_substeps: Samples per step.
        scale: Layout scale.

    Returns:
        The crossings, and how far each carrier wound round the centre.

    """
    tracks = _trajectories(machine, carriers, n_steps, n_substeps, scale)
    if around is None:
        around = deck_centre(machine, scale=scale)

    ids = sorted(tracks.xy)
    count = len(ids)
    offsets = (
        np.column_stack([tracks.xy[cid][:, 0] - around[0] for cid in ids]),
        np.column_stack([tracks.xy[cid][:, 1] - around[1] for cid in ids]),
    )
    radius = np.hypot(offsets[0], offsets[1])
    angle = np.unwrap(np.arctan2(offsets[1], offsets[0]), axis=0)

    order = sorted(range(count), key=lambda k: angle[0, k] % (2 * math.pi))
    word: list[int] = []
    for sample in range(1, len(tracks.times)):
        for slot in range(count):
            first, second = order[slot], order[(slot + 1) % count]
            # Cyclically adjacent strands cross when their unwrapped angles
            # pass through a whole number of turns of one another.
            before = angle[sample - 1, first] - angle[sample - 1, second]
            after = angle[sample, first] - angle[sample, second]
            if math.floor(before / (2 * math.pi)) == math.floor(after / (2 * math.pi)):
                continue
            outside = radius[sample, first] > radius[sample, second]
            word.append(slot + 1 if outside else -(slot + 1))
            order[slot], order[(slot + 1) % count] = second, first

    turns = 2 * math.pi
    winding = {
        cid: float((angle[-1, k] - angle[0, k]) / turns) for k, cid in enumerate(ids)
    }
    return AnnularWord(
        generators=word,
        winding=winding,
        centre=(float(around[0]), float(around[1])),
        n_strands=count,
    )


def strands_for_checking(machine: BraidingMachine, **kwargs) -> Sequence:
    """The machine's yarns, shaped for :func:`~braidpy.symmetric_braid.braid_word`.

    A convenience for the cross-check: it reads a word off *drawn curves*,
    where :func:`flat_word` reads one off the machine's own motion.  Agreement
    between the two is the point — the shape says the same thing as the
    mechanism.

    Args:
        machine: The machine definition.
        **kwargs: Passed to :func:`~braidpy.horn_gear.take_off.yarn_paths`.

    Returns:
        One object per yarn, answering ``position(z)`` over a common
        ``length``: the carriers' by id, then the axials' if the paths have
        them (``axials=True``), in the machine's order.
    """
    from .take_off import yarn_paths

    paths = yarn_paths(machine, **kwargs)

    class _Yarn:
        """A yarn's samples, read as a curve from the deck upward."""

        length = 1.0

        def __init__(self, points: np.ndarray) -> None:
            self._points = points

        def position(self, z: float) -> tuple[float, float, float]:
            last = len(self._points) - 1
            at = min(max(z, 0.0), 1.0) * last
            low = int(at)
            step = at - low
            here = self._points[low]
            nxt = self._points[min(low + 1, last)]
            point = here + (nxt - here) * step
            return float(point[0]), float(point[1]), float(point[2])

    # Carriers by id, then the axials in the machine's order: as the words
    # number them.
    axials = [a.name for a in getattr(machine, "axials", ()) if a.name in paths.points]
    carriers = sorted(cast("list[int]", [k for k in paths.points if k not in axials]))
    return [_Yarn(paths.points[k]) for k in [*carriers, *axials]]
