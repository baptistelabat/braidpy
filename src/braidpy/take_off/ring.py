# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A disk's braid, laid on a ring: only the crossings its moves make, kept,
and laid round a ring as a braid holds its strands."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence

import numpy as np

from .laying import lay_yarns
from .paths import StrandTrajectories, YarnPaths
from .sources import kumihimo_steps, mobidai_steps
from .tighten import tighten_yarns

# A disk's strands spend most of their time waiting on the rim while one
# moves, and where they wait is not the braid's cross-section: laid as it is,
# a kongo comes out flat and lopsided.  What the moves decide is only the
# order of the strands round the axis and, where two cross, which goes over.
# So that is all that is kept: the strands stand evenly round a small ring in
# their order round the disk, and each crossing the moves make swaps two
# neighbours on it, the one going over passing inside.


def disk_crossings(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
) -> tuple[list[Hashable], list[tuple[Hashable, Hashable]]]:
    """The crossings a disk's moves make, in the order they are made.

    See :func:`disk_crossing_steps`, which also says which step made each.

    Returns:
        The strands in slot order from slot 1 at the start, and each crossing
        as ``(over, under)``.
    """
    order, crossings, _ = disk_crossing_steps(start, steps, n_slots)
    return order, crossings


def disk_crossing_steps(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
) -> tuple[list[Hashable], list[tuple[Hashable, Hashable]], list[float]]:
    """The crossings a disk's moves make, and when each is made.

    A strand that moves while the others stay passes over each strand
    between its slot and its new one, one after another, nearest first —
    the rule :func:`disk_trajectories` draws and the mobidai's own word
    records.  A step that moves every strand alike turns the disk and
    crosses nothing; so does one that slides a few strands along together,
    as long as no strand that stays is in their way.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots, as
            :func:`mobidai_steps` and :func:`kumihimo_steps` give them.
        n_slots: Slots round the disk.

    Returns:
        The strands in slot order from slot 1 at the start, each crossing as
        ``(over, under)``, and when each is made, in steps: a strand moving
        ``n`` slots passes the slot ``j`` along at ``j / n`` of its step, as
        :func:`disk_trajectories` moves it.

    Raises:
        ValueError: If two strands move at once other than by turning the
            disk or sliding along together, which this cannot order into
            crossings.
    """
    where = dict(start)
    order = sorted(where, key=lambda k: where[k])
    crossings: list[tuple[Hashable, Hashable]] = []
    made_at: list[float] = []
    for number, step in enumerate(steps):
        moving = {k: d for k, d in step.items() if d}
        if not moving:
            continue
        if _slides(where, moving, n_slots):
            delta = next(iter(moving.values()))
            for k in moving:
                where[k] = (where[k] - 1 + delta) % n_slots + 1
            continue
        if len(moving) > 1:
            raise ValueError(f"Step {number} moves several strands at once.")
        ((mover, delta),) = moving.items()
        sense = 1 if delta > 0 else -1
        slot = where[mover]
        by_slot = {s: k for k, s in where.items()}
        for passed in range(1, abs(delta)):
            slot = (slot - 1 + sense) % n_slots + 1
            if slot in by_slot:
                crossings.append((mover, by_slot[slot]))
                made_at.append(number + passed / abs(delta))
        where[mover] = (where[mover] - 1 + delta) % n_slots + 1
    return order, crossings, made_at


def _slides(
    where: Mapping[Hashable, int], moving: Mapping[Hashable, int], n_slots: int
) -> bool:
    """Whether a step carries strands along together, crossing nobody.

    Every strand moves alike — the disk turning — or several move alike and
    no strand that stays is in the slots they sweep.  A single strand
    moving is not a slide: it crosses whoever it passes.
    """
    if len(set(moving.values())) != 1:
        return False
    if set(moving) == set(where):
        return True
    if len(moving) < 2:
        return False
    delta = next(iter(moving.values()))
    sense = 1 if delta > 0 else -1
    staying = {where[k] for k in where if k not in moving}
    for k in moving:
        slot = where[k]
        for _ in range(abs(delta)):
            slot = (slot - 1 + sense) % n_slots + 1
            if slot in staying:
                return False
    return True


