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
- :func:`ring_word` reads round an axis — a core, or a spot one could be
  fed at — and writes the braid as moves round a ring
  (:class:`RingWord`), turns and all: with the core kept as a strand it is
  the braid the machine makes round it, and it can be shortened
  (:meth:`RingWord.shortened`).
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

from braidpy.braid import Braid

from .model import Axial, BraidingMachine
from .simulation import CarrierId, state_period
from .take_off import carrier_trajectories
from .tracks import Position, simulation_period

__all__ = [
    "AnnularWord",
    "RingWord",
    "annular_word",
    "deck_centre",
    "default_axis",
    "flat_word",
    "ring_word",
]


def _trajectories(
    machine: BraidingMachine,
    carriers: dict[CarrierId, Position] | None,
    n_steps: int | None,
    n_substeps: int,
    scale: float,
):
    """Carrier positions in the deck plane, one cycle by default — as long as
    this loading takes to be back as it started
    (:func:`~braidpy.horn_gear.simulation.state_period`), or, for a machine
    that never is, until every slot is (:func:`simulation_period`) — and each
    axial yarn's, a strand of the braid that stands still where it rises
    through the deck (:func:`~braidpy.horn_gear.layout.axial_position`),
    numbered after the carriers, in the order the machine lists them.  The
    carriers braid round it, so it belongs in the word as one strand: a
    carrier crosses it where it passes its column."""
    from dataclasses import replace

    from .layout import axial_positions

    if n_steps is None:
        n_steps = state_period(machine, carriers) or simulation_period(machine)
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


# Carriers less than this far apart across the deck are level: the
# difference is rounding, so they have not crossed.
_LEVEL = 1e-9


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

    # Carriers level at the start, one behind the other, are in the order
    # they came there in: read over a whole period, the machine back as it
    # started, that is how it ended the period before, so that two carriers
    # crossing just as it starts are counted once, here, and not again as
    # they draw level at the end.  Read over less, in the order they part in.
    periodic = np.allclose(across[0], across[-1]) and np.allclose(depth[0], depth[-1])
    tiebreak = across[-2::-1] if periodic else across[1:]
    level = np.round(across[0] / _LEVEL)
    order = sorted(range(len(ids)), key=lambda k: (level[k], *tiebreak[:, k]))
    word: list[int] = []
    for sample in range(1, len(tracks.times)):
        # Passes until no neighbours are left to exchange: in one pass a
        # carrier going right can pass several others, one going left only
        # one, and a missed exchange would leave the order wrong for good.
        # Within a sample each carrier keeps its depth, so the order the
        # exchanges are written in does not change the braid.  Two carriers
        # have crossed only once one is past the other: drawing level is
        # not crossing, as two carriers back where they started level are.
        exchanged = True
        while exchanged:
            exchanged = False
            for slot in range(len(ids) - 1):
                first, second = order[slot], order[slot + 1]
                if across[sample, first] - across[sample, second] > _LEVEL:
                    in_front = depth[sample, first] > depth[sample, second]
                    word.append(slot + 1 if in_front else -(slot + 1))
                    order[slot], order[slot + 1] = second, first
                    exchanged = True
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


# Strands in line with the axis are told apart by their distance from it,
# as an angle this many turns times the distance over the greatest: so
# small no two strands at different angles change order, the same at both
# ends of a period, the carriers being where they were.
_LEVEL_TURNS = 1e-6
# The axis is read from a point this fraction of its clearance away, in a
# direction along no line of the machine's symmetry (_ASKEW radians): no
# strand comes nearer the axis than its clearance, so the braid round the
# point is the braid round the axis, and carriers that meet in line with
# the axis itself, by symmetry, are read in line with the point no longer.
_OFF_AXIS = 0.1
_ASKEW = 1.0


@dataclass(frozen=True)
class RingWord:
    """A machine's braid as moves round a ring, read round an axis.

    Args:
        moves: Crossings ``±1`` to ``±n_strands`` and turns
            ``±(n_strands + 1)``, as :mod:`braidpy.annulus_braid` writes
            them: the slots are numbered clockwise from a seam, as
            :mod:`braidpy.ring_program` numbers places, and a strand
            passing the seam is a turn.
        n_strands: The strands round the axis: the carriers, and the
            machine's axials but the axis's own.
        axis: Where the braid was read round: the core.
        strands: The carrier or axial in each slot to begin with.
    """

    moves: tuple[int, ...]
    n_strands: int
    axis: Axial
    strands: tuple[Hashable, ...]

    def braid(self) -> Braid:
        """The braid with nothing in its middle
        (:func:`~braidpy.annulus_braid.solid_word`): a tube and a flat braid
        curled up are then the same."""
        from braidpy.annulus_braid import solid_word

        return Braid(tuple(solid_word(self.moves, self.n_strands)), self.n_strands)

    def cored(self) -> Braid:
        """The braid round its core, the core strand 1
        (:func:`~braidpy.annulus_braid.cored_word`)."""
        from braidpy.annulus_braid import cored_word

        n = self.n_strands
        return Braid(tuple(cored_word(self.moves, n)), n + 1)

    def shortened(self) -> RingWord:
        """The same braid round the core in as few moves as are found
        (:func:`~braidpy.shortening.shortened_ring`)."""
        from dataclasses import replace

        from braidpy.shortening import shortened_ring

        return replace(self, moves=tuple(shortened_ring(self.moves, self.n_strands)))


