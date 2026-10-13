# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Disk braids: kumihimo's own S/R moves, a mobidai braid, an Ashley solid
sinnet.  Each is laid round a ring with its rows in the order the disk
makes their crossings, so the page can show the disk and the braid in step,
and comes with its moves, for the page to make it move by move as on a
marudai."""

from __future__ import annotations

import re
from typing import Callable, Dict, Hashable, List, Sequence, Tuple

import numpy as np

from braidpy.web._info import _disk_info, _disk_unit
from braidpy.web._result import _hues, _result, _tightened, _timeline
from braidpy.web._settings import (
    DISK_ITERATIONS,
    DISK_YARN,
    OWN,
    Kumihimo,
    Mobidai,
    Sinnet,
)
from braidpy.web._spec import _moves_text, _numbers, defaults, parse_moves
from braidpy.web._types import DiskProgram, Entry, Result, Source, Spec


def _sinnets():
    from braidpy.solid_sinnets_catalog import CATALOGUE

    return CATALOGUE


def _mobidais():
    from braidpy.mobidai_catalog import CATALOGUE

    return CATALOGUE


def _disk_program(
    start, steps, n_slots: int, clockwise: bool, keys: Sequence[Hashable]
) -> DiskProgram:
    """What a disk does, for the page to make the braid itself, move by
    move: each strand's slot to start with, in the order of the strands
    given, and per step the strands that move, by index, and by how many
    slots."""
    index = {k: i for i, k in enumerate(keys)}
    return {
        "n_slots": int(n_slots),
        "clockwise": bool(clockwise),
        "start": [int(start[k]) for k in keys],
        "steps": [
            [[index[k], int(delta)] for k, delta in step.items() if delta]
            for step in steps
        ],
    }


def _disk_in_step(
    start,
    steps,
    n_slots: int,
    diameter: float,
    iterations: int,
    clockwise: bool,
):
    """A disk's braid, laid round a ring with its rows made in the order
    the disk makes their crossings — as the side view of
    :class:`~braidpy.disk_animation.BraidGrowth` does — so the page can show
    the disk and the braid in step.

    Returns:
        The braid, and its clock: the disk's time at each crossing, and the
        braid's then.
    """
    from braidpy.take_off import (
        crossing_rows,
        disk_crossing_steps,
        lay_yarns,
        ring_trajectories,
    )

    order, crossings, made_at = disk_crossing_steps(start, steps, n_slots)
    if not crossings:
        raise ValueError("These moves cross no strands: there is no braid.")
    rows = crossing_rows(order, crossings, in_turn=True)
    ring = ring_trajectories(order, crossings, diameter, clockwise=clockwise, rows=rows)
    paths = lay_yarns(ring, take_off=1.5 * diameter, yarn_diameter=diameter)
    paths = _tightened(paths, diameter, iterations)
    clock = {
        "source": [0.0, *map(float, made_at), float(len(steps))],
        "braid": [0.0, *(r + 0.5 for r in rows), float(rows[-1] + 1)],
    }
    return paths, clock, ring


def _kumihimo_cycles(pattern: str, n_strands: int):
    from braidpy.take_off import kumihimo_steps

    n_slots, start, steps = kumihimo_steps(pattern, n_strands)
    return start, steps, n_slots


def _from_kumihimo(spec: Spec) -> Result:
    from braidpy.take_off import kumihimo_steps, kumihimo_trajectories

    pattern = re.sub(r"\s+", "", Kumihimo.pattern.read(spec)).upper()
    n_strands = Kumihimo.n_strands.read(spec)
    repeat = Kumihimo.repeat.read(spec)
    diameter = DISK_YARN.read(spec)
    n_slots, start, steps = kumihimo_steps(pattern * repeat, n_strands)
    paths, clock, ring = _disk_in_step(
        start,
        steps,
        n_slots,
        diameter,
        DISK_ITERATIONS.read(spec),
        clockwise=False,
    )
    disk = kumihimo_trajectories(pattern * repeat, n_strands)
    result = _result(
        f"Kumihimo {pattern} × {repeat}, {n_strands} strands",
        paths,
        diameter,
        colours=_hues(n_strands),
        info=_disk_unit(
            _disk_info(start, steps, n_slots, clockwise=False),
            lambda k: _kumihimo_cycles(pattern * k, n_strands),
            False,
            "repeat",
        ),
        timeline=_timeline(disk, list(paths.points), "disk", clock, ring),
    )
    result["disk"] = _disk_program(start, steps, n_slots, False, list(paths.points))
    result["info"]["made"] = repeat
    return result


def _from_mobidai(spec: Spec) -> Result:
    from braidpy.take_off import mobidai_steps, mobidai_trajectories

    from braidpy.mobidai_catalog import CataloguedMobidai

    mobidais = _mobidais()
    name = Mobidai.name.read(spec)
    if name == OWN:
        n_slots = Mobidai.n_slots.read(spec)
        slots = _numbers(spec.get("slots", ""), "slots the strands start in")
        if len(set(slots)) < len(slots):
            raise ValueError("Two strands start in the same slot.")
        if not all(1 <= slot <= n_slots for slot in slots):
            raise ValueError(f"Slots are numbered from 1 to {n_slots}.")
        moves = parse_moves(str(spec.get("moves", "")))
        if not all(1 <= p <= n_slots for move in moves for p in move):
            raise ValueError(f"Moves are between slots 1 to {n_slots}.")
        entry = CataloguedMobidai(
            name="your own disk braid",
            n_slots=n_slots,
            initial_slots=tuple(zip(slots, _hues(len(slots)))),
            moves=tuple(moves),
            n_shift_after_cycle=Mobidai.shift.read(spec),
            source="",
        )
    elif name in mobidais:
        entry = mobidais[name].make()
    else:
        raise ValueError(f"No mobidai braid {name!r}: one of {sorted(mobidais)}.")
    config = entry.to_config()
    cycles = Mobidai.cycles.read(spec)
    diameter = DISK_YARN.read(spec)
    start, steps = mobidai_steps(config, cycles)
    clockwise = getattr(config, "is_clockwise", True)
    paths, clock, ring = _disk_in_step(
        start,
        steps,
        config.n_slots,
        diameter,
        DISK_ITERATIONS.read(spec),
        clockwise=clockwise,
    )
    # Coloured by strand, in the order the braid gives them.
    colour_of = {k: colour for k, (_, colour) in zip(start, entry.initial_slots)}
    disk = mobidai_trajectories(config, n_cycles=cycles, slot_offset=0.5)
    result = _result(
        f"{entry.name[0].upper()}{entry.name[1:]}, {cycles} cycles",
        paths,
        diameter,
        colours=[colour_of[k] for k in paths.points],
        info=_disk_unit(
            _disk_info(start, steps, config.n_slots, clockwise),
            lambda k: (*mobidai_steps(config, k), config.n_slots),
            clockwise,
        ),
        timeline=_timeline(disk, list(paths.points), "disk", clock, ring),
    )
    result["disk"] = _disk_program(
        start, steps, config.n_slots, clockwise, list(paths.points)
    )
    result["info"]["made"] = cycles
    return result


def _from_sinnet(spec: Spec) -> Result:
    from braidpy.ashley_solid_sinnet import strand_colours
    from braidpy.take_off import disk_trajectories

    from braidpy.ashley_solid_sinnet import AshleySolidSinnet

    sinnets = _sinnets()
    name = Sinnet.name.read(spec)
    if name == OWN:
        counts = _numbers(spec.get("counts", ""), "strands in each space")
        if len(counts) < 2 or min(counts) < 0 or sum(counts) < 2:
            raise ValueError("Give two spaces or more, holding two strands or more.")
        if sum(counts) > Sinnet.most_strands:
            raise ValueError(f"That is over {Sinnet.most_strands} strands.")
        moves = parse_moves(str(spec.get("moves", "")))
        if not all(1 <= p <= len(counts) for move in moves for p in move):
            raise ValueError(f"Moves are between spaces 1 to {len(counts)}.")
        sinnet = AshleySolidSinnet(counts, moves)
    elif name in sinnets:
        sinnet = sinnets[name].make()
    else:
        raise ValueError(f"No sinnet {name!r}: one of {sorted(sinnets)}.")
    cycles = Sinnet.cycles.read(spec)
    diameter = DISK_YARN.read(spec)
    disk = sinnet.disk(cycles)
    paths, clock, ring = _disk_in_step(
        disk.start,
        disk.steps,
        disk.n_slots,
        diameter,
        DISK_ITERATIONS.read(spec),
        clockwise=False,
    )
    seen = disk_trajectories(
        disk.start,
        disk.steps,
        disk.n_slots,
        clockwise=False,
        slot_offset=disk.slot_offset,
        slot_names={
            disk.middle_slot(space): str(space) for space in range(1, disk.n_spaces + 1)
        },
    )
    seen = _with_sectors(seen, disk)
    notes = []
    counts = list(sinnet.initial_counts_per_space)
    for source, target in sinnet.moves:
        counts[source - 1] -= 1
        counts[target - 1] += 1
    if counts != list(sinnet.initial_counts_per_space):
        notes.append(
            "Its moves do not bring every space back to its count after a "
            "cycle: the catalogue's moves may be mistranscribed."
        )
    called = "Your own" if name == OWN else f"ABOK #{name.split('_')[1]},"
    info = _disk_info(disk.start, disk.steps, disk.n_slots, clockwise=False)

    def worked(k: int):
        made = sinnet.disk(k)
        return made.start, made.steps, made.n_slots

    # Cycles that do not come back to the counts they started from do not
    # repeat: there is no saying when they are pure.
    if not notes:
        _disk_unit(info, worked, False)
    if sinnet.shape:
        info["expected_shape"] = sinnet.shape
    result = _result(
        f"{called} {sinnet.n_strands}-strand {sinnet.shape or 'sinnet'}, "
        f"{cycles} cycles",
        paths,
        diameter,
        colours=[strand_colours(sinnet.n_strands)[int(k) - 1] for k in paths.points],
        info=info,
        notes=notes,
        timeline=_timeline(seen, list(paths.points), "disk", clock, ring),
    )
    result["disk"] = _disk_program(
        disk.start, disk.steps, disk.n_slots, False, list(paths.points)
    )
    result["info"]["made"] = cycles
    return result


def _with_sectors(seen, disk):
    """A sinnet's disk as the book draws it: its spaces as sectors, a line
    from the middle to the rim half a slot before each space's first."""
    import dataclasses

    from braidpy.take_off import _disk_point

    lines = tuple(
        _disk_point(
            np.full(2, (space - 1) * disk.slots_per_space + 0.5),
            np.array([0.0, 1.0]),
            disk.n_slots,
            False,
            disk.slot_offset,
        )
        for space in range(1, disk.n_spaces + 1)
    )
    return dataclasses.replace(seen, outlines=seen.outlines + lines)