def disk_annular_word(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
    clockwise: bool = True,
) -> tuple[list[int], int]:
    """The annular braid a disk's moves make — see :mod:`braidpy.annulus_braid`.

    The strands are numbered in order round the disk, seen from above and
    read clockwise from the seam between the last slot and slot 1, so an
    anticlockwise disk is read from its last slot back.  A strand lifted
    over another — over, seen from above — passes inside it, nearer the
    braid's axis, and the annulus counts a crossing by who is outside: a
    move clockwise over a strand is a negative crossing, anticlockwise a
    positive one.

    A strand passing between the last slot and slot 1, crossing nobody,
    changes nothing on the disk, but every strand's number then moves on
    one: a turn (:func:`~braidpy.annulus_braid.turn`), as the disk turning
    by one strand would be.  Which strands are numbered from where depends
    only on where slot 1 is; another starting point gives the same braid,
    conjugated.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots, as
            :func:`disk_crossings` takes them.
        n_slots: Slots round the disk.
        clockwise: Whether slot numbers go round clockwise, seen from above.

    Returns:
        The word, crossings ``±1`` to ``±n`` and turns ``±(n + 1)``, and the
        number of strands ``n``.

    Raises:
        ValueError: As :func:`disk_crossings`.
    """

    def read(slot: int) -> int:
        """A slot as numbered clockwise, the seam staying where it is."""
        return slot if clockwise else n_slots + 1 - slot

    where = {k: read(s) for k, s in start.items()}
    n = len(where)
    # The strands in order round the ring, from slot 1.
    ring = sorted(where, key=lambda k: where[k])
    word: list[int] = []
    for number, step in enumerate(steps):
        moving = {k: (d if clockwise else -d) for k, d in step.items() if d}
        if not moving:
            continue
        sliding = _slides(where, moving, n_slots)
        if len(moving) > 1 and not sliding:
            raise ValueError(f"Step {number} moves several strands at once.")
        delta = next(iter(moving.values()))
        sense = 1 if delta > 0 else -1
        for _ in range(abs(delta)):
            by_slot = {s: k for k, s in where.items()}
            # Front runners first, so nobody steps into a slot still held.
            for k in sorted(moving, key=lambda k: -sense * where[k]):
                here = where[k]
                there = (here - 1 + sense) % n_slots + 1
                if sense > 0 and there == 1:
                    # Last round the ring becomes first: everyone moves on.
                    ring.remove(k)
                    ring.insert(0, k)
                    word.append(n + 1)
                elif sense < 0 and here == 1:
                    ring.remove(k)
                    ring.append(k)
                    word.append(-(n + 1))
                other = by_slot.get(there)
                if not sliding and other is not None and other != k:
                    i = ring.index(k)
                    if sense > 0:
                        # The mover is first of the pair, and inside.
                        word.append(-(i + 1))
                        ring[i], ring[i + 1] = ring[i + 1], ring[i]
                    else:
                        # The other is first of the pair, and outside.
                        word.append(i)
                        ring[i - 1], ring[i] = ring[i], ring[i - 1]
                where[k] = there
    return word, n


def crossing_rows(
    order: Sequence[Hashable],
    crossings: Sequence[tuple[Hashable, Hashable]],
    in_turn: bool = False,
) -> list[int]:
    """The row of the ring each crossing is made in — see :func:`ring_trajectories`.

    Each crossing goes in the first row after both its strands' last ones,
    so crossings of different strands are made side by side and each
    strand's crossings stay in order.

    Args:
        order: The strands round the ring.
        crossings: ``(over, under)`` in the order they are made.
        in_turn: Never put a crossing in a row before an earlier crossing's,
            so the rows are made in the order the crossings are, as a braid
            grows below a disk.

    Returns:
        One row index per crossing.
    """
    free_from = {k: 0 for k in order}
    rows: list[int] = []
    for over, under in crossings:
        row = max(free_from[over], free_from[under])
        if in_turn and rows:
            row = max(row, rows[-1])
        rows.append(row)
        free_from[over] = free_from[under] = row + 1
    return rows


