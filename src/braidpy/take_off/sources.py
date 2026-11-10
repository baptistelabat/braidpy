# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Where strands go, from what makes them: a parametric braid or a braid
word, a disk's slots, and the mobidai and kumihimo sequences worked on one."""

from __future__ import annotations

from collections.abc import Hashable, Mapping, Sequence
from dataclasses import replace

import numpy as np

from .paths import StrandTrajectories


def parametric_trajectories(
    braid,
    n_samples: int = 400,
    label: str = "Strand ",
) -> StrandTrajectories:
    """The strands of a parametric braid, as trajectories to lay.

    A :class:`~braidpy.parametric_strand.ParametricStrand` is a curve
    ``γ(t) = (x, y, z)`` for ``t`` from 0 to 1.  Its ``(x, y)`` is taken as
    where its carrier was at time ``t``, so the strand drawn first is laid
    first and ends up highest, as ``ParametricBraid.plot`` draws it — over and
    under come from ``y``, as they do there.

    Args:
        braid: A :class:`~braidpy.parametric_braid.ParametricBraid`, or a
            sequence of strands.
        n_samples: Samples along each strand.
        label: Prefix naming a strand in a drawing.

    Returns:
        The trajectories, over times 0 to 1.
    """
    strands = getattr(braid, "strands", braid)
    if n_samples < 2:
        raise ValueError("n_samples must be at least 2.")
    times = np.linspace(0.0, 1.0, n_samples)
    xy: dict[Hashable, np.ndarray] = {
        index: np.array([strand.evaluate(float(t))[:2] for t in times])
        for index, strand in enumerate(strands)
    }
    return StrandTrajectories(times=times, xy=xy, label=label)


def braid_word_trajectories(
    braid,
    samples_per_crossing: int = 24,
    spacing: float = 1.0,
    lift: float = 0.5,
) -> StrandTrajectories:
    """A braid word's strands, as trajectories to lay.

    The strands stand in a row ``spacing`` apart, and a crossing swaps two
    neighbours, the one going over lifted ``lift * spacing`` to one side and
    the one going under to the other — the drawing of
    :meth:`~braidpy.braid.Braid.to_parametric_strands`.  Anything that makes
    a braid word can therefore be laid, tightened and drawn: a kumihimo
    sequence, a catalogue braid, or a word read off a machine.

    Args:
        braid: A :class:`~braidpy.braid.Braid`, or its generators as signed
            integers.
        samples_per_crossing: Samples per generator.
        spacing: Distance between neighbouring strands.
        lift: How far a crossing strand moves off the row, as a fraction of
            ``spacing``.

    Returns:
        The trajectories, over times 0 to 1.
    """
    from braidpy.braid import Braid

    if not isinstance(braid, Braid):
        braid = Braid(tuple(braid))
    strands = braid.to_parametric_strands(amplitude=1.0)
    n_segments = len(braid.generators) + 1
    traj = parametric_trajectories(
        strands, n_samples=samples_per_crossing * n_segments + 1
    )
    # Drawn with the row and the lift both one unit; stretch each to size.
    stretch = np.array([spacing, lift * spacing])
    return replace(traj, xy={k: xy * stretch for k, xy in traj.xy.items()})


def _disk_point(
    slot: np.ndarray,
    radius: np.ndarray,
    n_slots: int,
    clockwise: bool,
    slot_offset: float = 0.0,
):
    """Where slot ``slot`` (1-based, may be fractional) is on a disk.

    Slot 1 at the top, counting clockwise or not — the mobidai's drawing —
    unless ``slot_offset`` turns the numbering round by that many slots.
    """
    angle = 2 * np.pi * (slot - 1 + slot_offset) / n_slots * (1 if clockwise else -1)
    return np.column_stack([radius * np.sin(angle), radius * np.cos(angle)])


