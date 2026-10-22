# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""Horn gear braiding machines: the braid a machine makes, loaded as it loads
itself or by hand, stopped where carriers meet; and the machine as the page
draws it from above, to load it by hand."""

from __future__ import annotations

import re
from functools import lru_cache
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Collection,
    Dict,
    Hashable,
    List,
    Optional,
    Tuple,
    cast,
)

from braidpy.web._info import _braid_info

if TYPE_CHECKING:
    from braidpy.horn_gear.jacquard import JacquardLaceMachine
from braidpy.utils import PALETTE
from braidpy.web._result import _result, _tighten, _timeline
from braidpy.web._settings import OWN, Lace, Machine
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


def _card_text(program: Any) -> str:
    """A lace machine's card as typed: a step a line, the gears turning
    anticlockwise, then those turning clockwise, a 0 or 1 a gear."""
    return "\n".join(
        " ".join("".join("1" if on else "0" for on in line) for line in step)
        for step in program
    )


def _read_card(text: str, n_gears: int) -> List[Tuple[str, str]]:
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

    n_gears = Lace.n_gears.read(spec)
    if n_gears % 2:
        raise ValueError(
            f"{n_gears} gears cannot mesh in a ring: neighbours turn opposite "
            "ways, so give an even number."
        )
    return jacquard_lace_ring(n_gears, _read_card(Lace.card.read(spec), n_gears))


def _from_machine(spec: Spec) -> Result:
    from braidpy.horn_gear import axial_positions, compute_layout, gear_radii
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
    layout = compute_layout(machine)
    cores = axial_positions(machine, layout)
    stiff = Machine.cores.read(spec)
    if stiff not in Machine.stiffness:
        raise ValueError("Cores are either yarn or rigid.")
    # The cores run up the braid, each in its own place, where the machine
    # lays it; the yarns are drawn in round them.  A rigid core stays
    # straight there; a core of yarn is held there at both ends, and gives
    # way between to the yarns pressing on it — never so far as to pass
    # another core.
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
    paths = _tighten(
        paths, spec, diameter, rigid=list(cores) if stiff == "rigid" else []
    )
    info: Info = {}
    notes = ["Words are read over one cycle of the machine."]
    if stopped is not None:
        assert loading is not None
        info["collision"] = _collision(stopped, loading)
        notes = [_stopped_note(stopped, n_steps)]
    elif cores:
        notes = [
            "It braids round a core, drawn here in grey as the yarn it is; its "
            "word would need the core as a strand of its own: no word is given."
        ]
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
    colour = {k: PALETTE[i % len(PALETTE)] for i, k in enumerate(carriers)}
    colour.update({k: Machine.core_colour for k in cores})
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


def _braided(
    machine: Any,
    carriers_at: Optional[Dict[int, Tuple[str, int]]],
    cycles: int,
    period: Optional[int],
    diameter: float,
) -> Tuple[Any, Any, Optional[int]]:
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


def _collision(stopped: Any, loading: List[Tuple[str, int]]) -> Collision:
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


def _stopped_note(stopped: Any, n_steps: Optional[int]) -> str:
    return (
        f"Carriers met at step {stopped.step}, on {_met(stopped)}: the "
        f"braiding stopped there, after {n_steps} steps. The carriers that "
        "met are ringed where they started. No word is read."
    )


def _from_lace(spec: Spec) -> Result:
    """A Jacquard lace machine's braid: its card run so many passes, read
    off the machine itself (:func:`~braidpy.bridges.lace.ring_braid`)."""
    from braidpy.bridges.lace import punchcard_text, ring_braid
    from braidpy.horn_gear import gear_radii
    from braidpy.machine_catalog import LACE

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
    paths, stopped, n_steps = _braided(
        machine, carriers_at, cycles, machine.steps_per_pass, diameter
    )
    paths = _tighten(paths, spec, diameter, rigid=[])
    info: Info = {}
    card = punchcard_text(machine.program)
    notes = [
        "Words are read over one pass of the card. The card, a column a gear, "
        "two lines a step — the gears turning anticlockwise ↺, then "
        "clockwise ↻ — ● punched:\n" + card
    ]
    if stopped is not None:
        info["collision"] = _collision(
            stopped, loading or [own[k] for k in sorted(own)]
        )
        notes = [_stopped_note(stopped, n_steps)]
    else:
        word = ring_braid(machine, carriers_at).generators
        info.update(_braid_info([int(g) for g in word], len(paths.points)))
        info["repeated"] = "cycle"
        info["made"] = cycles
        info["pure"] = cycles % (info.get("pure_after") or 1) == 0
    keys = list(paths.points)
    return _result(
        title + f", {cycles} passes",
        paths,
        diameter,
        colours=[PALETTE[i % len(PALETTE)] for i in range(len(keys))],
        names=[f"Bobbin {k}" for k in keys],
        info=info,
        notes=notes,
        timeline=_timeline(paths.trajectories, keys, "machine"),
    )


def _loading(text: Any, machine: Any) -> Optional[List[Tuple[str, int]]]:
    """Carriers given as ``gear:slot``, each once; None if not given."""
    if text is None or not str(text).strip():
        return None
    if str(text).strip().lower() == "none":
        raise ValueError("Give at least one carrier.")
    loading: List[Tuple[str, int]] = []
    for token in re.split(r"[\s,;]+", str(text).strip()):
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
    way they turn and where their first slot is — the contacts between them,
    and the machine's own loading.  A slot's angle at step ``t`` is
    ``offset + 2π (slot + direction · t) / slots``."""
    from braidpy.horn_gear.layout import (
        carrier_radius,
        compute_layout,
        contact_point,
        gear_radii,
        slot_offsets,
    )

    machine = _machine(name)
    layout = compute_layout(machine)
    radii = gear_radii(machine)
    offsets = slot_offsets(machine, layout)
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
                "offset": float(offsets[gear_name]),
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
def _worked(name: str) -> Tuple[Any, Any]:
    """A machine to turn by hand, and its drawing: made once."""
    from braidpy.horn_gear.handle import drawing

    machine = _machine(name)
    return machine, drawing(machine)


def machine_turned(
    name: str, loading: List[List[Any]], time: int, frames: int = 8
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

    def rounded(points: List[List[float]]) -> List[List[float]]:
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


def machine_origin(name: str, place: List[Any], time: int) -> Optional[List[Any]]:
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


def _place_cores(paths, cores: Collection[Hashable]):
    """The cores, each standing straight in the braid where the machine
    lays it, all the way down to the fell: drawn in to the fell with the
    yarns, the cores would come closer there than the machine lays them,
    and could pass each other."""
    from dataclasses import replace

    if not cores:
        return paths
    points = dict(paths.points)
    n = paths.formed_count
    for k in cores:
        line = points[k].copy()
        line[:n, :2] = line[0, :2]
        points[k] = line
    return replace(paths, points=points)


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

    entries: List[Any] = []
    for name, entry in LACE.items():
        ring = entry.make()
        entries.append(
            {
                "name": name,
                "title": entry.title,
                "pattern": {"n_gears": ring.n_gears, "card": _card_text(ring.steps)},
            }
        )
    return {
        "title": "Jacquard lace machine",
        "defaults": defaults(*Lace.shown),
        "entries": entries + [{"name": OWN, "title": "Your own card…"}],
    }


SOURCES: Dict[str, Tuple[Callable[[], Source], Callable[[Spec], Result]]] = {
    "machine": (_machine_entry, _from_machine),
    "lace": (_lace_entry, _from_lace),
}
