# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Braid words, flat or round a ring: laid as braidpy draws them, and as moves
on a ring of bobbins, for the page to make the braid move by move as on a
marudai."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, cast

from braidpy.utils import PALETTE
from braidpy.web._info import _braid_info, _unit
from braidpy.web._result import _result, _tighten, _timeline
from braidpy.web._settings import DISK_ITERATIONS, Word
from braidpy.web._spec import parse_word
from braidpy.web._types import DiskProgram, Example, Result, Source, Spec
from braidpy.web.disks import _disk_in_step


def _ring_program(moves: Sequence[int], n_strands: int, mirrored: bool) -> DiskProgram:
    """Ring moves (:func:`braidpy.annulus_braid.ring_moves`) as a disk program for the page: the
    braid hanging free, as a disk braid does, and held only while the
    bobbins turn round it, twisting the yarns in.  Strand ``k`` starts in place ``k``
    round the ring, or ``n - 1 - k`` numbered the other way; each place is
    ``slots`` slots on from the last.

    A swap is three moves: the strand passing under goes most of the way
    first, the one passing over is then laid across it, and the first goes
    the rest of the way."""
    n = n_strands
    slots = 12
    at = [n - 1 - p if mirrored else p for p in range(n)]
    start = [0] * n
    for place, strand in enumerate(at):
        start[strand] = 1 + slots * place
    steps: list[list[list[int]]] = []
    for move in moves:
        index, sign = abs(move), (1 if move > 0 else -1)
        if index == n + 1:
            steps.append([[strand, sign * slots] for strand in range(n)])
            at = at[-1:] + at[:-1] if sign > 0 else at[1:] + at[:1]
            continue
        a, b = index - 1, index % n
        over, under = (at[b], at[a]) if sign > 0 else (at[a], at[b])
        way = slots if under == at[a] else -slots
        most = round(0.75 * way)
        steps.append([[under, most], [over, -way], [under, way - most]])
        at[a], at[b] = at[b], at[a]
    return {
        "n_slots": n * slots,
        "clockwise": False,
        "start": start,
        "steps": steps,
        "twists": True,
        # Nothing but turns is a rope: held all the while it is laid up.
        "held": all(abs(move) == n + 1 for move in moves),
    }


def _ring_steps(program: DiskProgram):
    """A ring program (:func:`_ring_program`) as a disk's start and steps,
    as :func:`braidpy.take_off.disk_crossing_steps` takes them: strands by
    index, a turn of every bobbin one step, other moves one at a time."""
    start = dict(enumerate(program["start"]))
    n = len(start)
    steps: list[dict[int, int]] = []
    for step in program["steps"]:
        if len(step) == n and len({delta for _, delta in step}) == 1:
            steps.append({k: delta for k, delta in step})
        else:
            steps.extend({k: delta} for k, delta in step)
    return start, steps


def _word_round_ring(
    word: Sequence[int], n_strands: int, diameter: float, iterations: int
):
    """A flat braid word laid round a ring, as a disk braid is: each
    crossing two neighbours swapping places, none rolled into a turn of the
    bobbins — a turn on a disk crosses nothing, and the twist it stands for
    would be lost.  Read back round the ring, it is the word.

    Returns:
        The braid, and its timeline, the ring seen from above."""
    from braidpy.take_off import disk_trajectories

    program = _ring_program(word, n_strands, False)
    start, steps = _ring_steps(program)
    n_slots = program["n_slots"]
    paths, clock, ring = _disk_in_step(
        start, steps, n_slots, diameter, iterations, clockwise=True
    )
    disk = disk_trajectories(start, steps, n_slots, clockwise=True)
    return paths, _timeline(disk, list(paths.points), "disk", clock, ring)


def _in_order(program: DiskProgram, keys: Sequence[Any]) -> DiskProgram:
    """A ring program, its strands numbered 0, 1, … renumbered in the
    order ``keys`` gives them, as the braid's strands are."""
    index = {int(k): i for i, k in enumerate(keys)}
    if all(index[k] == k for k in index):
        return program
    start = [0] * len(keys)
    for k, slot in enumerate(program["start"]):
        start[index[k]] = slot
    steps = [[[index[k], delta] for k, delta in step] for step in program["steps"]]
    return cast(DiskProgram, {**program, "start": start, "steps": steps})