def disk_trajectories(
    start: Mapping[Hashable, int],
    steps: Sequence[Mapping[Hashable, int]],
    n_slots: int,
    radius: float = 1.0,
    lift: float = 0.15,
    samples_per_step: int = 12,
    clockwise: bool = True,
    label: str = "Strand ",
    slot_offset: float = 0.0,
    slot_names: Mapping[int, str] | None = None,
) -> StrandTrajectories:
    """Strands moved between the slots round a disk, as trajectories to lay.

    This is how a kumihimo disk or a mobidai is worked: each step moves some
    strands round the rim by a number of slots — positive toward higher slot
    numbers — and a step that moves every strand alike is the disk itself
    turning.

    A strand that moves while others stay is lifted over the ones it passes —
    over as seen from above the disk, the side the braider works from, with
    the braid going down through the middle.  Over is therefore *inside*: the
    moving strand travels round inside the rim, a ``lift`` fraction of the
    radius in, and comes back out to its new slot.  Read in slot order with
    inside as over, that gives the crossings the mobidai's own braid word
    records on a clockwise disk — a move toward higher slots crosses over,
    positively.

    That is the opposite way round from :mod:`braidpy.annulus_braid`, which
    looks at a tube from outside, where over is outside.

    Args:
        start: Each strand's slot, 1-based.
        steps: Per step, the strands that move and by how many slots.
        n_slots: Slots round the disk.
        radius: The disk's radius.
        lift: How far in a moving strand travels, as a fraction of the radius.
        samples_per_step: Samples per step.
        clockwise: Whether slot numbers go round clockwise, seen from above.
        label: Prefix naming a strand in a drawing.
        slot_offset: Slots the numbering is turned by, so slot 1 sits that far
            round from the top.  A kumihimo disk marks the top between its
            last slot and slot 1: half a slot.
        slot_names: What to call each slot that is marked, by slot number;
            every slot by its number if None.

    Returns:
        The trajectories, one unit of time per step.

    Raises:
        ValueError: If a strand is not on a slot, or a step leaves two strands
            in one slot.
    """
    if samples_per_step < 1:
        raise ValueError("samples_per_step must be at least 1.")
    keys = list(start)
    where = {k: float(start[k]) for k in keys}
    for key, slot in where.items():
        if not 1 <= slot <= n_slots or slot != int(slot):
            raise ValueError(f"Strand {key!r} is not on a slot: {slot}.")
    if len(set(where.values())) < len(where):
        raise ValueError("Two strands start in the same slot.")

    slots: dict[Hashable, list[float]] = {k: [] for k in keys}
    rims: dict[Hashable, list[float]] = {k: [] for k in keys}
    fractions = np.arange(samples_per_step) / samples_per_step
    for number, step in enumerate(steps):
        unknown = set(step) - set(keys)
        if unknown:
            raise ValueError(f"Step {number} moves unknown strands {unknown}.")
        turning = set(step) == set(keys) and len(set(step.values())) == 1
        for key in keys:
            delta = float(step.get(key, 0))
            slots[key].extend(where[key] + delta * fractions)
            inward = 0.0 if turning or delta == 0 else lift
            rims[key].extend(radius * (1 - inward * np.sin(np.pi * fractions)))
            where[key] = (where[key] + delta - 1) % n_slots + 1
        if len({round(s) for s in where.values()}) < len(where):
            raise ValueError(f"Step {number} leaves two strands in one slot.")
    for key in keys:
        slots[key].append(where[key])
        rims[key].append(radius)

    times = np.arange(len(steps) * samples_per_step + 1) / samples_per_step
    xy = {
        k: _disk_point(
            np.array(slots[k]), np.array(rims[k]), n_slots, clockwise, slot_offset
        )
        for k in keys
    }
    rim = _disk_point(
        np.linspace(1, n_slots + 1, 4 * n_slots + 1),
        np.full(4 * n_slots + 1, radius),
        n_slots,
        clockwise,
        slot_offset,
    )
    if slot_names is None:
        slot_names = {slot: str(slot) for slot in range(1, n_slots + 1)}
    numbered = sorted(slot_names)
    marks = _disk_point(
        np.array(numbered, dtype=float),
        np.full(len(numbered), radius),
        n_slots,
        clockwise,
        slot_offset,
    )
    return StrandTrajectories(
        times=times,
        xy=xy,
        slots=tuple(
            (float(x), float(y), slot_names[slot])
            for (x, y), slot in zip(marks, numbered)
        ),
        outlines=(rim,),
        axis=(0.0, 0.0),
        label=label,
        outline_name="Disk",
    )