def default_axis(machine: BraidingMachine) -> Axial:
    """Where to read a machine's braid round, if not said: the core it
    braids round, or the nearest thing to one.

    In this order: an axial the machine feeds down a ring's hole; the hole
    a ring of gears encloses, which a tubular braider braids round
    (:func:`~braidpy.horn_gear.layout.tube_axials`); an axial the machine
    feeds up a gear, as a soutache's cord; the gear nearest the deck's
    centre (:func:`deck_centre`).

    Args:
        machine: The machine.

    Returns:
        The axis, one of the machine's
        :func:`~braidpy.horn_gear.layout.axial_spots`, or its own axials.
    """
    from .layout import axial_spots, compute_layout, tube_axials

    own = list(getattr(machine, "axials", ()))
    for axial in own:
        if len(axial.anchor) > 1:
            return axial
    layout = compute_layout(machine)
    holes = tube_axials(machine, layout)
    if holes:
        return holes[0]
    if own:
        return own[0]
    x, y = deck_centre(machine)
    gears = [spot for spot in axial_spots(machine, layout) if len(spot.anchor) == 1]
    return min(
        gears,
        key=lambda spot: math.hypot(
            layout[spot.anchor[0]][0] - x, layout[spot.anchor[0]][1] - y
        ),
    )


def ring_word(
    machine: BraidingMachine,
    axis: Optional[Axial] = None,
    carriers: Optional[dict[CarrierId, Position]] = None,
    n_steps: Optional[int] = None,
    n_substeps: int = 64,
) -> RingWord:
    """The braid a machine makes as moves round a ring, read round an axis.

    Seen from the axis, the strands are in a ring: in order round it,
    clockwise from a seam put in the widest gap between them.  Two strands
    neighbours round it cross when they come in line with the axis, the one
    further from it outside; a strand passing the seam, crossing nobody,
    turns the ring by a slot.  Where :func:`annular_word` keeps only the
    order round the axis, this keeps the seam, and so the turns: the braid
    round the axis, its core kept (:meth:`RingWord.cored`), is the braid
    the machine makes round a yarn fed there, exactly.

    The axis matters: round another point the same machine makes another
    braid round its core, the same once the core is taken away
    (:meth:`RingWord.braid`).

    Args:
        machine: The machine.
        axis: What to read the braid round, an axial or a spot one could be
            fed at (:func:`~braidpy.horn_gear.layout.axial_spots`);
            :func:`default_axis` if None.  An axial the machine feeds there
            is the core, not a strand.
        carriers: The loading; the machine's own if None.
        n_steps: How many steps to read: one cycle of the machine if None
            (:func:`~braidpy.horn_gear.simulation.state_period`), or for a
            machine driven by a programme, one pass of it.
        n_substeps: Samples per step.

    Returns:
        The moves, and which strand began where.

    Raises:
        ValueError: If a strand passes through the axis.
    """
    from .layout import axial_position, compute_layout

    if axis is None:
        axis = default_axis(machine)
    centre = axial_position(machine, compute_layout(machine), axis)
    machine = machine.with_axials(
        [a for a in getattr(machine, "axials", ()) if a.anchor != axis.anchor]
    )
    if n_steps is None:
        program = getattr(machine, "program", None)
        n_steps = (
            2 * len(program)
            if program is not None
            else state_period(machine, carriers) or simulation_period(machine)
        )
    # A step more, to begin the period where no two strands are in line.
    tracks = _trajectories(machine, carriers, n_steps + 1, n_substeps, 1.0)
    ids = sorted(tracks.xy, key=str)
    xs = np.column_stack([tracks.xy[k][:, 0] - centre[0] for k in ids])
    ys = np.column_stack([tracks.xy[k][:, 1] - centre[1] for k in ids])
    clearance = float(np.hypot(xs, ys).min())
    if clearance <= 0:
        raise ValueError(f"A strand passes through the axis {axis.name!r}.")
    xs -= _OFF_AXIS * clearance * math.cos(_ASKEW)
    # Clockwise seen from above: angles measured the other way round.
    ys = -(ys - _OFF_AXIS * clearance * math.sin(_ASKEW))
    samples = n_steps * n_substeps + 1
    first = _untied(xs, ys, n_substeps) if _recurs(xs, ys, samples) else 0
    xs, ys = xs[first : first + samples], ys[first : first + samples]
    radius = np.hypot(xs, ys)
    turns = np.unwrap(np.arctan2(ys, xs), axis=0) / (2 * math.pi)
    turns += _LEVEL_TURNS * radius / radius.max()
    moves, start = _ring_moves(turns, radius)
    return RingWord(tuple(moves), len(ids), axis, tuple(ids[k] for k in start))


