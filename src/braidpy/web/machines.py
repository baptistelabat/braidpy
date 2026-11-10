# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Horn gear braiding machines: the braid a machine makes, loaded as it loads
itself or by hand, stopped where carriers meet; and the machine as the page
draws it from above, to load it by hand."""

from __future__ import annotations

import re
from collections.abc import Callable
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    cast,
)

from braidpy.web._info import _braid_info

if TYPE_CHECKING:
    from braidpy.horn_gear.jacquard import JacquardLaceMachine
from braidpy.utils import PALETTE
from braidpy.web._result import (
    _place_cores,
    _result,
    _tighten,
    _timeline,
    _with_core,
)
from braidpy.web._settings import (
    CORE,
    CORE_COLOUR,
    CORE_KINDS,
    DISK_ITERATIONS,
    OLD_CORES,
    OWN,
    Lace,
    Machine,
    Word,
)
from braidpy.web._spec import defaults
from braidpy.web._types import (
    Collision,
    Info,
    MachineGeometry,
    MachineTurned,
    Result,
    Source,
    Spec,
)


def _machines():
    """Every catalogued machine the page can draw and turn by hand, by
    name: the horn gear machines and the lace machines."""
    from braidpy.machine_catalog import CATALOGUE, LACE

    return {**CATALOGUE, **LACE}


# A lace machine with a card of your own goes by its gears and card, for
# the page to draw it and turn it by hand as a catalogued one:
# "lace:6:100000 010000 ...".
OWN_LACE = "lace:"


def _machine(name: str) -> Any:
    """A machine by name: catalogued, or a lace machine of your own."""
    if name.startswith(OWN_LACE):
        n_gears, _, card = name[len(OWN_LACE) :].partition(":")
        return _own_lace({"n_gears": n_gears, "card": card})
    from braidpy.machine_catalog import LaceRing

    machines = _machines()
    if name not in machines:
        raise ValueError(f"No machine {name!r}: one of {sorted(machines)}.")
    made = machines[name].make()
    return made.machine() if isinstance(made, LaceRing) else made


def _read_card(text: str, n_gears: int) -> list[tuple[str, str]]:
    """A card as typed: groups of 0 and 1, a digit a gear, taken two by two
    — the gears turning anticlockwise, then clockwise — however the steps
    are laid out on lines."""
    groups = re.findall(r"\S+", text)
    for group in groups:
        if not re.fullmatch(r"[01]+", group):
            raise ValueError(
                f"Cannot read {group!r}: a card is 0 and 1, a digit a gear."
            )
        if len(group) != n_gears:
            raise ValueError(
                f"{group!r} has {len(group)} digits: give one for each of the "
                f"{n_gears} gears."
            )
    if not groups:
        raise ValueError(
            "Give the card: per step, the gears turning anticlockwise, then clockwise."
        )
    if len(groups) % 2:
        raise ValueError(
            "A step is two groups: the gears turning anticlockwise, then those "
            "turning clockwise."
        )
    return [(groups[k], groups[k + 1]) for k in range(0, len(groups), 2)]


def _own_lace(spec: Spec) -> Any:
    """A lace machine of your own: its gears, an even number, and its card."""
    from braidpy.horn_gear.jacquard import jacquard_lace_ring

    n_gears = _own_gears(spec)
    return jacquard_lace_ring(n_gears, _read_card(Lace.card.read(spec), n_gears))


def _own_gears(spec: Spec) -> int:
    """How many gears your own lace ring has: an even number."""
    n_gears = Lace.n_gears.read(spec)
    if n_gears % 2:
        raise ValueError(
            f"{n_gears} gears cannot mesh in a ring: neighbours turn opposite "
            "ways, so give an even number."
        )
    return n_gears


def _from_machine(spec: Spec) -> Result:
    from braidpy.horn_gear import gear_radii
    from braidpy.horn_gear.word import annular_word, flat_word
    from braidpy.machine_catalog import CATALOGUE as machines

    name = Machine.name.read(spec)
    if name not in machines:
        raise ValueError(f"No machine {name!r}: one of {sorted(machines)}.")
    machine = machines[name].make()
    cycles = Machine.cycles.read(spec)
    radii = gear_radii(machine)
    default = Machine.of_gear_radius * sum(radii.values()) / len(radii)
    diameter = Machine.yarn_diameter.read(spec, default=default)
    machine, cores, rigid = _cored(machine, spec)
    # Loaded by hand, or as the machine loads itself.  Carriers that meet
    # stop the machine: the braid is what it made until then.
    loading = _loading(spec.get("carriers"), machine)
    carriers_at = None if loading is None else dict(enumerate(loading))
    period = None
    if carriers_at is not None:
        from braidpy.horn_gear.simulation import state_period

        period = state_period(machine, carriers_at) or machine.contact_period()
    paths, stopped, n_steps = _braided(machine, carriers_at, cycles, period, diameter)
    paths = _place_cores(paths, cores)
    paths = _tighten(paths, spec, diameter, rigid=list(cores) if rigid else [])
    info: Info = {}
    notes = ["Words are read over one cycle of the machine."]
    if stopped is not None:
        assert loading is not None
        info["collision"] = _collision(stopped, loading)
        notes = [_stopped_note(stopped, n_steps)]
    elif cores:
        notes = [_core_note(rigid, len(cores))]
    elif name.startswith("tubular"):
        annular = annular_word(machine, carriers=carriers_at)
        info["annular_word"] = " ".join(str(g) for g in annular.generators)
        info["crossings"] = len(annular.generators)
    else:
        # Read over one cycle of the machine.
        info.update(
            _braid_info(flat_word(machine, carriers=carriers_at), len(paths.points))
        )
        info["repeated"] = "cycle"
        info["made"] = cycles
        # The cycles made, not the one read.
        info["pure"] = cycles % (info.get("pure_after") or 1) == 0
    keys = list(paths.points)
    carriers = [k for k in keys if k not in cores]
    own = machine.carrier_colours(carriers_at) or {}
    colour = {k: own.get(k, PALETTE[i % len(PALETTE)]) for i, k in enumerate(carriers)}
    colour.update({k: CORE_COLOUR for k in cores})
    return _result(
        machines[name].title + f", {cycles} cycles",
        paths,
        diameter,
        colours=[colour[k] for k in keys],
        names=[f"Core {k}" if k in cores else f"Yarn {k}" for k in keys],
        info=info,
        notes=notes,
        timeline=_timeline(paths.trajectories, keys, "machine"),
    )


def _cored(machine: Any, spec: Spec) -> tuple[Any, dict[str, Any], bool]:
    """The machine braiding round the core asked for (``CORE``): its own
    cores, none, or — for a machine with none of its own that is one ring
    of gears — one down the hole of the ring
    (:func:`~braidpy.horn_gear.ring_core`).

    The cores run up the braid, each in its own place, where the machine
    lays it; the yarns are drawn in round them.  A rigid core stays straight
    there; a core of yarn is held there at both ends, and gives way between
    to the yarns pressing on it — never so far as to pass another core.

    Returns:
        The machine, where its cores stand, by name, and whether they are
        rigid.

    Raises:
        ValueError: For a core asked of a machine with nowhere for one.
    """
    from braidpy.horn_gear import axial_positions, compute_layout, ring_core

    if CORE.key in spec:
        asked = CORE.read(spec)
    else:
        # A link made before says only how stiff the machine's own cores are.
        asked = "rigid" if OLD_CORES.read(spec) == "rigid" and machine.axials else "own"
    if asked not in CORE_KINDS:
        raise ValueError(f"A core is one of {', '.join(CORE_KINDS)}.")
    layout = compute_layout(machine)
    if asked == "none":
        machine = machine.with_axials([])
    elif asked != "own" and not machine.axials:
        core = ring_core(machine, layout)
        if core is None:
            raise ValueError(
                "This machine has nowhere for a core: a core goes down the hole "
                "a ring of gears encloses, where the carriers leave room for it."
            )
        machine = machine.with_axials([core])
    return machine, axial_positions(machine, layout), asked == "rigid"


def _core_note(rigid: bool, n_cores: int = 1) -> str:
    if n_cores == 1:
        kind = (
            "rigid, it stays straight"
            if rigid
            else "of yarn, it gives way to the others"
        )
        return (
            f"It braids round a core, drawn in grey: {kind}. Its word would need "
            "the core as a strand of its own: no word is given."
        )
    kind = (
        "rigid, they stay straight" if rigid else "of yarn, they give way to the others"
    )
    return (
        f"It braids round {n_cores} cores, drawn in grey: {kind}. Its word would "
        "need the cores as strands of their own: no word is given."
    )


def _braided(
    machine: Any,
    carriers_at: dict[int, tuple[str, int]] | None,
    cycles: int,
    period: int | None,
    diameter: float,
) -> tuple[Any, Any, int | None]:
    """The yarns a machine lays, ``cycles`` times ``period`` steps — or its
    own cycles, if no period is given — stopped where carriers meet.

    Returns:
        The yarn paths, the collision that stopped the machine if one did,
        and the steps turned (None for the machine's own cycles).

    Raises:
        ValueError: If carriers meet as soon as the machine turns.
    """
    from braidpy.horn_gear import yarn_paths

    stopped = None
    n_steps = None
    if period is not None:
        from braidpy.horn_gear.simulation import CollisionError, simulate

        n_steps = cycles * period
        try:
            simulate(machine, n_steps, carriers_at)
        except CollisionError as error:
            stopped = error
            n_steps = error.step - 1
            if n_steps < 1:
                raise ValueError(
                    "Those carriers meet as soon as the machine turns: "
                    + _met(error)
                    + "."
                ) from None
    paths = yarn_paths(
        machine,
        n_steps=n_steps,
        carrier_positions=carriers_at,
        n_cycles=cycles,
        yarn_diameter=diameter,
        axials=True,
    )
    return paths, stopped, n_steps


def _collision(stopped: Any, loading: list[tuple[str, int]]) -> Collision:
    """The carriers that met, where they started: as the page draws the
    machine, before it turns."""
    return {
        "step": int(stopped.step),
        "at": [
            [loading[k][0], int(loading[k][1])]
            for ids in stopped.collisions.values()
            for k in ids
        ],
    }


def _stopped_note(stopped: Any, n_steps: int | None) -> str:
    return (
        f"Carriers met at step {stopped.step}, on {_met(stopped)}: the "
        f"braiding stopped there, after {n_steps} steps. The carriers that "
        "met are ringed where they started. No word is read."
    )


def _notch_names(n_gears: int) -> dict[str, int]:
    """A lace ring's notches by name, ``A-B``, as its card names them: the
    notch gears A and B cut is notch 0, and so round."""
    names = [chr(ord("A") + g) for g in range(n_gears)]
    return {f"{names[k]}-{names[(k + 1) % n_gears]}": k for k in range(n_gears)}


def _lace_threading(text: Any, n_gears: int) -> list[int] | None:
    """The notches bobbins are put in, strand after strand: by name, ``A-B``,
    or as ``gear:slot`` at the start — slot 0 of a gear faces the next gear
    round the ring, slot 1 the previous.  None if not given."""
    if text is None or not str(text).strip():
        return None
    if str(text).strip().lower() == "none":
        raise ValueError("Give at least one bobbin.")
    named = _notch_names(n_gears)
    threaded: list[int] = []
    for token in re.split(r"[\s,;]+", str(text).strip()):
        match = re.fullmatch(r"([A-Za-z]):([01])", token)
        if token in named:
            notch = named[token]
        elif match and ord(match.group(1).upper()) - ord("A") < n_gears:
            gear = ord(match.group(1).upper()) - ord("A")
            notch = gear if match.group(2) == "0" else (gear - 1) % n_gears
        else:
            raise ValueError(
                f"Cannot read {token!r}: give each bobbin by its notch, A-B, "
                "or as gear:slot."
            )
        if notch in threaded:
            raise ValueError(f"Two bobbins in the same notch, {token}.")
        threaded.append(notch)
    return threaded


def _lace_card(spec: Spec) -> tuple[str, int, list[Any], list[int] | None]:
    """The lace machine asked for, as its card: its title, its gears, per
    step whether each gear turns anticlockwise, then clockwise, and the
    notches threaded, strand after strand (every one if None).  Read without
    building the machine."""
    from braidpy.machine_catalog import LACE

    name = Lace.name.read(spec)
    if name == OWN:
        n_gears = _own_gears(spec)
        steps = [
            (tuple(c == "1" for c in ccw), tuple(c == "1" for c in cw))
            for ccw, cw in _read_card(Lace.card.read(spec), n_gears)
        ]
        threaded: list[int] | None = None
        title = f"Your own card, {n_gears} gears"
    elif name in LACE:
        ring = LACE[name].make()
        n_gears, steps, title = ring.n_gears, list(ring.steps), LACE[name].title
        threaded = None if ring.threaded is None else list(ring.threaded)
    else:
        raise ValueError(f"No lace machine {name!r}: one of {sorted(LACE)}.")
    threaded = _lace_threading(spec.get("carriers"), n_gears) or threaded
    return title, n_gears, steps, threaded


def _lace_disk(spec: Spec):
    """The card asked for run round its ring, ``cycles`` passes, as a disk
    program for the page's marudai; and one pass, as a ring program."""
    from braidpy.making.lace import card_program
    from braidpy.ring_program import RingProgram
    from braidpy.web.words import place_program

    title, n_gears, steps, threaded = _lace_card(spec)
    once = card_program(n_gears, steps, threaded)
    whole = RingProgram(once.n_places, once.start, once.rows * Lace.cycles.read(spec))
    return title, steps, once, place_program(whole)


def _lace_on_disk(spec: Spec) -> Result:
    """A lace machine's braid made on a marudai: the card run round its ring
    of notches, each gear's turn its two notches swapping bobbins
    (:func:`~braidpy.making.lace.card_program`), the bobbins moved as a
    disk's.  Worked out from the card alone: no machine is built, so nothing
    is loaded that the machine needs.

    Round a core, it goes down the marudai's middle, as a disk braid's
    (:func:`~braidpy.web.disks._disk_in_step`): a marudai has room for one
    whatever card it is made from.
    """
    from braidpy.making.lace import punchcard_text
    from braidpy.take_off import disk_trajectories
    from braidpy.web.disks import CORE_NAME, _cored, _disk_in_step
    from braidpy.web.words import _in_order, _ring_steps

    core = CORE.read(spec)
    if core not in CORE_KINDS:
        raise ValueError(f"A core is one of {', '.join(CORE_KINDS)}.")
    # A lace machine has no core of its own.
    core = "none" if core == "own" else core
    title, steps, once, disk = _lace_disk(spec)
    cycles = Lace.cycles.read(spec)
    diameter = Machine.yarn_diameter.read(spec, default=Word.yarn_diameter.default)
    start, moves = _ring_steps(disk)
    paths, clock, ring_seen = _disk_in_step(
        start,
        moves,
        disk["n_slots"],
        diameter,
        DISK_ITERATIONS.read(spec),
        clockwise=True,
        core=core,
    )
    keys = list(paths.points)
    bobbins = [k for k in keys if k != CORE_NAME]
    trajectories = disk_trajectories(start, moves, disk["n_slots"], clockwise=True)
    if core != "none":
        trajectories = _with_core(trajectories, CORE_NAME)
    info: Info = {}
    word = [int(g) for g in once.braid().generators]
    info.update(_braid_info(word, len(bobbins)))
    info["repeated"] = "cycle"
    info["made"] = cycles
    info["pure"] = cycles % (info.get("pure_after") or 1) == 0
    result = _result(
        title + f", {cycles} passes",
        paths,
        diameter,
        colours=[PALETTE[i % len(PALETTE)] for i in range(len(keys))],
        names=[f"Bobbin {k}" for k in keys],
        info=info,
        notes=[
            "Made on a marudai: the card run round its ring of notches, each "
            "gear's turn its two notches swapping bobbins. Words are read over "
            "one pass of the card. The card, a column a gear, two lines a step "
            "— the gears turning anticlockwise ↺, then clockwise ↻ — ● "
            "punched:\n" + punchcard_text(steps)
        ],
        timeline=_timeline(trajectories, keys, "disk", clock, ring_seen),
    )
    return _cored(result, core, keys, _in_order(disk, bobbins))


def _from_lace(spec: Spec) -> Result:
    """A Jacquard lace machine's braid: its card run so many passes, read
    off the machine itself (:func:`~braidpy.making.lace.ring_braid`) — or,
    to be made on a marudai, off its card (:func:`_lace_on_disk`)."""
    if Lace.settle.read(spec) == "marudai":
        return _lace_on_disk(spec)
    from braidpy.horn_gear import gear_radii
    from braidpy.machine_catalog import LACE
    from braidpy.making.lace import punchcard_text, ring_braid

    name = Lace.name.read(spec)
    if name == OWN:
        machine = cast("JacquardLaceMachine", _own_lace(spec))
        title = f"Your own card, {len(machine.gears)} gears"
    elif name in LACE:
        machine = cast("JacquardLaceMachine", LACE[name].make().machine())
        title = LACE[name].title
    else:
        raise ValueError(f"No lace machine {name!r}: one of {sorted(LACE)}.")
    cycles = Lace.cycles.read(spec)
    radii = gear_radii(machine)
    default = Machine.of_gear_radius * sum(radii.values()) / len(radii)
    diameter = Machine.yarn_diameter.read(spec, default=default)
    # Threaded by hand, or as the card says; a pass of the card is two of
    # the machine's steps a punched step.
    loading = _loading(spec.get("carriers"), machine)
    own = machine.default_carriers()
    carriers_at = dict(enumerate(loading)) if loading else own
    machine, cores, rigid = _cored(machine, spec)
    paths, stopped, n_steps = _braided(
        machine, carriers_at, cycles, machine.steps_per_pass, diameter
    )
    paths = _place_cores(paths, cores)
    paths = _tighten(paths, spec, diameter, rigid=list(cores) if rigid else [])
    info: Info = {}
    card = (
        "The card, a column a gear, two lines a step — the gears turning "
        "anticlockwise ↺, then clockwise ↻ — ● punched:\n"
        + punchcard_text(machine.program)
    )
    notes = ["Words are read over one pass of the card. " + card]
    if stopped is not None:
        info["collision"] = _collision(
            stopped, loading or [own[k] for k in sorted(own)]
        )
        notes = [_stopped_note(stopped, n_steps)]
    elif cores:
        notes = [_core_note(rigid), card]
    else:
        word = ring_braid(machine, carriers_at).generators
        info.update(_braid_info([int(g) for g in word], len(paths.points)))
        info["repeated"] = "cycle"
        info["made"] = cycles
        info["pure"] = cycles % (info.get("pure_after") or 1) == 0
    keys = list(paths.points)
    bobbins = [k for k in keys if k not in cores]
    colour = {k: PALETTE[i % len(PALETTE)] for i, k in enumerate(bobbins)}
    colour.update({k: CORE_COLOUR for k in cores})
    result = _result(
        title + f", {cycles} passes",
        paths,
        diameter,
        colours=[colour[k] for k in keys],
        names=[f"Core {k}" if k in cores else f"Bobbin {k}" for k in keys],
        info=info,
        notes=notes,
        timeline=_timeline(paths.trajectories, keys, "machine"),
    )
    # To make it on a marudai, as asked later, from the card; its core, if
    # it has one, after the bobbins, as the marudai has it.
    if stopped is None:
        from braidpy.web.words import _in_order

        bobbins = [k for k in keys if k not in cores]
        assert keys[len(bobbins) :] == list(cores)
        result["disk"] = _in_order(_lace_disk(spec)[3], bobbins)
        if cores:
            result["disk"]["core"] = "rigid" if rigid else "yarn"
    return result


def _loading(text: Any, machine: Any) -> list[tuple[str, int]] | None:
    """Carriers given as ``gear:slot``, each once; None if not given."""
    if text is None or not str(text).strip():
        return None
    if str(text).strip().lower() == "none":
        raise ValueError("Give at least one carrier.")
    loading: list[tuple[str, int]] = []
    # A lace machine's bobbins may be named by their notch, "A-B", as its
    # card names them: the notch the two gears' circles cut.
    from braidpy.horn_gear.jacquard import JacquardLaceMachine, notch_positions

    notches = {}
    if isinstance(machine, JacquardLaceMachine):
        at = notch_positions(machine)
        notches = {name: at[k] for name, k in _notch_names(len(machine.gears)).items()}
    for token in re.split(r"[\s,;]+", str(text).strip()):
        if token in notches:
            gear, slot = notches[token]
            if (gear, slot) in loading:
                raise ValueError(f"Two bobbins in the same notch, {token}.")
            loading.append((gear, slot))
            continue
        match = re.fullmatch(r"([^:\s]+):(\d+)", token)
        if not match:
            raise ValueError(f"Cannot read {token!r}: give each carrier as gear:slot.")
        gear, slot = match.group(1), int(match.group(2))
        if gear not in machine.gears:
            raise ValueError(f"No gear {gear!r}: one of {sorted(machine.gears)}.")
        n = machine.gears[gear].n_slots
        if slot >= n:
            raise ValueError(f"Gear {gear} has slots 0 to {n - 1}.")
        if (gear, slot) in loading:
            raise ValueError(f"Two carriers on the same slot, {gear}:{slot}.")
        loading.append((gear, slot))
    if not loading:
        raise ValueError("Give at least one carrier.")
    return loading


def _met(error: Any) -> str:
    """Where carriers met, as gear:slot."""
    return " and ".join(f"{g}:{slot}" for g, slot in error.collisions)


def machine_geometry(name: str) -> MachineGeometry:
    """A machine as the page draws it from above, to load it by hand: its
    gears — where, how big, the circle their carriers ride, their slots, the
    way they turn and where each slot is at step 0, drawn as braidpy draws it
    (:class:`~braidpy.horn_gear.layout.GearAngles`) — the contacts between
    them, and the machine's own loading."""
    from braidpy.horn_gear.layout import (
        carrier_radius,
        compute_layout,
        contact_point,
        gear_radii,
        slot_angles,
    )

    machine = _machine(name)
    layout = compute_layout(machine)
    radii = gear_radii(machine)
    angles = slot_angles(machine, layout)
    own = machine.default_carriers()
    return {
        "name": name,
        "gears": [
            {
                "name": gear_name,
                "x": float(layout[gear_name][0]),
                "y": float(layout[gear_name][1]),
                "radius": float(radii[gear_name]),
                "ride": float(carrier_radius(machine, layout, gear_name)),
                "slots": int(gear.n_slots),
                "direction": int(gear.direction),
                "angles": [
                    float(angles[gear_name](machine.slot_angle(gear_name, slot, 0)))
                    for slot in range(gear.n_slots)
                ],
            }
            for gear_name, gear in machine.gears.items()
        ],
        "contacts": [
            {
                "a": conn.gear_a,
                "b": conn.gear_b,
                "x": float(point[0]),
                "y": float(point[1]),
            }
            for conn in machine.connections
            for point in [contact_point(machine, layout, conn.gear_a, conn.gear_b)]
        ],
        "loading": [[own[k][0], int(own[k][1])] for k in sorted(own)],
    }


@lru_cache(maxsize=4)
def _worked(name: str) -> tuple[Any, Any]:
    """A machine to turn by hand, and its drawing: made once."""
    from braidpy.horn_gear.handle import drawing

    machine = _machine(name)
    return machine, drawing(machine)


def machine_turned(
    name: str, loading: list[list[Any]], time: int, frames: int = 8
) -> MachineTurned:
    """A machine's handle turned ``time`` steps by hand, as the page shows
    it (see :mod:`braidpy.horn_gear.handle`): stopped where carriers meet,
    and drawn through the next step, for the page to turn it smoothly.

    Args:
        name: The machine.
        loading: The carriers at step 0, as (gear, slot).
        time: How many steps to turn.
        frames: Pictures of the next step.

    Returns:
        ``time``, the step reached; ``carriers`` there, in the loading's
        order; ``met``, where carriers met, if they did; ``slots``, every
        slot gear by gear; and ``frames``, the slots' and carriers' places
        through the next step, the first at the step reached.
    """
    from braidpy.horn_gear.handle import sweep, turn

    machine, drawn = _worked(name)
    turned = turn(machine, [(str(g), int(s)) for g, s in loading], int(time))
    slots, slot_xy, carrier_xy = sweep(machine, turned.state, frames, drawn)

    def rounded(points: list[list[float]]) -> list[list[float]]:
        return [[round(x, 4), round(y, 4)] for x, y in points]

    return {
        "time": turned.time,
        "carriers": [[g, int(s)] for g, s in turned.positions],
        "met": [[g, int(s)] for g, s in turned.met],
        "slots": [[g, int(s)] for g, s in slots],
        "frames": [
            {"slots": rounded(slot_xy[k]), "carriers": rounded(carrier_xy[k])}
            for k in range(frames)
        ],
    }


def machine_origin(name: str, place: list[Any], time: int) -> list[Any] | None:
    """The slot at step 0 whose carrier is at ``place`` at step ``time``:
    where a carrier put on the machine there goes in its loading.

    Args:
        name: The machine.
        place: As (gear, slot), at step ``time``.
        time: The step.

    Returns:
        (gear, slot) at step 0; None if no slot leads there.
    """
    from braidpy.horn_gear.handle import origin

    machine, _ = _worked(name)
    found = origin(machine, (str(place[0]), int(place[1])), int(time))
    return None if found is None else [found[0], int(found[1])]


def _machine_entry() -> Source:
    from braidpy.machine_catalog import CATALOGUE

    return {
        "title": "Horn gear braiding machine",
        "defaults": defaults(*Machine.shown),
        "entries": [
            {"name": name, "title": entry.title} for name, entry in CATALOGUE.items()
        ],
    }


def _lace_entry() -> Source:
    from braidpy.machine_catalog import LACE
    from braidpy.making.lace import card_digits

    entries: list[Any] = []
    for name, entry in LACE.items():
        ring = entry.make()
        entries.append(
            {
                "name": name,
                "title": entry.title,
                "pattern": {"n_gears": ring.n_gears, "card": card_digits(ring.steps)},
            }
        )
    return {
        "title": "Jacquard lace machine",
        "defaults": defaults(*Lace.shown),
        "entries": entries + [{"name": OWN, "title": "Your own card…"}],
    }


SOURCES: dict[str, tuple[Callable[[], Source], Callable[[Spec], Result]]] = {
    "machine": (_machine_entry, _from_machine),
    "lace": (_lace_entry, _from_lace),
}
