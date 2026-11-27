# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""A braid designed in braid3d, the 3D braid designer of craftdesignonline.com
(see the references page), read from its file as a mobidai braid: the disk's
slots, where each yarn starts, and the moves of a cycle
(:class:`~braidpy.mobidai_catalog.CatalogedMobidai`).

The file (``.b3d``) is URL-encoded JSON: each yarn's colour, and the steps
the braid was designed by, each a group of moves of yarns from one angle
round the disk to another, or a repeat of earlier steps.  ``web/b3d.js``
writes one for a braid made on the marudai here (:func:`write_b3d` writes
any design's JSON so, :func:`read_b3d` reads it).  This needs only the
standard library, so that Braid Studio can read a design in the browser too.

How a file is read:

- **Where the yarns start**: the first list of where the yarns are that
  names each yarn once.  braid3d, and braidpy after it, write with each step
  where the yarns are before it, the first step's list left as it was by
  braid3d and where they start by braidpy: either way, that list is the
  start.
- **A step** moves the yarns standing at its moves' first angles, as braid3d
  does, each to its second angle, the short way round, one after another in
  the order given, but for a yarn going where another of the step is
  leaving, which waits for it to go, as a braider makes room.
- **A repeat** first moves the yarns back to where the repeated steps found
  them, then plays those steps again, so many times.  Moving them back must
  pass no yarn over another, which is checked: the yarns keep their order
  round the disk, only spaced otherwise.  Its ``rotate`` turns the whole
  braid, which moves nothing against anything else and changes nothing here.
- **The disk**: angles become the slots of a disk of as few slots as hold
  them all exactly; a design whose angles fall on no such disk is given as
  few as keep every yarn in its order round the disk and every move going
  the same way round.  The braid is the same; only the spacing differs.  A
  move of exactly half a turn, which the file cannot say the way round of,
  goes round as a mobidai's does.  braidpy writes a move of half a turn or
  more as two steps, each less than half a turn, so it is read going round
  as it went.
- **The cycle**: a design that is one cycle and a repeat of it is that
  cycle, made as many times; any other is all its moves, made once.
"""

from __future__ import annotations

import json
import math
import urllib.parse
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from braidpy._renamed import renamed_attribute

if TYPE_CHECKING:
    from braidpy.mobidai_catalog import CatalogedMobidai

__all__ = ["MOST_SLOTS", "Design", "mobidai_from_b3d", "read_b3d", "write_b3d"]

# The most slots a disk is given: a mobidai's most, in Braid Studio.
MOST_SLOTS = 128
# Angles this close, in radians, are one place: a move's first angle and the
# yarn standing there, or an angle and the slot it falls on exactly.
_SAME_ANGLE = 1e-6
# A move this close to half a turn, in radians, is half a turn, its way round
# unsaid: rounding.
_HALF = 1e-9
_TURN = 2 * math.pi
# The colour of a yarn the file gives none: a light grey.
_NO_COLOR = "#cccccc"


def _wrap(angle: float) -> float:
    """An angle in [-π, π)."""
    return (angle + math.pi) % _TURN - math.pi


def write_b3d(data: dict[str, Any]) -> str:
    """A braid3d design's JSON as its file holds it, URL-encoded
    (:func:`read_b3d` reads it back)."""
    return urllib.parse.quote(json.dumps(data, separators=(",", ":")))


def read_b3d(text: str) -> dict[str, Any]:
    """A braid3d file's JSON, URL-encoded or not.

    Raises:
        ValueError: If it holds no braid3d design.
    """
    text = text.strip()
    if not text.startswith("{"):
        text = urllib.parse.unquote(text)
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        raise ValueError("This is not a braid3d file: it holds no design.") from None
    if not isinstance(data, dict) or "nThreads" not in data or "steps" not in data:
        raise ValueError("This is not a braid3d file: it gives no yarns and steps.")
    return data


@dataclass(frozen=True)
class Group:
    """Moves made together: a step's, or a repeat's moving the yarns back.

    Attributes:
        moves: Each move's angles, from and to, in the order given.
        back: Whether it moves the yarns back, passing none over another.
    """

    moves: tuple[tuple[float, float], ...]
    back: bool = False


@dataclass(frozen=True)
class Design:
    """A braid3d design: where each yarn starts, in what colour, and the
    groups of moves made, a repeat played out.

    Attributes:
        start: Each yarn's angle at the start.
        colors: Each yarn's colour, as ``#rrggbb``.
        prelude: The groups made before the cycle, once.
        cycle: The groups of a cycle.
        times: How many times the cycle is made.
    """

    start: dict[int, float]
    colors: tuple[str, ...]
    prelude: tuple[Group, ...]
    cycle: tuple[Group, ...]
    times: int

    # Its name before braidpy's code took American spelling.
    colours = renamed_attribute("colors")

    @classmethod
    def read(cls, text: str) -> Design:
        """The design a braid3d file holds.

        Raises:
            ValueError: If it holds none, or does what is not read here.
        """
        data = read_b3d(text)
        n = int(data["nThreads"])
        threads = (data.get("threadStates") or [])[:n]
        colors = tuple(
            f"#{int(t['colour']):06x}" if "colour" in t else _NO_COLOR for t in threads
        ) + (_NO_COLOR,) * (n - len(threads))
        steps = data["steps"]
        start = _start(steps, n)
        last = len(steps) - 1
        repeats = [k for k, step in enumerate(steps) if step.get("type") == "repeat"]
        if repeats == [last] and int(steps[last].get("repeatTimes") or 0) > 0:
            first = _repeated_from(steps, last)
            return cls(
                start,
                colors,
                tuple(_groups(steps, 1, first)),
                (*_groups(steps, first, last), _back(steps[last])),
                1 + int(steps[last]["repeatTimes"]),
            )
        return cls(start, colors, (), tuple(_groups(steps, 1, len(steps))), 1)


def _start(steps: Sequence[dict[str, Any]], n: int) -> dict[int, float]:
    """Where each yarn starts: the first list of where the yarns are that
    names each yarn once."""
    for step in steps:
        poss = step.get("poss") or []
        if sorted(int(p["id"]) for p in poss) == list(range(n)):
            return {int(p["id"]): float(p["angle"]) for p in poss}
    raise ValueError("The file never says where every yarn is: nowhere to start.")


def _repeated_from(steps: Sequence[dict[str, Any]], k: int) -> int:
    """The first step a repeat at step ``k`` plays again."""
    first = int(steps[k].get("repeatFrom") or 0)
    if not 0 < first < k:
        raise ValueError(f"Step {k} repeats from step {first}: there is none.")
    return first


def _back(step: dict[str, Any]) -> Group:
    """A repeat's moving the yarns back."""
    return Group(tuple((float(m["from"]), float(m["to"])) for m in step["moves"]), True)


def _groups(
    steps: Sequence[dict[str, Any]], first: int, end: int, depth: int = 0
) -> Iterator[Group]:
    """The groups of moves steps ``first`` to ``end`` make, a repeat among
    them played out."""
    if depth > len(steps):
        raise ValueError("Its repeats repeat one another without end.")
    for k in range(first, end):
        step = steps[k]
        kind = step.get("type")
        if kind == "threadMove":
            yield Group(
                tuple((float(m["from"]), float(m["to"])) for m in step["moves"])
            )
        elif kind == "repeat":
            again = _repeated_from(steps, k)
            for _ in range(int(step.get("repeatTimes") or 0)):
                yield _back(step)
                yield from _groups(steps, again, k, depth + 1)
        elif kind is not None:
            raise ValueError(f"Step {k} is a {kind!r} step: not read here.")


def _found(where: dict[int, float], angle: float) -> int:
    """The yarn standing at an angle."""
    for yarn, at in where.items():
        if abs(_wrap(at - angle)) < _SAME_ANGLE:
            return yarn
    raise ValueError(f"A move starts at {math.degrees(angle):.1f}°, where no yarn is.")


def _order(where: dict[int, float]) -> tuple[int, ...]:
    """The yarns in order round the disk, read from the least of them."""
    ranked = sorted(where, key=lambda yarn: _wrap(where[yarn]))
    k = ranked.index(min(ranked))
    return tuple(ranked[k:] + ranked[:k])


def _played(groups: Sequence[Group], where: dict[int, float]):
    """Each group as the yarns it moves, in the order given, with the angles
    each goes from and to; ``where`` follows them."""
    for group in groups:
        before = dict(where)
        moved = [(_found(before, start), end) for start, end in group.moves]
        for yarn, end in moved:
            where[yarn] = end
        if group.back and _order(where) != _order(before):
            raise ValueError(
                "Moving the yarns back for a repeat passes one over another: "
                "not read here."
            )
        yield group, [(yarn, before[yarn], end) for yarn, end in moved]


def _same_places(these, those) -> bool:
    """Whether two lists of angles are the same places round the disk."""
    ours, theirs = sorted(map(_wrap, these)), sorted(map(_wrap, those))
    return len(ours) == len(theirs) and all(
        abs(_wrap(x - y)) < _SAME_ANGLE for x, y in zip(ours, theirs)
    )


def _slot_of(angle: float, n_slots: int) -> int:
    """The slot of a mobidai's disk an angle falls on: the inverse of
    :func:`~braidpy.marudai.slot_angle` for a clockwise disk, a mobidai's,
    whose slots go round the way braid3d's angles do."""
    return round(_wrap(angle) % _TURN / _TURN * n_slots) % n_slots + 1


def _fits(angles: Sequence[float], turns, n: int) -> bool:
    """Whether a disk of ``n`` slots keeps the angles apart — and so in their
    order round it — and each move going the same way round."""
    if len({_slot_of(angle, n) for angle in angles}) < len(angles):
        return False
    for start, end in turns:
        turn = _wrap(end - start)
        steps = (_slot_of(end, n) - _slot_of(start, n)) % n
        if abs(turn) < _SAME_ANGLE:
            continue
        if abs(abs(turn) - math.pi) < _HALF:
            # Half a turn: no way round to keep.
            if 2 * steps != n:
                return False
        elif steps == 0 or 2 * steps == n or (turn > 0) != (2 * steps < n):
            return False
    return True


def _exact(angles: Sequence[float], n: int) -> bool:
    """Whether every angle falls on a slot of a disk of ``n``."""
    from braidpy.marudai import slot_angle

    return all(
        abs(_wrap(angle - slot_angle(_slot_of(angle, n), n, clockwise=True)))
        < _SAME_ANGLE
        for angle in angles
    )


def _disk(angles: Sequence[float], turns, most: int) -> int:
    """The fewest slots holding the angles: exactly if a disk does, else
    keeping their order and the moves' ways round."""
    distinct: list[float] = []
    for angle in angles:
        if all(abs(_wrap(angle - seen)) >= _SAME_ANGLE for seen in distinct):
            distinct.append(angle)
    least = max(1, len(distinct))
    for n in range(least, most + 1):
        if _exact(distinct, n) and _fits(distinct, turns, n):
            return n
    for n in range(least, most + 1):
        if _fits(distinct, turns, n):
            return n
    raise ValueError(f"Its yarns stand too close together for a disk of {most} slots.")


def _path(start: int, end: int, n: int) -> set[int]:
    """The slots a move passes before its last, the short way round."""
    steps = (end - start) % n
    way, count = (1, steps) if 2 * steps < n else (-1, n - steps)
    return {(start - 1 + way * k) % n + 1 for k in range(1, count)}


def _in_turn(
    group: Group, moved: list[tuple[int, int]], slot: dict[int, int], n: int
) -> Iterator[tuple[int, int]]:
    """A group's moves as slot moves made one after another: in the order
    given, a move to where another of the group is leaving waiting for it;
    moving the yarns back, also passing no other yarn.  ``slot`` follows."""
    left = [(yarn, target) for yarn, target in moved if target != slot[yarn]]
    while left:
        for k, (yarn, target) in enumerate(left):
            taken = {s for other, s in slot.items() if other != yarn}
            if target in taken:
                continue
            if group.back and _path(slot[yarn], target, n) & taken:
                continue
            yield (slot[yarn], target)
            slot[yarn] = target
            del left[k]
            break
        else:
            if group.back:
                raise ValueError(
                    "Moving the yarns back for a repeat turns them all round "
                    "together: not read here."
                )
            raise ValueError(
                "In a step, yarns take one another's places: not read here."
            )


def mobidai_from_b3d(
    text: str, name: str = "braid3d design", most_slots: int = MOST_SLOTS
) -> tuple[CatalogedMobidai, int]:
    """A braid3d design as a mobidai braid, and how many cycles make it.

    Args:
        text: The file's text.
        name: What to call it.
        most_slots: The most slots its disk may have.

    Returns:
        The mobidai braid — its disk, where each yarn starts, in its colour,
        and a cycle's moves — and how many cycles.

    Raises:
        ValueError: If the file holds no braid3d design, or one that does
            what is not read here.
    """
    from braidpy.mobidai_catalog import CatalogedMobidai

    design = Design.read(text)
    if design.prelude or design.times == 1:
        groups, times = (*design.prelude, *design.cycle * design.times), 1
    else:
        groups, times = design.cycle, design.times
    where = dict(design.start)
    played = list(_played(groups, where))
    if times > 1 and not _same_places(where.values(), design.start.values()):
        raise ValueError(
            "Its repeat does not bring the yarns back to where they started: "
            "not read here."
        )
    angles = [*design.start.values()] + [
        end for _, moved in played for *_, end in moved
    ]
    turns = [(start, end) for _, moved in played for _, start, end in moved]
    n = _disk(angles, turns, most_slots)

    slot = {yarn: _slot_of(angle, n) for yarn, angle in design.start.items()}
    yarns = sorted(slot)
    starts = [slot[yarn] for yarn in yarns]
    moves: list[tuple[int, int]] = []
    for group, moved in played:
        targets = [(yarn, _slot_of(end, n)) for yarn, _, end in moved]
        moves += _in_turn(group, targets, slot, n)
    return (
        CatalogedMobidai(
            name=name,
            n_slots=n,
            initial_slots=tuple(zip(starts, (design.colors[y] for y in yarns))),
            moves=tuple(moves),
            source="braid3d",
        ),
        times,
    )