def _recurs(xs: np.ndarray, ys: np.ndarray, samples: int) -> bool:
    """Whether the strands are where they were after ``samples`` samples,
    as a set: the period can then begin at any sample."""
    if len(xs) < samples + 1:
        return False
    here = sorted(zip(np.round(xs[0], 6), np.round(ys[0], 6)))
    there = sorted(zip(np.round(xs[samples - 1], 6), np.round(ys[samples - 1], 6)))
    return here == there


def _untied(xs: np.ndarray, ys: np.ndarray, n_substeps: int) -> int:
    """The sample of the first step whose strands are furthest from any
    being in line with the axis."""
    angles = np.arctan2(ys, xs) / (2 * math.pi)

    def closest(sample: int) -> float:
        round_ = np.sort(angles[sample] % 1.0)
        return float(np.diff(np.concatenate([round_, [round_[0] + 1.0]])).min())

    return max(range(n_substeps), key=closest)


def _ring_moves(turns: np.ndarray, radius: np.ndarray) -> tuple[list[int], list[int]]:
    """The moves of strands round a centre: per sample, each strand's angle
    in turns, unwrapped, and its distance.  Between samples each moves
    evenly, so every event — two strands in line, a strand on the seam —
    has its moment, and they are made in order.

    Returns:
        The moves, and the strand in each slot to begin with.
    """
    n = turns.shape[1]
    start = np.sort(turns[0] % 1.0)
    gaps = np.diff(np.concatenate([start, [start[0] + 1.0]]))
    widest = int(np.argmax(gaps))
    seam = start[widest] + gaps[widest] / 2
    order = sorted(range(n), key=lambda k: (turns[0, k] - seam) % 1.0)
    first = list(order)
    moves: list[int] = []
    for sample in range(1, len(turns)):
        before, after = turns[sample - 1], turns[sample]
        events: list[tuple[float, int, int]] = []
        for k in range(n):
            events += [
                (at, k, -1) for at in _passings(before[k] - seam, after[k] - seam)
            ]
        apart_before = before[:, None] - before[None, :]
        apart_after = after[:, None] - after[None, :]
        changed = np.floor(apart_before) != np.floor(apart_after)
        for a, b in zip(*np.nonzero(np.triu(changed, 1))):
            events += [
                (at, int(a), int(b))
                for at in _passings(apart_before[a, b], apart_after[a, b])
            ]
        for at, a, b in sorted(events):
            outside = radius[sample - 1] + at * (radius[sample] - radius[sample - 1])
            order = _made(order, moves, a, b, outside, after[a] > before[a])
    return moves, first


def _passings(before: float, after: float) -> list[float]:
    """When, as a fraction of the sample, a quantity moving evenly from
    ``before`` to ``after`` passes a whole number."""
    low, high = min(before, after), max(before, after)
    return [
        (whole - before) / (after - before)
        for whole in range(math.floor(low) + 1, math.floor(high) + 1)
    ]


def _made(
    order: list[int],
    moves: list[int],
    a: int,
    b: int,
    outside: np.ndarray,
    onwards: bool,
) -> list[int]:
    """The strands' order once an event is made, its move written: strand
    ``a`` passing the seam if ``b`` is -1, onwards being clockwise, else
    strands ``a`` and ``b`` crossing, ``outside`` each strand's distance
    from the centre then."""
    n = len(order)
    if b < 0:
        if onwards and order[-1] == a:
            moves.append(n + 1)
            return [a] + order[:-1]
        if not onwards and order[0] == a:
            moves.append(-(n + 1))
            return order[1:] + [a]
        raise RuntimeError(f"Strand {a} passes the seam from the middle of the ring.")
    i, j = order.index(a), order.index(b)
    if abs(i - j) == 1:
        low, high, index = min(i, j), max(i, j), min(i, j) + 1
    elif {i, j} == {0, n - 1} and n > 2:
        low, high, index = n - 1, 0, n
    else:
        raise RuntimeError(f"Strands {a} and {b} cross with others between.")
    lower, upper = order[low], order[high]
    moves.append(index if outside[lower] > outside[upper] else -index)
    order = list(order)
    order[low], order[high] = upper, lower
    return order


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