def mobidai_steps(
    mobidai, n_cycles: int = 1, drift: int | None = None
) -> tuple[dict[Hashable, int], list[dict[Hashable, int]]]:
    """A mobidai's cycles, as the start and steps :func:`disk_trajectories` takes.

    Reads either a ``Mobidai`` or its ``MobidaiConfig`` (see
    :mod:`braidpy.mobidai`) without running it, and follows its rules: a move
    goes the short way round unless forced, a move from an empty slot does
    nothing, and the disk turns ``n_shift_after_cycle`` slots after each cycle.

    Some braids do not come back to the slots they started in after a cycle
    but one or more slots round from them — kongo gumi creeps one slot back
    each time — and the braider simply repeats the same moves from where the
    strands now are: cycle ``c`` makes every move ``c * drift`` slots round
    from the first cycle's.  The drift is read off the cycle itself, as
    :class:`~braidpy.mobidai.Mobidai` does (see
    :func:`~braidpy.mobidai.cycle_drift`).

    Args:
        mobidai: The mobidai, or its configuration.
        n_cycles: Cycles to work.
        drift: Slots each cycle's moves are shifted from the one before;
            read off the cycle if None.

    Returns:
        Each strand's starting slot, keyed by strand id, and the steps.
    """
    config = getattr(mobidai, "config", mobidai)
    n = config.n_slots
    where: dict[Hashable, int] = {}
    for index, strand in enumerate(config.strands):
        key = strand.id if getattr(strand, "id", -1) >= 0 else index
        where[key] = strand.position
    start = dict(where)
    if drift is None:
        from braidpy.mobidai import cycle_drift

        drift = cycle_drift(
            list(start.values()), config.moves, n, config.n_shift_after_cycle
        )

    steps: list[dict[Hashable, int]] = []
    for cycle in range(n_cycles):
        for move in config.moves:
            source = (move.from_slot - 1 + cycle * drift) % n + 1
            target = (move.to_slot - 1 + cycle * drift) % n + 1
            mover = next((k for k, s in where.items() if s == source), None)
            if mover is None:
                continue
            diff = (target - source) % n
            force = getattr(move, "force_direction", 0)
            increasing = force == 1 or (force == 0 and diff <= n // 2)
            steps.append({mover: diff if increasing else diff - n})
            where[mover] = target
        shift = config.n_shift_after_cycle
        if shift:
            steps.append({k: shift for k in where})
            where = {k: (s - 1 + shift) % n + 1 for k, s in where.items()}
    return start, steps


def mobidai_trajectories(
    mobidai,
    n_cycles: int = 3,
    drift: int | None = None,
    radius: float = 1.0,
    lift: float = 0.15,
    samples_per_step: int = 12,
    slot_offset: float = 0.0,
) -> StrandTrajectories:
    """A mobidai worked for ``n_cycles`` cycles, as trajectories to lay.

    Args:
        mobidai: A ``Mobidai`` or ``MobidaiConfig`` (see :mod:`braidpy.mobidai`).
        n_cycles: Cycles to work.
        drift: Slots each cycle's moves are shifted from the one before; read
            off the cycle if None — see :func:`mobidai_steps`.
        radius: The disk's radius.
        lift: How far in a moving strand travels, as a fraction of the radius.
        samples_per_step: Samples per move.
        slot_offset: Slots the numbering is turned by — see
            :func:`disk_trajectories`.

    Returns:
        The trajectories, one unit of time per move.
    """
    config = getattr(mobidai, "config", mobidai)
    start, steps = mobidai_steps(config, n_cycles, drift)
    return disk_trajectories(
        start,
        steps,
        config.n_slots,
        radius=radius,
        lift=lift,
        samples_per_step=samples_per_step,
        clockwise=getattr(config, "is_clockwise", True),
        slot_offset=slot_offset,
    )


def kumihimo_steps(
    kumihimo, n_strands: int | None = None
) -> tuple[int, dict[Hashable, int], list[dict[Hashable, int]]]:
    """A kumihimo sequence, as the disk and steps :func:`disk_trajectories` takes.

    Reads a :class:`~braidpy.kumihimo.Kumihimo` — its strand count and the
    ``S`` and ``R`` moves it has recorded — or a pattern string such as
    ``"SRSR"`` for ``n_strands`` strands, without running anything.

    The disk is given twice as many slots as there are strands, so that a
    swap has somewhere to pass: position ``p`` is slot ``2p + 1``.  A swap of
    the top and bottom strands is then the move
    :meth:`~braidpy.kumihimo.Kumihimo.swap_top_bottom` writes down — the top
    strand goes over every strand on its way to just past the bottom one, the
    bottom one comes back over the others to the top, and the first settles
    into its place.  A rotation turns the whole disk, a quarter turn
    clockwise per ``R``.

    Args:
        kumihimo: A ``Kumihimo``, or a pattern of ``S`` and ``R``.
        n_strands: Strands, when given a pattern.

    Returns:
        The number of slots, each strand's starting slot, and the steps.

    Raises:
        ValueError: If the pattern is empty or has other moves, or the
            strands are not a multiple of four.
    """
    if isinstance(kumihimo, str):
        if n_strands is None:
            raise ValueError("A pattern needs n_strands.")
        if not kumihimo or set(kumihimo) - {"S", "R"}:
            raise ValueError("A kumihimo pattern is made of S (swap) and R (rotate).")
        n = n_strands
        moves = [m if m == "S" else "R**1" for m in kumihimo]
        start_order = list(range(n))
    else:
        n = kumihimo.n
        moves = list(kumihimo.history)
        start_order = list(kumihimo.frames[0])
    if n % 4:
        raise ValueError("A kumihimo disk takes a multiple of four strands.")

    position: dict[Hashable, int] = {s: p for p, s in enumerate(start_order)}
    start: dict[Hashable, int] = {s: 2 * p + 1 for s, p in position.items()}
    steps: list[dict[Hashable, int]] = []
    for move in moves:
        if move == "S":
            at = {p: strand for strand, p in position.items()}
            top, bottom = at[0], at[n // 2]
            steps += [{top: n + 1}, {bottom: -n}, {top: -1}]
            position[top], position[bottom] = n // 2, 0
        elif move.startswith("R"):
            turns = int(move.split("**")[1]) if "**" in move else 1
            shift = (n // 4) * turns
            steps.append({strand: -2 * shift for strand in position})
            position = {s: (p - shift) % n for s, p in position.items()}
        else:
            raise ValueError(f"Unknown kumihimo move {move!r}.")
    return 2 * n, start, steps


def kumihimo_trajectories(
    kumihimo,
    n_strands: int | None = None,
    radius: float = 1.0,
    lift: float = 0.15,
    samples_per_step: int = 12,
) -> StrandTrajectories:
    """A kumihimo sequence worked on its disk, as trajectories to lay.

    Positions are numbered anticlockwise from the top, as
    :meth:`~braidpy.kumihimo.Kumihimo.plot_timeline` draws them.

    Args:
        kumihimo: A ``Kumihimo``, or a pattern of ``S`` and ``R``.
        n_strands: Strands, when given a pattern.
        radius: The disk's radius.
        lift: How far in a moving strand travels, as a fraction of the radius.
        samples_per_step: Samples per step.

    Returns:
        The trajectories, one unit of time per step.
    """
    n_slots, start, steps = kumihimo_steps(kumihimo, n_strands)
    return disk_trajectories(
        start,
        steps,
        n_slots,
        radius=radius,
        lift=lift,
        samples_per_step=samples_per_step,
        clockwise=False,
        # Kumihimo's positions are the odd slots; the even ones are only
        # somewhere for a swap to pass.
        slot_names={2 * p + 1: str(p) for p in range(n_slots // 2)},
    )
