# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""The shapes of what :mod:`braidpy.web` takes and gives, as typed
dictionaries: plain JSON-ready data for the page, checked here by mypy.

A description of a braid (:class:`Spec`) comes from the page's form or its
address, so its numbers may come as numbers or as text: each builder reads
what it needs, checking it (:mod:`braidpy.web._settings`).
"""

from __future__ import annotations

from typing import Any, TypedDict

# A number as the page may give it: typed in, it comes as text.
Value = str | float | None

# A point, in the plane or in space.
Point = list[float]


class Spec(TypedDict, total=False):
    """A description of a braid: where it comes from, and its settings."""

    source: str
    # Every source.
    yarn_diameter: Value
    iterations: Value
    # How the page settles it; braidpy reads ``settle`` for words only.
    settle: str
    twist: str
    # A braid word.
    word: str
    layout: str
    n_strands: Value
    repeat: Value
    # Kumihimo.
    pattern: str
    # A catalogued braid: mobidai, sinnet, machine.
    name: str
    cycles: Value
    # Your own mobidai braid or sinnet.
    slots: str
    moves: str
    n_slots: Value
    shift: Value
    counts: str
    # A machine.
    carriers: str
    core: str
    # A link made before ``core``: how stiff a machine's own cores are.
    cores: str
    # Your own lace machine.
    n_gears: Value
    card: str
    # Your own horn gear machine: the gears that mesh (and n_slots).
    graph: str


# ------------------------------------------------------------------ result


class Strand(TypedDict):
    """One yarn: its name and colour, and its centreline, oldest first."""

    name: str
    colour: str
    points: list[Point]


class Garside(TypedDict):
    """The Garside normal form, as counts."""

    half_twists: int
    factors: int
    full_twists: int


class Collision(TypedDict):
    """Where carriers met and stopped a machine: the step, and the carriers
    that met, as ``[gear, slot]`` where they started."""

    step: int
    at: list[list[str | int]]


class Info(TypedDict, total=False):
    """What is known of the braid, for the page's info card."""

    n_strands: int
    word: str
    annular_word: str
    crossings: int
    exponent_sum: int
    permutation: list[int]
    components: int
    garside: Garside
    # How many of its unit — its word, or its moves' cycle — make it pure,
    # None if there is no saying; what the unit is; how many were made, and
    # whether that is pure.
    pure_after: int | None
    repeated: str
    made: int
    pure: bool
    # Pure, and trivial with any one strand out (Braid.is_brunnian): said
    # only of a pure braid small enough to ask.
    brunnian: bool
    closest_approach: float
    expected_shape: str
    collision: Collision


class Clock(TypedDict):
    """The source's time at some instants, and the braid's then."""

    source: list[float]
    braid: list[float]


class Track(TypedDict):
    """A carrier track, seen from above: the closed curve the carriers on it
    follow, and the colour braidpy draws it in."""

    colour: str
    points: list[Point]


class _Timeline(TypedDict):
    kind: str
    times: list[float]
    strands: list[list[Point]]
    outlines: list[list[Point]]
    slots: list[list[float | str]]
    reach: float
    clock: Clock


class Timeline(_Timeline, total=False):
    """What made the braid, seen from above, over time: each carrier's path,
    the outlines under them and the slots, named; for a disk, how far its
    braid turns with it; for a machine of fixed tracks, its tracks."""

    turn: list[float]
    tracks: list[Track]


class Tightening(TypedDict):
    """What tightening the yarns needs, for a page that does it itself, as
    :func:`braidpy.take_off.tighten_yarns` would: the samples' ``xy``, yarn
    after yarn, and its settings; ``chosen``, which samples the strands'
    points are, and ``centre``, what was taken off them; ``partner``, the
    yarn each runs into past the fell end, for tightening it endless
    (:class:`braidpy.take_off.Periodic`), None if the braid does not close."""

    n_yarns: int
    n: int
    spacing: float
    yarn_diameter: float
    iterations: int
    step: float
    tolerance: float
    hold_top: bool
    core_radius: float | None
    centre: list[float]
    xy: list[float]
    rigid: list[bool]
    partner: list[int] | None
    chosen: list[int]


class _DiskProgram(TypedDict):
    n_slots: int
    clockwise: bool
    start: list[int]
    steps: list[list[list[int]]]


class DiskProgram(_DiskProgram, total=False):
    """What a disk does, for the page to make the braid move by move: each
    strand's slot to start with, and per step, the strands that move, by
    index, and by how many slots.  A word's ring program also says whether
    its bobbins' turns twist the yarns in, and whether it is held; and a
    disk braid round a core, the core's kind: yarn or rigid."""

    twists: bool
    held: bool
    core: str


class _Result(TypedDict):
    title: str
    strands: list[Strand]
    times: list[float]
    yarn_diameter: float
    info: Info
    notes: list[str]


class Result(_Result, total=False):
    """A braid, as :func:`braidpy.web.build` gives it."""

    timeline: Timeline
    tighten: Tightening
    disk: DiskProgram
    # To make it by its carriers: braidpy.carried.carriers_job.
    carriers: dict[str, Any]


# --------------------------------------------------------------- catalogue

# A setting's value, as the catalogue gives it.
Default = str | int | float


class Example(TypedDict, total=False):
    """A braid word worth trying, with a title."""

    title: str
    word: str
    layout: str
    n_strands: int
    repeat: int


class Entry(TypedDict, total=False):
    """A catalogued braid, named, and what it is made of, to show or change."""

    name: str
    title: str
    shape: str | None
    pattern: dict[str, Default]


class _Source(TypedDict):
    title: str
    defaults: dict[str, Default]


class Source(_Source, total=False):
    """A source of braids: its title, its defaults, and what it offers."""

    entries: list[Entry]
    examples: list[Example]


# ---------------------------------------------------------------- machines


class Gear(TypedDict):
    """A gear seen from above: where it is, how big, the circle its carriers
    ride, its slots, the way it turns and where each slot is at step 0."""

    name: str
    x: float
    y: float
    radius: float
    ride: float
    slots: int
    direction: int
    # Each slot's angle at step 0, as braidpy draws it
    # (braidpy.horn_gear.layout.GearAngles).
    angles: list[float]


class Contact(TypedDict):
    """Where two gears meet."""

    a: str
    b: str
    x: float
    y: float


class TurnedFrame(TypedDict):
    """One picture of a machine turning: every slot's and carrier's place."""

    slots: list[list[float]]
    carriers: list[list[float]]


class MachineTurned(TypedDict):
    """A machine's handle turned by hand, as the page shows it."""

    time: int
    carriers: list[list[str | int]]
    met: list[list[str | int]]
    slots: list[list[str | int]]
    frames: list[TurnedFrame]


class MachineGeometry(TypedDict):
    """A machine as the page draws it from above, to load it by hand."""

    name: str
    gears: list[Gear]
    contacts: list[Contact]
    loading: list[list[str | int]]
    # Every place it could feed an axial yarn, as written and where; those
    # it feeds; and the colour cores are drawn in.
    axials: list[dict[str, Any]]
    own_axials: list[str]
    core_colour: str
    # The gears that mesh, and the slots most have; None for a machine of
    # split gears, or a lace machine.
    graph: dict[str, Any] | None
    # The carriers' tracks; none for a machine driven by a programme.
    tracks: list[Track]