def _shortened(text: str, most: int = 32) -> str:
    """A long word cut short for a title."""
    text = " ".join(text.split())
    return text if len(text) <= most else text[:most].rsplit(" ", 1)[0] + " …"


def _from_word(spec: Spec) -> Result:
    from braidpy.annulus_braid import ring_moves, solid_word
    from braidpy.braid import Braid
    from braidpy.take_off import braid_word_trajectories, lay_yarns

    layout = Word.layout.read(spec)
    if layout not in Word.layouts:
        raise ValueError("Strands are either in a row or round a ring.")
    ring = layout == "ring"
    word = parse_word(Word.word.read(spec))
    if not word:
        raise ValueError("Give a braid word, for example 1 -2.")
    repeat = Word.repeat.read(spec)
    top = max(abs(g) for g in word)
    if ring:
        # Round a ring, the greatest move is taken for the seam's crossing.
        n_strands = Word.n_strands.read(spec, default=max(top, 2))
        if top > n_strands + 1:
            raise ValueError(
                f"On a ring of {n_strands} strands, moves go up to "
                f"{n_strands + 1}, a turn."
            )
        moves = word * repeat
        word = solid_word(moves, n_strands)
        if not word:
            raise ValueError("That ring word crosses nothing once laid flat.")
    else:
        needed = top + 1
        n_strands = Word.n_strands.read(spec, default=needed)
        if n_strands < needed:
            raise ValueError(f"σ{needed - 1} needs at least {needed} strands.")
        word = word * repeat
    if len(word) > Word.most_crossings:
        raise ValueError(
            f"That is over {Word.most_crossings} crossings: repeat it fewer times."
        )
    diameter = Word.yarn_diameter.read(spec)
    samples = (
        Word.samples
        if len(word) <= Word.samples_up_to
        else max(
            Word.fewest_samples, round(Word.samples * Word.samples_up_to / len(word))
        )
    )
    # Settled by physics, the strands are laid round a ring, as from a disk,
    # each crossing two neighbours swapping places: the moves a marudai
    # makes, so that the three ways of making a word make the same braid.
    # In a row, the yarns are laid on their fell ring, the size of the braid.
    on_ring = Word.settle.read(spec) in Word.by_physics
    if on_ring:
        paths, timeline = _word_round_ring(
            word, n_strands, diameter, DISK_ITERATIONS.read(spec)
        )
    else:
        trajectories = braid_word_trajectories(
            Braid(word, n_strands), samples_per_crossing=samples
        )
        paths = lay_yarns(trajectories, yarn_diameter=diameter)
        paths = _tighten(paths, spec, diameter)
        timeline = _timeline(trajectories, list(paths.points), "line")
    keys = list(paths.points)
    info = _braid_info(word, n_strands)
    once = (
        solid_word(moves[: len(moves) // repeat], n_strands)
        if ring
        else word[: len(word) // repeat]
    )
    _unit(info, once, n_strands, "repeat")
    if ring:
        info["annular_word"] = " ".join(str(g) for g in moves)
    result = _result(
        ("Ring word " if ring else "Braid word ")
        + _shortened(Word.word.read(spec))
        + (f", {repeat} times" if repeat > 1 else ""),
        paths,
        diameter,
        colours=[PALETTE[int(k) % len(PALETTE)] for k in keys],
        names=[f"Strand {k}" for k in keys],
        info=info,
        timeline=timeline,
    )
    # Made move by move round a ring: a ring word as it is written, a braid
    # word rolled onto the ring.
    if ring:
        program = _ring_program(moves, n_strands, False)
    else:
        rolled, mirrored = ring_moves(word, n_strands)
        program = _ring_program(rolled, n_strands, mirrored)
    result["disk"] = _in_order(program, keys)
    result["info"]["made"] = repeat
    return result


def _word_entry() -> Source:
    from braidpy.braid_catalog import word_examples

    return {
        "title": "Braid word",
        "defaults": dict(Word.starts),
        "examples": cast(list[Example], word_examples()),
    }


SOURCES: dict[str, tuple[Callable[[], Source], Callable[[Spec], Result]]] = {
    "word": (_word_entry, _from_word)
}