def ring_trajectories(
    order: Sequence[Hashable],
    crossings: Sequence[tuple[Hashable, Hashable]],
    diameter: float = 1.0,
    samples_per_row: int = 12,
    clockwise: bool = True,
    label: str = "Strand ",
    rows: Sequence[int] | None = None,
) -> StrandTrajectories:
    """Strands standing evenly round a ring, swapping neighbours as they cross.

    Every crossing is made by two strands next to each other round the ring:
    they change places, the one going over passing inside, the other outside,
    a ``diameter`` apart where they meet.  Crossings of different strands are
    made side by side, in rows, as long as each strand's crossings stay in
    order; each row takes one unit of time.

    Nothing about which strand passes which, or on which side, is lost —
    inside is over, as on a disk seen from above — so a braid laid from this
    is the braid the moves made, with the strands where a braid holds them
    rather than where a disk does.

    Args:
        order: The strands round the ring, in slot order.
        crossings: ``(over, under)`` in the order they are made; each pair
            must be neighbours on the ring when its turn comes.
        diameter: Yarn diameter, setting the ring's size and how far apart
            the two strands of a crossing pass.
        samples_per_row: Samples per row of crossings.
        clockwise: Whether the order runs clockwise, seen from above.
        label: Prefix naming a strand in a drawing.
        rows: The row of each crossing; :func:`crossing_rows` if None.

    Returns:
        The trajectories, one unit of time per row.

    Raises:
        ValueError: If a crossing's strands are not neighbours on the ring.
    """
    if samples_per_row < 1:
        raise ValueError("samples_per_row must be at least 1.")
    n = len(order)
    rank = {k: i for i, k in enumerate(order)}
    if rows is None:
        rows = crossing_rows(order, crossings)
    by_row: list[list[tuple[Hashable, Hashable]]] = []
    for crossing, index in zip(crossings, rows):
        while len(by_row) <= index:
            by_row.append([])
        by_row[index].append(crossing)

    # Even round a ring a little looser than the strands' own width.
    radius = n * diameter / (2 * np.pi) / 0.8
    turn = 1 if clockwise else -1
    # Each strand's place round the ring, in units of one place; it is not
    # wrapped, so a strand that goes round keeps going round.
    angle = {k: float(rank[k]) for k in order}
    slot = dict(rank)
    fractions = np.arange(samples_per_row) / samples_per_row
    ease = 0.5 - 0.5 * np.cos(np.pi * fractions)
    xs: dict[Hashable, list[float]] = {k: [] for k in order}
    ys: dict[Hashable, list[float]] = {k: [] for k in order}

    def place(k: Hashable, a: np.ndarray, r: np.ndarray) -> None:
        theta = 2 * np.pi * a / n * turn
        xs[k].extend(r * np.sin(theta))
        ys[k].extend(r * np.cos(theta))

    for number, row in enumerate(by_row):
        moving: dict[Hashable, tuple[int, float]] = {}
        for over, under in row:
            gap = (slot[under] - slot[over]) % n
            if gap not in (1, n - 1):
                raise ValueError(
                    f"Crossing {over!r} over {under!r} in row {number}: "
                    "they are not neighbours on the ring."
                )
            step = 1 if gap == 1 else -1
            moving[over] = (step, -1.0)
            moving[under] = (-step, 1.0)
            slot[over], slot[under] = slot[under], slot[over]
        for k in order:
            here = angle[k]
            if k in moving:
                sense, side = moving[k]
                a = here + sense * ease
                r = radius + side * diameter / 2 * np.sin(np.pi * fractions)
            else:
                a = np.full(samples_per_row, here)
                r = np.full(samples_per_row, radius)
            place(k, a, r)
        for k, (sense, _) in moving.items():
            angle[k] += sense
    for k in order:
        place(k, np.array([angle[k]]), np.array([radius]))

    times = np.arange(len(by_row) * samples_per_row + 1) / samples_per_row
    ring = np.linspace(0, 2 * np.pi, 4 * n + 1)
    return StrandTrajectories(
        times=times,
        xy={k: np.column_stack([xs[k], ys[k]]) for k in order},
        outlines=(np.column_stack([radius * np.sin(ring), radius * np.cos(ring)]),),
        axis=(0.0, 0.0),
        label=label,
        outline_name="Ring",
    )


def disk_braid(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
    yarn_diameter: float,
    take_off_per_row: float = 1.5,
    iterations: int = 300,
    clockwise: bool = True,
) -> YarnPaths:
    """The braid a disk's moves make: laid on a ring, drawn in and tightened.

    The crossings are read off the moves (:func:`disk_crossings`), the
    strands set evenly round a ring and crossed there
    (:func:`ring_trajectories`), and the braid laid and tightened as any
    other (:func:`lay_yarns`, :func:`tighten_yarns`).

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots.
        n_slots: Slots round the disk.
        yarn_diameter: Yarn diameter.
        take_off_per_row: Braid taken off per row of crossings, in yarn
            diameters.  Above one: two strands often cross back over each
            other a row later, along the same path, and need that much room.
        iterations: Tightening steps.
        clockwise: Whether slot numbers go round clockwise, seen from above.

    Returns:
        The tightened braid.
    """
    order, crossings = disk_crossings(start, steps, n_slots)
    ring = ring_trajectories(order, crossings, yarn_diameter, clockwise=clockwise)
    paths = lay_yarns(
        ring, take_off=take_off_per_row * yarn_diameter, yarn_diameter=yarn_diameter
    )
    braid, _ = tighten_yarns(paths, yarn_diameter, iterations=iterations)
    return braid


def mobidai_braid(
    mobidai, yarn_diameter: float, n_cycles: int = 8, **kwargs
) -> YarnPaths:
    """The braid a mobidai makes in ``n_cycles`` cycles — see :func:`disk_braid`.

    Args:
        mobidai: A ``Mobidai`` or ``MobidaiConfig`` (see :mod:`braidpy.mobidai`).
        yarn_diameter: Yarn diameter.
        n_cycles: Cycles to work.
        **kwargs: Passed on to :func:`disk_braid`.

    Returns:
        The tightened braid, one yarn per strand, keyed as the mobidai's.
    """
    config = getattr(mobidai, "config", mobidai)
    start, steps = mobidai_steps(config, n_cycles)
    kwargs.setdefault("clockwise", getattr(config, "is_clockwise", True))
    return disk_braid(start, steps, config.n_slots, yarn_diameter, **kwargs)


def kumihimo_braid(
    kumihimo, yarn_diameter: float, n_strands: int | None = None, **kwargs
) -> YarnPaths:
    """The braid a kumihimo sequence makes — see :func:`disk_braid`.

    Args:
        kumihimo: A ``Kumihimo``, or a pattern of ``S`` and ``R``.
        yarn_diameter: Yarn diameter.
        n_strands: Strands, when given a pattern.
        **kwargs: Passed on to :func:`disk_braid`.

    Returns:
        The tightened braid.
    """
    n_slots, start, steps = kumihimo_steps(kumihimo, n_strands)
    kwargs.setdefault("clockwise", False)
    return disk_braid(start, steps, n_slots, yarn_diameter, **kwargs)