def _kumihimo_entry() -> Source:
    return {
        "title": "Kumihimo (S/R moves)",
        "defaults": defaults(*Kumihimo.shown),
    }


def _mobidai_entry() -> Source:
    entries: List[Entry] = [
        {
            "name": key,
            "title": catalogued.title,
            "pattern": {
                "n_slots": braid.n_slots,
                "slots": " ".join(str(slot) for slot, _ in braid.initial_slots),
                "moves": _moves_text(braid.moves),
                "shift": braid.n_shift_after_cycle,
            },
        }
        for key, catalogued in _mobidais().items()
        for braid in [catalogued.make()]
    ]
    return {
        "title": "Kumihimo disk (mobidai)",
        "defaults": defaults(*Mobidai.shown),
        "entries": entries + [{"name": OWN, "title": "Your own moves…"}],
    }


def _sinnet_entry() -> Source:
    entries: List[Entry] = [
        {
            "name": name,
            "title": catalogued.title,
            "shape": sinnet.shape,
            "pattern": {
                "counts": " ".join(str(c) for c in sinnet.initial_counts_per_space),
                "moves": _moves_text(sinnet.moves),
            },
        }
        for name, catalogued in _sinnets().items()
        for sinnet in [catalogued.make()]
    ]
    return {
        "title": "Ashley solid sinnet",
        "defaults": defaults(*Sinnet.shown),
        "entries": entries + [{"name": OWN, "title": "Your own moves…"}],
    }


# Each source: its catalogue entry, and what builds it.
SOURCES: Dict[str, Tuple[Callable[[], Source], Callable[[Spec], Result]]] = {
    "kumihimo": (_kumihimo_entry, _from_kumihimo),
    "mobidai": (_mobidai_entry, _from_mobidai),
    "sinnet": (_sinnet_entry, _from_sinnet),
}
